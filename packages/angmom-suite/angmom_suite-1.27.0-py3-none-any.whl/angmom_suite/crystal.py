"""
This module contains functions for working with crystal field Hamiltonians
"""

from functools import reduce, lru_cache
import warnings

import numpy as np
import numpy.linalg as la

from sympy.physics.wigner import wigner_3j, wigner_6j
import scipy.special as ssp

from . import utils as ut
from .basis import calc_ang_mom_ops

N_TOTAL_CFP_BY_RANK = {2: 5, 4: 14, 6: 27}
RANK_BY_N_TOTAL_CFP = {val: key for key, val in N_TOTAL_CFP_BY_RANK.items()}


@lru_cache(maxsize=None)
def recursive_a(k, q, m):
    """
    Given k,q,m this function
    calculates and returns the a(k,q-1,m)th
    Ryabov coefficient by recursion

    Parameters
    ----------
    k : int
        k value (rank)
    q : int
        q value (order)
    m : int
        m value

    Returns
    -------
    np.ndarray
        a(k,q,m) values for each power of X=J(J+1) (Ryabov) up to k+1
    """

    coeff = np.zeros(k+1)

    # Catch exceptions/outliers and end recursion
    if k == q-1 and m == 0:
        coeff[0] = 1
    elif q-1 + m > k:
        pass
    elif m < 0:
        pass
    else:
        # First and second terms
        coeff += (2*q+m-1)*recursive_a(k, q+1, m-1)
        coeff += (q*(q-1) - m*(m+1)/2) * recursive_a(k, q+1, m)

        # Third term (summation)
        for n in range(1, k-q-m+1):
            # First term in sum of third term
            coeff[1:] += (-1)**n * (
                            ut.binomial(m+n, m) * recursive_a(k, q+1, m+n)[:-1]
                        )
            # Second and third term in sum
            coeff += (-1)**n * (
                        - ut.binomial(m+n, m-1) - ut.binomial(m+n, m-2)
                    ) * recursive_a(k, q+1, m+n)

    return coeff


def get_ryabov_a_coeffs(k_max):

    """
    Given k_max this function calculates all possible values
    of a(k,q,m) for each power (i) of X=J(J+1)

    Parameters
    ----------
    k_max : int
        maximum k (rank) value

    Returns
    -------
    np.ndarray
        All a(k,q,m,i)
    np.ndarray
        Greatest common factor of each a(k,q,:,:)
    """

    a = np.zeros([k_max, k_max+1, k_max+1, k_max+1])
    f = np.zeros([k_max, k_max+1])

    # Calculate all a coefficients
    for k in range(1, k_max + 1):
        for qit, q in enumerate(range(k, -1, -1)):
            for m in range(k-q + 1):
                a[k-1, qit, m, :k+1] += recursive_a(k, q+1, m)

    # Calculate greatest common factor F for each a(k,q) value
    for k in range(1, k_max + 1):
        for qit, q in enumerate(range(k, -1, -1)):
            allvals = a[k-1, qit, :, :].flatten()
            nzind = np.nonzero(allvals)
            if np.size(nzind) > 0:
                f[k-1, qit] = reduce(ut.GCD, allvals[nzind])

    return a, f


