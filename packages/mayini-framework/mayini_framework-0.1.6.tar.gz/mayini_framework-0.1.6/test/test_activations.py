"""
Tests for activation functions.
"""
import pytest
import numpy as np
import mayini as mn
from mayini.nn import *
from mayini.nn.activations import *
from conftest import assert_tensors_close, assert_gradient_close

class TestReLU:
    """Test ReLU activation function."""

    def test_relu_forward(self):
        """Test ReLU forward pass."""
        layer = ReLU()

        x = mn.Tensor([[-1, 0, 1, 2, -3]], requires_grad=True)
        output = layer(x)

        expected = np.array([[0, 0, 1, 2, 0]])
        assert_tensors_close(output, expected)

    def test_relu_backward(self):
        """Test ReLU backward pass."""
        layer = ReLU()

        x = mn.Tensor([[-1, 0, 1, 2, -3]], requires_grad=True)
        output = layer(x)
        loss = output.sum()

        loss.backward()

        # Gradient should be 1 for positive inputs, 0 for negative
        expected_grad = np.array([[0, 0, 1, 1, 0]])
        assert_gradient_close(x, expected_grad)

    def test_relu_functional(self):
        """Test functional ReLU interface."""
        x = mn.Tensor([[-1, 0, 1, 2, -3]], requires_grad=True)
        output = relu(x)

        expected = np.array([[0, 0, 1, 2, 0]])
        assert_tensors_close(output, expected)

class TestLeakyReLU:
    """Test Leaky ReLU activation function."""

    def test_leaky_relu_forward(self):
        """Test Leaky ReLU forward pass."""
        layer = LeakyReLU(negative_slope=0.1)

        x = mn.Tensor([[-1, 0, 1, 2, -3]], requires_grad=True)
        output = layer(x)

        expected = np.array([[-0.1, 0, 1, 2, -0.3]])
        assert_tensors_close(output, expected)

    def test_leaky_relu_backward(self):
        """Test Leaky ReLU backward pass."""
        layer = LeakyReLU(negative_slope=0.2)

        x = mn.Tensor([[-1, 0, 1, 2, -3]], requires_grad=True)
        output = layer(x)
        loss = output.sum()

        loss.backward()

        # Gradient should be 1 for positive inputs, negative_slope for negative
        expected_grad = np.array([[0.2, 0.2, 1, 1, 0.2]])
        assert_gradient_close(x, expected_grad)

class TestSigmoid:
    """Test Sigmoid activation function."""

    def test_sigmoid_forward(self):
        """Test Sigmoid forward pass."""
        layer = Sigmoid()

        x = mn.Tensor([[0, 1, -1]], requires_grad=True)
        output = layer(x)

        # sigmoid(0) = 0.5, sigmoid(1) ≈ 0.731, sigmoid(-1) ≈ 0.269
        expected = 1 / (1 + np.exp(-x.data))
        assert_tensors_close(output, expected)

    def test_sigmoid_backward(self):
        """Test Sigmoid backward pass."""
        layer = Sigmoid()

        x = mn.Tensor([[0]], requires_grad=True)
        output = layer(x)
        loss = output.sum()

        loss.backward()

        # Gradient of sigmoid at x=0 is sigmoid(0) * (1 - sigmoid(0)) = 0.5 * 0.5 = 0.25
        expected_grad = np.array([[0.25]])
        assert_gradient_close(x, expected_grad)

    def test_sigmoid_functional(self):
        """Test functional Sigmoid interface."""
        x = mn.Tensor([[0, 1, -1]], requires_grad=True)
        output = sigmoid(x)

        expected = 1 / (1 + np.exp(-x.data))
        assert_tensors_close(output, expected)

class TestTanh:
    """Test Tanh activation function."""

    def test_tanh_forward(self):
        """Test Tanh forward pass."""
        layer = Tanh()

        x = mn.Tensor([[0, 1, -1]], requires_grad=True)
        output = layer(x)

        expected = np.tanh(x.data)
        assert_tensors_close(output, expected)

    def test_tanh_backward(self):
        """Test Tanh backward pass."""
        layer = Tanh()

        x = mn.Tensor([[0]], requires_grad=True)
        output = layer(x)
        loss = output.sum()

        loss.backward()

        # Gradient of tanh at x=0 is 1 - tanh²(0) = 1 - 0² = 1
        expected_grad = np.array([[1.0]])
        assert_gradient_close(x, expected_grad)

    def test_tanh_functional(self):
        """Test functional Tanh interface."""
        x = mn.Tensor([[0, 1, -1]], requires_grad=True)
        output = tanh(x)

        expected = np.tanh(x.data)
        assert_tensors_close(output, expected)

class TestSoftmax:
    """Test Softmax activation function."""

    def test_softmax_forward(self):
        """Test Softmax forward pass."""
        layer = Softmax(dim=1)

        x = mn.Tensor([[1, 2, 3]], requires_grad=True)
        output = layer(x)

        # Softmax should sum to 1
        assert abs(output.data.sum() - 1.0) < 1e-6

        # Check values are between 0 and 1
        assert np.all(output.data >= 0)
        assert np.all(output.data <= 1)

        # Largest input should have largest output
        assert np.argmax(output.data) == np.argmax(x.data)

    def test_softmax_backward(self):
        """Test Softmax backward pass."""
        layer = Softmax(dim=1)

        x = mn.Tensor([[1, 2, 3]], requires_grad=True)
        output = layer(x)
        loss = output.sum()

        loss.backward()

        # Gradient should sum to 0 for each sample
        grad_sum = np.sum(x.grad, axis=1)
        np.testing.assert_allclose(grad_sum, 0, atol=1e-6)

    def test_softmax_batch(self):
        """Test Softmax with batch input."""
        layer = Softmax(dim=1)

        x = mn.Tensor([[1, 2, 3], [4, 5, 6]], requires_grad=True)
        output = layer(x)

        # Each row should sum to 1
        row_sums = np.sum(output.data, axis=1)
        np.testing.assert_allclose(row_sums, 1.0)

    def test_softmax_functional(self):
        """Test functional Softmax interface."""
        x = mn.Tensor([[1, 2, 3]], requires_grad=True)
        output = softmax(x, dim=1)

        assert abs(output.data.sum() - 1.0) < 1e-6

