"""
GitHub Talent Scout - Production Frontend

Uses FastAPI backend for searching 927+ developers
"""

import streamlit as st
import requests
import os

# API URL (change if needed)
API_URL = os.getenv("API_URL", "http://localhost:8000")


def main():
    st.set_page_config(
        page_title="GitHub Talent Scout", 
        page_icon="", 
        layout="wide"
    )
    
    # Header
    st.title("GitHub Talent Scout")
    st.markdown("Search 927+ developers using ML-powered matching")
    
    # Get stats from API
    try:
        stats = requests.get(f"{API_URL}/stats").json()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Developers", f"{stats['total_developers']:,}")
        col2.metric("Avg Quality Score", f"{stats['average_quality_score']:.2f}")
        col3.metric("Advanced Developers", stats['complexity_distribution'].get('3', 0))
    except:
        st.warning("Could not load stats. Make sure API is running on http://localhost:8000")
    
    st.divider()
    
    # Job description input
    st.subheader("Job Description")
    job_description = st.text_area(
        "Describe the role you're hiring for:",
        "Looking for a senior Python machine learning engineer with experience in deep learning frameworks like PyTorch or TensorFlow. Should have strong open-source contributions and active GitHub presence.",
        height=150
    )
    
    # Search parameters
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**Search Settings**")
    
    with col2:
        limit = st.number_input("Results", min_value=5, max_value=50, value=10)
    
    # Search button
    if st.button("Search Developers", type="primary", use_container_width=True):
        
        with st.spinner("Searching with vector similarity..."):
            try:
                # Call API
                response = requests.post(
                    f"{API_URL}/search",
                    json={
                        "job_description": job_description,
                        "limit": limit
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if not results:
                        st.warning("No results found. Try a different description.")
                        return
                    
                    st.success(f" Found {len(results)} matching developers!")
                    st.divider()
                    
                    # Show top match
                    st.subheader("Best Match")
                    top = results[0]
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"### [{top['github_username']}]({top['github_url']})")
                        if top['name']:
                            st.caption(f"Name: {top['name']}")
                        if top['bio']:
                            st.write(top['bio'])
                    
                    with col2:
                        st.metric("Match Score", f"{top['similarity_score']:.1%}")
                        st.metric("Quality", f"{top['quality_score']:.2f}")
                    
                    with col3:
                        st.metric("Stars", f"{top['total_stars']:,}")
                        complexity_names = {0: "Simple", 1: "Medium", 2: "Complex", 3: "Advanced"}
                        st.metric("Complexity", complexity_names.get(top['complexity_level'], "Unknown"))
                    
                    st.divider()
                    
                    # All results
                    st.subheader("All Results")
                    
                    for rank, dev in enumerate(results, 1):
                        with st.container():
                            col1, col2, col3, col4 = st.columns([1, 4, 2, 2])
                            
                            with col1:
                                if rank <= 3:
                                    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                                    st.markdown(medals[rank])
                                else:
                                    st.markdown(f"**#{rank}**")
                            
                            with col2:
                                st.markdown(f"**[{dev['github_username']}]({dev['github_url']})**")
                                if dev['bio']:
                                    st.caption(dev['bio'][:100] + "..." if len(dev['bio']) > 100 else dev['bio'])
                            
                            with col3:
                                st.metric("Match", f"{dev['similarity_score']:.1%}")
                                st.caption(f"Quality: {dev['quality_score']:.2f}")
                            
                            with col4:
                                st.metric("Stars", f"{dev['total_stars']:,}")
                                st.caption(f"Repos: {dev['public_repos']}")
                            
                            # Expandable details
                            with st.expander(f"View {dev['github_username']}'s Details"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**Profile**")
                                    st.write(f"Name: {dev['name'] or 'N/A'}")
                                    st.write(f"Followers: {dev['followers']:,}")
                                    st.write(f"Public Repos: {dev['public_repos']}")
                                
                                with col2:
                                    st.write("**ML Scores**")
                                    st.write(f"Quality Score: {dev['quality_score']:.2f}")
                                    complexity_names = {0: "Simple", 1: "Medium", 2: "Complex", 3: "Advanced"}
                                    st.write(f"Complexity: {complexity_names.get(dev['complexity_level'], 'Unknown')}")
                                    st.write(f"Similarity: {dev['similarity_score']:.1%}")
                            
                            st.divider()
                
                else:
                    st.error(f"Search failed: {response.status_code}")
                    st.write(response.text)
            
            except Exception as e:
                st.error(f"Error connecting to API: {str(e)}")
                st.info("Make sure the API is running: `python backend/api/main.py`")


if __name__ == "__main__":
    main()