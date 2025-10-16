import re
from itertools import product, chain
from functools import reduce, lru_cache
from fractions import Fraction
from collections import namedtuple
import warnings

import numpy as np
import scipy
from jax import numpy as jnp
from jax.scipy.linalg import block_diag, expm, qr
from jax import random, vmap

from sympy.physics.quantum.cg import CG
from sympy.physics.wigner import wigner_3j, wigner_6j
from . import utils as ut
from .group import project_angm, project_SO3_irrep, R3_projector_integral


SPIN_SYMBOLS = ['R', 'S', 'T', 'U', 'V', 'W']
ANGM_SYMBOLS = ['L', 'M', 'N', 'O', 'P', 'Q']
TOTJ_SYMBOLS = ['F', 'G', 'H', 'I', 'J', 'K']


def is_int_or_half_int(x):
    if float(2 * x) != float(int(2 * x)):
        raise ValueError("Non-half-integer argument encountered!")
    return float(x)


def eval_wigner_3j(j1, j2, j3, m1, m2, m3):
    return float(wigner_3j(*map(is_int_or_half_int, (j1, j2, j3, m1, m2, m3))))


def eval_wigner_6j(j1, j2, j3, j4, j5, j6):
    return float(wigner_6j(*map(is_int_or_half_int, (j1, j2, j3, j4, j5, j6))))


def cart_comps(sph):
    return np.array([(-sph[2] + sph[0]) / np.sqrt(2),  # x
                     1.j * (sph[2] + sph[0]) / np.sqrt(2),  # y
                     sph[1]])  # z


def sph_comps(cart):
    return np.array([(cart[0] - 1.j * cart[1]) / np.sqrt(2),  # q = -1
                     cart[2],  # q = 0
                     -(cart[0] + 1.j * cart[1]) / np.sqrt(2)])  # q = +1


def sf2ws(sf_op, sf_mult):

    def expand(op, mult):
        return jnp.kron(op, np.identity(mult))

    return from_blocks(*map(expand, sf_op, sf_mult))


def ws2sf(ws_op, sf_mult):

    def collapse(spin_blk, mult, dim):

        def _collapse(spin_blk):
            blks = spin_blk.reshape((dim, mult, dim, mult))
            return vmap(vmap(lambda blk: jnp.mean(jnp.diag(blk)), 1, 0), 0, 0)(blks)

        if len(spin_blk.shape) > 2:
            return vmap(_collapse)(spin_blk)
        return _collapse(spin_blk)

    spin_labs = [mult for mult, dim in sf_mult.items() for _ in range(dim * mult)]
    spin_blks = extract_blocks(ws_op, spin_labs, spin_labs)
    return list(map(collapse, spin_blks, sf_mult.keys(), sf_mult.values()))


def sf2ws_spin(sf_op, sf_smult):

    def me(s1, ms1, sf1, s2, ms2, sf2):
        if jnp.abs(s1 - s2) <= 2 and jnp.abs(ms1 - ms2) <= 2:
            return coeff(s1, ms1, s2, ms2) * op(s1, ms1, sf1, s2, ms2, sf2)
        else:
            return 0.0

    def op(s1, ms1, sf1, s2, ms2, sf2):

        if jnp.abs(s1 - s2) <= 2:
            if ms1 == ms2:
                return sf_op[2, sf1, sf2]
            elif ms1 + 2 == ms2:
                return (+ sf_op[0, sf1, sf2] + 1.j * sf_op[1, sf1, sf2])
            elif ms1 - 2 == ms2:
                return (- sf_op[0, sf1, sf2] + 1.j * sf_op[1, sf1, sf2])
            else:
                return 0.0
        else:
            return 0.0

    def coeff(s1, ms1, s2, ms2):
        # double integer figures and extra "/ 2" factor in common factor due 2
        # double quantum number convention

        if s1 == s2:
            if s1 == 0:
                return 0.0
            elif ms1 == ms2:
                c = ms1
            elif ms1 + 2 == ms2:
                c = + jnp.sqrt((s1 - ms1) * (s1 + ms1 + 2)) / 2
            elif ms1 - 2 == ms2:
                c = - jnp.sqrt((s1 + ms1) * (s1 - ms1 + 2)) / 2
            else:
                c = 0.0
            return c / jnp.sqrt(s1 * (s1 + 2) * (2 * s1 + 2) / 2)

        elif s1 + 2 == s2:
            if ms1 == ms2:
                c = jnp.sqrt((s1 + 2)**2 - ms1**2)
            elif ms1 + 2 == ms2:
                c = - jnp.sqrt((s1 + ms1 + 2) * (s1 + ms1 + 4)) / 2
            elif ms1 - 2 == ms2:
                c = - jnp.sqrt((s1 - ms1 + 2) * (s1 - ms1 + 4)) / 2
            else:
                c = 0.0
            return c / jnp.sqrt((s1 + 1) * (2 * s1 + 1) * (2 * s1 + 3) / 2)
        
        elif s1 - 2 == s2:
            if ms1 == ms2:
                c = jnp.sqrt(s1**2 - ms1**2)
            elif ms1 + 2 == ms2:
                c = jnp.sqrt((s1 - ms1) * (s1 - ms1 - 2)) / 2
            elif ms1 - 2 == ms2:
                c = jnp.sqrt((s1 + ms1) * (s1 + ms1 - 2)) / 2
            else:
                c = 0.0
            return c / jnp.sqrt(s1 * (2 * s1 - 1) * (2 * s1 + 1) / 2)

        else:
            return 0.0

    if sf_op is None:
        ws_op = None

    else:
        ws_op = jnp.array([
            [me(s1, ms1, sf1, s2, ms2, sf2) for s2, ms2, sf2 in zip(
                [m - 1 for m in sf_smult for _ in range(m)],
                [- (m - 1) + 2 * i for m in sf_smult for i in range(m)],
                [i for i, m in enumerate(sf_smult) for _ in range(m)])
             ] for s1, ms1, sf1 in zip(
                [m - 1 for m in sf_smult for _ in range(m)],
                [- (m - 1) + 2 * i for m in sf_smult for i in range(m)],
                [i for i, m in enumerate(sf_smult) for _ in range(m)])
            ])

    return ws_op


