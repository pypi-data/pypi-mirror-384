# Contributing to QUTEN

Thank you for your interest in contributing to QUTEN! This document provides guidelines for contributions.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quten.git
cd quten
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

## Running Tests

Run the basic functionality tests:
```bash
python tests/test_basic.py
```

Run comprehensive benchmarks:
```bash
python tests/benchmark.py
```

Run the quick start example:
```bash
python example.py
```

## Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable names
- Add docstrings to all functions and classes
- Keep functions focused and concise

Format code with black (if available):
```bash
black quten.py tests/
```

## Areas for Contribution

### High Priority
- [ ] Learning rate scheduler integration
- [ ] Gradient accumulation support
- [ ] Mixed precision (AMP) compatibility
- [ ] Distributed training support (DDP)
- [ ] More comprehensive unit tests

### Research Directions
- [ ] Layer-wise adaptive tunneling strength
- [ ] Convergence theory and proofs
- [ ] Comparison with other quantum-inspired optimizers
- [ ] Hyperparameter auto-tuning
- [ ] Performance on large-scale models (BERT, ResNet-50+)

### Documentation
- [ ] Tutorial notebooks
- [ ] Video demonstrations
- [ ] More usage examples
- [ ] FAQ section
- [ ] Theoretical background deep-dive

### Benchmarks
- [ ] Computer vision tasks (CIFAR-10, ImageNet)
- [ ] NLP tasks (GLUE, machine translation)
- [ ] Reinforcement learning
- [ ] Generative models (GANs, VAEs)

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Pull Request Guidelines

- Describe what your PR does and why
- Reference any related issues
- Include test results if applicable
- Update documentation if you change functionality
- Keep PRs focused on a single feature or fix

## Reporting Bugs

Use GitHub Issues to report bugs. Include:
- Python version
- PyTorch version
- Operating system
- Minimal code to reproduce the issue
- Expected vs actual behavior
- Error messages or stack traces

## Feature Requests

We welcome feature requests! Please:
- Check if the feature has already been requested
- Clearly describe the use case
- Provide examples of how it would be used
- Consider whether it fits the project scope

## Questions?

Feel free to open an issue with the "question" label or reach out to the maintainers.

## Code of Conduct

Be respectful and constructive in all interactions. We aim to foster an inclusive and welcoming community.

---

Thank you for contributing to QUTEN!
