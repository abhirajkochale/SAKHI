import pandas as pd
import numpy as np
import os

def generate_synthetic_data(num_samples=1000):
    np.random.seed(42)
    
    # Generate random features mirroring RiskFeatures schema
    hours = np.random.uniform(0, 24, num_samples)
    hour_sin = np.sin(2 * np.pi * hours / 24.0)
    hour_cos = np.cos(2 * np.pi * hours / 24.0)
    
    is_weekend = np.random.choice([0.0, 1.0], size=num_samples, p=[0.7, 0.3])
    
    # Environmental indicators (0 to 1)
    isolation = np.random.uniform(0, 1, num_samples)
    cctv = np.random.uniform(0, 1, num_samples)
    police = np.random.uniform(0, 1, num_samples)
    transit = np.random.uniform(0, 1, num_samples)
    infra = np.random.uniform(0, 1, num_samples)
    historical = np.random.uniform(0, 1, num_samples)
    
    # 5% chance of validated report
    report = np.random.choice([0.0, 1.0], size=num_samples, p=[0.95, 0.05])
    
    # Synthesize target using a different, slightly non-linear relationship with noise
    # Base risk
    target = historical * 30.0
    
    # Non-linear isolation penalty
    target += (isolation ** 1.5) * 40.0
    
    # Protective effects (transit + police + cctv interaction)
    protection = (cctv * 0.4 + police * 0.4 + transit * 0.2)
    target -= (protection * 30.0)
    
    # Weekend late night penalty interaction
    late_night = (hour_cos > 0.5).astype(float)
    target += (late_night * is_weekend * 15.0)
    
    # Report overrides
    target += (report * 25.0)
    
    # Add random noise
    noise = np.random.normal(0, 5, num_samples)
    target += noise
    
    # Bound to 0-100
    target = np.clip(target, 0, 100)
    
    df = pd.DataFrame({
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "is_weekend": is_weekend,
        "environmental_isolation_indicator": isolation,
        "cctv_coverage": cctv,
        "police_proximity": police,
        "transit_access": transit,
        "infrastructure_score": infra,
        "historical_baseline": historical,
        "validated_report_signal": report,
        "target_risk_score": target
    })
    
    os.makedirs(os.path.join(os.path.dirname(__file__), "data", "synthetic"), exist_ok=True)
    file_path = os.path.join(os.path.dirname(__file__), "data", "synthetic", "synthetic_contextual_segments.csv")
    df.to_csv(file_path, index=False)
    print(f"Generated {num_samples} records at {file_path}")
    print("NOTE: Synthetic prototype data - not real incident data.")

if __name__ == "__main__":
    generate_synthetic_data()
