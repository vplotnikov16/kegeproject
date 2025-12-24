'use strict';

// Глобальное состояние
let allTasks = [];
let currentPage = 1;
const tasksPerPage = 15;

function el(tag, props = {}, ...children) {
  const e = document.createElement(tag);
  Object.entries(props).forEach(([k, v]) => {
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;
    else e.setAttribute(k, v);
  });
  children.flat().forEach(ch => {
    if (typeof ch === 'string') e.appendChild(document.createTextNode(ch));
    else if (ch instanceof Node) e.appendChild(ch);
  });
  return e;
}

function renderTasksList(container, tasks) {
  container.innerHTML = '';
  if (!tasks || tasks.length === 0) {
    container.appendChild(el('div', { class: 'text-muted' }, 'Ничего не найдено'));
    return;
  }

  const list = el('div', { class: 'list-group' });

  tasks.forEach(t => {
    const answerId = `answerCollapse-${t.id}`;
    const item = el('div', { class: 'list-group-item' });

    const leftTitle = el('div', { class: 'fw-bold' }, `#${t.id} — КИМ №${t.number}`);
    const rightMeta = el('div', { class: 'text-muted small' }, t.published_at || '');
    const header = el('div', { class: 'd-flex justify-content-between' }, leftTitle, rightMeta);

    let authorEl = null;
    if (t.author && (t.author.first_name || t.author.last_name)) {
      const authorName = `${t.author.first_name || ''} ${t.author.last_name || ''}`.trim();
      const authorUrl = t.author.id ? `/users/view_user/${t.author.id}` : '#';
      const authorLink = el('a', { href: authorUrl }, authorName || '—');
      authorEl = el('div', { class: 'small text-muted mt-1' },
        el('strong', {}, 'Автор: '),
        authorLink
      );
    }

    let sourceEl = null;
    if (t.source) {
      sourceEl = el('div', { class: 'task-source mt-1' }, `Источник: ${t.source}`);
    }

    const statement = el('div', { class: 'mt-2 task-statement-snippet' });
    statement.innerHTML = t.statement_html_snippet || t.statement_html || '';
    const toggleFullBtn = el('button', { type: 'button', class: 'btn btn-sm btn-link p-0 mt-2' }, 'Показать полностью');
    toggleFullBtn.addEventListener('click', () => {
      const expanded = statement.classList.toggle('expanded');
      toggleFullBtn.textContent = expanded ? 'Свернуть' : 'Показать полностью';
      if (expanded) item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });

    // Блок ответ (Bootstrap collapse)
    const answerToggle = el('a', {
      class: 'btn btn-sm btn-outline-secondary ms-2',
      href: `#${answerId}`,
      'data-bs-toggle': 'collapse',
      role: 'button',
      'aria-expanded': 'false',
      'aria-controls': answerId
    }, 'Ответ');

    const actions = el('div', { class: 'mt-2' },
      el('a', { class: 'btn btn-sm btn-outline-primary', href: t.view_url }, 'Открыть'),
      answerToggle
    );

    const answerCollapse = el('div', { class: 'collapse mt-2', id: answerId },
      el('div', { class: 'card card-body' },
        el('strong', {}, 'Ответ: '),
        el('div', { class: 'mt-1' }, t.answer || '—')
      )
    );

    item.appendChild(header);
    if (authorEl) item.appendChild(authorEl);
    if (sourceEl) item.appendChild(sourceEl);
    item.appendChild(statement);
    item.appendChild(toggleFullBtn);
    item.appendChild(actions);
    item.appendChild(answerCollapse);

    list.appendChild(item);
  });

  container.appendChild(list);
}

