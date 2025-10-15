# QUTEN Ablation Study

## Overview

This repository includes a comprehensive ablation study framework that systematically validates each component of the QUTEN optimizer through controlled experiments on realistic tasks.

## Quick Start

### Run Locally

```bash
cd tests
python run_ablation_production.py
```

This will:
- Generate realistic CIFAR-like classification data (5000 train / 1000 val samples)
- Train 6 optimizers for 100 epochs each:
  - **Baselines**: Adam, AdamW, SGD+Momentum
  - **QUTEN variants**: Full, NoTunneling, NoObservation
- Generate publication-quality PNG visualizations
- Save results to `ablation_results/`

**Runtime**: ~10-15 minutes on modern CPU

### Output Files

```
ablation_results/
├── loss_curves.png           # Training/validation loss evolution
├── performance_bars.png       # Performance comparison charts
├── gradient_dynamics.png      # Gradient and update norm evolution
├── summary_table.png          # Results summary table
└── results.json              # Raw data for further analysis
```

## GitHub Actions Integration

The ablation study runs automatically on:
- Every push to `main` or `develop`
- Every pull request
- Manual trigger via GitHub Actions UI

### Workflow Features

✅ **Automated Testing** - Runs on every PR to catch regressions
📊 **PR Comments** - Posts results directly to pull requests
📈 **Artifacts** - Uploads all visualizations for 30 days
⚠️ **Regression Detection** - Fails if QUTEN-Full degrades >10% vs Adam

### View Results

1. Go to **Actions** tab in GitHub
2. Click on latest "QUTEN Ablation Study" workflow
3. Download artifacts or view summary

## What's Being Tested

### Components

| Component | Ablation | Description |
|-----------|----------|-------------|
| **Tunneling** | `NoTunneling` | Tests quantum-inspired exploration (eta=0) |
| **Observation** | `NoObservation` | Tests measurement-based decoherence (gamma=0) |
| **Collapse** | N/A | Tests uncertainty decay dynamics |
| **AMSGrad** | N/A | Tests max squared gradient tracking |
| **Warmup** | N/A | Tests gradual observation activation |

### Metrics

**Effectiveness**
- Final validation loss (primary metric)
- Best validation loss achieved
- Convergence speed (epochs to threshold)

**Stability**
- Gradient norms over time
- Update norms over time
- No NaN/Inf occurrences

**Efficiency**
- Wall-clock training time
- Time per epoch

## Interpreting Results

### Loss Curves (`loss_curves.png`)

**What to look for:**
- Smooth convergence = stable optimizer
- Faster initial drop = good exploration
- Lower plateau = better final performance

**Red flags:**
- Oscillations = instability
- Divergence = too aggressive updates
- Slow convergence = poor exploration

### Performance Bars (`performance_bars.png`)

**Comparison dimensions:**
1. **Final Loss** - Which optimizer achieves best final performance?
2. **Best Loss** - Which optimizer achieves best peak performance?
3. **Time** - Which optimizer is most efficient?
4. **Convergence** - Which optimizer converges fastest?

### Gradient Dynamics (`gradient_dynamics.png`)

**What to look for:**
- Steady decrease = healthy optimization
- Stable update norms = controlled steps
- No spikes = numerical stability

**QUTEN-specific:**
- Adaptive updates should show more variance (exploration)
- Tunneling should allow occasional large steps
- Observation should dampen updates over time

## Customization

### Add Your Own Task

```python
# In run_ablation_production.py, modify main():

# Replace data generation
X_train, y_train = load_your_training_data()
X_val, y_val = load_your_validation_data()

# Replace model
class YourModel(nn.Module):
    def __init__(self):
        super().__init__()
        # Your architecture here
```

### Add Your Own Ablation

```python
# In run_ablation_production.py, add to configs list:

Config("QUTEN-YourAblation", "QUTEN", {
    'lr': 0.001,
    'eta': 0.0,      # Modify parameters
    'gamma': 0.5,    # to test specific components
    # ... other params
}, '#your_color')
```

