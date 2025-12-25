"""
Database Connection Manager for Supabase PostgreSQL
"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()


class DatabaseConnection:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.conn = None
        
    def connect(self):
        """Establish connection to database."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            print("Successfully connected to Supabase database")
            return self.conn
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return None
    
    def execute_query(self, query, params=None, fetch=True):
        """
        Execute a SQL query.
        
        Parameters:
        -----------
        query : str
            SQL query to execute
        params : tuple, optional
            Query parameters
        fetch : bool, default=True
            Whether to fetch results
            
        Returns:
        --------
        results : list of dicts or None
        """
        if not self.conn:
            self.connect()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                self.conn.commit()  #Always commit
                
                if fetch:
                    results = cur.fetchall()
                    return results
                else:
                    return None
                    
        except Exception as e:
            print(f"Query error: {e}")
            self.conn.rollback()
            return None
    
    def insert_developer(self, developer_data):
        """
        Insert a developer into the database.
        
        Parameters:
        -----------
        developer_data : dict
            Developer information
        """
        query = """
        INSERT INTO developers (
            github_username, name, bio, location, company,
            public_repos, followers, total_stars,
            language_score, stars_per_repo, commit_recency_days,
            code_quality_score, code_complexity_score, bio_relevance_score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (github_username) DO UPDATE SET
            name = EXCLUDED.name,
            bio = EXCLUDED.bio,
            total_stars = EXCLUDED.total_stars,
            public_repos = EXCLUDED.public_repos,
            last_updated = CURRENT_TIMESTAMP
        RETURNING developer_id;
        """
        
        params = (
            developer_data.get('github_username'),
            developer_data.get('name'),
            developer_data.get('bio'),
            developer_data.get('location'),
            developer_data.get('company'),
            developer_data.get('public_repos', 0),
            developer_data.get('followers', 0),
            developer_data.get('total_stars', 0),
            developer_data.get('language_score', 0),
            developer_data.get('stars_per_repo', 0),
            developer_data.get('commit_recency_days', 999),
            developer_data.get('code_quality_score', 0),
            developer_data.get('code_complexity_score', 0),
            developer_data.get('bio_relevance_score', 0)
        )
        
        if not self.conn:
            self.connect()
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                self.conn.commit()  #Commit the transaction
                dev_id = cur.fetchone()[0]
                return dev_id
        except Exception as e:
            print(f"Insert error: {e}")
            self.conn.rollback()
            return None
    
    def get_all_developers(self, limit=100):
        """Get all developers from database."""
        query = """
        SELECT * FROM developers
        ORDER BY total_stars DESC
        LIMIT %s;
        """
        return self.execute_query(query, (limit,))
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print(" Database connection closed")


# Test connection
if __name__ == "__main__":
    print("Testing Supabase connection...")
    
    db = DatabaseConnection()
    db.connect()
    
    # Test query
    print("\nTesting query...")
    result = db.execute_query("SELECT COUNT(*) as count FROM developers;")
    if result:
        print(f"Developers in database: {result[0]['count']}")
    
    # Test insert
    print("\nTesting insert...")
    test_dev = {
        'github_username': 'test_user_' + str(int(time.time()) if 'time' in dir() else '123'),
        'name': 'Test User',
        'bio': 'Test bio',
        'total_stars': 100,
        'public_repos': 10,
        'language_score': 5,
        'stars_per_repo': 10,
        'commit_recency_days': 30,
        'code_quality_score': 75,
        'code_complexity_score': 12,
        'bio_relevance_score': 3
    }
    
    dev_id = db.insert_developer(test_dev)
    if dev_id:
        print(f" Successfully inserted test developer with ID: {dev_id}")
    
    # Query again
    result = db.execute_query("SELECT COUNT(*) as count FROM developers;")
    if result:
        print(f"Developers in database now: {result[0]['count']}")
    
    db.close()