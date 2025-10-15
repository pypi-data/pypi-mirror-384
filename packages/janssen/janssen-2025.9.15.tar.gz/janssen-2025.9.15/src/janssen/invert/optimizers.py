"""
Complex-valued optimizers with Wirtinger derivatives for ptychography.

Extended Summary
----------------
This module implements complex-valued optimization algorithms including
Adam,
Adagrad, and RMSprop using Wirtinger calculus. It also provides learning
rate
schedulers for training optimization. All functions are JAX-compatible
and
support automatic differentiation.

Routine Listings
----------------
LRSchedulerState : class
    State maintained by learning rate schedulers
Optimizer : class
    Optimizer configuration with init and update functions
create_cosine_scheduler : function, scheduler
    Creates a cosine learning rate scheduler with smooth decay
create_step_scheduler : function, scheduler
    Creates a step decay scheduler with periodic learning rate drops
create_warmup_cosine_scheduler : function, scheduler
    Creates a scheduler with linear warmup followed by cosine decay
init_scheduler_state : function, scheduler
    Initialize scheduler state with given learning rate
wirtinger_grad : function
    Compute the Wirtinger gradient of a complex-valued function
complex_adam : function, optimizer
    Complex-valued Adam optimizer based on Wirtinger derivatives
complex_adagrad : function, optimizer
    Complex-valued Adagrad optimizer based on Wirtinger derivatives
complex_rmsprop : function, optimizer
    Complex-valued RMSprop optimizer based on Wirtinger derivatives
init_adam : function, initializer
    Initialize Adam optimizer state
init_adagrad : function, initializer
    Initialize Adagrad optimizer state
init_rmsprop : function, initializer
    Initialize RMSprop optimizer state
adam_update : function, updater
    Update parameters using Adam optimizer with Wirtinger derivatives
adagrad_update : function, updater
    Update parameters using Adagrad optimizer with Wirtinger derivatives
rmsprop_update : function, updater
    Update parameters using RMSprop optimizer with Wirtinger derivatives

Notes
-----
All optimizers use Wirtinger calculus for proper handling of
complex-valued
parameters. The Wirtinger derivative is defined as ∂f/∂z = ½(∂f/∂x -
i∂f/∂y).
All functions are designed to work with JAX transformations including
jit,
grad, and vmap.
"""

import jax
import jax.numpy as jnp
from beartype import beartype
from beartype.typing import (
    Any,
    Callable,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Union,
)
from jaxtyping import Array, Complex, Float, jaxtyped

from janssen.utils import OptimizerState, make_optimizer_state


class LRSchedulerState(NamedTuple):
    """State maintained by learning rate schedulers.

    Attributes
    ----------
    step : int
        Current optimization step
    learning_rate : float
        Current learning rate
    initial_lr : float
        Initial learning rate value
    """

    step: int
    learning_rate: float
    initial_lr: float


SchedulerFn = Callable[[LRSchedulerState], Tuple[float, LRSchedulerState]]


def create_cosine_scheduler(
    total_steps: int,
    final_lr_factor: Optional[float] = 0.01,
) -> SchedulerFn:
    """Create a cosine learning rate scheduler.

    This scheduler implements a cosine annealing schedule that smoothly
    decreases the learning rate from the initial value to a final value
    over the specified number of steps.

    Parameters
    ----------
    total_steps : int
        Total number of optimization steps
    final_lr_factor : float, optional
        Final learning rate as a fraction of initial learning rate.
        Default is 0.01.

    Returns
    -------
    scheduler_fn : SchedulerFn
        A function that takes the current scheduler state and returns
        the new learning rate and updated state.

    Notes
    -----
    Algorithm:
    - Calculate progress as min(step / total_steps, 1.0)
    - Compute cosine decay factor using 0.5 * (1 + cos(π * progress))
    - Calculate new learning rate using linear interpolation
    - Update scheduler state with new step and learning rate
    - Return new learning rate and updated state
    """

    @jax.jit
    def scheduler_fn(
        state: LRSchedulerState,
    ) -> Tuple[float, LRSchedulerState]:
        progress = jnp.minimum(state.step / total_steps, 1.0)
        cosine_decay = 0.5 * (1 + jnp.cos(jnp.pi * progress))
        lr = state.initial_lr * (
            final_lr_factor + (1 - final_lr_factor) * cosine_decay
        )
        new_state = LRSchedulerState(
            step=state.step + 1, learning_rate=lr, initial_lr=state.initial_lr
        )
        return lr, new_state

    return scheduler_fn