def wigner_eckard_expand(red, j1, j2, k, q):
    return jnp.array([[(-1)**(j1-m1) * eval_wigner_3j(j1, k, j2, -m1, q, m2)
                       for m2 in np.arange(-j2, j2 + 1, 1)]
                      for m1 in np.arange(-j1, j1 + 1, 1)], dtype="float64") * red


def sf2ws_amfi(sf_op, sf_mult):

    @lru_cache
    def coeff(q, s1, s2):
        # extra minus sign to ensure hermiticity
        return jnp.array([[(-1)**(s2 + m1 - 1) * (-1.0 if s2 > s1 else 1.0) *
                           eval_wigner_3j(s2, 1, s1, m2, q, -m1)
                           for m2 in np.arange(-s2, s2 + 1, 1)]
                          for m1 in np.arange(-s1, s1 + 1, 1)])

    def expand(op, mult1, mult2):

        s1, s2 = (mult1 - 1) / 2, (mult2 - 1) / 2

        if abs(s1 - s2) <= 1:
            spherical_components = jnp.array([
                jnp.kron(op[0] + 1.j * op[1], coeff(-1, s1, s2)) / jnp.sqrt(2),
                jnp.kron(op[2], coeff(0, s1, s2)),
                -jnp.kron(op[0] - 1.j * op[1], coeff(+1, s1, s2)) / jnp.sqrt(2)
            ])

            return jnp.sum(spherical_components, axis=0)
        else:
            return jnp.zeros((mult1 * op.shape[1], mult2 * op.shape[2]))

    # introduce imaginary unit
    return jnp.block([[expand(1.j * op, mult1, mult2)
                       for mult2, op in zip(sf_mult, row)]
                      for mult1, row in zip(sf_mult, sf_op)])


def wigner_eckart_reduce(tensor, j1, j2, k, q=None, full=False, rtol=1e-5, atol=1e-8):

    # Wigner-Eckart coefficients
    def we_coeffs(q):
        return np.array([[(-1)**(j1 - m1) * float(wigner_3j(j1, k, j2, -m1, q, m2))
                          for m2 in np.linspace(-j2, j2, int(2 * j2 + 1))]
                         for m1 in np.linspace(-j1, j1, int(2 * j1 + 1))])

    if q is None:
        q_range = range(-k, k + 1) if full else range(k)
        we = np.array([we_coeffs(q) for q in q_range])
    else:
        we = we_coeffs(q)

    j_sum = j1 + k + j2

    if not (abs(j1 - k) <= j2 and j2 <= (j1 + k) and
            (isinstance(j_sum, int) or j_sum.is_integer())):
        return 0.0

    # Non-zero reduced elements
    red = tensor[we != 0] / we[we != 0]
    red_mean = np.mean(red)

    if not np.allclose(red, red_mean, rtol=rtol, atol=atol):
        warnings.warn(f"Non-zero WE-reduced elements are not equal: {red}")

    return red_mean


