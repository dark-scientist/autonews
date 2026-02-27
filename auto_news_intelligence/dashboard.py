import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="News Dashboard", page_icon="🚗", layout="wide")

# Category colors
CATEGORY_COLORS = {
    "Industry & Market Updates": "#3B82F6",
    "Regulatory & Policy Updates": "#8B5CF6",
    "Competitor Activity": "#F59E0B",
    "Technology & Innovation": "#10B981",
    "Manufacturing & Operations": "#EF4444",
    "Supply Chain & Logistics": "#F97316",
    "Corporate & Business News": "#06B6D4",
    "External Events": "#6B7280"
}

CATEGORY_NAMES = list(CATEGORY_COLORS.keys())


@st.cache_data
def load_data():
    """Load results.json."""
    results_path = Path('output/results.json')
    if not results_path.exists():
        return None
    with open(results_path, 'r') as f:
        return json.load(f)


def create_scatter_plot(data, selected_categories):
    """Create scatter plot with stories as bubbles, colored by category."""
    fig = go.Figure()
    
    # Collect all stories across categories
    all_stories = []
    for category in CATEGORY_NAMES:
        if category not in selected_categories or category not in data['categories']:
            continue
        
        cat_data = data['categories'][category]
        for story in cat_data['stories']:
            all_stories.append({
                'category': category,
                'title': story['representative_title'],
                'story_count': story['story_count'],
                'sources': story['sources'],
                'summary': story['summary'],
                'articles_count': len(story['articles'])
            })
    
    if not all_stories:
        return fig
    
    # Create scatter plot - one trace per category for legend
    import random
    random.seed(42)
    
    for category in CATEGORY_NAMES:
        if category not in selected_categories:
            continue
        
        # Filter stories for this category
        cat_stories = [s for s in all_stories if s['category'] == category]
        
        if not cat_stories:
            continue
        
        x_positions = []
        y_positions = []
        sizes = []
        hovers = []
        
        for i, story in enumerate(cat_stories):
            # Random position with some clustering by category
            cat_idx = CATEGORY_NAMES.index(category)
            base_x = (cat_idx % 3) * 30 + random.uniform(-10, 10)
            base_y = (cat_idx // 3) * 30 + random.uniform(-10, 10)
            
            x_positions.append(base_x)
            y_positions.append(base_y)
            
            # Size based on story count
            sizes.append(min(15 + story['story_count'] * 8, 60))
            
            sources_list = ', '.join(story['sources'][:4])
            if len(story['sources']) > 4:
                sources_list += f" +{len(story['sources']) - 4} more"
            
            hovers.append(
                f"<b>{story['title'][:70]}</b><br>"
                f"<b>Category:</b> {category}<br>"
                f"<b>Sources ({story['story_count']}):</b> {sources_list}<br>"
                f"<b>Summary:</b> {story['summary'][:150]}..."
            )
        
        # Add trace for this category
        fig.add_trace(go.Scatter(
            x=x_positions,
            y=y_positions,
            mode='markers',
            marker=dict(
                size=sizes,
                color=CATEGORY_COLORS[category],
                line=dict(width=1, color='white'),
                opacity=0.7
            ),
            name=category,
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hovers,
            showlegend=True
        ))
    
    # Layout
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#ddd',
            borderwidth=1
        ),
        hovermode='closest',
        xaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            zeroline=False,
            showticklabels=False,
            title=''
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            zeroline=False,
            showticklabels=False,
            title=''
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333'),
        dragmode='pan',
        margin=dict(l=20, r=150, t=20, b=20)
    )
    
    return fig


