(() => {
  const track = document.getElementById('pa-home-cars-track');
  if (!track) return;
  const root = track.closest('#pa-home-cars');
  const prev = root.querySelector('.pa-home-cars-prev');
  const next = root.querySelector('.pa-home-cars-next');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const sync = () => {
    const max = Math.max(0, track.scrollWidth - track.clientWidth);
    prev.disabled = track.scrollLeft <= 2;
    next.disabled = track.scrollLeft >= max - 2;
    prev.hidden = next.hidden = max <= 2;
  };
  const move = direction => track.scrollBy({left: direction * Math.max(150, track.clientWidth - 160), behavior: reduced.matches ? 'instant' : 'smooth'});
  prev.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  track.addEventListener('scroll', sync, {passive:true});
  window.addEventListener('resize', sync, {passive:true});
  if ('ResizeObserver' in window) new ResizeObserver(sync).observe(track);
  sync();
})();