def calc_stev_ops(k_max, J, jp=None, jm=None, jz=None):
    """
    Calculates all Stevens operators Okq with k even and odd from k=1 to k_max
    k_max must be <= 12 (higher rank parameters require quad precision floats)

    Parameters
    ----------
    k_max : int
        maximum k value (rank)
    J : int
        J quantum number
    jp : np.array
        Matrix representation of angular momentum operator
    jm : np.array
        Matrix representation of angular momentum operator
    jz : np.array
        Matrix representation of angular momentum operator

    Returns
    -------
    np.ndarray
        Stevens operators shape = (n_k, n_q, (2J+1), (2J+1))
            ordered k=1 q=-k->k, k=2 q=-k->k ...
    """

    if all(op is None for op in (jp, jm, jz)):
        _, _, jz, jp, jm, _ = calc_ang_mom_ops(J)
    elif any(op is None for op in (jp, jm, jz)):
        ValueError("Either explicitely pass all or none of the angm ops!")

    # Only k <= 12 possible at double precision
    # k_max = min(k_max, 12)
    if k_max > 12:
        warnings.warn("Stevens operator with k > 12 requested. This will "
                      "likely lead to numerical errors at double precision!")

    # Get a(k,q,m,i) coefficients and greatest common factors
    a, f = get_ryabov_a_coeffs(k_max)

    # Sum a(k,q,m,i) coefficients over powers of J to give a(k,q,m)
    a_summed = np.zeros([k_max, k_max+1, k_max+1])

    for i in range(0, k_max+1):
        a_summed += a[:, :, :, i] * float(J*(J+1))**i

    _jp = np.complex128(jp)
    _jm = np.complex128(jm)
    _jz = np.complex128(jz)

    n_states = int(2*J+1)

    okq = np.zeros([k_max, 2*k_max+1, n_states, n_states], dtype=np.complex128)

    # Calulate q operators both + and - at the same time
    for kit, k in enumerate(range(1, k_max + 1)):
        # New indices for q ordering in final okq array
        qposit = 2*k + 1
        qnegit = -1
        for qit, q in enumerate(range(k, -1, -1)):
            qposit -= 1
            qnegit += 1
            if k % 2:  # Odd k, either odd/even q
                alpha = 1.
            elif q % 2:  # Even k, odd q
                alpha = 0.5
            else:  # Even k, even q
                alpha = 1.

            # Positive q
            for m in range(k-q + 1):
                okq[kit, qposit, :, :] += a_summed[kit, qit, m]*(
                    (
                        la.matrix_power(_jp, q)
                        + (-1.)**(k-q-m)*la.matrix_power(_jm, q)
                    ) @ la.matrix_power(_jz, m)
                )

            okq[kit, qposit, :, :] *= alpha/(2*f[kit, qit])

            # Negative q
            if q != 0:
                for m in range(k-q + 1):
                    okq[kit, qnegit, :, :] += a_summed[kit, qit, m]*(
                        (
                            la.matrix_power(_jp, q)
                            - (-1.)**(k-q-m)*la.matrix_power(_jm, q)
                        ) @ la.matrix_power(_jz, m)
                    )

                okq[kit, qnegit, :, :] *= alpha/(2j*f[kit, qit])

    return okq


def load_CFPs(f_name, style="phi", k_parity="even"):
    """
    Loads Crystal Field Parameters (CFPs) from file

    Parameters
    ----------
    f_name : str
        file name to load CFPs from
    style : str {'phi','raw'}
        Style of CFP file:
            Phi = Chilton's PHI Program input file
            raw = list of CFPs arranged starting with smallest value of k
                  following the scheme k=k_min q=-k->k, k=k_min+1 q=-k->k ...
    k_parity : str {'even', 'odd', 'both'}
        Indicates type of k values
            e.g. k=2,4,6,... or k=1,3,5,... or k=1,2,3...

    Returns
    -------
    np.ndarray
        CFPs with shape = (n_k, n_q)
            ordered k=k_min q=-k->k, k=k_min+mod q=-k->k ...
            where mod is 1 or 2 depending upon k_parity
    """

    _CFPs = []
    if style == "phi":
        # PHI does not support odd rank cfps
        k_parity = "even"
        # Read in CFPs, and k and q values
        kq = []
        # site, k, q, Bkq
        with open(f_name, 'r') as f:
            for line in f:
                if '****crystal' in line.lower():
                    line = next(f)
                    while "****" not in line:
                        kq.append(line.split()[1:3])
                        _CFPs.append(line.split()[3])
                        line = next(f)
                    break
        kq = [[int(k), int(q)] for [k, q] in kq]
        _CFPs = np.array([float(CFP) for CFP in _CFPs])

        # Include zero entries for missing CFPs
        # and reorder since PHI files might be in wrong order

        # find largest k and use to set size of array
        k_max = np.max(kq[0])
        n_cfps = np.sum([2*k + 1 for k in range(k_max, 0, -1)])
        CFPs = np.zeros([n_cfps])
        if k_parity == "even":
            for CFP, [k, q] in zip(_CFPs, kq):
                CFPs[_even_kq_to_num(k, q)] = CFP
        elif k_parity == "odd":
            for CFP, [k, q] in zip(_CFPs, kq):
                CFPs[_odd_kq_to_num(k, q)] = CFP
        else:
            for CFP, [k, q] in zip(_CFPs, kq):
                CFPs[_kq_to_num(k, q)] = CFP

    elif style == "raw":
        CFPs = np.loadtxt(f_name)

    return CFPs