def create_step_scheduler(step_size: int, gamma: float = 0.1) -> SchedulerFn:
    """Create a step decay scheduler.

    This creates a step decay scheduler that reduces learning rate by
    gamma
    every step_size steps. This scheduler implements a step-wise
    learning
    rate decay where the
    learning rate is multiplied by gamma every step_size steps.

    Parameters
    ----------
    step_size : int
        Number of steps between learning rate drops
    gamma : float
        Multiplicative factor for learning rate decay.
        Default is 0.1.

    Returns
    -------
    scheduler_fn : SchedulerFn
        A function that takes the current scheduler state and returns
        the new learning rate and updated state.

    Notes
    -----
    Algorithm:
    - Calculate number of learning rate drops as step // step_size
    - Compute new learning rate as initial_lr * (gamma ^ num_drops)
    - Update scheduler state with new step and learning rate
    - Return new learning rate and updated state
    """

    @jax.jit
    def scheduler_fn(
        state: LRSchedulerState,
    ) -> Tuple[float, LRSchedulerState]:
        num_drops = state.step // step_size
        lr = state.initial_lr * (gamma**num_drops)
        new_state = LRSchedulerState(
            step=state.step + 1, learning_rate=lr, initial_lr=state.initial_lr
        )
        return lr, new_state

    return scheduler_fn


def create_warmup_cosine_scheduler(
    total_steps: int,
    warmup_steps: int,
    final_lr_factor: float = 0.01,
) -> SchedulerFn:
    """Create a scheduler with linear warmup followed by cosine decay.

    This scheduler combines a linear warmup phase with a cosine
    annealing
    decay. During warmup, the learning rate increases linearly from 0 to
    the initial value. After warmup, it follows a cosine decay schedule.

    Parameters
    ----------
    total_steps : int
        Total number of optimization steps
    warmup_steps : int
        Number of warmup steps
    final_lr_factor : float
        Final learning rate as a fraction of initial learning rate.
        Default is 0.01.

    Returns
    -------
    scheduler_fn : SchedulerFn
        A function that takes the current scheduler state and returns
        the new learning rate and updated state.

    Notes
    -----
    Algorithm:
    - During warmup phase (step < warmup_steps):
        - Calculate linear warmup learning rate
    - During decay phase (step >= warmup_steps):
        - Calculate cosine decay learning rate
    - Choose appropriate learning rate based on current step
    - Update scheduler state with new step and learning rate
    - Return new learning rate and updated state
    """

    @jax.jit
    def scheduler_fn(
        state: LRSchedulerState,
    ) -> Tuple[float, LRSchedulerState]:
        warmup_progress = jnp.minimum(state.step / warmup_steps, 1.0)
        warmup_lr = state.initial_lr * warmup_progress
        remaining_steps = total_steps - warmup_steps
        decay_progress = (
            jnp.maximum(0.0, state.step - warmup_steps) / remaining_steps
        )
        decay_progress = jnp.minimum(decay_progress, 1.0)
        cosine_decay = 0.5 * (1 + jnp.cos(jnp.pi * decay_progress))
        decay_lr = state.initial_lr * (
            final_lr_factor + (1 - final_lr_factor) * cosine_decay
        )
        lr = jnp.where(state.step < warmup_steps, warmup_lr, decay_lr)
        new_state = LRSchedulerState(
            step=state.step + 1, learning_rate=lr, initial_lr=state.initial_lr
        )
        return lr, new_state

    return scheduler_fn


