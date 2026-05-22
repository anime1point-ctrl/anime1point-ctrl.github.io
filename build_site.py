import requests
import os
import json
from datetime import datetime, timezone

API_KEY = os.environ['YOUTUBE_API_KEY']
CHANNEL_ID = os.environ['CHANNEL_ID']
BASE = 'https://www.googleapis.com/youtube/v3'

def yt(endpoint, **params):
    params['key'] = API_KEY
    r = requests.get(f'{BASE}/{endpoint}', params=params)
    return r.json()

def get_videos(max_results=8, video_type='video'):
    data = yt('search', channelId=CHANNEL_ID, part='snippet', order='date',
              maxResults=max_results, type='video',
              videoDuration='medium' if video_type == 'video' else 'short')
    items = data.get('items', [])
    ids = ','.join(i['id']['videoId'] for i in items)
    if not ids:
        return []
    stats = yt('videos', part='statistics,contentDetails', id=ids)
    stats_map = {s['id']: s for s in stats.get('items', [])}
    results = []
    for item in items:
        vid_id = item['id']['videoId']
        s = item['snippet']
        st = stats_map.get(vid_id, {})
        views = int(st.get('statistics', {}).get('viewCount', 0))
        duration_raw = st.get('contentDetails', {}).get('duration', 'PT0S')
        # Parse duration PT1H2M3S
        import re
        dur_match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_raw)
        h = int(dur_match.group(1) or 0) if dur_match else 0
        m = int(dur_match.group(2) or 0) if dur_match else 0
        sec = int(dur_match.group(3) or 0) if dur_match else 0
        if h > 0:
            duration = f'{h}:{m:02d}:{sec:02d}'
        else:
            duration = f'{m}:{sec:02d}'
        # Format views
        if views >= 1000000:
            views_fmt = f'{views/1000000:.1f}M'
        elif views >= 1000:
            views_fmt = f'{views/1000:.1f}K'
        else:
            views_fmt = str(views)
        # Published time
        pub = s['publishedAt'][:10]
        results.append({
            'id': vid_id,
            'title': s['title'],
            'thumbnail': f'https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg',
            'thumb_fallback': f'https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg',
            'views': views_fmt,
            'duration': duration,
            'published': pub
        })
    return results

def get_community_posts():
    # Community posts via search
    data = yt('activities', channelId=CHANNEL_ID, part='snippet,contentDetails', maxResults=5)
    posts = []
    for item in data.get('items', []):
        if item.get('snippet', {}).get('type') == 'channelItem':
            continue
        s = item['snippet']
        posts.append({
            'title': s.get('title', ''),
            'description': s.get('description', '')[:200],
            'published': s.get('publishedAt', '')[:10]
        })
    return posts[:4]

def format_views_bar(views_str):
    return views_str

def video_card(v, is_short=False):
    badge = '<span class="badge">SHORT</span>' if is_short else ''
    return f"""
    <div class="video-card" onclick="openModal('{v['id']}','{v['title'].replace("'", "").replace(chr(10), '')}')">
      <div class="thumb-wrap">
        <img src="{v['thumbnail']}" alt="{v['title'][:60]} - Anime1Point" loading="lazy" onerror="this.src='{v['thumb_fallback']}'"/>
        <div class="play-btn"><svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg></div>
        <span class="duration">{v['duration']}</span>
        {badge}
      </div>
      <div class="video-info">
        <h3>{v['title'][:90]}{'...' if len(v['title']) > 90 else ''}</h3>
        <span class="meta">{v['views']} views &bull; {v['published']} &bull; Anime1Point</span>
      </div>
    </div>"""

