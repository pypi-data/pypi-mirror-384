import torch
from sklearn.metrics import accuracy_score, mean_squared_error

def evaluate_model(model, X_test, y_test):
    """
    Evaluates the model using test data.
    """
    model.eval()

    with torch.no_grad():
        output = model(X_test)

    if isinstance(model, SimpleNN):
        if model.output_layer.out_features == 1:  # Regression
            output = output.squeeze()
            mse = mean_squared_error(y_test.cpu(), output.cpu())
            return f"Mean Squared Error: {mse:.4f}"
        else:  # Classification
            _, predicted = torch.max(output, 1)
            accuracy = accuracy_score(y_test.cpu(), predicted.cpu())
            return f"Accuracy: {accuracy:.4f}"

    else:
        raise ValueError("Unsupported model type.")