def calc_HCF(J, cfps, stev_ops, k_max=False, oef=[]):
    """
    Calculates and diagonalises crystal field Hamiltonian (HCF)
    using CFPs Bkq and Stevens operators Okq, where k even and ranges 2 -> 2j

    Hamiltonian is sum_k (sum_q (oef_k*Bkq*Okq))

    Parameters
    ----------
    J : float
        J quantum number
    cfps : np.array
        Even k crystal Field parameters, size = (n_k*n_q)
        ordered k=2 q=-k->k, k=4 q=-k->k ...
    np.ndarray
        Stevens operators, shape = (n_k, n_q, (2J+1), (2J+1))
        ordered k=2 q=-k->k, k=4 q=-k->k ...
    k_max : int, default = 2*J
        Maximum value of k to use in summation
    oef : np.ndarray, optional
        Operator equivalent factors for each CFP i.e. 27 CFPs = 27 OEFs
        size = (n_k*n_q), ordered k=2 q=-k->k, k=4 q=-k->k ...

    Returns
    -------
    np.array
        Matrix representation of Crystal Field Hamiltonian (HCF)
    np.array
        Eigenvalues of HCF (lowest eigenvalue is zero)
    np.array
        Eigenvectors of HCF
    """

    if not k_max:
        k_max = int(2*J)
        k_max -= k_max % 2
        k_max = min(k_max, 12)

    if not len(oef):
        oef = np.ones(cfps.size)

    # calculate number of states
    n_states = int(2 * J + 1)

    # Form Hamiltonian
    HCF = np.zeros([n_states, n_states], dtype=np.complex128)
    for kit, k in enumerate(range(2, k_max+1, 2)):
        for qit, q in enumerate(range(-k, k+1)):
            HCF += stev_ops[kit, qit, :, :] * cfps[_even_kq_to_num(k, q)] \
                    * oef[_even_kq_to_num(k, q)]

    # Diagonalise
    CF_val, CF_vec = la.eigh(HCF)

    # Set ground energy to zero
    CF_val -= CF_val[0]

    return HCF, CF_val, CF_vec


