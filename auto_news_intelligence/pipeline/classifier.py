import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

CATEGORIES = {
    "Industry & Market Updates": 
        "industry sales trends demand outlook fuel price impact EV adoption trends "
        "market forecasts vehicle sales volume market share growth automotive market "
        "quarterly results annual sales retail numbers delivery statistics consumer demand",
    
    "Regulatory & Policy Updates": 
        "emission norms safety regulations EV incentives import export rules tax duty "
        "government policy CAFE standards fuel economy regulations compliance mandate "
        "subsidy scheme incentive program carbon credit emission target ban ICE",
    
    "Competitor Activity": 
        "new vehicle launch pricing changes feature announcement capacity expansion "
        "strategic partnerships model reveal debut competitor new car launch price cut "
        "competition rival market entry product lineup unveil showcase",
    
    "Technology & Innovation": 
        "battery technology ADAS features connected car software update platform "
        "autonomous driving self-driving OTA update infotainment system sensor lidar "
        "solid state battery fast charging range improvement AI vehicle innovation R&D",
    
    "Manufacturing & Operations": 
        "plant opening production changes capacity announcement labour update "
        "manufacturing investment factory expansion assembly line workforce retooling "
        "production halt shutdown output facility inauguration capex",
    
    "Supply Chain & Logistics": 
        "vendor development component availability logistics disruption raw material "
        "semiconductor shortage chip supply lithium cobalt supplier tier1 tier2 "
        "procurement inventory stockpile import component price commodity",
    
    "Corporate & Business News": 
        "investment partnership financial announcement leadership change CEO CFO "
        "merger acquisition joint venture funding IPO revenue profit quarterly earnings "
        "board director appointment resignation stake buyout valuation",
    
    "External Events": 
        "natural disaster flood earthquake infrastructure disruption economic development "
        "geopolitical trade war tariff port strike fuel price oil commodity market "
        "global recession inflation rate hike currency exchange impact"
}


class Classifier:
    """Classify articles into 8 fixed categories using SBERT similarity."""
    
    def __init__(self, embedder):
        self.embedder = embedder
        self.category_names = list(CATEGORIES.keys())
        self.prototypes = self._build_prototypes()
        logger.info(f"[CLASSIFY] Built prototypes for {len(self.category_names)} categories")
    
    def _build_prototypes(self):
        """Build category prototype embeddings."""
        texts = [CATEGORIES[cat] for cat in self.category_names]
        return self.embedder.model.encode(texts, normalize_embeddings=True)
    
    def classify(self, articles: list[dict], embeddings: np.ndarray) -> list[dict]:
        """Classify each article into one of 8 categories with cluster_reason."""
        scores_matrix = cosine_similarity(embeddings, self.prototypes)
        
        for i, article in enumerate(articles):
            scores = scores_matrix[i]
            best_idx = int(np.argmax(scores))
            
            article['category'] = self.category_names[best_idx]
            article['category_scores'] = {
                self.category_names[j]: float(scores[j])
                for j in range(len(self.category_names))
            }
            article['category_confidence'] = float(scores[best_idx])
            
            # Generate cluster_reason
            cluster_reason = self._generate_cluster_reason(
                article, 
                self.category_names[best_idx], 
                article['category_confidence']
            )
            article['cluster_reason'] = cluster_reason
            
            logger.info(f"[CLASSIFY] \"{article['title'][:50]}...\" → {article['category']} (score={article['category_confidence']:.2f})")
        
        return articles
    
    def _generate_cluster_reason(self, article: dict, category: str, confidence: float) -> str:
        """Generate explanation for why article was placed in this category."""
        # Get category prototype keywords
        prototype_text = CATEGORIES[category].lower()
        prototype_words = set(prototype_text.split())
        
        # Get article text (title + first 300 chars of content)
        article_text = article['title'] + ' ' + article.get('content', '')[:300]
        article_text_lower = article_text.lower()
        article_words = set(article_text_lower.split())
        
        # Find matching keywords
        matching_keywords = []
        for word in prototype_words:
            if len(word) > 3 and word in article_text_lower:  # Skip short words
                matching_keywords.append(word)
        
        # Take top 3 by frequency/relevance
        matching_keywords = matching_keywords[:3]
        
        if len(matching_keywords) >= 2:
            return f"Matched on: {', '.join(matching_keywords)}"
        else:
            # Fallback to semantic match
            return f"Best semantic match to {category} (score={confidence:.2f})"
