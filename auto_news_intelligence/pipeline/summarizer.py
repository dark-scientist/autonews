import logging
import os
import time
from collections import defaultdict
from openai import OpenAI

logger = logging.getLogger(__name__)


def summarize_subclusters(deduped_by_cat: dict):
    """Summarize each sub-cluster using GPT-4o-mini."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_key_here':
        logger.warning("[SUMMARIZE] OPENAI_API_KEY not set, skipping summarization")
        # Set placeholder summaries
        for category, articles in deduped_by_cat.items():
            for article in articles:
                article['summary'] = "Summary unavailable (API key not configured)"
        return
    
    client = OpenAI(api_key=api_key)
    
    # Group by sub_cluster_id across all categories
    all_subclusters = defaultdict(list)
    for category, articles in deduped_by_cat.items():
        for article in articles:
            sc_id = article['sub_cluster_id']
            all_subclusters[sc_id].append(article)
    
    total_subclusters = len(all_subclusters)
    logger.info(f"[SUMMARIZE] Processing {total_subclusters} unique sub-clusters")
    
    processed = 0
    batch_count = 0
    
    for sc_id, sc_articles in all_subclusters.items():
        # Find representative
        rep = next((a for a in sc_articles if a.get('is_representative')), sc_articles[0])
        
        # Build context
        sources = list(set(a['source'] for a in sc_articles))
        all_titles = [a['title'] for a in sc_articles]
        combined_content = rep.get('content', '')[:2000]
        
        # Build prompt
        system_prompt = (
            "You are an automotive industry analyst. You will receive multiple news article titles "
            "about the same story, reported by different sources. Write a single 2-3 sentence summary "
            "that captures the key facts of the story."
        )
        
        user_prompt = (
            f"Story covered by {len(sources)} sources: {', '.join(sources)}\n\n"
            f"Article titles:\n" + '\n'.join(f"- {t}" for t in all_titles) + "\n\n"
            f"Content:\n{combined_content}\n\n"
            f"Write a 2-3 sentence summary of this automotive news story."
        )
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=180,
                temperature=0
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Apply summary to all articles in sub-cluster
            for article in sc_articles:
                article['summary'] = summary
            
            processed += 1
            
            if processed % 5 == 0:
                logger.info(f"[SUMMARIZE] {processed}/{total_subclusters} sub-clusters done")
                time.sleep(1)  # Rate limiting
        
        except Exception as e:
            logger.error(f"[SUMMARIZE] Error for {sc_id}: {e}")
            for article in sc_articles:
                article['summary'] = "Summary unavailable"
    
    logger.info(f"[SUMMARIZE] Completed {processed}/{total_subclusters} sub-clusters")
