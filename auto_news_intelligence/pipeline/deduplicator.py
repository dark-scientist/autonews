import logging
import re
from collections import defaultdict
from difflib import SequenceMatcher
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Auto brands for entity detection
AUTO_BRANDS = {'tesla','toyota','honda','ford','bmw','mercedes','hyundai','kia','nissan',
              'maruti','mahindra','tata','suzuki','bajaj','tvs','ather','ola','rivian',
              'nio','byd','volkswagen','vw','audi','volvo','porsche','ferrari','renault',
              'mg','skoda','jeep','lexus','isuzu','ktm','yamaha','hero','royal','enfield',
              'ducati','triumph','harley','davidson'}


class UnionFind:
    """Union-Find data structure for clustering."""
    
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1


def extract_named_entities(text: str) -> set[str]:
    """Extract named entities: brands, capitalized words 5+ chars, 4-digit numbers."""
    entities = set()
    
    # Add brands
    text_lower = text.lower()
    for brand in AUTO_BRANDS:
        if brand in text_lower:
            entities.add(brand)
    
    # Add capitalized words 5+ chars (proper nouns)
    words = re.findall(r'\b[A-Z][a-z]{4,}\b', text)
    entities.update(w.lower() for w in words)
    
    # Add 4-digit numbers (years, prices like 2024, 5000)
    numbers = re.findall(r'\b\d{4}\b', text)
    entities.update(numbers)
    
    return entities


def compute_cluster_coherence(indices: list[int], sim_matrix: np.ndarray) -> float:
    """Compute average pairwise similarity within a cluster."""
    if len(indices) <= 1:
        return 1.0
    
    similarities = []
    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            similarities.append(sim_matrix[indices[i]][indices[j]])
    
    return float(np.mean(similarities)) if similarities else 1.0


def deduplicate_within_category(articles, embeddings, threshold, global_sc_counter):
    """Find duplicate sub-clusters within a category with improved coherence checking."""
    n = len(articles)
    if n == 0:
        return articles
    
    uf = UnionFind(n)
    sim_matrix = cosine_similarity(embeddings)
    
    for i in range(n):
        for j in range(i + 1, n):
            cos_sim = sim_matrix[i][j]
            if cos_sim < threshold:
                continue
            
            # Title entity overlap gate
            title_i = articles[i]['title']
            title_j = articles[j]['title']
            stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'is', 'are', 'was', 'were', 'has', 'be'}
            words_i = set(title_i.lower().split()) - stop_words
            words_j = set(title_j.lower().split()) - stop_words
            
            if words_i and words_j:
                overlap = len(words_i & words_j) / len(words_i | words_j)
            else:
                overlap = 0
            
            title_sim = SequenceMatcher(None, title_i.lower(), title_j.lower()).ratio()
            
            # Only hard-block if titles contain CONFLICTING named entities
            brands_i = {b for b in AUTO_BRANDS if b in title_i.lower()}
            brands_j = {b for b in AUTO_BRANDS if b in title_j.lower()}
            
            # If both titles mention brands AND they are different brands → not duplicates
            # OR if one has a brand and the other doesn't AND similarity is not very high
            if brands_i and brands_j and brands_i.isdisjoint(brands_j):
                continue
            if (brands_i or brands_j) and not (brands_i & brands_j) and cos_sim < 0.90:
                continue
            
            # Otherwise let cosine decide
            uf.union(i, j)
    
    # Build sub-clusters
    groups = defaultdict(list)
    for i in range(n):
        root = uf.find(i)
        groups[root].append(i)
    
    # Compute coherence and detect strays
    final_groups = {}
    stray_count = 0
    
    for root, indices in groups.items():
        # Compute cluster coherence
        coherence = compute_cluster_coherence(indices, sim_matrix)
        
        if coherence < 0.70:
            logger.warning(f"[DEDUP WARNING] Low coherence cluster: {coherence:.2f} — may be mis-grouped")
        
        # Representative = longest content
        rep_idx = max(indices, key=lambda i: len(articles[i].get('content', '')))
        rep_title = articles[rep_idx]['title']
        rep_entities = extract_named_entities(rep_title)
        
        # Check for stray articles
        cluster_members = []
        strays = []
        
        for idx in indices:
            if idx == rep_idx:
                cluster_members.append(idx)
                continue
            
            # Check similarity to representative
            sim_to_rep = sim_matrix[idx][rep_idx]
            
            if sim_to_rep < 0.78:
                # Check entity overlap
                article_title = articles[idx]['title']
                article_entities = extract_named_entities(article_title)
                
                shared_entities = rep_entities & article_entities
                
                if not shared_entities:
                    # This is a stray - remove from cluster
                    strays.append(idx)
                    stray_count += 1
                    logger.info(f"[DEDUP] Stray detected: '{article_title[:50]}...' (sim={sim_to_rep:.2f}, no shared entities)")
                else:
                    cluster_members.append(idx)
            else:
                cluster_members.append(idx)
        
        # Keep main cluster
        if cluster_members:
            final_groups[root] = (cluster_members, coherence)
        
        # Create singleton clusters for strays
        for stray_idx in strays:
            final_groups[stray_idx] = ([stray_idx], 1.0)
    
    if stray_count > 0:
        logger.info(f"[DEDUP] Removed {stray_count} stray articles from clusters")
    
    # Assign sub_cluster_id and metadata
    for root, (indices, coherence) in final_groups.items():
        sub_cluster_id = f"sc_{next(global_sc_counter):06d}"
        
        # Representative = longest content
        rep_idx = max(indices, key=lambda i: len(articles[i].get('content', '')))
        rep_title = articles[rep_idx]['title']
        
        for idx in indices:
            articles[idx]['sub_cluster_id'] = sub_cluster_id
            articles[idx]['sub_cluster_size'] = len(indices)
            articles[idx]['is_representative'] = (idx == rep_idx)
            articles[idx]['duplicate_sources'] = [articles[k]['source'] for k in indices if k != idx]
            articles[idx]['cluster_coherence_score'] = coherence
            
            # Add duplicate_reason for non-representatives
            if idx != rep_idx:
                sim_to_rep = sim_matrix[idx][rep_idx]
                truncated_title = rep_title[:45] + '...' if len(rep_title) > 45 else rep_title
                articles[idx]['duplicate_reason'] = f"Similar to: '{truncated_title}' (sim={sim_to_rep:.2f})"
    
    unique_count = len(final_groups)
    logger.info(f"[DEDUP] {len(articles)} articles → {unique_count} unique stories")
    return articles


def run_deduplication(articles_by_category: dict, embeddings_by_category: dict, threshold: float, global_sc_counter):
    """Run deduplication for all categories with global counter."""
    result = {}
    for category, articles in articles_by_category.items():
        embs = embeddings_by_category[category]
        deduped = deduplicate_within_category(articles, embs, threshold, global_sc_counter)
        result[category] = deduped
        unique = len(set(a['sub_cluster_id'] for a in deduped))
        logger.info(f"[DEDUP] {category}: {len(articles)} articles → {unique} unique stories")
    return result
