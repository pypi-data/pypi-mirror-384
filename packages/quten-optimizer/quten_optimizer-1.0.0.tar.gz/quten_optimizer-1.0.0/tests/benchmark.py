"""Benchmark comparing QUTEN optimizer against Adam on challenging tasks."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
import time
from quten import QUTEN


def generate_nonlinear_regression_data(n_samples=1000, n_features=20, noise=0.1):
    """Generate challenging non-linear regression problem."""
    torch.manual_seed(42)
    X = torch.randn(n_samples, n_features)

    # Complex non-linear relationship
    y = (torch.sin(X[:, 0]) +
         torch.cos(X[:, 1] * X[:, 2]) +
         X[:, 3] ** 2 -
         torch.exp(-torch.abs(X[:, 4])) +
         torch.tanh(X[:, 5:10].sum(dim=1)))

    y = y + noise * torch.randn(n_samples)
    return X, y.unsqueeze(1)


def generate_classification_data(n_samples=2000, n_features=50, n_classes=5):
    """Generate multi-class classification problem with class imbalance."""
    torch.manual_seed(42)
    X = torch.randn(n_samples, n_features)

    # Create non-linear decision boundaries
    weights = torch.randn(n_features, n_classes)
    logits = torch.tanh(X @ weights) + 0.5 * torch.sin(X[:, :10].sum(dim=1, keepdim=True))
    y = logits.argmax(dim=1)

    return X, y


class DeepNetwork(nn.Module):
    """Deep network for regression tasks."""
    def __init__(self, input_dim, hidden_dims, output_dim, dropout=0.2):
        super().__init__()
        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


class ResidualBlock(nn.Module):
    """Residual block for deeper networks."""
    def __init__(self, dim):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
            nn.ReLU(),
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim)
        )
        self.relu = nn.ReLU()

    def forward(self, x):
        return self.relu(x + self.block(x))


class ResNet(nn.Module):
    """Deep residual network for classification."""
    def __init__(self, input_dim, hidden_dim, n_blocks, n_classes):
        super().__init__()
        self.input_layer = nn.Linear(input_dim, hidden_dim)
        self.blocks = nn.ModuleList([ResidualBlock(hidden_dim) for _ in range(n_blocks)])
        self.output_layer = nn.Linear(hidden_dim, n_classes)

    def forward(self, x):
        x = F.relu(self.input_layer(x))
        for block in self.blocks:
            x = block(x)
        return self.output_layer(x)


def train_model(model, optimizer, criterion, train_loader, epochs, task_name=""):
    """Train model and return training history."""
    history = {'loss': [], 'time': []}
    model.train()

    start_time = time.time()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(train_loader)
        history['loss'].append(avg_loss)

        if epoch % 20 == 0:
            elapsed = time.time() - start_time
            print(f"  Epoch {epoch:3d}: Loss = {avg_loss:.6f}, Time = {elapsed:.2f}s")

    total_time = time.time() - start_time
    history['time'] = total_time
    return history


def benchmark_nonlinear_regression():
    """Benchmark on deep non-linear regression."""
    print("\n" + "=" * 70)
    print("BENCHMARK 1: Deep Non-Linear Regression")
    print("=" * 70)
    print("Task: 20 input features → 3 hidden layers [128, 64, 32] → 1 output")
    print("Dataset: 1000 samples with complex non-linear relationships\n")

    # Generate data
    X, y = generate_nonlinear_regression_data(n_samples=1000, n_features=20)
    dataset = TensorDataset(X, y)
    train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

    # Test Adam
    print("Training with Adam...")
    model_adam = DeepNetwork(20, [128, 64, 32], 1, dropout=0.2)
    optimizer_adam = torch.optim.Adam(model_adam.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    history_adam = train_model(model_adam, optimizer_adam, criterion, train_loader,
                               epochs=300, task_name="Adam")

    # Test QUTEN
    print("\nTraining with QUTEN...")
    model_quten = DeepNetwork(20, [128, 64, 32], 1, dropout=0.2)
    optimizer_quten = QUTEN(model_quten.parameters(), lr=0.001, eta=0.001,
                            beta1=0.9, beta2=0.999, hbar=0.1,
                            amsgrad=True, warmup_steps=200, gamma=4.0, collapse=0.998)
    criterion = nn.MSELoss()
    history_quten = train_model(model_quten, optimizer_quten, criterion, train_loader,
                                epochs=300, task_name="QUTEN")

    # Compare results
    print("\n" + "-" * 70)
    print("RESULTS:")
    print(f"  Adam  - Final Loss: {history_adam['loss'][-1]:.6f}, Time: {history_adam['time']:.2f}s")
    print(f"  QUTEN - Final Loss: {history_quten['loss'][-1]:.6f}, Time: {history_quten['time']:.2f}s")

    if history_quten['loss'][-1] < history_adam['loss'][-1]:
        improvement = (1 - history_quten['loss'][-1] / history_adam['loss'][-1]) * 100
        print(f"  → QUTEN achieved {improvement:.2f}% better loss than Adam")
    else:
        improvement = (1 - history_adam['loss'][-1] / history_quten['loss'][-1]) * 100
        print(f"  → Adam achieved {improvement:.2f}% better loss than QUTEN")
    print("-" * 70)


def benchmark_deep_classification():
    """Benchmark on deep residual network for classification."""
    print("\n" + "=" * 70)
    print("BENCHMARK 2: Deep ResNet Multi-Class Classification")
    print("=" * 70)
    print("Task: 50 input features → ResNet (128-dim, 4 blocks) → 5 classes")
    print("Dataset: 2000 samples with non-linear decision boundaries\n")

    # Generate data
    X, y = generate_classification_data(n_samples=2000, n_features=50, n_classes=5)
    dataset = TensorDataset(X, y)
    train_loader = DataLoader(dataset, batch_size=64, shuffle=True)

    # Test Adam
    print("Training with Adam...")
    model_adam = ResNet(50, 128, n_blocks=4, n_classes=5)
    optimizer_adam = torch.optim.Adam(model_adam.parameters(), lr=0.001, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    history_adam = train_model(model_adam, optimizer_adam, criterion, train_loader,
                               epochs=200, task_name="Adam")

    # Test QUTEN
    print("\nTraining with QUTEN...")
    model_quten = ResNet(50, 128, n_blocks=4, n_classes=5)
    optimizer_quten = QUTEN(model_quten.parameters(), lr=0.001, eta=0.001,
                            beta1=0.9, beta2=0.999, weight_decay=1e-4, hbar=0.1,
                            amsgrad=True, warmup_steps=200, gamma=4.0, collapse=0.998)
    criterion = nn.CrossEntropyLoss()
    history_quten = train_model(model_quten, optimizer_quten, criterion, train_loader,
                                epochs=200, task_name="QUTEN")

    # Evaluate accuracy
    model_adam.eval()
    model_quten.eval()
    with torch.no_grad():
        pred_adam = model_adam(X).argmax(dim=1)
        pred_quten = model_quten(X).argmax(dim=1)
        acc_adam = (pred_adam == y).float().mean().item() * 100
        acc_quten = (pred_quten == y).float().mean().item() * 100

    # Compare results
    print("\n" + "-" * 70)
    print("RESULTS:")
    print(f"  Adam  - Final Loss: {history_adam['loss'][-1]:.6f}, Accuracy: {acc_adam:.2f}%, Time: {history_adam['time']:.2f}s")
    print(f"  QUTEN - Final Loss: {history_quten['loss'][-1]:.6f}, Accuracy: {acc_quten:.2f}%, Time: {history_quten['time']:.2f}s")

    if acc_quten > acc_adam:
        print(f"  → QUTEN achieved {acc_quten - acc_adam:.2f}% higher accuracy")
    else:
        print(f"  → Adam achieved {acc_adam - acc_quten:.2f}% higher accuracy")
    print("-" * 70)


def benchmark_difficult_landscape():
    """Benchmark on optimization with difficult loss landscape (Rosenbrock-like)."""
    print("\n" + "=" * 70)
    print("BENCHMARK 3: Difficult Loss Landscape (Rosenbrock-inspired)")
    print("=" * 70)
    print("Task: Optimize function with narrow valley and saddle points")
    print("Target: Find minimum in difficult terrain\n")

    def rosenbrock_loss(params):
        """Generalized Rosenbrock function - narrow valley, hard to optimize."""
        loss = 0
        for i in range(len(params) - 1):
            loss += 100 * (params[i+1] - params[i]**2)**2 + (1 - params[i])**2
        return loss

    n_params = 10
    epochs = 200

    # Test Adam
    print("Training with Adam...")
    params_adam = [torch.tensor([-1.0], requires_grad=True) for _ in range(n_params)]
    optimizer_adam = torch.optim.Adam(params_adam, lr=0.01)
    history_adam_losses = []

    start_time = time.time()
    for epoch in range(epochs):
        optimizer_adam.zero_grad()
        loss = rosenbrock_loss(params_adam)
        loss.backward()
        optimizer_adam.step()
        history_adam_losses.append(loss.item())

        if epoch % 40 == 0:
            print(f"  Epoch {epoch:3d}: Loss = {loss.item():.6f}")
    time_adam = time.time() - start_time

    # Test QUTEN
    print("\nTraining with QUTEN...")
    params_quten = [torch.tensor([-1.0], requires_grad=True) for _ in range(n_params)]
    optimizer_quten = QUTEN(params_quten, lr=0.01, eta=0.1, hbar=0.01)
    history_quten_losses = []

    start_time = time.time()
    for epoch in range(epochs):
        optimizer_quten.zero_grad()
        loss = rosenbrock_loss(params_quten)
        loss.backward()
        optimizer_quten.step()
        history_quten_losses.append(loss.item())

        if epoch % 40 == 0:
            print(f"  Epoch {epoch:3d}: Loss = {loss.item():.6f}")
    time_quten = time.time() - start_time

    # Compare results
    print("\n" + "-" * 70)
    print("RESULTS:")
    print(f"  Adam  - Final Loss: {history_adam_losses[-1]:.6f}, Time: {time_adam:.2f}s")
    print(f"  QUTEN - Final Loss: {history_quten_losses[-1]:.6f}, Time: {time_quten:.2f}s")

    if history_quten_losses[-1] < history_adam_losses[-1]:
        improvement = (1 - history_quten_losses[-1] / history_adam_losses[-1]) * 100
        print(f"  → QUTEN achieved {improvement:.2f}% better loss than Adam")
        print("  → Tunneling may help escape saddle points!")
    else:
        improvement = (1 - history_adam_losses[-1] / history_quten_losses[-1]) * 100
        print(f"  → Adam achieved {improvement:.2f}% better loss than QUTEN")
    print("-" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("QUTEN vs ADAM: COMPREHENSIVE BENCHMARK")
    print("=" * 70)
    print("Testing on challenging optimization problems...")

    # Run all benchmarks
    benchmark_nonlinear_regression()
    benchmark_deep_classification()
    benchmark_difficult_landscape()

    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)
    print("\nNote: QUTEN's quantum-inspired tunneling is designed to help with:")
    print("  • Escaping local minima and saddle points")
    print("  • Exploring difficult loss landscapes")
    print("  • Providing adaptive exploration via uncertainty (sigma)")
    print("=" * 70 + "\n")
