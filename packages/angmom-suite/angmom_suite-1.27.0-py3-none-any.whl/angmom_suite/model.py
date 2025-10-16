from functools import reduce, partial
from itertools import product, accumulate
from collections import namedtuple
from fractions import Fraction
import warnings
from operator import add, mul
import h5py

from jax import numpy as jnp
from jax import scipy as jscipy
from jax import value_and_grad
from jax.tree import map as tmap
from jax.tree import reduce as treduce
from jax import config

import numpy as np

from hpc_suite.store import Store
from molcas_suite.extractor import make_extractor as make_molcas_extractor

from sympy.functions.special.tensor_functions import LeviCivita
from sympy.core.numbers import Zero
from .magnetism import zeeman_hamiltonian, compute_eprg_tensors, magmom, \
    susceptibility_tensor, make_susceptibility_tensor
from . import utils as ut
from .basis import unitary_transform, cartesian_op_squared, rotate_cart, perturb_doublets, \
    sfy, calc_ang_mom_ops, make_angmom_ops_from_mult, project_irrep_basis, \
    Symbol, Term, Level, couple, sf2ws, ws2sf, sf2ws_amfi, extract_blocks, \
    dissect_array, from_blocks, ANGM_SYMBOLS, TOTJ_SYMBOLS, \
    print_sf_term_content, print_so_term_content, build_random_unitary
from .optimisation import riem_sd
from .crystal import calc_stev_ops
from .group import cartan_killing_metric

config.update("jax_enable_x64", True)

HARTREE2INVCM = 219474.6


def print_basis(hamiltonian, spin, angm, space, comp_thresh=0.05, field=None, plot=False, shift=True, **ops):
    """Print information of basis transformation and plot transformed angmom
    operators.

    Parameters
    ----------
    hamiltonian : np.array
        Array containing the total Hamiltonian in the angmom basis.
    spin : np.array
        Array containing the total spin operator in the angm basis.
    angm : np.array
        Array containing the total orbital angmom operator in the angmom basis.
    space : list of obj
        List of Symbol objects specifing the input space, e.g. terms/levels.
    comp_thresh : float
        Maximum amplitude of a given angular momentum state to be printed in
        the composition section.

    Returns
    -------
    None
    """

    if plot:
        titles = [comp + "-component" for comp in ["x", "y", "z"]]
        ut.plot_op([hamiltonian], 'hamiltonian' + ".png")
        for lab, op in ops.items():
            ut.plot_op(op, lab + ".png", sq=True, titles=titles)

    # print angmom basis and composition of the electronic states
    basis = space[0].basis

    qn_dict = {op + comp: np.sqrt(
        1/4 + np.diag(cartesian_op_squared(ops[op]).real)) - 1/2
        if comp == '2' else np.diag(ops[op][2]).real
        for op, comp in basis if op in ops and ops[op] is not None}

    def form_frac(rat, signed=True):
        return ('+' if rat > 0 and signed else '') + str(Fraction(rat))

    print("Angular momentum basis:")
    hline = 12 * "-" + "----".join([13 * "-"] * len(basis))

    print(hline)
    print(12 * " " + " || ".join(["{:^13}".format(op) for op in basis]))

    def states():
        for symbol in space:
            for state in symbol.states:
                yield state

    print(hline)
    for idx, state in enumerate(states()):
        print(f"state {idx + 1:4d}: " + " || ".join(
            ["{:>5} ({:5.2f})".format(
                form_frac(getattr(state, op + comp),
                          signed=False if comp == '2' else True),
                qn_dict[op + comp][idx] if op + comp in qn_dict else np.nan)
             for op, comp in basis]))

    print(hline)
    print("Basis labels - state N: [[<theo qn> (<approx qn>)] ...]")

    print()

    print("-----------------------------------------------------------")
    print("Diagonal basis energy, <S_z>, <L_z>, <J_z> and composition:")
    print("( angular momentum kets - " + "|" + ', '.join(basis) + "> )")
    print("-----------------------------------------------------------")

    if field:
        zeeman = zeeman_hamiltonian(spin, angm, [0, 0, field])
        eig, vec_total = np.linalg.eigh(hamiltonian + zeeman)

    else:
        eig, vec = np.linalg.eigh(hamiltonian)

        if field is None:
            vec_total = vec
        else:
            vec_total = vec @ perturb_doublets(
                eig, unitary_transform(spin + angm, vec))

    if shift:
        eners = (eig - eig[0]) * HARTREE2INVCM
    else:
        eners = eig * HARTREE2INVCM

    expectation = zip(*[np.diag(unitary_transform(op[2], vec_total).real)
                        for op in (spin, angm, spin + angm)])

    composition = np.real(vec_total * vec_total.conj())

    def format_state(state, op):
        return form_frac(getattr(state, op), signed=op[1] == 'z')

    for idx, (ener, exp, comp) in enumerate(
            zip(eners, expectation, composition.T), start=1):
        # generate states and sort by amplitude
        super_position = sorted(
            ((amp * 100, tuple(format_state(state, op) for op in basis))
             for state, amp in zip(states(), comp) if amp > comp_thresh),
            key=lambda item: item[0],
            reverse=True)

        print(f"State {idx:4d} {ener:8.4f}  " +
              " ".join([f"{val:+4.2f}" for val in exp]) + " : " +
              '  +  '.join("{:.2f}% |{}>".format(amp, ', '.join(state))
                           for amp, state in super_position))

    print("------------------------")
    print()


def make_operator_storage(op, **ops):

    description_dict = {
        "hamiltonian": "Hamiltonian matrix elements",
        "angm": "Orbital angular momentum matrix elements",
        "spin": "Spin angular momentum matrix elements"
    }

    return StoreOperator(ops[op], op, description_dict[op])


class StoreOperator(Store):

    def __init__(self, op, *args, units='au', fmt='% 20.13e'):

        self.op = op

        super().__init__(*args, label=(), units=units, fmt=fmt)

    def __iter__(self):
        yield (), self.op


def make_proj_evaluator(_, molcas_rassi=None, **options):
    if molcas_rassi is not None:
        return ProjectModelHamiltonianMolcas(molcas_rassi, options)


