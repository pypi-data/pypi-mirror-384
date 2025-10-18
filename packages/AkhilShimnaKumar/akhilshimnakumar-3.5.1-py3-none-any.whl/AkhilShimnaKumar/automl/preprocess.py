from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
import numpy as np

def preprocess_data(data, task='classification'):
    """
    Preprocesses data by handling missing values, scaling features, and encoding categorical variables.
    """
    # Handle missing values
    imputer = SimpleImputer(strategy='mean')  # Mean imputation for numerical data
    data = data.apply(lambda x: imputer.fit_transform(x.values.reshape(-1, 1)) if x.isnull().any() else x, axis=0)
    
    # Encoding categorical columns
    categorical_columns = data.select_dtypes(include=['object']).columns
    label_encoder = LabelEncoder()
    for col in categorical_columns:
        data[col] = label_encoder.fit_transform(data[col])
    
    # Feature Scaling
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data.drop('target', axis=1))
    
    return pd.DataFrame(scaled_data, columns=data.drop('target', axis=1).columns)
