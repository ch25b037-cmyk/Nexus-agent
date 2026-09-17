# app/services/embedding.py
import os
from typing import List
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("[!] GEMINI_API_KEY is not set in .env")

client = genai.Client(api_key=api_key)

# The active model replacing text-embedding-004
EMBEDDING_MODEL = "gemini-embedding-001"


def get_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
    """
    Generates a 768-dimensional vector embedding using gemini-embedding-001
    scaled down with Matryoshka Representation Learning (output_dimensionality=768).
    """
    clean_text = " ".join(text.split())[:8000]

    config = types.EmbedContentConfig(
        task_type=task_type,
        output_dimensionality=768  # Projects down to 768 to fit our pgvector column
    )

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=clean_text,
        config=config
    )

    return response.embeddings[0].values