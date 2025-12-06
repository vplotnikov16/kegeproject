'use strict';

document.addEventListener('DOMContentLoaded', () => {
  // Устанавливаем обработку "Показать полностью" для каждого блока
  document.querySelectorAll('.btn-expand-snippet').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const card = btn.closest('.task-card');
      const snippet = card.querySelector('.task-statement-snippet');
      const expanded = snippet.classList.toggle('expanded');
      btn.textContent = expanded ? 'Свернуть' : 'Показать полностью';
      if (expanded) card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });

  // Обработчик кнопок "Ответ" — используем bootstrap collapse via data-bs-target attr
  document.querySelectorAll('.btn-toggle-answer').forEach(btn => {
    btn.addEventListener('click', (e) => {
      // bootstrap collapse via attribute works automatically; можно доп. логика если нужно
      // здесь просто предотвратим лишний переход если ссылка есть
      e.preventDefault();
      const target = btn.getAttribute('data-bs-target');
      if (!target) return;
      const el = document.querySelector(target);
      if (!el) return;
      // toggling via class (Bootstrap will manage classes if bundle loaded)
      el.classList.toggle('show');
    });
  });

  // Подтверждение удаления (fallback, если нет JS — форма всё равно отправится)
  document.querySelectorAll('.delete-task-form').forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!confirm('Удалить задачу? Это действие необратимо.')) {
        e.preventDefault();
      }
    });
  });
});
