from __future__ import annotations

# third party
import numpy as np
# built-in
from abc import ABC, abstractmethod
import logging
# local
from .machinery import (
    Tensor, TensorValuedFunction, _shape_safe_grad, _update_ctx, sqrt
)
from . import general_math

# *----------------------------------------------------*
#                        GLOBALS
# *----------------------------------------------------*

_logger = logging.getLogger(__name__)

# *----------------------------------------------------*
#               CLASSES & HELPER FUNCTIONS
# *----------------------------------------------------*

class Layer(ABC):
    """A module with (optional) trainable parameters and (optional) non-trainable buffers."""

    def __init__(self, *, training: bool = True) -> None:
        self._training = bool(training)

    @property
    def training(self) -> bool:
        # Fallback to True if subclass didn't call super().__init__
        return getattr(self, "_training", True)

    @training.setter
    def training(self, mode: bool) -> None:
        mode = bool(mode)
        prev = getattr(self, "_training", None)
        self._training = mode
        if prev is None or prev != mode:
            self.on_mode_change(mode)

    def train(self) -> Layer:
        self.training = True
        return self

    def eval(self) -> Layer:
        self.training = False
        return self

    def on_mode_change(self, training: bool) -> None:
        """Subclass hook called when `.training` flips.
        Override in layers like BatchNorm/Dropout if needed.
        """
        pass

    @property
    @abstractmethod
    def parameters(self) -> tuple[Tensor, ...]:
        """Return trainable parameters (possibly empty)."""
        raise NotImplementedError

    def named_buffers(self) -> dict[str, Tensor | np.ndarray]:
        """Return mapping of buffer-name -> Tensor/ndarray (non-trainable). Default: {}."""
        return {}

    def apply_state(
        self,
        *,
        tunable: tuple[np.ndarray, ...] | list[np.ndarray] = (),
        buffers: dict[str, np.ndarray] | None = None,
    ) -> None:
        """Default in-place state load: writes arrays into `parameters` and `named_buffers()` Tensors."""
        # write trainables in-order
        if tunable:
            for t, arr in zip(self.parameters, tunable):
                t.data = np.asarray(arr, dtype=t.data.dtype)

        # write buffers by name (only if buffer is a Tensor)
        if buffers:
            for name, v in self.named_buffers().items():
                if name in buffers and isinstance(v, Tensor):
                    v.data = np.asarray(buffers[name], dtype=v.data.dtype)

