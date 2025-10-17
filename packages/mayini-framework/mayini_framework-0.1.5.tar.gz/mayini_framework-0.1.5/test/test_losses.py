"""
Tests for loss functions.
"""
import pytest
import numpy as np
import mayini as mn
from mayini.nn import *
from conftest import assert_tensors_close, assert_gradient_close

class TestMSELoss:
    """Test Mean Squared Error loss function."""

    def test_mse_forward(self):
        """Test MSE forward pass."""
        criterion = MSELoss()

        pred = mn.Tensor([[1, 2, 3]], requires_grad=True)
        target = mn.Tensor([[1, 1, 1]])

        loss = criterion(pred, target)

        # MSE = mean((pred - target)^2) = mean([0, 1, 4]) = 5/3
        expected = 5.0 / 3.0
        assert_tensors_close(loss, expected)

    def test_mse_backward(self):
        """Test MSE backward pass."""
        criterion = MSELoss()

        pred = mn.Tensor([[1, 2, 3]], requires_grad=True)
        target = mn.Tensor([[1, 1, 1]])

        loss = criterion(pred, target)
        loss.backward()

        # Gradient: 2 * (pred - target) / N = 2 * [0, 1, 2] / 3
        expected_grad = np.array([[0, 2.0/3.0, 4.0/3.0]])
        assert_gradient_close(pred, expected_grad)

    def test_mse_reduction_modes(self):
        """Test different reduction modes."""
        pred = mn.Tensor([[1, 2], [3, 4]], requires_grad=True)
        target = mn.Tensor([[1, 1], [1, 1]])

        # Mean reduction (default)
        criterion_mean = MSELoss(reduction='mean')
        loss_mean = criterion_mean(pred, target)
        expected_mean = np.mean((pred.data - target.data) ** 2)
        assert_tensors_close(loss_mean, expected_mean)

        # Sum reduction
        criterion_sum = MSELoss(reduction='sum')
        loss_sum = criterion_sum(pred, target)
        expected_sum = np.sum((pred.data - target.data) ** 2)
        assert_tensors_close(loss_sum, expected_sum)

        # None reduction
        criterion_none = MSELoss(reduction='none')
        loss_none = criterion_none(pred, target)
        expected_none = (pred.data - target.data) ** 2
        assert_tensors_close(loss_none, expected_none)

class TestMAELoss:
    """Test Mean Absolute Error loss function."""

    def test_mae_forward(self):
        """Test MAE forward pass."""
        criterion = MAELoss()

        pred = mn.Tensor([[1, 2, 3]], requires_grad=True)
        target = mn.Tensor([[1, 1, 1]])

        loss = criterion(pred, target)

        # MAE = mean(|pred - target|) = mean([0, 1, 2]) = 1
        expected = 1.0
        assert_tensors_close(loss, expected)

    def test_mae_backward(self):
        """Test MAE backward pass."""
        criterion = MAELoss()

        pred = mn.Tensor([[1, 2, 3]], requires_grad=True)
        target = mn.Tensor([[1, 1, 1]])

        loss = criterion(pred, target)
        loss.backward()

        # Gradient: sign(pred - target) / N = [0, 1, 1] / 3
        expected_grad = np.array([[0, 1.0/3.0, 1.0/3.0]])
        assert_gradient_close(pred, expected_grad)

class TestHuberLoss:
    """Test Huber loss function."""

    def test_huber_forward_smooth(self):
        """Test Huber loss in smooth (L2) region."""
        criterion = HuberLoss(delta=1.0)

        pred = mn.Tensor([[1.0, 1.5]], requires_grad=True)
        target = mn.Tensor([[1.0, 1.0]])

        loss = criterion(pred, target)

        # For |pred - target| <= delta, Huber = 0.5 * (pred - target)^2
        # |0| <= 1, so 0.5 * 0^2 = 0
        # |0.5| <= 1, so 0.5 * 0.5^2 = 0.125
        # Mean = 0.0625
        expected = 0.0625
        assert_tensors_close(loss, expected)

    def test_huber_forward_linear(self):
        """Test Huber loss in linear (L1) region."""
        criterion = HuberLoss(delta=1.0)

        pred = mn.Tensor([[3.0]], requires_grad=True)
        target = mn.Tensor([[1.0]])

        loss = criterion(pred, target)

        # For |pred - target| > delta, Huber = delta * (|pred - target| - 0.5 * delta)
        # |2| > 1, so 1 * (2 - 0.5) = 1.5
        expected = 1.5
        assert_tensors_close(loss, expected)

