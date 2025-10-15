"""Quick start example for QUTEN optimizer."""
import torch
import torch.nn as nn
from quten import QUTEN


def main():
    """Train a simple neural network with QUTEN."""
    print("QUTEN Optimizer - Quick Start Example")
    print("=" * 50)

    # Create synthetic data
    torch.manual_seed(42)
    X = torch.randn(100, 10)
    y = (X[:, 0] + X[:, 1] ** 2).unsqueeze(1) + 0.1 * torch.randn(100, 1)

    # Define model
    model = nn.Sequential(
        nn.Linear(10, 32),
        nn.ReLU(),
        nn.Linear(32, 16),
        nn.ReLU(),
        nn.Linear(16, 1)
    )

    # Initialize QUTEN optimizer
    optimizer = QUTEN(
        model.parameters(),
        lr=0.01,            # Learning rate
        eta=0.001,          # Tunneling strength (small for stability)
        gamma=4.0,          # Strong observation-based decoherence
        amsgrad=True,       # Use AMSGrad for extra stability
        warmup_steps=50     # Gradual observation activation
    )

    # Loss function
    criterion = nn.MSELoss()

    # Training loop
    print("\nTraining with QUTEN...")
    for epoch in range(200):
        optimizer.zero_grad()

        # Forward pass
        predictions = model(X)
        loss = criterion(predictions, y)

        # Backward pass
        loss.backward()
        optimizer.step()

        if epoch % 40 == 0:
            print(f"Epoch {epoch:3d}: Loss = {loss.item():.6f}")

    print(f"\nFinal Loss: {loss.item():.6f}")
    print("\nQUTEN successfully optimized the model!")
    print("\nKey features demonstrated:")
    print("  - Quantum-inspired tunneling for exploration")
    print("  - Observation-based decoherence for stability")
    print("  - Adaptive learning rate per parameter")
    print("  - AMSGrad variant for robust convergence")


if __name__ == "__main__":
    main()
