import numpy as np
import jax.numpy as jnp
from functools import reduce, partial
from math import prod, ceil, floor
from operator import add
from jax.scipy.linalg import expm
from sympy.physics.wigner import wigner_3j
from scipy.special import factorial, binom, gamma
from scipy.cluster.hierarchy import linkage, leaves_list


def block_triangular_expm(A, B, C, t):
    n = A.shape[0]
    idc = np.ix_(range(0, n), range(n, 2 * n))
    blk = jnp.block([[A, B], [jnp.zeros((n, n)), C]])
    return expm(t * blk)[idc]


def integrate_expm(A, t):
    n = A.shape[0]
    return block_triangular_expm(A, jnp.identity(n), jnp.zeros((n, n)), t)


def integrate_cosk_expm(k, A, t):
    n = A.shape[0]
    return integrate_expm(A + 1.j * k * np.identity(n), t).real


def integrate_SO3_char_psi(j, Jz):
    return 0.5 * (integrate_cosk_expm(j, Jz, np.pi) -
                  integrate_cosk_expm(j + 1, Jz, np.pi))


def integrate_SO3_theta(Jy, B):
    dim = Jy.shape[0]
    return block_triangular_expm(
        Jy, B, Jy + 1.j * jnp.identity(dim), np.pi).imag @ expm(-np.pi * Jy)


def integrate_SO3_phi(Jz, B):
    return block_triangular_expm(Jz, B, Jz, 2 * np.pi) @ expm(-2 * np.pi * Jz)


def count_SO3_irrep(j, Jz):
    return 2/np.pi * jnp.trace(integrate_SO3_char_psi(j, Jz))


def project_SO3_irrep(j, Jy, Jz):
    psi_int = integrate_SO3_char_psi(j, Jz)
    theta_int = integrate_SO3_theta(Jy, psi_int)
    phi_int = integrate_SO3_phi(Jz, theta_int)
    return (2 * j + 1) / (2 * np.pi**2) * phi_int


def project_angm(j, j2, jmax=None):

    n = j2.shape[1]

    if (j * 2) % 2 == 0:
        jmax = jmax or 100
        irreps = np.arange(jmax + 1)
    elif (j * 2) % 2 == 1:
        jmax = jmax or 100.5
        irreps = np.arange(1/2, jmax + 1)
    else:
        raise ValueError(f"j = {j} must be an exact (half-)integer number!")

    def jval(k):
        return k * (k + 1)

    def terms():
        for l in irreps:
            if l == j:
                continue

            yield (j2 - jval(l) * np.identity(n)) / (jval(j) - jval(l))

    return reduce(np.matmul, terms())


def cartesian_to_polar_basis(j_ops):
    j_p = (j_ops[0] + 1.j * j_ops[1]) / np.sqrt(2)
    j_m = (j_ops[0] - 1.j * j_ops[1]) / np.sqrt(2)
    return [j_ops[2]], [[j_p, j_m]]


def dot(inv_metric, a, b):
    return np.einsum('ij, i..., j...', inv_metric, jnp.array(a), jnp.array(b))


def norm(inv_metric, root):
    return dot(inv_metric, root, root)


def racah_unit_tensor(tensor, k, l):
    coeff = (-1)**k / factorial(k) * np.sqrt(factorial(2 * k) * factorial(2 * l - k) / factorial(2 * l + k + 1))
    return tensor * coeff * np.sqrt(2 * k + 1)  # Judd-factor

def w_op(tensors, l, n, m):
    return np.sum([(-1)**(l - n) * (1 - (-1)**k) * np.sqrt(2 * k + 1) *
                   float(wigner_3j(l, k, l, -n, q, m)) *
                   (((-1)**q * tensors[k][-q].conj().T) if q < 1 else tensors[k][q])
                   for k in range(1, 2 * l, 2) for q in range(-k, k+1)], axis=0)


def root_vec(l, *idc):
    root = [0] * l
    for idx in idc:
        if idx == 0:
            continue
        root[abs(idx) - 1] = 1 if idx > 0 else -1
    return tuple(root)


def is_positive_root(root):
    # tests if first non-zero entry is positive
    if root[0] > 0:
        return True
    elif root[0] == 0:
        return is_positive_root(root[1:])
    else:
        return False


def is_simple_root(pos_roots, root):
    # can not be writen as sum of positive roots
    for idx, iroot in enumerate(pos_roots):
        for jroot in pos_roots[idx+1:]:
            if all(r == i + j for r, i, j in zip(root, iroot, jroot)):
                return False
    return True


def sigma_plus_ordering(roots):
    # l = len(roots[0])
    pos_roots = list(filter(is_positive_root, roots))
    # simp_roots = list(filter(partial(is_simple_root, pos_roots), pos_roots))
    # components = np.linalg.solve(np.array(simp_roots).T, np.array(pos_roots).T).T
    if len(pos_roots) == 1:
        return pos_roots

    Z = linkage(pos_roots, method='single', metric='cosine', optimal_ordering=True)
    print(Z)
    print(leaves_list(Z))
    # for i in leaves_list(Z):
    #     print(pos_roots[i])

    return [pos_roots[i] for i in leaves_list(Z)]


