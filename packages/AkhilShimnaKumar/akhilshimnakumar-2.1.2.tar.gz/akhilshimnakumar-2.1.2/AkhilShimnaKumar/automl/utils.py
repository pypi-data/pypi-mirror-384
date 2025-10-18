import torch

def save_model(model, model_name='model.pth'):
    """
    Saves the PyTorch model to a file.
    """
    torch.save(model.state_dict(), model_name)

def load_model(model_name='model.pth'):
    """
    Loads a PyTorch model from a file.
    """
    model = SimpleNN(input_dim=30, output_dim=2, task='classification')  # Specify the task and input/output dims
    model.load_state_dict(torch.load(model_name))
    model.eval()
    return model