def build_html(videos, shorts):
    updated = datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')
    video_cards = '\n'.join(video_card(v) for v in videos)
    short_cards = '\n'.join(video_card(v, is_short=True) for v in shorts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Anime1Point | Anime One Point | Anime Breakdown YouTube Channel</title>
  <meta name="description" content="Anime1Point (also known as Anime One Point or Anime Point) is a YouTube channel dedicated to anime breakdowns, That Time I Got Reincarnated as a Slime Season 4 reviews, Tensura lore, manga analysis and deep story discussions."/>
  <meta name="keywords" content="Anime1Point, Anime One Point, AnimeOnePoint, Anime Point, anime breakdown, anime explained, That Time I Got Reincarnated as a Slime, Tensura Season 4, Rimuru Tempest, Diablo, anime review, anime lore, manga analysis, tensura explained, anime1point youtube"/>
  <meta name="author" content="Anime1Point"/>
  <meta property="og:title" content="Anime1Point | Anime One Point | Anime Breakdown YouTube Channel"/>
  <meta property="og:description" content="Anime1Point (Anime One Point) is a YouTube channel covering That Time I Got Reincarnated as a Slime Season 4 breakdowns, anime explained, and deep manga analysis."/>
  <meta property="og:url" content="https://anime1point-ctrl.github.io"/>
  <meta property="og:type" content="website"/>
  <link rel="canonical" href="https://anime1point-ctrl.github.io"/>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Segoe UI',sans-serif;background:#0d0d1a;color:#e0e0e0}}
    header{{background:linear-gradient(135deg,#1a0533,#0d1f4d);padding:48px 20px 36px;text-align:center;border-bottom:3px solid #7c3aed}}
    header h1{{font-size:2.8em;color:#fff;letter-spacing:2px;text-shadow:0 0 20px #7c3aed}}
    header p.tagline{{color:#a78bfa;font-size:1.1em;margin-top:10px}}
    .also-known{{background:#1a1a2e;padding:10px 20px;text-align:center;font-size:0.92em;color:#9ca3af;border-bottom:1px solid #2d2d4e}}
    .also-known span{{color:#a78bfa;font-weight:600}}
    nav{{background:#111128;padding:10px 20px;text-align:center;border-bottom:1px solid #2d2d4e;position:sticky;top:0;z-index:100}}
    nav a{{color:#a78bfa;text-decoration:none;margin:0 14px;font-size:0.95em;font-weight:600}}
    nav a:hover{{color:#fff}}
    .container{{max-width:1000px;margin:0 auto;padding:40px 20px}}
    .about{{background:#161625;border-left:4px solid #7c3aed;padding:24px;border-radius:8px;margin-bottom:40px;line-height:1.85}}
    .about h2{{color:#a78bfa;margin-bottom:12px;font-size:1.4em}}
    .about p{{color:#d1d5db}}
    .cta-btn{{display:inline-block;background:#ff0000;color:#fff;padding:14px 36px;border-radius:6px;text-decoration:none;font-size:1.1em;font-weight:700;margin-top:20px;transition:background 0.2s}}
    .cta-btn:hover{{background:#cc0000}}
    .section-title{{color:#a78bfa;font-size:1.5em;margin:40px 0 20px;border-bottom:2px solid #2d2d4e;padding-bottom:8px}}
    .updated{{color:#4b5563;font-size:0.82em;margin-bottom:16px}}
    .videos-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:22px;margin-bottom:40px}}
    .video-card{{background:#1a1a2e;border-radius:10px;overflow:hidden;border:1px solid #2d2d4e;transition:transform 0.2s,border-color 0.2s;cursor:pointer}}
    .video-card:hover{{transform:translateY(-5px);border-color:#7c3aed}}
    .thumb-wrap{{position:relative;width:100%;padding-top:56.25%;overflow:hidden;background:#0d0d1a}}
    .thumb-wrap img{{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;transition:transform 0.3s}}
    .video-card:hover .thumb-wrap img{{transform:scale(1.04)}}
    .play-btn{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:56px;height:56px;background:rgba(255,0,0,0.88);border-radius:50%;display:flex;align-items:center;justify-content:center;pointer-events:none}}
    .play-btn svg{{width:22px;height:22px;fill:#fff;margin-left:4px}}
    .video-card:hover .play-btn{{background:#ff0000}}
    .duration{{position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.82);color:#fff;font-size:0.78em;padding:2px 6px;border-radius:3px}}
    .badge{{position:absolute;top:8px;left:8px;background:#7c3aed;color:#fff;font-size:0.72em;padding:2px 8px;border-radius:3px;font-weight:700}}
    .video-info{{padding:14px}}
    .video-info h3{{color:#e0e0e0;font-size:0.9em;line-height:1.45;margin-bottom:6px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
    .video-info .meta{{color:#6b7280;font-size:0.8em}}
    .modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.88);z-index:999;align-items:center;justify-content:center}}
    .modal-overlay.active{{display:flex}}
    .modal-box{{background:#111128;border-radius:12px;overflow:hidden;width:90%;max-width:860px;position:relative;border:2px solid #7c3aed}}
    .modal-close{{position:absolute;top:10px;right:14px;background:none;border:none;color:#fff;font-size:1.8em;cursor:pointer;z-index:10;line-height:1}}
    .modal-box iframe{{width:100%;aspect-ratio:16/9;display:block;border:none}}
    .modal-title{{padding:12px 16px;color:#a78bfa;font-size:0.95em;font-weight:600}}
    .playlists{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:20px;margin-bottom:40px}}
    .playlist-card{{background:#1a1a2e;border-radius:10px;overflow:hidden;border:1px solid #2d2d4e;transition:transform 0.2s,border-color 0.2s}}
    .playlist-card:hover{{transform:translateY(-4px);border-color:#7c3aed}}
    .playlist-thumb{{position:relative;width:100%;padding-top:56.25%;background:#0d0d1a;overflow:hidden}}
    .playlist-thumb img{{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover}}
    .playlist-count{{position:absolute;top:0;right:0;background:rgba(0,0,0,0.82);color:#fff;font-size:0.78em;padding:4px 8px}}
    .playlist-info{{padding:14px}}
    .playlist-info h3{{color:#a78bfa;margin-bottom:6px;font-size:1em}}
    .playlist-info p{{color:#9ca3af;font-size:0.85em;margin-bottom:10px;line-height:1.5}}
    .playlist-info a{{color:#60a5fa;font-size:0.88em;text-decoration:none;font-weight:600}}
    .tags{{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 40px}}
    .tag{{background:#1e1e3a;border:1px solid #4c1d95;color:#a78bfa;padding:5px 13px;border-radius:20px;font-size:0.83em}}
    .sub-banner{{background:linear-gradient(135deg,#4c1d95,#1e3a8a);border-radius:12px;padding:32px 24px;text-align:center;margin:40px 0}}
    .sub-banner h2{{color:#fff;font-size:1.6em;margin-bottom:10px}}
    .sub-banner p{{color:#c4b5fd;margin-bottom:20px;font-size:1em}}
    footer{{background:#0a0a14;text-align:center;padding:30px 20px;color:#4b5563;border-top:1px solid #1f2937;font-size:0.88em}}
    footer a{{color:#60a5fa;text-decoration:none}}
    @media(max-width:600px){{header h1{{font-size:1.9em}}.modal-box{{width:97%}}}}
  </style>
</head>
<body>
<header>
  <h1>&#9654; Anime1Point</h1>
  <p class="tagline">Anime Breakdown &bull; Anime Explained &bull; Deep Story Analysis</p>
</header>
<div class="also-known">
  Also known as <span>Anime One Point</span> &bull; <span>AnimeOnePoint</span> &bull; <span>Anime Point</span> &bull; <span>Anime 1 Point</span>
</div>
<nav>
  <a href="#videos">Videos</a>
  <a href="#shorts">Shorts</a>
  <a href="#playlists">Playlists</a>
  <a href="#about">About</a>
  <a href="https://www.youtube.com/@anime1point" target="_blank" rel="noopener">&#9654; YouTube</a>
</nav>
<div class="container">
  <div class="about" id="about">
    <h2>About Anime1Point</h2>
    <p>Welcome to <strong>Anime1Point</strong> &mdash; also known as <strong>Anime One Point</strong>, <strong>AnimeOnePoint</strong>, and <strong>Anime Point</strong> &mdash; your ultimate destination for anime breakdowns and anime explained content on YouTube. We specialize in <strong>That Time I Got Reincarnated as a Slime (Tensura) Season 4</strong> episode reviews, manga analysis, anime lore deep dives, hidden details, and story breakdowns covering Rimuru Tempest, Diablo, Milim Nava, Veldora, and the Primordial Demons.</p>
    <a href="https://www.youtube.com/@anime1point?sub_confirmation=1" class="cta-btn" target="_blank" rel="noopener">&#9654; Subscribe on YouTube</a>
  </div>
  <h2 class="section-title" id="videos">&#127916; Latest Videos</h2>
  <p class="updated">&#128260; Auto-updated: {updated} &bull; Click any video to watch here (views count on YouTube!)</p>
  <div class="videos-grid">
{video_cards}
  </div>
  <div style="text-align:center;margin-bottom:40px">
    <a href="https://www.youtube.com/@anime1point/videos" target="_blank" rel="noopener" class="cta-btn" style="background:#7c3aed">&#9654; See All Videos on YouTube</a>
  </div>
  <h2 class="section-title" id="shorts">&#9889; Latest Shorts</h2>
  <div class="videos-grid">
{short_cards}
  </div>
  <div style="text-align:center;margin-bottom:40px">
    <a href="https://www.youtube.com/@anime1point/shorts" target="_blank" rel="noopener" class="cta-btn" style="background:#7c3aed">&#9654; See All Shorts on YouTube</a>
  </div>
  <h2 class="section-title" id="playlists">&#128203; Playlists</h2>
  <div class="playlists">
    <div class="playlist-card">
      <div class="playlist-thumb"><img src="https://i.ytimg.com/vi/ZVmqQk1GbqE/maxresdefault.jpg" alt="Tensura Season 4 Reviews" loading="lazy"/><span class="playlist-count">16 videos</span></div>
      <div class="playlist-info"><h3>Tensura Season 4 Reviews</h3><p>Full episode breakdown and analysis of That Time I Got Reincarnated as a Slime Season 4 in English Dub &amp; Sub.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank" rel="noopener">Watch Playlist &rarr;</a></div>
    </div>
    <div class="playlist-card">
      <div class="playlist-thumb"><img src="https://i.ytimg.com/vi/ommA4DBy5RQ/maxresdefault.jpg" alt="Tensura Season 4 Shorts" loading="lazy"/><span class="playlist-count">116+ videos</span></div>
      <div class="playlist-info"><h3>Tensura Season 4 Shorts</h3><p>116+ short clips covering key moments, character breakdowns and hidden details from Tensura Season 4.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank" rel="noopener">Watch Playlist &rarr;</a></div>
    </div>
    <div class="playlist-card">
      <div class="playlist-thumb"><img src="https://i.ytimg.com/vi/o_PazOqPg0I/maxresdefault.jpg" alt="Pokemon Play" loading="lazy"/><span class="playlist-count">113+ videos</span></div>
      <div class="playlist-info"><h3>Pokemon Play</h3><p>113+ Pokemon-themed videos and quizzes. Can you guess them from the hints?</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank" rel="noopener">Watch Playlist &rarr;</a></div>
    </div>
  </div>
  <div class="sub-banner">
    <h2>&#9654; Join the Anime1Point Community</h2>
    <p>New episodes every week &bull; That Time I Got Reincarnated as a Slime Season 4 &bull; Anime Breakdowns &bull; Manga Analysis</p>
    <a href="https://www.youtube.com/@anime1point?sub_confirmation=1" class="cta-btn" target="_blank" rel="noopener">Subscribe for Free</a>
  </div>
  <h2 class="section-title">&#127991; Topics We Cover</h2>
  <div class="tags">
    <span class="tag">Anime1Point</span><span class="tag">Anime One Point</span><span class="tag">AnimeOnePoint</span><span class="tag">Anime Point</span>
    <span class="tag">That Time I Got Reincarnated as a Slime</span><span class="tag">Tensura Season 4</span>
    <span class="tag">Rimuru Tempest</span><span class="tag">Diablo Tensura</span><span class="tag">Milim Nava</span>
    <span class="tag">Veldora</span><span class="tag">Primordial Demons</span><span class="tag">Anime Breakdown</span>
    <span class="tag">Anime Explained</span><span class="tag">Anime Review</span><span class="tag">Manga Analysis</span>
    <span class="tag">Anime Lore</span><span class="tag">Tensura Lore</span><span class="tag">Isekai Anime</span>
    <span class="tag">Anime Hindi</span><span class="tag">Pokemon Quiz</span><span class="tag">Anime Discussion</span>
  </div>
</div>
<div class="modal-overlay" id="videoModal" onclick="closeModalOutside(event)">
  <div class="modal-box">
    <button class="modal-close" onclick="closeModal()">&times;</button>
    <div class="modal-title" id="modalTitle"></div>
    <iframe id="modalIframe" src="" allowfullscreen allow="autoplay; encrypted-media"></iframe>
  </div>
</div>
<footer>
  <p>&copy; 2026 <strong>Anime1Point</strong> (Anime One Point) &mdash; All Rights Reserved</p>
  <p style="margin-top:10px"><a href="https://www.youtube.com/@anime1point" target="_blank">YouTube</a> &bull; <a href="https://www.youtube.com/@anime1point/videos" target="_blank">Videos</a> &bull; <a href="https://www.youtube.com/@anime1point/shorts" target="_blank">Shorts</a> &bull; <a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Playlists</a></p>
  <p style="margin-top:10px;font-size:0.82em">Anime1Point &bull; Anime One Point &bull; AnimeOnePoint &bull; Anime Point &bull; Tensura Season 4 &bull; That Time I Got Reincarnated as a Slime</p>
</footer>
<script>
function openModal(id,title){{document.getElementById('modalTitle').textContent=title;document.getElementById('modalIframe').src='https://www.youtube.com/embed/'+id+'?autoplay=1&rel=0';document.getElementById('videoModal').classList.add('active');document.body.style.overflow='hidden';}}
function closeModal(){{document.getElementById('videoModal').classList.remove('active');document.getElementById('modalIframe').src='';document.body.style.overflow='';}}
function closeModalOutside(e){{if(e.target===document.getElementById('videoModal'))closeModal();}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeModal();}});
</script>
</body>
</html>"""

if __name__ == '__main__':
    print("Fetching videos...")
    videos = get_videos(max_results=8, video_type='video')
    print(f"Got {len(videos)} videos")
    
    print("Fetching shorts...")
    shorts = get_videos(max_results=6, video_type='short')
    print(f"Got {len(shorts)} shorts")
    
    html = build_html(videos, shorts)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("index.html rebuilt successfully!")
    print(f"Videos: {[v['title'][:40] for v in videos]}")
