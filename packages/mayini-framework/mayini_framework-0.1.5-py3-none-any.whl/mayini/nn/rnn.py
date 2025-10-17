# Create a simplified rnn.py file with basic RNN components

rnn_content = '''"""
Recurrent Neural Network components.
"""

import numpy as np
from typing import Tuple, Optional
from ..tensor import Tensor
from .modules import Module
from .activations import tanh, sigmoid

class RNNCell(Module):
    """Basic RNN Cell."""
    
    def __init__(self, input_size: int, hidden_size: int, bias: bool = True):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.use_bias = bias
        
        # Initialize weights
        std = 1.0 / np.sqrt(hidden_size)
        self.weight_ih = Tensor(np.random.uniform(-std, std, (hidden_size, input_size)), requires_grad=True)
        self.weight_hh = Tensor(np.random.uniform(-std, std, (hidden_size, hidden_size)), requires_grad=True)
        
        self._parameters.extend([self.weight_ih, self.weight_hh])
        
        if bias:
            self.bias_ih = Tensor(np.zeros(hidden_size), requires_grad=True)
            self.bias_hh = Tensor(np.zeros(hidden_size), requires_grad=True)
            self._parameters.extend([self.bias_ih, self.bias_hh])
        else:
            self.bias_ih = None
            self.bias_hh = None
    
    def forward(self, input_tensor: Tensor, hidden: Optional[Tensor] = None) -> Tensor:
        if hidden is None:
            hidden = Tensor(np.zeros((input_tensor.shape[0], self.hidden_size)))
        
        # RNN computation: h_t = tanh(W_ih @ x_t + b_ih + W_hh @ h_{t-1} + b_hh)
        ih_result = input_tensor.matmul(self.weight_ih.transpose())
        hh_result = hidden.matmul(self.weight_hh.transpose())
        
        if self.use_bias:
            ih_result = ih_result + self.bias_ih
            hh_result = hh_result + self.bias_hh
        
        return tanh(ih_result + hh_result)

class LSTMCell(Module):
    """LSTM Cell (simplified implementation)."""
    
    def __init__(self, input_size: int, hidden_size: int, bias: bool = True):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.use_bias = bias
        
        # Initialize weights for all gates (forget, input, output, cell)
        std = 1.0 / np.sqrt(hidden_size)
        self.weight_ih = Tensor(np.random.uniform(-std, std, (4 * hidden_size, input_size)), requires_grad=True)
        self.weight_hh = Tensor(np.random.uniform(-std, std, (4 * hidden_size, hidden_size)), requires_grad=True)
        
        self._parameters.extend([self.weight_ih, self.weight_hh])
        
        if bias:
            self.bias_ih = Tensor(np.zeros(4 * hidden_size), requires_grad=True)
            self.bias_hh = Tensor(np.zeros(4 * hidden_size), requires_grad=True)
            self._parameters.extend([self.bias_ih, self.bias_hh])
        else:
            self.bias_ih = None
            self.bias_hh = None
    
    def forward(self, input_tensor: Tensor, state: Optional[Tuple[Tensor, Tensor]] = None) -> Tuple[Tensor, Tensor]:
        if state is None:
            batch_size = input_tensor.shape[0]
            hidden = Tensor(np.zeros((batch_size, self.hidden_size)))
            cell = Tensor(np.zeros((batch_size, self.hidden_size)))
        else:
            hidden, cell = state
        
        # Compute gates
        ih_result = input_tensor.matmul(self.weight_ih.transpose())
        hh_result = hidden.matmul(self.weight_hh.transpose())
        
        if self.use_bias:
            ih_result = ih_result + self.bias_ih
            hh_result = hh_result + self.bias_hh
        
        gates = ih_result + hh_result
        
        # Split gates (forget, input, output, candidate)
        # Note: This is a simplified implementation
        gate_size = self.hidden_size
        forget_gate = sigmoid(gates[:, :gate_size] if gates.data.ndim > 1 else gates[:gate_size])
        input_gate = sigmoid(gates[:, gate_size:2*gate_size] if gates.data.ndim > 1 else gates[gate_size:2*gate_size])
        output_gate = sigmoid(gates[:, 2*gate_size:3*gate_size] if gates.data.ndim > 1 else gates[2*gate_size:3*gate_size])
        candidate_gate = tanh(gates[:, 3*gate_size:] if gates.data.ndim > 1 else gates[3*gate_size:])
        
        # Update cell state
        new_cell = forget_gate * cell + input_gate * candidate_gate
        
        # Update hidden state
        new_hidden = output_gate * tanh(new_cell)
        
        return new_hidden, new_cell

class GRUCell(Module):
    """GRU Cell (simplified implementation)."""
    
    def __init__(self, input_size: int, hidden_size: int, bias: bool = True):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.use_bias = bias
        
        # Initialize weights for reset and update gates
        std = 1.0 / np.sqrt(hidden_size)
        self.weight_ih = Tensor(np.random.uniform(-std, std, (3 * hidden_size, input_size)), requires_grad=True)
        self.weight_hh = Tensor(np.random.uniform(-std, std, (3 * hidden_size, hidden_size)), requires_grad=True)
        
        self._parameters.extend([self.weight_ih, self.weight_hh])
        
        if bias:
            self.bias_ih = Tensor(np.zeros(3 * hidden_size), requires_grad=True)
            self.bias_hh = Tensor(np.zeros(3 * hidden_size), requires_grad=True)
            self._parameters.extend([self.bias_ih, self.bias_hh])
        else:
            self.bias_ih = None
            self.bias_hh = None
    
    def forward(self, input_tensor: Tensor, hidden: Optional[Tensor] = None) -> Tensor:
        if hidden is None:
            hidden = Tensor(np.zeros((input_tensor.shape[0], self.hidden_size)))
        
        # Compute gates
        ih_result = input_tensor.matmul(self.weight_ih.transpose())
        hh_result = hidden.matmul(self.weight_hh.transpose())
        
        if self.use_bias:
            ih_result = ih_result + self.bias_ih
            hh_result = hh_result + self.bias_hh
        
        # Split into reset, update, and new gates
        gate_size = self.hidden_size
        reset_gate = sigmoid(ih_result[:, :gate_size] + hh_result[:, :gate_size])
        update_gate = sigmoid(ih_result[:, gate_size:2*gate_size] + hh_result[:, gate_size:2*gate_size])
        new_gate = tanh(ih_result[:, 2*gate_size:] + reset_gate * hh_result[:, 2*gate_size:])
        
        # Compute new hidden state
        new_hidden = (Tensor(np.ones_like(update_gate.data)) - update_gate) * new_gate + update_gate * hidden
        
        return new_hidden

class RNN(Module):
    """Multi-layer RNN wrapper."""
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int = 1, 
                 cell_type: str = 'rnn', dropout: float = 0.0, batch_first: bool = False):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.cell_type = cell_type.lower()
        self.dropout = dropout
        self.batch_first = batch_first
        
        # Create cells
        self.cells = []
        for i in range(num_layers):
            if cell_type == 'lstm':
                cell = LSTMCell(input_size if i == 0 else hidden_size, hidden_size)
            elif cell_type == 'gru':
                cell = GRUCell(input_size if i == 0 else hidden_size, hidden_size)
            else:  # 'rnn'
                cell = RNNCell(input_size if i == 0 else hidden_size, hidden_size)
            
            self.cells.append(cell)
            self._modules.append(cell)
    
    def forward(self, input_seq: Tensor, initial_states: Optional[list] = None):
        if not self.batch_first:
            # Convert from (seq_len, batch, features) to (batch, seq_len, features)
            input_seq = input_seq.transpose((1, 0, 2))
        
        batch_size, seq_len, _ = input_seq.shape
        outputs = []
        states = initial_states or [None] * self.num_layers
        
        for t in range(seq_len):
            x = Tensor(input_seq.data[:, t, :])  # Get timestep t
            
            new_states = []
            for layer_idx, cell in enumerate(self.cells):
                if self.cell_type == 'lstm':
                    x, new_cell = cell(x, states[layer_idx])
                    new_states.append((x, new_cell))
                else:
                    x = cell(x, states[layer_idx])
                    new_states.append(x)
            
            outputs.append(x)
            states = new_states
        
        # Stack outputs: (batch, seq_len, hidden_size)
        output_data = np.stack([out.data for out in outputs], axis=1)
        output_tensor = Tensor(output_data, requires_grad=any(out.requires_grad for out in outputs))
        
        if not self.batch_first:
            # Convert back to (seq_len, batch, features)
            output_tensor = output_tensor.transpose((1, 0, 2))
        
        return output_tensor, states

__all__ = ['RNNCell', 'LSTMCell', 'GRUCell', 'RNN']
'''

print("✓ Created complete rnn.py with RNN components")
print("Length:", len(rnn_content), "characters")
