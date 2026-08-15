import os
import json
import joblib
import pandas as pd
from typing import Optional, Dict, Any
from app.schemas.risk import RiskFeatures

class MLModelService:
    def __init__(self, models_dir: Optional[str] = None):
        self.model = None
        self.metadata = None
        
        # Determine paths relative to this file if not provided
        if models_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            models_dir = os.path.join(base_dir, "ml", "models")
            
        model_path = os.path.join(models_dir, "contextual_risk_model.joblib")
        metadata_path = os.path.join(models_dir, "model_metadata.json")
        
        try:
            if os.path.exists(model_path) and os.path.exists(metadata_path):
                self.model = joblib.load(model_path)
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
        except Exception:
            # Fallback will trigger if model fails to load
            pass

    def is_available(self) -> bool:
        return self.model is not None and self.metadata is not None

    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata or {}

    def predict(self, features: RiskFeatures) -> Optional[float]:
        if not self.is_available():
            return None
            
        expected_features = self.metadata.get("feature_names", [])
        
        # Convert Pydantic model to dict
        feature_dict = features.model_dump()
        
        # Validate feature schema consistency
        for feature in expected_features:
            if feature not in feature_dict:
                return None
                
        # Order features exactly as expected by the model
        input_data = {f: [feature_dict[f]] for f in expected_features}
        df_input = pd.DataFrame(input_data)
        
        try:
            prediction = self.model.predict(df_input)[0]
            # Normalize/bound to 0-100
            return float(max(0.0, min(100.0, prediction)))
        except Exception:
            # Inference error -> trigger fallback
            return None
