from typing import NamedTuple, Union
from functools import partial

from optax._src import base
from optax._src import transform
from optax._src import combine
from optax import tree_utils as otu

import jax
import jax.scipy as jscipy
import jax.numpy as jnp

def tree_expm_scalar_mul(scalar, tree):
    return jax.tree.map(jscipy.linalg.expm, otu.tree_scalar_mul(scalar, tree))

def compute_riemann_gradient(conj_grad, vecs):
    return conj_grad @ vecs.conj().T - vecs @ conj_grad.conj().T

def compute_riemann_norm(x, y=None):
    if y is None:
        return jnp.trace(x @ x.conj().T).real / 2
    return jnp.trace(x @ y.conj().T).real / 2

def compute_rotation(step, riem_grad):
    return jscipy.linalg.expm(-step * riem_grad)


class ScaleByRiemannState(NamedTuple):
    gradient_norm: float


def scale_by_riemann():
    # DOI: 10.1109/TSP.2007.908999

    def init_fn(params):
        return ScaleByRiemannState(gradient_norm=0.0)

    def update_fn(updates, state, current_unitary):
        # Compute Riemannian gradient direction
        conjugate_grads = jax.tree.map(jnp.conjugate, updates)
        riem_grad = jax.tree.map(compute_riemann_gradient, conjugate_grads, current_unitary)
        state = ScaleByRiemannState(gradient_norm=otu.tree_sum(jax.tree.map(compute_riemann_norm, riem_grad)))
        return riem_grad, state

    return base.GradientTransformation(init_fn, update_fn)


class ScaleByRiemannCGState(NamedTuple):
    dimension: int
    iteration: int
    riem_grad: base.Updates
    direction: base.Updates


def scale_by_riemann_cg():
    # DOI: 10.1109/ICASSP.2008.4518119

    def init_fn(params):

        def get_dimension(mat):
            dimension = mat.shape[0]
            if all(dimension == dim for dim in mat.shape):
                return dimension
            else:
                raise ValueError("Expected square unitary, but got non-square matrix.")
            
        dimension = otu.tree_sum(jax.tree.map(get_dimension, params))

        return ScaleByRiemannCGState(dimension=dimension, iteration=0, riem_grad=None, direction=None)

    def update_fn(riem_grad, state, params):

        if state.iteration % state.dimension**2 == 0:
            direction = riem_grad
        else:
            weighting = otu.tree_sum(jax.tree.map(compute_riemann_norm, otu.tree_sub(riem_grad, state.riem_grad), riem_grad)) / otu.tree_sum(jax.tree.map(compute_riemann_norm, state.riem_grad))
            direction = otu.tree_add(riem_grad, otu.tree_scalar_mul(weighting, state.direction))
        
        state = ScaleByRiemannCGState(
            dimension=state.dimension,
            iteration=state.iteration + 1,
            riem_grad=riem_grad,
            direction=direction,
        )

        return direction, state

    return base.GradientTransformation(init_fn, update_fn)


class ScaleByRiemannLinesearchState(NamedTuple):
    learning_rate: Union[float, jax.Array]


def scale_by_riemann_linesearch():

    class RiemannLineSearchState(NamedTuple):
        """State during the inner loop of a Riemann line-search."""
        learning_rate: Union[float, jax.Array]
        p_rotation: base.Updates
        q_rotation: base.Updates
        decrease_measure: Union[float, jax.Array]
        iter_num: int

    def init_fn(params):
        return ScaleByRiemannLinesearchState(learning_rate=jnp.array(1.0))

    def update_fn(updates, state, params, *, value, value_fn):

        grad_norm = otu.tree_sum(jax.tree.map(compute_riemann_norm, updates))
        current_unitary = params

        def increase_cond_fn(search_state):
            return search_state.decrease_measure >= 0.0

        def decrease_cond_fn(search_state):
            return (search_state.decrease_measure < 0.0)

        def compute_decrease_measure(rotation, learning_rate, increase):
            new_unitary = jax.tree.map(jnp.matmul, rotation, current_unitary)
            new_value = value_fn(new_unitary)
            decrease_measure = value - new_value - learning_rate * (1.0 if increase else 0.5) * grad_norm
            return decrease_measure

        def body_fn(increase, search_state):

            if increase:
                p_rotation = search_state.q_rotation
                q_rotation = jax.tree.map(jnp.matmul, p_rotation, p_rotation)
            else:
                p_rotation = tree_expm_scalar_mul(-search_state.learning_rate, updates)
                q_rotation = search_state.q_rotation

            learning_rate = search_state.learning_rate * (2.0 if increase else 0.5)
            
            decrease_measure = compute_decrease_measure(
                q_rotation if increase else p_rotation, learning_rate, increase)

            search_state = RiemannLineSearchState(
                learning_rate=learning_rate,
                p_rotation=p_rotation,
                q_rotation=q_rotation,
                decrease_measure=decrease_measure,
                iter_num=search_state.iter_num + 1,
            )

            return search_state

        p_rotation = tree_expm_scalar_mul(-state.learning_rate, updates)
        q_rotation = jax.tree.map(jnp.matmul, p_rotation, p_rotation)

        # todo: uses naive while loop structure since lax.while_loop leads to recomilation during every iteration
        def while_loop(cond_fun, body_fun, init_val):
            val = init_val
            while cond_fun(val):
                val = body_fun(val)
            return val

        search_state = RiemannLineSearchState(
            learning_rate=state.learning_rate,
            p_rotation=p_rotation,
            q_rotation=q_rotation,
            decrease_measure=compute_decrease_measure(q_rotation, state.learning_rate, True),
            iter_num=0,
        )

        # search_state = jax.lax.while_loop(increase_cond_fn, partial(body_fn, True), search_state)
        search_state = while_loop(increase_cond_fn, partial(body_fn, True), search_state)

        search_state = RiemannLineSearchState(
            learning_rate=search_state.learning_rate,
            p_rotation=search_state.p_rotation,
            q_rotation=search_state.q_rotation,
            decrease_measure=compute_decrease_measure(search_state.p_rotation, search_state.learning_rate, False),
            iter_num=0,
        )

        # search_state = jax.lax.while_loop(decrease_cond_fn, partial(body_fn, False), search_state)
        search_state = while_loop(decrease_cond_fn, partial(body_fn, False), search_state)

        # new_updates = search_state.p_rotation
        new_updates = otu.tree_scalar_mul(search_state.learning_rate, updates)

        new_state = ScaleByRiemannLinesearchState(
            learning_rate=search_state.learning_rate
        )

        return new_updates, new_state

    return base.GradientTransformationExtraArgs(init_fn, update_fn)

 
# Aliases

def riem_sd(learning_rate=None):

    if learning_rate is None:
        base_scaling = transform.scale(-1.0)
    else:
        base_scaling = transform.scale_by_learning_rate(learning_rate)

    return combine.chain(
        scale_by_riemann(),
        scale_by_riemann_linesearch(),
        base_scaling
    )


def riem_cg(learning_rate=None):
    if learning_rate is None:
        base_scaling = transform.scale(-1.0)
    else:
        base_scaling = transform.scale_by_learning_rate(learning_rate)

    return combine.chain(
        scale_by_riemann(),
        scale_by_riemann_cg(),
        scale_by_riemann_linesearch(),  # todo: seems like current linesearch does not improve performance beyond sd
        base_scaling
    )
