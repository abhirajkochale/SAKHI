import os
import shap
import pandas as pd
from typing import Optional
from app.schemas.risk import RiskFeatures, RiskExplanation, SHAPContribution

class SHAPService:
    def __init__(self, ml_service):
        self.ml_service = ml_service
        self.explainer = None
        
        if self.ml_service.is_available() and self.ml_service.model is not None:
            try:
                # TreeExplainer is heavily optimized for XGBoost
                self.explainer = shap.TreeExplainer(self.ml_service.model)
            except Exception:
                self.explainer = None

    def explain(self, features: RiskFeatures, predicted_risk: float) -> RiskExplanation:
        if not self.ml_service.is_available() or self.explainer is None:
            return RiskExplanation(
                available=False,
                reason="SHAP explanation unavailable because XGBoost model is not active."
            )
            
        expected_features = self.ml_service.get_metadata().get("feature_names", [])
        feature_dict = features.model_dump()
        
        # Verify schema
        for f in expected_features:
            if f not in feature_dict:
                return RiskExplanation(
                    available=False,
                    reason="Invalid feature schema for explanation."
                )
                
        # Order features exactly as expected
        input_data = {f: [feature_dict[f]] for f in expected_features}
        df_input = pd.DataFrame(input_data)
        
        try:
            # Calculate SHAP values
            shap_values_obj = self.explainer(df_input)
            shap_values = shap_values_obj.values[0]
            base_value = float(shap_values_obj.base_values[0])
            
            contributions = []
            for i, feature_name in enumerate(expected_features):
                val = float(shap_values[i])
                feat_val = float(feature_dict[feature_name])
                
                direction = "increases_risk" if val > 0 else "decreases_risk"
                
                contributions.append(SHAPContribution(
                    feature_name=feature_name,
                    feature_value=feat_val,
                    shap_value=val,
                    direction=direction
                ))
                
            # Sort by absolute SHAP magnitude descending
            contributions.sort(key=lambda x: abs(x.shap_value), reverse=True)
            
            positive_factors = [c for c in contributions if c.shap_value > 0]
            negative_factors = [c for c in contributions if c.shap_value <= 0]
            
            return RiskExplanation(
                available=True,
                base_value=base_value,
                predicted_risk=predicted_risk,
                top_positive_factors=positive_factors[:3],
                top_negative_factors=negative_factors[:3],
                all_contributions=contributions
            )
            
        except Exception as e:
            return RiskExplanation(
                available=False,
                reason="SHAP calculation failed."
            )