def we_reduce_blocks(tensor, symbols, rtol=1e0, atol=1e-1):

    coupling = symbols[0].coupling

    if all(symbol.coupling == coupling for symbol in symbols):
        jlab, = coupling.keys()
    else:
        raise ValueError("Inhomogenious angmom space!")

    states = [state for sym in symbols for state in sym.states]
    ops = states[0]._fields

    labs = [tuple(getattr(state, op) for op in ops if op != jlab + 'z')
            for state in states]

    # extract operator matrix blocks
    blks = dissect_array(jnp.array(tensor), labs, labs, ordered=True)

    # get unique quantum numbers
    qns = list(dict.fromkeys(getattr(state, jlab + '2') for state in states))

    rank = len(tensor) // 2
    q_list = tuple(range(-rank, rank + 1))

    red = np.moveaxis([[[wigner_eckart_reduce(tensor, j1, j2, 1, q=q,
                                              rtol=rtol, atol=atol)
                         for q, tensor in zip(q_list, tensors)]
                        for j2, tensors in zip(qns, row)]
                       for j1, row in zip(qns, blks)], 2, 0)
    return red


def we_reduce_term_blocks(tensor, states, j_list, q_list, rtol=1e0, atol=1e-1):

    proj_idx = states[0]._fields.index(j_list[0] + 'z')

    order = [states[0]._fields.index(j + 'z') for j in reversed(j_list)]
    if sorted(order) != order:
        raise ValueError("Wrong basis ordering in WE-reduction!")

    State = namedtuple('state', [op for idx, op in enumerate(states[0]._fields)
                                 if idx != proj_idx])
    labs = [State(*(qn for idx, qn in enumerate(state) if idx != proj_idx))
            for state in states]

    if q_list[0] is None:  # Skip reduction step
        red = tensor
    else:
        qn_idx = states[0]._fields.index(j_list[0] + '2')
        qns = list(zip(*list(dict.fromkeys(labs))))[qn_idx]
        blks = dissect_array(jnp.array(tensor), labs, labs, ordered=True)

        red = np.moveaxis([[[wigner_eckart_reduce(tensor, j1, j2, 1, q=q,
                                                  rtol=rtol, atol=atol)
                             for q, tensor in zip(q_list[0], tensors)]
                            for j2, tensors in zip(qns, row)]
                           for j1, row in zip(qns, blks)], 2, 0)

    if len(j_list) > 1:
        _states = list(dict.fromkeys(labs))
        return we_reduce_term_blocks(red, _states, j_list[1:], q_list[1:],
                                     rtol=rtol, atol=atol)

    return red


# def we_reduce_hso_tensor(hso_tensor, terms, spin_only=False, angm_only=False):
#     """Reduce H_so tensor = [L(-1) S(+1), L(0) S(0), L(+1) S(-1)] to
#     (spherical) reduced matrix elements to be averaged"""

#     if not angm_only:

#         spin_labs = [(term.qn['S'], term.qn['L'], m) for term in terms
#                      for m in range(-term.qn['L'], term.qn['L'] + 1)
#                      for _ in range(term.mult['S'])]

#         unique_spin_labs = list(dict.fromkeys(spin_labs))

#         hso_tensor_blks = dissect_array(hso_tensor, spin_labs, spin_labs)

#         hso_spin_red = np.moveaxis([[[wigner_eckart_reduce(tensor, s_row, s, 1, q=q)
#                                       for q, tensor in zip([1, 0, -1], tensors)]
#                                      for (s, _, _), tensors in zip(unique_spin_labs, row)]
#                                     for (s_row, _, _), row in zip(unique_spin_labs, hso_tensor_blks)], 2, 0)

#     if spin_only:
#         return hso_spin_red

#     if angm_only:
#         hso_spin_red = hso_tensor

#     angm_labs = [(term.qn['S'], term.qn['L']) for term in terms
#                  for m in range(-term.qn['L'], term.qn['L'] + 1)]

#     hso_spin_red_blks = dissect_array(hso_spin_red, angm_labs, angm_labs)

#     hso_angm_red = np.moveaxis([[[wigner_eckart_reduce(tensor, row_term.qn['L'], term.qn['L'], 1, q=q)
#                                   for q, tensor in zip([-1, 0, 1], tensors)]
#                                  for term, tensors in zip(terms, row)]
#                                 for row_term, row in zip(terms, hso_spin_red_blks)], 2, 0)

#     return hso_angm_red


def sfy(fun, sf=0):
    if sf == 0:
        return fun
    else:
        return lambda *x: list(map(lambda *y: sfy(fun, sf=sf - 1)(*y), *x))


def unitary_transform(op, Umat, sf=0):
    if sf == 0:
        return Umat.conj().T @ op @ Umat
    elif sf == 1:
        return list(map(unitary_transform, op, Umat))
    elif sf == 2:
        return [[u.conj().T @ o @ w for o, w in zip(row, Umat)]
                for row, u in zip(op, Umat)]
    else:
        raise ValueError(f"Invalid sf={sf} argument.")


