
from functools import partial
import numpy as np

from jax import numpy as jnp
from jax import scipy as jscipy
from jax import grad, jacfwd, jit
from jax.lax import stop_gradient
from jax import config

from .basis import extract_blocks

config.update("jax_enable_x64", True)


def magmom(spin, angm):
    """(negative) Magnetic moment
    """
    muB = 0.5  # atomic units
    g_e = 2.002319
    return muB * (angm + g_e * spin)


def eprg_tensor(spin, angm):
    muB = 0.5  # atomic units
    magm = magmom(spin, angm) / muB
    return 2 * jnp.einsum('kij,lji->kl', magm, magm).real


def compute_eprg_tensors(spin, angm, ener=None, multiplets=None):
    """Compute list of EPR G-tensors.

    Parameters
    ----------
    spin : np.array
        Spin operator in the SO eigenstate basis.
    angm : np.array
        Orbital angular momentum operator in the SO eigenstate basis.
    ener : np.array
        SO eigen energies.
    multiplet : list(int)
        List of low lying manifold multiplicities.

    Returns
    -------
    list(np.array)
        List of EPR G-tensors.
    """

    if multiplets is None:
        labs = np.unique(np.around(ener, 8), return_inverse=True)[1]
    else:
        labs = [lab for lab, mult in enumerate(multiplets) for _ in range(mult)]

    # extract diagonal blocks according to degeneracy patterns or multiplet def
    spin_blks = extract_blocks(spin, labs, labs)
    angm_blks = extract_blocks(angm, labs, labs)

    return list(map(eprg_tensor, spin_blks, angm_blks))


def zeeman_hamiltonian(spin, angm, field):
    """Compute Zeeman Hamiltonian in atomic units.

    Parameters
    ----------
    spin : np.array
        Spin operator in the SO basis.
    angm : np.array
        Orbital angular momentum operator in the SO basis.
    field : np.array
        Magnetic field in mT.

    Returns
    -------
    np.array
        Zeeman Hamiltonian matrix.
    """

    au2mT = 2.35051756758e5 * 1e3  # mTesla / au

    # calculate zeeman operator and convert field in mT to T
    return jnp.einsum('i,imn->mn', jnp.array(field) / au2mT, magmom(spin, angm))


# @partial(jit, static_argnames=['differential', 'algorithm'])
def susceptibility_tensor(temp, hamiltonian, spin, angm, field=0.,
                          differential=True, algorithm=None):
    """Differential molar magnetic susceptipility tensor under applied magnetic
    field along z, or conventional susceptibility tensor where each column
    represents the magnetic response under applied magnetic field along x, y or
    z.

    Parameters
    ----------
    temp : float
        Temperature in Kelvin.
    hamiltonian : np.array
        Electronic Hamiltonian in atomic units.
    spin : np.array
        Spin operator in the SO basis.
    angm : np.array
        Orbital angular momentum operator in the SO basis.
    field : float
        Magnetic field in mT at which susceptibility is measured.
    differential : bool
        If True, calculate differential susceptibility.
    algorithm : {'eigh', 'expm'}
        Algorithm for the computation of the partition function.

    Returns
    -------
    3x3 np.array

    """
    a0 = 5.29177210903e-11  # Bohr radius in m
    c0 = 137.036  # a.u.
    mu0 = 4 * np.pi / c0**2  # vacuum permeability in a.u.
    au2mT = 2.35051756758e5 * 1e3  # mTesla / au

    # [hartree] / [mT mol] * [a.u.(velocity)^2] / [mT]
    algorithm = algorithm or ('expm' if differential else 'eigh')
    mol_mag = partial(molecular_magnetisation, temp, hamiltonian, spin, angm,
                      algorithm=algorithm)

    if differential:
        chi = mu0 * jacfwd(mol_mag)(jnp.array([0., 0., field]))
    else:
        # conventional susceptibility at finite field
        chi = mu0 * jnp.column_stack([mol_mag(fld) / field
                                      for fld in field * jnp.identity(3)])

    # [cm^3] / [mol] + 4*pi for conversion from SI cm3
    return (a0 * 100)**3 * au2mT**2 * chi / (4 * np.pi)


