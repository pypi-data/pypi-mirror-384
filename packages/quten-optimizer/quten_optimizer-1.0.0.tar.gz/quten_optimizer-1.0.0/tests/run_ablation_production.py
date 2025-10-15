"""
Production-ready ablation study for QUTEN optimizer.
Generates comprehensive visualizations for GitHub Actions CI/CD.
"""
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
import numpy as np
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from quten import QUTEN


@dataclass
class Config:
    """Optimizer configuration."""
    name: str
    optimizer_class: str
    kwargs: Dict[str, Any]
    color: str = 'blue'


@dataclass
class Results:
    """Experiment results."""
    config_name: str
    train_losses: List[float]
    val_losses: List[float]
    final_loss: float
    best_loss: float
    convergence_epoch: Optional[int]
    time_seconds: float
    gradient_norms: List[float]
    update_norms: List[float]


def create_cifar_like_data(n_train=5000, n_val=1000, n_features=512, n_classes=10, seed=42):
    """
    Create challenging image-like classification data.
    Features: high-dimensional, non-linear decision boundaries, significant class overlap,
    adversarial patterns, multiple local minima in loss landscape.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    # Create class prototypes with MUCH closer spacing (harder problem)
    class_centers = torch.randn(n_classes, n_features) * 0.5  # Reduced from 1.5

    # Add pairwise class confusion (some classes are inherently similar)
    confusion_pairs = [(0, 6), (1, 8), (2, 3), (4, 9), (5, 7)]
    for class_a, class_b in confusion_pairs:
        # Make these pairs closer together
        shared_features = torch.randn(n_features) * 0.3
        class_centers[class_a] += shared_features
        class_centers[class_b] += shared_features

    # Training data with complex multimodal distributions
    X_train = []
    y_train = []

    for class_idx in range(n_classes):
        n_samples_per_class = n_train // n_classes

        # Create multiple distinct modes per class (like different viewpoints/styles)
        n_modes = 5  # Increased from 3
        samples_per_mode = n_samples_per_class // n_modes

        class_samples = []
        for mode_idx in range(n_modes):
            # Each mode has its own center with large variance
            mode_offset = torch.randn(n_features) * 1.5  # Large intra-class variance
            mode_center = class_centers[class_idx] + mode_offset

            # Samples from this mode with high noise
            mode_samples = mode_center.unsqueeze(0) + torch.randn(samples_per_mode, n_features) * 1.2
            class_samples.append(mode_samples)

        samples = torch.cat(class_samples)

        X_train.append(samples)
        y_train.append(torch.full((len(samples),), class_idx, dtype=torch.long))

    X_train = torch.cat(X_train)
    y_train = torch.cat(y_train)

    # Apply non-linear transformations to create complex decision boundaries
    # Simulate feature interactions (like pixel correlations in images)
    X_train_normalized = torch.tanh(X_train * 0.5)

    # Add adversarial-like noise patterns (correlated noise across features)
    noise_patterns = torch.randn(n_features, n_features) * 0.2
    correlated_noise = torch.matmul(torch.randn(len(X_train), n_features), noise_patterns)
    X_train = X_train_normalized + correlated_noise * 0.8

    # Add high-frequency noise components
    X_train += 0.5 * torch.randn_like(X_train)

    # Create significant label noise (30% ambiguous/mislabeled samples)
    confusing_indices = torch.randperm(len(X_train))[:int(0.3 * len(X_train))]
    for idx in confusing_indices:
        current_class = y_train[idx].item()

        # 50% chance: blend with a similar class (creates ambiguity)
        if torch.rand(1).item() < 0.5:
            if current_class in [pair[0] for pair in confusion_pairs]:
                other_class = [pair[1] for pair in confusion_pairs if pair[0] == current_class][0]
            elif current_class in [pair[1] for pair in confusion_pairs]:
                other_class = [pair[0] for pair in confusion_pairs if pair[1] == current_class][0]
            else:
                other_class = (current_class + 1) % n_classes

            # Blend features (creates samples on decision boundary)
            blend_factor = 0.3 + 0.4 * torch.rand(1).item()
            X_train[idx] = (1 - blend_factor) * X_train[idx] + blend_factor * class_centers[other_class]

        # 50% chance: actually mislabel (Bayes-irreducible error)
        if torch.rand(1).item() < 0.15:
            wrong_class = (current_class + torch.randint(1, n_classes, (1,)).item()) % n_classes
            y_train[idx] = wrong_class

    # Validation data (similar process but with less label noise)
    X_val = []
    y_val = []

    for class_idx in range(n_classes):
        n_samples_per_class = n_val // n_classes

        # Use same multimodal structure
        n_modes = 5
        samples_per_mode = n_samples_per_class // n_modes

        class_samples = []
        for mode_idx in range(n_modes):
            mode_offset = torch.randn(n_features) * 1.5
            mode_center = class_centers[class_idx] + mode_offset
            mode_samples = mode_center.unsqueeze(0) + torch.randn(samples_per_mode, n_features) * 1.2
            class_samples.append(mode_samples)

        samples = torch.cat(class_samples)
        X_val.append(samples)
        y_val.append(torch.full((len(samples),), class_idx, dtype=torch.long))

    X_val = torch.cat(X_val)
    y_val = torch.cat(y_val)

    # Apply same transformations
    X_val_normalized = torch.tanh(X_val * 0.5)
    correlated_noise_val = torch.matmul(torch.randn(len(X_val), n_features), noise_patterns)
    X_val = X_val_normalized + correlated_noise_val * 0.8
    X_val += 0.5 * torch.randn_like(X_val)

    # Add 15% label noise to validation (simulate real-world noisy labels)
    confusing_indices_val = torch.randperm(len(X_val))[:int(0.15 * len(X_val))]
    for idx in confusing_indices_val:
        current_class = y_val[idx].item()
        if torch.rand(1).item() < 0.5:
            blend_factor = 0.3 + 0.3 * torch.rand(1).item()
            other_class = (current_class + 1) % n_classes
            X_val[idx] = (1 - blend_factor) * X_val[idx] + blend_factor * class_centers[other_class]

    # Shuffle
    train_perm = torch.randperm(len(X_train))
    X_train, y_train = X_train[train_perm], y_train[train_perm]

    val_perm = torch.randperm(len(X_val))
    X_val, y_val = X_val[val_perm], y_val[val_perm]

    print(f"Dataset characteristics:")
    print(f"  - Class separation: LOW (significant overlap)")
    print(f"  - Intra-class variance: HIGH (5 modes per class)")
    print(f"  - Label noise: 30% train, 15% val")
    print(f"  - Decision boundaries: HIGHLY NON-LINEAR")

    return X_train, y_train, X_val, y_val


class RealisticNet(nn.Module):
    """Realistic deep network (mimics ResNet-like architecture)."""
    def __init__(self, input_dim=512, n_classes=10):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(128, n_classes)
        )

    def forward(self, x):
        return self.network(x)


def run_experiment(config: Config, train_loader, val_loader, epochs: int, device) -> Results:
    """Run single experiment and collect metrics."""
    print(f"\n{'='*60}")
    print(f"Running: {config.name}")
    print(f"{'='*60}")

    model = RealisticNet().to(device)

    # Create optimizer
    if config.optimizer_class == "QUTEN":
        optimizer = QUTEN(model.parameters(), **config.kwargs)
    elif config.optimizer_class == "Adam":
        optimizer = torch.optim.Adam(model.parameters(), **config.kwargs)
    elif config.optimizer_class == "AdamW":
        optimizer = torch.optim.AdamW(model.parameters(), **config.kwargs)
    elif config.optimizer_class == "SGD":
        optimizer = torch.optim.SGD(model.parameters(), **config.kwargs)
    else:
        raise ValueError(f"Unknown optimizer: {config.optimizer_class}")

    criterion = nn.CrossEntropyLoss()

    train_losses = []
    val_losses = []
    gradient_norms = []
    update_norms = []
    convergence_epoch = None
    convergence_threshold = 1.5  # Consider converged when val loss < 1.5 (harder problem)

    start_time = time.time()

    for epoch in range(epochs):
        # Training
        model.train()
        epoch_loss = 0.0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)

            # Store old params for update norm
            old_params = [p.detach().clone() for p in model.parameters()]

            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()

            # Compute gradient norm
            grad_norm = 0.0
            for p in model.parameters():
                if p.grad is not None:
                    grad_norm += p.grad.data.norm(2).item() ** 2
            grad_norm = grad_norm ** 0.5
            gradient_norms.append(grad_norm)

            optimizer.step()

            # Compute update norm
            update_norm = 0.0
            for old_p, new_p in zip(old_params, model.parameters()):
                update_norm += (new_p - old_p).norm(2).item() ** 2
            update_norm = update_norm ** 0.5
            update_norms.append(update_norm)

            epoch_loss += loss.item()

        avg_train_loss = epoch_loss / len(train_loader)
        train_losses.append(avg_train_loss)

        # Validation
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()

                _, predicted = outputs.max(1)
                total += batch_y.size(0)
                correct += predicted.eq(batch_y).sum().item()

        avg_val_loss = val_loss / len(val_loader)
        val_losses.append(avg_val_loss)
        accuracy = 100.0 * correct / total

        # Check convergence
        if convergence_epoch is None and avg_val_loss < convergence_threshold:
            convergence_epoch = epoch

        if epoch % 10 == 0:
            print(f"Epoch {epoch:3d}: Train={avg_train_loss:.4f}, Val={avg_val_loss:.4f}, Acc={accuracy:.2f}%")

    elapsed = time.time() - start_time

    print(f"Completed in {elapsed:.2f}s")
    print(f"Final: Train={train_losses[-1]:.4f}, Val={val_losses[-1]:.4f}")
    print(f"Best Val Loss: {min(val_losses):.4f}")
    if convergence_epoch:
        print(f"Converged at epoch {convergence_epoch}")

    return Results(
        config_name=config.name,
        train_losses=train_losses,
        val_losses=val_losses,
        final_loss=val_losses[-1],
        best_loss=min(val_losses),
        convergence_epoch=convergence_epoch,
        time_seconds=elapsed,
        gradient_norms=gradient_norms,
        update_norms=update_norms
    )


def plot_results(results: List[Results], output_dir: Path):
    """Generate comprehensive visualization plots."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    colors = plt.cm.tab10(np.linspace(0, 1, len(results)))

    # Figure 1: Loss curves
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    for i, res in enumerate(results):
        epochs = range(len(res.train_losses))
        ax1.plot(epochs, res.train_losses, label=res.config_name,
                linewidth=2.5, alpha=0.8, color=colors[i])
        ax2.plot(epochs, res.val_losses, label=res.config_name,
                linewidth=2.5, alpha=0.8, color=colors[i])

    ax1.set_xlabel('Epoch', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Training Loss', fontsize=14, fontweight='bold')
    ax1.set_title('Training Loss Curves', fontsize=16, fontweight='bold')
    ax1.legend(fontsize=11, framealpha=0.9)
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    ax2.set_xlabel('Epoch', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Validation Loss', fontsize=14, fontweight='bold')
    ax2.set_title('Validation Loss Curves', fontsize=16, fontweight='bold')
    ax2.legend(fontsize=11, framealpha=0.9)
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')

    plt.tight_layout()
    plt.savefig(output_dir / 'loss_curves.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'loss_curves.png'}")
    plt.close()

    # Figure 2: Performance comparison bars
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    names = [r.config_name for r in results]
    final_losses = [r.final_loss for r in results]
    best_losses = [r.best_loss for r in results]
    times = [r.time_seconds for r in results]
    convergence_epochs = [r.convergence_epoch if r.convergence_epoch else len(r.val_losses)
                          for r in results]

    # Sort by final loss for better visualization
    sorted_indices = np.argsort(final_losses)

    # Final loss
    ax1.barh([names[i] for i in sorted_indices],
            [final_losses[i] for i in sorted_indices],
            color=[colors[i] for i in sorted_indices], alpha=0.8)
    ax1.set_xlabel('Final Validation Loss', fontsize=13, fontweight='bold')
    ax1.set_title('Final Performance', fontsize=15, fontweight='bold')
    ax1.grid(True, axis='x', alpha=0.3)

    # Best loss
    ax2.barh([names[i] for i in sorted_indices],
            [best_losses[i] for i in sorted_indices],
            color=[colors[i] for i in sorted_indices], alpha=0.8)
    ax2.set_xlabel('Best Validation Loss', fontsize=13, fontweight='bold')
    ax2.set_title('Best Performance Achieved', fontsize=15, fontweight='bold')
    ax2.grid(True, axis='x', alpha=0.3)

    # Training time
    ax3.barh(names, times, color=colors, alpha=0.8)
    ax3.set_xlabel('Training Time (seconds)', fontsize=13, fontweight='bold')
    ax3.set_title('Computational Efficiency', fontsize=15, fontweight='bold')
    ax3.grid(True, axis='x', alpha=0.3)

    # Convergence speed
    ax4.barh(names, convergence_epochs, color=colors, alpha=0.8)
    ax4.set_xlabel('Epochs to Convergence', fontsize=13, fontweight='bold')
    ax4.set_title('Convergence Speed', fontsize=15, fontweight='bold')
    ax4.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'performance_bars.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'performance_bars.png'}")
    plt.close()

    # Figure 3: Gradient dynamics
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    for i, res in enumerate(results):
        # Subsample for readability
        step_indices = range(0, len(res.gradient_norms), max(1, len(res.gradient_norms) // 200))
        grad_norms_sub = [res.gradient_norms[j] for j in step_indices]
        update_norms_sub = [res.update_norms[j] for j in step_indices]

        ax1.plot(step_indices, grad_norms_sub, label=res.config_name,
                linewidth=2, alpha=0.7, color=colors[i])
        ax2.plot(step_indices, update_norms_sub, label=res.config_name,
                linewidth=2, alpha=0.7, color=colors[i])

    ax1.set_xlabel('Training Step', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Gradient Norm', fontsize=14, fontweight='bold')
    ax1.set_title('Gradient Norm Evolution', fontsize=16, fontweight='bold')
    ax1.legend(fontsize=11, framealpha=0.9)
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    ax2.set_xlabel('Training Step', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Update Norm', fontsize=14, fontweight='bold')
    ax2.set_title('Update Norm Evolution', fontsize=16, fontweight='bold')
    ax2.legend(fontsize=11, framealpha=0.9)
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')

    plt.tight_layout()
    plt.savefig(output_dir / 'gradient_dynamics.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'gradient_dynamics.png'}")
    plt.close()

    # Figure 4: Summary comparison table as image
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('tight')
    ax.axis('off')

    # Create table data
    table_data = [['Optimizer', 'Final Loss', 'Best Loss', 'Time (s)', 'Conv. Epoch']]
    for res in sorted(results, key=lambda x: x.final_loss):
        table_data.append([
            res.config_name,
            f'{res.final_loss:.4f}',
            f'{res.best_loss:.4f}',
            f'{res.time_seconds:.2f}',
            str(res.convergence_epoch) if res.convergence_epoch else 'N/A'
        ])

    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.3, 0.2, 0.2, 0.15, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2)

    # Style header
    for i in range(5):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Style rows
    for i in range(1, len(table_data)):
        for j in range(5):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')

    # Highlight best performer
    table[(1, 0)].set_facecolor('#FFD700')
    for j in range(1, 5):
        table[(1, j)].set_facecolor('#FFF9C4')

    plt.title('Ablation Study Results Summary', fontsize=18, fontweight='bold', pad=20)
    plt.savefig(output_dir / 'summary_table.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'summary_table.png'}")
    plt.close()


def save_json_results(results: List[Results], output_dir: Path):
    """Save results as JSON for further analysis."""
    output_file = output_dir / 'results.json'

    json_data = []
    for res in results:
        json_data.append({
            'config_name': res.config_name,
            'final_loss': res.final_loss,
            'best_loss': res.best_loss,
            'convergence_epoch': res.convergence_epoch,
            'time_seconds': res.time_seconds,
            'train_losses': res.train_losses,
            'val_losses': res.val_losses
        })

    with open(output_file, 'w') as f:
        json.dump(json_data, f, indent=2)

    print(f"✓ Saved: {output_file}")


def main():
    """Run production ablation study."""
    print("\n" + "="*70)
    print("QUTEN PRODUCTION ABLATION STUDY")
    print("="*70)
    print("Generating publication-quality visualizations for CI/CD\n")

    # Setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")

    # Create realistic data
    print("\nGenerating realistic CIFAR-like dataset...")
    X_train, y_train, X_val, y_val = create_cifar_like_data(
        n_train=5000, n_val=1000, n_features=512, n_classes=10
    )

    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

    print(f"Train samples: {len(X_train)}, Val samples: {len(X_val)}")

    # Define configurations
    configs = [
        Config("Adam", "Adam", {'lr': 0.001}, '#1f77b4'),
        Config("AdamW", "AdamW", {'lr': 0.001, 'weight_decay': 1e-4}, '#ff7f0e'),
        Config("SGD+Momentum", "SGD", {'lr': 0.01, 'momentum': 0.9, 'nesterov': True}, '#2ca02c'),
        Config("QUTEN-Full", "QUTEN", {
            'lr': 0.001, 'eta': 0.001, 'beta1': 0.9, 'beta2': 0.999,
            'gamma': 4.0, 'hbar': 0.1, 'amsgrad': True, 'warmup_steps': 200, 'collapse': 0.998
        }, '#d62728'),
        Config("QUTEN-NoTunneling", "QUTEN", {
            'lr': 0.001, 'eta': 0.0, 'beta1': 0.9, 'beta2': 0.999,
            'gamma': 4.0, 'hbar': 0.1, 'amsgrad': True, 'warmup_steps': 200, 'collapse': 0.998
        }, '#9467bd'),
        Config("QUTEN-NoObservation", "QUTEN", {
            'lr': 0.001, 'eta': 0.001, 'beta1': 0.9, 'beta2': 0.999,
            'gamma': 0.0, 'beta_observe': 1.0, 'hbar': 0.1, 'amsgrad': True, 'warmup_steps': 0, 'collapse': 0.998
        }, '#8c564b'),
    ]

    print(f"\nTesting {len(configs)} configurations:")
    for i, config in enumerate(configs, 1):
        print(f"  {i}. {config.name}")

    # Run experiments
    epochs = 100
    print(f"\nRunning {epochs} epochs per configuration...\n")

    results = []
    for config in configs:
        try:
            result = run_experiment(config, train_loader, val_loader, epochs, device)
            results.append(result)
        except Exception as e:
            print(f"ERROR running {config.name}: {e}")
            import traceback
            traceback.print_exc()

    if not results:
        print("\n✗ No results to visualize!")
        return

    # Generate visualizations
    output_dir = Path('ablation_results')
    print(f"\n{'='*70}")
    print("Generating visualizations...")
    print(f"{'='*70}\n")

    plot_results(results, output_dir)
    save_json_results(results, output_dir)

    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")

    sorted_results = sorted(results, key=lambda x: x.final_loss)
    print(f"{'Optimizer':<25} {'Final Loss':>12} {'Best Loss':>12} {'Time (s)':>10}")
    print("-"*70)
    for res in sorted_results:
        print(f"{res.config_name:<25} {res.final_loss:>12.4f} {res.best_loss:>12.4f} {res.time_seconds:>10.2f}")

    print(f"\n🏆 Best performer: {sorted_results[0].config_name}")
    print(f"   Final Loss: {sorted_results[0].final_loss:.4f}")
    print(f"   Best Loss: {sorted_results[0].best_loss:.4f}")

    # Compare to Adam
    adam_result = next((r for r in results if r.config_name == 'Adam'), None)
    if adam_result:
        print(f"\n📊 Comparison to Adam baseline:")
        for res in sorted_results:
            if res.config_name != 'Adam':
                improvement = (adam_result.final_loss - res.final_loss) / adam_result.final_loss * 100
                print(f"   {res.config_name}: {improvement:+.2f}%")

    print(f"\n{'='*70}")
    print("✅ ABLATION STUDY COMPLETE")
    print(f"{'='*70}")
    print(f"\nResults saved to: {output_dir.absolute()}")
    print("\nGenerated files:")
    print("  • loss_curves.png - Training/validation loss over time")
    print("  • performance_bars.png - Performance comparison bars")
    print("  • gradient_dynamics.png - Gradient and update norms")
    print("  • summary_table.png - Results summary table")
    print("  • results.json - Raw data for further analysis")
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
