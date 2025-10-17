"""
Tests for RNN components (RNN, LSTM, GRU).
"""
import pytest
import numpy as np
import mayini as mn
from mayini.nn import *
from conftest import assert_tensors_close

class TestRNNCell:
    """Test basic RNN cell functionality."""

    def test_rnn_cell_creation(self):
        """Test RNN cell creation."""
        cell = RNNCell(input_size=10, hidden_size=20)

        assert cell.input_size == 10
        assert cell.hidden_size == 20
        assert cell.weight_ih.shape == (10, 20)
        assert cell.weight_hh.shape == (20, 20)
        assert cell.bias.shape == (20,)

    def test_rnn_cell_forward(self):
        """Test RNN cell forward pass."""
        cell = RNNCell(input_size=3, hidden_size=4)

        # Set known weights for reproducible testing
        cell.weight_ih.data = np.ones((3, 4)) * 0.1
        cell.weight_hh.data = np.ones((4, 4)) * 0.1  
        cell.bias.data = np.zeros(4)

        x = mn.Tensor([[1, 2, 3]], requires_grad=True)  # batch_size=1
        h_prev = mn.Tensor([[0, 0, 0, 0]], requires_grad=True)

        h_next = cell(x, h_prev)

        assert h_next.shape == (1, 4)
        # Output should be result of tanh(x @ W_ih + h @ W_hh + bias)

    def test_rnn_cell_backward(self):
        """Test RNN cell backward pass."""
        cell = RNNCell(input_size=2, hidden_size=3)

        x = mn.Tensor([[1, 2]], requires_grad=True)
        h_prev = mn.Tensor([[0, 0, 0]], requires_grad=True)

        h_next = cell(x, h_prev)
        loss = h_next.sum()

        loss.backward()

        # Check gradients exist
        assert x.grad is not None
        assert h_prev.grad is not None
        assert cell.weight_ih.grad is not None
        assert cell.weight_hh.grad is not None
        assert cell.bias.grad is not None

class TestLSTMCell:
    """Test LSTM cell functionality."""

    def test_lstm_cell_creation(self):
        """Test LSTM cell creation."""
        cell = LSTMCell(input_size=10, hidden_size=20)

        assert cell.input_size == 10
        assert cell.hidden_size == 20
        # LSTM has 4 gates, so weight matrices are 4x larger
        assert cell.weight_ih.shape == (10, 80)  # 4 * 20
        assert cell.weight_hh.shape == (20, 80)  # 4 * 20
        assert cell.bias.shape == (80,)  # 4 * 20

    def test_lstm_cell_forward(self):
        """Test LSTM cell forward pass."""
        cell = LSTMCell(input_size=2, hidden_size=3)

        x = mn.Tensor([[1, 2]], requires_grad=True)
        h_prev = mn.Tensor([[0, 0, 0]], requires_grad=True)
        c_prev = mn.Tensor([[0, 0, 0]], requires_grad=True)

        h_next, c_next = cell(x, (h_prev, c_prev))

        assert h_next.shape == (1, 3)
        assert c_next.shape == (1, 3)

    def test_lstm_cell_state_flow(self):
        """Test LSTM cell state flow through time."""
        cell = LSTMCell(input_size=1, hidden_size=2)

        # Sequence of inputs
        inputs = [mn.Tensor([[i]], requires_grad=True) for i in [1, 2, 3]]

        h = mn.Tensor([[0, 0]], requires_grad=True)
        c = mn.Tensor([[0, 0]], requires_grad=True)

        outputs = []
        for x in inputs:
            h, c = cell(x, (h, c))
            outputs.append(h)

        assert len(outputs) == 3
        for output in outputs:
            assert output.shape == (1, 2)

