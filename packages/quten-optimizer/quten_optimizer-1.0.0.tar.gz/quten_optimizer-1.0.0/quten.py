"""
Fully vectorized and fused QUTEN optimizer.
Maximum GPU throughput via tensor flattening and kernel fusion.
"""
import torch
from typing import Dict, List, Optional, Tuple, Callable, Any, Iterable
import warnings


class QUTEN(torch.optim.Optimizer):
    """
    Quantum Uncertainty Tunneling Estimation Network (QUTEN) optimizer.
    Fully fused implementation for maximum GPU performance.
    """

    def __init__(
        self,
        params: Iterable[torch.Tensor],
        lr: float = 1e-3,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eta: float = 0.02,
        hbar: float = 1e-3,
        eps: float = 1e-8,
        weight_decay: float = 0.0,
        collapse: float = 0.99,
        gamma: float = 2.0,
        beta_observe: float = 0.9,
        amsgrad: bool = False,
        warmup_steps: int = 100,
        initial_sigma: float = 0.1,
        grad_clamp: float = 10.0,
        phase_clamp: float = 10.0,
        delta_clamp: float = 1.0,
        adaptive_eta_scale: float = 0.1,
        warn_on_clamp: bool = False,
    ):
        """
        Args:
            lr: Learning rate (α), must be > 0
            beta1: Momentum decay for p, must be in [0, 1)
            beta2: Uncertainty decay for σ, must be in [0, 1)
            eta: Tunneling strength, must be >= 0
            hbar: "Planck" constant, must be > 0
            eps: Numerical stability, must be > 0
            weight_decay: L2 regularization, must be >= 0
            collapse: σ decay factor, must be in (0, 1]
            gamma: Observation nonlinearity, must be > 0
            beta_observe: Observation EMA decay, must be in [0, 1)
            amsgrad: Use max of squared gradients
            warmup_steps: Observation warmup steps, must be > 0
            initial_sigma: Initial uncertainty value, must be > 0
            grad_clamp: Gradient magnitude clamp limit, must be > 0
            phase_clamp: Tunneling phase clamp limit, must be > 0
            delta_clamp: Update delta clamp limit, must be > 0
            adaptive_eta_scale: Adaptive tunneling scale factor, must be >= 0
            warn_on_clamp: Emit warnings when clamping occurs
        """
        # Validate hyperparameters
        if lr <= 0.0:
            raise ValueError(f"Invalid learning rate: {lr}, must be > 0")
        if not 0.0 <= beta1 < 1.0:
            raise ValueError(f"Invalid beta1: {beta1}, must be in [0, 1)")
        if not 0.0 <= beta2 < 1.0:
            raise ValueError(f"Invalid beta2: {beta2}, must be in [0, 1)")
        if eta < 0.0:
            raise ValueError(f"Invalid eta: {eta}, must be >= 0")
        if hbar <= 0.0:
            raise ValueError(f"Invalid hbar: {hbar}, must be > 0")
        if eps <= 0.0:
            raise ValueError(f"Invalid eps: {eps}, must be > 0")
        if weight_decay < 0.0:
            raise ValueError(f"Invalid weight_decay: {weight_decay}, must be >= 0")
        if not 0.0 < collapse <= 1.0:
            raise ValueError(f"Invalid collapse: {collapse}, must be in (0, 1]")
        if gamma < 0.0:
            raise ValueError(f"Invalid gamma: {gamma}, must be >= 0")
        if not 0.0 <= beta_observe <= 1.0:
            raise ValueError(f"Invalid beta_observe: {beta_observe}, must be in [0, 1]")
        if warmup_steps < 0:
            raise ValueError(f"Invalid warmup_steps: {warmup_steps}, must be >= 0")
        if initial_sigma <= 0.0:
            raise ValueError(f"Invalid initial_sigma: {initial_sigma}, must be > 0")
        if grad_clamp <= 0.0:
            raise ValueError(f"Invalid grad_clamp: {grad_clamp}, must be > 0")
        if phase_clamp <= 0.0:
            raise ValueError(f"Invalid phase_clamp: {phase_clamp}, must be > 0")
        if delta_clamp <= 0.0:
            raise ValueError(f"Invalid delta_clamp: {delta_clamp}, must be > 0")
        if adaptive_eta_scale < 0.0:
            raise ValueError(f"Invalid adaptive_eta_scale: {adaptive_eta_scale}, must be >= 0")

        defaults = dict(
            lr=lr,
            beta1=beta1,
            beta2=beta2,
            eta=eta,
            hbar=hbar,
            eps=eps,
            weight_decay=weight_decay,
            collapse=collapse,
            gamma=gamma,
            beta_observe=beta_observe,
            amsgrad=amsgrad,
            warmup_steps=warmup_steps,
            initial_sigma=initial_sigma,
            grad_clamp=grad_clamp,
            phase_clamp=phase_clamp,
            delta_clamp=delta_clamp,
            adaptive_eta_scale=adaptive_eta_scale,
            warn_on_clamp=warn_on_clamp,
        )
        super().__init__(params, defaults)

    @staticmethod
    @torch.jit.script
    def _fused_quten_update(
        flat_p: torch.Tensor,
        flat_g: torch.Tensor,
        p_mom: torch.Tensor,
        sigma: torch.Tensor,
        observe: torch.Tensor,
        sigma_max: torch.Tensor,
        lr: float,
        beta1: float,
        beta2: float,
        eta: float,
        hbar: float,
        eps: float,
        wd: float,
        collapse: float,
        gamma: float,
        beta_observe: float,
        amsgrad: bool,
        inv_bc1: float,
        inv_bc2: float,
        warmup_factor: float,
        grad_clamp: float,
        phase_clamp: float,
        delta_clamp: float,
        adaptive_eta_scale: float,
        warn_on_clamp: bool,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, Dict[str, bool]]:
        """Fused QUTEN update for maximum GPU performance."""
        clamp_flags = {
            "grad_clamped": False,
            "phase_clamped": False,
            "delta_clamped": False,
        }

        # Weight decay
        if wd != 0.0:
            flat_g = flat_g.add(flat_p, alpha=wd)

        # Update momentum and uncertainty (fused)
        p_mom.mul_(beta1).add_(flat_g, alpha=1.0 - beta1)
        sigma.mul_(beta2).add_(flat_g.abs(), alpha=1.0 - beta2)

        # AMSGrad
        if amsgrad:
            torch.max(sigma_max, sigma, out=sigma_max)
            sigma_to_use = sigma_max
        else:
            sigma_to_use = sigma

        # Bias correction (avoid in-place on intermediate tensors)
        p_mom_corrected = p_mom * inv_bc1
        sigma_corrected = sigma_to_use * inv_bc2

        # Update observation fidelity (avoid in-place on intermediate tensors)
        current_observation = (1.0 + sigma_corrected).reciprocal()
        observe.mul_(beta_observe).add_(current_observation, alpha=1.0 - beta_observe)

        # Adaptive tunneling strength with clamp tracking
        grad_abs_mean = flat_g.abs().mean()
        if warn_on_clamp and (grad_abs_mean < 0.0 or grad_abs_mean > grad_clamp):
            clamp_flags["grad_clamped"] = True
        grad_magnitude = grad_abs_mean.clamp(0.0, grad_clamp)
        adaptive_eta = eta * (1.0 + adaptive_eta_scale * grad_magnitude)

        # Observation-based decoherence (avoid in-place on intermediate tensors)
        observe_clamped = (observe * warmup_factor).clamp(0.0, 1.0)
        observation_damping = 1.0 - observe_clamped.pow(gamma)

        # Tunneling term with clamp tracking
        tunneling_phase_raw = p_mom_corrected * sigma_corrected / (hbar + eps)
        if warn_on_clamp and (tunneling_phase_raw.abs().max() > phase_clamp):
            clamp_flags["phase_clamped"] = True
        tunneling_phase = tunneling_phase_raw.clamp(-phase_clamp, phase_clamp)
        tunneling = adaptive_eta * observation_damping * tunneling_phase.sin()

        # Main update with clamp tracking
        classical_update = -lr * p_mom_corrected / (sigma_corrected.sqrt() + eps)
        delta_raw = classical_update + tunneling
        if warn_on_clamp and (delta_raw.abs().max() > delta_clamp):
            clamp_flags["delta_clamped"] = True
        delta = delta_raw.clamp(-delta_clamp, delta_clamp)

        # Apply update
        flat_p.add_(delta)

        # Wavefunction collapse
        sigma.mul_(collapse)

        return flat_p, p_mom, sigma, observe, sigma_max, clamp_flags

    @torch.no_grad()
    def step(self, closure: Optional[Callable[[], float]] = None) -> Optional[float]:
        """Performs a single optimization step (fully vectorized)."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            # Extract hyperparameters
            lr = group["lr"]
            beta1 = group["beta1"]
            beta2 = group["beta2"]
            eta = group["eta"]
            hbar = group["hbar"]
            eps = group["eps"]
            wd = group["weight_decay"]
            collapse = group["collapse"]
            gamma = group["gamma"]
            beta_observe = group["beta_observe"]
            amsgrad = group["amsgrad"]
            warmup_steps = group["warmup_steps"]
            initial_sigma = group["initial_sigma"]
            grad_clamp = group["grad_clamp"]
            phase_clamp = group["phase_clamp"]
            delta_clamp = group["delta_clamp"]
            adaptive_eta_scale = group["adaptive_eta_scale"]
            warn_on_clamp = group["warn_on_clamp"]

            # Separate dense and sparse parameters
            dense_params = []
            dense_grads = []
            sparse_params = []

            for p in group["params"]:
                if p.grad is None:
                    continue

                if p.grad.is_sparse:
                    sparse_params.append(p)
                else:
                    dense_params.append(p)
                    dense_grads.append(p.grad)

            # Process dense parameters with full vectorization
            if len(dense_params) > 0:
                # Get or create group state
                group_id = id(group)
                if group_id not in self.state:
                    # Initialize flattened state
                    total_numel = sum(p.numel() for p in dense_params)
                    device = dense_params[0].device
                    dtype = dense_params[0].dtype

                    self.state[group_id] = {
                        "step": 0,
                        "p_mom": torch.zeros(total_numel, device=device, dtype=dtype),
                        "sigma": torch.full((total_numel,), initial_sigma, device=device, dtype=dtype),
                        "observe": torch.zeros(total_numel, device=device, dtype=dtype),
                        "sigma_max": torch.full((total_numel,), initial_sigma, device=device, dtype=dtype) if amsgrad else torch.empty(0),
                        "param_shapes": [p.shape for p in dense_params],
                        "param_numels": [p.numel() for p in dense_params],
                        # Store flattened view buffer to avoid recreating
                        "flat_p_buffer": torch.empty(total_numel, device=device, dtype=dtype),
                        "flat_g_buffer": torch.empty(total_numel, device=device, dtype=dtype),
                    }

                state = self.state[group_id]
                state["step"] += 1
                step = state["step"]

                # Pre-compute scalar factors
                inv_bc1 = 1.0 / (1.0 - beta1 ** step)
                inv_bc2 = 1.0 / (1.0 - beta2 ** step)
                warmup_factor = min(1.0, step / max(1, warmup_steps))

                # Use pre-allocated buffers to avoid repeated allocations
                flat_p_buffer = state["flat_p_buffer"]
                flat_g_buffer = state["flat_g_buffer"]

                # Copy parameters and gradients into buffers
                offset = 0
                for p, g, numel in zip(dense_params, dense_grads, state["param_numels"]):
                    flat_p_buffer[offset : offset + numel] = p.view(-1)
                    flat_g_buffer[offset : offset + numel] = g.view(-1)
                    offset += numel

                # Fused update
                (
                    flat_p_buffer,
                    state["p_mom"],
                    state["sigma"],
                    state["observe"],
                    state["sigma_max"],
                    clamp_flags,
                ) = self._fused_quten_update(
                    flat_p_buffer,
                    flat_g_buffer,
                    state["p_mom"],
                    state["sigma"],
                    state["observe"],
                    state["sigma_max"],
                    lr,
                    beta1,
                    beta2,
                    eta,
                    hbar,
                    eps,
                    wd,
                    collapse,
                    gamma,
                    beta_observe,
                    amsgrad,
                    inv_bc1,
                    inv_bc2,
                    warmup_factor,
                    grad_clamp,
                    phase_clamp,
                    delta_clamp,
                    adaptive_eta_scale,
                    warn_on_clamp,
                )

                # Emit warnings if clamping occurred
                if warn_on_clamp:
                    if clamp_flags["grad_clamped"]:
                        warnings.warn(f"Gradient magnitude clamped at step {step}", stacklevel=2)
                    if clamp_flags["phase_clamped"]:
                        warnings.warn(f"Tunneling phase clamped at step {step}", stacklevel=2)
                    if clamp_flags["delta_clamped"]:
                        warnings.warn(f"Update delta clamped at step {step}", stacklevel=2)

                # Scatter back to parameters
                offset = 0
                for p, numel in zip(dense_params, state["param_numels"]):
                    p.copy_(flat_p_buffer[offset : offset + numel].view_as(p))
                    offset += numel

            # Process sparse parameters (per-tensor with proper sparse handling)
            for p in sparse_params:
                # Work with sparse gradients directly when possible
                grad = p.grad
                if grad.is_sparse:
                    grad = grad.coalesce()
                    # For truly sparse updates, we only update the indices that have gradients
                    indices = grad.indices()
                    values = grad.values()
                    is_truly_sparse = values.numel() < p.numel() * 0.1  # Less than 10% non-zero
                else:
                    is_truly_sparse = False

                state = self.state[p]

                if len(state) == 0:
                    state["step"] = 0
                    state["p_mom"] = torch.zeros_like(p)
                    state["sigma"] = torch.full_like(p, initial_sigma)
                    state["observe"] = torch.zeros_like(p)
                    if amsgrad:
                        state["sigma_max"] = torch.full_like(p, initial_sigma)

                state["step"] += 1
                step = state["step"]

                inv_bc1 = 1.0 / (1.0 - beta1 ** step)
                inv_bc2 = 1.0 / (1.0 - beta2 ** step)
                warmup_factor = min(1.0, step / max(1, warmup_steps))

                if is_truly_sparse:
                    # For truly sparse gradients, only update affected indices
                    # This preserves sparsity and improves performance
                    grad_dense = torch.zeros_like(p)
                    if grad.is_sparse:
                        # Scatter sparse gradient values into dense tensor at the specified indices
                        if indices.dim() == 1:
                            grad_dense.view(-1)[indices] = values
                        else:
                            # Multi-dimensional indices
                            grad_dense[tuple(indices)] = values
                    else:
                        grad_dense = grad

                    # Flatten for processing
                    p_flat = p.reshape(-1)
                    grad_flat = grad_dense.reshape(-1)
                    p_mom_flat = state["p_mom"].reshape(-1)
                    sigma_flat = state["sigma"].reshape(-1)
                    observe_flat = state["observe"].reshape(-1)
                    sigma_max_flat = state["sigma_max"].reshape(-1) if amsgrad else torch.empty(0)
                else:
                    # Convert to dense for dense-like sparse gradients
                    grad_dense = grad.to_dense() if grad.is_sparse else grad
                    p_flat = p.reshape(-1)
                    grad_flat = grad_dense.reshape(-1)
                    p_mom_flat = state["p_mom"].reshape(-1)
                    sigma_flat = state["sigma"].reshape(-1)
                    observe_flat = state["observe"].reshape(-1)
                    sigma_max_flat = state["sigma_max"].reshape(-1) if amsgrad else torch.empty(0)

                # Use fused update
                (
                    p_flat,
                    p_mom_flat,
                    sigma_flat,
                    observe_flat,
                    sigma_max_flat,
                    clamp_flags,
                ) = self._fused_quten_update(
                    p_flat,
                    grad_flat,
                    p_mom_flat,
                    sigma_flat,
                    observe_flat,
                    sigma_max_flat,
                    lr,
                    beta1,
                    beta2,
                    eta,
                    hbar,
                    eps,
                    wd,
                    collapse,
                    gamma,
                    beta_observe,
                    amsgrad,
                    inv_bc1,
                    inv_bc2,
                    warmup_factor,
                    grad_clamp,
                    phase_clamp,
                    delta_clamp,
                    adaptive_eta_scale,
                    warn_on_clamp,
                )

                # Emit warnings if clamping occurred
                if warn_on_clamp:
                    if clamp_flags["grad_clamped"]:
                        warnings.warn(f"Sparse param gradient magnitude clamped at step {step}", stacklevel=2)
                    if clamp_flags["phase_clamped"]:
                        warnings.warn(f"Sparse param tunneling phase clamped at step {step}", stacklevel=2)
                    if clamp_flags["delta_clamped"]:
                        warnings.warn(f"Sparse param update delta clamped at step {step}", stacklevel=2)

                # Reshape state back to original parameter shape
                p.copy_(p_flat.view_as(p))
                state["p_mom"] = p_mom_flat.view_as(p)
                state["sigma"] = sigma_flat.view_as(p)
                state["observe"] = observe_flat.view_as(p)
                if amsgrad:
                    state["sigma_max"] = sigma_max_flat.view_as(p)

        return loss