def calc_oef(n, J, L, S):
    """
    Calculate operator equivalent factors for Stevens Crystal Field
    Hamiltonian in |J, mJ> basis

    Using the approach of
    https://arxiv.org/pdf/0803.4358.pdf

    Parameters
    ----------
    n : int
        number of electrons in f shell
    J : float
        J Quantum number
    L : int
        L Quantum number
    S : float
        S Quantum number

    Returns
    -------
    np.ndarray
        operator equivalent factors for each parameter, size = (n_k*n_q)
        ordered k=2 q=-k->k, k=4 q=-k->k ...
    """

    def _oef_lambda(p, J, L, S):
        lam = (-1)**(J+L+S+p)*(2*J+1)
        lam *= wigner_6j(J, J, p, L, L, S)/wigner_3j(p, L, L, 0, L, -L)
        return lam

    def _oef_k(p, k, n):
        K = 7. * wigner_3j(p, 3, 3, 0, 0, 0)
        if n <= 7:
            n_max = n
        else:
            n_max = n-7
            if k == 0:
                K -= np.sqrt(7)

        Kay = 0
        for j in range(1, n_max+1):
            Kay += (-1.)**j * wigner_3j(k, 3, 3, 0, 4-j, j-4)

        return K*Kay

    def _oef_RedJ(J, p):
        return 1./(2.**p) * (ssp.factorial(2*J+p+1)/ssp.factorial(2*J-p))**0.5

    # Calculate OEFs and store in array
    # Each parameter Bkq has its own parameter
    oef = np.zeros(27)
    k_max = np.min([6, int(2*J)])
    shift = 0
    for k in range(2, k_max+2, 2):
        oef[shift:shift + 2*k+1] = float(_oef_lambda(k, J, L, S))
        oef[shift:shift + 2*k+1] *= float(_oef_k(k, k, n) / _oef_RedJ(J, k))
        shift += 2*k + 1

    return oef


def calc_order_strength(params: list[float]) -> list[float]:
    """
    Calculates per-order strength parameter S_q for a set of Stevens parameters
    up to rank 6
    """

    max_rank = get_max_rank(params)

    # Convert Stevens parameters to Wybourne scheme
    wparams = abs(stevens_to_wybourne(params, max_rank))

    square_params = wparams ** 2

    # Calculate strength within order (S_q)

    sq = np.zeros(len(params))

    # Rank 2 contributions
    sq[0] = 1./5. * square_params[2]
    sq[1] = 1./5. * square_params[3]
    sq[2] = 1./5. * square_params[4]

    # Rank 4 contributions
    if max_rank > 2:
        sq[0] += 1./9. * square_params[9]
        sq[1] += 1./9. * square_params[10]
        sq[2] += 1./9. * square_params[11]
        sq[3] += 1./9. * square_params[12]
        sq[4] += 1./9. * square_params[13]

    # Rank 6 contributions
    if max_rank > 4:
        sq[6] += 1./13. * square_params[26]
        sq[5] += 1./13. * square_params[25]
        sq[4] += 1./13. * square_params[24]
        sq[3] += 1./13. * square_params[23]
        sq[2] += 1./13. * square_params[22]
        sq[1] += 1./13. * square_params[21]
        sq[0] += 1./13. * square_params[20]

    sq = np.sqrt(sq)

    return sq


def calc_rank_strength(params: list[float]) -> list[float]:
    """
    Calculates per-rank strength parameter S^k for a set of Stevens parameters
    up to rank 6
    """

    max_rank = get_max_rank(params)

    # Convert Stevens parameters to Wybourne scheme
    wparams = abs(stevens_to_wybourne(params, max_rank))

    # Calculate strength within rank (S^k)
    sk2 = np.sqrt(np.sum(wparams[:5]**2) / 5.)
    sk4 = np.sqrt(np.sum(wparams[5:14]**2) / 9.)
    sk6 = np.sqrt(np.sum(wparams[14:]**2) / 13.)

    sk = np.array([sk2, sk4, sk6])

    return sk


def calc_total_strength(params: list[float]) -> float:
    """
    Calculates strength parameter S for a set of Stevens parameters up to
    rank 6
    """

    sk = calc_rank_strength(params)

    # Calculate overall strength as weighted sum of S^k values
    S = np.array(np.sqrt(1./3.*(sk[0]**2 + sk[1]**2 + sk[2]**2)))

    return S


def get_max_rank(params):
    """
    Finds maximum rank in a set of parameters, assumes parameters are ordered
    k=2, q=-2...2, k=4, q=-4, ..., 4...
    """

    try:
        max_rank = RANK_BY_N_TOTAL_CFP[len(params)]
    except ValueError:
        raise ValueError("Incorrect number of CFPs")

    return max_rank


