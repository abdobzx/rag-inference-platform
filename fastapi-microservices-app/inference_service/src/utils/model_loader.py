from typing import Any
import joblib

def load_model(model_path: str) -> Any:
    """Load a machine learning model from the specified path."""
    model = joblib.load(model_path)
    return model

def predict(model: Any, data: Any) -> Any:
    """Make a prediction using the loaded model and input data."""
    return model.predict(data)