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