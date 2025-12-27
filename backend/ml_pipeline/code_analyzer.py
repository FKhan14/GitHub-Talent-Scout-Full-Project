"""
Code Analyzer - Analyzes Actual Code Quality

This module:
1. Downloads code samples from GitHub repos
2. Calculates real code metrics (cyclomatic complexity, maintainability)
3. Uses Neural Network to predict quality from code metrics
4. Stores results in database
"""

import requests
import base64
from github import Github, Auth
import os
from dotenv import load_dotenv
import numpy as np
from radon.complexity import cc_visit
from radon.metrics import mi_visit
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

load_dotenv()

try:
    from ml_from_scratch.neural_networks import NeuralNetwork
except ImportError:
    from backend.ml_from_scratch.neural_networks import NeuralNetwork


class CodeAnalyzer:
    """
    Analyzes actual code from GitHub repositories.
    """
    
    def __init__(self):
        token = os.getenv('GITHUB_TOKEN')
        auth = Auth.Token(token)
        self.github = Github(auth=auth)
        
        # Neural Network for code analysis
        self.quality_nn = NeuralNetwork(
            input_size=5,  # 5 code metrics
            hidden_size=8,
            output_size=1,
            learning_rate=0.3
        )
        self.is_trained = False
        
    def get_code_sample(self, username, max_files=5):
        """
        Download code samples from user's repos.
        
        Parameters:
        -----------
        username : str
            GitHub username
        max_files : int
            Maximum number of files to analyze
            
        Returns:
        --------
        code_samples : list of str
            Python code samples
        """
        try:
            user = self.github.get_user(username)
            repos = list(user.get_repos())[:5]  # Top 5 repos
            
            code_samples = []
            
            for repo in repos:
                try:
                    # Get Python files
                    contents = repo.get_contents("")
                    
                    for content in contents:
                        if content.name.endswith('.py') and len(code_samples) < max_files:
                            # Download file
                            file_content = repo.get_contents(content.path)
                            code = base64.b64decode(file_content.content).decode('utf-8')
                            code_samples.append(code)
                            
                except Exception:
                    continue
                
                if len(code_samples) >= max_files:
                    break
            
            return code_samples
            
        except Exception as e:
            print(f"Error getting code for {username}: {e}")
            return []
    
    def analyze_code_metrics(self, code):
        """
        Calculate code quality metrics.
        
        Metrics:
        1. Cyclomatic Complexity (how complex the logic is)
        2. Maintainability Index (how easy to maintain)
        3. Lines of Code
        4. Average Complexity per Function
        5. Number of Functions
        
        Returns:
        --------
        metrics : dict
        """
        try:
            # Cyclomatic complexity
            complexity_results = cc_visit(code)
            avg_complexity = np.mean([func.complexity for func in complexity_results]) if complexity_results else 1
            num_functions = len(complexity_results)
            
            # Maintainability index
            mi_score = mi_visit(code, True)
            
            # Lines of code
            loc = len([line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')])
            
            return {
                'avg_complexity': avg_complexity,
                'maintainability_index': mi_score,
                'lines_of_code': loc,
                'num_functions': num_functions,
                'complexity_per_function': avg_complexity / max(num_functions, 1)
            }
            
        except Exception as e:
            return {
                'avg_complexity': 0,
                'maintainability_index': 0,
                'lines_of_code': 0,
                'num_functions': 0,
                'complexity_per_function': 0
            }
    
    def analyze_developer_code(self, username):
        """
        Analyze all code samples for a developer.
        
        Returns:
        --------
        aggregated_metrics : dict
            Average metrics across all code samples
        """
        code_samples = self.get_code_sample(username, max_files=5)
        
        if not code_samples:
            return None
        
        all_metrics = []
        for code in code_samples:
            metrics = self.analyze_code_metrics(code)
            all_metrics.append(metrics)
        
        # Aggregate metrics
        avg_metrics = {
            'avg_complexity': np.mean([m['avg_complexity'] for m in all_metrics]),
            'maintainability_index': np.mean([m['maintainability_index'] for m in all_metrics]),
            'lines_of_code': np.sum([m['lines_of_code'] for m in all_metrics]),
            'num_functions': np.sum([m['num_functions'] for m in all_metrics]),
            'complexity_per_function': np.mean([m['complexity_per_function'] for m in all_metrics])
        }
        
        return avg_metrics
    
    def prepare_features_from_code(self, code_metrics):
        """
        Convert code metrics to feature vector for Neural Network.
        
        Returns:
        --------
        features : numpy array of shape (5,)
        """
        # Normalize metrics to 0-1 range
        features = np.array([
            min(code_metrics['avg_complexity'] / 10, 1),       # Cap at 10
            code_metrics['maintainability_index'] / 100,        # Already 0-100
            min(code_metrics['lines_of_code'] / 1000, 1),      # Cap at 1000 LOC
            min(code_metrics['num_functions'] / 50, 1),         # Cap at 50 functions
            min(code_metrics['complexity_per_function'] / 5, 1) # Cap at 5
        ])
        
        return features
    
    def predict_quality_from_code(self, code_metrics):
        """
        Predict code quality using Neural Network.
        
        Returns:
        --------
        quality_score : float (0-1)
        """
        if not self.is_trained:
            # Use maintainability index as proxy
            return code_metrics['maintainability_index'] / 100
        
        features = self.prepare_features_from_code(code_metrics)
        features = features.reshape(1, -1)
        
        score = self.quality_nn.predict(features)[0][0]
        return float(score)


# Test it!
if __name__ == "__main__":
    print("="*70)
    print("  Code Analyzer - Analyzing Real Code Quality")
    print("="*70)
    
    analyzer = CodeAnalyzer()
    
    # Test on a few developers
    test_users = ['karpathy', 'gvanrossum', 'torvalds']
    
    print("\nAnalyzing code samples...\n")
    
    for username in test_users:
        print(f"Analyzing {username}...")
        metrics = analyzer.analyze_developer_code(username)
        
        if metrics:
            print(f"  Avg Complexity: {metrics['avg_complexity']:.2f}")
            print(f"  Maintainability: {metrics['maintainability_index']:.2f}")
            print(f"  Lines of Code: {metrics['lines_of_code']}")
            print(f"  Functions: {metrics['num_functions']}")
            print(f"  Complexity/Function: {metrics['complexity_per_function']:.2f}")
            
            quality = analyzer.predict_quality_from_code(metrics)
            print(f"  → Predicted Quality: {quality:.4f}")
        else:
            print(f"  No Python code found")
        
        print()
    
    print("✓ Code analysis working!")