class TestGELU:
    """Test GELU activation function."""

    def test_gelu_forward(self):
        """Test GELU forward pass."""
        layer = GELU()

        x = mn.Tensor([[0, 1, -1]], requires_grad=True)
        output = layer(x)

        # GELU(0) should be 0
        assert abs(output.data[0, 0]) < 1e-6

        # GELU should be smooth and monotonic
        assert output.data[0, 1] > output.data[0, 0]  # GELU(1) > GELU(0)
        assert output.data[0, 0] > output.data[0, 2]  # GELU(0) > GELU(-1)

    def test_gelu_functional(self):
        """Test functional GELU interface."""
        x = mn.Tensor([[0, 1, -1]], requires_grad=True)
        output = gelu(x)

        # Should match module version
        layer = GELU()
        expected = layer(x)
        assert_tensors_close(output, expected)

class TestActivationProperties:
    """Test general properties of activation functions."""

    def test_activation_ranges(self):
        """Test that activation functions stay in expected ranges."""
        x = mn.Tensor(np.linspace(-10, 10, 100).reshape(1, -1), requires_grad=True)

        # ReLU should be non-negative
        relu_out = ReLU()(x)
        assert np.all(relu_out.data >= 0)

        # Sigmoid should be between 0 and 1
        sigmoid_out = Sigmoid()(x)
        assert np.all(sigmoid_out.data >= 0)
        assert np.all(sigmoid_out.data <= 1)

        # Tanh should be between -1 and 1
        tanh_out = Tanh()(x)
        assert np.all(tanh_out.data >= -1)
        assert np.all(tanh_out.data <= 1)

        # Softmax should sum to 1
        softmax_out = Softmax(dim=1)(x)
        assert abs(softmax_out.data.sum() - 1.0) < 1e-6

    def test_activation_monotonicity(self):
        """Test monotonicity properties."""
        x_sorted = mn.Tensor([[-2, -1, 0, 1, 2]], requires_grad=True)

        # ReLU should be monotonically non-decreasing
        relu_out = ReLU()(x_sorted)
        for i in range(1, relu_out.data.shape[1]):
            assert relu_out.data[0, i] >= relu_out.data[0, i-1]

        # Sigmoid should be monotonically increasing
        sigmoid_out = Sigmoid()(x_sorted)
        for i in range(1, sigmoid_out.data.shape[1]):
            assert sigmoid_out.data[0, i] > sigmoid_out.data[0, i-1]

        # Tanh should be monotonically increasing
        tanh_out = Tanh()(x_sorted)
        for i in range(1, tanh_out.data.shape[1]):
            assert tanh_out.data[0, i] > tanh_out.data[0, i-1]

class TestActivationGradients:
    """Test gradient computation for activation functions."""

    def test_activation_gradients_exist(self):
        """Test that all activations compute gradients properly."""
        x = mn.Tensor([[1.0, -1.0, 0.5]], requires_grad=True)

        activations = [ReLU(), LeakyReLU(), Sigmoid(), Tanh(), GELU()]

        for activation in activations:
            x.zero_grad()
            output = activation(x)
            loss = output.sum()
            loss.backward()

            assert x.grad is not None, f"{activation.__class__.__name__} didn't compute gradients"
            assert x.grad.shape == x.shape

    def test_softmax_gradient(self):
        """Test Softmax gradient specifically."""
        x = mn.Tensor([[1.0, 2.0, 3.0]], requires_grad=True)

        softmax_layer = Softmax(dim=1)
        output = softmax_layer(x)

        # Test gradient of one output
        output[0, 0].backward()

        assert x.grad is not None
        # Softmax gradient has specific properties we can check
        assert x.grad.sum() == 0  # Jacobian rows sum to 0

class TestActivationNumericalStability:
    """Test numerical stability of activation functions."""

    def test_large_inputs(self):
        """Test activations with very large inputs."""
        x_large = mn.Tensor([[100, -100]], requires_grad=True)

        # Sigmoid should not overflow
        sigmoid_out = Sigmoid()(x_large)
        assert not np.any(np.isnan(sigmoid_out.data))
        assert not np.any(np.isinf(sigmoid_out.data))

        # Tanh should not overflow
        tanh_out = Tanh()(x_large)
        assert not np.any(np.isnan(tanh_out.data))
        assert not np.any(np.isinf(tanh_out.data))

        # Softmax should not overflow
        softmax_out = Softmax(dim=1)(x_large)
        assert not np.any(np.isnan(softmax_out.data))
        assert not np.any(np.isinf(softmax_out.data))

    def test_zero_gradients(self):
        """Test behavior at points where gradients might be zero."""
        # Test ReLU at zero
        x_zero = mn.Tensor([[0.0]], requires_grad=True)
        relu_out = ReLU()(x_zero)
        relu_out.backward()

        # Gradient at zero for ReLU is conventionally 0
        assert x_zero.grad[0, 0] == 0.0

