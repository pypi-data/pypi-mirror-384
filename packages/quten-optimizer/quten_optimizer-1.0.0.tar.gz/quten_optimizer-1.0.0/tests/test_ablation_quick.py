"""
Quick test of ablation study framework.
Runs a minimal version to verify everything works.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ablation_study import (
    create_ablation_configs,
    run_ablation_study,
    print_summary_table
)
import torch

if __name__ == "__main__":
    print("\n" + "="*70)
    print("QUICK ABLATION TEST")
    print("="*70)
    print("Running a quick test with reduced epochs to verify setup...\n")

    device = torch.device('cpu')  # Force CPU for quick test

    # Create limited set of configs for testing
    all_configs = create_ablation_configs()

    # Test just a few configs
    test_configs = [
        all_configs[0],  # Adam
        all_configs[3],  # QUTEN-Full
        all_configs[4],  # QUTEN-NoTunneling
    ]

    print(f"Testing {len(test_configs)} configurations with 10 epochs each:\n")
    for config in test_configs:
        print(f"  - {config.name}")

    # Run quick ablation
    results = run_ablation_study(
        configs=test_configs,
        benchmark="synthetic",
        epochs=10,  # Very short
        batch_size=32,
        device=device,
        save_dir="test_ablation_results"
    )

    # Print summary
    if results:
        print_summary_table(results)
        print("\n✓ Ablation framework is working correctly!")
        print("\nTo run full study:")
        print("  PYTHONPATH=.. python ablation_study.py")
    else:
        print("\n✗ Something went wrong!")

    print("\n" + "="*70)