class ProjectModelHamiltonian(Store):

    def __init__(self, ops, sf_mult, model_space=None, coupling=None,
                 basis='l', truncate=None, quax=None, terms=None, k_max=6,
                 theta=None, ion=None, zeeman=False, orbital_reduction=False,
                 tp_equivalence=False, comp_thresh=0.05, field=None, verbose=False,
                 units='cm^-1', fmt='% 20.13e'):

        self.ops = ops
        self.sf_mult = sf_mult
        self.spin_mults = np.repeat(*zip(*self.sf_mult.items()))

        # basis options
        self.model_space = model_space
        self.coupling = coupling
        self.quax = quax

        if self.model_space is None:
            smult = np.repeat(list(self.sf_mult.keys()), list(self.sf_mult.values()))

            ws_angm = sf2ws(ops['sf_angm'], self.sf_mult)
            ws_spin = np.array(make_angmom_ops_from_mult(smult)[0:3])
            ws_hamiltonian = sf2ws(ops['sf_mch'], self.sf_mult) + \
                sf2ws_amfi(ops['sf_amfi'], self.sf_mult)

            eig, vec = np.linalg.eigh(ws_hamiltonian)
            so_eners = (eig - eig[0]) * HARTREE2INVCM

            sf_eners = [(np.diag(eners) - eners[0, 0]) * HARTREE2INVCM
                        for eners in ops['sf_mch']]

            print_sf_term_content(ops['sf_angm'], sf_eners, self.sf_mult)
            print_so_term_content(unitary_transform(ws_spin, vec),
                                  unitary_transform(ws_angm, vec),
                                  so_eners, self.sf_mult)
            exit()

        # model options
        self.terms = terms
        self.k_max = k_max
        self.theta = theta
        self.ion = ion

        self.basis = basis
        self.truncate = \
            truncate if truncate is None or self.basis == 'l' else truncate[0]

        self.zeeman = zeeman
        self.orbital_reduction = orbital_reduction
        self.tp_equivalence = tp_equivalence

        self.model = SpinHamiltonian(self.model_space, k_max=self.k_max, theta=self.theta,
                                     ion=self.ion, time_reversal_symm="even", **self.terms)

        if self.basis == 'l':
            self.basis_space, self.cg_vecs = \
                evaluate_term_space(model_space, coupling=coupling)
        elif self.basis == 'j':
            self.basis_space, self.cg_vecs = \
                evaluate_level_space(model_space, coupling=coupling)

        # raise ValueError(f"Unknown intermediate basis: {self.basis}!")

        # printing options
        self.comp_thresh = comp_thresh
        self.field = field
        self.verbose = verbose

        description = \
            f"Spin Hamiltonian parameters of the {model_space} multiplet."

        super().__init__('parameters', description,
                         label=("term", "operators"), units=units, fmt=fmt)

    def evaluate(self, **ops):

        if self.verbose:
            print("Ab initio angular momentum basis space:")
            print(self.basis_space)

        # rotation of quantisation axis
        def rot_cart(ops):
            return rotate_cart(ops, self.quax)

        if self.quax is not None:
            ops['sf_amfi'] = sfy(rot_cart, sf=2)(ops['sf_amfi'])
            ops['sf_angm'] = sfy(rot_cart, sf=1)(ops['sf_angm'])

        if self.orbital_reduction:
            ws_basis_vecs, angmom_reduction_dict = \
                self.evaluate_ws_basis_transform(ops, orbital_reduction=True)
        else:
            ws_basis_vecs = self.evaluate_ws_basis_transform(ops)

        if len(self.basis_space) > 1:
            basis_hamiltonian = unitary_transform(self.evaluate_hamiltonian(ops), ws_basis_vecs)
            basis_rot = self.evaluate_basis_rot(basis_hamiltonian)
            ws_basis_vecs = ws_basis_vecs @ basis_rot

        ws_vecs = ws_basis_vecs @ self.cg_vecs

        if self.verbose:
            ut.plot_op([ws_vecs, ws_vecs * ws_vecs.conj()], "ws_vecs.png")
            self.print_basis(ops, ws_vecs)

        hamiltonian = unitary_transform(self.evaluate_hamiltonian(ops), ws_vecs)
        param_dict = self.model.project(hamiltonian, verbose=self.verbose)

        if self.zeeman:
            ws_spin = np.array(make_angmom_ops_from_mult(self.spin_mults)[0:3])
            ws_angm = sf2ws(ops['sf_angm'], self.sf_mult)
            spin = unitary_transform(ws_spin, ws_vecs)
            angm = unitary_transform(ws_angm, ws_vecs)
            zeeman_dict = ZeemanHamiltonian(self.model_space).project(spin, angm, verbose=self.verbose)
            param_dict |= zeeman_dict

        if self.orbital_reduction:
            param_dict |= angmom_reduction_dict

        return list(param_dict.values()), list(param_dict.keys())

    def print_basis(self, ops, ws_vecs):

        ws_spin = np.array(make_angmom_ops_from_mult(self.spin_mults)[0:3])
        ws_angm = sf2ws(ops['sf_angm'], self.sf_mult)

        ws_compl_vecs, rmat = jnp.linalg.qr(ws_vecs, mode='complete')
        ws_compl_vecs = ws_compl_vecs.at[:, :rmat.shape[1]].multiply(jnp.diag(rmat))

        hamiltonian = unitary_transform(self.evaluate_hamiltonian(ops), ws_compl_vecs)
        spin = unitary_transform(ws_spin, ws_compl_vecs)
        angm = unitary_transform(ws_angm, ws_compl_vecs)

        print_basis(hamiltonian, spin, angm,
                    [self.model_space], comp_thresh=self.comp_thresh,
                    field=self.field, plot=self.verbose,
                    S=spin, L=angm, J=spin + angm)
        return

    def evaluate_hamiltonian(self, ops):
        return sf2ws_amfi(ops['sf_amfi'], self.sf_mult) + sf2ws(ops['sf_mch'], self.sf_mult)

    def evaluate_ws_basis_transform(self, ops, orbital_reduction=False):

        if orbital_reduction:

            def complement_angm(ops, kappa=None, sf_angm_residuals=None):

                def compl_angm(sf_angm):

                    if kappa is not None:
                        def rescale_angm(sf_angm):
                            return sf_angm / kappa[:, jnp.newaxis, jnp.newaxis]
                        return tmap(rescale_angm, sf_angm)

                    if sf_angm_residuals is not None:
                        return tmap(add, sf_angm, sf_angm_residuals)

                return {key: compl_angm(val) if key == 'sf_angm' else val
                        for key, val in ops.items()}

            threshold = 1e-5
            max_step = 100
            angm_model = AngmomReduction(self.model_space)
            angm_reduction_dict, kappa = angm_model.evaluate_cartan_killing_reduction(
                sf2ws(ops['sf_angm'] if self.truncate is None else
                      [angm[:, :truncate, :truncate] for angm, truncate in
                       zip(ops['sf_angm'], self.truncate)],
                      self.sf_mult),
                negative_sign=self.tp_equivalence
            )

            ws_basis_vecs = self.evaluate_ws_basis_transform(
                complement_angm(ops, kappa=kappa))
            ws_angm = sf2ws(ops['sf_angm'], self.sf_mult)

            def make_orb_red_str(angm_red_dict):
                orb_red_dict = {op: [params[namedtuple("k", "comp")(comp)] for comp in "xyz"]
                                for (_, (op,)), params in angm_red_dict.items()}
                return ", ".join([f"{op:1}: " + " ".join([f"{param:>4.5f}" for param in params])
                                  for op, params in orb_red_dict.items()])
            if self.verbose:
                print("Determination of orbital reduction:")
                print("===================================")
                print(f"{'step':>4}  {'residuals':>14}  orbital reduction factors")
                print(f"intital guess ------- {make_orb_red_str(angm_reduction_dict)}")

            # iteratively determine orbital reduction
            for step in range(1, max_step + 1):

                ws_vecs = ws_basis_vecs @ self.cg_vecs
                angm = unitary_transform(ws_angm, ws_vecs)

                diff = tmap(lambda x, y: (x - y)**2,
                            angm_reduction_dict,
                            angm_reduction_dict := angm_model.project(angm))

                residuals = treduce(add, diff)
                if self.verbose:
                    print(f"{step:4d}  {residuals:>14.8e}  {make_orb_red_str(angm_reduction_dict)}")

                if residuals < threshold:
                    return ws_basis_vecs, angm_reduction_dict

                angm_res = angm_model.compute_residual_angmom(angm_reduction_dict)
                ws_angm_res = unitary_transform(angm_res, ws_vecs.conj().T)
                sf_angm_res = ws2sf(ws_angm_res, self.sf_mult)
                # assert jnp.allclose(ws_angm_res, sf2ws(sf_angm_res, self.sf_mult))
                ws_basis_vecs = self.evaluate_ws_basis_transform(
                    complement_angm(ops, sf_angm_residuals=sf_angm_res))

            raise ValueError("Angular momentum reduction not converged!")

        if self.basis == 'l':
            sf_term_vecs = self.evaluate_sf_term_transform(ops)
            return sf2ws(sf_term_vecs, self.sf_mult)

        elif self.basis == 'j':
            level_vecs = self.evaluate_level_transform(ops)
            return level_vecs

    def evaluate_basis_rot(self, basis_hamiltonian):

        if self.basis == 'l':
            sf_term_rot = self.evaluate_sf_term_rotation(basis_hamiltonian)
            return sf2ws(sf_term_rot, self.sf_mult)

        # if self.verbose:
        #     ut.plot_op(sf_term_vecs, "sf_vecs.png")
        #     ut.plot_op(np.block(unitary_transform(ops['sf_amfi'], sf_term_vecs, sf=2)), "sf_amfi_phased.png")

        elif self.basis == 'j':
            return self.evaluate_level_rotation(basis_hamiltonian)

    def evaluate_sf_term_transform(self, ops):

        def term_trafo(terms, *ops):
            return project_irrep_basis(terms, **dict(zip(["L"], ops)))

        sf_terms = [[Symbol(L=term.qn['L']) for term in self.basis_space if term.mult['S'] == mult]
                    for mult in self.sf_mult]

        if self.truncate is None:
            sf_term_vecs = list(map(term_trafo, sf_terms, ops['sf_angm']))
        else:
            sf_angm = [angm[:, :truncate, :truncate] for angm, truncate in
                       zip(ops['sf_angm'], self.truncate)]
            sf_term_vecs = list(map(term_trafo, sf_terms, sf_angm))
            sf_term_vecs = [np.identity(num)[:, :truncate] @ term_vecs
                            for num, truncate, term_vecs in
                            zip(self.sf_mult.values(), self.truncate, sf_term_vecs)]

        if self.verbose:
            ut.plot_op(from_blocks(*unitary_transform(ops['sf_angm'], sf_term_vecs, sf=1)), "sf_angm.png", sq=True)

        return sf_term_vecs

    def evaluate_sf_term_rotation(self, hamiltonian):

        sf_terms = [[Symbol(L=term.qn['L']) for term in self.basis_space if term.mult['S'] == mult]
                    for mult in self.sf_mult]

        sf_sub_dims = [dict(zip(*np.unique([term.mult['L'] for term in terms], return_counts=True)))
                       for terms in sf_terms]

        def build_sf_unitary(sf_sub_rot):
            return [from_blocks(*(jnp.kron(rot, jnp.identity(mult)) for rot, mult in zip(sub_rot, sub_dims)))
                    if sub_dims else jnp.empty([0, 0])
                    for sub_rot, sub_dims in zip(sf_sub_rot, sf_sub_dims)]

        def cost_function(sf_sub_rot):
            sf_rot = build_sf_unitary(sf_sub_rot)
            ws_rot = sf2ws(sf_rot, self.sf_mult) @ self.cg_vecs
            ham = unitary_transform(hamiltonian, ws_rot) * HARTREE2INVCM
            return -self.model.compute_projection_norm(ham)

        sf_sub_rot = [[build_random_unitary(dim) for dim in sub_dims.values()]
                      for sub_dims in sf_sub_dims]

        max_step = 500
        threshold = 1.0e-15

        solver = riem_sd()
        opt_state = solver.init(sf_sub_rot)

        if self.verbose:
            print("Progress of the basis rotation:")
            print("===============================")
            print(f"{'step':>4}  {'model coverage':>14}  {'gradient_norm':>14}  {'step_size':>9}")

        for step in range(max_step):

            cost, sf_sub_eucl_grad = value_and_grad(cost_function)(sf_sub_rot)

            if self.verbose:
                print(f"{step:4d}  {-cost:>14.12f}  {opt_state[0][0]:>14.8e}  {opt_state[-2][0]:>9.3e}")

            updates, opt_state = solver.update(sf_sub_eucl_grad, opt_state, sf_sub_rot, value=cost, value_fn=cost_function)
            sf_sub_rot = tmap(jnp.matmul, tmap(jscipy.linalg.expm, updates), sf_sub_rot)

            if opt_state[0][0] < threshold:
                break

        sf_sub_sgn = [[jnp.ones(dim) for dim in sub_dims.values()] for sub_dims in sf_sub_dims]
        cost = cost_function(sf_sub_rot)
        if self.verbose:
            print(f"{'':4}  {-cost:>14.12f} -- relative sign determination started")

        def flip_relative_sign(sf_sub_sgn, mult_idx, dim_idx):
            for _mult_idx in range(mult_idx):
                for _dim_idx in range(len(sf_sub_dims[_mult_idx])):
                    sf_sub_sgn[_mult_idx][_dim_idx] *= -1
            for _dim_idx in range(dim_idx + 1):
                sf_sub_sgn[mult_idx][_dim_idx] *= -1
            return sf_sub_sgn

        for mult_idx, sub_dims in enumerate(sf_sub_dims):
            for dim_idx, dim in enumerate(sub_dims.values()):
                sf_sub_sgn = flip_relative_sign(sf_sub_sgn, mult_idx, dim_idx)
                _cost = cost_function(tmap(mul, sf_sub_sgn, sf_sub_rot))
                if self.verbose:
                    print(f"{'':4}  {-_cost:>14.12f}  {'':14}  {'':9}")
                if _cost <= cost:
                    cost = _cost
                else:
                    sf_sub_sgn = flip_relative_sign(sf_sub_sgn, mult_idx, dim_idx)

        sf_sub_rot = tmap(mul, sf_sub_sgn, sf_sub_rot)
        cost = cost_function(sf_sub_rot)

        if self.verbose:
            print(f"{'':4}  {-cost:>14.12f} -- final model coverage")

        return build_sf_unitary(sf_sub_rot)

    def evaluate_level_transform(self, ops):

        ws_spin = np.array(make_angmom_ops_from_mult(self.spin_mults)[0:3])
        ws_angm = sf2ws(ops['sf_angm'], self.sf_mult)

        if self.truncate is None:
            level_vecs = project_irrep_basis(self.basis_space, J=ws_spin + ws_angm)
        else:
            hamiltonian = sf2ws_amfi(ops['sf_amfi'], self.sf_mult) + sf2ws(ops['sf_mch'], self.sf_mult)
            _, so_vecs = np.linalg.eigh(hamiltonian)
            so_spin = unitary_transform(ws_spin, so_vecs[:, :self.truncate])
            so_angm = unitary_transform(ws_angm, so_vecs[:, :self.truncate])
            so_level_vecs = project_irrep_basis(self.basis_space, J=so_spin + so_angm)

            level_vecs = so_vecs[:, :self.truncate] @ so_level_vecs

        return level_vecs

    def evaluate_level_rotation(self, hamiltonian):

        sub_dims = dict(zip(*np.unique([(lvl.mult['J']) for lvl in self.basis_space], return_counts=True)))

        def build_unitary(sub_rot):
            return from_blocks(*(jnp.kron(rot, jnp.identity(mult)) for rot, mult in zip(sub_rot, sub_dims)))

        def cost_function(sub_rot):
            ws_rot = build_unitary(sub_rot) @ self.cg_vecs
            ham = unitary_transform(hamiltonian, ws_rot) * HARTREE2INVCM
            return -self.model.compute_projection_norm(ham)

        sub_rot = [build_random_unitary(dim) for dim in sub_dims.values()]

        max_step = 500
        threshold = 1.0e-15

        solver = riem_sd()
        opt_state = solver.init(sub_rot)

        if self.verbose:
            print("Progress of the basis rotation:")
            print("===============================")
            print(f"{'step':>4}  {'model coverage':>14}  {'gradient_norm':>14}  {'step_size':>9}")

        for step in range(max_step):

            cost, sub_eucl_grad = value_and_grad(cost_function)(sub_rot)

            if self.verbose:
                print(f"{step:4d}  {-cost:>14.12f}  {opt_state[0][0]:>14.8e}  {opt_state[-2][0]:>9.3e}")

            updates, opt_state = solver.update(sub_eucl_grad, opt_state, sub_rot, value=cost, value_fn=cost_function)

            sub_rot = tmap(jnp.matmul, tmap(jscipy.linalg.expm, updates), sub_rot)

            if opt_state[0][0] < threshold:
                break

        return build_unitary(sub_rot)

    def __iter__(self):
        yield from map(lambda val, lab: (self.format_label(lab), val),
                       *self.evaluate(**self.ops))

    def format_label(self, label):
        return (label[0], '_'.join(label[1]))


