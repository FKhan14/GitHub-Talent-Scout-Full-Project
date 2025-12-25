"""
Embedding Generator - Create Vector Embeddings for Developers

Uses HuggingFace sentence-transformers to create 384-dimensional embeddings
that will be stored in Pgvector for fast similarity search.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.db_connection import DatabaseConnection


class EmbeddingGenerator:
    """Generate embeddings using HuggingFace."""
    
    def __init__(self):
        print("Loading HuggingFace model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print(" Model loaded (384 dimensions)")
        
    def create_profile_text(self, developer_data):
        """
        Create text representation of developer profile.
        
        Combines: name, bio, languages, and stats into searchable text.
        """
        parts = []
        
        if developer_data.get('name'):
            parts.append(f"Name: {developer_data['name']}")
        
        if developer_data.get('bio'):
            parts.append(f"Bio: {developer_data['bio']}")
        
        parts.append(f"Username: {developer_data['github_username']}")
        
        if developer_data.get('location'):
            parts.append(f"Location: {developer_data['location']}")
        
        if developer_data.get('company'):
            parts.append(f"Company: {developer_data['company']}")
        
        # Add stats
        parts.append(f"{developer_data.get('public_repos', 0)} repositories")
        parts.append(f"{developer_data.get('total_stars', 0)} total stars")
        parts.append(f"{developer_data.get('followers', 0)} followers")
        
        text = ". ".join(parts)
        return text
    
    def generate_embedding(self, text):
        """
        Generate embedding for text.
        
        Returns:
        --------
        embedding : numpy array of shape (384,)
        """
        embedding = self.model.encode(text)
        return embedding
    
    def generate_for_developer(self, developer_data):
        """
        Generate embedding for a developer profile.
        
        Returns:
        --------
        embedding : numpy array of shape (384,)
        """
        text = self.create_profile_text(developer_data)
        return self.generate_embedding(text)
    
    def batch_generate(self, developers_list, show_progress=True):
        """
        Generate embeddings for multiple developers.
        
        Returns:
        --------
        embeddings : list of numpy arrays
        """
        texts = [self.create_profile_text(dev) for dev in developers_list]
        
        if show_progress:
            print(f"Generating embeddings for {len(texts)} developers...")
        
        embeddings = self.model.encode(texts, show_progress_bar=show_progress)
        
        if show_progress:
            print(f" Generated {len(embeddings)} embeddings")
        
        return embeddings


def update_database_with_embeddings():
    """Generate and store embeddings for all developers."""
    
    print("="*70)
    print("  Generating Embeddings for All Developers")
    print("="*70)
    
    # Connect to database
    db = DatabaseConnection()
    db.connect()
    
    # Get all developers
    print("\nFetching developers...")
    developers = db.execute_query("SELECT * FROM developers;")
    print(f" Fetched {len(developers)} developers")
    
    # Generate embeddings
    print("\nGenerating embeddings with HuggingFace...")
    generator = EmbeddingGenerator()
    embeddings = generator.batch_generate(developers)
    
    # Update database
    print("\n" + "="*70)
    print("  Storing Embeddings in Pgvector")
    print("="*70)
    
    for i, (dev, embedding) in enumerate(zip(developers, embeddings), 1):
        # Convert numpy array to list for PostgreSQL
        embedding_list = embedding.tolist()
        
        update_query = """
        UPDATE developers 
        SET combined_embedding = %s
        WHERE developer_id = %s;
        """
        
        db.execute_query(update_query, (embedding_list, dev['developer_id']), fetch=False)
        
        if i % 100 == 0:
            print(f"  Stored {i}/{len(developers)} embeddings...")
    
    print(f"✓ Stored all {len(developers)} embeddings in Pgvector!")
    
    # Verify
    print("\n" + "="*70)
    print("  Verification")
    print("="*70)
    
    result = db.execute_query("""
        SELECT COUNT(*) as count 
        FROM developers 
        WHERE combined_embedding IS NOT NULL;
    """)
    
    print(f"Developers with embeddings: {result[0]['count']}")
    
    # Test similarity search
    print("\nTesting vector similarity search...")
    test_query = "Python machine learning engineer"
    query_embedding = generator.generate_embedding(test_query)
    
    # Convert to string format for pgvector
    embedding_str = '[' + ','.join(map(str, query_embedding.tolist())) + ']'
    
    search_query = """
    SELECT github_username, total_stars,
           1 - (combined_embedding <=> %s::vector) AS similarity
    FROM developers
    WHERE combined_embedding IS NOT NULL
    ORDER BY combined_embedding <=> %s::vector
    LIMIT 5;
    """
    
    results = db.execute_query(search_query, (embedding_str, embedding_str))
    
    if results:
        print(f"\nTop 5 matches for '{test_query}':")
        for r in results:
            print(f"  {r['github_username']:20s} - Similarity: {r['similarity']:.4f}")
    else:
        print("Vector search query failed")
    
    db.close()
    
    print("\n" + "="*70)
    print("   EMBEDDINGS COMPLETE! Pgvector Ready for Search!")
    print("="*70)


if __name__ == "__main__":
    update_database_with_embeddings()