def cartesian_op_squared(op):
    return jnp.sum(op @ op, axis=0)


def rotate_cart(op, rot_mat):
    return np.einsum('ji,imn->jmn', rot_mat, op)


def unique_labels(labs, ordered=False):

    if ordered:  # preserve order
        return list(dict.fromkeys(labs))

    # determine canonical order
    return np.unique(labs, axis=0)


def dissect_array(mat, *blk_labs, ordered=False, axes=None):

    ndim = len(mat.shape)

    for ulab in unique_labels(blk_labs[0], ordered=ordered):

        slice_idc = np.flatnonzero([np.all(lab == ulab) for lab in blk_labs[0]])

        if axes is None:
            idc = tuple(slice_idc if ndim - i == len(blk_labs) else slice(None)
                        for i in range(ndim))
        else:
            idc = tuple(slice_idc if i == axes[0] else slice(None)
                        for i in range(ndim))

        _mat = mat[idc]

        if len(blk_labs) > 1:
            yield dissect_array(_mat, *blk_labs[1:], ordered=ordered, axes=axes)
        else:
            yield _mat


def extract_blocks(mat, *blk_labs, ordered=False):
    for ulab in unique_labels(blk_labs[0], ordered=ordered):
        idc = [np.flatnonzero([lab == ulab for lab in labs])
               for labs in blk_labs]
        yield mat[(...,) + np.ix_(*idc)]


def from_blocks(*blocks):
    """Generalisation of scipy.block_diag for multi-component operators.
    """
    try:
        return block_diag(*blocks)
    except ValueError:
        return jnp.array([from_blocks(*comps) for comps in zip(*blocks)])


def build_random_unitary(dim, key_dict={"key": random.key(42)}):
    # uses mutable keyword argument to propagate new key
    newkey, subkey = random.split(key_dict["key"])
    key_dict["key"] = newkey
    return random.orthogonal(subkey, dim, dtype=complex)


def phase(op, sgn="pos"):

    angles = jnp.angle(jnp.diag(op, k=-1))

    Amat = jnp.diag(jnp.concatenate([-jnp.ones(angles.size)]), k=1) + \
        jnp.diag(jnp.ones(angles.size + 1))

    phase_ang = jnp.linalg.solve(Amat, jnp.append(-angles, 0))

    return jnp.diag(jnp.exp(1.j * phase_ang))


def calc_ang_mom_ops(J):
    """
    Calculates the angular momentum operators jx jy jz jp jm j2

    Parameters
    ----------
    J : float
        J quantum number

    Returns
    -------
    np.array
        Matrix representation of jx angular momentum operator
    np.array
        Matrix representation of jy angular momentum operator
    np.array
        Matrix representation of jz angular momentum operator
    np.array
        Matrix representation of jp angular momentum operator
    np.array
        Matrix representation of jm angular momentum operator
    np.array
        Matrix representation of j2 angular momentum operator
    """

    # Create vector of mj values
    mj = np.arange(-J, J + 1, 1, dtype=np.complex128)

    # jz operator - diagonal in jz basis- entries are mj
    jz = np.diag(mj)

    # jp and jm operators
    jp = np.array([[np.sqrt(J * (J + 1) - m2 * (m2 + 1)) if m1 == m2+1 else 0.0
                    for it2, m2 in enumerate(mj)]
                   for it1, m1 in enumerate(mj)])

    jm = np.array([[np.sqrt(J * (J + 1) - m2 * (m2 - 1)) if m1 == m2-1 else 0.0
                    for it2, m2 in enumerate(mj)]
                   for it1, m1 in enumerate(mj)])

    # jx, jy, and j2
    jx = 0.5 * (jp + jm)
    jy = 1. / (2. * 1j) * (jp - jm)
    j2 = jx @ jx + jy @ jy + jz @ jz

    return jx, jy, jz, jp, jm, j2


def make_angmom_ops_from_mult(mult):
    """
    Calculates the angular momentum operators jx jy jz jp jm j2 for a manifold
    of multiplicities. The resulting operator take block diagonal shape.

    Parameters
    ----------
    mult : list
        Array of multiplicities.

    Returns
    -------
    np.array
        Matrix representation of jx angular momentum operator
    np.array
        Matrix representation of jy angular momentum operator
    np.array
        Matrix representation of jz angular momentum operator
    np.array
        Matrix representation of jp angular momentum operator
    np.array
        Matrix representation of jm angular momentum operator
    np.array
        Matrix representation of j2 angular momentum operator
    """

    j = np.block([[
        np.array(calc_ang_mom_ops((smult1 - 1) / 2)[0:3]) if idx1 == idx2 else
        np.zeros((3, smult1, smult2))
        for idx2, smult2 in enumerate(mult)]
        for idx1, smult1 in enumerate(mult)])

    j2 = cartesian_op_squared(j)

    return j[0], j[1], j[2], j[0] + 1.j * j[1], j[0] - 1.j * j[1], j2


