"""
Tests for the core Tensor class and automatic differentiation.
"""
import pytest
import numpy as np
import mayini as mn
from conftest import assert_tensors_close, assert_gradient_close, numerical_gradient

class TestTensorBasics:
    """Test basic tensor operations and properties."""

    def test_tensor_creation(self):
        """Test tensor creation with various input types."""
        # Test with list
        t1 = mn.Tensor([1, 2, 3])
        assert t1.shape == (3,)
        assert t1.dtype == np.float32

        # Test with numpy array
        arr = np.array([[1, 2], [3, 4]], dtype=np.float64)
        t2 = mn.Tensor(arr, dtype=np.float32)
        assert t2.shape == (2, 2)
        assert t2.dtype == np.float32

        # Test with scalar
        t3 = mn.Tensor(5.0)
        assert t3.shape == ()
        assert t3.item() == 5.0

    def test_tensor_properties(self):
        """Test tensor properties."""
        t = mn.Tensor([[1, 2, 3], [4, 5, 6]])
        assert t.shape == (2, 3)
        assert t.ndim == 2
        assert t.size == 6

    def test_tensor_requires_grad(self):
        """Test gradient requirements."""
        t1 = mn.Tensor([1, 2, 3], requires_grad=True)
        t2 = mn.Tensor([1, 2, 3], requires_grad=False)

        assert t1.requires_grad == True
        assert t2.requires_grad == False
        assert t1.grad is None
        assert t2.grad is None

class TestTensorArithmetic:
    """Test tensor arithmetic operations."""

    def test_addition(self, sample_tensor_2d):
        """Test tensor addition."""
        t1 = sample_tensor_2d
        t2 = mn.Tensor([[2, 1], [1, 2]], requires_grad=True)

        result = t1 + t2
        expected = np.array([[3, 3], [4, 6]])
        assert_tensors_close(result, expected)

        # Test gradient
        loss = result.sum()
        loss.backward()

        assert_gradient_close(t1, np.ones((2, 2)))
        assert_gradient_close(t2, np.ones((2, 2)))

    def test_multiplication(self, sample_tensor_2d):
        """Test tensor multiplication."""
        t1 = sample_tensor_2d
        t2 = mn.Tensor([[2, 3], [1, 2]], requires_grad=True)

        result = t1 * t2
        expected = np.array([[2, 6], [3, 8]])
        assert_tensors_close(result, expected)

        # Test gradient
        loss = result.sum()
        loss.backward()

        assert_gradient_close(t1, t2.data)
        assert_gradient_close(t2, t1.data)

    def test_scalar_operations(self, sample_tensor_2d):
        """Test operations with scalars."""
        t = sample_tensor_2d

        # Addition with scalar
        result1 = t + 5
        expected1 = t.data + 5
        assert_tensors_close(result1, expected1)

        # Multiplication with scalar
        result2 = t * 3
        expected2 = t.data * 3
        assert_tensors_close(result2, expected2)

    def test_subtraction_and_division(self, sample_tensor_2d):
        """Test subtraction and division operations."""
        t1 = sample_tensor_2d
        t2 = mn.Tensor([[1, 1], [2, 2]], requires_grad=True)

        # Subtraction
        result_sub = t1 - t2
        expected_sub = t1.data - t2.data
        assert_tensors_close(result_sub, expected_sub)

        # Division
        result_div = t1 / 2
        expected_div = t1.data / 2
        assert_tensors_close(result_div, expected_div)

class TestTensorReductions:
    """Test tensor reduction operations."""

    def test_sum(self, sample_tensor_2d):
        """Test sum operation."""
        t = sample_tensor_2d

        # Sum all elements
        result_all = t.sum()
        expected_all = np.sum(t.data)
        assert_tensors_close(result_all, expected_all)

        # Sum along axis
        result_axis0 = t.sum(axis=0)
        expected_axis0 = np.sum(t.data, axis=0)
        assert_tensors_close(result_axis0, expected_axis0)

        result_axis1 = t.sum(axis=1)
        expected_axis1 = np.sum(t.data, axis=1)
        assert_tensors_close(result_axis1, expected_axis1)

    def test_mean(self, sample_tensor_2d):
        """Test mean operation."""
        t = sample_tensor_2d

        # Mean all elements
        result_all = t.mean()
        expected_all = np.mean(t.data)
        assert_tensors_close(result_all, expected_all)

        # Mean along axis
        result_axis0 = t.mean(axis=0)
        expected_axis0 = np.mean(t.data, axis=0)
        assert_tensors_close(result_axis0, expected_axis0)

