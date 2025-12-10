'use strict';

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
      const authorUrl = t.author.id ? `/users/view/${t.author.id}` : '#';
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

async function fetchByKims(kims) {
  const resp = await fetch('/tasks/api/by_numbers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
    body: JSON.stringify({ numbers: kims })
  });
  if (!resp.ok) throw new Error('Ошибка сети: ' + resp.status);
  return resp.json();
}

async function fetchByIds(ids) {
  const resp = await fetch('/tasks/api/by_ids', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
    body: JSON.stringify({ ids: ids })
  });
  if (!resp.ok) throw new Error('Ошибка сети: ' + resp.status);
  return resp.json();
}

document.addEventListener('DOMContentLoaded', () => {
  const kimSelect = document.getElementById('kim-select');
  const btnLoad = document.getElementById('btn-load-by-kim');
  const btnClear = document.getElementById('btn-clear-results');
  const results = document.getElementById('results');
  const getTaskBtn = document.getElementById('btn-get-task');
  const taskIdInput = document.getElementById('task_id_input');

  btnLoad.addEventListener('click', async (e) => {
    e.preventDefault();
    const selected = Array.from(kimSelect.selectedOptions).map(o => parseInt(o.value, 10)).filter(Boolean);
    if (!selected.length) {
      alert('Выберите хотя бы один номер КИМ.');
      return;
    }
    results.innerHTML = 'Загрузка...';
    try {
      const data = await fetchByKims(selected);
      renderTasksList(results, data.tasks);
    } catch (err) {
      results.innerHTML = '';
      results.appendChild(el('div', { class: 'alert alert-danger' }, String(err)));
    }
  });

  btnClear.addEventListener('click', (e) => {
    e.preventDefault();
    kimSelect.selectedIndex = -1;
    results.innerHTML = '<div class="text-muted">Результаты поиска появятся здесь</div>';
  });

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
      renderTasksList(results, data.tasks);
    } catch (err) {
      results.innerHTML = '';
      results.appendChild(el('div', { class: 'alert alert-danger' }, String(err)));
    }
  });
});
