import torch.nn as nn

class SimpleNN(nn.Module):
    def __init__(self, input_dim, output_dim, task='classification'):
        super(SimpleNN, self).__init__()
        
        # Classification or regression architecture
        self.hidden_layer = nn.Linear(input_dim, 64)
        self.output_layer = nn.Linear(64, output_dim)

        if task == 'classification':
            self.activation = nn.Softmax(dim=1)  # For classification
        else:
            self.activation = nn.Identity()  # For regression (no activation)
    
    def forward(self, x):
        x = torch.relu(self.hidden_layer(x))
        x = self.activation(self.output_layer(x))
        return x

def select_model(task='classification'):
    """
    Select the appropriate PyTorch model based on the task (classification or regression).
    """
    if task == 'classification':
        # 2 output units for binary classification, or more for multi-class
        return SimpleNN(input_dim=30, output_dim=2, task=task)
    elif task == 'regression':
        return SimpleNN(input_dim=30, output_dim=1, task=task)
    else:
        raise ValueError("Invalid task. Choose either 'classification' or 'regression'.")
