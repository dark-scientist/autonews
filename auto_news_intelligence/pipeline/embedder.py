import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Embedder:
    """Generate SBERT embeddings for articles."""
    
    def __init__(self):
        logger.info("Loading SBERT all-MiniLM-L6-v2 (~90MB, first run downloads model)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("SBERT model loaded successfully")
    
    def embed(self, articles: list[dict]) -> np.ndarray:
        """Generate embeddings for articles."""
        texts = []
        for a in articles:
            title = a.get('title', '')
            content = a.get('content', '')[:600]
            texts.append(f"{title}. {content}")
        
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False
        )
        
        logger.info(f"[EMBED] Generated {len(embeddings)} embeddings (384-dim)")
        return embeddings
