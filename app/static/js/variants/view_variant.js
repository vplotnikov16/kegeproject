document.addEventListener('DOMContentLoaded', function () {
  const toggles = Array.from(document.querySelectorAll('.answer-toggle'));
  toggles.forEach(btn => {
    const targetSelector = btn.getAttribute('data-bs-target');
    if (!targetSelector) return;
    const target = document.querySelector(targetSelector);
    if (!target) return;

    target.addEventListener('show.bs.collapse', () => {
      const icon = btn.querySelector('.chev-icon');
      if (icon) icon.textContent = '▴';
      btn.classList.add('active');
      btn.querySelectorAll('span:not(.chev-icon)').forEach(s => s.textContent = 'Скрыть');
    });
    target.addEventListener('hide.bs.collapse', () => {
      const icon = btn.querySelector('.chev-icon');
      if (icon) icon.textContent = '▾';
      btn.classList.remove('active');
      btn.querySelectorAll('span:not(.chev-icon)').forEach(s => s.textContent = 'Показать');
    });

    if (typeof bootstrap === 'undefined') {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        if (target.classList.contains('show')) {
          target.classList.remove('show');
          const icon = btn.querySelector('.chev-icon');
          if (icon) icon.textContent = '▾';
          btn.textContent = ' Показать';
        } else {
          target.classList.add('show');
          const icon = btn.querySelector('.chev-icon');
          if (icon) icon.textContent = '▴';
          btn.textContent = ' Скрыть';
        }
      });
    }
  });
});