def print_sf_term_content(sf_angm, sf_eners, spin_mult, max_angm=13):

    term_composition = \
        [{Term(L=qn, S=(mult - 1) / 2): np.diag(project_angm(qn, cartesian_op_squared(angm))).real
                for qn in range(max_angm)}
         for mult, angm in zip(spin_mult, sf_angm)]

    print("Spin-free section:")
    for mult, composition, eners in zip(spin_mult, term_composition, sf_eners):
        print(f"S = {(mult-1)/2}")
        print_terms(composition, eners)


def print_so_term_content(so_spin, so_angm, eners, spin_mults, max_angm=13):

    def mult2qn(mult):
        return (mult - 1) / 2

    def make_proj(j_ops):
        @lru_cache
        def partial_func(qn):
            return project_angm(qn, cartesian_op_squared(j_ops))
        return partial_func

    proj_spin, proj_angm, proj_totj = \
        map(make_proj, [so_spin, so_angm, so_spin + so_angm])

    term_composition = \
        {Level(S=spin_qn, L=angm_qn, J=totj_qn, coupling={'J': (('L', None), ('S', None))}):
         np.diag(proj_totj(totj_qn) @ proj_angm(angm_qn) @ proj_spin(spin_qn)).real
         for spin_qn in map(mult2qn, spin_mults)
         for angm_qn in range(max_angm)
         for totj_qn in np.arange(np.abs(angm_qn - spin_qn), angm_qn + spin_qn + 1)}

    print("Spin-orbit section:")
    print_terms(term_composition, eners)


def print_terms(composition, eners):

    print("=" * 33)
    print("Term composition:")
    print("-" * 33)
    for term, comp in composition.items():
        content = ' + '.join([f"{contr:4.2f}|{idx}>" for idx, contr in
                              enumerate(comp, start=1) if contr > 0.1])
        count = np.sum(comp) / (term.mult['J'] if isinstance(term, Level) else term.mult['L'])
        if count > 0.1:
            print(f"{count:4.2f} |{term}> = {content}")
    print("=" * 33)
    print("State composition:")
    print("-" * 33)
    for state, ener in enumerate(eners):
        content = ' + '.join([f"{comp[state]:4.2f}|{term}>"
                              for term, comp in composition.items()
                              if comp[state] > 0.1])
        print(f"|State {state+1:3d}> ({ener:8.2f}) = {content}")
    print("=" * 33)


def block_triangular_expm(A, B, C, t):
    n = A.shape[0]
    idc = np.ix_(range(0, n), range(n, 2 * n))
    blk = jnp.block([[A, B], [jnp.zeros((n, n)), C]])
    return expm(t * blk)[idc]


def integrate_expm(A, t):
    n = A.shape[0]
    return block_triangular_expm(A, jnp.identity(n), jnp.zeros((n, n)), t)


def project_function_basis(terms, **chain):

    def generate_projector(term, m):
        for lab, ops in chain.items():
            if lab == 'L':
                yield project_SO3_function(ops, term.qn['L'], m)
            else:
                raise NotImplementedError("Only SO(3) implemented!")

    def project_SO3_function(ops, l, m):
        proj = R3_projector_integral(l, m, m, ops)
        return proj

    def evaluate_basis(term):

        # norm = np.sqrt(np.diag(reduce(np.matmul, generate_projector(term, term.qn['L']))))

        def evaluate_basis_function(m):
            proj = reduce(np.matmul, generate_projector(term, m))
            vec, _, _ = scipy.linalg.svd(proj)
            return vec[:, :1]

        basis = np.hstack([evaluate_basis_function(m)
                           for m in range(-term.qn['L'], term.qn['L'] + 1)])
        vecs = orthonormalise(basis)
        ph_vecs = phase(unitary_transform(chain['L'][0], vecs))
        return vecs @ ph_vecs

    if terms:
        # non-ortogonal basis
        basis = np.hstack(list(map(evaluate_basis, terms)))
        # Orthonormalise
        return orthonormalise(basis)
        # return basis
    else:
        return jnp.empty((chain['L'].shape[1], 0))


def orthonormalise(basis, method="svd"):
    if method == "svd":
        vec, _, wech = scipy.linalg.svd(basis)
        vecs = vec @ np.eye(*basis.shape) @ wech
    elif method == "qr":
        vecs, _ = np.linalg.qr(basis)

    return vecs


