# QUTEN Ablation Study

Comprehensive ablation study framework to systematically validate each component of the QUTEN optimizer.

## Overview

This ablation study tests:

### Components Tested
1. **Tunneling** (eta parameter) - Quantum-inspired exploration
2. **Observation damping** (beta_observe, gamma) - Measurement-based decoherence
3. **Uncertainty collapse** (collapse parameter) - Wavefunction collapse dynamics
4. **Adaptive tunneling** (adaptive_eta_scale) - Gradient-magnitude modulation
5. **AMSGrad** - Maximum squared gradient tracking
6. **Warmup** - Gradual observation activation

### Baselines
- **Adam** - Standard adaptive optimizer
- **AdamW** - Adam with decoupled weight decay
- **SGD+Momentum** - Classical momentum-based optimization

### Configurations
1. `QUTEN-Full` - Full QUTEN with all components
2. `QUTEN-NoTunneling` - QUTEN without tunneling (eta=0)
3. `QUTEN-NoObservation` - QUTEN without observation damping
4. `QUTEN-NoCollapse` - QUTEN without uncertainty collapse
5. `QUTEN-FixedEta` - QUTEN with fixed tunneling strength
6. `QUTEN-NoAMSGrad` - QUTEN without AMSGrad
7. `QUTEN-NoWarmup` - QUTEN without warmup
8. `QUTEN-Minimal` - Reduced to Adam-like (no quantum features)

## Quick Start

### Run the ablation study:

```bash
cd tests
PYTHONPATH=.. python ablation_study.py
```

This will:
- Test all 11 configurations (3 baselines + 8 QUTEN variants)
- Run on 2 benchmarks: Synthetic regression + Rosenbrock
- Save results to `ablation_results/`
- Print summary tables

### Generate visualizations:

```bash
python visualize_ablation.py ablation_results/synthetic visualizations/synthetic
python visualize_ablation.py ablation_results/rosenbrock visualizations/rosenbrock
```

This creates:
- `training_curves.png` - Loss evolution over time
- `gradient_dynamics.png` - Gradient and update norms
- `quten_internals.png` - QUTEN-specific internal states (sigma, observe)
- `performance_comparison.png` - Bar charts comparing final performance
- `ablation_report.txt` - Detailed text report with component analysis

## Metrics Tracked

### Effectiveness
- Final validation loss
- Best validation loss achieved
- Steps to reach loss threshold
- Generalization gap (train-val difference)

### Stability
- NaN/Inf occurrences
- Gradient norms over time
- Update norms over time
- Parameter norms over time
- Cosine similarity to baseline updates

### Efficiency
- Wall clock time
- Time per step
- Peak memory usage (GPU)

### QUTEN Internals (for QUTEN variants only)
- Mean uncertainty (sigma)
- Std uncertainty (sigma spread)
- Mean observation fidelity
- Tunneling magnitude

## Interpreting Results

### Component Contribution
Look for ablation results where removing a component:
- **Increases loss** → Component helps performance
- **Decreases loss** → Component may hurt performance (consider removing)
- **No change** → Component is neutral (may simplify without loss)

### Baseline Comparison
Compare QUTEN variants to Adam:
- **Lower loss + similar time** → Clear win
- **Lower loss + 2x time** → Trade-off (depends on application)
- **Higher loss** → Need hyperparameter tuning or component doesn't help this task

### Task-Specific Analysis
- **Smooth landscapes** (synthetic regression): Simpler optimizers may excel
- **Nonconvex landscapes** (Rosenbrock): Tunneling should show clear advantage
- **Real tasks**: Look for consistent trends across multiple benchmarks

## Customization

### Add your own benchmark:

```python
# In ablation_study.py, add to run_ablation_study():

elif benchmark == "my_task":
    print("BENCHMARK: My Custom Task")

    # Load your data
    train_loader = ...
    val_loader = ...

    # Define your model
    model_fn = lambda: MyModel()

    # Run experiments
    for config in configs:
        metrics = run_experiment(
            config=config,
            model_fn=model_fn,
            train_loader=train_loader,
            val_loader=val_loader,
            criterion=nn.CrossEntropyLoss(),
            epochs=epochs,
            device=device
        )
        results.append(metrics)
```

### Add your own ablation:

```python
# In create_ablation_configs():

AblationConfig(
    name="QUTEN-CustomAblation",
    description="Description of what this tests",
    optimizer_class="QUTEN",
    optimizer_kwargs={
        **base_quten,
        'eta': 0.0,  # Modify parameters here
        'gamma': 0.5
    }
)
```

## Expected Runtime

On CPU (M-series Mac or modern Intel):
- Synthetic regression (100 epochs × 11 configs): ~15-20 minutes
- Rosenbrock (200 epochs × 11 configs): ~5 minutes
- Total: ~25 minutes

On GPU:
- ~5-10x faster

## Output Structure

```
ablation_results/
├── synthetic/
│   ├── Adam.json
│   ├── QUTEN-Full.json
│   ├── QUTEN-NoTunneling.json
│   └── ...
└── rosenbrock/
    ├── Adam_rosenbrock.json
    └── ...

visualizations/
├── synthetic/
│   ├── training_curves.png
│   ├── gradient_dynamics.png
│   ├── quten_internals.png
│   ├── performance_comparison.png
│   └── ablation_report.txt
└── rosenbrock/
    └── ...
```

## Key Questions to Answer

1. **Which component contributes most?**
   - Look at loss delta when component is removed

2. **Does tunneling help?**
   - Compare QUTEN-Full vs QUTEN-NoTunneling
   - Should show advantage on Rosenbrock (nonconvex)

3. **Is observation necessary?**
   - Compare QUTEN-Full vs QUTEN-NoObservation
   - Tests if decoherence stabilizes learning

4. **What's the minimal effective QUTEN?**
   - Look at QUTEN-Minimal performance
   - Determines which components are essential

5. **How does QUTEN compare to Adam?**
   - Direct comparison on all metrics
   - Look for task-specific advantages

## Tips for Analysis

1. **Don't trust single runs** - Add randomized seeds and run multiple times
2. **Hyperparameter sensitivity** - Try different LR/eta values per config
3. **Task diversity** - Test on vision (CIFAR), NLP (WikiText), and tabular data
4. **Statistical significance** - Use bootstrapping or t-tests for confidence
5. **Computational budget** - Compare what each optimizer achieves in fixed time

## Next Steps

After running the ablation study:

1. **Identify winning components** - Keep what works, remove what doesn't
2. **Hyperparameter optimization** - Tune the promising configurations
3. **Scale to real tasks** - Test on production-scale problems
4. **Iterate** - Simplify based on findings, repeat

## Citation

If you use this ablation framework:

```bibtex
@software{quten_ablation,
  title={QUTEN Ablation Study Framework},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/quten}
}
```