def init_scheduler_state(initial_lr: float) -> LRSchedulerState:
    """Initialize scheduler state with given learning rate.

    Parameters
    ----------
    initial_lr : float
        Initial learning rate value

    Returns
    -------
    state : LRSchedulerState
        Initialized scheduler state with step=0 and
        learning_rate=initial_lr
    """
    return LRSchedulerState(
        step=0, learning_rate=initial_lr, initial_lr=initial_lr
    )


class Optimizer(NamedTuple):
    """Optimizer configuration.

    Attributes
    ----------
    init : Callable
        Function to initialize optimizer state
    update : Callable
        Function to update parameters using optimizer
    """

    init: Callable
    update: Callable


@jaxtyped(typechecker=beartype)
def wirtinger_grad(
    func2diff: Callable[..., Float[Array, " ..."]],
    argnums: Optional[Union[int, Sequence[int]]] = 0,
) -> Callable[
    ..., Union[Complex[Array, " ..."], Tuple[Complex[Array, " ..."], ...]]
]:
    r"""Compute the Wirtinger gradient of a complex-valued function.

    This function returns a new function that computes the Wirtinger
    gradient
    of the input function f with respect to the specified argument(s).
    This is based on the formula for Wirtinger derivative:

    .. math::
        \frac{\partial f}{\partial z} = \frac{1}{2} \left(
        \frac{\partial f}
        {\partial x} - i \frac{\partial f}{\partial y} \right)


    Parameters
    ----------
    func2diff : Callable[..., Float[Array, " ..."]]
        A complex-valued function to differentiate.
    argnums : Union[int, Sequence[int]], optional
        Specifies which argument(s) to compute the gradient with respect
        to.
        Can be an int or a sequence of ints. Default is 0.

    Returns
    -------
    grad_f :
        Callable[..., Complex[Array, " ..."] | Tuple[Complex[Array, "
        ..."], ...]]
        A function that computes the Wirtinger gradient of f with
        respect to
        the specified argument(s).
    """

    def grad_f(
        *args: Any,
    ) -> Union[Complex[Array, " ..."], Tuple[Complex[Array, " ..."], ...]]:
        def split_complex(args: Any) -> Tuple[Any, ...]:
            return tuple(
                jnp.real(arg) if jnp.iscomplexobj(arg) else arg for arg in args
            ) + tuple(
                jnp.imag(arg) if jnp.iscomplexobj(arg) else jnp.zeros_like(arg)
                for arg in args
            )

        def combine_complex(r: Any, i: Any) -> Tuple[Any, ...]:
            return tuple(
                rr + 1j * ii if jnp.iscomplexobj(arg) else rr
                for rr, ii, arg in zip(r, i, args, strict=False)
            )

        split_args = split_complex(args)
        n = len(args)

        def f_real(*split_args: Any) -> Float[Array, " ..."]:
            return jnp.real(
                func2diff(*combine_complex(split_args[:n], split_args[n:]))
            )

        def f_imag(*split_args: Any) -> Float[Array, " ..."]:
            return jnp.imag(
                func2diff(*combine_complex(split_args[:n], split_args[n:]))
            )

        gr = jax.grad(f_real, argnums=argnums)(*split_args)
        gi = jax.grad(f_imag, argnums=argnums)(*split_args)

        if isinstance(argnums, int):
            return 0.5 * (gr - 1j * gi)
        return tuple(
            0.5 * (grr - 1j * gii) for grr, gii in zip(gr, gi, strict=False)
        )

    return grad_f


