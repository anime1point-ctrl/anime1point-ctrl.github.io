import requests, os, re
from datetime import datetime, timezone

API_KEY    = os.environ['YOUTUBE_API_KEY']
CHANNEL_ID = os.environ['CHANNEL_ID']
BASE       = 'https://www.googleapis.com/youtube/v3'

def yt(endpoint, **params):
    params['key'] = API_KEY
    r = requests.get(f'{BASE}/{endpoint}', params=params)
    return r.json()

def enrich(items):
    """Add stats+duration to a list of search result items."""
    if not items: return []
    ids = ','.join(i['id']['videoId'] for i in items)
    stats = yt('videos', part='statistics,contentDetails', id=ids)
    sm = {s['id']: s for s in stats.get('items', [])}
    out = []
    for item in items:
        vid = item['id']['videoId']
        s   = item['snippet']
        st  = sm.get(vid, {})
        views = int(st.get('statistics', {}).get('viewCount', 0))
        dr  = st.get('contentDetails', {}).get('duration', 'PT0S')
        dm  = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', dr)
        h   = int(dm.group(1) or 0) if dm else 0
        m   = int(dm.group(2) or 0) if dm else 0
        sec = int(dm.group(3) or 0) if dm else 0
        dur = f'{h}:{m:02d}:{sec:02d}' if h else f'{m}:{sec:02d}'
        vf  = (f'{views/1e6:.1f}M' if views>=1_000_000
               else f'{views/1000:.1f}K' if views>=1000 else str(views))
        out.append({'id':vid,'title':s['title'],
            'thumbnail':f'https://i.ytimg.com/vi/{vid}/maxresdefault.jpg',
            'fallback':f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg',
            'views':vf,'views_raw':views,'duration':dur,
            'published':s['publishedAt'][:10]})
    return out

def get_carousel(n=7):
    items = yt('search', channelId=CHANNEL_ID, part='snippet',
               order='viewCount', maxResults=n, type='video').get('items',[])
    return enrich(items)

def get_most_watched(n=8):
    items = yt('search', channelId=CHANNEL_ID, part='snippet',
               order='viewCount', maxResults=n, type='video').get('items',[])
    result = enrich(items)
    return sorted(result, key=lambda v: v['views_raw'], reverse=True)

def get_latest_videos(n=8):
    items = yt('search', channelId=CHANNEL_ID, part='snippet',
               order='date', maxResults=n, type='video',
               videoDuration='medium').get('items',[])
    result = enrich(items)
    return sorted(result, key=lambda v: v['published'], reverse=True)

def get_latest_shorts(n=6):
    items = yt('search', channelId=CHANNEL_ID, part='snippet',
               order='date', maxResults=n, type='video',
               videoDuration='short').get('items',[])
    return enrich(items)

def get_community_posts(n=4):
    posts = []
    data  = yt('activities', channelId=CHANNEL_ID,
               part='snippet,contentDetails', maxResults=20)
    for item in data.get('items', []):
        t = item.get('snippet', {}).get('type', '')
        s = item['snippet']
        if t in ('bulletinPost','recommendation','channelItem','social'):
            text = s.get('description','') or s.get('title','Community Update')
            img  = next((s['thumbnails'][sz]['url']
                        for sz in ['high','medium','default']
                        if sz in s.get('thumbnails',{})), '')
            posts.append({'text':text[:300],'image':img,
                'published':s.get('publishedAt','')[:10],
                'url':'https://www.youtube.com/@anime1point/community'})
            if len(posts)>=n: break
    return posts

def safe(t):
    return t.replace("'","&#39;").replace('"','&quot;').replace('\n',' ')

def carousel_slide(v, idx):
    ts     = safe(v['title'])
    active = ' active' if idx==0 else ''
    eager  = 'eager' if idx<2 else 'lazy'
    short  = (v['title'][:78]+'...') if len(v['title'])>78 else v['title']
    return (
        '<div class="carousel-slide'+active+'" data-vid="'+v['id']+'">'
        +'<img class="carousel-bg-img" src="'+v['thumbnail']+'"'
        +' onerror="this.src=\''+v['fallback']+'\';" alt="'+ts+'" loading="'+eager+'"/>'
        +'<div class="carousel-overlay"></div>'
        +'<div class="carousel-content">'
        +'<div class="carousel-channel-badge">&#9654;&nbsp;ANIME1POINT</div>'
        +'<h2 class="carousel-title">'+short+'</h2>'
        +'<div class="carousel-meta">&#128065; '+v['views']+' views</div>'
        +'<button class="carousel-play-btn" onclick="openModal(\''+v['id']+'\',' 
           +'\''+ts+'\')" >&#9654; Watch Now</button>'
        +'</div></div>'
    )

