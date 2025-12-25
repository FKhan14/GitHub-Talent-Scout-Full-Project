"""
Complexity Predictor - Uses  Random Forest from Scratch

Predicts project complexity level:
- 0: Simple (small personal projects)
- 1: Medium (production apps, libraries)
- 2: Complex (frameworks, large systems)
- 3: Advanced (infrastructure, compilers, ML frameworks)
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import Random Forest
try:
    from ml_from_scratch.ensemble import RandomForestClassifier
except ImportError:
    from backend.ml_from_scratch.ensemble import RandomForestClassifier


class ComplexityPredictor:
    """
    Predicts project complexity using Random Forest.
    """
    
    def __init__(self):
        #  Random Forest from scratch
        self.rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        self.is_trained = False
        
    def prepare_features(self, developer_data):
        """
        Extract features for complexity prediction.
        
        Features:
        - Total stars (popularity indicator)
        - Public repos (portfolio size)
        - Followers (community impact)
        - Stars per repo (project quality)
        - Language score (tech diversity)
        """
        features = np.array([
            developer_data.get('total_stars', 0),
            developer_data.get('public_repos', 0),
            developer_data.get('followers', 0),
            developer_data.get('stars_per_repo', 0),
            developer_data.get('language_score', 0)
        ])
        
        return features
    
    def create_complexity_label(self, developer_data):
        """
        Create complexity label based on metrics.
        
        0: Simple (stars < 1000, repos < 10)
        1: Medium (stars < 10000, repos < 50)
        2: Complex (stars < 100000, repos < 100)
        3: Advanced (stars >= 100000 or repos >= 100)
        """
        total_stars = developer_data.get('total_stars', 0)
        public_repos = developer_data.get('public_repos', 0)
        
        if total_stars >= 100000 or public_repos >= 100:
            return 3  # Advanced
        elif total_stars >= 10000 or public_repos >= 50:
            return 2  # Complex
        elif total_stars >= 1000 or public_repos >= 10:
            return 1  # Medium
        else:
            return 0  # Simple
    
    def train_on_data(self, developers_list):
        """
        Train Random Forest on developer data.
        
        Parameters:
        -----------
        developers_list : list of dicts
            Developer data from database
        """
        if len(developers_list) < 20:
            print("Not enough data to train. Need at least 20 developers.")
            return
        
        # Prepare training data
        X = []
        y = []
        
        for dev in developers_list:
            features = self.prepare_features(dev)
            label = self.create_complexity_label(dev)
            
            X.append(features)
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Training Random Forest on {len(X)} developers...")
        print(f"  Input features: {X.shape}")
        print(f"  Complexity classes: {len(np.unique(y))} (0=Simple, 1=Medium, 2=Complex, 3=Advanced)")
        
        # Count distribution
        unique, counts = np.unique(y, return_counts=True)
        for cls, count in zip(unique, counts):
            class_names = ['Simple', 'Medium', 'Complex', 'Advanced']
            print(f"    Class {cls} ({class_names[cls]}): {count} developers")
        
        # Train Random Forest
        self.rf.fit(X, y)
        self.is_trained = True
        
        # Test accuracy
        predictions = self.rf.predict(X)
        accuracy = (predictions == y).mean()
        print(f"  Training accuracy: {accuracy:.2%}")
        print(" Random Forest training complete!")
    
    def predict_complexity(self, developer_data):
        """
        Predict complexity level for a developer.
        
        Parameters:
        -----------
        developer_data : dict
            Developer data
            
        Returns:
        --------
        complexity : int
            0=Simple, 1=Medium, 2=Complex, 3=Advanced
        """
        if not self.is_trained:
            # If not trained, use heuristic
            return self.create_complexity_label(developer_data)
        
        features = self.prepare_features(developer_data).reshape(1, -1)
        complexity = self.rf.predict(features)[0]
        return int(complexity)
    
    def batch_predict(self, developers_list):
        """
        Predict complexity for multiple developers.
        
        Returns:
        --------
        scores : list of ints
        """
        scores = []
        for dev in developers_list:
            score = self.predict_complexity(dev)
            scores.append(score)
        return scores
    
    def get_complexity_name(self, complexity_level):
        """Get human-readable name for complexity level."""
        names = {
            0: "Simple",
            1: "Medium",
            2: "Complex",
            3: "Advanced"
        }
        return names.get(complexity_level, "Unknown")


# Test it
if __name__ == "__main__":
    from backend.database.db_connection import DatabaseConnection
    
    print("="*60)
    print("  Complexity Predictor Random Forest")
    print("="*60)
    
    # Get developers
    db = DatabaseConnection()
    db.connect()
    
    developers = db.get_all_developers(limit=200)
    print(f"\nFetched {len(developers)} developers from database")
    
    # Train the model
    predictor = ComplexityPredictor()
    predictor.train_on_data(developers)
    
    # Test predictions
    print("\n" + "="*60)
    print("  Predictions on Sample Developers")
    print("="*60)
    
    sample_devs = developers[:15]
    for dev in sample_devs:
        complexity = predictor.predict_complexity(dev)
        complexity_name = predictor.get_complexity_name(complexity)
        print(f"{dev['github_username']:20s} - Complexity: {complexity} ({complexity_name:8s}) | Stars: {dev['total_stars']:>8,} | Repos: {dev['public_repos']:>4}")
    
    db.close()
    
    print("\n Complexity Predictor working with Random Forest!")
    