@jaxtyped(typechecker=beartype)
def complex_adam(
    params: Complex[Array, " ..."],
    grads: Complex[Array, " ..."],
    state: Tuple[Complex[Array, " ..."], Complex[Array, " ..."], int],
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    eps: float = 1e-8,
) -> Tuple[
    Complex[Array, " ..."],
    Tuple[Complex[Array, " ..."], Complex[Array, " ..."], int],
]:
    """Complex-valued Adam optimizer based on Wirtinger derivatives.

    This function performs one step of the Adam optimization algorithm
    for complex-valued parameters using Wirtinger calculus.

    Parameters
    ----------
    params : Complex[Array, " ..."]
        Current complex-valued parameters
    grads : Complex[Array, " ..."]
        Complex-valued gradients computed using Wirtinger derivatives
    state : Tuple[Complex[Array, " ..."], Complex[Array, " ..."], int]
        Optimizer state containing (first moment, second moment,
        timestep)
    learning_rate : float, optional
        Learning rate for parameter updates.
        Default is 0.001.
    beta1 : float, optional
        Exponential decay rate for first moment estimates.
        Default is 0.9.
    beta2 : float, optional
        Exponential decay rate for second moment estimates.
        Default is 0.999.
    eps : float, optional
        Small value to avoid division by zero.
        Default is 1e-8.

    Returns
    -------
    new_params : Complex[Array, " ..."]
        Updated complex-valued parameters
    new_state :
        Tuple[Complex[Array, " ..."], Complex[Array, " ..."], int]
        Updated optimizer state

    Notes
    -----
    Algorithm:
    - Increment timestep counter
    - Update first moment estimate: m = β₁ * m + (1 - β₁) * grads
    - Update second moment estimate: v = β₂ * v + (1 - β₂) * |grads|²
    - Compute bias-corrected moments: m̂ = m / (1 - β₁^t), v̂ = v / (1 -
    β₂^t)
    - Calculate parameter update: update = lr * m̂ / (√v̂ + ε)
    - Apply update: new_params = params - update
    - Return updated parameters and state
    """
    m, v, t = state
    t += 1
    m = beta1 * m + (1 - beta1) * grads
    v = beta2 * v + (1 - beta2) * jnp.abs(grads) ** 2
    m_hat = m / (1 - beta1**t)
    v_hat = v / (1 - beta2**t)
    update = learning_rate * m_hat / (jnp.sqrt(v_hat) + eps)
    new_params = params - update
    return new_params, (m, v, t)


@jaxtyped(typechecker=beartype)
def complex_adagrad(
    params: Complex[Array, " ..."],
    grads: Complex[Array, " ..."],
    state: Complex[Array, " ..."],
    learning_rate: float = 0.01,
    eps: float = 1e-8,
) -> Tuple[Complex[Array, " ..."], Complex[Array, " ..."]]:
    """Complex-valued Adagrad optimizer based on Wirtinger derivatives.

    This function performs one step of the Adagrad optimization
    algorithm
    for complex-valued parameters using Wirtinger calculus.

    Parameters
    ----------
    params : Complex[Array, " ..."]
        Current complex-valued parameters
    grads : Complex[Array, " ..."]
        Complex-valued gradients computed using Wirtinger derivatives
    state : Complex[Array, " ..."]
        Optimizer state containing accumulated squared gradients
    learning_rate : float, optional
        Learning rate for parameter updates.
        Default is 0.01.
    eps : float, optional
        Small value to avoid division by zero.
        Default is 1e-8.

    Returns
    -------
    new_params : Complex[Array, " ..."]
        Updated complex-valued parameters
    new_state : Complex[Array, " ..."]
        Updated optimizer state with accumulated gradients

    Notes
    -----
    Algorithm:
    - Update accumulated squared gradients: G = G + |grads|²
    - Calculate adaptive learning rate: lr_adaptive = lr / (√G + ε)
    - Apply update: new_params = params - lr_adaptive * grads
    - Return updated parameters and accumulated gradients
    """
    accumulated_grads = state
    new_accumulated_grads = accumulated_grads + jnp.abs(grads) ** 2
    adaptive_lr = learning_rate / (jnp.sqrt(new_accumulated_grads) + eps)
    new_params = params - adaptive_lr * grads
    return new_params, new_accumulated_grads


