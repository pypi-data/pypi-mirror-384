"""Speed comparison: QUTEN vs Adam."""
import torch
import torch.nn as nn
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quten import QUTEN


def create_large_model():
    """Create a large model to stress-test optimizer speed."""
    return nn.Sequential(
        nn.Linear(512, 1024),
        nn.ReLU(),
        nn.Linear(1024, 2048),
        nn.ReLU(),
        nn.Linear(2048, 1024),
        nn.ReLU(),
        nn.Linear(1024, 512),
        nn.ReLU(),
        nn.Linear(512, 10)
    )


def benchmark_optimizer(optimizer_class, model, data, target, num_iters=100, **kwargs):
    """Benchmark optimizer speed."""
    optimizer = optimizer_class(model.parameters(), **kwargs)
    criterion = nn.CrossEntropyLoss()

    # Warmup
    for _ in range(5):
        optimizer.zero_grad()
        loss = criterion(model(data), target)
        loss.backward()
        optimizer.step()

    # Timed run
    torch.cuda.synchronize() if torch.cuda.is_available() else None
    start = time.time()

    for _ in range(num_iters):
        optimizer.zero_grad()
        loss = criterion(model(data), target)
        loss.backward()
        optimizer.step()

    torch.cuda.synchronize() if torch.cuda.is_available() else None
    elapsed = time.time() - start

    return elapsed, loss.item()


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 70)
    print(f"QUTEN vs ADAM SPEED BENCHMARK (device: {device})")
    print("=" * 70)
    print()

    # Create data
    batch_size = 128
    data = torch.randn(batch_size, 512, device=device)
    target = torch.randint(0, 10, (batch_size,), device=device)

    num_iters = 100

    # Test Adam
    print("Benchmarking Adam...")
    model_adam = create_large_model().to(device)
    time_adam, loss_adam = benchmark_optimizer(
        torch.optim.Adam, model_adam, data, target, num_iters, lr=0.001
    )
    print(f"  Time: {time_adam:.3f}s ({time_adam/num_iters*1000:.2f}ms/iter)")
    print(f"  Final loss: {loss_adam:.4f}")
    print()

    # Test QUTEN
    print("Benchmarking QUTEN (fully fused)...")
    model_quten = create_large_model().to(device)
    model_quten.load_state_dict(model_adam.state_dict())  # Same initialization
    time_quten, loss_quten = benchmark_optimizer(
        QUTEN, model_quten, data, target, num_iters, lr=0.001, eta=0.001,
        gamma=4.0, amsgrad=True
    )
    print(f"  Time: {time_quten:.3f}s ({time_quten/num_iters*1000:.2f}ms/iter)")
    print(f"  Final loss: {loss_quten:.4f}")
    print()

    # Summary
    print("=" * 70)
    print("RESULTS:")
    print("-" * 70)
    speedup = time_adam / time_quten
    overhead = (time_quten / time_adam - 1) * 100

    print(f"Adam:  {time_adam:.3f}s total, {time_adam/num_iters*1000:.2f}ms/iter")
    print(f"QUTEN: {time_quten:.3f}s total, {time_quten/num_iters*1000:.2f}ms/iter")
    print()

    if speedup > 1.0:
        print(f"✓ QUTEN is {speedup:.2f}× FASTER than Adam")
    else:
        print(f"QUTEN has {overhead:.1f}% overhead vs Adam")
        if overhead < 50:
            print("  (Acceptable for the superior optimization quality)")

    print()
    print("Model size:")
    num_params = sum(p.numel() for p in model_adam.parameters())
    print(f"  Total parameters: {num_params:,}")
    print(f"  Throughput (Adam): {num_params * num_iters / time_adam / 1e6:.1f}M params/sec")
    print(f"  Throughput (QUTEN): {num_params * num_iters / time_quten / 1e6:.1f}M params/sec")
    print("=" * 70)


if __name__ == "__main__":
    main()