class TestCrossEntropyLoss:
    """Test Cross-Entropy loss function."""

    def test_crossentropy_forward(self):
        """Test Cross-Entropy forward pass."""
        criterion = CrossEntropyLoss()

        # Logits (before softmax)
        pred = mn.Tensor([[1.0, 2.0, 0.5]], requires_grad=True)
        target = mn.Tensor([1])  # Class 1

        loss = criterion(pred, target)

        # Should be positive
        assert loss.item() > 0

        # Loss should decrease if we increase the logit for the correct class
        pred_better = mn.Tensor([[1.0, 3.0, 0.5]], requires_grad=True)
        loss_better = criterion(pred_better, target)
        assert loss_better.item() < loss.item()

    def test_crossentropy_backward(self):
        """Test Cross-Entropy backward pass."""
        criterion = CrossEntropyLoss()

        pred = mn.Tensor([[1.0, 2.0, 0.5]], requires_grad=True)
        target = mn.Tensor([1])

        loss = criterion(pred, target)
        loss.backward()

        # Gradient should exist and have correct shape
        assert pred.grad is not None
        assert pred.grad.shape == pred.shape

        # Gradient for correct class should be negative (to decrease loss)
        assert pred.grad[0, 1] < 0

    def test_crossentropy_batch(self):
        """Test Cross-Entropy with batch input."""
        criterion = CrossEntropyLoss()

        pred = mn.Tensor([[1.0, 2.0], [0.5, 1.5]], requires_grad=True)
        target = mn.Tensor([1, 0])

        loss = criterion(pred, target)

        # Should handle batch correctly
        assert loss.item() > 0

        loss.backward()
        assert pred.grad is not None
        assert pred.grad.shape == (2, 2)

class TestBCELoss:
    """Test Binary Cross-Entropy loss function."""

    def test_bce_forward(self):
        """Test BCE forward pass."""
        criterion = BCELoss()

        pred = mn.Tensor([[0.8, 0.3, 0.9]], requires_grad=True)
        target = mn.Tensor([[1.0, 0.0, 1.0]])

        loss = criterion(pred, target)

        # BCE = -[target*log(pred) + (1-target)*log(1-pred)]
        # Should be positive
        assert loss.item() > 0

    def test_bce_backward(self):
        """Test BCE backward pass."""
        criterion = BCELoss()

        pred = mn.Tensor([[0.8]], requires_grad=True)
        target = mn.Tensor([[1.0]])

        loss = criterion(pred, target)
        loss.backward()

        # Gradient should push prediction toward target
        assert pred.grad is not None
        # For target=1 and pred=0.8, gradient should be negative (increase pred)
        assert pred.grad[0, 0] < 0

    def test_bce_edge_cases(self):
        """Test BCE with edge cases."""
        criterion = BCELoss()

        # Perfect prediction
        pred_perfect = mn.Tensor([[0.999, 0.001]], requires_grad=True)
        target = mn.Tensor([[1.0, 0.0]])
        loss_perfect = criterion(pred_perfect, target)

        # Bad prediction  
        pred_bad = mn.Tensor([[0.001, 0.999]], requires_grad=True)
        target_bad = mn.Tensor([[1.0, 0.0]])
        loss_bad = criterion(pred_bad, target_bad)

        # Bad prediction should have higher loss
        assert loss_bad.item() > loss_perfect.item()

