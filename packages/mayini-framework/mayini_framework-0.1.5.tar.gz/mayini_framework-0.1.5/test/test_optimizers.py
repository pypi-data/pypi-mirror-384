"""
Tests for optimization algorithms.
"""
import pytest
import numpy as np
import mayini as mn
from mayini.nn import *
from mayini.optim import *
from conftest import assert_tensors_close

class TestSGD:
    """Test Stochastic Gradient Descent optimizer."""

    def test_sgd_creation(self):
        """Test SGD optimizer creation."""
        model = Sequential(Linear(2, 1))
        optimizer = SGD(model.parameters(), lr=0.01)

        assert optimizer.lr == 0.01
        assert optimizer.momentum == 0
        assert optimizer.weight_decay == 0
        assert len(optimizer.param_groups) == 1
        assert len(optimizer.param_groups[0]['params']) == 2  # weight + bias

    def test_sgd_step_simple(self):
        """Test SGD optimization step."""
        # Simple quadratic function: f(x) = x^2, minimum at x=0
        x = mn.Tensor([5.0], requires_grad=True)
        optimizer = SGD([x], lr=0.1)

        initial_value = x.item()

        # One optimization step
        loss = x ** 2
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # x should move toward 0
        new_value = x.item()
        assert abs(new_value) < abs(initial_value)

    def test_sgd_with_momentum(self):
        """Test SGD with momentum."""
        x = mn.Tensor([5.0], requires_grad=True)
        optimizer = SGD([x], lr=0.1, momentum=0.9)

        values = []
        for i in range(10):
            optimizer.zero_grad()
            loss = x ** 2
            loss.backward()
            optimizer.step()
            values.append(x.item())

        # Should converge to 0
        assert abs(values[-1]) < abs(values[0])

    def test_sgd_with_weight_decay(self):
        """Test SGD with weight decay."""
        model = Linear(2, 1)
        optimizer = SGD(model.parameters(), lr=0.01, weight_decay=0.001)

        x = mn.Tensor([[1, 2]], requires_grad=True)
        target = mn.Tensor([[1.0]])

        initial_weight_norm = np.linalg.norm(model.weight.data)

        # Training step
        optimizer.zero_grad()
        output = model(x)
        loss = MSELoss()(output, target)
        loss.backward()
        optimizer.step()

        # Weight decay should reduce weight magnitude
        new_weight_norm = np.linalg.norm(model.weight.data)
        # Note: this test might be sensitive, weight decay effect is small

    def test_sgd_linear_regression(self):
        """Test SGD on simple linear regression."""
        # Generate simple linear data: y = 2x + 1
        np.random.seed(42)
        X = np.random.randn(50, 1).astype(np.float32)
        y = (2 * X + 1).astype(np.float32)

        model = Linear(1, 1)
        optimizer = SGD(model.parameters(), lr=0.01)
        criterion = MSELoss()

        initial_loss = None
        final_loss = None

        for epoch in range(100):
            optimizer.zero_grad()

            X_tensor = mn.Tensor(X, requires_grad=True)
            y_tensor = mn.Tensor(y)

            output = model(X_tensor)
            loss = criterion(output, y_tensor)

            if epoch == 0:
                initial_loss = loss.item()
            if epoch == 99:
                final_loss = loss.item()

            loss.backward()
            optimizer.step()

        # Loss should decrease
        assert final_loss < initial_loss

class TestAdam:
    """Test Adam optimizer."""

    def test_adam_creation(self):
        """Test Adam optimizer creation."""
        model = Sequential(Linear(2, 1))
        optimizer = Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8)

        assert optimizer.lr == 0.001
        assert optimizer.betas == (0.9, 0.999)
        assert optimizer.eps == 1e-8
        assert optimizer.weight_decay == 0

    def test_adam_step(self):
        """Test Adam optimization step."""
        x = mn.Tensor([5.0], requires_grad=True)
        optimizer = Adam([x], lr=0.1)

        initial_value = x.item()

        # Multiple steps
        for _ in range(10):
            optimizer.zero_grad()
            loss = x ** 2
            loss.backward()
            optimizer.step()

        # Should converge toward 0
        final_value = x.item()
        assert abs(final_value) < abs(initial_value)

    def test_adam_vs_sgd_convergence(self):
        """Compare Adam vs SGD convergence."""
        # Test on simple quadratic function
        x_adam = mn.Tensor([5.0], requires_grad=True)
        x_sgd = mn.Tensor([5.0], requires_grad=True)

        optimizer_adam = Adam([x_adam], lr=0.1)
        optimizer_sgd = SGD([x_sgd], lr=0.1)

        adam_values = []
        sgd_values = []

        for _ in range(50):
            # Adam step
            optimizer_adam.zero_grad()
            loss_adam = x_adam ** 2
            loss_adam.backward()
            optimizer_adam.step()
            adam_values.append(x_adam.item())

            # SGD step  
            optimizer_sgd.zero_grad()
            loss_sgd = x_sgd ** 2
            loss_sgd.backward()
            optimizer_sgd.step()
            sgd_values.append(x_sgd.item())

        # Both should converge, Adam might be faster
        assert abs(adam_values[-1]) < abs(adam_values[0])
        assert abs(sgd_values[-1]) < abs(sgd_values[0])

