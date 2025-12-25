"""
Quality Predictor - Uses My Custom Built Random Forest for Code Quality

Predicts code quality level:
- 0: Low Quality
- 1: Medium Quality
- 2: High Quality
- 3: Excellent Quality
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from ml_from_scratch.ensemble import RandomForestClassifier
except ImportError:
    from backend.ml_from_scratch.ensemble import RandomForestClassifier


class QualityPredictorRF:
    """Predicts code quality using Random Forest."""
    
    def __init__(self):
        self.rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        self.is_trained = False
        
    def prepare_features(self, developer_data):
        """Extract features for quality prediction."""
        features = np.array([
            developer_data.get('stars_per_repo', 0),
            developer_data.get('followers', 0),
            developer_data.get('public_repos', 0),
            developer_data.get('language_score', 0),
            developer_data.get('bio_relevance_score', 0),
            999 - developer_data.get('commit_recency_days', 999)  # Invert so recent = high
        ])
        return features
    
    def create_quality_label(self, developer_data):
        """
        Create quality label based on stars per repo.
        
        0: Low (< 10 stars/repo)
        1: Medium (10-50 stars/repo)
        2: High (50-200 stars/repo)
        3: Excellent (>= 200 stars/repo)
        """
        stars_per_repo = developer_data.get('stars_per_repo', 0)
        
        if stars_per_repo >= 200:
            return 3
        elif stars_per_repo >= 50:
            return 2
        elif stars_per_repo >= 10:
            return 1
        else:
            return 0
    
    def train_on_data(self, developers_list):
        """Train Random Forest on developer data."""
        if len(developers_list) < 20:
            print("Not enough data to train.")
            return
        
        X = []
        y = []
        
        for dev in developers_list:
            features = self.prepare_features(dev)
            label = self.create_quality_label(dev)
            X.append(features)
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Training Random Forest on {len(X)} developers...")
        print(f"  Quality classes: {len(np.unique(y))}")
        
        unique, counts = np.unique(y, return_counts=True)
        quality_names = ['Low', 'Medium', 'High', 'Excellent']
        for cls, count in zip(unique, counts):
            print(f"    Class {cls} ({quality_names[cls]:9s}): {count} developers")
        
        self.rf.fit(X, y)
        self.is_trained = True
        
        predictions = self.rf.predict(X)
        accuracy = (predictions == y).mean()
        print(f"  Training accuracy: {accuracy:.2%}")
        print("Quality predictor training complete!")
    
    def predict_quality(self, developer_data):
        """Predict quality level (0-3)."""
        if not self.is_trained:
            return self.create_quality_label(developer_data)
        
        features = self.prepare_features(developer_data).reshape(1, -1)
        quality = self.rf.predict(features)[0]
        return int(quality)
    
    def predict_quality_score(self, developer_data):
        """
        Predict quality as a 0-1 score (for compatibility).
        Maps classes to scores: 0→0.0, 1→0.33, 2→0.67, 3→1.0
        """
        quality_level = self.predict_quality(developer_data)
        score_map = {0: 0.0, 1: 0.33, 2: 0.67, 3: 1.0}
        return score_map[quality_level]


# Test and score all
if __name__ == "__main__":
    from backend.database.db_connection import DatabaseConnection
    
    print("="*70)
    print("  Quality Predictor - Random Forest")
    print("="*70)
    
    db = DatabaseConnection()
    db.connect()
    
    # Get all developers
    developers = db.execute_query("SELECT * FROM developers;")
    print(f"\nFetched {len(developers)} developers")
    
    # Train
    predictor = QualityPredictorRF()
    predictor.train_on_data(developers)
    
    # Score all and update database
    print("\n" + "="*70)
    print("  Updating Database with Quality Scores")
    print("="*70)
    
    for i, dev in enumerate(developers, 1):
        quality_score = predictor.predict_quality_score(dev)
        
        update_query = """
        UPDATE developers 
        SET neural_network_quality_score = %s
        WHERE developer_id = %s;
        """
        
        db.execute_query(update_query, (quality_score, dev['developer_id']), fetch=False)
        
        if i % 100 == 0:
            print(f"  Updated {i}/{len(developers)} developers...")
    
    print(f" Updated all {len(developers)} developers with quality scores!")
    
    # Show results
    print("\n" + "="*70)
    print("  Sample Results")
    print("="*70)
    
    results = db.execute_query("""
        SELECT github_username, total_stars, 
               neural_network_quality_score as quality,
               random_forest_complexity_score as complexity
        FROM developers 
        ORDER BY total_stars DESC 
        LIMIT 15;
    """)
    
    quality_names = {0.0: "Low", 0.33: "Medium", 0.67: "High", 1.0: "Excellent"}
    complexity_names = {0: "Simple", 1: "Medium", 2: "Complex", 3: "Advanced"}
    
    for dev in results:
        quality_name = quality_names.get(dev['quality'], "Unknown")
        complexity_name = complexity_names.get(int(dev['complexity']), "Unknown")
        print(f"{dev['github_username']:20s} | Quality: {quality_name:9s} ({dev['quality']:.2f}) | Complexity: {complexity_name:8s} | Stars: {dev['total_stars']:,}")
    
    db.close()
    print("\nAll developers now have ML scores")