class Affine(Layer):
    """Affine (linear) layer implementing Y = X @ W + b.

    This class stores the **transpose** of the usual weight matrix so that
    forward calls use `X @ W` directly when `X.shape == (B, n)` and
    `W.shape == (n, m)`.

    Args:
        fan_in (int): Input feature dimension `n`.
        fan_out (int): Output feature dimension `m`.
        method (str, optional): Initialization method. Currently supports
            `"xavier-glorot-normal"`. Defaults to `"xavier-glorot-normal"`.
        W (Tensor, optional): Optional pre-initialized weight tensor of shape
            `(fan_out, fan_in)`; will be transposed and stored as `(n, m)`.
        b (Tensor, optional): Optional pre-initialized bias tensor of shape `(m,)`.

    Attributes:
        W (Tensor): Weight matrix stored as shape `(n, m)`.
        b (Tensor): Bias vector stored as shape `(m,)`.
    """

    def __init__(self, fan_in: int, fan_out: int, method="xavier-glorot-normal", W: Tensor = None, b: Tensor = None):
        super().__init__()

        init_fn = {
            "xavier-glorot-normal": self._xavier_glorot_normal
        }[method]
        W_init, b_init = init_fn(fan_in, fan_out)

        # note, we transpose because X.shape == (B, n)
        # and initially W.shape == (m, n)
        # we want to get Y == (B, m), so we must do X @ W.T, thus storing the transpose
        self.W = (W if W is not None else W_init).T # (n, m)
        self.b = (b if b is not None else b_init)

        _logger.debug(
            "Affine initialized: fan_in=%d, fan_out=%d, method=%s, W.shape=%s, b.shape=%s",
            fan_in, fan_out, method, getattr(self.W, "shape", None), getattr(self.b, "shape", None)
        )

    @property
    def parameters(self) -> tuple[Tensor, Tensor]:
        """Return the trainable parameters `(W, b)`.

        Returns:
            tuple[Tensor, Tensor]: Weight `(n, m)` and bias `(m,)`.
        """
        return self.W, self.b

    @staticmethod
    def _xavier_glorot_normal(fan_in, fan_out) -> tuple[Tensor, Tensor]:
        """Initialize weights and bias using Xavier/Glorot normal.

        Args:
            fan_in (int): Input feature dimension.
            fan_out (int): Output feature dimension.

        Returns:
            tuple[Tensor, Tensor]: `(W, b)` where `W.shape == (fan_out, fan_in)` and
            `b.shape == (fan_out,)`, both wrapped as `Tensor` with `requires_grad=True`.
        """
        std = np.sqrt(2/(fan_in+fan_out))
        _logger.debug("Xavier/Glorot normal init: fan_in=%d, fan_out=%d, std=%.6f", fan_in, fan_out, std)
        W = np.random.normal(0, std, (fan_out, fan_in))
        b = np.zeros((fan_out,))
        return Tensor(W, requires_grad=True), Tensor(b, requires_grad=True)

    @staticmethod
    def _affine(X: np.ndarray, W: np.ndarray, b: np.ndarray, *, context: dict | None = None) -> np.ndarray:
        """Compute the affine map `Y = X @ W + b`.

        Args:
            X (np.ndarray): Input data of shape `(B, n)` (or `(n,)` if unbatched).
            W (np.ndarray): Weight matrix of shape `(n, m)`.
            b (np.ndarray): Bias vector of shape `(m,)` (broadcast to `(B, m)`).

        Returns:
            np.ndarray: Output array `Y` with shape `(B, m)` (or `(m,)` if unbatched).
        """
        # X: (B, n)
        # W: (n, m)
        # b: (m,) <-- is broadcast to (B, m)
        _logger.debug("Affine forward: X.shape=%s, W.shape=%s, b.shape=%s", X.shape, W.shape, b.shape)
        out = X @ W + b
        _logger.debug("Affine forward: Y.shape=%s", out.shape)

        # cache useful intermediates for backward reuse (avoid extra transposes):
        # keep it lazy to avoid any cost if grads are disabled
        _update_ctx(context, WT=lambda: W.T, XT=lambda: X.T)

        return out

    @staticmethod
    @_shape_safe_grad
    def _affine_grad(upstream_grad: np.ndarray, X: np.ndarray, W: np.ndarray, b: np.ndarray, *, context: dict | None = None):
        """Compute gradients of `Y = X @ W + b`.

        Gradients are computed w.r.t. inputs `(X, W, b)` given `upstream_grad = dL/dY`.

        Args:
            upstream_grad (np.ndarray): Upstream gradient `dL/dY` with shape `(B, m)` for
                batched `X` or `(m,)` for single-sample.
            X (np.ndarray): Input `X` with shape `(B, n)` or `(n,)`.
            W (np.ndarray): Weight matrix with shape `(n, m)`.
            b (np.ndarray): Bias vector with shape `(m,)`.

        Returns:
            tuple[np.ndarray, np.ndarray, np.ndarray]:
                - `grad_X`: Same shape as `X` -> `(B, n)` or `(n,)`
                - `grad_W`: Shape `(n, m)`
                - `grad_b`: Shape `(m,)`

        Raises:
            ValueError: If `X` is not 1D or 2D.
        """
        _logger.debug(
            "Affine backward: upstream_grad.shape=%s, X.shape=%s, W.shape=%s, b.shape=%s",
            getattr(upstream_grad, "shape", None), getattr(X, "shape", None),
            getattr(W, "shape", None), getattr(b, "shape", None)
        )

        ctx = context or {}
        WT = ctx.get("WT", W.T)
        XT = ctx.get("XT", X.T)

        if X.ndim == 1:
            # Single sample: X:(n,), upstream_grad:(m,)
            _logger.debug("Affine backward path: single sample")
            g = upstream_grad
            grad_X = g @ WT
            grad_W = np.outer(X, g)
            grad_b = g
        elif X.ndim == 2:
            # Batched: X:(B,n), upstream_grad:(B,m)
            _logger.debug("Affine backward path: batched")
            G = upstream_grad
            grad_X = G @ WT          # (..., n)
            grad_W = XT @ G          # (n, m)
            grad_b = G.sum(axis=0)
        else:
            raise ValueError(f"X must be 1D or 2D, got {X.ndim}D")
        _logger.debug("Affine backward: grad_X.shape=%s, grad_W.shape=%s, grad_b.shape=%s",
                      getattr(grad_X, "shape", None), getattr(grad_W, "shape", None),
                      getattr(grad_b, "shape", None))
        return grad_X, grad_W, grad_b

    def __call__(self, X: Tensor) -> Tensor:
        """Apply the affine transform to input tensor `X`.

        Validates input dimensionality and delegates to `TensorValuedFunction`
        with `_affine` as the forward and `_affine_grad` as the backward.

        Args:
            X (Tensor): Input tensor with `X.data.ndim in {1, 2}`. If 1D, must
                have shape `(n,)`; if 2D, must have shape `(B, n)` where
                `n == self.W.shape[0]`.

        Returns:
            Tensor: Output tensor of shape `(m,)` for 1D input or `(B, m)` for 2D input.

        Raises:
            ValueError: If `X.data` is not 1D or 2D, or if the last dimension
                does not match `self.W.shape[0]`.
        """
        _logger.debug("Affine __call__: X.data.ndim=%s, X.data.shape=%s, W.shape=%s",
                      getattr(X.data, "ndim", None), getattr(X.data, "shape", None),
                      getattr(self.W, "shape", None))
        if X.data.ndim == 1:
            if X.data.shape != (self.W.shape[0],):
                raise ValueError(
                    f"Incompatible dimensions. Expected a {self.W.shape[0]}-dimensional tensor; "
                    f"received {X.data.shape[0]}"
                )
        elif X.data.ndim == 2:
            if X.data.shape[1] != self.W.shape[0]:
                raise ValueError(
                    f"Incompatible dims. Expected last dim {self.W.shape[0]}; "
                    f"received {X.data.shape[1]}"
                )
        else:
            raise ValueError(f"x must be 1D or 2D, got {X.data.ndim}D")
        out = TensorValuedFunction(self._affine, self._affine_grad)(X, self.W, self.b)
        _logger.debug("Affine __call__: output Tensor created")
        return out

