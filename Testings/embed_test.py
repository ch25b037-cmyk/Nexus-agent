# test_embed.py
from app.services.embedding import get_embedding

vector = get_embedding("Junior Python and Backend Developer", task_type="RETRIEVAL_QUERY")
print(f"Success! Generated vector with dimension: {len(vector)}")
print(f"Sample values (first 5 numbers): {vector[:5]}")