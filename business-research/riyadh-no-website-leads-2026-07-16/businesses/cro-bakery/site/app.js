const menuBtn = document.querySelector('.menu-btn');
const nav = document.querySelector('nav');

menuBtn?.addEventListener('click', () => {
  const open = nav?.classList.toggle('open') ?? false;
  menuBtn.setAttribute('aria-expanded', String(open));
  menuBtn.textContent = open ? '✕' : '☰';
});

nav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
  nav.classList.remove('open');
  menuBtn?.setAttribute('aria-expanded', 'false');
  if (menuBtn) menuBtn.textContent = '☰';
}));

document.querySelectorAll('.filter').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('.filter').forEach((filter) => filter.classList.remove('active'));
  button.classList.add('active');
  const filter = button.dataset.filter;
  document.querySelectorAll('.menu-item').forEach((item) => {
    item.classList.toggle('hidden', filter !== 'all' && item.dataset.category !== filter);
  });
}));

const revealItems = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    entry.target.classList.add('visible');
    observer.unobserve(entry.target);
  }), { threshold: 0.12 });
  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add('visible'));
}

document.getElementById('year')?.append(new Date().getFullYear());

// طبقات CSS ثلاثية الأبعاد: تفاعل خفيف للمؤشر على أجهزة المؤشر الدقيقة فقط.
const tiltScene = document.querySelector('[data-tilt]');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const finePointer = window.matchMedia('(pointer: fine)');

if (tiltScene && !reducedMotion.matches && finePointer.matches) {
  const stage = tiltScene.querySelector('.hero-stage');
  let animationFrame;
  let pointerPosition;

  const reset = () => {
    pointerPosition = null;
    stage?.style.setProperty('--tilt-x', '0deg');
    stage?.style.setProperty('--tilt-y', '0deg');
    tiltScene.querySelectorAll('[data-depth]').forEach((card) => {
      card.style.setProperty('--move-x', '0px');
      card.style.setProperty('--move-y', '0px');
    });
  };

  const updateTilt = () => {
    animationFrame = undefined;
    if (!pointerPosition || !stage) return;
    const { x, y } = pointerPosition;
    stage.style.setProperty('--tilt-x', `${-y * 7}deg`);
    stage.style.setProperty('--tilt-y', `${x * 9}deg`);
    tiltScene.querySelectorAll('[data-depth]').forEach((card) => {
      const depth = Number(card.dataset.depth);
      card.style.setProperty('--move-x', `${x * depth * 0.12}px`);
      card.style.setProperty('--move-y', `${y * depth * 0.12}px`);
    });
  };

  tiltScene.addEventListener('pointermove', (event) => {
    const rect = tiltScene.getBoundingClientRect();
    pointerPosition = {
      x: (event.clientX - rect.left) / rect.width - 0.5,
      y: (event.clientY - rect.top) / rect.height - 0.5,
    };
    if (!animationFrame) animationFrame = requestAnimationFrame(updateTilt);
  });
  tiltScene.addEventListener('pointerleave', reset);
  reset();
}
