import requests, os, re
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
    if not ids: return []
    stats = yt('videos', part='statistics,contentDetails', id=ids)
    stats_map = {s['id']: s for s in stats.get('items', [])}
    results = []
    for item in items:
        vid_id = item['id']['videoId']
        s = item['snippet']
        st = stats_map.get(vid_id, {})
        views = int(st.get('statistics', {}).get('viewCount', 0))
        dr = st.get('contentDetails', {}).get('duration', 'PT0S')
        dm = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', dr)
        h = int(dm.group(1) or 0) if dm else 0
        m = int(dm.group(2) or 0) if dm else 0
        sec = int(dm.group(3) or 0) if dm else 0
        duration = f'{h}:{m:02d}:{sec:02d}' if h > 0 else f'{m}:{sec:02d}'
        vf = f'{views/1e6:.1f}M' if views>=1000000 else (f'{views/1000:.1f}K' if views>=1000 else str(views))
        results.append({'id':vid_id,'title':s['title'],
            'thumbnail':f'https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg',
            'thumb_fallback':f'https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg',
            'views':vf,'duration':duration,'published':s['publishedAt'][:10]})
    return results

def get_carousel_videos(max_results=7):
    data = yt('search', channelId=CHANNEL_ID, part='snippet', order='viewCount',
              maxResults=max_results, type='video')
    items = data.get('items', [])
    ids = ','.join(i['id']['videoId'] for i in items)
    if not ids: return []
    stats = yt('videos', part='statistics,contentDetails', id=ids)
    stats_map = {s['id']: s for s in stats.get('items', [])}
    results = []
    for item in items:
        vid_id = item['id']['videoId']
        s = item['snippet']
        st = stats_map.get(vid_id, {})
        views = int(st.get('statistics', {}).get('viewCount', 0))
        vf = f'{views/1e6:.1f}M' if views>=1000000 else (f'{views/1000:.1f}K' if views>=1000 else str(views))
        results.append({'id':vid_id,'title':s['title'],
            'thumbnail':f'https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg',
            'thumb_fallback':f'https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg',
            'views':vf})
    return results

def get_community_posts(max_results=4):
    posts = []
    data = yt('activities', channelId=CHANNEL_ID, part='snippet,contentDetails', maxResults=20)
    for item in data.get('items', []):
        t = item.get('snippet', {}).get('type', '')
        s = item['snippet']
        if t in ('bulletinPost', 'recommendation', 'channelItem', 'social'):
            text = s.get('description', '') or s.get('title', 'Community Update')
            img = ''
            for sz in ['high','medium','default']:
                if sz in s.get('thumbnails',{}): img = s['thumbnails'][sz].get('url',''); break
            posts.append({'text':text[:300],'image':img,
                'published':s.get('publishedAt','')[:10],
                'url':'https://www.youtube.com/@anime1point/community'})
            if len(posts) >= max_results: break
    return posts

def carousel_slide(v, idx):
    ts = v['title'].replace("'", '&#39;').replace('"', '&quot;')
    active = ' active' if idx == 0 else ''
    eager = 'eager' if idx < 2 else 'lazy'
    vid = v['id']
    thumb = v['thumbnail']
    fallback = v['thumb_fallback']
    title_short = (v['title'][:80] + '...') if len(v['title']) > 80 else v['title']
    return (
        '<div class="carousel-slide' + active + '" data-vid="' + vid + '">'
        + '<img class="carousel-bg-img" src="' + thumb + '"'
        + ' onerror="this.src=\'' + fallback + '\'"'
        + ' alt="' + ts + '" loading="' + eager + '"/>'
        + '<div class="carousel-overlay"></div>'
        + '<div class="carousel-content">'
        + '<div class="carousel-channel-badge">&#9654;&nbsp;ANIME1POINT</div>'
        + '<h2 class="carousel-title">' + title_short + '</h2>'
        + '<div class="carousel-meta">&#128065; ' + v['views'] + ' views</div>'
        + '<button class="carousel-play-btn" onclick="openModal(\'' + vid + '\',\'' + ts + '\')">&#9654; Watch Now</button>'
        + '</div></div>'
    )