def project_irrep_basis(symbols, **chain):

    if not symbols:  # if symbols is the empty list
        return jnp.empty((next(iter(chain.values())).shape[-1], 0))

    coupling = symbols[0].coupling

    if all(symbol.coupling == coupling for symbol in symbols):
        jlab, = coupling.keys()
    else:
        raise ValueError("Inhomogenious angmom space!")

    def generate_projectors(symbol):
        for lab, ops in chain.items():
            if lab == 'L':
                yield project_SO3_function(ops, symbol.qn['L'])
            elif lab == 'J': # and symbol.qn['J'] % 2 == 0:
                yield project_SO3_function(ops, symbol.qn['J'])
            else:
                raise NotImplementedError("Only SO(3) implemented!")

    def project_SO3_function(ops, j):
        proj = np.sum([R3_projector_integral(j, m, m, ops)
                       for m in np.arange(-j, j + 1)], axis=0)
        return proj

    def evaluate_basis(symbol):
        proj = reduce(np.matmul, generate_projectors(symbol))
        vec, _, _ = scipy.linalg.svd(proj)

        irrep_vec = vec[:, :symbol.multiplicity]
        eig, diag_vec = np.linalg.eigh(unitary_transform(chain[jlab][2], irrep_vec))
        ph_vec = phase(unitary_transform(chain[jlab][0], irrep_vec @ diag_vec))

        return irrep_vec @ diag_vec @ ph_vec

    # non-ortogonal basis
    basis = np.hstack(list(map(evaluate_basis, symbols)))
    # Orthonormalise
    return orthonormalise(basis)


def project_angm_basis(terms, angm, complete=False):

    try:
        # orthogonal projection operator into subspace of irrep j
        j = next(terms).qn['L']
        proj = project_angm(j, cartesian_op_squared(angm))
        _, _, perm = scipy.linalg.qr(proj, pivoting=True)
        # proj_vec, r = qr(proj[:, jnp.argsort(-jnp.diag(proj))])
        proj_vec, r = qr(proj[:, perm])

        # split basis of irrep space from its orthogonal complement
        irrep_vec, compl_vec = proj_vec[:, :(2*j + 1)], proj_vec[:, (2*j + 1):]

        # diagonalise z-component + phase x-component
        _, diag_vec = jnp.linalg.eigh(unitary_transform(angm[2], irrep_vec))

        ph_vec = phase(unitary_transform(angm[0], irrep_vec @ diag_vec))

        irrep_basis = irrep_vec @ diag_vec @ ph_vec
        compl_basis = project_angm_basis(
            terms, unitary_transform(angm, compl_vec), complete=complete)

        return jnp.hstack([irrep_basis, compl_vec @ compl_basis])

    except StopIteration:
        if complete:
            return jnp.identity(angm.shape[1])
        else:
            return jnp.empty((angm.shape[1], 0))


def perturb_doublets(ener, totj):
    """Quantise Kramers doublets along z-axis by rotating each doublet into
    eigenstates of Jz.

    Parameters
    ----------
    ener : np.array
        Array of SO energies in hartree.
    totj : np.array
        Total angular momentum operator.

    Returns
    -------
        Transformation matrix which quantises angular momentum states
        by rotating Kramers doublets into eigenstates of Jz at zero field.
    """

    @np.vectorize
    def round_significant_digits(x, **kwargs):
        return np.format_float_positional(
            x, unique=False, fractional=False, trim='k', **kwargs)

    labs = round_significant_digits(ener, precision=8)
    totj_blks = extract_blocks(totj[2], labs, labs, ordered=True)
    vec = from_blocks(*map(lambda jz: np.linalg.eigh(jz)[1], totj_blks))

    return vec