class TestGRUCell:
    """Test GRU cell functionality."""

    def test_gru_cell_creation(self):
        """Test GRU cell creation."""
        cell = GRUCell(input_size=10, hidden_size=20)

        assert cell.input_size == 10
        assert cell.hidden_size == 20
        # GRU has 3 gates
        assert cell.weight_ih.shape == (10, 60)  # 3 * 20
        assert cell.weight_hh.shape == (20, 60)  # 3 * 20
        assert cell.bias.shape == (60,)  # 3 * 20

    def test_gru_cell_forward(self):
        """Test GRU cell forward pass."""
        cell = GRUCell(input_size=2, hidden_size=3)

        x = mn.Tensor([[1, 2]], requires_grad=True)
        h_prev = mn.Tensor([[0, 0, 0]], requires_grad=True)

        h_next = cell(x, h_prev)

        assert h_next.shape == (1, 3)

class TestRNN:
    """Test multi-layer RNN module."""

    def test_rnn_creation(self):
        """Test RNN module creation."""
        rnn = RNN(input_size=10, hidden_size=20, num_layers=2, 
                 cell_type='rnn', dropout=0.1, batch_first=True)

        assert rnn.input_size == 10
        assert rnn.hidden_size == 20
        assert rnn.num_layers == 2
        assert rnn.cell_type == 'rnn'
        assert rnn.dropout_p == 0.1
        assert rnn.batch_first == True
        assert len(rnn.cells) == 2

    def test_rnn_forward_batch_first(self):
        """Test RNN forward pass with batch_first=True."""
        rnn = RNN(input_size=5, hidden_size=8, num_layers=1, 
                 cell_type='rnn', batch_first=True)

        # Input shape: (batch_size, seq_len, input_size)
        x = mn.Tensor(np.random.randn(3, 7, 5), requires_grad=True)

        output, hidden = rnn(x)

        # Output shape: (batch_size, seq_len, hidden_size)
        assert output.shape == (3, 7, 8)
        # Hidden shape: (num_layers, batch_size, hidden_size)
        assert hidden.shape == (1, 3, 8)

    def test_rnn_forward_batch_second(self):
        """Test RNN forward pass with batch_first=False."""
        rnn = RNN(input_size=5, hidden_size=8, num_layers=1,
                 cell_type='rnn', batch_first=False)

        # Input shape: (seq_len, batch_size, input_size)
        x = mn.Tensor(np.random.randn(7, 3, 5), requires_grad=True)

        output, hidden = rnn(x)

        # Output shape: (seq_len, batch_size, hidden_size)
        assert output.shape == (7, 3, 8)
        # Hidden shape: (num_layers, batch_size, hidden_size)
        assert hidden.shape == (1, 3, 8)

    def test_lstm_forward(self):
        """Test LSTM forward pass."""
        rnn = RNN(input_size=4, hidden_size=6, num_layers=2,
                 cell_type='lstm', batch_first=True)

        x = mn.Tensor(np.random.randn(2, 5, 4), requires_grad=True)

        output, (hidden, cell) = rnn(x)

        assert output.shape == (2, 5, 6)
        assert hidden.shape == (2, 2, 6)  # (num_layers, batch_size, hidden_size)
        assert cell.shape == (2, 2, 6)

    def test_gru_forward(self):
        """Test GRU forward pass."""
        rnn = RNN(input_size=3, hidden_size=5, num_layers=1,
                 cell_type='gru', batch_first=True)

        x = mn.Tensor(np.random.randn(4, 6, 3), requires_grad=True)

        output, hidden = rnn(x)

        assert output.shape == (4, 6, 5)
        assert hidden.shape == (1, 4, 5)

    def test_rnn_multilayer(self):
        """Test multi-layer RNN."""
        rnn = RNN(input_size=2, hidden_size=3, num_layers=3,
                 cell_type='rnn', batch_first=True)

        x = mn.Tensor(np.random.randn(1, 4, 2), requires_grad=True)

        output, hidden = rnn(x)

        assert output.shape == (1, 4, 3)
        assert hidden.shape == (3, 1, 3)  # 3 layers

    def test_rnn_with_dropout(self):
        """Test RNN with dropout."""
        rnn = RNN(input_size=2, hidden_size=3, num_layers=2,
                 cell_type='rnn', dropout=0.5, batch_first=True)

        # Set training mode
        rnn.training = True

        x = mn.Tensor(np.random.randn(2, 3, 2), requires_grad=True)

        output1, _ = rnn(x)
        output2, _ = rnn(x)

        # With dropout, outputs should be different
        # (This test might occasionally fail due to randomness)
        assert not np.allclose(output1.data, output2.data, atol=1e-6)