def stevens_to_wybourne(CFPs, k_max):
    """
    Transforms Crystal Field parameters from Wybourne notation to
    Stevens notation

    Assumes only even Ranks (k) are present

    Parameters
    ----------
        CFPs : np.ndarray
            CFPs in Stevens notation, shape = (n_k, n_q)
            ordered k=1 q=-k->k, k=2 q=-k->k ...
        k_max : int
            maximum value of k (rank)

    Returns
    -------
        np.ndarray, dtype=complex128
            CFPs in Wybourne notation, shape = (n_k, n_q)
    """

    if k_max > 6:
        raise ValueError("Cannot convert k>6 parameters to Wybourne")

    # Taken from Mulak and Gajek
    lmbda = [
        np.sqrt(6.)/3.,
        -np.sqrt(6.)/6.,
        2.,
        -np.sqrt(6.)/6.,
        np.sqrt(6.)/3.,
        4.*np.sqrt(70.)/35.,
        -2.*np.sqrt(35.)/35.,
        2.*np.sqrt(10.)/5.,
        -2*np.sqrt(5.)/5.,
        8.,
        -2.*np.sqrt(5.)/5.,
        2.*np.sqrt(10.)/5.,
        -2.*np.sqrt(35.)/35.,
        4.*np.sqrt(70.)/35.,
        16.*np.sqrt(231.)/231.,
        -8.*np.sqrt(77.)/231.,
        8.*np.sqrt(14.)/21.,
        -8.*np.sqrt(105.)/105.,
        16.*np.sqrt(105.)/105.,
        -4.*np.sqrt(42.)/21.,
        16.,
        -4.*np.sqrt(42.)/21.,
        16.*np.sqrt(105.)/105.,
        -8.*np.sqrt(105.)/105.,
        8.*np.sqrt(14.)/21.,
        -8.*np.sqrt(77.)/231.,
        16.*np.sqrt(231.)/231.
    ]

    w_CFPs = np.zeros(N_TOTAL_CFP_BY_RANK[k_max], dtype=np.complex128)

    for k in range(2, k_max + 2, 2):
        for q in range(-k, k + 1):
            ind = _even_kq_to_num(k, q)
            neg_ind = _even_kq_to_num(k, -q)
            if q == 0:
                w_CFPs[ind] = lmbda[ind] * CFPs[ind]
            elif q > 0:
                w_CFPs[ind] = lmbda[ind]*(CFPs[ind] + 1j*CFPs[neg_ind])
            elif q < 0:
                w_CFPs[ind] = lmbda[ind]*(-1)**q*(CFPs[neg_ind] - 1j*CFPs[ind])

    return w_CFPs


def _even_kq_to_num(k, q):
    """
    Converts Rank (k) and order (q) to array index
    Assuming that only even ranks are present

    Parameters
    ----------
        k : int
            Rank k
        q : int
            Order q

    Returns
    -------
        int
            Array index
    """

    index = k + q
    for kn in range(1, int(k/2)):
        index += 2*(k-2*kn) + 1

    return index


def _odd_kq_to_num(k, q):
    """
    Converts Rank (k) and order (q) to array index
    Assuming that only odd ranks are present

    Parameters
    ----------
        k : int
            Rank k
        q : int
            Order q

    Returns
    -------
        int
            Array index
    """

    index = 0
    for kn in range(1, k, 2):
        index += 2*kn + 1

    index += q + k + 1

    return index


def _kq_to_num(k, q):
    """
    Converts Rank (k) and order (q) to array index
    Assuming that all ranks are present

    Parameters
    ----------
        k : int
            Rank k
        q : int
            Order q

    Returns
    -------
        int
            Array index
    """

    index = -1
    for kn in range(1, k):
        index += 2*kn + 1
    index += q + k + 1

    return index


K_MAX = 15

stevens_kq_indices = tuple(
        (k, q)
        for k in range(2, K_MAX, 2)
        for q in range(-k, k+1)
)