class TestLossReductionModes:
    """Test different reduction modes across loss functions."""

    def test_reduction_consistency(self):
        """Test that reduction modes work consistently."""
        pred = mn.Tensor([[1, 2], [3, 4]], requires_grad=True)
        target = mn.Tensor([[1, 1], [1, 1]])

        # Test MSE with different reductions
        mse_mean = MSELoss(reduction='mean')(pred, target)
        mse_sum = MSELoss(reduction='sum')(pred, target)
        mse_none = MSELoss(reduction='none')(pred, target)

        # Relationships should hold
        expected_mean = mse_sum.item() / pred.data.size
        assert abs(mse_mean.item() - expected_mean) < 1e-6

        expected_sum = np.sum(mse_none.data)
        assert abs(mse_sum.item() - expected_sum) < 1e-6

class TestLossNumericalStability:
    """Test numerical stability of loss functions."""

    def test_crossentropy_stability(self):
        """Test Cross-Entropy numerical stability."""
        criterion = CrossEntropyLoss()

        # Very large logits
        pred_large = mn.Tensor([[100.0, 50.0]], requires_grad=True)
        target = mn.Tensor([0])

        loss_large = criterion(pred_large, target)

        # Should not overflow
        assert not np.isnan(loss_large.item())
        assert not np.isinf(loss_large.item())

        # Very small logits
        pred_small = mn.Tensor([[-100.0, -50.0]], requires_grad=True)
        target_small = mn.Tensor([0])

        loss_small = criterion(pred_small, target_small)

        # Should not underflow to NaN
        assert not np.isnan(loss_small.item())

    def test_bce_stability(self):
        """Test BCE numerical stability."""
        criterion = BCELoss()

        # Values close to 0 and 1
        pred_edge = mn.Tensor([[0.0001, 0.9999]], requires_grad=True)
        target = mn.Tensor([[0.0, 1.0]])

        loss_edge = criterion(pred_edge, target)

        # Should not produce NaN or inf
        assert not np.isnan(loss_edge.item())
        assert not np.isinf(loss_edge.item())

class TestLossGradientProperties:
    """Test gradient properties of loss functions."""

    def test_mse_gradient_symmetry(self):
        """Test MSE gradient symmetry."""
        criterion = MSELoss()

        # Positive error
        pred_pos = mn.Tensor([[2.0]], requires_grad=True)
        target = mn.Tensor([[1.0]])
        loss_pos = criterion(pred_pos, target)
        loss_pos.backward()
        grad_pos = pred_pos.grad.copy()

        # Negative error
        pred_neg = mn.Tensor([[0.0]], requires_grad=True)
        loss_neg = criterion(pred_neg, target)
        loss_neg.backward()
        grad_neg = pred_neg.grad.copy()

        # Gradients should have opposite signs but same magnitude
        assert abs(grad_pos[0, 0] + grad_neg[0, 0]) < 1e-6

    def test_crossentropy_gradient_sum(self):
        """Test Cross-Entropy gradient properties."""
        criterion = CrossEntropyLoss()

        pred = mn.Tensor([[1.0, 2.0, 3.0]], requires_grad=True)
        target = mn.Tensor([1])

        loss = criterion(pred, target)
        loss.backward()

        # For single sample, gradients should sum to 0 (softmax property)
        grad_sum = np.sum(pred.grad)
        assert abs(grad_sum) < 1e-6

class TestLossWithModels:
    """Test loss functions integrated with models."""

    def test_loss_with_linear_model(self):
        """Test loss function with a simple linear model."""
        model = Sequential(
            Linear(2, 1)
        )

        criterion = MSELoss()

        x = mn.Tensor([[1, 2]], requires_grad=True)
        target = mn.Tensor([[1.0]])

        output = model(x)
        loss = criterion(output, target)

        loss.backward()

        # All parameters should have gradients
        for param in model.parameters():
            assert param.grad is not None

    def test_loss_with_classification_model(self):
        """Test Cross-Entropy with classification model."""
        model = Sequential(
            Linear(3, 2),
            Softmax(dim=1)
        )

        criterion = CrossEntropyLoss()

        x = mn.Tensor([[1, 2, 3]], requires_grad=True)
        target = mn.Tensor([0])

        output = model(x)
        loss = criterion(output, target)

        loss.backward()

        # Check that gradients flow back to input
        assert x.grad is not None

        # Check that all model parameters have gradients
        for param in model.parameters():
            assert param.grad is not None