function renderPagination(totalTasks) {
  const paginationContainer = document.getElementById('pagination');
  paginationContainer.innerHTML = '';

  const totalPages = Math.ceil(totalTasks / tasksPerPage);

  if (totalPages <= 1) return; // Не показываем пагинацию, если только одна страница

  // Кнопка "Назад"
  const prevLi = el('li', { class: `page-item ${currentPage === 1 ? 'disabled' : ''}` });
  const prevLink = el('a', { class: 'page-link', href: '#' }, '«');
  prevLink.addEventListener('click', (e) => {
    e.preventDefault();
    if (currentPage > 1) {
      currentPage--;
      displayPage(currentPage);
    }
  });
  prevLi.appendChild(prevLink);
  paginationContainer.appendChild(prevLi);

  // Генерация номеров страниц с умной логикой
  const pagesToShow = getPageNumbers(currentPage, totalPages);

  pagesToShow.forEach(pageNum => {
    if (pageNum === '...') {
      // Многоточие (неактивная кнопка)
      const li = el('li', { class: 'page-item disabled' });
      const span = el('span', { class: 'page-link' }, '...');
      li.appendChild(span);
      paginationContainer.appendChild(li);
    } else {
      // Обычная кнопка страницы
      const li = el('li', { class: `page-item ${pageNum === currentPage ? 'active' : ''}` });
      const link = el('a', { class: 'page-link', href: '#' }, String(pageNum));
      link.addEventListener('click', (e) => {
        e.preventDefault();
        currentPage = pageNum;
        displayPage(currentPage);
      });
      li.appendChild(link);
      paginationContainer.appendChild(li);
    }
  });

  // Кнопка "Вперёд"
  const nextLi = el('li', { class: `page-item ${currentPage === totalPages ? 'disabled' : ''}` });
  const nextLink = el('a', { class: 'page-link', href: '#' }, '»');
  nextLink.addEventListener('click', (e) => {
    e.preventDefault();
    if (currentPage < totalPages) {
      currentPage++;
      displayPage(currentPage);
    }
  });
  nextLi.appendChild(nextLink);
  paginationContainer.appendChild(nextLi);
}

function getPageNumbers(current, total) {
  const delta = 2; // Количество страниц с каждой стороны от текущей
  const range = [];
  const rangeWithDots = [];

  // Если страниц мало, показываем все
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      range.push(i);
    }
    return range;
  }

  // Генерируем диапазон страниц для показа
  for (let i = 1; i <= total; i++) {
    if (
      i === 1 ||                          // Первая страница
      i === total ||                      // Последняя страница
      (i >= current - delta && i <= current + delta) // Текущая +/- delta
    ) {
      range.push(i);
    }
  }

  // Добавляем многоточия между разрывами
  let prev = 0;
  for (const i of range) {
    if (i - prev === 2) {
      // Если между двумя номерами только одна страница, показываем её
      rangeWithDots.push(prev + 1);
    } else if (i - prev > 1) {
      // Если разрыв больше, добавляем многоточие
      rangeWithDots.push('...');
    }
    rangeWithDots.push(i);
    prev = i;
  }

  return rangeWithDots;
}

function displayPage(page) {
  const start = (page - 1) * tasksPerPage;
  const end = start + tasksPerPage;
  const tasksToShow = allTasks.slice(start, end);

  const results = document.getElementById('results');
  renderTasksList(results, tasksToShow);
  renderPagination(allTasks.length);

  // Обновить счётчик
  const counter = document.getElementById('results-counter');
  counter.textContent = `Показано ${start + 1}-${Math.min(end, allTasks.length)} из ${allTasks.length}`;

  // Прокрутить к началу результатов
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function fetchByKims(kims) {
  const resp = await fetch('/api/tasks/by_numbers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
    body: JSON.stringify({ numbers: kims })
  });
  if (!resp.ok) throw new Error('Ошибка сети: ' + resp.status);
  return resp.json();
}

async function fetchByIds(ids) {
  const resp = await fetch('/api/tasks/by_ids', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
    body: JSON.stringify({ ids: ids })
  });
  if (!resp.ok) throw new Error('Ошибка сети: ' + resp.status);
  return resp.json();
}

