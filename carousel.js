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

/* ── Hover-to-preview ── */
(function () {
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

   var hoverTimer = null;

   function getVideoId(card) {
         var m = (card.getAttribute('onclick') || '').match(/openModal\s*\(\s*'([^']+)'/);
         return m ? m[1] : null;
   }

   function startPreview(card) {
         var videoId = getVideoId(card);
         if (!videoId) return;
         var thumbWrap = card.querySelector('.thumb-wrap');
         if (!thumbWrap || thumbWrap.querySelector('.hover-preview-iframe')) return;
         var iframe = document.createElement('iframe');
         iframe.className = 'hover-preview-iframe';
         iframe.allow = 'autoplay; encrypted-media';
         iframe.setAttribute('allowfullscreen', '');
         iframe.setAttribute('title', 'Preview');
         iframe.src = 'https://www.youtube.com/embed/' + videoId
           + '?autoplay=1&mute=0&controls=0&loop=1&playlist=' + videoId
           + '&modestbranding=1&rel=0&showinfo=0';
         thumbWrap.appendChild(iframe);
         requestAnimationFrame(function () {
                 requestAnimationFrame(function () { iframe.classList.add('visible'); });
         });
   }

   function stopPreview(card) {
         var iframe = card.querySelector('.hover-preview-iframe');
         if (iframe) {
                 iframe.classList.remove('visible');
                 setTimeout(function () {
                           if (iframe.parentNode) iframe.parentNode.removeChild(iframe);
                 }, 350);
         }
   }

   function attachListeners(card) {
         if (card.dataset.hoverPreviewAttached) return;
         card.dataset.hoverPreviewAttached = 'true';
         card.addEventListener('mouseenter', function () {
                 clearTimeout(hoverTimer);
                 hoverTimer = setTimeout(function () { startPreview(card); }, 300);
         });
         card.addEventListener('mouseleave', function () {
                 clearTimeout(hoverTimer);
                 stopPreview(card);
         });
   }

   document.querySelectorAll('.video-card').forEach(attachListeners);

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
