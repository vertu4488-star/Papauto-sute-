/* Show photos only after they are self-hosted on PapAuto.
   Each group is keyed to an exact Autowini item; never substitute stock photos.
   No off-site links or image requests from the public page. */
(() => {
  const groups = {
    'IC5605199': 'bmw-x1-kr-ic5605199',
    'IC5604396': 'bmw-x3-kr-ic5604396',
    'IC5486298': 'audi-q3sb-kr-ic5486298'
  };
  const root = '/assets/premium-auctions/';
  Object.entries(groups).forEach(async ([id, basename]) => {
    const card = document.querySelector('.real-card[data-korea-id="' + id + '"]');
    if (!card) return;
    const photos = [1,2,3].map(i => root + basename + '-photo-' + i + '.webp');
    try {
      const check = await fetch(photos[0], {method:'HEAD', cache:'no-store'});
      if (!check.ok || !/^image\//.test(check.headers.get('content-type')||'')) return;
      const holder = card.querySelector('.real-unavailable');
      if (!holder) return;
      const group = document.createElement('div');
      group.className = 'real-imggroup';
      for (let i=0;i<3;i++) {
        const anchor = document.createElement('a');
        anchor.className = ['real-img-main','real-img-mini','real-img-sheet'][i];
        anchor.href = photos[i];
        anchor.target='_blank';anchor.rel='noopener';
        const photo=document.createElement('img');
        photo.src=photos[i];
        photo.loading='lazy';
        photo.decoding='async';
        photo.alt='Оригинальное фото ' + (i+1) + ' автомобиля из объявления №' + id;
        photo.onerror=()=>{anchor.remove();};
        anchor.append(photo);
        if (i===2) {
          const caption=document.createElement('span');
          caption.textContent='Фото 3, не аукционный лист';
          anchor.append(caption);
        }
        group.append(anchor);
      }
      holder.replaceWith(group);
      const note = card.querySelector('.real-note');
      if(note) note.textContent += ' Оригинальные фотографии объявления сохранены локально; отчёт осмотра не получен.';
    } catch (error) {
      /* Photo import not available yet; show honest no-photo state. */
    }
  });
})();