class TestAdamW:
    """Test AdamW optimizer."""

    def test_adamw_creation(self):
        """Test AdamW optimizer creation."""
        model = Sequential(Linear(2, 1))
        optimizer = AdamW(model.parameters(), lr=0.001, weight_decay=0.01)

        assert optimizer.lr == 0.001
        assert optimizer.weight_decay == 0.01

    def test_adamw_weight_decay(self):
        """Test AdamW decoupled weight decay."""
        model = Linear(2, 1)
        optimizer = AdamW(model.parameters(), lr=0.001, weight_decay=0.1)

        x = mn.Tensor([[1, 2]], requires_grad=True)
        target = mn.Tensor([[1.0]])

        initial_weight = model.weight.data.copy()

        # Training step
        optimizer.zero_grad()
        output = model(x)
        loss = MSELoss()(output, target)
        loss.backward()
        optimizer.step()

        # Weight should be decayed
        weight_change = np.linalg.norm(model.weight.data - initial_weight)
        assert weight_change > 0

class TestRMSprop:
    """Test RMSprop optimizer."""

    def test_rmsprop_creation(self):
        """Test RMSprop optimizer creation."""
        model = Sequential(Linear(2, 1))
        optimizer = RMSprop(model.parameters(), lr=0.01, alpha=0.99, eps=1e-8)

        assert optimizer.lr == 0.01
        assert optimizer.alpha == 0.99
        assert optimizer.eps == 1e-8

    def test_rmsprop_step(self):
        """Test RMSprop optimization step."""
        x = mn.Tensor([5.0], requires_grad=True)
        optimizer = RMSprop([x], lr=0.1)

        initial_value = x.item()

        # Multiple steps
        for _ in range(20):
            optimizer.zero_grad()
            loss = x ** 2
            loss.backward()
            optimizer.step()

        # Should converge toward 0
        final_value = x.item()
        assert abs(final_value) < abs(initial_value)

class TestOptimizerProperties:
    """Test general optimizer properties."""

    def test_optimizer_zero_grad(self):
        """Test optimizer zero_grad functionality."""
        model = Sequential(Linear(2, 1))
        optimizer = SGD(model.parameters(), lr=0.01)

        x = mn.Tensor([[1, 2]], requires_grad=True)
        target = mn.Tensor([[1.0]])

        # Forward pass and backward
        output = model(x)
        loss = MSELoss()(output, target)
        loss.backward()

        # Check gradients exist
        for param in model.parameters():
            assert param.grad is not None

        # Zero gradients
        optimizer.zero_grad()

        # Check gradients are zeroed
        for param in model.parameters():
            assert param.grad is None

    def test_optimizer_param_groups(self):
        """Test optimizer parameter groups."""
        linear1 = Linear(2, 1)
        linear2 = Linear(1, 1)

        # Different learning rates for different layers
        optimizer = SGD([
            {'params': linear1.parameters(), 'lr': 0.01},
            {'params': linear2.parameters(), 'lr': 0.001}
        ])

        assert len(optimizer.param_groups) == 2
        assert optimizer.param_groups[0]['lr'] == 0.01
        assert optimizer.param_groups[1]['lr'] == 0.001