class ProjectModelHamiltonianMolcas(ProjectModelHamiltonian):

    def __init__(self, h_file, options):

        angm = make_molcas_extractor(h_file, ("rassi", "SFS_angmom"))[()]
        ener = make_molcas_extractor(h_file, ("rassi", "SFS_energies"))[()]
        amfi = make_molcas_extractor(h_file, ("rassi", "SFS_AMFIint"))[()]

        spin_mult = make_molcas_extractor(h_file, ("rassi", "spin_mult"))[()]

        # spin-free energies; reference to ground state of lowest multiplicity
        sf_ener = list(extract_blocks(ener, spin_mult))

        ops = {
            'sf_angm': list(extract_blocks(angm, spin_mult, spin_mult)),
            'sf_mch': list(map(lambda e: np.diag(e - sf_ener[0][0]), sf_ener)),
            'sf_amfi': list(map(list, dissect_array(amfi, spin_mult, spin_mult)))
        }

        sf_mult = dict(zip(*np.unique(spin_mult, return_counts=True)))

        super().__init__(ops, sf_mult, **options)


def evaluate_term_space(model_space, coupling=None):
    """Connects model space with space of L,S terms"""

    def reorder(terms):
        """Reorder term basis of model-term transformation to match S, L, M_L, M_S ordering"""
        terms, perms = zip(*map(lambda term: term.reduce(ops=('L', 'S'), cls=Term, return_perm=True), terms))
        start_idc = accumulate([term.multiplicity for term in terms], initial=0)
        _terms, _start_idc, _perms = \
            zip(*sorted(zip(terms, start_idc, perms), key=lambda x: (x[0].qn['S'], x[0].qn['L'])))
        return _terms, [start + idx for start, perm in zip(_start_idc, _perms) for idx in perm]

    if coupling:
        cpld_space, cg_vec = couple(model_space, **coupling)
        term_space, order = reorder(cpld_space)
        trafo = cg_vec[:, order].T

    elif isinstance(model_space, Level):
        term_space = [Term(L=model_space.qn['L'], S=model_space.qn['S'])]
        _, trafo = term_space[0].couple('J', 'L', 'S', levels=[model_space])

    elif isinstance(model_space, Term):
        term_space = [model_space]
        trafo = np.identity(model_space.multiplicity)

    else:
        raise ValueError(f"Invalid model_space {model_space}!")

    return term_space, trafo