def make_susceptibility_tensor(hamiltonian, spin, angm, field=0.):
    """Differential molar magnetic susceptipility tensor under applied magnetic
    field along z, or conventional susceptibility tensor where each column
    represents the magnetic response under applied magnetic field along x, y or
    z. Maker function for partial evaluation of matrix eigen decomposition.


    Parameters
    ----------
    hamiltonian : np.array
        Electronic Hamiltonian in atomic units.
    spin : np.array
        Spin operator in the SO basis.
    angm : np.array
        Orbital angular momentum operator in the SO basis.
    field : float
        Magnetic field in mT at which susceptibility is measured.

    Returns
    -------
    3x3 np.array

    """
    a0 = 5.29177210903e-11  # Bohr radius in m
    c0 = 137.036  # a.u.
    mu0 = 4 * np.pi / c0**2  # vacuum permeability in a.u.
    au2mT = 2.35051756758e5 * 1e3  # mTesla / au

    # [hartree] / [mT mol] * [a.u.(velocity)^2] / [mT]

    mol_mag = [make_molecular_magnetisation(hamiltonian, spin, angm, fld)
               for fld in field * jnp.identity(3)]

    # conventional susceptibility at finite field
    def susceptibility_tensor(temp):
        chi = mu0 * jnp.column_stack([mol_mag[comp](temp) / field for comp in range(3)])
        # [cm^3] / [mol] + 4*pi for conversion from SI cm3
        return (a0 * 100)**3 * au2mT**2 * chi / (4 * np.pi)

    return susceptibility_tensor


def molecular_magnetisation(temp, hamiltonian, spin, angm, field, algorithm='eigh'):
    """ Molar molecular magnetisation in [hartree] / [mT mol]

    Parameters
    ----------
    temp : float
        Temperature in Kelvin.
    hamiltonian : np.array
        Electronic Hamiltonian in atomic units.
    spin : np.array
        Spin operator in the SO basis.
    angm : np.array
        Orbital angular momentum operator in the SO basis.
    field : np.array
        Magnetic field in mT at which susceptibility is measured. If None,
        returns differential susceptibility.
    algorithm : {'eigh', 'expm'}
        Algorithm for the computation of the partition function.
    """

    Na = 6.02214076e23  # 1 / mol
    kb = 3.166811563e-6  # hartree / K
    beta = 1 / (kb * temp)  # hartree
    au2mT = 2.35051756758e5 * 1e3  # mTesla / au

    h_total = hamiltonian + zeeman_hamiltonian(spin, angm, field)

    if algorithm == 'expm':
        dim = h_total.shape[0]
        # condition matrix by diagonal shift
        h_shft = h_total - stop_gradient(jnp.eye(dim) * jnp.min(h_total))
        expH = jscipy.linalg.expm(-beta * h_shft)
        Z = jnp.trace(expH).real

    elif algorithm == 'eigh':
        eig, vec = jnp.linalg.eigh(h_total)
        eig_shft = eig - stop_gradient(eig[0])
        expH = vec @ jnp.diag(jnp.exp(-beta * eig_shft)) @ vec.T.conj()
        Z = jnp.sum(jnp.exp(-beta * eig_shft))

    else:
        ValueError(f"Unknown algorithm {algorithm}!")

    dZ = -jnp.einsum('ij,mji', expH, magmom(spin, angm) / au2mT).real

    return Na * dZ / Z


def make_molecular_magnetisation(hamiltonian, spin, angm, field):
    """ Molar molecular magnetisation in [hartree] / [mT mol] maker function
    for partial evaluation of matrix eigen decomposition.

    Parameters
    ----------
    hamiltonian : np.array
        Electronic Hamiltonian in atomic units.
    spin : np.array
        Spin operator in the SO basis.
    angm : np.array
        Orbital angular momentum operator in the SO basis.
    field : np.array
        Magnetic field in mT at which susceptibility is measured. If None,
        returns differential susceptibility.
    """

    Na = 6.02214076e23  # 1 / mol
    kb = 3.166811563e-6  # hartree / K
    au2mT = 2.35051756758e5 * 1e3  # mTesla / au

    h_total = hamiltonian + zeeman_hamiltonian(spin, angm, field)
    # condition matrix by diagonal shift
    eig, vec = jnp.linalg.eigh(h_total)

    def molecular_magnetisation(temp):
        beta = 1 / (kb * temp)  # hartree
        eig_shft = eig - stop_gradient(eig[0])
        expH = vec @ jnp.diag(jnp.exp(-beta * eig_shft)) @ vec.T.conj()
        Z = jnp.sum(jnp.exp(-beta * eig_shft))
        dZ = -jnp.einsum('ij,mji', expH, magmom(spin, angm) / au2mT).real
        return Na * dZ / Z

    return molecular_magnetisation
