import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import os

# Set seed for reproducibility
np.random.seed(42)

def generate_synthetic_peer_data(num_samples=1000):
    """
    Generates a realistic synthetic dataset representing 1000 GATE aspirants.
    """
    # 1. Generate independent features
    total_attempts = np.random.randint(40, 500, size=num_samples)
    accuracy = np.random.uniform(0.35, 0.95, size=num_samples)
    
    # Medium/Hard accuracy is correlated with overall accuracy but slightly lower
    medium_hard_accuracy = accuracy * np.random.uniform(0.75, 0.95, size=num_samples)
    medium_hard_accuracy = np.clip(medium_hard_accuracy, 0.0, 1.0)
    
    # Average time per question (seconds)
    avg_time = np.random.uniform(40, 180, size=num_samples)
    
    # Syllabus coverage (0.0 to 1.0)
    syllabus_coverage = np.random.uniform(0.15, 0.98, size=num_samples)
    
    # Consistency score (based on regular practice frequency, 0.0 to 1.0)
    consistency = np.random.uniform(0.20, 0.95, size=num_samples)
    
    # 2. Formulate target GATE Score (100 to 1000 scale)
    # Base score
    base_score = 100
    
    # Score component calculations
    score_acc = accuracy * 450
    score_coverage = syllabus_coverage * 280
    score_hard_acc = medium_hard_accuracy * 120
    # Penalty for being too slow, reward for moderate efficiency
    score_speed = (180 - avg_time) / 140 * 50
    
    # Random variance / noise representing exam day factors
    noise = np.random.normal(0, 15, size=num_samples)
    
    gate_score = base_score + score_acc + score_coverage + score_hard_acc + score_speed + noise
    gate_score = np.clip(gate_score, 100, 1000).astype(int)
    
    # 3. Formulate target GATE Rank (AIR: 1 to ~150,000)
    # Higher score = lower rank (i.e. better rank). GATE rank follows a steep exponential/logarithmic distribution curve.
    gate_rank = np.zeros(num_samples)
    
    for i in range(num_samples):
        sc = gate_score[i]
        rk_noise = np.random.normal(0, max(1, (1000 - sc) * 0.05))
        
        if sc >= 850:
            rk = 1 + (1000 - sc) * 0.7 + rk_noise
        elif sc >= 700:
            rk = 105 + (850 - sc) * 6 + rk_noise
        elif sc >= 500:
            rk = 1005 + (700 - sc) * 20 + rk_noise
        elif sc >= 350:
            rk = 5005 + (500 - sc) * 120 + rk_noise
        else:
            rk = 23005 + (350 - sc) * 650 + rk_noise
            
        gate_rank[i] = np.clip(rk, 1, 150000)
        
    gate_rank = gate_rank.astype(int)
    
    # Create DataFrame
    df = pd.DataFrame({
        "total_attempts": total_attempts,
        "accuracy": accuracy,
        "medium_hard_accuracy": medium_hard_accuracy,
        "avg_time_spent": avg_time,
        "consistency": consistency,
        "syllabus_coverage": syllabus_coverage,
        "gate_score": gate_score,
        "gate_rank": gate_rank
    })
    
    return df

def train_and_save_models():
    # Set output paths
    models_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(models_dir, exist_ok=True)
    
    score_model_path = os.path.join(models_dir, 'gate_score_model.pkl')
    rank_model_path = os.path.join(models_dir, 'gate_rank_model.pkl')
    csv_data_path = os.path.join(os.path.dirname(models_dir), 'data', 'synthetic_peers.csv')
    os.makedirs(os.path.dirname(csv_data_path), exist_ok=True)
    
    # Generate data
    df = generate_synthetic_peer_data(1200)
    df.to_csv(csv_data_path, index=False)
    print(f"Generated synthetic training data saved to {csv_data_path}")
    
    # Define features and targets
    X = df[["total_attempts", "accuracy", "medium_hard_accuracy", "avg_time_spent", "consistency", "syllabus_coverage"]]
    y_score = df["gate_score"]
    y_rank = df["gate_rank"]
    
    # Train Score Predictor
    X_train, X_test, y_train, y_test = train_test_split(X, y_score, test_size=0.2, random_state=42)
    score_model = RandomForestRegressor(n_estimators=120, max_depth=12, random_state=42)
    score_model.fit(X_train, y_train)
    
    # Evaluate Score Predictor
    preds = score_model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    print(f"Score Model trained. R2: {r2:.4f}, RMSE: {rmse:.2f}")
    
    # Save Score Model
    with open(score_model_path, 'wb') as f:
        pickle.dump(score_model, f)
    print(f"Saved score model to {score_model_path}")
    
    # Train Rank Predictor (predict rank directly using predicted score)
    # We will use predicted score as feature for Rank model to maintain tight connection!
    X_rank_feat = df[["gate_score"]]
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_rank_feat, y_rank, test_size=0.2, random_state=42)
    
    rank_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    rank_model.fit(X_train_r, y_train_r)
    
    # Evaluate Rank Predictor
    preds_r = rank_model.predict(X_test_r)
    r2_r = r2_score(y_test_r, preds_r)
    print(f"Rank Model trained. R2: {r2_r:.4f}")
    
    # Save Rank Model
    with open(rank_model_path, 'wb') as f:
        pickle.dump(rank_model, f)
    print(f"Saved rank model to {rank_model_path}")

if __name__ == '__main__':
    train_and_save_models()
