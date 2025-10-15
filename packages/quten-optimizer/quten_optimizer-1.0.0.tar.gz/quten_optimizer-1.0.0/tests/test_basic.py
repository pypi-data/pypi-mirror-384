import torch
import torch.nn as nn
from quten import QUTEN

# Simple test: optimize a quadratic function
def test_quadratic():
    """Test QUTEN on a simple quadratic: f(x) = (x - 3)^2"""
    print("=" * 50)
    print("Test 1: Quadratic Function f(x) = (x - 3)^2")
    print("=" * 50)

    # Initialize parameter
    x = torch.tensor([0.0], requires_grad=True)

    # Create optimizer
    optimizer = QUTEN([x], lr=0.1, eta=0.01)

    # Optimization loop
    for step in range(100):
        optimizer.zero_grad()

        # Loss: (x - 3)^2, minimum at x = 3
        loss = (x - 3) ** 2
        loss.backward()

        optimizer.step()

        if step % 20 == 0:
            print(f"Step {step:3d}: x = {x.item():.6f}, loss = {loss.item():.6f}")

    print(f"\nFinal: x = {x.item():.6f} (target: 3.0)")
    print(f"Error: {abs(x.item() - 3.0):.6f}\n")


# Test on a simple neural network
def test_neural_network():
    """Test QUTEN on a simple neural network learning XOR"""
    print("=" * 50)
    print("Test 2: Neural Network Learning XOR")
    print("=" * 50)

    # XOR dataset
    X = torch.tensor([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])
    y = torch.tensor([[0.0], [1.0], [1.0], [0.0]])

    # Simple 2-layer network
    model = nn.Sequential(
        nn.Linear(2, 4),
        nn.Tanh(),
        nn.Linear(4, 1),
        nn.Sigmoid()
    )

    # Create optimizer
    optimizer = QUTEN(model.parameters(), lr=0.5, eta=0.05, beta1=0.9, beta2=0.999)
    criterion = nn.BCELoss()

    # Training loop
    for epoch in range(500):
        optimizer.zero_grad()

        # Forward pass
        outputs = model(X)
        loss = criterion(outputs, y)

        # Backward pass
        loss.backward()
        optimizer.step()

        if epoch % 100 == 0:
            print(f"Epoch {epoch:3d}: Loss = {loss.item():.6f}")

    # Final predictions
    print("\nFinal predictions:")
    with torch.no_grad():
        predictions = model(X)
        for i in range(4):
            print(f"Input: {X[i].tolist()} -> Output: {predictions[i].item():.4f} (Target: {y[i].item():.1f})")
    print()


# Test with entanglement enabled
def test_with_entanglement():
    """Test QUTEN with entanglement coupling"""
    print("=" * 50)
    print("Test 3: Multiple Parameters with Entanglement")
    print("=" * 50)

    # Multiple parameters that should converge to [1, 2, 3]
    params = [torch.tensor([0.0], requires_grad=True) for _ in range(3)]
    targets = [1.0, 2.0, 3.0]

    # Optimizer with entanglement
    optimizer = QUTEN(params, lr=0.1, eta=0.02, entangle=0.05)

    for step in range(100):
        optimizer.zero_grad()

        # Individual losses: (p - target)^2
        total_loss = sum((p - t) ** 2 for p, t in zip(params, targets))
        total_loss.backward()

        optimizer.step()

        if step % 20 == 0:
            values = [p.item() for p in params]
            print(f"Step {step:3d}: params = [{values[0]:.4f}, {values[1]:.4f}, {values[2]:.4f}], loss = {total_loss.item():.6f}")

    print(f"\nFinal values: [{params[0].item():.4f}, {params[1].item():.4f}, {params[2].item():.4f}]")
    print(f"Target values: [1.0000, 2.0000, 3.0000]\n")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("QUTEN Optimizer Tests")
    print("=" * 50 + "\n")

    # Run all tests
    test_quadratic()
    test_neural_network()
    test_with_entanglement()

    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)