def evaluate_level_space(model_space, coupling=None):
    """Connects model space with space of J levels"""

    def reorder(levels):
        """Reorder level basis of model-level transformation to match J, M_J ordering"""
        levels, perms = zip(*map(lambda term: term.reduce(ops=('J',), return_perm=True), levels))
        start_idc = accumulate([level.multiplicity for level in levels], initial=0)
        _levels, _start_idc, _perms = \
            zip(*sorted(zip(levels, start_idc, perms), key=lambda x: x[0].qn['J']))
        return _levels, [start + idx for start, perm in zip(_start_idc, _perms) for idx in perm]

    if coupling:
        cpld_space, cg_vec = couple(model_space, **coupling)
        level_space, order = reorder(cpld_space)
        trafo = cg_vec[:, order].T

    elif isinstance(model_space, Level):
        level_space = [model_space]
        trafo = np.identity(model_space.multiplicity)

    elif isinstance(model_space, Term):
        cpld_space, cg_vec = couple(model_space, J=('L', 'S'))
        level_space, order = reorder(cpld_space)
        trafo = cg_vec[:, order].T

    else:
        raise ValueError(f"Invalid model_space {model_space}!")

    return level_space, trafo


def read_params(file, group='/', **mapping):
    with h5py.File(file, 'r') as h:
        for term in iter(grp := h[group]):
            if term == 'diag':
                pass
            else:
                for ops in iter(grp[term]):
                    path = grp['/'.join([term, ops, 'parameters'])]
                    op_labs = tuple(mapping.get(o, o) for o in ops.split('_'))
                    key = path.attrs['typename']
                    env = {key: namedtuple(key, path.attrs['field_names'])}
                    names = [eval(row, env) for row in path.attrs['row_names']]
                    data = path[...]
                    yield (term, op_labs), {k: v for k, v in zip(names, data)}


class Model:

    def __init__(self, symbol):

        self.symbol = symbol

    def __iter__(self):
        # todo: yield from?
        yield from (((term, labs), self.resolve_model_ops[term](labs))
                    for term, sub in self.terms.items() for labs in sub)

    def print_basis(self):
        print(self.symbol.states)

    def check_orthogonality(self):

        def proj(op1, op2):
            return np.sum(op1 * op2.conj()).real / \
                (np.linalg.norm(op1) * np.linalg.norm(op1))

        def generate_ops():
            for (term, labs), ops in iter(self):
                for key, op in ops:
                    yield op

        ortho_matrix = np.array([[proj(op1, op2) for op2 in generate_ops()]
                                 for op1 in generate_ops()])

        if not np.allclose(ortho_matrix, np.identity(len(list(generate_ops())))):
            warnings.warn("Non-orthogonality detected in model operators!")

        return


