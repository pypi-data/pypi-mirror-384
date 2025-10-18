import torch
import torch.optim as optim
import pandas as pd
from sklearn.model_selection import train_test_split
from .preprocess import preprocess_data
from .model import select_model
from .tune import tune_model
from .evaluate import evaluate_model
from .utils import save_model, load_model

class AutoML:
    def __init__(self, task='classification', device=None, random_state=42):
        self.task = task
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        self.random_state = random_state
        self.model = None

    def load_data(self, file_path):
        """
        Loads data from a CSV file and preprocesses it.
        """
        data = pd.read_csv(file_path)
        return preprocess_data(data, task=self.task)

    def train(self, data):
        """
        Trains the model by selecting the appropriate model and tuning hyperparameters.
        """
        X = data.drop('target', axis=1).values
        y = data['target'].values

        # Convert to PyTorch tensors
        X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)
        y_tensor = torch.tensor(y, dtype=torch.float32).to(self.device)

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X_tensor, y_tensor, test_size=0.2, random_state=self.random_state)

        # Select model
        self.model = select_model(task=self.task).to(self.device)
        
        # Hyperparameter tuning
        self.model = tune_model(self.model, X_train, y_train)

        # Train the model
        self._train_model(X_train, y_train)

        # Evaluate the model
        evaluation_results = evaluate_model(self.model, X_test, y_test)
        print(evaluation_results)

        return self.model

    def _train_model(self, X_train, y_train):
        """
        Train the model using PyTorch. Includes forward pass, loss calculation, and backpropagation.
        """
        criterion = torch.nn.MSELoss() if self.task == 'regression' else torch.nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        # Training loop
        epochs = 10
        for epoch in range(epochs):
            self.model.train()

            optimizer.zero_grad()

            # Forward pass
            output = self.model(X_train)

            # Calculate loss
            loss = criterion(output, y_train)
            loss.backward()

            # Update weights
            optimizer.step()

            if (epoch+1) % 5 == 0:
                print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

    def save_model(self, model_name='model.pth'):
        """
        Saves the trained model to a file.
        """
        save_model(self.model, model_name)

    def load_saved_model(self, model_name='model.pth'):
        """
        Loads a saved model.
        """
        self.model = load_model(model_name)
        return self.model
