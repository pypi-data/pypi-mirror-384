"""
Tests for neural network modules and layers.
"""
import pytest
import numpy as np
import mayini as mn
from mayini.nn import *
from conftest import assert_tensors_close, assert_gradient_close

class TestLinearLayer:
    """Test Linear (Dense) layer functionality."""

    def test_linear_creation(self):
        """Test Linear layer creation."""
        layer = Linear(10, 5)

        assert layer.in_features == 10
        assert layer.out_features == 5
        assert layer.weight.shape == (10, 5)
        assert layer.bias.shape == (5,)
        assert layer.weight.requires_grad == True
        assert layer.bias.requires_grad == True

    def test_linear_forward(self):
        """Test Linear layer forward pass."""
        layer = Linear(3, 2)

        # Set known weights for testing
        layer.weight.data = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.float32)
        layer.bias.data = np.array([0.1, 0.2], dtype=np.float32)

        x = mn.Tensor([[1, 2, 3]], requires_grad=True)
        output = layer(x)

        # Expected: [1*1 + 2*0 + 3*1, 1*0 + 2*1 + 3*1] + [0.1, 0.2] = [4.1, 5.2]
        expected = np.array([[4.1, 5.2]])
        assert_tensors_close(output, expected)

    def test_linear_backward(self):
        """Test Linear layer backward pass."""
        layer = Linear(2, 1)
        layer.weight.data = np.array([[1], [2]], dtype=np.float32)
        layer.bias.data = np.array([0], dtype=np.float32)

        x = mn.Tensor([[1, 2]], requires_grad=True)
        output = layer(x)
        loss = output.sum()

        loss.backward()

        # Check gradients
        assert x.grad is not None
        assert layer.weight.grad is not None
        assert layer.bias.grad is not None

    def test_linear_initialization_methods(self):
        """Test different initialization methods."""
        # Xavier initialization
        layer_xavier = Linear(100, 50, init_method='xavier')
        weight_std = np.std(layer_xavier.weight.data)
        expected_std = np.sqrt(2.0 / (100 + 50))
        assert abs(weight_std - expected_std) < 0.1

        # He initialization
        layer_he = Linear(100, 50, init_method='he')
        weight_std_he = np.std(layer_he.weight.data)
        expected_std_he = np.sqrt(2.0 / 100)
        assert abs(weight_std_he - expected_std_he) < 0.1

class TestConv2D:
    """Test 2D Convolutional layer."""

    def test_conv2d_creation(self):
        """Test Conv2D layer creation."""
        layer = Conv2D(3, 16, kernel_size=3, padding=1, stride=1)

        assert layer.in_channels == 3
        assert layer.out_channels == 16
        assert layer.kernel_size == 3
        assert layer.padding == 1
        assert layer.stride == 1
        assert layer.weight.shape == (16, 3, 3, 3)
        assert layer.bias.shape == (16,)

    def test_conv2d_forward_simple(self):
        """Test Conv2D forward pass with simple case."""
        layer = Conv2D(1, 1, kernel_size=3, padding=0, stride=1)

        # Set known kernel for testing
        layer.weight.data = np.ones((1, 1, 3, 3), dtype=np.float32)
        layer.bias.data = np.array([0], dtype=np.float32)

        # Input: 1x1x5x5 (batch, channel, height, width)
        x = mn.Tensor(np.ones((1, 1, 5, 5)), requires_grad=True)
        output = layer(x)

        # With 3x3 kernel on 5x5 input, output should be 3x3
        assert output.shape == (1, 1, 3, 3)
        # All values should be 9 (sum of 3x3 ones)
        expected = np.full((1, 1, 3, 3), 9.0)
        assert_tensors_close(output, expected)

class TestPoolingLayers:
    """Test pooling layers."""

    def test_maxpool2d(self):
        """Test MaxPool2D layer."""
        layer = MaxPool2D(kernel_size=2, stride=2)

        # Create input with known values
        x_data = np.array([[[[1, 2, 3, 4],
                            [5, 6, 7, 8],
                            [9, 10, 11, 12],
                            [13, 14, 15, 16]]]], dtype=np.float32)
        x = mn.Tensor(x_data, requires_grad=True)

        output = layer(x)

        # Expected max pooling result
        expected = np.array([[[[6, 8],
                              [14, 16]]]], dtype=np.float32)

        assert output.shape == (1, 1, 2, 2)
        assert_tensors_close(output, expected)

    def test_avgpool2d(self):
        """Test AvgPool2D layer."""
        layer = AvgPool2D(kernel_size=2, stride=2)

        # Create input with known values
        x_data = np.array([[[[1, 2, 3, 4],
                            [5, 6, 7, 8],
                            [9, 10, 11, 12],
                            [13, 14, 15, 16]]]], dtype=np.float32)
        x = mn.Tensor(x_data, requires_grad=True)

        output = layer(x)

        # Expected average pooling result
        expected = np.array([[[[3.5, 5.5],
                              [11.5, 13.5]]]], dtype=np.float32)

        assert output.shape == (1, 1, 2, 2)
        assert_tensors_close(output, expected)

class TestNormalizationLayers:
    """Test normalization layers."""

    def test_batchnorm1d(self):
        """Test BatchNorm1d layer."""
        layer = BatchNorm1d(3)

        # Create batch of data
        x = mn.Tensor([[1, 2, 3],
                      [4, 5, 6],
                      [7, 8, 9]], requires_grad=True)

        output = layer(x)

        # Check that output has mean ~0 and std ~1 along batch dimension
        output_mean = np.mean(output.data, axis=0)
        output_std = np.std(output.data, axis=0)

        np.testing.assert_allclose(output_mean, 0, atol=1e-6)
        np.testing.assert_allclose(output_std, 1, atol=1e-6)