class Symbol:

    def __init__(self, coupling=None, **qn):

        if coupling is None:
            self.coupling = {op: None for op in qn}
        else:
            self.coupling = {op: coupling[op] for op in qn if op in coupling}

        self.qn = qn

        self.mult = {op: int(2 * qn) + 1 for op, qn in qn.items()
                     if op in self.coupling}

        self.multiplicity = reduce(lambda x, y: x * y, self.mult.values())

        self.basis = [op + comp for op in self.qn for comp in ('2', 'z')
                      if comp == '2' or op in self.coupling]

    def elementary_ops(self, group=None):

        if not (group == 'spin' or group == 'angm' or group is None):
            raise ValueError(f'Invalid group argument {group}!')

        def generate_leaves(op):
            match op:
                case (j, None):
                    if group is None:
                        yield j
                    elif group == 'spin' and j.upper() in SPIN_SYMBOLS:
                        yield j
                    elif group == 'angm' and j.upper() in ANGM_SYMBOLS:
                        yield j

                case (j, (j1, j2)):
                    yield from generate_leaves(j1)
                    yield from generate_leaves(j2)

        return list(chain(*map(generate_leaves, self.coupling.items())))

    @property
    def states(self):
        State = namedtuple('state', self.basis)
        func = {
            '2': lambda o: (self.qn[o],),
            'z': lambda o: np.linspace(-self.qn[o], self.qn[o], self.mult[o])
        }
        return [State(*qns) for qns in product(
            *(func[comp](op) for op, comp in self.basis))]

    def make_state(self, **proj_qns):
        State = namedtuple('state', self.basis)
        return State(*(proj_qns[op] if comp == 'z' else self.qn[op] for op, comp in self.basis))

    def get_op(self, op):

        if op == "spin":
            spin_ops = self.elementary_ops('spin')
            if not spin_ops:
                return np.zeros((3, self.multiplicity, self.multiplicity))
            return np.sum([self.get_op(op) for op in spin_ops], axis=0)

        if op == "angm":
            angm_ops = self.elementary_ops('angm')
            if not angm_ops:
                return np.zeros((3, self.multiplicity, self.multiplicity))
            return np.sum([self.get_op(op) for op in angm_ops], axis=0)

        if op == "totj":
            return np.sum([self.get_op(op) for op in self.elementary_ops()], axis=0)

        if op not in self.qn.keys():
            raise ValueError(f"Angular momentum label {op} is undefined!")

        k = 1

        def get_red(cplg):

            j, j1j2 = cplg
            j_qn = self.qn[j]

            if j == op:
                return jnp.sqrt(j_qn * (j_qn + 1) * (2 * j_qn + 1))

            if j1j2 is None:
                return None

            j1, j2 = j1j2
            j1_qn, j2_qn = self.qn[j1[0]], self.qn[j2[0]]

            if (red1 := get_red(j1)) is not None:
                return (-1)**(j1_qn + j2_qn + j_qn + k) * (2 * j_qn + 1) * \
                    eval_wigner_6j(j_qn, k, j_qn, j1_qn, j2_qn, j1_qn) * red1

            if (red2 := get_red(j2)) is not None:
                return (-1)**(j1_qn + j2_qn + j_qn + k) * (2 * j_qn + 1) * \
                    eval_wigner_6j(j_qn, k, j_qn, j2_qn, j1_qn, j2_qn) * red2

            return None

        def expand_op(red, j):

            if red is None:
                return jnp.identity(self.mult[j])

            j_qn = self.qn[j]

            return cart_comps([wigner_eckard_expand(red, j_qn, j_qn, k, q)
                               for q in [-1, 0, 1]])

        return reduce(jnp.kron, [expand_op(get_red((j, j1j2)), j)
                                 for j, j1j2 in self.coupling.items()])


    def couple(self, j, j1, j2, levels=None):

        levels = levels or self.levels(j, j1, j2)

        # j1, m1, j2, m2 - order does not matter, only introduces phase factor
        uncpld_basis = [j + comp for j, comp in product((j1, j2), ('2', 'z'))]
        cpld_basis = [j + comp for comp in ('2', 'z')]
        extra_basis = [op for op in self.basis if op not in uncpld_basis]

        def qns(uncpld_state, cpld_state):
            j1m1j2m2 = tuple(getattr(uncpld_state, op) for op in uncpld_basis)
            jm = tuple(getattr(cpld_state, op) for op in cpld_basis)
            return j1m1j2m2 + jm

        def equal_extra(uncpld_state, cpld_state):
            for op in extra_basis:
                yield getattr(uncpld_state, op) == getattr(cpld_state, op)

        cg_vec = jnp.array(
            [[float(CG(*qns(uncpld, cpld)).doit())
              if all(equal_extra(uncpld, cpld)) else 0.0
              for lvl in levels for cpld in lvl.states]
             for uncpld in self.states])

        return levels, cg_vec

    def levels(self, j, j1, j2, cls=None):

        qn1, qn2 = self.qn[j1], self.qn[j2]

        cplg = {o: c for o, c in self.coupling.items() if o not in (j1, j2)} \
            | {j: ((j1, self.coupling[j1]), (j2, self.coupling[j2]))}

        uncpld_qn = {op: qn for op, qn in self.qn.items() if op not in cplg}
        cpld_qn = [{op: qn if op == j else self.qn[op] for op in cplg}
                   for qn in np.arange(np.abs(qn1 - qn2), qn1 + qn2 + 1)]

        if cls is None:
            cls = Symbol

        return [cls(coupling=cplg, **uncpld_qn, **cpld) for cpld in cpld_qn]

    def rotate(self, rot, space=None):
        totj = np.sum([self.get_op(o) for o in space or self.coupling], axis=0)
        return rotation_operator(totj, rot)

    def reduce(self, ops=None, cls=None, return_perm=False):

        if cls is None:
            cls = Symbol

        red = cls(**{op: self.qn[op] for op in ops or self.coupling})
        ori = [tuple(getattr(state, op) for op in red.basis) for state in self.states]
        perm = [ori.index(tuple(getattr(state, op) for op in red.basis))
                for state in red.states]

        if return_perm:
            return red, perm
        else:
            return red

    def __contains__(self, other):
        return all(self.qn[key] == val for key, val in other.qn.items())

    def __str__(self):
        qn_str = ', '.join(f"{op}={qn}" for op, qn in self.qn.items())
        return f'{self.__class__.__name__}({qn_str})'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.coupling},**{self.qn})'

    def __eq__(self, other):
        return all(other.qn[lab] == qn for lab, qn in self.qn.items())

    def __hash__(self):
        return hash(tuple(self.qn.items()))

    def __mul__(self, other):
        return Symbol(coupling=self.coupling | other.coupling, **self.qn, **other.qn)