class TestTensorOperations:
    """Test other tensor operations."""

    def test_matmul(self):
        """Test matrix multiplication."""
        t1 = mn.Tensor([[1, 2], [3, 4]], requires_grad=True)
        t2 = mn.Tensor([[5, 6], [7, 8]], requires_grad=True)

        result = t1.matmul(t2)
        expected = np.dot(t1.data, t2.data)
        assert_tensors_close(result, expected)

        # Test gradient
        loss = result.sum()
        loss.backward()

        expected_grad_t1 = np.dot(np.ones_like(result.data), t2.data.T)
        expected_grad_t2 = np.dot(t1.data.T, np.ones_like(result.data))

        assert_gradient_close(t1, expected_grad_t1)
        assert_gradient_close(t2, expected_grad_t2)

    def test_power(self, sample_tensor_2d):
        """Test power operation."""
        t = sample_tensor_2d

        result = t ** 2
        expected = t.data ** 2
        assert_tensors_close(result, expected)

        # Test gradient
        loss = result.sum()
        loss.backward()

        expected_grad = 2 * t.data
        assert_gradient_close(t, expected_grad)

    def test_reshape(self, sample_tensor_2d):
        """Test reshape operation."""
        t = sample_tensor_2d

        result = t.reshape((4, 1))
        assert result.shape == (4, 1)
        assert_tensors_close(result, t.data.reshape((4, 1)))

        # Test gradient
        loss = result.sum()
        loss.backward()

        assert_gradient_close(t, np.ones_like(t.data))

    def test_transpose(self, sample_tensor_2d):
        """Test transpose operation."""
        t = sample_tensor_2d

        result = t.transpose()
        expected = np.transpose(t.data)
        assert_tensors_close(result, expected)

        # Test gradient
        loss = result.sum()
        loss.backward()

        assert_gradient_close(t, np.ones_like(t.data))

class TestAutoDiff:
    """Test automatic differentiation."""

    def test_simple_chain_rule(self):
        """Test chain rule with simple operations."""
        x = mn.Tensor([2.0], requires_grad=True)

        # f(x) = x^2 + 3x + 1
        y = x ** 2 + 3 * x + 1
        y.backward()

        # df/dx = 2x + 3 = 2*2 + 3 = 7
        expected_grad = 7.0
        assert_gradient_close(x, np.array([expected_grad]))

    def test_complex_chain_rule(self):
        """Test chain rule with more complex operations."""
        x = mn.Tensor([[1.0, 2.0]], requires_grad=True)
        w = mn.Tensor([[1.0], [2.0]], requires_grad=True)

        # Forward pass
        z = x.matmul(w)  # [1*1 + 2*2] = [5]
        y = z ** 2       # [25]

        y.backward()

        # dy/dx = dy/dz * dz/dx = 2*z * w^T = 2*5 * [1, 2] = [10, 20]
        expected_grad_x = np.array([[10.0, 20.0]])
        assert_gradient_close(x, expected_grad_x)

        # dy/dw = dy/dz * dz/dw = 2*z * x^T = 2*5 * [[1], [2]] = [[10], [20]]  
        expected_grad_w = np.array([[10.0], [20.0]])
        assert_gradient_close(w, expected_grad_w)

class TestNumericalGradient:
    """Test automatic differentiation against numerical gradients."""

    def test_numerical_vs_auto_diff(self):
        """Compare automatic differentiation with numerical gradients."""
        x = mn.Tensor([1.0, 2.0], requires_grad=True)

        def func(tensor):
            return (tensor ** 2).sum()

        # Compute automatic gradient
        y = func(x)
        x.zero_grad()
        y.backward()
        auto_grad = x.grad.copy()

        # Compute numerical gradient
        x.zero_grad()
        num_grad = numerical_gradient(func, x)

        # Compare
        np.testing.assert_allclose(auto_grad, num_grad, rtol=1e-5, atol=1e-6)

class TestTensorUtilities:
    """Test tensor utility methods."""

    def test_detach(self, sample_tensor_2d):
        """Test tensor detachment from computational graph."""
        t = sample_tensor_2d
        detached = t.detach()

        assert detached.requires_grad == False
        assert_tensors_close(detached, t.data)

    def test_zero_grad(self, sample_tensor_2d):
        """Test gradient zeroing."""
        t = sample_tensor_2d
        loss = t.sum()
        loss.backward()

        assert t.grad is not None

        t.zero_grad()
        assert t.grad is None

    def test_numpy_conversion(self, sample_tensor_2d):
        """Test conversion to numpy."""
        t = sample_tensor_2d
        np_array = t.numpy()

        assert isinstance(np_array, np.ndarray)
        assert_tensors_close(np_array, t.data)

    def test_item(self, sample_tensor_scalar):
        """Test scalar value extraction."""
        t = sample_tensor_scalar
        value = t.item()

        assert isinstance(value, float)
        assert value == 5.0

class TestBroadcasting:
    """Test broadcasting operations."""

    def test_broadcasting_addition(self):
        """Test addition with broadcasting."""
        t1 = mn.Tensor([[1, 2, 3]], requires_grad=True)  # Shape: (1, 3)
        t2 = mn.Tensor([[1], [2]], requires_grad=True)   # Shape: (2, 1)

        result = t1 + t2  # Should broadcast to (2, 3)
        expected = np.array([[2, 3, 4], [3, 4, 5]])

        assert result.shape == (2, 3)
        assert_tensors_close(result, expected)

        # Test gradients with broadcasting
        loss = result.sum()
        loss.backward()

        # t1 gradient should be summed over the broadcasted dimension
        expected_grad_t1 = np.array([[2, 2, 2]])  # Sum over the first dimension
        assert_gradient_close(t1, expected_grad_t1)

        # t2 gradient should be summed over the broadcasted dimension  
        expected_grad_t2 = np.array([[3], [3]])  # Sum over the last dimension
        assert_gradient_close(t2, expected_grad_t2)