def video_card(v, is_short=False):
    badge = '<span class="badge">SHORT</span>' if is_short else ''
    ts = v['title'].replace("'", '&#39;').replace('"', '&quot;').replace('\n', ' ')
    return (
        '<div class="video-card" onclick="openModal(\'' + v['id'] + '\',\'' + ts + '\')"> '
        + '<div class="thumb-wrap">'
        + '<img src="' + v['thumbnail'] + '" alt="' + v['title'][:50] + '" loading="lazy" onerror="this.src=\'' + v['thumb_fallback'] + '\'" />'
        + '<div class="play-btn"><svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg></div>'
        + '<span class="duration">' + v['duration'] + '</span>' + badge
        + '</div><div class="video-info">'
        + '<h3>' + (v['title'][:90] + ('...' if len(v['title'])>90 else '')) + '</h3>'
        + '<span class="meta">' + v['views'] + ' views &bull; ' + v['published'] + ' &bull; Anime1Point</span>'
        + '</div></div>'
    )

def post_card(p):
    img = ('<img src="'+p['image']+'" loading="lazy" style="width:100%;border-radius:6px;margin-top:10px;"/>') if p.get('image') else ''
    txt = p['text'][:280] + ('...' if len(p['text'])>=280 else '')
    return ('<a class="post-card" href="'+p['url']+'" target="_blank" rel="noopener">'
            + '<div class="post-date">'+p['published']+'</div>'
            + '<p class="post-text">'+txt+'</p>'
            + img + '</a>')

