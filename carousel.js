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

/* ── Video preview: hover (desktop) + scroll-into-view (mobile) ── */
(function () {

   /* ── Shared CSS ── */
   var style = document.createElement('style');
    style.textContent = [
          '.thumb-wrap .hover-preview-iframe{',
          '  position:absolute;top:0;left:0;width:100%;height:100%;',
          '  border:none;z-index:3;opacity:0;',
          '  transition:opacity 0.3s ease;pointer-events:none;}',
          '.thumb-wrap .hover-preview-iframe.visible{opacity:1;pointer-events:auto;}',
          '.video-card:hover .thumb-wrap .play-btn{opacity:0;transition:opacity 0.2s;}'
        ].join('');
    document.head.appendChild(style);

   /* ── Helpers ── */
   var isMobile = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

   function getVideoId(card) {
         var m = (card.getAttribute('onclick') || '').match(/openModal\s*\(\s*'([^']+)'/);
         return m ? m[1] : null;
   }

   function buildSrc(videoId, muted) {
         return 'https://www.youtube.com/embed/' + videoId
           + '?autoplay=1&mute=' + (muted ? '1' : '0')
           + '&controls=0&loop=1&playlist=' + videoId
           + '&modestbranding=1&rel=0&showinfo=0&playsinline=1';
   }

   function startPreview(card, muted) {
         var videoId = getVideoId(card);
         if (!videoId) return;
         var thumbWrap = card.querySelector('.thumb-wrap');
         if (!thumbWrap) return;
         var existing = thumbWrap.querySelector('.hover-preview-iframe');
         if (existing) return;
         var iframe = document.createElement('iframe');
         iframe.className = 'hover-preview-iframe';
         iframe.allow = 'autoplay; encrypted-media';
         iframe.setAttribute('allowfullscreen', '');
         iframe.setAttribute('playsinline', '');
         iframe.setAttribute('title', 'Preview');
         iframe.src = buildSrc(videoId, muted);
         thumbWrap.appendChild(iframe);
         requestAnimationFrame(function () {
                 requestAnimationFrame(function () { iframe.classList.add('visible'); });
         });
   }

   function stopPreview(card) {
         var thumbWrap = card.querySelector('.thumb-wrap');
         if (!thumbWrap) return;
         var iframe = thumbWrap.querySelector('.hover-preview-iframe');
         if (iframe) {
                 iframe.classList.remove('visible');
                 setTimeout(function () {
                           if (iframe.parentNode) iframe.parentNode.removeChild(iframe);
                 }, 350);
         }
   }

   /* ── Desktop: hover ── */
   var hoverTimer = null;

   function attachHoverListeners(card) {
         if (card.dataset.hoverAttached) return;
         card.dataset.hoverAttached = 'true';
         card.addEventListener('mouseenter', function () {
                 clearTimeout(hoverTimer);
                 hoverTimer = setTimeout(function () { startPreview(card, false); }, 300);
         });
         card.addEventListener('mouseleave', function () {
                 clearTimeout(hoverTimer);
                 stopPreview(card);
         });
   }

   /* ── Mobile: IntersectionObserver — play when >=60% visible ── */
   var mobileObserver = null;

   function setupMobileObserver() {
         if (!('IntersectionObserver' in window)) return;
         mobileObserver = new IntersectionObserver(function (entries) {
                 entries.forEach(function (entry) {
                           var card = entry.target;
                           if (entry.intersectionRatio >= 0.6) {
                                       startPreview(card, true);
                           } else {
                                       stopPreview(card);
                           }
                 });
         }, { threshold: [0, 0.6] });
   }

   function attachMobileObserver(card) {
         if (card.dataset.mobileObserved) return;
         card.dataset.mobileObserved = 'true';
         if (mobileObserver) mobileObserver.observe(card);
   }

   /* ── Init ── */
   if (isMobile) {
         setupMobileObserver();
   }

   function attachListeners(card) {
         if (isMobile) {
                 attachMobileObserver(card);
         } else {
                 attachHoverListeners(card);
         }
   }

   document.querySelectorAll('.video-card').forEach(attachListeners);

   /* ── Watch for dynamically added cards ── */
   new MutationObserver(function (mutations) {
         mutations.forEach(function (m) {
                 m.addedNodes.forEach(function (node) {
                           if (node.nodeType !== 1) return;
                           if (node.classList && node.classList.contains('video-card')) attachListeners(node);
                           if (node.querySelectorAll) node.querySelectorAll('.video-card').forEach(attachListeners);
                 });
         });
   }).observe(document.body, { childList: true, subtree: true });

})();
