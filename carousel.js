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
    /* preview iframe — non-interactive by default, taps go to card */
    '.thumb-wrap .hover-preview-iframe{',
    '  position:absolute;top:0;left:0;width:100%;height:100%;',
    '  border:none;z-index:3;opacity:0;pointer-events:none;',
    '  transition:opacity 0.3s ease;}',
    '.thumb-wrap .hover-preview-iframe.visible{opacity:1;}',
    /* when card is tapped on mobile, iframe becomes interactive for fullscreen */
    '.video-card.mob-active .hover-preview-iframe{pointer-events:auto;}',
    '.video-card:hover .thumb-wrap .play-btn,',
    '.video-card.mob-playing .thumb-wrap .play-btn{opacity:0;transition:opacity 0.2s;}',
    /* unmute pill */
    '.unmute-btn{',
    '  position:absolute;bottom:10px;left:50%;transform:translateX(-50%);',
    '  z-index:6;background:rgba(0,0,0,0.75);color:#fff;',
    '  font-size:12px;font-weight:700;padding:5px 14px;',
    '  border-radius:20px;border:none;cursor:pointer;',
    '  white-space:nowrap;pointer-events:auto;',
    '  display:flex;align-items:center;gap:6px;}',
    '.unmute-btn.hidden{display:none;}'
  ].join('');
  document.head.appendChild(style);

  var isMobile = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
  var audioUnlocked = false;
  var activeCard    = null;
  var scrollTimer   = null;
  var hoverTimer    = null;

  function getVideoId(card) {
    var m = (card.getAttribute('onclick') || '').match(/openModal\s*\(\s*'([^']+)'/);
    return m ? m[1] : null;
  }

  function buildSrc(videoId, muted, controls) {
    return 'https://www.youtube.com/embed/' + videoId
      + '?autoplay=1&mute=' + (muted ? '1' : '0')
      + '&controls=' + (controls ? '1' : '0')
      + '&loop=1&playlist=' + videoId
      + '&modestbranding=1&rel=0&showinfo=0&playsinline=1';
  }
  /* Start muted preview on a card */
  function startPreview(card, muted) {
    var videoId = getVideoId(card);
    if (!videoId) return;
    var tw = card.querySelector('.thumb-wrap');
    if (!tw || tw.querySelector('.hover-preview-iframe')) return;
    var iframe = document.createElement('iframe');
    iframe.className = 'hover-preview-iframe';
    iframe.allow = 'autoplay; encrypted-media';
    iframe.setAttribute('allowfullscreen', '');
    iframe.setAttribute('playsinline', '');
    /* mobile preview: muted, controls visible so fullscreen btn is accessible */
    /* desktop preview: unmuted, no controls for clean look */
    iframe.src = buildSrc(videoId, muted, isMobile);
    tw.appendChild(iframe);
    if (isMobile && !audioUnlocked) {
      var btn = document.createElement('button');
      btn.className = 'unmute-btn';
      btn.innerHTML = '&#128263; Tap for audio';
      btn.addEventListener('touchend', function(e) {
        e.preventDefault();
        e.stopPropagation();
        unmuteActive();
      });
      tw.appendChild(btn);
    }
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
    var btn = tw.querySelector('.unmute-btn');
    if (btn && btn.parentNode) btn.parentNode.removeChild(btn);
    card.classList.remove('mob-playing');
    card.classList.remove('mob-active');
  }

  /* Unmute the currently active card's iframe */
  function unmuteActive() {
    audioUnlocked = true;
    if (!activeCard) return;
    var videoId = getVideoId(activeCard);
    var ifrm = activeCard.querySelector('.hover-preview-iframe');
    if (ifrm && videoId) ifrm.src = buildSrc(videoId, false, true);
    var btn = activeCard.querySelector('.unmute-btn');
    if (btn) btn.classList.add('hidden');
  }

  /*
   * activateCard — called when user taps a card on mobile.
   * - Suppresses the openModal popup.
   * - Makes the inline iframe interactive (pointer-events on) so
   *   the YouTube fullscreen button inside it is tappable.
   * - Unmutes audio (first tap unlocks audio policy).
   */
  function activateCard(card, e) {
    /* Only intercept if this card already has a preview playing */
    var tw = card.querySelector('.thumb-wrap');
    if (!tw || !tw.querySelector('.hover-preview-iframe')) return;
    /* Prevent the openModal popup from opening */
    e.preventDefault();
    e.stopPropagation();
    /* Make iframe interactive so YouTube controls (incl. fullscreen) work */
    card.classList.add('mob-active');
    /* Unmute on first tap */
    if (!audioUnlocked) unmuteActive();
  }
  /* --- Desktop: hover --- */
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
  }

  /* --- Mobile: scroll picks most-visible card to preview --- */
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
    if (activeCard) startPreview(activeCard, !audioUnlocked);
  }

  /* --- Mobile tap: intercept onclick, activate inline player --- */
  function attachMobileTap(card) {
    if (card.dataset.mobileTapAttached) return;
    card.dataset.mobileTapAttached = '1';
    /* Use click (fires after touchend) to intercept the onclick='openModal(...)' */
    card.addEventListener('click', function(e) {
      activateCard(card, e);
    });
  }

  function attach(card) {
    if (isMobile) {
      attachMobileTap(card);
    } else {
      attachHover(card);
    }
  }

  if (isMobile) {
    window.addEventListener('scroll', function() {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(pickAndPlay, 150);
    }, { passive: true });
    /* Run once on load in case a card is already in view */
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