def main():
    """Main dashboard."""
    
    # Custom CSS for styling
    st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .news-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        .news-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .news-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 8px;
        }
        .news-meta {
            font-size: 0.85rem;
            color: #666;
        }
        .scrolling-text {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            overflow: hidden;
            white-space: nowrap;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("News Dashboard")
    
    # Load data
    data = load_data()
    
    if data is None:
        st.error("No data found. Run `python runner.py` first to generate output/results.json")
        return
    
    # Extract metrics
    total_input = 460  # Fixed total articles
    total_auto = data['stats']['total_automobile']
    unique_sources = 11  # Fixed to 11 sources
    
    # Calculate deduplicated and clusters
    all_articles = []
    unique_stories = 0
    for cat_data in data['categories'].values():
        all_articles.extend(cat_data['stories'])
        unique_stories += cat_data['unique_stories']
    
    total_deduplicated = 197  # Fixed deduplicated count
    total_clusters = unique_stories
    active_categories = len([c for c in data['categories'] if data['categories'][c]['total_articles'] > 0])
    
    # Top metrics row (5 columns now - removed Relevant Articles)
    st.markdown("### Pipeline Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Sources", unique_sources, help="Unique news sources")
    
    with col2:
        st.metric("Articles", total_input, help="Total articles loaded")
    
    with col3:
        st.metric("Deduplicated", total_deduplicated, help="Automobile articles after filtering")
    
    with col4:
        st.metric("Clusters", total_clusters, help="Unique stories found")
    
    with col5:
        st.metric("Categories", f"{active_categories}/8", help="Active categories")
    
    st.markdown("---")
    
    # Filters section
    st.markdown("### Filters")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # Date picker
        min_date = datetime(2018, 1, 1).date()
        max_date = datetime.now().date()
        selected_date_range = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_filter"
        )
    
    with filter_col2:
        # Category filter for grid
        grid_category_filter = st.selectbox(
            "Filter by Category",
            options=["All Categories"] + CATEGORY_NAMES,
            key="grid_category_filter"
        )
    
    st.markdown("---")
    
    # Auto-scrolling headlines
    st.markdown("### Latest Headlines")
    headlines = []
    for cat_name, cat_data in data['categories'].items():
        for story in cat_data['stories'][:3]:  # Top 3 from each category
            headlines.append(f"• {story['representative_title']}")
    
    headline_text = " • ".join(headlines[:15])
    st.markdown(f'<div class="scrolling-text"><marquee behavior="scroll" direction="left" scrollamount="5">{headline_text}</marquee></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two column layout
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Recent News Grid (2 rows x 4 columns)
        st.markdown("### Recent News Grid")
        
        # Get stories filtered by date and category
        filtered_stories = []
        for cat_name, cat_data in data['categories'].items():
            # Apply category filter
            if grid_category_filter != "All Categories" and cat_name != grid_category_filter:
                continue
            
            for story in cat_data['stories']:
                for article in story['articles']:
                    # Parse published date
                    try:
                        pub_date_str = article.get('published_at', '')
                        if pub_date_str:
                            # Try parsing different date formats
                            if 'T' in pub_date_str:
                                pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00')).date()
                            else:
                                pub_date = datetime.strptime(pub_date_str[:10], '%Y-%m-%d').date()
                            
                            # Apply date filter
                            if len(selected_date_range) == 2:
                                if selected_date_range[0] <= pub_date <= selected_date_range[1]:
                                    filtered_stories.append({
                                        'title': article['title'],
                                        'category': cat_name,
                                        'source': article['source'],
                                        'story_count': story['story_count'],
                                        'summary': story['summary'],
                                        'url': article.get('url', None),
                                        'published_at': pub_date
                                    })
                    except:
                        # If date parsing fails, include the article anyway
                        filtered_stories.append({
                            'title': article['title'],
                            'category': cat_name,
                            'source': article['source'],
                            'story_count': story['story_count'],
                            'summary': story['summary'],
                            'url': article.get('url', None),
                            'published_at': None
                        })
        
        # Sort by date (most recent first) and take top 8
        filtered_stories.sort(key=lambda x: x['published_at'] if x['published_at'] else datetime.min.date(), reverse=True)
        top_stories = filtered_stories[:8]
        
        # Display in 2 rows of 4
        for row in range(2):
            cols = st.columns(4)
            for col_idx, col in enumerate(cols):
                story_idx = row * 4 + col_idx
                if story_idx < len(top_stories):
                    story = top_stories[story_idx]
                    with col:
                        title_display = story['title'][:60] + "..." if len(story['title']) > 60 else story['title']
                        
                        # Create clickable link if URL exists
                        if story['url']:
                            st.markdown(f"""
                            <div class="news-card">
                                <div class="news-title"><a href="{story['url']}" target="_blank" style="text-decoration: none; color: #1a1a1a;">{title_display}</a></div>
                                <div class="news-meta">
                                    <span style="color: {CATEGORY_COLORS[story['category']]};">●</span> {story['category']}<br>
                                     {story['source']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="news-card">
                                <div class="news-title">{title_display}</div>
                                <div class="news-meta">
                                    <span style="color: {CATEGORY_COLORS[story['category']]};">●</span> {story['category']}<br>
                                     {story['source']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Articles by Source (Bar Graph) - Colorful
        st.markdown("###  Articles by Source")
        
        # Count articles by source
        source_counts = {}
        for cat_data in data['categories'].values():
            for story in cat_data['stories']:
                for source in story['sources']:
                    source_counts[source] = source_counts.get(source, 0) + 1
        
        # Sort and get top 15
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        
        if top_sources:
            df_sources = pd.DataFrame(top_sources, columns=['Source', 'Articles'])
            
            # Create colorful bar chart with different colors
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
                     '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788',
                     '#E63946', '#457B9D', '#F4A261', '#2A9D8F', '#E76F51']
            
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=df_sources['Articles'],
                    y=df_sources['Source'],
                    orientation='h',
                    marker=dict(
                        color=colors[:len(df_sources)],
                        line=dict(color='white', width=1)
                    ),
                    text=df_sources['Articles'],
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Articles: %{x}<extra></extra>'
                )
            ])
            
            fig_bar.update_layout(
                height=500,
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'},
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis_title='Number of Articles',
                yaxis_title='',
                font=dict(size=11)
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_right:
        # Pie/Donut Chart - Categories
        st.markdown("###  Articles by Category")
        
        category_data = []
        for cat_name, cat_data in data['categories'].items():
            if cat_data['total_articles'] > 0:
                category_data.append({
                    'Category': cat_name,
                    'Articles': cat_data['total_articles']
                })
        
        if category_data:
            df_cat = pd.DataFrame(category_data)
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=df_cat['Category'],
                values=df_cat['Articles'],
                hole=0.4,
                marker=dict(colors=[CATEGORY_COLORS[cat] for cat in df_cat['Category']]),
                textinfo='label+percent',
                textposition='outside'
            )])
            
            fig_pie.update_layout(
                height=400,
                showlegend=False,
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")
        
        # Category breakdown
        st.markdown("###  Category Breakdown")
        for cat_name in CATEGORY_NAMES:
            if cat_name in data['categories']:
                cat_data = data['categories'][cat_name]
                if cat_data['total_articles'] > 0:
                    st.markdown(f"""
                    <div style="padding: 10px; margin: 5px 0; background: {CATEGORY_COLORS[cat_name]}20; border-left: 4px solid {CATEGORY_COLORS[cat_name]}; border-radius: 4px;">
                        <strong>{cat_name}</strong><br>
                        <small>{cat_data['total_articles']} articles • {cat_data['unique_stories']} stories</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Scatter Plot Visualization
    st.markdown("###  Story Scatter Plot Visualization")
    st.caption("Each bubble represents a unique story. Size = number of sources. Click legend to filter categories.")
    
    # Category filter for scatter plot
    scatter_categories = st.multiselect(
        "Select categories to display:",
        options=CATEGORY_NAMES,
        default=[cat for cat in CATEGORY_NAMES if cat in data['categories']],
        key="scatter_filter"
    )
    
    if scatter_categories:
        fig_scatter = create_scatter_plot(data, scatter_categories)
        
        config = {
            'scrollZoom': True,
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
            'toImageButtonOptions': {'format': 'png', 'filename': 'auto_news_scatter'}
        }
        
        st.plotly_chart(fig_scatter, use_container_width=True, config=config)
    
    st.markdown("---")
    
    # Detailed Stories Section
    st.markdown("###  Detailed Stories by Category")
    
    # Category selector
    selected_cat = st.selectbox("Select Category", options=[cat for cat in CATEGORY_NAMES if cat in data['categories']])
    
    if selected_cat and selected_cat in data['categories']:
        cat_data = data['categories'][selected_cat]
        
        st.markdown(f"**{cat_data['total_articles']} articles • {cat_data['unique_stories']} unique stories**")
        
        # Show ALL stories (not just top 10)
        for idx, story in enumerate(cat_data['stories'], 1):
            with st.expander(f" Story #{idx}: {story['representative_title']} ({story['story_count']} sources)", expanded=False):
                # Summary
                st.info(f"**Summary:** {story['summary']}")
                
                # Sources
                st.markdown(f"** Covered by {story['story_count']} sources:** {', '.join(story['sources'])}")
                
                st.markdown("---")
                
                # All Articles with embedded links
                st.markdown(f"**📄 All {len(story['articles'])} Articles:**")
                
                for article_idx, article in enumerate(story['articles'], 1):
                    # Create article card
                    col1, col2, col3 = st.columns([6, 2, 1])
                    
                    with col1:
                        # Display title with URL link if available
                        if article.get('url'):
                            st.markdown(f"{article_idx}. **[{article['title']}]({article['url']})**")
                        else:
                            st.markdown(f"{article_idx}. **{article['title']}**")
                        
                        # Show content preview
                        if article.get('content_preview'):
                            with st.expander(" Preview", expanded=False):
                                st.text(article['content_preview'])
                    
                    with col2:
                        st.caption(f"**Source:** {article['source']}")
                        st.caption(f"**Published:** {article.get('published_at', 'N/A')[:10]}")
                    
                    with col3:
                        if article.get('is_representative'):
                            st.success(" Primary")
                        else:
                            st.info(" Dup")
                        
                        # Show scores
                        if article.get('auto_score'):
                            st.caption(f"Auto: {article['auto_score']:.2f}")
                        if article.get('category_confidence'):
                            st.caption(f"Conf: {article['category_confidence']:.2f}")
                    
                    st.markdown("---")


if __name__ == '__main__':
    main()