class TestRNNBackpropagation:
    """Test backpropagation through RNN components."""

    def test_rnn_cell_gradients(self):
        """Test gradient computation for RNN cell."""
        cell = RNNCell(input_size=2, hidden_size=3)

        x = mn.Tensor([[1, 2]], requires_grad=True)
        h_prev = mn.Tensor([[0.5, -0.5, 1.0]], requires_grad=True)

        h_next = cell(x, h_prev)
        loss = h_next.sum()

        loss.backward()

        # All parameters should have gradients
        assert cell.weight_ih.grad is not None
        assert cell.weight_hh.grad is not None
        assert cell.bias.grad is not None

        # Input gradients should exist
        assert x.grad is not None
        assert h_prev.grad is not None

    def test_lstm_cell_gradients(self):
        """Test gradient computation for LSTM cell."""
        cell = LSTMCell(input_size=2, hidden_size=2)

        x = mn.Tensor([[1, 0]], requires_grad=True)
        h_prev = mn.Tensor([[0, 0]], requires_grad=True)
        c_prev = mn.Tensor([[0, 0]], requires_grad=True)

        h_next, c_next = cell(x, (h_prev, c_prev))
        loss = h_next.sum() + c_next.sum()

        loss.backward()

        # Check parameter gradients
        assert cell.weight_ih.grad is not None
        assert cell.weight_hh.grad is not None
        assert cell.bias.grad is not None

        # Check input gradients
        assert x.grad is not None
        assert h_prev.grad is not None
        assert c_prev.grad is not None

    def test_rnn_sequence_gradients(self):
        """Test gradient computation through RNN sequence."""
        rnn = RNN(input_size=1, hidden_size=2, num_layers=1,
                 cell_type='rnn', batch_first=True)

        # Short sequence
        x = mn.Tensor([[[1], [2], [3]]], requires_grad=True)  # (batch=1, seq=3, input=1)

        output, hidden = rnn(x)
        loss = output.sum()

        loss.backward()

        # Input should have gradients
        assert x.grad is not None

        # All RNN parameters should have gradients
        for cell in rnn.cells:
            assert cell.weight_ih.grad is not None
            assert cell.weight_hh.grad is not None
            assert cell.bias.grad is not None