document.addEventListener('DOMContentLoaded', () => {
  const kimCheckboxes = document.querySelectorAll('.kim-checkbox');
  const btnLoad = document.getElementById('btn-load-by-kim');
  const btnClear = document.getElementById('btn-clear-results');
  const results = document.getElementById('results');
  const getTaskBtn = document.getElementById('btn-get-task');
  const taskIdInput = document.getElementById('task_id_input');
  const selectAllBtn = document.getElementById('select-all-btn');

  // Функции для кнопки "Выбрать все"
  function getSelectAllState() {
    const total = kimCheckboxes.length;
    const checked = Array.from(kimCheckboxes).filter(cb => cb.checked).length;

    if (checked === 0) return 'unchecked';
    if (checked === total) return 'checked';
    return 'partial';
  }

  function updateSelectAllUI() {
    if (!selectAllBtn) return;

    const state = getSelectAllState();
    selectAllBtn.classList.remove('btn-outline-secondary', 'btn-secondary', 'btn-success');

    if (state === 'unchecked') {
      selectAllBtn.textContent = 'Выбрать все';
      selectAllBtn.classList.add('btn-outline-secondary');
    } else if (state === 'partial') {
      selectAllBtn.textContent = 'Выбрано частично';
      selectAllBtn.classList.add('btn-secondary');
    } else {
      selectAllBtn.textContent = 'Снять выбор';
      selectAllBtn.classList.add('btn-success');
    }
  }

  function setAllCheckboxes(checked) {
    kimCheckboxes.forEach(cb => {
      cb.checked = checked;
    });
    updateSelectAllUI();
  }

  // Обработчик кнопки "Выбрать все"
  if (selectAllBtn) {
    selectAllBtn.addEventListener('click', () => {
      const state = getSelectAllState();
      setAllCheckboxes(state !== 'checked');
    });
  }

  // Обновление UI при изменении чекбоксов
  kimCheckboxes.forEach(cb => {
    cb.addEventListener('change', updateSelectAllUI);
  });

  // Инициализация UI
  updateSelectAllUI();

  // Загрузка задач по выбранным КИМ
  btnLoad.addEventListener('click', async (e) => {
    e.preventDefault();

    const selected = Array.from(kimCheckboxes)
      .filter(cb => cb.checked)
      .map(cb => parseInt(cb.value, 10))
      .filter(Boolean);

    if (!selected.length) {
      alert('Выберите хотя бы один номер КИМ.');
      return;
    }

    results.innerHTML = 'Загрузка...';
    try {
      const data = await fetchByKims(selected);
      allTasks = data.tasks || [];
      currentPage = 1;
      displayPage(currentPage);
    } catch (err) {
      results.innerHTML = '';
      results.appendChild(el('div', { class: 'alert alert-danger' }, String(err)));
    }
  });

  // Очистка результатов
  btnClear.addEventListener('click', (e) => {
    e.preventDefault();
    kimCheckboxes.forEach(cb => cb.checked = false);
    updateSelectAllUI();
    allTasks = [];
    currentPage = 1;
    results.innerHTML = '<div class="text-muted">Результаты поиска появятся здесь</div>';
    document.getElementById('pagination').innerHTML = '';
    document.getElementById('results-counter').textContent = '';
  });

  // Поиск по ID
  getTaskBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    const raw = (taskIdInput.value || '').trim();
    if (!raw) {
      alert('Введите id задачи (или несколько через запятую).');
      return;
    }
    const ids = raw.split(',').map(s => parseInt(s.trim(), 10)).filter(Boolean);
    if (!ids.length) {
      alert('Неверный формат id.');
      return;
    }
    if (ids.length === 1) {
      window.location.href = `/tasks/view_task/${ids[0]}`;
      return;
    }
    results.innerHTML = 'Загрузка...';
    try {
      const data = await fetchByIds(ids);
      allTasks = data.tasks || [];
      currentPage = 1;
      displayPage(currentPage);
    } catch (err) {
      results.innerHTML = '';
      results.appendChild(el('div', { class: 'alert alert-danger' }, String(err)));
    }
  });
});
