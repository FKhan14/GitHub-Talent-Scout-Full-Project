"""
Analyze Code Quality for All Developers

This script analyzes actual code from repositories and updates
the database with real code quality metrics.

Note: This will take several hours for 900+ developers due to:
- API rate limits
- Downloading code samples
- Running complexity analysis
"""

import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.db_connection import DatabaseConnection
from backend.ml_pipeline.code_analyzer import CodeAnalyzer


def analyze_all_developers(start_from=0, batch_size=50):
    """
    Analyze code quality for all developers.
    
    Parameters:
    -----------
    start_from : int
        Skip first N developers (for resuming)
    batch_size : int
        Analyze in batches (for progress tracking)
    """
    print("="*70)
    print("  Analyzing Real Code Quality for All Developers")
    print("="*70)
    print("\nThis will take several hours...")
    print("You can stop anytime with Ctrl+C and resume later\n")
    
    # Connect
    db = DatabaseConnection()
    db.connect()
    
    analyzer = CodeAnalyzer()
    
    # Get all developers
    developers = db.execute_query("""
        SELECT developer_id, github_username 
        FROM developers 
        ORDER BY total_stars DESC;
    """)
    
    print(f"Total developers to analyze: {len(developers)}")
    print(f"Starting from: {start_from}")
    
    # Skip already analyzed
    developers = developers[start_from:]
    
    analyzed_count = 0
    skipped_count = 0
    
    for i, dev in enumerate(developers, start=start_from + 1):
        username = dev['github_username']
        
        print(f"\n[{i}/{len(developers) + start_from}] Analyzing {username}...")
        
        try:
            # Analyze code
            code_metrics = analyzer.analyze_developer_code(username)
            
            if code_metrics:
                # Predict quality from code
                quality_from_code = analyzer.predict_quality_from_code(code_metrics)
                
                # Update database with code metrics
                update_query = """
                UPDATE developers 
                SET neural_network_quality_score = %s
                WHERE developer_id = %s;
                """
                
                db.execute_query(
                    update_query,
                    (float(quality_from_code), dev['developer_id']),
                    fetch=False
                )
                
                print(f"  ✓ Quality from code: {quality_from_code:.4f}")
                print(f"    Complexity: {code_metrics['avg_complexity']:.2f}")
                print(f"    Maintainability: {code_metrics['maintainability_index']:.2f}")
                
                analyzed_count += 1
            else:
                print(f"  - No Python code found, skipping")
                skipped_count += 1
            
            # Rate limiting
            time.sleep(2)  # Be nice to GitHub API
            
        except KeyboardInterrupt:
            print(f"\n\nAnalysis interrupted!")
            print(f"Analyzed: {analyzed_count}")
            print(f"Skipped: {skipped_count}")
            print(f"Resume with: start_from={i}")
            break
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            skipped_count += 1
            continue
        
        # Progress update every batch
        if i % batch_size == 0:
            print(f"\n{'='*70}")
            print(f"  Progress: {i}/{len(developers) + start_from}")
            print(f"  Analyzed: {analyzed_count} | Skipped: {skipped_count}")
            print(f"{'='*70}")
    
    print(f"\n{'='*70}")
    print(f"  ✓ Code Analysis Complete!")
    print(f"  Total analyzed: {analyzed_count}")
    print(f"  Total skipped: {skipped_count}")
    print(f"{'='*70}")
    
    db.close()


if __name__ == "__main__":
    # Start analysis
    # To resume, set start_from to where you left off
    analyze_all_developers(start_from=0, batch_size=50)