# Only works with pure j
# def eval_R3_proj(angm, j, m):
#     """Löwdin-Shapiro infinitesimal form"""

#     jp = (angm[0] + 1.j * angm[1]) / np.sqrt(2)
#     jm = (angm[0] - 1.j * angm[1]) / np.sqrt(2)

#     def term(r):
#         pre = (-1)**r * (2 * j + 1) / factorial(r) / factorial(2 * j + r + 1)
#         return pre * np.linalg.matrix_power(jm, j - m + r) @ np.linalg.matrix_power(jp, j - m + r)

#     pre = np.sqrt(factorial(j + m) * factorial(j + m) /
#                   factorial(j - m) / factorial(j - m))

#     return pre * np.sum([term(r) for r in range(100)], axis=0)


def eval_R3_ops(tensors, l):
    """Normalisation: (-1/2) * J+, at least for even l"""
    h_ops = [tensors[1][0] / np.sqrt(3 / l / (l + 1) / (2 * l + 1))]
    e_ops = {(1,): tensors[1][1] / np.sqrt(3 / l / (l + 1) / (2 * l + 1))}
    e_ops = {r: e / np.sqrt(2) for r, e in e_ops.items()}
    inv_metric = np.identity(1) / 2
    return h_ops, e_ops, inv_metric


def eval_R3_ladder_ops(tensors, l, j, m):
    # factor 2 from normalisation of R3 e_ops
    _, e_ops, _ = eval_R3_ops(tensors, l)
    return [jnp.sqrt(factorial(j + m) / factorial(2 * j) / factorial(j - m)) *
            jnp.linalg.matrix_power(2 * e_ops[(1,)], j - m)]


def eval_R5_R3_ladder_op(tensors, W, L, l):
    # factor 2 from normalisation of R3 e_ops
    _, e_ops, _ = eval_R2lp1_ops(tensors, l)
    v = list(range(ceil((W[0] + L) / 3 - max(0, (W[0] - L + 2) / 3)),
                   floor((L + 1) / 2) + 1))
    print(v)
    v = v[0]
    print("powers:", W[0] + L - 3 * v, 2 * v - L)
    shift_op = (jnp.linalg.matrix_power(e_ops[(1, 0)].conj().T, W[0] + L - 3 * v) @
                jnp.linalg.matrix_power(e_ops[(1, 1)].conj().T, 2 * v - L))
    h_ops, e_ops, inv_metric = eval_R3_ops(tensors, l)
    proj_op = projection_onto_highest_weight(h_ops, e_ops, inv_metric, (L,))
    
    return proj_op @ shift_op


def eval_R2lp1_ops(tensors, l):

    def sgn(q):
        if q > 0:
            return +1
        elif q < 0:
            return -1
        else:
            return 0

    h_ops = [w_op(tensors, l, l + 1 - i, l + 1 - i) for i in range(1, l + 1)]
    e_ops = {root_vec(l, sgn(n) * (l - abs(n) + 1), -sgn(m) * (l - abs(m) + 1)):
             w_op(tensors, l, n, m) for n in range(-l, l + 1) for m in range(-l, l + 1)
             if n != -m and n != m and abs(n) > abs(m)}
    inv_metric = np.identity(l) / (2 * l - 1) / 2
    roots = sigma_plus_ordering(list(e_ops.keys()))
    e_ops = {r: e_ops[r] / np.sqrt(2 * (2 * l - 1)) for r in roots}
    return h_ops, e_ops, inv_metric


def comm(a, b):
    return a @ b - b @ a


def adjoint_rep(*ops):
    # return [-np.array([np.linalg.lstsq(np.array([d.flatten() for d in ops]).T, comm(a, b).flatten(), rcond=None)[0]
    return [-np.array([[np.trace(d @ comm(a, b).conj().T) / np.trace(d @ d.conj().T) for d in ops]
    # return [np.array([[np.sum(d * comm(a, b).conj()) / np.sum(d * d.conj()) for d in ops]
                      for b in ops]) for a in ops]


def cartan_killing_metric(*ops):
    adj = adjoint_rep(*ops)
    return np.array([[np.trace(a @ b) for b in adj] for a in adj])


def is_herm(a):
    return np.allclose(a, a.conj().T)