def rotation_operator(j_ops, rot):
    return expm(-1.j * np.einsum('i,ijk->jk', rot.as_rotvec(), j_ops))


def couple(space, **coupling):

    if coupling:

        j, (j1, j2) = coupling.popitem()
        lvls, cg_vec = couple(space, **coupling)

        level_blks, cg_vec_blks = zip(*[lvl.couple(j, j1, j2) for lvl in lvls])

        return ([lvl for blk in level_blks for lvl in blk],
                cg_vec @ block_diag(*cg_vec_blks))

    else:
        return [space], jnp.identity(space.multiplicity)


spec2angm = {
    'S': 0, 'P': 1, 'D': 2, 'F': 3, 'G': 4, 'H': 5, 'I': 6, 'K': 7,
    'L': 8, 'M': 9, 'N': 10, 'O': 11, 'Q': 12, 'R': 13
}

angm2spec = {
    0: 'S', 1: 'P', 2: 'D', 3: 'F', 4: 'G', 5: 'H', 6: 'I', 7: 'K',
    8: 'L', 9: 'M', 10: 'N', 11: 'O', 12: 'Q', 13: 'R'
}


class Term(Symbol):

    def __init__(self, coupling=None, **qn):
        super().__init__(coupling=coupling, **qn)
        self.spin_mult = 2 * self.qn['S'] + 1
        self.orb_letter = angm2spec[self.qn['L']]

    def levels(self, j='J', j1='L', j2='S'):
        return super().levels(j, j1, j2, cls=Level)

    @classmethod
    def parse(cls, symbol_str, spin_major=True):
        m = re.match(r'(?P<S>\d+)(?P<L>[A-Z])$', symbol_str)

        if m:
            d = m.groupdict()
        else:
            raise ValueError("Expected form like 6H.")

        if spin_major:
            return cls(L=spec2angm[d['L']], S=(int(d['S']) - 1) / 2)
        else:
            return cls(S=(int(d['S']) - 1) / 2, L=spec2angm[d['L']])

    def __str__(self):
        return ''.join(map(str, [self.mult['S'], self.orb_letter]))

    def __repr__(self):
        return f'Term({self.mult["S"]},{self.orb_letter})'


class Level(Symbol):

    def __init__(self, coupling=None, **qn):

        if 'J' not in coupling:
            raise ValueError("Level needs to include J-coupling!")

        super().__init__(coupling=coupling, **qn)
        self.spin_mult = 2 * self.qn['S'] + 1
        self.orb_letter = angm2spec[self.qn['L']]

    @classmethod
    def parse(cls, symbol_str, spin_major=True):
        m = re.match(r'(?P<S>\d+)(?P<L>[A-Z])(?P<Jn>\d+)(?:\/(?P<Jd>\d+))?$',
                     symbol_str)
        if m:
            d = m.groupdict()
        else:
            raise ValueError("Expected form like 6H15/2.")

        if spin_major:
            return cls(coupling={'J': (('L', None), ('S', None))},
                       S=(int(d['S']) - 1) / 2, L=spec2angm[d['L']],
                       J=int(d['Jn']) / (int(d['Jd'] or 1)))
        else:
            return cls(coupling={'J': (('S', None), ('L', None))},
                       L=spec2angm[d['L']], S=(int(d['S']) - 1) / 2,
                       J=int(d['Jn']) / (int(d['Jd'] or 1)))

    def __str__(self):
        return ''.join(map(str, [
            int(2 * self.qn['S']) + 1,
            self.orb_letter,
            Fraction(self.qn['J'])]))

    def __repr__(self):
        print(self.mult)
        return f'Level({self.spin_mult},{self.orb_letter},{self.qn["J"]})'


def parse_termsymbol(symbol_str):
    try:
        return Level.parse(symbol_str)
    except ValueError:
        try:
            return Term.parse(symbol_str)
        except ValueError:
            return eval(f"Symbol({symbol_str})", {"Symbol": Symbol})
