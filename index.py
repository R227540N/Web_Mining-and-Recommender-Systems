from flask import Flask
import feedparser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from datetime import datetime
import re
import base64
import os

app = Flask(__name__)

# ── UZ Logo (base64-embedded so no external URL needed) ──────────────────────
# Place your logo file at api/uz_logo.png and it will be embedded automatically.
# Falls back to the Wikimedia hosted image if the file is not found.
def get_logo_uri():
    logo_path = os.path.join(os.path.dirname(__file__), "uz_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    # Fallback
    return "https://upload.wikimedia.org/wikipedia/en/thumb/3/3d/University_of_Zimbabwe_coat_of_arms.png/150px-University_of_Zimbabwe_coat_of_arms.png"


def clean_text(text):
    """Strip HTML tags from RSS summaries."""
    return re.sub(r'<[^>]+>', '', text)


@app.route('/')
def home():
    FEEDS = [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "http://rss.cnn.com/rss/edition.rss",
        "https://moxie.foxnews.com/google-publisher/world.xml",
        "https://www.wired.com/feed/rss",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml",
    ]

    articles = []
    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                articles.append({
                    "title":   entry.get("title", ""),
                    "link":    entry.get("link", ""),
                    "summary": clean_text(entry.get("summary", "")[:150]) + "...",
                    "source":  feed.feed.get("title", "News Source"),
                })
        except Exception:
            continue   # Skip a feed that fails; don't crash the whole page

    if not articles:
        return "<h2>⚠️ Could not fetch any news feeds. Please try again shortly.</h2>", 500

    # ── TF-IDF vectorisation ──────────────────────────────────────────────────
    texts = [f"{a['title']} {a['summary']}" for a in articles]
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    X = vectorizer.fit_transform(texts)

    # ── K-Means clustering ────────────────────────────────────────────────────
    num_clusters = max(2, min(8, len(articles) // 6))
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    kmeans.fit(X)

    # ── Topic names: top 3 keywords per cluster ───────────────────────────────
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()
    cluster_topics = {
        i: " • ".join(terms[ind].capitalize() for ind in order_centroids[i, :3])
        for i in range(num_clusters)
    }

    # ── Group articles by cluster ─────────────────────────────────────────────
    clustered_data = {i: [] for i in range(num_clusters)}
    for idx, label in enumerate(kmeans.labels_):
        clustered_data[label].append(articles[idx])

    current_time = datetime.now().strftime("%B %d, %Y • %I:%M %p")
    logo_uri = get_logo_uri()

    # ── HTML ──────────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UZ Global News</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg:     #f8fafc;
      --card:   #ffffff;
      --text:   #0f172a;
      --muted:  #64748b;
      --accent: #3b82f6;
      --border: #e2e8f0;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}

    /* ── Header ── */
    header {{
      background: var(--card);
      border-bottom: 1px solid var(--border);
      padding: 24px 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 24px;
      flex-wrap: wrap;
    }}
    .header-logo {{
      width: 80px;
      height: 80px;
      object-fit: contain;
      flex-shrink: 0;
    }}
    .header-text {{ text-align: center; }}
    .header-text h1 {{
      font-size: clamp(1.4rem, 4vw, 2.2rem);
      font-weight: 800;
      letter-spacing: -0.04em;
    }}
    .header-text .subtitle {{
      color: var(--muted);
      font-size: 0.875rem;
      margin-top: 4px;
    }}

    /* ── Masonry grid ── */
    .container {{
      max-width: 1400px;
      margin: 40px auto;
      padding: 0 20px 60px;
      columns: 380px;
      column-gap: 24px;
    }}

    /* ── Cluster card ── */
    .cluster-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 22px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
      transition: transform .2s, box-shadow .2s, border-color .2s;
      break-inside: avoid;
      display: inline-block;
      width: 100%;
      margin-bottom: 24px;
    }}
    .cluster-card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 10px 20px rgba(0,0,0,0.08);
      border-color: var(--accent);
    }}

    /* ── Topic label ── */
    .topic-header {{
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: .1em;
      color: var(--accent);
      font-weight: 700;
      padding-bottom: 14px;
      margin-bottom: 18px;
      border-bottom: 2px solid #f1f5f9;
    }}

    /* ── Article row ── */
    .article {{ margin-bottom: 18px; }}
    .article:last-of-type {{ margin-bottom: 0; }}
    .article a {{
      display: block;
      font-weight: 600;
      font-size: 1rem;
      color: var(--text);
      text-decoration: none;
      margin-bottom: 5px;
      line-height: 1.4;
      transition: color .2s;
    }}
    .article a:hover {{ color: var(--accent); }}
    .summary {{
      color: var(--muted);
      font-size: 0.85rem;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      margin-bottom: 7px;
    }}
    .source-tag {{
      display: inline-block;
      background: #f1f5f9;
      color: #475569;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 20px;
    }}

    /* ── Toggle button ── */
    .toggle-btn {{
      width: 100%;
      margin-top: 14px;
      padding: 11px;
      background: #f8fafc;
      color: var(--accent);
      border: 1px dashed #cbd5e1;
      border-radius: 8px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: background .2s, border-color .2s;
    }}
    .toggle-btn:hover {{ background: #eff6ff; border-color: var(--accent); }}

    /* ── Responsive ── */
    @media (max-width: 500px) {{
      .header-logo {{ width: 55px; height: 55px; }}
    }}
  </style>
</head>
<body>

<header>
  <img src="{logo_uri}" alt="UZ Logo" class="header-logo" onerror="this.style.display='none'">
  <div class="header-text">
    <h1>🌍 Global News</h1>
    <p class="subtitle">University of Zimbabwe &nbsp;|&nbsp; AI-Clustered Topics &nbsp;|&nbsp; {current_time}</p>
  </div>
  <img src="{logo_uri}" alt="UZ Logo" class="header-logo" onerror="this.style.display='none'">
</header>

<div class="container">
"""

    for cluster_id, cluster_articles in clustered_data.items():
        if len(cluster_articles) < 2:
            continue

        visible  = cluster_articles[:2]
        hidden   = cluster_articles[2:]
        topic    = cluster_topics[cluster_id]

        html += f'<div class="cluster-card">\n'
        html += f'  <div class="topic-header">{topic}</div>\n'

        for a in visible:
            html += f"""  <div class="article">
    <a href="{a['link']}" target="_blank" rel="noopener">{a['title']}</a>
    <div class="summary">{a['summary']}</div>
    <span class="source-tag">{a['source']}</span>
  </div>\n"""

        if hidden:
            html += '  <div class="extra-articles" style="display:none;">\n'
            for a in hidden:
                html += f"""    <div class="article" style="margin-top:16px;">
      <a href="{a['link']}" target="_blank" rel="noopener">{a['title']}</a>
      <div class="summary">{a['summary']}</div>
      <span class="source-tag">{a['source']}</span>
    </div>\n"""
            html += '  </div>\n'
            html += f'  <button class="toggle-btn" onclick="toggleArticles(this)">▼ View {len(hidden)} More Articles</button>\n'

        html += '</div>\n'

    html += """</div>

<script>
  function toggleArticles(btn) {
    const extra = btn.previousElementSibling;
    const opening = extra.style.display === 'none';
    extra.style.display = opening ? 'block' : 'none';
    const count = extra.querySelectorAll('.article').length;
    btn.innerHTML = opening ? '▲ Show Less' : `▼ View ${count} More Articles`;
  }
</script>
</body>
</html>"""

    return html
