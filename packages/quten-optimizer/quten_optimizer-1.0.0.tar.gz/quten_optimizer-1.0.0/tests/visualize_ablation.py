"""
Visualization utilities for ablation study results.
Creates plots and analysis reports from ablation experiments.
"""
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


def load_results(results_dir: str) -> List[Dict[str, Any]]:
    """Load all JSON results from directory."""
    results = []
    results_path = Path(results_dir)

    if not results_path.exists():
        print(f"Results directory not found: {results_dir}")
        return []

    for json_file in results_path.glob("*.json"):
        with open(json_file, 'r') as f:
            results.append(json.load(f))

    return results


def plot_training_curves(results: List[Dict], save_path: str = "training_curves.png"):
    """Plot training and validation loss curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    # Plot training losses
    for result in results:
        config_name = result['config']['name']
        train_losses = result['train_losses']
        epochs = range(len(train_losses))
        ax1.plot(epochs, train_losses, label=config_name, linewidth=2, alpha=0.8)

    ax1.set_xlabel('Epoch', fontsize=12)
    ax1.set_ylabel('Training Loss', fontsize=12)
    ax1.set_title('Training Loss Curves', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=9, loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    # Plot validation losses
    for result in results:
        config_name = result['config']['name']
        val_losses = result['val_losses']
        if val_losses:
            epochs = range(len(val_losses))
            ax2.plot(epochs, val_losses, label=config_name, linewidth=2, alpha=0.8)

    ax2.set_xlabel('Epoch', fontsize=12)
    ax2.set_ylabel('Validation Loss', fontsize=12)
    ax2.set_title('Validation Loss Curves', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=9, loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved training curves to {save_path}")
    plt.close()


def plot_gradient_dynamics(results: List[Dict], save_path: str = "gradient_dynamics.png"):
    """Plot gradient and update norms."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    # Plot gradient norms
    for result in results:
        config_name = result['config']['name']
        grad_norms = result['gradient_norms']
        if grad_norms:
            steps = range(len(grad_norms))
            ax1.plot(steps, grad_norms, label=config_name, linewidth=2, alpha=0.7)

    ax1.set_xlabel('Step', fontsize=12)
    ax1.set_ylabel('Gradient Norm', fontsize=12)
    ax1.set_title('Gradient Norms Over Time', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=9, loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    # Plot update norms
    for result in results:
        config_name = result['config']['name']
        update_norms = result['update_norms']
        if update_norms:
            steps = range(len(update_norms))
            ax2.plot(steps, update_norms, label=config_name, linewidth=2, alpha=0.7)

    ax2.set_xlabel('Step', fontsize=12)
    ax2.set_ylabel('Update Norm', fontsize=12)
    ax2.set_title('Update Norms Over Time', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=9, loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved gradient dynamics to {save_path}")
    plt.close()


def plot_quten_internals(results: List[Dict], save_path: str = "quten_internals.png"):
    """Plot QUTEN-specific internal states."""
    quten_results = [r for r in results if 'QUTEN' in r['config']['name']]

    if not quten_results:
        print("No QUTEN results to plot")
        return

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Plot sigma (uncertainty) mean
    ax = axes[0, 0]
    for result in quten_results:
        config_name = result['config']['name']
        sigma_mean = result.get('sigma_mean', [])
        if sigma_mean:
            steps = range(len(sigma_mean))
            ax.plot(steps, sigma_mean, label=config_name, linewidth=2, alpha=0.8)

    ax.set_xlabel('Step', fontsize=12)
    ax.set_ylabel('Mean σ (Uncertainty)', fontsize=12)
    ax.set_title('Uncertainty Evolution', fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, loc='best')
    ax.grid(True, alpha=0.3)

    # Plot sigma std
    ax = axes[0, 1]
    for result in quten_results:
        config_name = result['config']['name']
        sigma_std = result.get('sigma_std', [])
        if sigma_std:
            steps = range(len(sigma_std))
            ax.plot(steps, sigma_std, label=config_name, linewidth=2, alpha=0.8)

    ax.set_xlabel('Step', fontsize=12)
    ax.set_ylabel('Std σ (Uncertainty)', fontsize=12)
    ax.set_title('Uncertainty Spread', fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, loc='best')
    ax.grid(True, alpha=0.3)

    # Plot observation mean
    ax = axes[1, 0]
    for result in quten_results:
        config_name = result['config']['name']
        observe_mean = result.get('observe_mean', [])
        if observe_mean:
            steps = range(len(observe_mean))
            ax.plot(steps, observe_mean, label=config_name, linewidth=2, alpha=0.8)

    ax.set_xlabel('Step', fontsize=12)
    ax.set_ylabel('Mean Observation Fidelity', fontsize=12)
    ax.set_title('Observation Evolution', fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, loc='best')
    ax.grid(True, alpha=0.3)

    # Leave last subplot for future use
    axes[1, 1].axis('off')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved QUTEN internals to {save_path}")
    plt.close()


def plot_performance_comparison(results: List[Dict], save_path: str = "performance_comparison.png"):
    """Plot performance comparison bar charts."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Sort results by final val loss
    sorted_results = sorted(results, key=lambda x: x['final_val_loss'])

    config_names = [r['config']['name'] for r in sorted_results]
    final_losses = [r['final_val_loss'] for r in sorted_results]
    best_losses = [r['best_val_loss'] for r in sorted_results]
    wall_times = [r['wall_clock_time'] for r in sorted_results]
    gen_gaps = [r['generalization_gap'] for r in sorted_results]

    # Plot 1: Final validation loss
    ax = axes[0, 0]
    bars = ax.barh(config_names, final_losses, color='steelblue', alpha=0.8)
    ax.set_xlabel('Final Validation Loss', fontsize=12)
    ax.set_title('Final Performance', fontsize=14, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)

    # Highlight best performer
    bars[0].set_color('darkgreen')

    # Plot 2: Best validation loss
    ax = axes[0, 1]
    bars = ax.barh(config_names, best_losses, color='coral', alpha=0.8)
    ax.set_xlabel('Best Validation Loss', fontsize=12)
    ax.set_title('Best Performance Achieved', fontsize=14, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)
    bars[0].set_color('darkgreen')

    # Plot 3: Wall clock time
    ax = axes[1, 0]
    bars = ax.barh(config_names, wall_times, color='mediumpurple', alpha=0.8)
    ax.set_xlabel('Wall Clock Time (s)', fontsize=12)
    ax.set_title('Training Time', fontsize=14, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)

    # Plot 4: Generalization gap
    ax = axes[1, 1]
    bars = ax.barh(config_names, gen_gaps, color='indianred', alpha=0.8)
    ax.set_xlabel('Generalization Gap', fontsize=12)
    ax.set_title('Train-Val Gap', fontsize=14, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved performance comparison to {save_path}")
    plt.close()


def generate_report(results: List[Dict], save_path: str = "ablation_report.txt"):
    """Generate a detailed text report."""
    with open(save_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("QUTEN ABLATION STUDY - DETAILED REPORT\n")
        f.write("="*80 + "\n\n")

        # Sort by performance
        sorted_results = sorted(results, key=lambda x: x['final_val_loss'])

        # Overall summary
        f.write("OVERALL SUMMARY\n")
        f.write("-"*80 + "\n")
        f.write(f"{'Config':<25} {'Final Loss':>12} {'Best Loss':>12} {'Time (s)':>10} {'NaNs':>6}\n")
        f.write("-"*80 + "\n")

        for result in sorted_results:
            f.write(f"{result['config']['name']:<25} "
                   f"{result['final_val_loss']:>12.6f} "
                   f"{result['best_val_loss']:>12.6f} "
                   f"{result['wall_clock_time']:>10.2f} "
                   f"{result['nan_count']:>6d}\n")

        f.write("\n")

        # Best performer
        best = sorted_results[0]
        f.write("BEST PERFORMER\n")
        f.write("-"*80 + "\n")
        f.write(f"Config: {best['config']['name']}\n")
        f.write(f"Description: {best['config']['description']}\n")
        f.write(f"Final Val Loss: {best['final_val_loss']:.6f}\n")
        f.write(f"Best Val Loss: {best['best_val_loss']:.6f}\n")
        f.write(f"Time: {best['wall_clock_time']:.2f}s\n")
        f.write(f"Generalization Gap: {best['generalization_gap']:.6f}\n")
        f.write("\n")

        # Comparison to baselines
        adam_result = next((r for r in results if r['config']['name'] == 'Adam'), None)
        if adam_result:
            f.write("COMPARISON TO ADAM BASELINE\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Config':<25} {'Loss Δ':>15} {'Time Ratio':>12} {'Verdict':>15}\n")
            f.write("-"*80 + "\n")

            for result in sorted_results:
                if result['config']['name'] != 'Adam':
                    loss_delta = ((adam_result['final_val_loss'] - result['final_val_loss']) /
                                 adam_result['final_val_loss'] * 100)
                    time_ratio = result['wall_clock_time'] / adam_result['wall_clock_time']

                    # Verdict
                    if loss_delta > 5 and time_ratio < 1.5:
                        verdict = "Better"
                    elif loss_delta > 0 and time_ratio < 2.0:
                        verdict = "Competitive"
                    elif loss_delta < -5:
                        verdict = "Worse"
                    else:
                        verdict = "Similar"

                    f.write(f"{result['config']['name']:<25} "
                           f"{loss_delta:>+14.2f}% "
                           f"{time_ratio:>12.2f}x "
                           f"{verdict:>15}\n")

            f.write("\n")

        # Component analysis
        f.write("COMPONENT CONTRIBUTION ANALYSIS\n")
        f.write("-"*80 + "\n")

        # Find full QUTEN result
        full_quten = next((r for r in results if r['config']['name'] == 'QUTEN-Full'), None)
        if full_quten:
            f.write(f"Baseline: QUTEN-Full (Loss: {full_quten['final_val_loss']:.6f})\n\n")

            # Analyze each ablation
            ablations = [
                ('QUTEN-NoTunneling', 'Tunneling (eta)'),
                ('QUTEN-NoObservation', 'Observation damping'),
                ('QUTEN-NoCollapse', 'Uncertainty collapse'),
                ('QUTEN-FixedEta', 'Adaptive tunneling'),
                ('QUTEN-NoAMSGrad', 'AMSGrad'),
                ('QUTEN-NoWarmup', 'Warmup'),
            ]

            for ablation_name, component_name in ablations:
                ablation_result = next((r for r in results if r['config']['name'] == ablation_name), None)
                if ablation_result:
                    loss_change = ablation_result['final_val_loss'] - full_quten['final_val_loss']
                    pct_change = (loss_change / full_quten['final_val_loss']) * 100

                    impact = "Hurts" if loss_change > 0 else "Helps"
                    f.write(f"{component_name:<30}: {impact} ({pct_change:+.2f}%)\n")

        f.write("\n")

        # Stability analysis
        f.write("STABILITY ANALYSIS\n")
        f.write("-"*80 + "\n")
        for result in sorted_results:
            if result['nan_count'] > 0:
                f.write(f"WARNING: {result['config']['name']} had {result['nan_count']} NaN occurrences\n")

        f.write("\n")

        # Key findings
        f.write("KEY FINDINGS\n")
        f.write("-"*80 + "\n")
        f.write("1. Best overall optimizer: {}\n".format(sorted_results[0]['config']['name']))

        if adam_result:
            quten_better = [r for r in sorted_results
                           if 'QUTEN' in r['config']['name']
                           and r['final_val_loss'] < adam_result['final_val_loss']]
            if quten_better:
                f.write(f"2. {len(quten_better)} QUTEN variants beat Adam baseline\n")
            else:
                f.write("2. No QUTEN variants beat Adam baseline on this task\n")

        f.write("\n")
        f.write("="*80 + "\n")

    print(f"Saved detailed report to {save_path}")


def visualize_all(results_dir: str, output_dir: str = "visualizations"):
    """Generate all visualizations for a results directory."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    print(f"\nLoading results from {results_dir}...")
    results = load_results(results_dir)

    if not results:
        print("No results found!")
        return

    print(f"Found {len(results)} result files\n")

    print("Generating visualizations...")
    plot_training_curves(results, str(output_path / "training_curves.png"))
    plot_gradient_dynamics(results, str(output_path / "gradient_dynamics.png"))
    plot_quten_internals(results, str(output_path / "quten_internals.png"))
    plot_performance_comparison(results, str(output_path / "performance_comparison.png"))
    generate_report(results, str(output_path / "ablation_report.txt"))

    print(f"\nAll visualizations saved to {output_dir}/")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "visualizations"
    else:
        print("Usage: python visualize_ablation.py <results_dir> [output_dir]")
        print("\nTrying default directories...")
        results_dir = "ablation_results/synthetic"
        output_dir = "visualizations/synthetic"

    visualize_all(results_dir, output_dir)