class Dropout(Layer):
    """Inverted Dropout layer.

    During training, zeros out each element of the input with probability `p`
    and scales the survivors by `1/(1-p)` so that the expected activation
    stays constant. In eval mode, this is an identity map.

    Args:
        p (float): Drop probability in [0, 1]. Defaults to 0.5.
        seed (int | None): Optional RNG seed for reproducibility.
        training (bool): If True, applies dropout; otherwise acts as identity.
                         Defaults to True.
    """

    def __init__(self, p: float = 0.5, *, seed: int | None = None, training: bool = True) -> None:
        super().__init__(training=training)
        if not (0.0 <= float(p) <= 1.0):
            raise ValueError(f"Dropout p must be in [0, 1], got {p}")
        self.p: float = float(p)
        self.seed = np.random.randint(0, 2**32 - 1) if seed is None else int(seed)
        self._rng: np.random.Generator = np.random.default_rng(self.seed)
        _logger.debug("Dropout initialized: p=%.4f, training=%s, seed=%s",
              self.p, self.training, self.seed)

    def on_mode_change(self, training: bool):
        if training:
            _logger.debug("Dropout set to training mode")
        else:
            _logger.debug("Dropout set to inference mode")

    @property
    def parameters(self) -> tuple[Tensor, ...]:
        return ()  # no trainables

    def named_buffers(self) -> dict[str, np.ndarray]:
        return {
            "p":        np.asarray(float(self.p), dtype=np.float64),
            "seed": np.asarray(self.seed, dtype=np.int32)
        }
    
    def apply_state(self, *, tunable=(), buffers=None) -> None:
        if buffers:
            if "p" in buffers:
                self.p = float(np.asarray(buffers["p"]).item())
            if "training" in buffers:
                self.training = bool(int(np.asarray(buffers["training"]).item()))
            if "seed" in buffers:
                seed_val = int(np.asarray(buffers["seed"]).item())
                self.seed = seed_val
                self._rng = np.random.default_rng(seed_val)

    @staticmethod
    def _dropout(X: np.ndarray, mask: np.ndarray, scale: np.ndarray, *, context: dict | None = None) -> np.ndarray:
        """Forward: elementwise masked scaling."""
        _logger.debug(
            "Dropout forward: X.shape=%s, mask.shape=%s, scale=%s",
            getattr(X, "shape", None), getattr(mask, "shape", None), getattr(scale, "item", lambda: scale)()
        )

        _update_ctx(context, mask=mask, scale=scale)

        return X * (mask * scale) 

    @staticmethod
    @_shape_safe_grad
    def _dropout_grad(upstream_grad: np.ndarray, X: np.ndarray, mask: np.ndarray, scale: np.ndarray, *, context: dict | None = None):
        """Backward: dL/dX = upstream * mask * scale. No grads for mask/scale."""
        _logger.debug(
            "Dropout backward: upstream_grad.shape=%s, X.shape=%s, mask.shape=%s, scale=%s",
            getattr(upstream_grad, "shape", None), getattr(X, "shape", None),
            getattr(mask, "shape", None), getattr(scale, "item", lambda: scale)()
        )
        # elementwise upstream mult is by the same logic as for, say, relu
        grad_X = upstream_grad * (mask * scale) # (mask * scale) is the local grad
        # mask/scale are not trainable; return zeros of matching shapes
        return grad_X, np.zeros_like(mask), np.zeros_like(scale)

    def __call__(self, X: Tensor) -> Tensor:
        """Apply dropout to `X` in training mode; identity in eval mode.

        Supports 1D `(n,)` and 2D `(B, n)` inputs.
        """
        if not isinstance(X, Tensor):
            raise TypeError(f"Dropout expects a Tensor, got {type(X)}")

        x = X.data
        if x.ndim not in (1, 2):
            raise ValueError(f"Dropout only supports 1D/2D inputs, got {x.ndim}D")

        # Eval mode or p == 0 -> identity
        if (not self.training) or (self.p <= 0.0):
            _logger.debug("Dropout passthrough (eval mode or p<=0).")
            return X

        keep_p = 1.0 - self.p
        if keep_p <= 0.0:
            # degenerate case: drop everything
            _logger.warning("Dropout p=1.0: output will be all zeros.")
            mask_arr = np.zeros_like(x, dtype=x.dtype)
            scale_arr = np.asarray(1.0, dtype=x.dtype)  # irrelevant cuz output is zero anyway
        else:
            # elementwise Bernoulli mask and inverted scaling (note we sample uniformly between 0 & 1)
            mask_arr = (self._rng.random(x.shape) < keep_p).astype(x.dtype, copy=False)
            scale_arr = np.asarray(1.0 / keep_p, dtype=x.dtype)

        # wrap mask/scale as non-trainable Tensors so the autograd context saves them
        mask = Tensor(mask_arr, requires_grad=False)
        scale = Tensor(scale_arr, requires_grad=False)

        out = TensorValuedFunction(self._dropout, self._dropout_grad)(X, mask, scale)
        _logger.debug("Dropout __call__: output Tensor created with shape=%s", getattr(out.data, "shape", None))
        return out