def video_card(v, badge_text=''):
    ts    = safe(v['title'])
    badge = ('<span class="badge badge-'+badge_text.lower()+'">'+badge_text+'</span>') if badge_text else ''
    short = (v['title'][:88]+'...') if len(v['title'])>88 else v['title']
    return (
        '<div class="video-card" onclick="openModal(\''+v['id']+'\',' 
           +'\''+ts+'\')">'
        +'<div class="thumb-wrap">'
        +'<img src="'+v['thumbnail']+'" alt="'+v['title'][:55]+'" loading="lazy"'
        +' onerror="this.src=\''+v['fallback']+'\'"/>'
        +'<div class="play-btn"><svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg></div>'
        +'<span class="duration">'+v['duration']+'</span>'
        +badge
        +'</div>'
        +'<div class="video-info">'
        +'<h3>'+short+'</h3>'
        +'<span class="meta">'+v['views']+' views &bull; '+v['published']+'</span>'
        +'</div></div>'
    )

def post_card(p):
    img = ('<img src="'+p['image']+'" loading="lazy" style="width:100%;border-radius:6px;margin-top:10px;"/>') if p.get('image') else ''
    txt = p['text'][:260]+('...' if len(p['text'])>260 else '')
    return ('<a class="post-card" href="'+p['url']+'" target="_blank" rel="noopener">'
            +'<div class="post-date">'+p['published']+'</div>'
            +'<p class="post-text">'+txt+'</p>'+img+'</a>')

def section(icon, title, anchor, cards_html, btn_url, btn_label):
    return (
        '<h2 class="section-title" id="'+anchor+'">'+icon+' '+title+'</h2>'
        +'<div class="videos-grid">'+cards_html+'</div>'
        +'<div class="section-footer">'
        +'<a href="'+btn_url+'" target="_blank" rel="noopener" class="cta-btn cta-purple">&#9654; '+btn_label+'</a>'
        +'</div>'
    )

