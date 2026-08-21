import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import joblib
import json
import os

def train_model():
    data_path = os.path.join(os.path.dirname(__file__), "data", "synthetic", "synthetic_contextual_segments.csv")
    if not os.path.exists(data_path):
        print(f"Error: Dataset not found at {data_path}. Run generate_synthetic_data.py first.")
        return

    df = pd.read_csv(data_path)
    
    # Feature ordering must explicitly match RiskFeatures schema exactly
    feature_cols = [
        "hour_sin",
        "hour_cos",
        "is_weekend",
        "environmental_isolation_indicator",
        "cctv_coverage",
        "police_proximity",
        "transit_access",
        "infrastructure_score",
        "historical_baseline",
        "validated_report_signal"
    ]
    
    X = df[feature_cols]
    y = df["target_risk_score"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training XGBoost Regressor...")
    model = xgb.XGBRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0, 100) # output constraint
    
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    print("\n--- Evaluation Metrics ---")
    print("These metrics measure performance on synthetic prototype data only.")
    print("They demonstrate the ML pipeline but do not establish real-world predictive validity.")
    print(f"Dataset Size: {len(df)}")
    print(f"Train Size: {len(X_train)} | Test Size: {len(X_test)}")
    print(f"MAE:  {mae:.2f}")
    print(f"MSE:  {mse:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²:   {r2:.4f}")
    
    # Save model and metadata
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, "contextual_risk_model.joblib")
    joblib.dump(model, model_path)
    
    metadata = {
        "model_name": "sakhi_contextual_risk",
        "model_version": "0.1.0",
        "model_source": "xgboost",
        "dataset_type": "synthetic_prototype",
        "training_dataset_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "feature_names": feature_cols,
        "evaluation_metrics": {
            "mae": mae,
            "mse": mse,
            "rmse": rmse,
            "r2": r2,
            "disclaimer": "These metrics measure performance on synthetic prototype data only."
        },
        "xgboost_parameters": {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 5
        }
    }
    
    metadata_path = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"\nSaved model artifact to: {model_path}")
    print(f"Saved metadata to: {metadata_path}")

if __name__ == "__main__":
    train_model()