class ZeemanHamiltonian(Model):

    def __init__(self, symbol, angm_ops=None):

        self.terms = {"zee": list(map(lambda lab: (lab,), symbol.mult.keys()))}

        self.resolve_model_ops = {
            "zee": self._build_zee
        }

        super().__init__(symbol)

        self.angm = \
            {o: tuple(angm_ops[o]) + (angm_ops[o][0] + 1.j * angm_ops[o][1],
                                      angm_ops[o][0] - 1.j * angm_ops[o][1],
                                      cartesian_op_squared(angm_ops[o])[0])
             if angm_ops is not None and o in angm_ops else
             calc_ang_mom_ops(self.symbol.qn[o]) for o in self.symbol.coupling.keys()}

    def _build_zee(self, ops):

        Key = namedtuple('g', 'comp')

        return ((Key(["x", "y", "z"][comp]),
                 reduce(np.kron,
                        [self.angm[o][comp] if o == ops[0] else np.identity(m)
                         for o, m in self.symbol.mult.items()]))
                for comp in range(3))

    def resolve_zeeman_ops(self, params, verbose=False):

        g_e = 2.002319

        zee = np.zeros((3, self.symbol.multiplicity, self.symbol.multiplicity),
                       dtype='complex128')

        for (term, labs), ops in iter(self):
            if term == "zee":
                for key, op in ops:

                    if verbose:
                        print(f"Parametrising {key} of {term}{labs}")

                    zee[{'x': 0, 'y': 1, 'z': 2}[getattr(key, 'comp')]] += \
                        params[(term, labs)][key] * op

        jtot = reduce(add,
                      [reduce(np.kron,
                              [self.angm[o][:3] if o == p else np.identity(m)
                               for o, m in self.symbol.mult.items()])
                       for p in self.symbol.mult.keys()])

        spin = (zee - jtot) / (g_e - 1)
        angm = jtot - spin

        return spin, angm

    def project(self, spin, angm, verbose=False):

        g_e = 2.002319

        zee = g_e * spin + angm

        def proj(op):
            return jnp.sum(zee * op.conj()).real / jnp.linalg.norm(op)**2

        params = {(term, labs): {key: proj(op) for key, op in ops}
                  for (term, labs), ops in iter(self)}

        self.check_orthogonality()

        return params


class AngmomReduction(Model):

    def __init__(self, symbol, angm_ops=None):

        self.terms = {"angm_red": [(lab,) for lab in symbol.coupling if lab in ANGM_SYMBOLS]}

        self.resolve_model_ops = {
            "angm_red": self._build_angm_red
        }

        super().__init__(symbol)

        self.angm = \
            {o: tuple(angm_ops[o]) + (angm_ops[o][0] + 1.j * angm_ops[o][1],
                                      angm_ops[o][0] - 1.j * angm_ops[o][1],
                                      cartesian_op_squared(angm_ops[o])[0])
             if angm_ops is not None and o in angm_ops else
             calc_ang_mom_ops(self.symbol.qn[o]) for o in self.symbol.coupling}

    def _build_angm_red(self, ops):

        Key = namedtuple('k', 'comp')

        return ((Key(["x", "y", "z"][comp]),
                 reduce(np.kron,
                        [self.angm[o][comp] if o == ops[0] else np.identity(m)
                         for o, m in self.symbol.mult.items()]))
                for comp in range(3))

    def compute_residual_angmom(self, params, verbose=False):

        angm_res = np.zeros((3, self.symbol.multiplicity, self.symbol.multiplicity),
                            dtype='complex128')

        for (term, labs), ops in iter(self):
            if term == "angm_red":
                for key, op in ops:

                    if verbose:
                        print(f"Parametrising {key} of {term}{labs}")

                    angm_res[{'x': 0, 'y': 1, 'z': 2}[getattr(key, 'comp')]] += \
                        (1.0 - params[(term, labs)][key]) * op

        return angm_res

    def project(self, angm, verbose=False):

        def proj(op):
            return jnp.sum(angm * op.conj()).real / jnp.linalg.norm(op)**2

        params = {(term, labs): {key: proj(op) for key, op in ops}
                  for (term, labs), ops in iter(self)}

        self.check_orthogonality()

        return params

    def evaluate_cartan_killing_reduction(self, angm, negative_sign=False):
        metric = cartan_killing_metric(*angm).real
        kappa = (-1 if negative_sign else +1) * jnp.sqrt(jnp.diag(metric) / 2)
        kappa_dict = dict(zip('xyz', kappa))
        params = {(term, labs): {key: kappa_dict[getattr(key, 'comp')] for key, op in ops}
                  for (term, labs), ops in iter(self)}
        return params, kappa



def make_broken_symmetry_exchange_storage(_, eners=None, **kwargs):
    return BrokenSymmExchange(eners, **kwargs)


class BrokenSymmExchange(Store):

    def __init__(self, eners, model_space=None, terms=None, coupling=None,
                 verbose=True, comp_thresh=0.05, field=None, shift=True, units='cm^-1', fmt='% 20.13e'):

        self.eners = eners
        self.model_space = model_space
        self.coupling = coupling

        self.model = BrokenSymmetryHamiltonian(model_space, **terms)
        self.full_model = SpinHamiltonian(model_space, **terms)

        self.verbose = verbose
        self.comp_thresh = comp_thresh
        self.field = field
        self.shift = shift

        super().__init__(
            "parameters",
            "Exchange coupling from a set of broken symmetry states.",
            label=("term", "operators"), units=units, fmt=fmt)

    def print_basis(self, params):

        # expand model space by L=0 for compatibility with evaluate_term_space()
        # model_space = Symbol(self.model_space.coupling | {'L': None}, **self.model_space.qn, L=0)
        basis_space, cg_vecs = couple(self.model_space, **self.coupling)

        hamiltonian = unitary_transform(self.full_model.parametrise(params), cg_vecs) / HARTREE2INVCM
        angm = unitary_transform(self.model_space.get_op("angm"), cg_vecs)
        spin = unitary_transform(self.model_space.get_op("spin"), cg_vecs)

        print_basis(hamiltonian, spin, angm,
                    basis_space, comp_thresh=self.comp_thresh,
                    field=self.field, plot=self.verbose, shift=self.shift,
                    S=spin, L=angm, J=spin + angm)
        return

    def evaluate(self, eners):

        param_dict = self.model.project(eners, verbose=self.verbose)

        if self.verbose:
            self.print_basis(param_dict)

        return list(param_dict.values()), list(param_dict.keys())

    def __iter__(self):
        yield from map(lambda val, lab: (self.format_label(lab), val),
                       *self.evaluate(self.eners))

    def format_label(self, label):
        return (label[0], '_'.join(label[1]))