class TestRegularizationLayers:
    """Test regularization layers."""

    def test_dropout_training_mode(self):
        """Test Dropout layer in training mode."""
        layer = Dropout(p=0.5)
        layer.training = True

        x = mn.Tensor(np.ones((10, 10)), requires_grad=True)
        output = layer(x)

        # In training mode, some values should be zeroed out
        # and others should be scaled by 1/(1-p) = 2
        unique_values = np.unique(output.data)
        assert 0.0 in unique_values  # Some values are zeroed
        assert len(unique_values) <= 2  # Should only have 0 and scaled values

    def test_dropout_eval_mode(self):
        """Test Dropout layer in evaluation mode."""
        layer = Dropout(p=0.5)
        layer.training = False

        x = mn.Tensor(np.ones((10, 10)), requires_grad=True)
        output = layer(x)

        # In eval mode, should pass through unchanged
        assert_tensors_close(output, x.data)

class TestSequential:
    """Test Sequential container."""

    def test_sequential_creation(self):
        """Test Sequential model creation."""
        model = Sequential(
            Linear(10, 5),
            ReLU(),
            Linear(5, 2),
            Softmax(dim=1)
        )

        assert len(model.layers) == 4
        assert isinstance(model.layers[0], Linear)
        assert isinstance(model.layers[1], ReLU)
        assert isinstance(model.layers[2], Linear)
        assert isinstance(model.layers[3], Softmax)

    def test_sequential_forward(self):
        """Test Sequential model forward pass."""
        model = Sequential(
            Linear(3, 2),
            ReLU()
        )

        # Set known weights
        model.layers[0].weight.data = np.array([[1, -1], [0, 1], [-1, 0]], dtype=np.float32)
        model.layers[0].bias.data = np.array([0, 0], dtype=np.float32)

        x = mn.Tensor([[1, 2, 3]], requires_grad=True)
        output = model(x)

        # Linear: [1*1 + 2*0 + 3*(-1), 1*(-1) + 2*1 + 3*0] = [-2, 1]
        # ReLU: [0, 1]
        expected = np.array([[0, 1]])
        assert_tensors_close(output, expected)

    def test_sequential_parameters(self):
        """Test Sequential model parameter collection."""
        model = Sequential(
            Linear(3, 2),
            ReLU(),
            Linear(2, 1)
        )

        params = list(model.parameters())

        # Should have 4 parameters: 2 weights + 2 biases
        assert len(params) == 4

        # Check shapes
        assert params[0].shape == (3, 2)  # First layer weight
        assert params[1].shape == (2,)    # First layer bias
        assert params[2].shape == (2, 1)  # Second layer weight
        assert params[3].shape == (1,)    # Second layer bias

class TestFlattenLayer:
    """Test Flatten layer."""

    def test_flatten(self):
        """Test Flatten layer functionality."""
        layer = Flatten()

        # Input shape: (batch_size, channels, height, width)
        x = mn.Tensor(np.random.randn(2, 3, 4, 5), requires_grad=True)
        output = layer(x)

        # Output should be (batch_size, channels * height * width)
        expected_shape = (2, 3 * 4 * 5)
        assert output.shape == expected_shape

        # Check that backward pass works
        loss = output.sum()
        loss.backward()
        assert x.grad is not None
        assert x.grad.shape == x.shape

class TestModuleBase:
    """Test base Module functionality."""

    def test_module_training_mode(self):
        """Test training mode setting."""
        model = Sequential(
            Linear(3, 2),
            Dropout(0.5),
            Linear(2, 1)
        )

        # Initially in training mode
        assert model.training == True
        assert model.layers[1].training == True

        # Switch to eval mode
        model.eval()
        assert model.training == False
        assert model.layers[1].training == False

        # Switch back to training mode
        model.train()
        assert model.training == True
        assert model.layers[1].training == True

    def test_module_zero_grad(self):
        """Test gradient zeroing."""
        model = Sequential(
            Linear(3, 2),
            Linear(2, 1)
        )

        x = mn.Tensor([[1, 2, 3]], requires_grad=True)
        output = model(x)
        loss = output.sum()
        loss.backward()

        # Check that gradients exist
        for param in model.parameters():
            assert param.grad is not None

        # Zero gradients
        model.zero_grad()

        # Check that gradients are zeroed
        for param in model.parameters():
            assert param.grad is None

class TestModelComplexity:
    """Test more complex model architectures."""

    def test_cnn_architecture(self):
        """Test CNN architecture."""
        model = Sequential(
            Conv2D(1, 8, kernel_size=3, padding=1),
            ReLU(),
            MaxPool2D(kernel_size=2),
            Conv2D(8, 16, kernel_size=3, padding=1),
            ReLU(),
            MaxPool2D(kernel_size=2),
            Flatten(),
            Linear(16 * 7 * 7, 10)
        )

        # Test with MNIST-like input
        x = mn.Tensor(np.random.randn(1, 1, 28, 28), requires_grad=True)
        output = model(x)

        assert output.shape == (1, 10)

        # Test backward pass
        loss = output.sum()
        loss.backward()
        assert x.grad is not None

    def test_mlp_architecture(self):
        """Test multi-layer perceptron."""
        model = Sequential(
            Linear(784, 256),
            ReLU(),
            Dropout(0.5),
            Linear(256, 128),
            ReLU(),
            Dropout(0.5),
            Linear(128, 10),
            Softmax(dim=1)
        )

        # Test with flattened MNIST-like input
        x = mn.Tensor(np.random.randn(32, 784), requires_grad=True)
        output = model(x)

        assert output.shape == (32, 10)

        # Check that probabilities sum to 1 (softmax)
        probs_sum = np.sum(output.data, axis=1)
        np.testing.assert_allclose(probs_sum, 1.0, rtol=1e-5)

