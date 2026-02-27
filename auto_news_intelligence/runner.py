import logging
import json
import os
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict
from itertools import count as itercount

from pipeline.html_loader import load_html_articles
from pipeline.auto_filter import filter_automobile_articles
from pipeline.embedder import Embedder
from pipeline.classifier import Classifier
from pipeline.deduplicator import run_deduplication
from pipeline.summarizer import summarize_subclusters

load_dotenv()

logger = logging.getLogger(__name__)


def build_output(deduped_by_cat, all_articles, auto_articles):
    """Build final output structure."""
    categories_out = {}
    
    for category, articles in deduped_by_cat.items():
        # Group by sub_cluster_id
        sub_clusters = defaultdict(list)
        for a in articles:
            sub_clusters[a['sub_cluster_id']].append(a)
        
        stories = []
        for sc_id, sc_articles in sub_clusters.items():
            rep = next((a for a in sc_articles if a.get('is_representative')), sc_articles[0])
            
            # Compute average cluster coherence for this story
            coherence_scores = [a.get('cluster_coherence_score', 0) for a in sc_articles]
            avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0
            
            stories.append({
                'sub_cluster_id': sc_id,
                'story_count': len(sc_articles),
                'summary': rep.get('summary', rep.get('content', '')[:200] + '...'),  # Use content preview if no summary
                'representative_title': rep['title'],
                'sources': list(set(a['source'] for a in sc_articles)),
                'cluster_coherence_score': avg_coherence,  # NEW
                'articles': [
                    {
                        'id': a['id'],
                        'title': a['title'],
                        'source': a['source'],
                        'published_at': a.get('published_at', ''),
                        'is_representative': a.get('is_representative', False),
                        'content_preview': a.get('content', '')[:200],
                        'auto_score': a.get('auto_score', 0),
                        'category_confidence': a.get('category_confidence', 0),
                        'url': a.get('url', None),
                        'cluster_reason': a.get('cluster_reason', ''),  # NEW - Task 5
                        'duplicate_reason': a.get('duplicate_reason', ''),  # NEW - Task 4
                        'cluster_coherence_score': a.get('cluster_coherence_score', 0),  # NEW - Task 4
                    }
                    for a in sc_articles
                ]
            })
        
        # Sort stories by story_count desc (most covered first)
        stories.sort(key=lambda x: x['story_count'], reverse=True)
        
        categories_out[category] = {
            'total_articles': len(articles),
            'unique_stories': len(sub_clusters),
            'stories': stories
        }
    
    # Count unique sources across all articles
    unique_sources = len(set(a['source'] for a in all_articles))
    
    return {
        'run_at': datetime.now().isoformat(),
        'stats': {
            'total_input': len(all_articles),
            'total_automobile': len(auto_articles),
            'unique_sources': unique_sources,
            'similarity_threshold': float(os.getenv('SIMILARITY_THRESHOLD', '0.82')),
        },
        'categories': categories_out
    }


def run():
    """Execute full pipeline."""
    logger.info("=" * 50)
    logger.info("AUTO NEWS INTELLIGENCE PIPELINE")
    logger.info("=" * 50)
    
    # 1. Load HTML articles
    input_folder = os.getenv('INPUT_FOLDER', 'input/articles')
    articles = load_html_articles(input_folder)
    loaded_count = len(articles)
    if not articles:
        logger.error("No articles loaded. Exiting.")
        return
    
    # 2. Filter to automobile only
    auto_articles, rejected = filter_automobile_articles(
        articles, 
        threshold=float(os.getenv('AUTO_FILTER_THRESHOLD', '0.25'))
    )
    auto_count = len(auto_articles)
    if not auto_articles:
        logger.error("No automobile articles found after filtering.")
        return
    
    # 3. Generate SBERT embeddings
    embedder = Embedder()
    embeddings = embedder.embed(auto_articles)
    
    # 4. Classify into 8 categories
    classifier = Classifier(embedder)
    auto_articles = classifier.classify(auto_articles, embeddings)
    
    # 5. Confidence gate - Remove false positives with low confidence
    MIN_CONFIDENCE = float(os.getenv('MIN_CATEGORY_CONFIDENCE', '0.14'))
    before_gate = len(auto_articles)
    auto_articles = [a for a in auto_articles if a.get('category_confidence', 0) >= MIN_CONFIDENCE]
    conf_removed = before_gate - len(auto_articles)
    if conf_removed > 0:
        logger.info(f"[CONFIDENCE GATE] Removed {conf_removed} articles with category_confidence < {MIN_CONFIDENCE}")
    
    # Re-generate embeddings for filtered articles
    embeddings = embedder.embed(auto_articles)
    
    # 6. Group by category
    articles_by_cat = defaultdict(list)
    embeddings_by_cat = defaultdict(list)
    for i, article in enumerate(auto_articles):
        cat = article['category']
        articles_by_cat[cat].append(article)
        embeddings_by_cat[cat].append(embeddings[i])
    
    # Convert embedding lists to numpy arrays
    for cat in embeddings_by_cat:
        embeddings_by_cat[cat] = np.array(embeddings_by_cat[cat])
    
    # 7. Deduplicate within each category with global counter
    threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.72'))
    global_sc_counter = itercount(0)
    deduped_by_cat = run_deduplication(articles_by_cat, embeddings_by_cat, threshold, global_sc_counter)
    
    # 8. Summarize sub-clusters (DISABLED to save costs)
    # summarize_subclusters(deduped_by_cat)
    logger.info("[SUMMARIZE] Skipped - LLM summarization disabled to save costs")
    
    # 9. Build output
    output = build_output(deduped_by_cat, articles, auto_articles)
    
    # 10. Save
    os.makedirs('output', exist_ok=True)
    with open('output/results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    # 11. Print stats with gate summary
    final_count = len(auto_articles)
    total_stories = sum(
        len(set(a['sub_cluster_id'] for a in arts))
        for arts in deduped_by_cat.values()
    )
    gpt_calls = total_stories
    
    logger.info("=" * 50)
    logger.info(f"[GATE] HTML load:        {loaded_count} articles")
    logger.info(f"[GATE] Auto filter:      {auto_count} passed")
    logger.info(f"[GATE] Confidence gate:  {conf_removed} removed")
    logger.info(f"[GATE] Final pipeline:   {final_count} articles")
    logger.info("=" * 50)
    logger.info(f"INPUT:       {len(articles)} total articles")
    logger.info(f"AUTO FILTER: {final_count} automobile articles")
    logger.info(f"CATEGORIES:  8 fixed categories")
    logger.info(f"STORIES:     {total_stories} unique stories found")
    logger.info(f"GPT CALLS:   ~{gpt_calls} (one per unique story)")
    logger.info(f"OUTPUT:      output/results.json")
    logger.info("=" * 50)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')
    run()
