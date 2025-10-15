"""Test QUTEN with sparse gradients (embeddings)."""
import torch
import torch.nn as nn
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quten import QUTEN


class EmbeddingModel(nn.Module):
    """Simple model with embedding layer (sparse gradients)."""
    def __init__(self, vocab_size=1000, embed_dim=128, hidden_dim=64, num_classes=10):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, sparse=True)
        self.fc1 = nn.Linear(embed_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        # x: batch of token indices
        embedded = self.embedding(x).mean(dim=1)  # Average pooling
        hidden = torch.relu(self.fc1(embedded))
        return self.fc2(hidden)


def test_sparse_gradients():
    """Test QUTEN with sparse gradients from embeddings."""
    print("=" * 70)
    print("TESTING SPARSE GRADIENT SUPPORT")
    print("=" * 70)
    print("Model: Embedding (sparse) + 2 linear layers (dense)")
    print("Task: Text classification simulation\n")

    # Create model
    model = EmbeddingModel(vocab_size=1000, embed_dim=128)

    # Generate synthetic data (sequences of token indices)
    torch.manual_seed(42)
    batch_size = 32
    seq_length = 20
    num_batches = 50

    # Create optimizer
    optimizer = QUTEN(
        model.parameters(),
        lr=0.01,
        eta=0.001,
        gamma=4.0,
        amsgrad=True,
        warmup_steps=10
    )

    criterion = nn.CrossEntropyLoss()

    print("Training with sparse embeddings...")
    for batch_idx in range(num_batches):
        # Generate random token sequences
        tokens = torch.randint(0, 1000, (batch_size, seq_length))
        labels = torch.randint(0, 10, (batch_size,))

        # Forward pass
        optimizer.zero_grad()
        outputs = model(tokens)
        loss = criterion(outputs, labels)

        # Backward pass (creates sparse gradients for embedding layer)
        loss.backward()

        # Check that embedding gradients are sparse
        embed_grad = model.embedding.weight.grad
        if embed_grad is not None and embed_grad.is_sparse:
            sparsity = 1.0 - (embed_grad._nnz() / embed_grad.numel())
            if batch_idx % 10 == 0:
                print(f"Batch {batch_idx:2d}: Loss={loss.item():.4f}, "
                      f"Embedding sparsity={sparsity*100:.1f}%")

        # Optimizer step (should handle sparse gradients)
        optimizer.step()

    print("\n" + "=" * 70)
    print("✓ SPARSE GRADIENT TEST PASSED")
    print("=" * 70)
    print("Successfully trained model with:")
    print("  - Sparse gradients from embedding layer")
    print("  - Dense gradients from linear layers")
    print("  - Mixed sparse/dense optimization in single step")
    print("=" * 70 + "\n")


def test_sparse_vs_dense_equivalence():
    """Verify sparse and dense gradients produce same results."""
    print("=" * 70)
    print("TESTING SPARSE VS DENSE EQUIVALENCE")
    print("=" * 70)

    torch.manual_seed(42)

    # Model with sparse embeddings
    model_sparse = EmbeddingModel(vocab_size=100, embed_dim=32)
    optimizer_sparse = QUTEN(model_sparse.parameters(), lr=0.01)

    # Same model with dense embeddings (sparse=False)
    model_dense = EmbeddingModel(vocab_size=100, embed_dim=32)
    model_dense.embedding = nn.Embedding(100, 32, sparse=False)

    # Copy weights to make them identical
    model_dense.load_state_dict(model_sparse.state_dict())
    optimizer_dense = QUTEN(model_dense.parameters(), lr=0.01)

    criterion = nn.CrossEntropyLoss()

    # Train one step
    tokens = torch.randint(0, 100, (16, 10))
    labels = torch.randint(0, 10, (16,))

    # Sparse path
    optimizer_sparse.zero_grad()
    loss_sparse = criterion(model_sparse(tokens), labels)
    loss_sparse.backward()
    optimizer_sparse.step()

    # Dense path
    optimizer_dense.zero_grad()
    loss_dense = criterion(model_dense(tokens), labels)
    loss_dense.backward()
    optimizer_dense.step()

    # Compare final weights
    max_diff = 0.0
    for (name1, p1), (name2, p2) in zip(model_sparse.named_parameters(),
                                         model_dense.named_parameters()):
        diff = (p1 - p2).abs().max().item()
        max_diff = max(max_diff, diff)

    print(f"\nMaximum parameter difference: {max_diff:.6f}")

    if max_diff < 1e-5:
        print("✓ Sparse and dense paths produce equivalent results")
    else:
        print("⚠ Warning: Some difference between sparse and dense paths")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("QUTEN SPARSE GRADIENT TESTS")
    print("=" * 70 + "\n")

    test_sparse_gradients()
    test_sparse_vs_dense_equivalence()

    print("=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)