class BrokenSymmetryHamiltonian(Model):
    """Set up model spin Hamiltonian whose diagonal matrix elements are to be
    fitted to the energies of a set of broken symmetry states.

    Parameters
    ----------
    centre_spins : list of floats
       Spin quantum number of each centre.
    **terms : keyword arguments
        Terms to include in the model Hamiltonian specified as:
            Heisenberg-Dirac-van-Vleck terms: hdvv_ex=[("T", "U"), ("U", "V"), ("V", "T")]
            Lenz-Ising. li=[("T", "U"), ("U", "V"), ("V", "T")]

    """

    def __init__(self, symbol, **terms):

        self.symbol = symbol

        self.terms = {"diag": [()]} | terms

        self.resolve_model_ops = {
            "diag": self._build_diag,
            "hdvv_ex": self._build_hdvv_ex,
            "li_ex": self._build_li_ex
        }

    def _build_diag(self, ops):
        if ops:
            raise ValueError("Inconsistency in building diagonal shift op.")

        Key = namedtuple('shift', '')
        return ((Key(), jnp.ones(self.symbol.multiplicity)),)

    def _build_hdvv_ex(self, ops):

        Key = namedtuple('J', '')
        return ((Key(), reduce(jnp.kron,
                 [jnp.arange(-s, s + 1, 1) if o in ops else jnp.ones(self.symbol.mult[o])
                  for o, s in self.symbol.qn.items()])),)

    def _build_li_ex(self, ops):  # todo: same as hdvv??

        Key = namedtuple('J', '')
        return ((Key(), reduce(jnp.kron,
                 [jnp.arange(-s, s + 1, 1) if o in ops else jnp.ones(self.symbol.mult[o])
                  for o, s in self.symbol.qn.items()])),)

    def project(self, eners, verbose=False):
        """Project ab initio energies onto diagonal elements of model.

        Parameters
        ----------
        eners : dict
            Energies of the high spin and broken symmetry solution. Keys are
            denoting the corresponding determinants, e.g. {'ddu': -123.45}.

        Returns
        -------
        dict of dicts
            Dictionary of terms. Each term is a dictionary itself listing all
            projected model parameters.
        """

        def find_state_index(det):

            def resolve_spin_projection(op, proj):

                if proj == 'u':
                    return self.symbol.qn[op]

                if proj == 'd':
                    return -self.symbol.qn[op]

                raise ValueError(f"Unknown spin projection: {proj}")

            proj_qns = {op: resolve_spin_projection(op, proj)
                        for op, proj in zip(self.symbol.coupling, det)}

            state = self.symbol.make_state(**proj_qns)

            return self.symbol.states.index(state)

        eners = {det: ener * HARTREE2INVCM for det, ener in eners.items()}

        bs_idc, bvec = zip(*[(find_state_index(det), ener) for det, ener in eners.items()])

        Amat = jnp.column_stack([diag[jnp.array(bs_idc)] for _, ops in iter(self) for _, diag in ops])

        param_list, (abs_err,), _, _ = jnp.linalg.lstsq(Amat, jnp.array(bvec))

        param_iter = iter(param_list)
        params = {(term, labs): {key: next(param_iter).real for key, op in ops}
                  for (term, labs), ops in iter(self)}

        if verbose:

            shift = list(params[("diag", ())].values())[0]

            ener_values = jnp.array(list(eners.values())) - shift
            rel_err = abs_err / jnp.linalg.norm(ener_values)
            rmsd = abs_err / jnp.sqrt(len(eners))

            print(f"Absolute err (RMSD, i.e. sqrt[1/N^2 * sum of squared residuals])\n{rmsd:10.4f}")
            print(f"Relative err (sqrt[sum of squared residuals] / norm of ab initio Hamiltonian)\n{rel_err:10.4%}")

            print("Energies of the broken symmetry solution and diagonal elements of the model Hamiltonian (shift substracted):")

            eners_fit = self.parametrise(params, verbose=False)[jnp.array(bs_idc)]

            for (det, ener), ener_fit in zip(eners.items(), eners_fit):
                print(f"|{det}> : {ener - shift} {ener_fit - shift}")

        return params

    def parametrise(self, params, verbose=False):
        return reduce(lambda x, y: x + y,
                      (params[lab][key] * op
                       for lab, ops in iter(self) for key, op in ops))