class BatchNorm1d(Layer):
    """Batch Normalization for 2D inputs shaped (B, F).

    Normalizes each feature across the batch:
        y = gamma * (x - mu) / sqrt(var + eps) + beta

    Running statistics (EMA) are updated only in training mode:
        running = (1 - momentum) * running + momentum * batch_stat

    Args:
        num_features: Feature dimension F.
        eps: Small constant for numerical stability.
        momentum: EMA coefficient for running stats (PyTorch-style).
        gamma, beta: Optional trainable scale/shift (shape (F,)).
        running_variance, running_mean: Optional buffers to resume from.
        training: Initial mode.
    """

    def __init__(
        self,
        num_features: int,
        *,
        eps: float = 1e-5,
        momentum: float = 0.1,
        gamma: Tensor | None = None,
        beta: Tensor | None = None,
        running_variance: Tensor | None = None,
        running_mean: Tensor | None = None,
        training: bool = True,
    ) -> None:
        super().__init__(training=training)

        _logger.debug("BN1d.__init__: F=%d, eps=%g, momentum=%.3f, has_gamma=%s, has_beta=%s, "
                      "has_runvar=%s, has_runmean=%s, training=%s",
                      int(num_features), float(eps), float(momentum),
                      gamma is not None, beta is not None,
                      running_variance is not None, running_mean is not None, bool(training))

        self.num_features = int(num_features)
        self.momentum = float(momentum)

        # -- tuned --------------------------------------------------
        self.gamma = Tensor(np.ones((self.num_features,), dtype=np.float64)
                            if gamma is None else gamma.data,
                            requires_grad=True)

        self.beta  = Tensor(np.zeros((self.num_features,), dtype=np.float64)
                            if beta  is None else beta.data,
                            requires_grad=True)

        self.eps = Tensor(eps, requires_grad=False)
        # -------------------------------------------------------------

        # -- accumulated ----------------------------------------------
        self.running_variance = Tensor(np.ones((self.num_features,),  dtype=np.float64)
                                       if running_variance is None else running_variance.data,
                                       requires_grad=False)

        self.running_mean = Tensor(np.zeros((self.num_features,), dtype=np.float64)
                                   if running_mean is None else running_mean.data,
                                   requires_grad=False)
        # -------------------------------------------------------------

        _logger.debug("BN1d.__init__: gamma.shape=%s, beta.shape=%s, run_mean.shape=%s, run_var.shape=%s",
                      self.gamma.data.shape, self.beta.data.shape,
                      self.running_mean.data.shape, self.running_variance.data.shape)

    def on_mode_change(self, training: bool):
        if training:
            _logger.debug("BatchNorm1d set to training mode")
        else:
            _logger.debug("BatchNorm1d set to inference mode")

    @property
    def parameters(self) -> tuple[Tensor, ...]:
        return (self.gamma, self.beta)

    def named_buffers(self) -> dict[str, Tensor]:
        return {
            "running_mean": self.running_mean,
            "running_variance": self.running_variance,
        }

    def __call__(self, X: Tensor) -> Tensor:
        """Apply BN over the batch axis for (B, F) input.

        In training:
            - compute per-feature batch mean/var (axis=0)
            - update running stats via EMA
            - normalize using batch stats

        In eval:
            - normalize using running stats only
        """ 
        x = X.data
        if x.ndim != 2 or x.shape[1] != self.num_features:
            raise ValueError(f"BatchNorm1d expects input of shape (B, {self.num_features}); got {x.shape}")

        _logger.debug("BN1d.__call__: training=%s, X.shape=%s", self.training, x.shape)

        if self.training:
            mu  = general_math.mean(X, axis=0)   # (F,)
            var = general_math.variance(X, axis=0)  # (F,)
            _logger.debug("BN1d.__call__: batch mu.shape=%s, var.shape=%s", mu.data.shape, var.data.shape)

            # EMA update: new = (1 - m)*old + m*current  -> ewma(old, current, beta=1-m)
            self.running_mean.data = general_math.ewma(self.running_mean.data,     mu.data,  beta=1.0 - self.momentum)
            self.running_variance.data = general_math.ewma(self.running_variance.data, var.data, beta=1.0 - self.momentum)
            _logger.debug("BN1d.__call__: updated running stats (momentum=%.3f)", self.momentum)

            used_mu, used_var = mu, var
        else:
            used_mu, used_var = self.running_mean, self.running_variance
            _logger.debug("BN1d.__call__: using running stats")

        X_hat = (X - used_mu) / sqrt(used_var + self.eps)
        out = X_hat * self.gamma + self.beta
        _logger.debug("BN1d.__call__: out.shape=%s", getattr(out.data, "shape", None))
        return out


__all__ = [
    "Layer",
    "Affine",
    "Dropout",
    "BatchNorm1d"
]

if __name__ == "__main__":
    pass
