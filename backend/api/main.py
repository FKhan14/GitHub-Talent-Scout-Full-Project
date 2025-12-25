"""
FastAPI Backend for GitHub Talent Scout

Endpoints:
- POST /search - Search developers by job description
- GET /developer/{username} - Get developer details
- GET /stats - Get database statistics
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.db_connection import DatabaseConnection
from backend.ml_pipeline.embedding_generator import EmbeddingGenerator

app = FastAPI(title="GitHub Talent Scout API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = DatabaseConnection()
embedding_gen = EmbeddingGenerator()


class SearchRequest(BaseModel):
    job_description: str
    limit: int = 10


class DeveloperResponse(BaseModel):
    github_username: str
    name: Optional[str]
    bio: Optional[str]
    total_stars: int
    public_repos: int
    followers: int
    quality_score: float
    complexity_level: int
    similarity_score: float


@app.on_event("startup")
async def startup():
    """Connect to database on startup."""
    db.connect()
    print("✓ API started and connected to database")


@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown."""
    db.close()
    print("✓ API shutdown")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "GitHub Talent Scout API",
        "version": "1.0.0",
        "endpoints": {
            "search": "POST /search",
            "developer": "GET /developer/{username}",
            "stats": "GET /stats"
        }
    }


@app.get("/stats")
async def get_stats():
    """Get database statistics."""
    total = db.execute_query("SELECT COUNT(*) as count FROM developers;")
    
    avg_quality = db.execute_query("""
        SELECT AVG(neural_network_quality_score) as avg_quality
        FROM developers
        WHERE neural_network_quality_score IS NOT NULL;
    """)
    
    complexity_dist = db.execute_query("""
        SELECT random_forest_complexity_score as complexity, COUNT(*) as count
        FROM developers
        WHERE random_forest_complexity_score IS NOT NULL
        GROUP BY random_forest_complexity_score
        ORDER BY complexity;
    """)
    
    return {
        "total_developers": total[0]['count'],
        "average_quality_score": float(avg_quality[0]['avg_quality']) if avg_quality[0]['avg_quality'] else 0,
        "complexity_distribution": {
            int(row['complexity']): row['count'] 
            for row in complexity_dist
        }
    }


@app.get("/developer/{username}")
async def get_developer(username: str):
    """Get developer details by username."""
    result = db.execute_query(
        "SELECT * FROM developers WHERE github_username = %s;",
        (username,)
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Developer not found")
    
    dev = result[0]
    
    return {
        "github_username": dev['github_username'],
        "name": dev['name'],
        "bio": dev['bio'],
        "location": dev['location'],
        "company": dev['company'],
        "public_repos": dev['public_repos'],
        "followers": dev['followers'],
        "total_stars": dev['total_stars'],
        "stars_per_repo": float(dev['stars_per_repo']) if dev['stars_per_repo'] else 0,
        "quality_score": float(dev['neural_network_quality_score']) if dev['neural_network_quality_score'] else 0,
        "complexity_level": int(dev['random_forest_complexity_score']) if dev['random_forest_complexity_score'] else 0,
        "github_url": f"https://github.com/{dev['github_username']}"
    }


@app.post("/search")
async def search_developers(request: SearchRequest):
    """
    Search developers using vector similarity.
    
    Uses Pgvector for fast semantic search based on job description.
    """
    # Generate embedding for job description
    job_embedding = embedding_gen.generate_embedding(request.job_description)
    
    # Convert to string format for pgvector
    embedding_str = '[' + ','.join(map(str, job_embedding.tolist())) + ']'
    
    # Vector similarity search
    search_query = """
    SELECT 
        github_username,
        name,
        bio,
        total_stars,
        public_repos,
        followers,
        neural_network_quality_score as quality_score,
        random_forest_complexity_score as complexity_level,
        1 - (combined_embedding <=> %s::vector) AS similarity_score
    FROM developers
    WHERE combined_embedding IS NOT NULL
    ORDER BY combined_embedding <=> %s::vector
    LIMIT %s;
    """
    
    results = db.execute_query(search_query, (embedding_str, embedding_str, request.limit))
    
    if not results:
        return {"results": [], "count": 0}
    
    # Format results
    developers = []
    for r in results:
        developers.append({
            "github_username": r['github_username'],
            "name": r['name'],
            "bio": r['bio'],
            "total_stars": r['total_stars'],
            "public_repos": r['public_repos'],
            "followers": r['followers'],
            "quality_score": float(r['quality_score']) if r['quality_score'] else 0,
            "complexity_level": int(r['complexity_level']) if r['complexity_level'] else 0,
            "similarity_score": float(r['similarity_score']),
            "github_url": f"https://github.com/{r['github_username']}"
        })
    
    return {
        "job_description": request.job_description,
        "results": developers,
        "count": len(developers)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)