# CSS as a plain string (no f-string, so { } are literal)
CSS = '''
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0d0d1a;color:#e0e0e0}
.carousel-wrap{position:relative;width:100%;height:520px;overflow:hidden;background:#000}
@media(max-width:600px){.carousel-wrap{height:300px}}
.carousel-slide{position:absolute;inset:0;opacity:0;transition:opacity 0.9s ease;pointer-events:none}
.carousel-slide.active{opacity:1;pointer-events:auto}
.carousel-bg-img{width:100%;height:100%;object-fit:cover;display:block;filter:brightness(0.52)}
.carousel-overlay{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.88) 0%,rgba(0,0,0,0.08) 55%,transparent 100%)}
.carousel-content{position:absolute;bottom:90px;left:50%;transform:translateX(-50%);width:90%;max-width:860px;text-align:center}
@media(max-width:600px){.carousel-content{bottom:55px}}
.carousel-channel-badge{display:inline-block;background:#7c3aed;color:#fff;font-size:0.74em;font-weight:700;padding:4px 14px;border-radius:20px;letter-spacing:1px;margin-bottom:12px}
.carousel-title{color:#fff;font-size:1.85em;font-weight:800;line-height:1.25;margin-bottom:10px;text-shadow:0 2px 16px rgba(0,0,0,0.9)}
@media(max-width:600px){.carousel-title{font-size:1.1em}}
.carousel-meta{color:#d1d5db;font-size:0.9em;margin-bottom:18px;text-shadow:0 1px 6px rgba(0,0,0,0.9)}
.carousel-play-btn{background:#ff0000;color:#fff;border:none;padding:14px 38px;font-size:1.05em;font-weight:700;border-radius:6px;cursor:pointer;transition:background 0.2s,transform 0.15s}
.carousel-play-btn:hover{background:#cc0000;transform:scale(1.06)}
.carousel-arrow{position:absolute;top:50%;transform:translateY(-50%);background:rgba(0,0,0,0.45);border:none;color:#fff;font-size:1.5em;width:44px;height:44px;cursor:pointer;border-radius:50%;z-index:10;transition:background 0.2s;display:flex;align-items:center;justify-content:center}
.carousel-arrow:hover{background:rgba(124,58,237,0.85)}
.carousel-arrow.prev{left:14px}.carousel-arrow.next{right:14px}
.carousel-dots{position:absolute;bottom:24px;left:50%;transform:translateX(-50%);display:flex;gap:8px;z-index:10}
.dot{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,0.35);border:none;cursor:pointer;padding:0;transition:background 0.25s,transform 0.25s}
.dot.active{background:#7c3aed;transform:scale(1.4)}
.carousel-progress{position:absolute;bottom:0;left:0;height:4px;background:linear-gradient(90deg,#7c3aed,#a855f7);width:0%;z-index:10;transition:width linear}
header{background:linear-gradient(135deg,#1a0533,#0d1f4d);padding:28px 20px 20px;text-align:center;border-bottom:3px solid #7c3aed}
header h1{font-size:2.1em;color:#fff;letter-spacing:2px;text-shadow:0 0 20px #7c3aed}
header p.tagline{color:#a78bfa;font-size:1em;margin-top:8px}
.also-known{background:#1a1a2e;padding:8px 20px;text-align:center;font-size:0.9em;color:#9ca3af;border-bottom:1px solid #2d2d4e}
.also-known span{color:#a78bfa;font-weight:600}
nav{background:#111128;padding:10px 20px;text-align:center;border-bottom:1px solid #2d2d4e;position:sticky;top:0;z-index:100}
nav a{color:#a78bfa;text-decoration:none;margin:0 12px;font-size:0.9em;font-weight:600}
nav a:hover{color:#fff}
.container{max-width:1000px;margin:0 auto;padding:40px 20px}
.about{background:#161625;border-left:4px solid #7c3aed;padding:24px;border-radius:8px;margin-bottom:40px;line-height:1.85}
.about h2{color:#a78bfa;margin-bottom:12px;font-size:1.4em}
.about p{color:#d1d5db}
.cta-btn{display:inline-block;background:#ff0000;color:#fff;padding:13px 34px;border-radius:6px;text-decoration:none;font-size:1em;font-weight:700;margin-top:20px;transition:background 0.2s}
.cta-btn:hover{background:#cc0000}
.section-title{color:#a78bfa;font-size:1.5em;margin:40px 0 20px;border-bottom:2px solid #2d2d4e;padding-bottom:8px}
.updated{color:#4b5563;font-size:0.82em;margin-bottom:16px}
.videos-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:22px;margin-bottom:40px}
.video-card{background:#1a1a2e;border-radius:10px;overflow:hidden;border:1px solid #2d2d4e;transition:transform 0.2s,border-color 0.2s;cursor:pointer}
.video-card:hover{transform:translateY(-5px);border-color:#7c3aed}
.thumb-wrap{position:relative;width:100%;padding-top:56.25%;overflow:hidden;background:#0d0d1a}
.thumb-wrap img{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;transition:transform 0.3s}
.video-card:hover .thumb-wrap img{transform:scale(1.04)}
.play-btn{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:50px;height:50px;background:rgba(255,0,0,0.88);border-radius:50%;display:flex;align-items:center;justify-content:center;pointer-events:none}
.play-btn svg{width:20px;height:20px;fill:#fff;margin-left:3px}
.duration{position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.82);color:#fff;font-size:0.76em;padding:2px 6px;border-radius:3px}
.badge{position:absolute;top:8px;left:8px;background:#7c3aed;color:#fff;font-size:0.72em;padding:2px 8px;border-radius:3px;font-weight:700}
.video-info{padding:14px}
.video-info h3{color:#e0e0e0;font-size:0.9em;line-height:1.45;margin-bottom:6px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.video-info .meta{color:#6b7280;font-size:0.8em}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.88);z-index:999;align-items:center;justify-content:center}
.modal-overlay.active{display:flex}
.modal-box{background:#111128;border-radius:12px;overflow:hidden;width:90%;max-width:860px;position:relative;border:2px solid #7c3aed}
.modal-close{position:absolute;top:10px;right:14px;background:none;border:none;color:#fff;font-size:1.8em;cursor:pointer;z-index:10;line-height:1}
.modal-box iframe{width:100%;aspect-ratio:16/9;display:block;border:none}
.modal-title{padding:12px 16px;color:#a78bfa;font-size:0.95em;font-weight:600}
.playlists{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:20px;margin-bottom:40px}
.playlist-card{background:#1a1a2e;border-radius:10px;overflow:hidden;border:1px solid #2d2d4e;transition:transform 0.2s,border-color 0.2s}
.playlist-card:hover{transform:translateY(-4px);border-color:#7c3aed}
.playlist-thumb{position:relative;width:100%;padding-top:56.25%;background:#0d0d1a;overflow:hidden}
.playlist-thumb img{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover}
.playlist-count{position:absolute;top:0;right:0;background:rgba(0,0,0,0.82);color:#fff;font-size:0.78em;padding:4px 8px}
.playlist-info{padding:14px}
.playlist-info h3{color:#a78bfa;margin-bottom:6px;font-size:1em}
.playlist-info p{color:#9ca3af;font-size:0.85em;margin-bottom:10px;line-height:1.5}
.playlist-info a{color:#60a5fa;font-size:0.88em;text-decoration:none;font-weight:600}
.posts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin-bottom:40px}
.post-card{background:#1a1a2e;border-radius:10px;border:1px solid #2d2d4e;padding:18px;text-decoration:none;color:inherit;display:block;transition:transform 0.2s,border-color 0.2s}
.post-card:hover{transform:translateY(-4px);border-color:#7c3aed}
.post-date{color:#6b7280;font-size:0.8em;margin-bottom:8px}
.post-text{color:#d1d5db;font-size:0.9em;line-height:1.6}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0 40px}
.tag{background:#1e1e3a;border:1px solid #4c1d95;color:#a78bfa;padding:5px 13px;border-radius:20px;font-size:0.83em}
.sub-banner{background:linear-gradient(135deg,#4c1d95,#1e3a8a);border-radius:12px;padding:32px 24px;text-align:center;margin:40px 0}
.sub-banner h2{color:#fff;font-size:1.5em;margin-bottom:10px}
.sub-banner p{color:#c4b5fd;margin-bottom:20px}
footer{background:#0a0a14;text-align:center;padding:30px 20px;color:#4b5563;border-top:1px solid #1f2937;font-size:0.88em}
footer a{color:#60a5fa;text-decoration:none}
@media(max-width:600px){.modal-box{width:97%}nav a{margin:0 7px;font-size:0.82em}}
'''