class SpinHamiltonian(Model):
    """Set up model spin Hamiltonian to be fitted to ab initio Hamiltonian in
    angular momentum basis.
    The model might be composed of: H = V_0 + H_so + H_ex + H_cf
    (V_0: diagonal shift, H_so: spin-orbit coupling, H_ex: exchange coupling,
    H_cf: CF interaction).

    Parameters
    ----------
    symbol : obj
        Symbol object specifying the angular momentum space.
    angm_ops : dict, default = None
        Dictionary of angm operators. Keys are the angm operator labels. If
        omitted, exact operators are used.
    k_max : int, default = 6
        Maximum Stevens operator rank used in crystal field Hamiltonian.
    theta : bool, default = False
        If True, factor out operator equivalent factors theta.
    diag : bool
        If True, include constant diagonal shift term.
    time_reversal_symm : ["even", "odd"], default "even"
        If "even" ("odd"), only include exchange terms which are "even" ("odd")
        under time reversal.
    ion : object, default = None
        Ion object for operator equivalent factor lookup.
    **terms: keyword arguments
        Terms to include in the model Hamiltonian specified as:
            spin-orbit coupling: soc=[("L", "S")]
            crystal field: cf=[("L",)]
            exchange: ex=[("R", "S"), ("R", "L"), ("R", "S", "L")]

    Attributes
    ----------
    symbol : obj
        Symbol object specifying the angular momentum space.
    angm : dict
        Dictionary of angm operators. Keys are the angm operator labels.
    k_max : int
        Maximum Stevens operator rank used in crystal field Hamiltonian.
    theta : bool, default = False
        If true, factor out operator equivalent factors theta.
    ion : object, default = None
        Ion object for operator equivalent factor lookup.
    term_dict : dict of dicts
        Dictionary of terms. Each entry of sub-dict is a contribution to the
        model Hamiltonian associated with a parameter.
    term_len : dict
        Dictionary of number of parameter of each term in model Hamiltonian.
    """

    def __init__(self, symbol, angm_ops=None, ion=None, k_max=6, theta=False,
                 diag=True, time_reversal_symm="even", **terms):

        self.ion = ion
        self.k_max = k_max
        self.theta = theta
        self.time_reversal_symm = time_reversal_symm
        self.diag = diag

        self.terms = ({"diag": [()]} if diag else {}) | terms

        self.resolve_model_ops = {
            "diag": self._build_diag,
            "soc": self._build_soc,
            "aniso_soc": self._build_aniso_soc,
            "cf": self._build_cf,
            "hdvv_ex": self._build_hdvv_ex,
            "aniso_ex": self._build_aniso_ex,
            "ex": self._build_ex,
            "dm": self._build_dm
        }

        super().__init__(symbol)

        self.angm = \
            {o: tuple(angm_ops[o]) + (angm_ops[o][0] + 1.j * angm_ops[o][1],
                                      angm_ops[o][0] - 1.j * angm_ops[o][1],
                                      cartesian_op_squared(angm_ops[o])[0])
             if angm_ops is not None and o in angm_ops else
             calc_ang_mom_ops(self.symbol.qn[o]) for o in self.symbol.coupling.keys()}

    def _build_diag(self, ops):
        if ops:
            raise ValueError("Inconsistency in building diagonal shift op.")

        Key = namedtuple('shift', '')
        return ((Key(), jnp.identity(self.symbol.multiplicity)),)

    def _build_soc(self, ops):

        Key = namedtuple('lamb', '')
        return ((Key(), jnp.sum(jnp.array([
            reduce(jnp.kron,
                   [self.angm[o][c] if o in ops else jnp.identity(m)
                    for o, m in self.symbol.mult.items()])
            for c in range(3)]), axis=0)),)

    def _build_aniso_soc(self, ops):

        Key = namedtuple('lamb', 'component')
        return ((Key(("x", "y", "z")[c]),
                reduce(jnp.kron,
                       [self.angm[o][c] if o in ops else jnp.identity(m)
                        for o, m in self.symbol.mult.items()]))
                for c in range(3))

    def _build_dm(self, ops):
        Key = namedtuple('d', 'component')
        return ((Key(("x", "y", "z")[c]),
                sum((float(LeviCivita(i, j, c)) * reduce(jnp.kron, [self.angm[o][(i, j)[ops.index(o)]] if o in ops else jnp.identity(m)
                     for o, m in self.symbol.mult.items()]) for i in range(3) for j in range(3) if LeviCivita(i, j, c) != Zero)))
                for c in range(3))

    def _build_cf(self, ops):

        op = ops[0]

        if self.k_max > 12:
            warnings.warn("Exclude k > 12 terms from exchange Hamiltonian "
                          "due to numerical instability at double prec!")

        Okq = \
            calc_stev_ops(min(self.k_max, 12), (self.symbol.mult[op] - 1) / 2,
                          self.angm[op][3], self.angm[op][4], self.angm[op][2])

        if not self.theta:
            pass
        elif self.theta and op.upper() in ANGM_SYMBOLS:
            theta = self.ion.theta('l')
        elif self.theta and op.upper() in TOTJ_SYMBOLS:
            theta = self.ion.theta('j')
        else:
            raise ValueError(f"Unknown angular momentum identifier: {op}")

        Key = namedtuple('B', 'k q')
        return ((Key(k, q),
                reduce(jnp.kron,
                       [Okq[k - 1, k + q, ...] *
                        (theta[k] if self.theta else 1.0)
                        if o == op else jnp.identity(m)
                        for o, m in self.symbol.mult.items()]))
                for k in range(2, self.k_max + 1, 2) for q in range(-k, k + 1))

    def _build_hdvv_ex(self, ops):

        Key = namedtuple('J', '')
        return ((Key(), jnp.sum(jnp.array([
            reduce(jnp.kron,
                   [self.angm[o][c] if o in ops else jnp.identity(m)
                    for o, m in self.symbol.mult.items()])
                for c in range(3)]), axis=0)),)

    def _build_aniso_ex(self, ops):

        Key = namedtuple('D', 'comp1 comp2')
        return ((Key(("x", "y", "z")[c1], ("x", "y", "z")[c2]),
                 reduce(jnp.kron,
                        [self.angm[o][(c1, c2)[ops.index(o)]] if o in ops else jnp.identity(m)
                         for o, m in self.symbol.mult.items()]))
                for c1 in range(3) for c2 in range(3))

    def _build_ex(self, ops):

        def time_rev_symm(ranks):
            if self.time_reversal_symm == "even":
                return not sum(ranks) % 2
            elif self.time_reversal_symm == "odd":
                return sum(ranks) % 2
            else:
                return True

        Okqs = {o: calc_stev_ops(
            min(self.symbol.mult[o] - 1, 12), self.symbol.qn[o],
            self.angm[o][3], self.angm[o][4], self.angm[o][2]) for o in ops}

        kdc = (dict(zip(ops, idc))
               for idc in product(*(range(1, min(self.symbol.mult[o], 12 + 1))
                                    for o in ops)))
        for o in ops:
            if self.symbol.mult[o] - 1 > 12:
                warnings.warn("Exclude k > 12 terms from exchange Hamiltonian "
                              "due to numerical instability at double prec!")

        # generator of orders
        def qdc(kdx):
            return (dict(zip(ops, idc))
                    for idc in product(
                        *(range(-k, k + 1) for k in kdx.values())))

        idc = iter([('k', 'q'), ('n', 'm')])
        Key = namedtuple('J', (i for o in ops for i in (("alpha",) if o == 'R'
                                                        else next(idc))))

        return ((Key(*(i for o, kx, qx in zip(ops, k.values(), q.values())
                for i in ((('z', 'x', 'y')[qx],) if o == 'R' else (kx, qx)))),
                (-1) * reduce(jnp.kron,
                              [Okqs[o][k[o] - 1, k[o] + q[o], ...] /
                               (1.0 if o.upper() == 'R' else
                                Okqs[o][k[o] - 1, k[o], -1, -1])  # IC scalar
                               if o in ops else jnp.identity(m)
                               for o, m in self.symbol.mult.items()]))
                for k in kdc for q in qdc(k) if time_rev_symm(k.values()))

    def project_parameters(self, ham, algo='proj'):
        """Project ab initio Hamiltonian onto model.

        Parameters
        ----------
        ham : np.array
            Ab initio Hamiltonian in the appropiate basis. (Ordering according
            to basis_mult argument of constructor.)
        algo: str
            Algorithm to determine model parameter either via true projection
            using the per-operator trace (assumes orthogonality of model
            operators) or a simultaneous linear least squares fit.

        Returns
        -------
        dict of dicts
            Dictionary of terms. Each term is a dictionary itself listing all
            projected model parameters. Sub-keys are Stevens operator rank
            order pairs in the same order as defined in the **terms parameters.
        """

        def proj(op):
            return jnp.sum(ham * op.conj()).real / jnp.linalg.norm(op)**2

        # def orthonorm(op1, op2):
        #     return (np.sum(op1 * op2.conj()) / (np.linalg.norm(op1) * np.linalg.norm(op2))).real

        if algo == 'proj':
            params = {(term, labs): {key: proj(op) for key, op in ops}
                      for (term, labs), ops in iter(self)}

        elif algo == 'lstsq':
            Amat = jnp.column_stack([op.flatten() for _, ops in iter(self) for _, op in ops])
            bvec = ham.flatten()
            param_list = jnp.linalg.lstsq(Amat, bvec)[0].real
            param_iter = iter(param_list)
            params = {(term, labs): {key: next(param_iter) for key, op in ops}
                      for (term, labs), ops in iter(self)}
        else:
            raise ValueError(f"Algorithm {algo} not available!")

        return params

    def compute_error(self, ham, params):

        ham_fit = self.parametrise(params, verbose=False)

        abs_err = jnp.linalg.norm(ham_fit - ham)
        rel_err = abs_err / jnp.linalg.norm(ham)
        rmsd = abs_err / ham.shape[0]

        return abs_err, rel_err, rmsd

    def project(self, ham, verbose=False):
        """Project ab initio Hamiltonian onto model.

        Parameters
        ----------
        ham : np.array
            Ab initio Hamiltonian in the appropiate basis. (Ordering according
            to basis_mult argument of constructor.)
        verbose : bool
            Flag for printing information from least squares fit and plot
            original and fitted Hamiltonian matrices.

        Returns
        -------
        dict of dicts
            Dictionary of terms. Each term is a dictionary itself listing all
            projected model parameters. Sub-keys are Stevens operator rank
            order pairs in the same order as defined in the **terms parameters.
        """

        # print(np.array([[orthonorm(op1, op2) for _, ops1 in iter(self) for _, op1 in ops1] for _, ops2 in iter(self) for _, op2 in ops2]))

        ham = ham * HARTREE2INVCM

        params = self.project_parameters(ham, algo='proj')

        if verbose:
            abs_err, rel_err, rmsd = self.compute_error(ham, params)
            print(self.compute_error(ham, params))

            print(f"Absolute err (RMSD, i.e. sqrt[1/N^2 * sum of squared residuals])\n{rmsd:10.4f}")
            print(f"Relative err (sqrt[sum of squared residuals] / norm of ab initio Hamiltonian)\n{rel_err:10.4%}")

            print("Eigenvalues of the ab initio and model Hamiltonian (diagonal shift substracted):")

            ham_fit = self.parametrise(params, verbose=False)

            shift = list(params[("diag", ())].values())[0] if self.diag else 0.
            diag_shift = shift * jnp.identity(self.symbol.multiplicity)
            eig_a, _ = jnp.linalg.eigh(ham - diag_shift)
            eig_m, _ = jnp.linalg.eigh(ham_fit - diag_shift)

            for i, (a, m) in enumerate(zip(eig_a, eig_m), start=1):
                print(f"{i} {a} {m}")

            ut.plot_op([ham, ham_fit], "h_ai.png", titles=["Ab initio Hamiltonian", "Model fit"])

        return params

    def parametrise(self, params, scale=None, verbose=False):

        ham = jnp.zeros((self.symbol.multiplicity, self.symbol.multiplicity),
                        dtype='complex128')

        for lab, ops in iter(self):
            for key, op in ops:
                if verbose:
                    print(f"Parametrising {key} of {lab[0]}{lab[1]}")
                if scale is None:
                    ham += params[lab][key] * op
                else:
                    ham += params[lab][key] * op * scale.get(lab[0], 1.0)

        return ham
        # return reduce(lambda x, y: x + y,
        #               (params[lab][key] * op
        #                for lab, ops in iter(self) for key, op in ops))

    def compute_projection_norm(self, ham):
        """Measures overlap of model operators with Hamiltonian

        Parameters
        ----------
        ham : np.array
            Ab initio Hamiltonian in the appropiate basis. (Ordering according
            to basis_mult argument of constructor.)

        Returns
        -------
        float
            Value of projection norm.
        """

        # ham = ham * HARTREE2INVCM
        ham_norm = jnp.linalg.norm(ham)

        def proj(op):
            return jnp.sum(ham * op.conj()).real / ham_norm / jnp.linalg.norm(op)

        def generate_projection_norms():
            for (term, labs), ops in iter(self):
                for key, op in ops:
                    yield proj(op)**2

        return sum(generate_projection_norms())