### Adjust Training

```python
# In run_ablation_production.py, modify:

epochs = 200  # More epochs for harder tasks
batch_size = 128  # Larger batches for stability
```

## Expected Performance

On the default CIFAR-like task:

| Optimizer | Typical Final Loss | Typical Best Loss |
|-----------|-------------------|-------------------|
| Adam | 0.30-0.40 | 0.25-0.35 |
| AdamW | 0.28-0.38 | 0.24-0.34 |
| SGD+Momentum | 0.35-0.50 | 0.30-0.45 |
| QUTEN-Full | 0.25-0.40 | 0.22-0.35 |
| QUTEN-NoTunneling | 0.30-0.45 | 0.25-0.38 |
| QUTEN-NoObservation | 0.28-0.42 | 0.24-0.36 |

**Note**: Results vary due to random initialization. Run multiple times for statistical confidence.

## Key Findings Template

When analyzing results, answer these questions:

### 1. Overall Performance
- Which optimizer achieves the lowest final loss?
- Is the difference statistically significant?

### 2. Component Contribution
- Does removing tunneling (NoTunneling) hurt performance?
  - **If yes**: Tunneling helps exploration
  - **If no**: Task may not need exploration
- Does removing observation (NoObservation) hurt performance?
  - **If yes**: Decoherence provides stability
  - **If no**: Task is already well-behaved

### 3. Baseline Comparison
- How does QUTEN-Full compare to Adam?
  - Better: **+X% improvement**
  - Worse: **-X% degradation**
  - Similar: Within ±5%

### 4. Trade-offs
- Time cost: Is QUTEN X% slower?
- Convergence: Does QUTEN converge in fewer epochs?
- Stability: Are gradients/updates well-behaved?

## CI/CD Integration Tips

### For Pull Requests

The workflow will:
1. Run ablation study automatically
2. Post results as PR comment
3. Fail if QUTEN-Full regresses >10% vs Adam

**What to check:**
- Look for performance regressions in PR comments
- Download artifacts to inspect visualizations
- Check logs if workflow fails

### For Releases

Before tagging a release:
1. Run ablation study manually: `python tests/run_ablation_production.py`
2. Verify QUTEN-Full beats Adam on at least one metric
3. Check that no components cause >15% degradation
4. Document results in release notes

## Troubleshooting

### "Module not found" errors
```bash
# Ensure you're in the tests directory
cd tests

# Or set PYTHONPATH
PYTHONPATH=.. python run_ablation_production.py
```

### Memory issues
```python
# Reduce batch size or model size
batch_size = 32  # Instead of 64
# Or reduce dataset size
n_train = 2000  # Instead of 5000
```

### Slow training
```python
# Use GPU if available (auto-detected)
# Or reduce epochs
epochs = 50  # Instead of 100
```

### Different results each run
```python
# Set seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)
```

## Dependencies

```bash
pip install torch torchvision matplotlib numpy
```

**Minimum versions:**
- Python ≥ 3.8
- PyTorch ≥ 1.12
- Matplotlib ≥ 3.5
- NumPy ≥ 1.21

## Citation

If you use this ablation framework in your research:

```bibtex
@software{quten_ablation2025,
  title={QUTEN Ablation Study Framework},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/quten}
}
```

## License

Same as QUTEN optimizer (see LICENSE file).

## Contributing

To add new ablation experiments:

1. Fork the repository
2. Add your configuration in `run_ablation_production.py`
3. Run locally to verify
4. Submit PR with results

## Questions?

- **Issues**: Open a GitHub issue
- **Discussions**: Start a GitHub discussion
- **Email**: your.email@example.com

---

**Pro tip**: Run the ablation study on YOUR specific task to see if QUTEN helps. Generic results don't always transfer!