def build_html(carousel_vids, most_watched, latest_vids, latest_shorts, posts):
    updated = datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')

    # Carousel
    slides  = '\n'.join(carousel_slide(v,i) for i,v in enumerate(carousel_vids))
    dot_html = '\n'.join(
        '<button class="dot'+(' active' if i==0 else '')+'" onclick="goToSlide('+str(i)+')"></button>'
        for i in range(len(carousel_vids)))

    # Most Watched â rank badge (1st, 2nd, â¦)
    mw_cards = '\n'.join(video_card(v, badge_text='#'+str(i+1)) for i,v in enumerate(most_watched))

    # Latest Videos
    lv_cards = '\n'.join(video_card(v, badge_text='NEW') for v in latest_vids)

    # Latest Shorts
    ls_cards = '\n'.join(video_card(v, badge_text='SHORT') for v in latest_shorts)

    # Community Posts
    if posts:
        pc_html = '\n'.join(post_card(p) for p in posts)
    else:
        pc_html = ('<p style="color:#9ca3af;padding:20px 0;">Community posts update automatically. '
                   '<a href="https://www.youtube.com/@anime1point/community" style="color:#60a5fa"'
                   ' target="_blank" rel="noopener">View on YouTube &rarr;</a></p>')

    lines = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8"/>',
        '<meta name="viewport" content="width=device-width,initial-scale=1.0"/>',
        '<title>Anime1Point | Anime One Point | Anime Breakdown YouTube Channel</title>',
        '<meta name="description" content="Anime1Point (Anime One Point) â anime breakdowns, That Time I Got Reincarnated as a Slime Season 4, Tensura lore, manga analysis."/>',
        '<meta name="keywords" content="Anime1Point,Anime One Point,AnimeOnePoint,Anime Point,anime breakdown,That Time I Got Reincarnated as a Slime,Tensura Season 4,Rimuru Tempest,Diablo"/>',
        '<meta property="og:title" content="Anime1Point | Anime One Point"/>',
        '<meta property="og:url" content="https://anime1point-ctrl.github.io"/>',
        '<link rel="canonical" href="https://anime1point-ctrl.github.io"/>',
        '<link rel="stylesheet" href="style.css"/>',
        '</head>',
        '<body>',
        # ââ HERO CAROUSEL ââââââââââââââââââââââââââââââââââââââââââââââââ
        '<div class="carousel-wrap" id="carousel" onmouseenter="pauseCarousel()" onmouseleave="resumeCarousel()">',
        slides,
        '<button class="carousel-arrow prev" onclick="prevSlide()" aria-label="Previous">&#10094;</button>',
        '<button class="carousel-arrow next" onclick="nextSlide()" aria-label="Next">&#10095;</button>',
        '<div class="carousel-dots">'+dot_html+'</div>',
        '<div class="carousel-progress" id="carouselProgress"></div>',
        '</div>',
        # ââ HEADER âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
        '<header>',
        '<h1>&#9654; Anime1Point</h1>',
        '<p class="tagline">Anime Breakdown &bull; Anime Explained &bull; Deep Story Analysis</p>',
        '</header>',
        '<div class="also-known">Also known as <span>Anime One Point</span> &bull; <span>AnimeOnePoint</span> &bull; <span>Anime Point</span> &bull; <span>Anime 1 Point</span></div>',
        # ââ NAV ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
        '<nav>',
        '<a href="#most-watched">&#128293; Most Watched</a>',
        '<a href="#latest">&#128196; Latest</a>',
        '<a href="#shorts">&#9889; Shorts</a>',
        '<a href="#community">&#128172; Community</a>',
        '<a href="#playlists">&#128203; Playlists</a>',
        '<a href="#about">About</a>',
        '<a href="https://www.youtube.com/@anime1point" target="_blank" rel="noopener">&#9654; YouTube</a>',
        '</nav>',
        '<div class="container">',
        # ââ AUTO-UPDATE NOTICE ââââââââââââââââââââââââââââââââââââââââââââ
        '<p class="updated">&#128260; Last updated: '+updated+' &bull; All videos clickable &mdash; views count on YouTube!</p>',
        # ââ MOST WATCHED âââââââââââââââââââââââââââââââââââââââââââââââââ
        section('&#128293;','Most Watched','most-watched', mw_cards,
                'https://www.youtube.com/@anime1point/videos?sort=p','See All on YouTube'),
        # ââ LATEST VIDEOS ââââââââââââââââââââââââââââââââââââââââââââââââ
        section('&#128196;','Latest Uploads','latest', lv_cards,
                'https://www.youtube.com/@anime1point/videos','See All Videos'),
        # ââ LATEST SHORTS ââââââââââââââââââââââââââââââââââââââââââââââââ
        section('&#9889;','Latest Shorts','shorts', ls_cards,
                'https://www.youtube.com/@anime1point/shorts','See All Shorts'),
        # ââ COMMUNITY POSTS âââââââââââââââââââââââââââââââââââââââââââââ
        '<h2 class="section-title" id="community">&#128172; Community Posts</h2>',
        '<p class="section-sub">Latest updates, polls and announcements from Anime1Point.</p>',
        '<div class="posts-grid">'+pc_html+'</div>',
        '<div class="section-footer"><a href="https://www.youtube.com/@anime1point/community" target="_blank" rel="noopener" class="cta-btn cta-purple">&#9654; See All Community Posts</a></div>',
        # ââ PLAYLISTS ââââââââââââââââââââââââââââââââââââââââââââââââââââ
        '<h2 class="section-title" id="playlists">&#128203; Playlists</h2>',
        '<div class="playlists">',
        '<div class="playlist-card"><div class="playlist-thumb"><img src="https://i.ytimg.com/vi/ZVmqQk1GbqE/maxresdefault.jpg" alt="Tensura S4 Reviews" loading="lazy"/><span class="playlist-count">16 videos</span></div><div class="playlist-info"><h3>Tensura Season 4 Reviews</h3><p>Full episode breakdown of That Time I Got Reincarnated as a Slime Season 4.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Watch &rarr;</a></div></div>',
        '<div class="playlist-card"><div class="playlist-thumb"><img src="https://i.ytimg.com/vi/ommA4DBy5RQ/maxresdefault.jpg" alt="Tensura S4 Shorts" loading="lazy"/><span class="playlist-count">116+ videos</span></div><div class="playlist-info"><h3>Tensura Season 4 Shorts</h3><p>116+ short clips covering key moments and character breakdowns.</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Watch &rarr;</a></div></div>',
        '<div class="playlist-card"><div class="playlist-thumb"><img src="https://i.ytimg.com/vi/o_PazOqPg0I/maxresdefault.jpg" alt="Pokemon Play" loading="lazy"/><span class="playlist-count">113+ videos</span></div><div class="playlist-info"><h3>Pokemon Play</h3><p>113+ Pokemon-themed videos and quizzes. Can you guess them all?</p><a href="https://www.youtube.com/@anime1point/playlists" target="_blank">Watch &rarr;</a></div></div>',
        '</div>',
        # ââ ABOUT ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
        '<div class="about" id="about">',
        '<h2>About Anime1Point</h2>',
        '<p>Welcome to <strong>Anime1Point</strong> &mdash; also known as <strong>Anime One Point</strong>, <strong>AnimeOnePoint</strong>, and <strong>Anime Point</strong> &mdash; your ultimate destination for anime breakdowns on YouTube. We specialize in <strong>That Time I Got Reincarnated as a Slime (Tensura) Season 4</strong> episode reviews, manga analysis, anime lore deep dives, and story breakdowns covering Rimuru Tempest, Diablo, Milim Nava, Veldora, and the Primordial Demons.</p>',
        '<a href="https://www.youtube.com/@anime1point?sub_confirmation=1" class="cta-btn" target="_blank" rel="noopener">&#9654; Subscribe on YouTube</a>',
        '</div>',
        # ââ SUBSCRIBE BANNER âââââââââââââââââââââââââââââââââââââââââââââ
        '<div class="sub-banner">',
        '<h2>&#9654; Join the Anime1Point Community</h2>',
        '<p>New episodes every week &bull; Tensura Season 4 &bull; Anime Breakdowns &bull; Manga Analysis</p>',
        '<a href="https://www.youtube.com/@anime1point?sub_confirmation=1" class="cta-btn" target="_blank" rel="noopener">Subscribe for Free</a>',
        '</div>',
        # ââ TAGS âââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
        '<h2 class="section-title">&#127991; Topics We Cover</h2>',
        '<div class="tags">',
        '<span class="tag">Anime1Point</span><span class="tag">Anime One Point</span><span class="tag">AnimeOnePoint</span><span class="tag">Anime Point</span><span class="tag">That Time I Got Reincarnated as a Slime</span><span class="tag">Tensura Season 4</span><span class="tag">Rimuru Tempest</span><span class="tag">Diablo Tensura</span><span class="tag">Milim Nava</span><span class="tag">Veldora</span><span class="tag">Anime Breakdown</span><span class="tag">Anime Explained</span><span class="tag">Manga Analysis</span><span class="tag">Anime Lore</span><span class="tag">Isekai Anime</span><span class="tag">Pokemon Quiz</span>',
        '</div>',
        '</div>',  # /container
        # ââ MODAL ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
        '<div class="modal-overlay" id="videoModal" onclick="closeModalOutside(event)"><div class="modal-box"><button class="modal-close" onclick="closeModal()">&times;</button><div class="modal-title" id="modalTitle"></div><iframe id="modalIframe" src="" allowfullscreen allow="autoplay; encrypted-media"></iframe></div></div>',
        # ââ FOOTER âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
        '<footer>',
        '<p>&copy; 2026 <strong>Anime1Point</strong> (Anime One Point) &mdash; All Rights Reserved</p>',
        '<p style="margin-top:10px"><a href="https://www.youtube.com/@anime1point">YouTube</a> &bull; <a href="https://www.youtube.com/@anime1point/videos">Videos</a> &bull; <a href="https://www.youtube.com/@anime1point/shorts">Shorts</a> &bull; <a href="https://www.youtube.com/@anime1point/community">Community</a> &bull; <a href="https://www.youtube.com/@anime1point/playlists">Playlists</a></p>',
        '<p style="margin-top:10px;font-size:0.82em">Anime1Point &bull; Anime One Point &bull; AnimeOnePoint &bull; Anime Point &bull; Tensura Season 4 &bull; That Time I Got Reincarnated as a Slime</p>',
        '</footer>',
        '<script src="carousel.js"><' + '/script>',
        '</body></html>'
    ]
    return '\n'.join(lines)

if __name__ == '__main__':
    print('Fetching carousel...')
    carousel_vids = get_carousel(7)
    print(f'  {len(carousel_vids)} slides')
    print('Fetching most watched...')
    most_watched = get_most_watched(8)
    print(f'  Top: {most_watched[0]["title"][:40] if most_watched else "none"} ({most_watched[0]["views"] if most_watched else 0})')
    print('Fetching latest videos...')
    latest_vids = get_latest_videos(8)
    print(f'  Latest: {latest_vids[0]["title"][:40] if latest_vids else "none"} ({latest_vids[0]["published"] if latest_vids else ""})')
    print('Fetching latest shorts...')
    latest_shorts = get_latest_shorts(6)
    print(f'  {len(latest_shorts)} shorts')
    print('Fetching community posts...')
    posts = get_community_posts(4)
    print(f'  {len(posts)} posts')
    html = build_html(carousel_vids, most_watched, latest_vids, latest_shorts, posts)
    with open('index.html','w',encoding='utf-8') as f:
        f.write(html)
    print('Done! Sections: Most Watched | Latest Uploads | Shorts | Community | Playlists')h