# JS as a plain string - braces are real JS braces, not Python f-string
JS = '''
function openModal(id, title) {
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalIframe').src = 'https://www.youtube.com/embed/' + id + '?autoplay=1&rel=0';
  document.getElementById('videoModal').classList.add('active');
  document.body.style.overflow = 'hidden';
}
function closeModal() {
  document.getElementById('videoModal').classList.remove('active');
  document.getElementById('modalIframe').src = '';
  document.body.style.overflow = '';
}
function closeModalOutside(e) {
  if (e.target === document.getElementById('videoModal')) closeModal();
}
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeModal(); });
(function() {
  var slides = document.querySelectorAll('.carousel-slide');
  var dots = document.querySelectorAll('.dot');
  var progress = document.getElementById('carouselProgress');
  var cur = 0, total = slides.length, timer = null, paused = false;
  var INTERVAL = 4000;
  function goTo(n) {
    slides[cur].classList.remove('active');
    dots[cur].classList.remove('active');
    cur = (n + total) % total;
    slides[cur].classList.add('active');
    dots[cur].classList.add('active');
    resetProgress();
  }
  function resetProgress() {
    progress.style.transition = 'none';
    progress.style.width = '0%';
    setTimeout(function() {
      progress.style.transition = 'width ' + INTERVAL + 'ms linear';
      progress.style.width = '100%';
    }, 30);
  }
  function startAuto() {
    clearInterval(timer);
    timer = setInterval(function() { if (!paused) goTo(cur + 1); }, INTERVAL);
  }
  window.goToSlide = function(n) { goTo(n); startAuto(); };
  window.prevSlide = function() { goTo(cur - 1); startAuto(); };
  window.nextSlide = function() { goTo(cur + 1); startAuto(); };
  window.pauseCarousel = function() { paused = true; progress.style.transition = 'none'; };
  window.resumeCarousel = function() { paused = false; resetProgress(); };
  startAuto();
  resetProgress();
})();
'''