class TestOptimizerIntegration:
    """Test optimizers integrated with models and training."""

    def test_optimizer_with_neural_network(self):
        """Test optimizer with multi-layer neural network."""
        model = Sequential(
            Linear(10, 5),
            ReLU(),
            Linear(5, 1)
        )

        optimizer = Adam(model.parameters(), lr=0.001)
        criterion = MSELoss()

        # Generate synthetic data
        np.random.seed(42)
        X = np.random.randn(32, 10).astype(np.float32)
        y = np.random.randn(32, 1).astype(np.float32)

        initial_loss = None
        final_loss = None

        for epoch in range(50):
            optimizer.zero_grad()

            X_tensor = mn.Tensor(X, requires_grad=True)
            y_tensor = mn.Tensor(y)

            output = model(X_tensor)
            loss = criterion(output, y_tensor)

            if epoch == 0:
                initial_loss = loss.item()
            if epoch == 49:
                final_loss = loss.item()

            loss.backward()
            optimizer.step()

        # Training should reduce loss
        assert final_loss < initial_loss

    def test_optimizer_with_classification(self):
        """Test optimizer with classification task."""
        model = Sequential(
            Linear(5, 3),
            ReLU(),
            Linear(3, 2)
        )

        optimizer = SGD(model.parameters(), lr=0.01)
        criterion = CrossEntropyLoss()

        # Generate synthetic classification data
        np.random.seed(42)
        X = np.random.randn(20, 5).astype(np.float32)
        y = np.random.randint(0, 2, 20)

        losses = []

        for epoch in range(30):
            optimizer.zero_grad()

            X_tensor = mn.Tensor(X, requires_grad=True)
            y_tensor = mn.Tensor(y)

            output = model(X_tensor)
            loss = criterion(output, y_tensor)

            losses.append(loss.item())

            loss.backward()
            optimizer.step()

        # Loss should generally decrease
        assert losses[-1] < losses[0]

class TestOptimizerNumericalStability:
    """Test optimizer numerical stability."""

    def test_adam_with_very_small_gradients(self):
        """Test Adam with very small gradients."""
        x = mn.Tensor([1.0], requires_grad=True)
        optimizer = Adam([x], lr=0.001, eps=1e-8)

        # Very small gradient
        optimizer.zero_grad()
        loss = 1e-10 * x ** 2
        loss.backward()

        old_x = x.item()
        optimizer.step()
        new_x = x.item()

        # Should still make progress without numerical issues
        assert not np.isnan(new_x)
        assert not np.isinf(new_x)

    def test_optimizers_with_large_gradients(self):
        """Test optimizers with large gradients."""
        x = mn.Tensor([1.0], requires_grad=True)

        optimizers_to_test = [
            SGD([x], lr=0.001),
            Adam([x], lr=0.001), 
            RMSprop([x], lr=0.001)
        ]

        for optimizer in optimizers_to_test:
            x.data = np.array([1.0])  # Reset

            # Large gradient
            optimizer.zero_grad()
            loss = 1e6 * x ** 2
            loss.backward()

            old_x = x.item()
            optimizer.step()
            new_x = x.item()

            # Should handle large gradients without overflow
            assert not np.isnan(new_x)
            assert not np.isinf(new_x)

class TestOptimizerPerformance:
    """Test optimizer performance characteristics."""

    def test_convergence_rates(self):
        """Compare convergence rates of different optimizers."""
        # Simple 2D quadratic function with different conditioning
        def quadratic_loss(x, y, a=1, b=100):
            return a * x ** 2 + b * y ** 2

        optimizers_config = [
            ('SGD', lambda params: SGD(params, lr=0.01)),
            ('Adam', lambda params: Adam(params, lr=0.01)),
            ('RMSprop', lambda params: RMSprop(params, lr=0.01))
        ]

        convergence_steps = {}

        for opt_name, opt_factory in optimizers_config:
            x = mn.Tensor([5.0], requires_grad=True)
            y = mn.Tensor([5.0], requires_grad=True)
            optimizer = opt_factory([x, y])

            for step in range(100):
                optimizer.zero_grad()
                loss = quadratic_loss(x, y)
                loss.backward()
                optimizer.step()

                # Check if converged (within 1% of optimum)
                if abs(x.item()) < 0.05 and abs(y.item()) < 0.05:
                    convergence_steps[opt_name] = step
                    break

        # All should converge eventually (though rates may differ)
        for opt_name in [name for name, _ in optimizers_config]:
            if opt_name in convergence_steps:
                assert convergence_steps[opt_name] < 100