class FromFile:

    def __init__(self, h_file, **kwargs):

        self.h_file = h_file

        with h5py.File(self.h_file, 'r') as h:
            ops = {op: h[op][...] for op in ['hamiltonian', 'spin', 'angm']}

        super().__init__(ops, **kwargs)


class MagneticSusceptibility(Store):

    def __init__(self, ops, temperatures=None, field=None, differential=False,
                 iso=True, powder=False, chi_T=False, units='cm^3 / mol',
                 fmt='% 20.13e'):

        self.ops = ops
        self.temperatures = temperatures

        # basis options
        self.field = field
        self.differential = differential
        self.iso = iso
        self.powder = powder
        self.chi_T = chi_T

        title = "chi_T" if self.chi_T else "chi"
        description = " ".join(["Temperature-dependent"] +
                               (["differential"] if self.differential else []) +
                               (["isotropic"] if self.iso else []) +
                               ["molecular susceptibility"] +
                               (["tensor"] if not self.iso else []) +
                               (["times temperature"] if self.chi_T else []) +
                               [f"at {field} mT"])

        super().__init__(title, description, label=(), units=units, fmt=fmt)

    def evaluate(self, **ops):

        if self.differential:
            tensor_func = partial(susceptibility_tensor,
                                  hamiltonian=ops['hamiltonian'],
                                  spin=ops['spin'], angm=ops['angm'],
                                  field=self.field,
                                  differential=self.differential)
        else:
            tensor_func = make_susceptibility_tensor(
                hamiltonian=ops['hamiltonian'],
                spin=ops['spin'], angm=ops['angm'],
                field=self.field)

        if self.iso:
            def func(temp):
                return jnp.trace(tensor_func(temp)) / 3
        else:
            func = tensor_func

        # vmap does not repeat the eigen decomp
        if self.differential:
            chi_list = [func(temp) for temp in self.temperatures]
        else:  # non-bached more efficient when using the expm backend
            chi_list = [func(temp) for temp in self.temperatures]
            # chi_list = vmap(func)(jnp.array(self.temperatures))

        Key = namedtuple('chi', 'temp')
        data = {Key(temp): (temp * chi) if self.chi_T else chi
                for temp, chi in zip(self.temperatures, chi_list)}
        return [data], [()]

    def __iter__(self):
        yield from ((lab, dat) for dat, lab in zip(*self.evaluate(**self.ops)))


class MagneticSusceptibilityFromFile(FromFile, MagneticSusceptibility):
    pass


class EPRGtensor(Store):

    def __init__(self, ops, multiplets=None, eprg_values=False,
                 eprg_vectors=False, eprg_tensors=False,
                 units='au', fmt='% 20.13e'):

        self.ops = ops

        self.multiplets = multiplets

        self.eprg_values = eprg_values
        self.eprg_vectors = eprg_vectors
        self.eprg_tensors = eprg_tensors

        if self.eprg_values:
            args = ("eprg_values", "Principal values of the EPR G-tensor")
        elif self.eprg_vectors:
            args = ("eprg_vectors", "Principal axes of the EPR G-tensor")
        elif self.eprg_tensors:
            args = ("eprg_tensors", "EPR G-tensor")
        else:
            raise ValueError("Supply one of eprg_values/_vectors/_tensors!")

        super().__init__(*args, label=("doublet",), units=units, fmt=fmt)

    def evaluate(self, **ops):

        eig, vec = jnp.linalg.eigh(ops['hamiltonian'])

        eprg_list = compute_eprg_tensors(
            unitary_transform(ops['spin'], vec),
            unitary_transform(ops['angm'], vec),
            ener=eig, multiplets=self.multiplets
        )

        if self.eprg_tensors:
            data = list(eprg_list)

        else:
            eprg_vals, eprg_vecs = zip(*map(jnp.linalg.eigh, eprg_list))

            if self.eprg_values:
                data = eprg_vals
            elif self.eprg_vectors:
                data = eprg_vecs

        return list(data), [(idx,) for idx, _ in enumerate(data, start=1)]

    def __iter__(self):
        yield from ((lab, dat) for dat, lab in zip(*self.evaluate(**self.ops)))


class EPRGtensorFromFile(FromFile, EPRGtensor):
    pass


class Tint(Store):

    def __init__(self, ops, field=0., states=None, units='au', fmt='% 20.13e'):

        self.ops = ops
        self.field = field
        self.states = states

        super().__init__(
            "tint",
            "Matrix elements of the magnetic dipole transition intensity",
            label=("istate",), units=units, fmt=fmt)

    def evaluate(self, **ops):

        zee = zeeman_hamiltonian(
                ops['spin'], ops['angm'], np.array([0., 0., self.field]))
        _, vec = jnp.linalg.eigh(ops['hamiltonian'] + zee)

        vec_out = vec if self.states is None else vec[:, list(self.states)]

        magm = vec_out.conj().T @ magmom(ops['spin'], ops['angm']) @ vec
        tint = np.sum(np.real(magm * magm.conj()), axis=0) / 3

        Key = namedtuple('jstate', 'index')
        data = [{Key(idx): val for idx, val in enumerate(row, start=1)} for row in tint]
        return data, [(idx,) for idx, _ in enumerate(data, start=1)]

    def __iter__(self):
        yield from ((lab, dat) for dat, lab in zip(*self.evaluate(**self.ops)))


class TintFromFile(FromFile, Tint):
    pass