@jaxtyped(typechecker=beartype)
def complex_rmsprop(
    params: Complex[Array, " ..."],
    grads: Complex[Array, " ..."],
    state: Complex[Array, " ..."],
    learning_rate: float = 0.001,
    decay_rate: float = 0.9,
    eps: float = 1e-8,
) -> Tuple[Complex[Array, " ..."], Complex[Array, " ..."]]:
    r"""Complex-valued RMSprop optimizer based on Wirtinger derivatives.

    This function performs one step of the RMSprop optimization
    algorithm
    for complex-valued parameters using Wirtinger calculus.

    Parameters
    ----------
    params : Complex[Array, " ..."]
        Current complex-valued parameters
    grads : Complex[Array, " ..."]
        Complex-valued gradients computed using Wirtinger derivatives
    state : Complex[Array, " ..."]
        Optimizer state containing moving average of squared gradients
    learning_rate : float, optional
        Learning rate for parameter updates.
        Default is 0.001.
    decay_rate : float, optional
        Decay rate for moving average of squared gradients.
        Default is 0.9.
    eps : float, optional
        Small value to avoid division by zero.
        Default is 1e-8.

    Returns
    -------
    new_params : Complex[Array, " ..."]
        Updated complex-valued parameters
    new_state : Complex[Array, " ..."]
        Updated optimizer state with moving average

    Notes
    -----
    Algorithm:
    - Update moving average of squared gradients:
        .. math::
        v = \rho \cdot v + (1 - \rho) \cdot |\text{grads}|^2
    - Calculate adaptive learning rate:
        .. math::
        lr_{adaptive} = \frac{lr}{\sqrt{v} + \epsilon}
    - Apply update:
    .. math::
        \text{new\_params} = \text{params} - lr_{adaptive} \cdot
        \text{grads}
    - Return updated parameters and moving average
    """
    moving_avg = state
    new_moving_avg = (
        decay_rate * moving_avg + (1 - decay_rate) * jnp.abs(grads) ** 2
    )
    adaptive_lr = learning_rate / (jnp.sqrt(new_moving_avg) + eps)
    new_params = params - adaptive_lr * grads
    return new_params, new_moving_avg


@jaxtyped(typechecker=beartype)
def init_adam(shape: Tuple) -> OptimizerState:
    """Initialize Adam optimizer state.

    Parameters
    ----------
    shape : Tuple
        Shape of the parameters to be optimized

    Returns
    -------
    state : OptimizerState
        Initialized Adam optimizer state with zero moments and step=0
    """
    return make_optimizer_state(shape)


@jaxtyped(typechecker=beartype)
def init_adagrad(shape: Tuple) -> OptimizerState:
    """Initialize Adagrad optimizer state.

    Parameters
    ----------
    shape : Tuple
        Shape of the parameters to be optimized

    Returns
    -------
    state : OptimizerState
        Initialized Adagrad optimizer state with zero accumulated
        gradients
    """
    return make_optimizer_state(shape)


@jaxtyped(typechecker=beartype)
def init_rmsprop(shape: Tuple) -> OptimizerState:
    """Initialize RMSprop optimizer state.

    Parameters
    ----------
    shape : Tuple
        Shape of the parameters to be optimized

    Returns
    -------
    state : OptimizerState
        Initialized RMSprop optimizer state with zero moving average
    """
    return make_optimizer_state(shape)