def projection_onto_highest_weight(h_ops, e_ops, inv_metric, mu, algo='exp'):
    roots = list(e_ops.keys())
    rho = np.sum(roots, axis=0) / 2
    num = h_ops[0].shape[0]
    # rank = len(h_ops)

    _dot = partial(dot, inv_metric)
    _norm = partial(norm, inv_metric)

    def h_root(root):
        return np.einsum('imn,ij,j', h_ops, inv_metric, root)
        # return comm(e_ops[root], e_ops[root].conj().T)

    def e_herm(root):
        return e_ops[root] + e_ops[root].conj().T

    def scalar(scal):
        return scal * np.identity(num)

    # implementation of exponential algo
    def phi_int(root):
        exp = (h_root(root) - scalar(_dot(root, mu))) / _norm(root)
        return integrate_expm(1.j * exp, 2 * np.pi)

    def theta_int(root):

        n = 4 * _dot(root, rho) / _norm(root) - 1 + 2 * _dot(root, mu) / _norm(root)
        n = int(np.rint(4 * _dot(root, rho) / _norm(root) - 1 + 2 * _dot(root, mu) / _norm(root)))

        def term(k):
            exp = e_herm(root) / np.sqrt(2 * _norm(root))
            exp_pos = exp + scalar((n - 2 * k + 1) / 2)
            exp_neg = exp + scalar((n - 2 * k - 1) / 2)
            return binom(n, k) * (integrate_expm(1.j * exp_pos, np.pi) -
                                  integrate_expm(1.j * exp_neg, np.pi))

        return np.sum([term(k) for k in range(n + 1)], axis=0) / (2**n * 2.j)

    def root_int(root):
        return phi_int(root) @ theta_int(root)

    def psi_int(h, m):
        exp = (h - scalar(m)) / 2
        return integrate_expm(1.j * exp, 4 * np.pi)

    def norm_factor(root):
        return _dot(root, mu + rho) / _dot(root, rho)

    def theta_norm(root):
        return 2 / (4 * _dot(root, rho) / _norm(root))

    # implementation of infitesimal algo
    def coeff_func(root, r):

        eig, vec = np.linalg.eigh(2 * _dot(root, tuple(map(add, h_ops, map(scalar, rho)))) / _norm(root))

        return (-2 / _norm(root))**r / factorial(r) * \
            vec.T.conj() @ np.diag(gamma(eig + 1) / gamma(eig + r + 1)) @ vec
        # val = 2 * _dot(root, mu + rho) / _norm(root)
        # return (-2 / _norm(root))**r / factorial(r) * factorial(val) / factorial(val + r)

    def proj_root(root):

        def term(r):
            return coeff_func(root, r) @ \
                    np.linalg.matrix_power(e_ops[root].conj().T, r) @ \
                    np.linalg.matrix_power(e_ops[root], r)

        return np.sum([term(r) for r in range(100)], axis=0)

    if algo == 'exp':
        proj_int = reduce(np.matmul, map(root_int, roots)) @ \
                reduce(np.matmul, map(psi_int, h_ops, mu))

        proj_norm = (2 * np.pi)**len(roots) * (4 * np.pi)**len(roots[0]) * \
                reduce(lambda x, y: x * y, map(theta_norm, roots))

        dim = reduce(lambda x, y: x * y, map(norm_factor, roots))

        return dim * proj_int / proj_norm

    elif algo == 'inf':
        return reduce(np.matmul, map(proj_root, roots))


def R3_projector_loewdin(l, m, k, angm):

    # _, vec = np.linalg.eigh(angm[2])
    # angm = vec.T.conj() @ angm @ vec
    # print(_)

    lp = angm[0] + 1.j * angm[1]
    lm = angm[0] - 1.j * angm[1]

    def term(r):
        pre = (-1)**r * (2 * l + 1) / factorial(r) / factorial(2 * l + 1 + r)
        return pre * (np.linalg.matrix_power(lm, l - m + r) @
                      np.linalg.matrix_power(lp, l - k + r))

    pre = np.sqrt(factorial(l + m) * factorial(l + k) /
                  factorial(l - m) / factorial(l - k))

    # return pre * vec @ reduce(add, (term(r) for r in range(0, 100))) @ vec.conj().T
    return pre * reduce(add, (term(r) for r in range(20)))


def R3_projector_integral(l, m, k, angm):

    num = angm.shape[1]

    def scalar(scal):
        return scal * np.identity(num)

    def phi_int():
        exp = angm[2] - scalar(m)
        return integrate_expm(1.j * exp, 2 * np.pi)

    def theta_int():

        def term(s):
            def term(nc, ns):
                def term(kc, ks):
                    # 2 from binomial theorem cancels 1/2 from theta/2
                    exp = angm[0] + scalar((nc + ns - 2 * kc - 2 * ks) / 2)
                    return (-1)**ks * binom(nc, kc) * binom(ns, ks) * integrate_expm(1.j * exp, np.pi)
                return np.sum([term(kc, ks) for kc in np.arange(nc + 1) for ks in np.arange(ns + 1)], axis=0) / 2**nc / 2.j**ns
            # increment both powers by one from invariant measure
            return (-1)**s * 1.j**(k - m) * term(2 * l + k - m - 2 * s + 1, m - k + 2 * s + 1) \
                / factorial(l + k - s) / factorial(s) / factorial(m - k + s) / factorial(l - m - s)

        pre = np.sqrt(factorial(l + m) * factorial(l - m) * factorial(l + k) * factorial(l - k))

        return pre * np.sum([term(s) for s in np.arange(max(0, k - m), min(l + k, l - m) + 1)], axis=0)

    def psi_int():
        exp = (angm[2] - scalar(k)) / 2
        return integrate_expm(1.j * exp, 4 * np.pi)

    return (2 * l + 1) / (8 * np.pi**2) * phi_int() @ theta_int() @ psi_int()
