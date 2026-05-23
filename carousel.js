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
/* == Video preview: hover (desktop) + scroll-into-view (mobile) == */
(function () {

  var style = document.createElement('style');
  style.textContent = [
    /* iframe default: visible and fully interactive once playing */
    '.thumb-wrap .hover-preview-iframe{',
    '  position:absolute;top:0;left:0;width:100%;height:100%;',
    '  border:none;z-index:3;opacity:0;',
    '  transition:opacity 0.3s ease;}',
    '.thumb-wrap .hover-preview-iframe.visible{',
    '  opacity:1;pointer-events:auto;}',
    /* desktop only: hide play button on hover */
    '.video-card:hover .thumb-wrap .play-btn,',
    '.video-card.mob-playing .thumb-wrap .play-btn{opacity:0;transition:opacity 0.2s;}',
    /* no blue tap ring */
    '.video-card{outline:none;-webkit-tap-highlight-color:transparent;cursor:pointer;}'
  ].join('');
  document.head.appendChild(style);

  var isMobile = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
  var activeCard  = null;
  var scrollTimer = null;
  var hoverTimer  = null;

  /* ── helpers ── */

  /*
   * getVideoId: reads from data-vid (set by stripOnclick).
   * Fallback parses onclick for safety.
   */
  function getVideoId(card) {
    if (card.dataset.vid) return card.dataset.vid;
    var raw = card.getAttribute('onclick') || '';
    var m = raw.match(/openModal\s*\(\s*'([^']+)'/);
    return m ? m[1] : null;
  }

  /*
   * stripOnclick — called for EVERY card on ALL devices.
   * Permanently removes onclick so popup modal can never open.
   */
  function stripOnclick(card) {
    if (card.dataset.vid) return;
    var raw = card.getAttribute('onclick') || '';
    var m = raw.match(/openModal\s*\(\s*'([^']+)'/);
    if (m) card.dataset.vid = m[1];
    card.removeAttribute('onclick');
  }

  function buildSrc(videoId, muted) {
    /* Always controls=1 so YouTube's own mute/fullscreen buttons are available */
    return 'https://www.youtube.com/embed/' + videoId
      + '?autoplay=1&mute=' + (muted ? '1' : '0')
      + '&controls=1'
      + '&loop=1&playlist=' + videoId
      + '&modestbranding=1&rel=0&showinfo=0&playsinline=1';
  }

  function startPreview(card, muted) {
    var videoId = getVideoId(card);
    if (!videoId) return;
    var tw = card.querySelector('.thumb-wrap');
    if (!tw || tw.querySelector('.hover-preview-iframe')) return;
    var iframe = document.createElement('iframe');
    iframe.className = 'hover-preview-iframe';
    iframe.allow = 'autoplay; encrypted-media; fullscreen';
    iframe.setAttribute('allowfullscreen', '');
    iframe.setAttribute('playsinline', '');
    iframe.src = buildSrc(videoId, muted);
    tw.appendChild(iframe);
    card.classList.add('mob-playing');
    requestAnimationFrame(function() {
      requestAnimationFrame(function() { iframe.classList.add('visible'); });
    });
  }

  function stopPreview(card) {
    var tw = card.querySelector('.thumb-wrap');
    if (!tw) return;
    var iframe = tw.querySelector('.hover-preview-iframe');
    if (iframe) {
      iframe.classList.remove('visible');
      setTimeout(function() { if (iframe.parentNode) iframe.parentNode.removeChild(iframe); }, 300);
    }
    card.classList.remove('mob-playing');
  }

  /* ── Desktop: mouseenter/leave ── */
  function attachHover(card) {
    if (card.dataset.hoverAttached) return;
    card.dataset.hoverAttached = '1';
    card.addEventListener('mouseenter', function() {
      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(function() { startPreview(card, false); }, 300);
    });
    card.addEventListener('mouseleave', function() {
      clearTimeout(hoverTimer);
      stopPreview(card);
    });
    /* Desktop click while hovering: open modal (full watch experience) */
    card.addEventListener('click', function() {
      var vid = getVideoId(card);
      var title = card.querySelector('.video-title') ? card.querySelector('.video-title').textContent : '';
      if (vid) openModal(vid, title);
    });
  }

  /* ── Mobile helpers ── */
  function getVisibleRatio(card) {
    var r = card.getBoundingClientRect();
    var vph = window.innerHeight;
    var visH = Math.max(0, Math.min(vph, r.bottom) - Math.max(0, r.top));
    return r.height > 0 ? visH / r.height : 0;
  }

  function pickAndPlay() {
    var cards = document.querySelectorAll('.video-card');
    var bestCard = null, bestRatio = 0.5;
    cards.forEach(function(card) {
      var ratio = getVisibleRatio(card);
      if (ratio > bestRatio) { bestRatio = ratio; bestCard = card; }
    });
    if (bestCard === activeCard) return;
    if (activeCard) stopPreview(activeCard);
    activeCard = bestCard;
    if (activeCard) startPreview(activeCard, true);
  }

  function attach(card) {
    /* Always strip onclick on all devices to prevent popup */
    stripOnclick(card);
    if (isMobile) {
      /* nothing extra needed — iframe is interactive as soon as visible */
    } else {
      attachHover(card);
    }
  }

  if (isMobile) {
    window.addEventListener('scroll', function() {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(pickAndPlay, 150);
    }, { passive: true });
    setTimeout(pickAndPlay, 600);
  }

  document.querySelectorAll('.video-card').forEach(attach);

  new MutationObserver(function(mutations) {
    mutations.forEach(function(m) {
      m.addedNodes.forEach(function(node) {
        if (node.nodeType !== 1) return;
        if (node.classList && node.classList.contains('video-card')) attach(node);
        if (node.querySelectorAll) node.querySelectorAll('.video-card').forEach(attach);
      });
    });
  }).observe(document.body, { childList: true, subtree: true });

})();