@jaxtyped(typechecker=beartype)
def adam_update(
    params: Complex[Array, " ..."],
    grads: Complex[Array, " ..."],
    state: OptimizerState,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    eps: float = 1e-8,
) -> Tuple[Complex[Array, " ..."], OptimizerState]:
    """Update parameters using Adam optimizer with Wirtinger
    derivatives.

    Parameters
    ----------
    params : Complex[Array, " ..."]
        Current complex-valued parameters
    grads : Complex[Array, " ..."]
        Complex-valued gradients computed using Wirtinger derivatives
    state : OptimizerState
        Current optimizer state
    learning_rate : float, optional
        Learning rate for parameter updates.
        Default is 0.001.
    beta1 : float, optional
        Exponential decay rate for first moment estimates.
        Default is 0.9.
    beta2 : float, optional
        Exponential decay rate for second moment estimates.
        Default is 0.999.
    eps : float, optional
        Small value to avoid division by zero.
        Default is 1e-8.

    Returns
    -------
    new_params : Complex[Array, " ..."]
        Updated complex-valued parameters
    new_state : OptimizerState
        Updated optimizer state

    Notes
    -----
    Algorithm:
    - Extract current state components (m, v, step)
    - Call complex_adam to perform the update
    - Return updated parameters and state
    """
    m, v, step = state
    new_params, (new_m, new_v, new_step) = complex_adam(
        params, grads, (m, v, step), learning_rate, beta1, beta2, eps
    )
    return new_params, make_optimizer_state(
        shape=new_m.shape, m=new_m, v=new_v, step=new_step
    )


@jaxtyped(typechecker=beartype)
def adagrad_update(
    params: Complex[Array, " ..."],
    grads: Complex[Array, " ..."],
    state: OptimizerState,
    learning_rate: float = 0.01,
    eps: float = 1e-8,
) -> Tuple[Complex[Array, " ..."], OptimizerState]:
    """Update parameters using Adagrad optimizer with Wirtinger
    derivatives.

    Parameters
    ----------
    params : Complex[Array, " ..."]
        Current complex-valued parameters
    grads : Complex[Array, " ..."]
        Complex-valued gradients computed using Wirtinger derivatives
    state : OptimizerState
        Current optimizer state
    learning_rate : float, optional
        Learning rate for parameter updates.
        Default is 0.01.
    eps : float, optional
        Small value to avoid division by zero.
        Default is 1e-8.

    Returns
    -------
    new_params : Complex[Array, " ..."]
        Updated complex-valued parameters
    new_state : OptimizerState
        Updated optimizer state

    Notes
    -----
    Algorithm:
    - Extract current state components (m, v, step)
    - Call complex_adagrad to perform the update
    - Return updated parameters and state
    """
    m, v, step = state
    new_params, new_v = complex_adagrad(params, grads, v, learning_rate, eps)
    return new_params, make_optimizer_state(
        shape=new_v.shape, m=m, v=new_v, step=step + 1
    )


@jaxtyped(typechecker=beartype)
def rmsprop_update(
    params: Complex[Array, " ..."],
    grads: Complex[Array, " ..."],
    state: OptimizerState,
    learning_rate: float = 0.001,
    decay_rate: float = 0.9,
    eps: float = 1e-8,
) -> Tuple[Complex[Array, " ..."], OptimizerState]:
    """Update parameters using RMSprop optimizer with Wirtinger
    derivatives.

    Parameters
    ----------
    params : Complex[Array, " ..."]
        Current complex-valued parameters
    grads : Complex[Array, " ..."]
        Complex-valued gradients computed using Wirtinger derivatives
    state : OptimizerState
        Current optimizer state
    learning_rate : float, optional
        Learning rate for parameter updates.
        Default is 0.001.
    decay_rate : float, optional
        Decay rate for moving average of squared gradients.
        Default is 0.9.
    eps : float, optional
        Small value to avoid division by zero.
        Default is 1e-8.

    Returns
    -------
    new_params : Complex[Array, " ..."]
        Updated complex-valued parameters
    new_state : OptimizerState
        Updated optimizer state

    Notes
    -----
    Algorithm:
    - Extract current state components (m, v, step)
    - Call complex_rmsprop to perform the update
    - Return updated parameters and state
    """
    m, v, step = state
    new_params, new_v = complex_rmsprop(
        params, grads, v, learning_rate, decay_rate, eps
    )
    return new_params, make_optimizer_state(
        shape=new_v.shape, m=m, v=new_v, step=step + 1
    )
