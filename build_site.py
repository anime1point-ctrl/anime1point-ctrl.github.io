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

CSS = open('style.css').read() if __import__('os').path.exists('style.css') else ''

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
    # Read CSS from file (written separately, keeps build_site.py clean)
    css_tag = '<link rel="stylesheet" href="style.css"/>'
    lines = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8"/>',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0"/>',
        '<title>Anime1Point | Anime One Point | Anime Breakdown YouTube Channel</title>',
        '<meta name="description" content="Anime1Point (Anime One Point) - YouTube anime breakdowns, That Time I Got Reincarnated as a Slime Season 4, Tensura lore, manga analysis."/>',
        '<meta name="keywords" content="Anime1Point,Anime One Point,AnimeOnePoint,Anime Point,anime breakdown,That Time I Got Reincarnated as a Slime,Tensura Season 4,Rimuru Tempest,Diablo"/>',
        '<meta property="og:title" content="Anime1Point | Anime One Point"/>',
        '<meta property="og:url" content="https://anime1point-ctrl.github.io"/>',
        '<link rel="canonical" href="https://anime1point-ctrl.github.io"/>',
        css_tag,
        '</head>',
        '<body>',
        '<div class="carousel-wrap" id="carousel" onmouseenter="pauseCarousel()" onmouseleave="resumeCarousel()">',
        slides_html,
        '<button class="carousel-arrow prev" onclick="prevSlide()" aria-label="Previous">&#10094;</button>',
        '<button class="carousel-arrow next" onclick="nextSlide()" aria-label="Next">&#10095;</button>',
        '<div class="carousel-dots">' + dot_html + '</div>',
        '<div class="carousel-progress" id="carouselProgress"></div>',
        '</div>',
        '<header><h1>&#9654; Anime1Point</h1><p class="tagline">Anime Breakdown &bull; Anime Explained &bull; Deep Story Analysis</p></header>',
        '<div class="also-known">Also known as <span>Anime One Point</span> &bull; <span>AnimeOnePoint</span> &bull; <span>Anime Point</span> &bull; <span>Anime 1 Point</span></div>',
        '<nav><a href="#videos">Videos</a><a href="#shorts">Shorts</a><a href="#posts">Community</a><a href="#playlists">Playlists</a><a href="#about">About</a><a href="https://www.youtube.com/@anime1point" target="_blank" rel="noopener">&#9654; YouTube</a></nav>',
        '<div class="container">',
        '<div class="about" id="about"><h2>About Anime1Point</h2><p>Welcome to <strong>Anime1Point</strong> &mdash; also known as <strong>Anime One Point</strong>, <strong>AnimeOnePoint</strong>, and <strong>Anime Point</strong> &mdash; your ultimate destination for anime breakdowns on YouTube. We specialize in <strong>That Time I Got Reincarnated as a Slime (Tensura) Season 4</strong> episode reviews, manga analysis, anime lore deep dives, and story breakdowns.</p><a href="https://www.youtube.com/@anime1point?sub_confirmation=1" class="cta-btn" target="_blank" rel="noopener">&#9654; Subscribe on YouTube</a></div>',
        '<h2 class="section-title" id="videos">&#127916; Latest Videos</h2>',
        '<p class="updated">&#128260; Auto-updated: ' + updated + ' &bull; Click any video to watch (views count on YouTube!)</p>',
        '<div class="videos-grid">' + video_cards + '</div>',
        '<div style="text-align:center;margin-bottom:40px"><a href="https://www.youtube.com/@anime1point/videos" target="_blank" rel="noopener" class="cta-btn" style="background:#7c3aed">&#9654; See All Videos on YouTube</a></div>',
        '<h2 class="section-title" id="shorts">&#9889; Latest Shorts</h2>',
        '<div class="videos-grid">' + short_cards + '</div>',
        '<div style="text-align:center;margin-bottom:40px"><a href="https://www.youtube.com/@anime1point/shorts" target="_blank" rel="noopener" class="cta-btn" style="background:#7c3aed">&#9654; See All Shorts on YouTube</a></div>',
        '<h2 class="section-title" id="posts">&#128172; Community Posts</h2>',
        '<p class="updated">Latest updates, polls, and announcements from the Anime1Point community.</p>',
        '<div class="posts-grid">' + post_cards_html + '</div>',
        '<div style="text-align:center;margin-bottom:40px"><a href="https://www.youtube.com/@anime1point/community" target="_blank" rel="noopener" class="cta-btn" style="background:#7c3aed">&#9654; See All Posts on YouTube</a></div>',
        '<h2 class="section-title" id="playlists">&#128203; Playlists</h2>',
        '<div class="playlists">',
        '<div class="playlist-card"><div class="playlist-thumb"><img src="https://i.ytimg.com/vi/ZVmqQk1GbqE/maxresdefault.jpg" alt="Tensura S4" loading="lazy"/><span class="playlist-count">16 videos</span></div><div class="playlist-info"><h3>Tensura Season 4 Reviews</h3><p>Full episode breakdown of That Time I Got Reincarnated as a Slime Season 4.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Watch &rarr;</a></div></div>',
        '<div class="playlist-card"><div class="playlist-thumb"><img src="https://i.ytimg.com/vi/ommA4DBy5RQ/maxresdefault.jpg" alt="Tensura S4 Shorts" loading="lazy"/><span class="playlist-count">116+ videos</span></div><div class="playlist-info"><h3>Tensura Season 4 Shorts</h3><p>116+ short clips covering key moments and character breakdowns.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Watch &rarr;</a></div></div>',
        '<div class="playlist-card"><div class="playlist-thumb"><img src="https://i.ytimg.com/vi/o_PazOqPg0I/maxresdefault.jpg" alt="Pokemon Play" loading="lazy"/><span class="playlist-count">113+ videos</span></div><div class="playlist-info"><h3>Pokemon Play</h3><p>113+ Pokemon-themed videos and quizzes.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Watch &rarr;</a></div></div>',
        '</div>',
        '<div class="sub-banner"><h2>&#9654; Join the Anime1Point Community</h2><p>New episodes every week &bull; Tensura Season 4 &bull; Anime Breakdowns &bull; Manga Analysis</p><a href="https://www.youtube.com/@anime1point?sub_confirmation=1" class="cta-btn" target="_blank" rel="noopener">Subscribe for Free</a></div>',
        '<h2 class="section-title">&#127991; Topics We Cover</h2>',
        '<div class="tags"><span class="tag">Anime1Point</span><span class="tag">Anime One Point</span><span class="tag">AnimeOnePoint</span><span class="tag">Anime Point</span><span class="tag">That Time I Got Reincarnated as a Slime</span><span class="tag">Tensura Season 4</span><span class="tag">Rimuru Tempest</span><span class="tag">Diablo Tensura</span><span class="tag">Milim Nava</span><span class="tag">Veldora</span><span class="tag">Anime Breakdown</span><span class="tag">Anime Explained</span><span class="tag">Manga Analysis</span><span class="tag">Anime Lore</span><span class="tag">Isekai Anime</span></div>',
        '</div>',
        '<div class="modal-overlay" id="videoModal" onclick="closeModalOutside(event)"><div class="modal-box"><button class="modal-close" onclick="closeModal()">&times;</button><div class="modal-title" id="modalTitle"></div><iframe id="modalIframe" src="" allowfullscreen allow="autoplay; encrypted-media"></iframe></div></div>',
        '<footer><p>&copy; 2026 <strong>Anime1Point</strong> (Anime One Point) &mdash; All Rights Reserved</p><p style="margin-top:10px"><a href="https://www.youtube.com/@anime1point">YouTube</a> &bull; <a href="https://www.youtube.com/@anime1point/videos">Videos</a> &bull; <a href="https://www.youtube.com/@anime1point/shorts">Shorts</a> &bull; <a href="https://www.youtube.com/@anime1point/community">Community</a> &bull; <a href="https://www.youtube.com/@anime1point/playlists">Playlists</a></p><p style="margin-top:10px;font-size:0.82em">Anime1Point &bull; Anime One Point &bull; AnimeOnePoint &bull; Anime Point &bull; Tensura Season 4</p></footer>',
        '<script src="carousel.js"><' + '/script>',
        '</body></html>'
    ]
    return '\n'.join(lines)

if __name__ == '__main__':
    print('Fetching carousel videos (top by views)...')
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
    print('Done! index.html rebuilt - carousel arrows and dots now work.')