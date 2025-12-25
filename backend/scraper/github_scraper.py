"""
GitHub Profile Scraper - Collect 100K+ Developer Profiles
"""

import time
from github import Github, Auth
from dotenv import load_dotenv
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from datetime import datetime
from backend.database.db_connection import DatabaseConnection

load_dotenv()


class GitHubScraper:
    def __init__(self):
        token = os.getenv('GITHUB_TOKEN')
        auth = Auth.Token(token)
        self.github = Github(auth=auth)
        self.db = DatabaseConnection()
        self.db.connect()
        
    def scrape_developers(self, query, max_users=10):
        """
        Scrape developers matching a search query.
        
        Parameters:
        -----------
        query : str
            GitHub search query (e.g., "language:Python followers:>100")
        max_users : int
            Maximum number of users to scrape
        """
        print(f"Searching: {query}")
        users = self.github.search_users(query)
        
        count = 0
        
        for user in users:
            # Add max_users limit
            if count >= max_users:
                break
            
            try:
                # Get full user data
                full_user = self.github.get_user(user.login)
                
                #Calculate total stars
                total_stars = 0
                repos = full_user.get_repos()
                for repo in repos:
                    total_stars += repo.stargazers_count
                
                # Calculate feature scores (simple version for now)
                stars_per_repo = total_stars / full_user.public_repos if full_user.public_repos > 0 else 0
                
                # Extract profile data
                dev_data = {
                    'github_username': full_user.login,
                    'name': full_user.name,
                    'bio': full_user.bio,
                    'location': full_user.location,
                    'company': full_user.company,
                    'public_repos': full_user.public_repos,
                    'followers': full_user.followers,
                    'total_stars': total_stars,
                    'stars_per_repo': stars_per_repo,
                    'language_score': 0,  
                    'commit_recency_days': 999,  
                    'code_quality_score': 0,  
                    'code_complexity_score': 0,  
                    'bio_relevance_score': 0,  
                }
                
                # Store in database
                dev_id = self.db.insert_developer(dev_data)
                
                #Progress feedback
                count += 1
                print(f"   [{count}/{max_users}] Inserted {full_user.login} (ID: {dev_id}, Stars: {total_stars})")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                #Error handling
                print(f"   Error with {user.login}: {e}")
                continue
        
        print(f"\n Scraping complete! Collected {count} developers.")


if __name__ == "__main__":
    scraper = GitHubScraper()
    
    print("="*60)
    print("  GitHub Scraper - Collecting 1,000 Developers")
    print("="*60)
    print("\nThis will take approximately 2-3 hours...")
    print("Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("\n")
    
    queries = [
        ("language:Python followers:>50", 200),
        ("language:JavaScript followers:>50", 200),
        ("language:TypeScript followers:>50", 100),
        ("language:Java followers:>50", 100),
        ("language:Go followers:>50", 100),
        ("language:Rust followers:>50", 100),
        ("language:C++ followers:>50", 100),
        ("repos:>10 followers:>20", 100),
    ]
    
    total = 0
    for i, (query, max_users) in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}/{len(queries)}: {query}")
        print(f"Target: {max_users} developers")
        print(f"{'='*60}")
        
        try:
            scraper.scrape_developers(query, max_users=max_users)
        except KeyboardInterrupt:
            print("\n\nScraping interrupted by user!")
            break
        except Exception as e:
            print(f"Error with query: {e}")
            continue
        
        result = scraper.db.execute_query("SELECT COUNT(*) as count FROM developers;")
        total = result[0]['count']
        print(f"\n Total developers in database: {total}")
        
        if total >= 1000:
            print("\n Reached 1,000 developers!")
            break
    
    print(f"\n{'='*60}")
    print(f"   Scraping Complete!")
    print(f"  Total Developers: {total}")
    print(f"  Ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    scraper.db.close()