class TestRNNSequenceModeling:
    """Test RNN for sequence modeling tasks."""

    def test_rnn_language_model_style(self):
        """Test RNN in language model style task."""
        vocab_size = 10
        embed_size = 8
        hidden_size = 16

        # Simple sequence model: embedding -> RNN -> output
        model = Sequential(
            # Note: In real implementation, you'd have an embedding layer
            # For now, assume inputs are already embedded
            RNN(embed_size, hidden_size, num_layers=1, cell_type='rnn', batch_first=True),
            # Note: This doesn't handle the RNN output properly, just for testing
        )

        # Simulate embedded input sequence
        x = mn.Tensor(np.random.randn(2, 5, embed_size), requires_grad=True)

        # For this test, just check that forward pass works
        # In reality, you'd need to extract outputs properly and add a classifier
        try:
            output, hidden = model.layers[0](x)  # Just test the RNN layer
            assert output.shape == (2, 5, hidden_size)
            assert hidden.shape == (1, 2, hidden_size)
        except Exception as e:
            pytest.fail(f"RNN forward pass failed: {e}")

    def test_rnn_sequence_classification(self):
        """Test RNN for sequence classification."""
        seq_len = 10
        input_size = 5
        hidden_size = 8
        num_classes = 3

        # Model: RNN + take last output + classify
        rnn = RNN(input_size, hidden_size, num_layers=1, cell_type='lstm', batch_first=True)
        classifier = Linear(hidden_size, num_classes)

        x = mn.Tensor(np.random.randn(4, seq_len, input_size), requires_grad=True)

        # Forward pass
        rnn_output, (hidden, cell) = rnn(x)

        # Take last time step output
        last_output = rnn_output[:, -1, :]  # (batch_size, hidden_size)

        # Classify
        logits = classifier(last_output)

        assert logits.shape == (4, num_classes)

        # Test backward pass
        loss = logits.sum()
        loss.backward()

        assert x.grad is not None

    def test_rnn_sequence_to_sequence(self):
        """Test RNN for sequence-to-sequence task."""
        input_size = 4
        hidden_size = 6
        output_size = 3
        seq_len = 7

        # Encoder-Decoder style
        encoder = RNN(input_size, hidden_size, num_layers=1, cell_type='gru', batch_first=True)
        decoder_cell = GRUCell(output_size, hidden_size)
        output_projection = Linear(hidden_size, output_size)

        # Encoder input
        encoder_input = mn.Tensor(np.random.randn(1, seq_len, input_size), requires_grad=True)

        # Encode
        encoder_output, encoder_hidden = encoder(encoder_input)

        # Use last encoder hidden as initial decoder hidden
        decoder_hidden = encoder_hidden[-1]  # (batch_size, hidden_size)

        # Decode (simplified - just one step)
        decoder_input = mn.Tensor(np.random.randn(1, output_size), requires_grad=True)
        decoder_hidden = decoder_cell(decoder_input, decoder_hidden)
        output = output_projection(decoder_hidden)

        assert output.shape == (1, output_size)

        # Test backward pass
        loss = output.sum()
        loss.backward()

        assert encoder_input.grad is not None
        assert decoder_input.grad is not None

class TestRNNNumericalStability:
    """Test RNN numerical stability."""

    def test_rnn_long_sequences(self):
        """Test RNN with longer sequences."""
        rnn = RNN(input_size=2, hidden_size=4, num_layers=1,
                 cell_type='rnn', batch_first=True)

        # Longer sequence
        x = mn.Tensor(np.random.randn(1, 50, 2), requires_grad=True)

        output, hidden = rnn(x)

        # Check for numerical issues
        assert not np.any(np.isnan(output.data))
        assert not np.any(np.isinf(output.data))
        assert not np.any(np.isnan(hidden.data))
        assert not np.any(np.isinf(hidden.data))

    def test_lstm_vanishing_gradients(self):
        """Test LSTM handling of vanishing gradients."""
        lstm = RNN(input_size=1, hidden_size=3, num_layers=1,
                  cell_type='lstm', batch_first=True)

        # Create a sequence where early inputs should influence final output
        x = mn.Tensor([[[1], [0], [0], [0], [0]]], requires_grad=True)

        output, (hidden, cell) = lstm(x)

        # Loss depends on final output
        loss = output[:, -1, :].sum()
        loss.backward()

        # Gradient should exist for the first input (LSTM should help with vanishing gradients)
        assert x.grad is not None
        assert not np.all(x.grad[0, 0, :] == 0)  # First timestep should have non-zero gradient

    def test_rnn_gradient_clipping_need(self):
        """Test scenarios where gradient clipping might be needed."""
        rnn = RNN(input_size=1, hidden_size=2, num_layers=1,
                 cell_type='rnn', batch_first=True)

        # Initialize with large weights (might cause exploding gradients)
        for cell in rnn.cells:
            cell.weight_hh.data *= 10.0

        x = mn.Tensor(np.ones((1, 10, 1)), requires_grad=True)

        output, hidden = rnn(x)
        loss = output.sum()

        loss.backward()

        # Check if gradients are very large
        max_grad = 0
        for cell in rnn.cells:
            if cell.weight_hh.grad is not None:
                max_grad = max(max_grad, np.max(np.abs(cell.weight_hh.grad)))

        # This test just checks that we can detect when gradients might explode
        # In practice, you'd implement gradient clipping if max_grad > threshold

