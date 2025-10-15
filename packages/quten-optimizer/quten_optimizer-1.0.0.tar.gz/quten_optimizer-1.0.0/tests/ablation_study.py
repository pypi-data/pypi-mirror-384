"""
Comprehensive ablation study for QUTEN optimizer.
Tests each component systematically to validate contributions.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
import time
import json
import warnings
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from quten import QUTEN


@dataclass
class AblationConfig:
    """Configuration for a single ablation experiment."""
    name: str
    description: str
    optimizer_class: str  # "QUTEN", "Adam", "AdamW", "SGD"
    optimizer_kwargs: Dict[str, Any]

    def __str__(self):
        return f"{self.name}: {self.description}"


@dataclass
class ExperimentMetrics:
    """Metrics collected during training."""
    # Effectiveness
    train_losses: List[float]
    val_losses: List[float]
    best_val_loss: float
    steps_to_threshold: Optional[int]  # Steps to reach loss < threshold
    final_train_loss: float
    final_val_loss: float
    generalization_gap: float

    # Stability
    nan_count: int
    gradient_norms: List[float]
    update_norms: List[float]
    param_norms: List[float]
    cosine_sim_to_baseline: List[float]

    # QUTEN-specific internals
    sigma_mean: List[float]
    sigma_std: List[float]
    observe_mean: List[float]
    tunneling_mean: List[float]

    # Efficiency
    wall_clock_time: float
    time_per_step: float
    peak_memory_mb: float

    # Config
    config: AblationConfig

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['config'] = asdict(self.config)
        return result


class MetricsTracker:
    """Tracks detailed metrics during training."""

    def __init__(self, track_quten_internals: bool = True):
        self.track_quten_internals = track_quten_internals
        self.reset()

    def reset(self):
        """Reset all tracked metrics."""
        self.train_losses = []
        self.val_losses = []
        self.gradient_norms = []
        self.update_norms = []
        self.param_norms = []
        self.cosine_sim_to_baseline = []

        self.sigma_mean = []
        self.sigma_std = []
        self.observe_mean = []
        self.tunneling_mean = []

        self.nan_count = 0
        self.start_time = None
        self.end_time = None
        self.peak_memory = 0.0

        self.baseline_updates = []  # For cosine similarity

    def start(self):
        """Start timing."""
        self.start_time = time.time()
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

    def end(self):
        """End timing."""
        self.end_time = time.time()
        if torch.cuda.is_available():
            self.peak_memory = torch.cuda.max_memory_allocated() / 1024**2

    def log_train_loss(self, loss: float):
        """Log training loss."""
        if np.isnan(loss) or np.isinf(loss):
            self.nan_count += 1
        self.train_losses.append(loss)

    def log_val_loss(self, loss: float):
        """Log validation loss."""
        self.val_losses.append(loss)

    def log_gradients(self, model: nn.Module):
        """Log gradient norms."""
        total_norm = 0.0
        for p in model.parameters():
            if p.grad is not None:
                total_norm += p.grad.data.norm(2).item() ** 2
        total_norm = total_norm ** 0.5
        self.gradient_norms.append(total_norm)

    def log_parameters(self, model: nn.Module):
        """Log parameter norms."""
        total_norm = 0.0
        for p in model.parameters():
            total_norm += p.data.norm(2).item() ** 2
        total_norm = total_norm ** 0.5
        self.param_norms.append(total_norm)

    def log_update(self, old_params: List[torch.Tensor], new_params: List[torch.Tensor]):
        """Log update norms and compute cosine similarity."""
        # Compute update norm
        total_norm = 0.0
        update_flat = []

        for old_p, new_p in zip(old_params, new_params):
            delta = new_p - old_p
            total_norm += delta.norm(2).item() ** 2
            update_flat.append(delta.flatten())

        total_norm = total_norm ** 0.5
        self.update_norms.append(total_norm)

        # Compute cosine similarity to baseline (if available)
        if len(self.baseline_updates) > 0:
            current_update = torch.cat(update_flat)
            baseline_update = self.baseline_updates[-1]

            cos_sim = F.cosine_similarity(
                current_update.unsqueeze(0),
                baseline_update.unsqueeze(0)
            ).item()
            self.cosine_sim_to_baseline.append(cos_sim)

    def store_baseline_update(self, old_params: List[torch.Tensor], new_params: List[torch.Tensor]):
        """Store baseline optimizer update for comparison."""
        update_flat = []
        for old_p, new_p in zip(old_params, new_params):
            delta = new_p - old_p
            update_flat.append(delta.flatten())
        self.baseline_updates.append(torch.cat(update_flat))

    def log_quten_internals(self, optimizer: QUTEN):
        """Log QUTEN-specific internal state."""
        if not self.track_quten_internals:
            return

        sigma_vals = []
        observe_vals = []

        for group in optimizer.param_groups:
            group_id = id(group)
            if group_id in optimizer.state:
                state = optimizer.state[group_id]
                if 'sigma' in state:
                    sigma_vals.append(state['sigma'].cpu())
                if 'observe' in state:
                    observe_vals.append(state['observe'].cpu())

        if sigma_vals:
            sigma_tensor = torch.cat([s.flatten() for s in sigma_vals])
            self.sigma_mean.append(sigma_tensor.mean().item())
            self.sigma_std.append(sigma_tensor.std().item())

        if observe_vals:
            observe_tensor = torch.cat([o.flatten() for o in observe_vals])
            self.observe_mean.append(observe_tensor.mean().item())

    def create_metrics(self, config: AblationConfig, loss_threshold: float = 0.1) -> ExperimentMetrics:
        """Create ExperimentMetrics from tracked data."""
        # Find steps to threshold
        steps_to_threshold = None
        for i, loss in enumerate(self.train_losses):
            if loss < loss_threshold:
                steps_to_threshold = i
                break

        # Compute generalization gap
        gen_gap = abs(self.train_losses[-1] - self.val_losses[-1]) if self.val_losses else 0.0

        # Compute timing
        wall_clock = self.end_time - self.start_time if self.end_time else 0.0
        time_per_step = wall_clock / len(self.train_losses) if self.train_losses else 0.0

        return ExperimentMetrics(
            train_losses=self.train_losses,
            val_losses=self.val_losses,
            best_val_loss=min(self.val_losses) if self.val_losses else float('inf'),
            steps_to_threshold=steps_to_threshold,
            final_train_loss=self.train_losses[-1] if self.train_losses else float('inf'),
            final_val_loss=self.val_losses[-1] if self.val_losses else float('inf'),
            generalization_gap=gen_gap,
            nan_count=self.nan_count,
            gradient_norms=self.gradient_norms,
            update_norms=self.update_norms,
            param_norms=self.param_norms,
            cosine_sim_to_baseline=self.cosine_sim_to_baseline,
            sigma_mean=self.sigma_mean,
            sigma_std=self.sigma_std,
            observe_mean=self.observe_mean,
            tunneling_mean=self.tunneling_mean,
            wall_clock_time=wall_clock,
            time_per_step=time_per_step,
            peak_memory_mb=self.peak_memory,
            config=config
        )


def create_ablation_configs() -> List[AblationConfig]:
    """Create all ablation study configurations."""

    base_quten = {
        'lr': 0.001,
        'beta1': 0.9,
        'beta2': 0.999,
        'eta': 0.02,
        'hbar': 0.1,
        'eps': 1e-8,
        'weight_decay': 0.0,
        'collapse': 0.99,
        'gamma': 2.0,
        'beta_observe': 0.9,
        'amsgrad': True,
        'warmup_steps': 100,
    }

    configs = [
        # === BASELINES ===
        AblationConfig(
            name="Adam",
            description="Standard Adam optimizer",
            optimizer_class="Adam",
            optimizer_kwargs={'lr': 0.001, 'betas': (0.9, 0.999), 'eps': 1e-8}
        ),
        AblationConfig(
            name="AdamW",
            description="Adam with decoupled weight decay",
            optimizer_class="AdamW",
            optimizer_kwargs={'lr': 0.001, 'betas': (0.9, 0.999), 'eps': 1e-8, 'weight_decay': 1e-4}
        ),
        AblationConfig(
            name="SGD+Momentum",
            description="SGD with momentum",
            optimizer_class="SGD",
            optimizer_kwargs={'lr': 0.01, 'momentum': 0.9, 'nesterov': True}
        ),

        # === FULL QUTEN ===
        AblationConfig(
            name="QUTEN-Full",
            description="Full QUTEN with all components",
            optimizer_class="QUTEN",
            optimizer_kwargs=base_quten.copy()
        ),

        # === ABLATION 1: Tunneling ===
        AblationConfig(
            name="QUTEN-NoTunneling",
            description="QUTEN without tunneling (eta=0)",
            optimizer_class="QUTEN",
            optimizer_kwargs={**base_quten, 'eta': 0.0}
        ),

        # === ABLATION 2: Observation Damping ===
        AblationConfig(
            name="QUTEN-NoObservation",
            description="QUTEN without observation damping (beta_observe=1, gamma=0)",
            optimizer_class="QUTEN",
            optimizer_kwargs={**base_quten, 'beta_observe': 1.0, 'gamma': 0.0}
        ),

        # === ABLATION 3: Uncertainty Collapse ===
        AblationConfig(
            name="QUTEN-NoCollapse",
            description="QUTEN without uncertainty collapse (collapse=1.0)",
            optimizer_class="QUTEN",
            optimizer_kwargs={**base_quten, 'collapse': 1.0}
        ),

        # === ABLATION 4: Adaptive Tunneling ===
        AblationConfig(
            name="QUTEN-FixedEta",
            description="QUTEN with fixed tunneling strength (adaptive_eta_scale=0)",
            optimizer_class="QUTEN",
            optimizer_kwargs={**base_quten, 'adaptive_eta_scale': 0.0}
        ),

        # === ABLATION 5: AMSGrad ===
        AblationConfig(
            name="QUTEN-NoAMSGrad",
            description="QUTEN without AMSGrad",
            optimizer_class="QUTEN",
            optimizer_kwargs={**base_quten, 'amsgrad': False}
        ),

        # === ABLATION 6: Warmup ===
        AblationConfig(
            name="QUTEN-NoWarmup",
            description="QUTEN without warmup (warmup_steps=0)",
            optimizer_class="QUTEN",
            optimizer_kwargs={**base_quten, 'warmup_steps': 0}
        ),

        # === ABLATION 7: Minimal QUTEN (only momentum + uncertainty) ===
        AblationConfig(
            name="QUTEN-Minimal",
            description="QUTEN reduced to Adam-like (no tunneling, no observation, no collapse)",
            optimizer_class="QUTEN",
            optimizer_kwargs={
                **base_quten,
                'eta': 0.0,
                'beta_observe': 1.0,
                'gamma': 0.0,
                'collapse': 1.0,
                'warmup_steps': 0
            }
        ),
    ]

    return configs


def create_optimizer(config: AblationConfig, model_params):
    """Create optimizer from configuration."""
    if config.optimizer_class == "QUTEN":
        return QUTEN(model_params, **config.optimizer_kwargs)
    elif config.optimizer_class == "Adam":
        return torch.optim.Adam(model_params, **config.optimizer_kwargs)
    elif config.optimizer_class == "AdamW":
        return torch.optim.AdamW(model_params, **config.optimizer_kwargs)
    elif config.optimizer_class == "SGD":
        return torch.optim.SGD(model_params, **config.optimizer_kwargs)
    else:
        raise ValueError(f"Unknown optimizer class: {config.optimizer_class}")


def run_experiment(
    config: AblationConfig,
    model_fn,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion,
    epochs: int,
    device: torch.device,
    baseline_tracker: Optional[MetricsTracker] = None,
    verbose: bool = True
) -> ExperimentMetrics:
    """Run a single ablation experiment."""

    if verbose:
        print(f"\n{'='*70}")
        print(f"Running: {config.name}")
        print(f"  {config.description}")
        print(f"{'='*70}")

    # Create model and optimizer
    model = model_fn().to(device)
    optimizer = create_optimizer(config, model.parameters())

    # Create metrics tracker
    is_quten = config.optimizer_class == "QUTEN"
    tracker = MetricsTracker(track_quten_internals=is_quten)
    tracker.start()

    # Training loop
    for epoch in range(epochs):
        model.train()
        epoch_train_loss = 0.0

        for batch_idx, (batch_x, batch_y) in enumerate(train_loader):
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)

            # Store old parameters for update tracking
            old_params = [p.detach().clone() for p in model.parameters()]

            # Forward pass
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)

            # Backward pass
            loss.backward()

            # Log gradients before step
            tracker.log_gradients(model)

            # Optimizer step
            optimizer.step()

            # Log update
            new_params = [p.detach().clone() for p in model.parameters()]
            tracker.log_update(old_params, new_params)

            # Store baseline updates if this is the baseline
            if baseline_tracker is not None and config.name == "Adam":
                baseline_tracker.store_baseline_update(old_params, new_params)

            # Log QUTEN internals
            if is_quten:
                tracker.log_quten_internals(optimizer)

            epoch_train_loss += loss.item()

        # Log training loss
        avg_train_loss = epoch_train_loss / len(train_loader)
        tracker.log_train_loss(avg_train_loss)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()

        avg_val_loss = val_loss / len(val_loader)
        tracker.log_val_loss(avg_val_loss)
        tracker.log_parameters(model)

        # Print progress
        if verbose and epoch % 20 == 0:
            print(f"  Epoch {epoch:3d}: Train Loss = {avg_train_loss:.6f}, Val Loss = {avg_val_loss:.6f}")

    tracker.end()

    if verbose:
        print(f"  Completed in {tracker.end_time - tracker.start_time:.2f}s")
        print(f"  Final Train Loss: {tracker.train_losses[-1]:.6f}")
        print(f"  Final Val Loss: {tracker.val_losses[-1]:.6f}")
        print(f"  Best Val Loss: {min(tracker.val_losses):.6f}")

    return tracker.create_metrics(config)


def generate_synthetic_data(n_samples=1000, n_features=20, noise=0.1, seed=42):
    """Generate synthetic nonlinear regression data."""
    torch.manual_seed(seed)
    X = torch.randn(n_samples, n_features)

    # Complex non-linear relationship
    y = (torch.sin(X[:, 0]) +
         torch.cos(X[:, 1] * X[:, 2]) +
         X[:, 3] ** 2 -
         torch.exp(-torch.abs(X[:, 4])) +
         torch.tanh(X[:, 5:10].sum(dim=1)))

    y = y + noise * torch.randn(n_samples)
    return X, y.unsqueeze(1)


class SimpleNet(nn.Module):
    """Simple feedforward network for testing."""
    def __init__(self, input_dim=20, hidden_dims=[64, 32], output_dim=1):
        super().__init__()
        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
            ])
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


class RosenbrockTask:
    """Rosenbrock optimization task."""
    def __init__(self, n_params=10, device='cpu'):
        self.n_params = n_params
        self.device = device

    def create_params(self):
        """Create initial parameters."""
        return [torch.tensor([-1.0], requires_grad=True, device=self.device)
                for _ in range(self.n_params)]

    def compute_loss(self, params):
        """Compute Rosenbrock loss."""
        loss = 0
        for i in range(len(params) - 1):
            loss += 100 * (params[i+1] - params[i]**2)**2 + (1 - params[i])**2
        return loss


def run_rosenbrock_experiment(
    config: AblationConfig,
    n_params: int,
    epochs: int,
    device: torch.device,
    verbose: bool = True
) -> ExperimentMetrics:
    """Run Rosenbrock optimization experiment."""

    if verbose:
        print(f"\n{'='*70}")
        print(f"Running Rosenbrock: {config.name}")
        print(f"{'='*70}")

    task = RosenbrockTask(n_params, device)
    params = task.create_params()
    optimizer = create_optimizer(config, params)

    tracker = MetricsTracker(track_quten_internals=False)
    tracker.start()

    for epoch in range(epochs):
        # Store old params
        old_params = [p.detach().clone() for p in params]

        # Forward
        optimizer.zero_grad()
        loss = task.compute_loss(params)

        # Backward
        loss.backward()
        tracker.log_gradients(type('Model', (), {'parameters': lambda: params})())

        # Step
        optimizer.step()

        # Log
        new_params = [p.detach().clone() for p in params]
        tracker.log_update(old_params, new_params)
        tracker.log_train_loss(loss.item())
        tracker.log_val_loss(loss.item())  # No val set for Rosenbrock

        if verbose and epoch % 40 == 0:
            print(f"  Epoch {epoch:3d}: Loss = {loss.item():.6f}")

    tracker.end()

    if verbose:
        print(f"  Final Loss: {tracker.train_losses[-1]:.6f}")

    return tracker.create_metrics(config, loss_threshold=10.0)


def run_ablation_study(
    configs: List[AblationConfig],
    benchmark: str = "synthetic",
    epochs: int = 100,
    batch_size: int = 32,
    device: torch.device = torch.device('cpu'),
    save_dir: str = "ablation_results"
) -> List[ExperimentMetrics]:
    """Run full ablation study across all configurations."""

    results = []
    save_path = Path(save_dir)
    save_path.mkdir(exist_ok=True)

    if benchmark == "synthetic":
        print(f"\n{'='*70}")
        print("BENCHMARK: Synthetic Nonlinear Regression")
        print(f"{'='*70}")

        # Generate data
        X_train, y_train = generate_synthetic_data(n_samples=800, n_features=20)
        X_val, y_val = generate_synthetic_data(n_samples=200, n_features=20, seed=43)

        train_dataset = TensorDataset(X_train, y_train)
        val_dataset = TensorDataset(X_val, y_val)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        criterion = nn.MSELoss()
        model_fn = lambda: SimpleNet(input_dim=20, hidden_dims=[64, 32], output_dim=1)

        # Run experiments
        for config in configs:
            try:
                metrics = run_experiment(
                    config=config,
                    model_fn=model_fn,
                    train_loader=train_loader,
                    val_loader=val_loader,
                    criterion=criterion,
                    epochs=epochs,
                    device=device,
                    verbose=True
                )
                results.append(metrics)

                # Save individual result
                result_file = save_path / f"{config.name}.json"
                with open(result_file, 'w') as f:
                    json.dump(metrics.to_dict(), f, indent=2)

            except Exception as e:
                print(f"  ERROR running {config.name}: {e}")
                import traceback
                traceback.print_exc()

    elif benchmark == "rosenbrock":
        print(f"\n{'='*70}")
        print("BENCHMARK: Rosenbrock Optimization")
        print(f"{'='*70}")

        for config in configs:
            try:
                metrics = run_rosenbrock_experiment(
                    config=config,
                    n_params=10,
                    epochs=epochs,
                    device=device,
                    verbose=True
                )
                results.append(metrics)

                # Save individual result
                result_file = save_path / f"{config.name}_rosenbrock.json"
                with open(result_file, 'w') as f:
                    json.dump(metrics.to_dict(), f, indent=2)

            except Exception as e:
                print(f"  ERROR running {config.name}: {e}")
                import traceback
                traceback.print_exc()

    return results


def print_summary_table(results: List[ExperimentMetrics]):
    """Print a summary comparison table."""
    print("\n" + "="*70)
    print("ABLATION STUDY SUMMARY")
    print("="*70)

    # Header
    print(f"\n{'Config':<25} {'Final Loss':>12} {'Best Loss':>12} {'Time (s)':>10} {'NaNs':>6}")
    print("-"*70)

    # Sort by final val loss
    sorted_results = sorted(results, key=lambda x: x.final_val_loss)

    for metrics in sorted_results:
        print(f"{metrics.config.name:<25} "
              f"{metrics.final_val_loss:>12.6f} "
              f"{metrics.best_val_loss:>12.6f} "
              f"{metrics.wall_clock_time:>10.2f} "
              f"{metrics.nan_count:>6d}")

    print("="*70)

    # Find best performer
    best = sorted_results[0]
    print(f"\nBest performer: {best.config.name}")
    print(f"  Final Loss: {best.final_val_loss:.6f}")
    print(f"  Time: {best.wall_clock_time:.2f}s")

    # Compare QUTEN variants to Adam baseline
    adam_result = next((r for r in results if r.config.name == "Adam"), None)
    if adam_result:
        print(f"\n{'Comparison to Adam Baseline:':<25}")
        print(f"{'Config':<25} {'Loss Improvement':>18} {'Time Ratio':>12}")
        print("-"*70)

        for metrics in sorted_results:
            if metrics.config.name != "Adam":
                loss_improvement = ((adam_result.final_val_loss - metrics.final_val_loss) /
                                   adam_result.final_val_loss * 100)
                time_ratio = metrics.wall_clock_time / adam_result.wall_clock_time

                print(f"{metrics.config.name:<25} "
                      f"{loss_improvement:>+17.2f}% "
                      f"{time_ratio:>12.2f}x")

    print("="*70)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("QUTEN COMPREHENSIVE ABLATION STUDY")
    print("="*70)
    print("\nThis will systematically test each component of QUTEN")
    print("to validate its contribution to optimization performance.\n")

    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}\n")

    # Create ablation configurations
    configs = create_ablation_configs()
    print(f"Testing {len(configs)} configurations:")
    for i, config in enumerate(configs, 1):
        print(f"  {i}. {config.name}: {config.description}")

    # Run ablation studies
    print("\n" + "="*70)
    print("RUNNING EXPERIMENTS")
    print("="*70)

    # Test 1: Synthetic regression
    results_synthetic = run_ablation_study(
        configs=configs,
        benchmark="synthetic",
        epochs=100,
        batch_size=32,
        device=device,
        save_dir="ablation_results/synthetic"
    )

    print_summary_table(results_synthetic)

    # Test 2: Rosenbrock
    results_rosenbrock = run_ablation_study(
        configs=configs,
        benchmark="rosenbrock",
        epochs=200,
        device=device,
        save_dir="ablation_results/rosenbrock"
    )

    print_summary_table(results_rosenbrock)

    print("\n" + "="*70)
    print("ABLATION STUDY COMPLETE")
    print("="*70)
    print("\nResults saved to: ablation_results/")
    print("\nKey findings to look for:")
    print("  • Which components contribute most to performance?")
    print("  • Are there components that hurt performance?")
    print("  • How does QUTEN compare to standard baselines?")
    print("  • Where does tunneling help most?")
    print("="*70 + "\n")