def build_html(carousel, videos, shorts, posts):
    updated = datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')
    slides_html = '\n'.join(carousel_slide(v, i) for i, v in enumerate(carousel))
    dot_html = '\n'.join(
        '<button class="dot' + (' active' if i == 0 else '') + '" onclick="goToSlide(' + str(i) + ')"></button>'
        for i in range(len(carousel))
    )
    video_cards = '\n'.join(video_card(v) for v in videos)
    short_cards = '\n'.join(video_card(v, is_short=True) for v in shorts)
    if posts:
        post_cards_html = '\n'.join(post_card(p) for p in posts)
    else:
        post_cards_html = ('<p style="color:#9ca3af;padding:20px 0;">Community posts update automatically. '
                          '<a href="https://www.youtube.com/@anime1point/community" style="color:#60a5fa" target="_blank" rel="noopener">'
                          'View on YouTube &rarr;</a></p>')
    # Build HTML using plain string concatenation - no f-string near CSS/JS
    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0"/>\n'
        '<title>Anime1Point | Anime One Point | Anime Breakdown YouTube Channel</title>\n'
        '<meta name="description" content="Anime1Point (Anime One Point) - YouTube anime breakdowns, That Time I Got Reincarnated as a Slime Season 4, Tensura lore."/>\n'
        '<meta name="keywords" content="Anime1Point,Anime One Point,AnimeOnePoint,Anime Point,anime breakdown,That Time I Got Reincarnated as a Slime,Tensura Season 4,Rimuru Tempest"/>\n'
        '<meta property="og:title" content="Anime1Point | Anime One Point"/>\n'
        '<meta property="og:url" content="https://anime1point-ctrl.github.io"/>\n'
        '<link rel="canonical" href="https://anime1point-ctrl.github.io"/>\n'
        '<style>' + CSS + '</style>\n'
        '</head>\n<body>\n'
        '<!-- HERO CAROUSEL -->\n'
        '<div class="carousel-wrap" id="carousel" onmouseenter="pauseCarousel()" onmouseleave="resumeCarousel()">\n'
        + slides_html + '\n'
        + '<button class="carousel-arrow prev" onclick="prevSlide()" aria-label="Previous">&#10094;</button>\n'
        + '<button class="carousel-arrow next" onclick="nextSlide()" aria-label="Next">&#10095;</button>\n'
        + '<div class="carousel-dots">' + dot_html + '</div>\n'
        + '<div class="carousel-progress" id="carouselProgress"></div>\n'
        + '</div>\n'
        + '<header><h1>&#9654; Anime1Point</h1><p class="tagline">Anime Breakdown &bull; Anime Explained &bull; Deep Story Analysis</p></header>\n'
        + '<div class="also-known">Also known as <span>Anime One Point</span> &bull; <span>AnimeOnePoint</span> &bull; <span>Anime Point</span> &bull; <span>Anime 1 Point</span></div>\n'
        + '<nav><a href="#videos">Videos</a><a href="#shorts">Shorts</a><a href="#posts">Community</a><a href="#playlists">Playlists</a><a href="#about">About</a><a href="https://www.youtube.com/@anime1point" target="_blank" rel="noopener">&#9654; YouTube</a></nav>\n'
        + '<div class="container">'
        + '<div class="about" id="about"><h2>About Anime1Point</h2>'
        + '<p>Welcome to <strong>Anime1Point</strong> &mdash; also known as <strong>Anime One Point</strong>, <strong>AnimeOnePoint</strong>, and <strong>Anime Point</strong> &mdash; your ultimate destination for anime breakdowns on YouTube. We specialize in <strong>That Time I Got Reincarnated as a Slime (Tensura) Season 4</strong> episode reviews, manga analysis, anime lore deep dives, and story breakdowns.</p>'
        + '<a href="https://www.youtube.com/@anime1point?sub_confirmation=1" class="cta-btn" target="_blank" rel="noopener">&#9654; Subscribe on YouTube</a></div>'
        + '<h2 class="section-title" id="videos">&#127916; Latest Videos</h2>'
        + '<p class="updated">&#128260; Auto-updated: ' + updated + ' &bull; Click any video to watch (views count on YouTube!)</p>'
        + '<div class="videos-grid">' + video_cards + '</div>'
        + '<div style="text-align:center;margin-bottom:40px"><a href="https://www.youtube.com/@anime1point/videos" target="_blank" rel="noopener" class="cta-btn" style="background:#7c3aed">&#9654; See All Videos on YouTube</a></div>'
        + '<h2 class="section-title" id="shorts">&#9889; Latest Shorts</h2>'
        + '<div class="videos-grid">' + short_cards + '</div>'
        + '<div style="text-align:center;margin-bottom:40px"><a href="https://www.youtube.com/@anime1point/shorts" target="_blank" rel="noopener" class="cta-btn" style="background:#7c3aed">&#9654; See All Shorts on YouTube</a></div>'
        + '<h2 class="section-title" id="posts">&#128172; Community Posts</h2>'
        + '<p class="updated">Latest updates, polls, and announcements from the Anime1Point community.</p>'
        + '<div class="posts-grid">' + post_cards_html + '</div>'
        + '<div style="text-align:center;margin-bottom:40px"><a href="https://www.youtube.com/@anime1point/community" target="_blank" rel="noopener" class="cta-btn" style="background:#7c3aed">&#9654; See All Posts on YouTube</a></div>'
        + '<h2 class="section-title" id="playlists">&#128203; Playlists</h2>'
        + '<div class="playlists">'
        + '<div class="playlist-card"><div class="playlist-thumb"><img src="https://i.ytimg.com/vi/ZVmqQk1GbqE/maxresdefault.jpg" alt="Tensura S4" loading="lazy"/><span class="playlist-count">16 videos</span></div><div class="playlist-info"><h3>Tensura Season 4 Reviews</h3><p>Full episode breakdown of That Time I Got Reincarnated as a Slime Season 4.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Watch &rarr;</a></div></div>'
        + '<div class="playlist-card"><div class="playlist-thumb"><img src="https://i.ytimg.com/vi/ommA4DBy5RQ/maxresdefault.jpg" alt="Tensura S4 Shorts" loading="lazy"/><span class="playlist-count">116+ videos</span></div><div class="playlist-info"><h3>Tensura Season 4 Shorts</h3><p>116+ short clips covering key moments and character breakdowns.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Watch &rarr;</a></div></div>'
        + '<div class="playlist-card"><div class="playlist-thumb"><img src="https://i.ytimg.com/vi/o_PazOqPg0I/maxresdefault.jpg" alt="Pokemon Play" loading="lazy"/><span class="playlist-count">113+ videos</span></div><div class="playlist-info"><h3>Pokemon Play</h3><p>113+ Pokemon-themed videos and quizzes.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Watch &rarr;</a></div></div>'
        + '</div>'
        + '<div class="sub-banner"><h2>&#9654; Join the Anime1Point Community</h2><p>New episodes every week &bull; Tensura Season 4 &bull; Anime Breakdowns &bull; Manga Analysis</p><a href="https://www.youtube.com/@anime1point?sub_confirmation=1" class="cta-btn" target="_blank" rel="noopener">Subscribe for Free</a></div>'
        + '<h2 class="section-title">&#127991; Topics We Cover</h2>'
        + '<div class="tags"><span class="tag">Anime1Point</span><span class="tag">Anime One Point</span><span class="tag">AnimeOnePoint</span><span class="tag">Anime Point</span><span class="tag">That Time I Got Reincarnated as a Slime</span><span class="tag">Tensura Season 4</span><span class="tag">Rimuru Tempest</span><span class="tag">Diablo Tensura</span><span class="tag">Milim Nava</span><span class="tag">Veldora</span><span class="tag">Anime Breakdown</span><span class="tag">Anime Explained</span><span class="tag">Manga Analysis</span><span class="tag">Anime Lore</span><span class="tag">Isekai Anime</span></div>'
        + '</div>'
        + '<div class="modal-overlay" id="videoModal" onclick="closeModalOutside(event)"><div class="modal-box"><button class="modal-close" onclick="closeModal()">&times;</button><div class="modal-title" id="modalTitle"></div><iframe id="modalIframe" src="" allowfullscreen allow="autoplay; encrypted-media"></iframe></div></div>'
        + '<footer><p>&copy; 2026 <strong>Anime1Point</strong> (Anime One Point) &mdash; All Rights Reserved</p>'
        + '<p style="margin-top:10px"><a href="https://www.youtube.com/@anime1point">YouTube</a> &bull; <a href="https://www.youtube.com/@anime1point/videos">Videos</a> &bull; <a href="https://www.youtube.com/@anime1point/shorts">Shorts</a> &bull; <a href="https://www.youtube.com/@anime1point/community">Community</a> &bull; <a href="https://www.youtube.com/@anime1point/playlists">Playlists</a></p>'
        + '<p style="margin-top:10px;font-size:0.82em">Anime1Point &bull; Anime One Point &bull; AnimeOnePoint &bull; Anime Point &bull; Tensura Season 4</p></footer>'
        + '<script>' + JS + '<\/script>'
        + '</body></html>'
    )
    return html

if __name__ == '__main__':
    print('Fetching top carousel videos...')
    carousel = get_carousel_videos(max_results=7)
    print(f'Got {len(carousel)} carousel slides')
    print('Fetching latest videos...')
    videos = get_videos(max_results=8, video_type='video')
    print(f'Got {len(videos)} videos')
    print('Fetching latest shorts...')
    shorts = get_videos(max_results=6, video_type='short')
    print(f'Got {len(shorts)} shorts')
    print('Fetching community posts...')
    posts = get_community_posts(max_results=4)
    print(f'Got {len(posts)} posts')
    html = build_html(carousel, videos, shorts, posts)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Done! index.html rebuilt with working carousel.')