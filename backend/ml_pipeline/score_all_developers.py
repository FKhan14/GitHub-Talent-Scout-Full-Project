"""
Score All Developers - Apply My Custom ML Algorithms to All Data

This script:
1. Loads all developers from database
2. Trains  Neural Network on code quality
3. Trains  Random Forest on complexity
4. Scores all 927 developers
5. Updates database with ML scores
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.db_connection import DatabaseConnection
from backend.ml_pipeline.code_quality_scorer import CodeQualityScorer
from backend.ml_pipeline.complexity_predictor import ComplexityPredictor


def score_all_developers():
    """Score all developers in database with ML algorithms."""
    
    print("="*70)
    print("  Scoring All Developers with ML Algorithms")
    print("="*70)
    
    # Connect to database
    db = DatabaseConnection()
    db.connect()
    
    # Get ALL developers
    print("\nFetching all developers from database...")
    all_developers = db.execute_query("SELECT * FROM developers ORDER BY total_stars DESC;")
    print(f"✓ Fetched {len(all_developers)} developers")
    
    # Train models
    print("\n" + "="*70)
    print("  Training Neural Network (Code Quality)")
    print("="*70)
    quality_scorer = CodeQualityScorer()
    quality_scorer.train_on_data(all_developers)
    
    print("\n" + "="*70)
    print("  Training Random Forest (Complexity)")
    print("="*70)
    complexity_predictor = ComplexityPredictor()
    complexity_predictor.train_on_data(all_developers)
    
    # Score all developers
    print("\n" + "="*70)
    print("  Scoring All Developers")
    print("="*70)
    
    for i, dev in enumerate(all_developers, 1):
        # Predict using algorithms
        quality_score = quality_scorer.predict_quality(dev)
        complexity_level = complexity_predictor.predict_complexity(dev)
        
        # Update database
        update_query = """
        UPDATE developers 
        SET neural_network_quality_score = %s,
            random_forest_complexity_score = %s
        WHERE developer_id = %s;
        """
        
        db.execute_query(update_query, (
            float(quality_score),
            float(complexity_level),
            dev['developer_id']
        ), fetch=False)
        
        if i % 50 == 0:
            print(f"  Scored {i}/{len(all_developers)} developers...")
    
    print(f" Scored all {len(all_developers)} developers!")
    
    # Verify updates
    print("\n" + "="*70)
    print("  Verification - Top 10 with ML Scores")
    print("="*70)
    
    top_10 = db.execute_query("""
        SELECT github_username, total_stars, 
               neural_network_quality_score, 
               random_forest_complexity_score
        FROM developers 
        WHERE neural_network_quality_score IS NOT NULL
        ORDER BY total_stars DESC 
        LIMIT 10;
    """)
    
    complexity_names = {0: "Simple", 1: "Medium", 2: "Complex", 3: "Advanced"}
    
    for dev in top_10:
        complexity_name = complexity_names.get(int(dev['random_forest_complexity_score']), "Unknown")
        print(f"{dev['github_username']:20s} | Quality: {dev['neural_network_quality_score']:.4f} | Complexity: {complexity_name}")
    
    db.close()
    
    print("\n" + "="*70)
    print("  ALL DEVELOPERS SCORED ")
    print("="*70)


if __name__ == "__main__":
    score_all_developers()