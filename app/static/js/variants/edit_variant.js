document.addEventListener('DOMContentLoaded', function () {
  const variantId = (function () {
    const el = document.querySelector('h3.mb-0');
    if (!el) return null;
    const m = el.textContent.match(/#(\d+)/);
    return m ? parseInt(m[1], 10) : null;
  })();

  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || '';

  function csrfHeaders(headers = {}) {
    if (csrftoken) headers['X-CSRFToken'] = csrftoken;
    headers['Content-Type'] = 'application/json';
    return headers;
  }

  const variantTasksList = document.getElementById('variant-tasks-list');
  const addTaskBtn = document.getElementById('add-task-btn');
  const addTaskInput = document.getElementById('add-task-id');
  const addFeedback = document.getElementById('add-task-feedback');

  variantTasksList?.addEventListener('click', (e) => {
    const t = e.target;
    if (t.closest('.remove-task-btn')) {
      const btn = t.closest('.remove-task-btn');
      const taskId = btn.dataset.task;
      if (!taskId) return;
      if (!confirm('Удалить задачу из варианта?')) return;
      removeTaskFromVariant(taskId, btn);
    } else if (t.closest('.preview-task-btn')) {
      const btn = t.closest('.preview-task-btn');
      const taskId = btn.dataset.task;
      if (!taskId) return;
      fetchTaskAndShowPreview(taskId);
    } else if (t.closest('.move-up-btn')) {
      const btn = t.closest('.move-up-btn');
      const taskId = btn.dataset.task;
      moveTask(taskId, 'up', btn);
    } else if (t.closest('.move-down-btn')) {
      const btn = t.closest('.move-down-btn');
      const taskId = btn.dataset.task;
      moveTask(taskId, 'down', btn);
    }
  });

  addTaskBtn?.addEventListener('click', async (e) => {
    e.preventDefault();
    const id = parseInt(addTaskInput.value, 10);
    if (!id) {
      showAddFeedback('Введите корректный id задачи', 'warning');
      return;
    }
    addTaskBtn.disabled = true;
    showAddFeedback('Добавляю…', 'muted');
    try {
      const res = await fetch(`/variants/${variantId}/add_task`, {
        method: 'POST',
        headers: csrfHeaders(),
        body: JSON.stringify({ task_id: id }),
      });
      const data = await safeJson(res);
      if (!res.ok) {
        const message = data?.message || `Ошибка ${res.status}`;
        showAddFeedback(message, 'danger');
        console.error('add_task bad response text:', data?.rawText || data);
      } else if (!data.ok) {
        showAddFeedback(data.message || 'Не удалось добавить задачу', 'danger');
      } else {
        prependTaskToList(data.task);
        showAddFeedback('Задача добавлена', 'success');
        addTaskInput.value = '';
      }
    } catch (err) {
      showAddFeedback('Ошибка: ' + err, 'danger');
      console.error(err);
    } finally {
      addTaskBtn.disabled = false;
    }
  });

  document.body?.addEventListener('click', (e) => {
    const t = e.target;
    if (t.closest('.add-task-from-list-btn')) {
      const btn = t.closest('.add-task-from-list-btn');
      const taskId = btn.dataset.task;
      if (!taskId) return;
      btn.disabled = true;
      (async () => {
        try {
          const res = await fetch(`/variants/${variantId}/add_task`, {
            method: 'POST',
            headers: csrfHeaders(),
            body: JSON.stringify({ task_id: parseInt(taskId, 10) }),
          });
          const data = await safeJson(res);
          if (!res.ok) {
            alert(data?.message || `Ошибка ${res.status}`);
            console.error('add_task bad response text:', data?.rawText || data);
          } else if (!data.ok) {
            alert(data.message || 'Не удалось добавить задачу');
          } else {
            prependTaskToList(data.task);
            btn.textContent = 'Добавлено';
            btn.classList.remove('btn-success');
            btn.classList.add('btn-outline-secondary');
            btn.disabled = true;
          }
        } catch (err) {
          alert('Ошибка: ' + err);
        } finally {
          try { btn.disabled = false; } catch (e) {}
        }
      })();
    } else if (t.closest('.preview-task-btn')) {
      const btn = t.closest('.preview-task-btn');
      if (btn) fetchTaskAndShowPreview(btn.dataset.task);
    }
  });

  function showAddFeedback(msg, type = 'muted') {
    if (!addFeedback) return;
    addFeedback.innerHTML = `<div class="text-${type}">${msg}</div>`;
  }

  async function removeTaskFromVariant(taskId, buttonEl) {
    buttonEl.disabled = true;
    try {
      const res = await fetch(`/variants/${variantId}/remove_task`, {
        method: 'POST',
        headers: csrfHeaders(),
        body: JSON.stringify({ task_id: parseInt(taskId, 10) }),
      });
      const data = await safeJson(res);
      if (!res.ok) {
        alert(data?.message || `Ошибка ${res.status}`);
        console.error('remove_task bad response text:', data?.rawText || data);
        buttonEl.disabled = false;
        return;
      }
      if (!data.ok) {
        alert(data.message || 'Не удалось удалить задачу');
        buttonEl.disabled = false;
        return;
      }
      const row = buttonEl.closest('.variant-task-item');
      if (row) row.remove();
    } catch (err) {
      alert('Ошибка: ' + err);
      buttonEl.disabled = false;
    }
  }
  async function moveTask(taskId, direction, btn) {
    btn = btn || null;
    if (btn) btn.disabled = true;
    try {
      const res = await fetch(`/variants/${variantId}/move_task`, {
        method: 'POST',
        headers: csrfHeaders(),
        body: JSON.stringify({ task_id: parseInt(taskId,10), direction: direction }),
      });
      const data = await safeJson(res);
      if (!res.ok) {
        alert(data?.message || `Ошибка ${res.status}`);
        console.error('move_task bad response text:', data?.rawText || data);
        return;
      }
      if (!data.ok) {
        alert(data.message || 'Не удалось переместить задачу');
        return;
      }
      if (data.order && Array.isArray(data.order)) {
        reorderVariantListByOrder(data.order);
      } else if (data.moved && data.task_id) {
        const node = variantTasksList.querySelector(`.variant-task-item[data-task-id="${data.task_id}"]`);
        if (node) {
          if (direction === 'up' && node.previousElementSibling) {
            variantTasksList.insertBefore(node, node.previousElementSibling);
          } else if (direction === 'down' && node.nextElementSibling) {
            variantTasksList.insertBefore(node.nextElementSibling, node);
          }
        }
      }
    } catch (err) {
      alert('Ошибка: ' + err);
      console.error(err);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  function reorderVariantListByOrder(order) {
    const map = {};
    variantTasksList.querySelectorAll('.variant-task-item').forEach(el => {
      map[el.dataset.taskId] = el;
    });
    variantTasksList.innerHTML = '';
    order.forEach(id => {
      const idStr = String(id);
      if (map[idStr]) variantTasksList.appendChild(map[idStr]);
    });
  }

  function prependTaskToList(task) {
    if (!variantTasksList) return;
    if (variantTasksList.querySelector(`.variant-task-item[data-task-id="${task.id}"]`)) return;

    const node = document.createElement('div');
    node.className = 'list-group-item d-flex justify-content-between align-items-start variant-task-item';
    node.setAttribute('data-task-id', task.id);
    node.innerHTML = `
      <div class="flex-grow-1">
        <div class="fw-bold">№${task.number} — Задача #${task.id}</div>
        <div class="small text-muted mb-1">Источник: ${task.source || '-'}</div>
        <div class="task-statement-preview small text-truncate" style="max-height:6em; overflow:hidden;">${task.statement_html || ''}</div>
      </div>
      <div class="d-flex flex-column align-items-end gap-2">
        <a href="/tasks/view_task/${task.id}" class="btn btn-sm btn-outline-primary">К задаче</a>
        <button class="btn btn-sm btn-outline-secondary preview-task-btn" data-task="${task.id}">Просмотр</button>
        <div class="d-flex gap-1">
          //<button class="btn btn-sm btn-light move-up-btn" data-task="${task.id}" title="Вверх">▲</button>
          //<button class="btn btn-sm btn-light move-down-btn" data-task="${task.id}" title="Вниз">▼</button>
          <button class="btn btn-sm btn-danger remove-task-btn" data-task="${task.id}">Удалить</button>
        </div>
      </div>
    `;
    variantTasksList.prepend(node);
  }

  async function fetchTaskAndShowPreview(taskId) {
    try {
      const res = await fetch(`/tasks/${taskId}/json`);
      const data = await safeJson(res);
      if (!res.ok) {
        alert(data?.message || `Ошибка ${res.status}`);
        console.error('task json bad response:', data?.rawText || data);
        return;
      }
      if (!data.ok) {
        alert(data.message || 'Не удалось получить задачу');
        return;
      }
      showTaskModal(data.task);
    } catch (err) {
      alert('Ошибка: ' + err);
    }
  }

  function showTaskModal(task) {
    const modalId = 'tmpEditTaskModal';
    let container = document.getElementById(modalId);
    if (container) container.remove();

    container = document.createElement('div');
    container.id = modalId;
    container.innerHTML = `
      <div class="modal fade" tabindex="-1" id="${modalId}-inner">
        <div class="modal-dialog modal-lg modal-dialog-scrollable">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Задача №${task.number} (id: ${task.id})</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              ${task.statement_html || ''}
              <hr/>
              <div><strong>Ответ:</strong> ${task.answer || ''}</div>
              ${task.attachments && task.attachments.length ? '<hr/><div><strong>Вложения:</strong><ul>' + task.attachments.map(a => `<li><a href="${a.download_url}">${a.filename}</a> ${a.size ? '(' + Math.round(a.size/1024) + ' KB)' : ''}</li>`).join('') + '</ul></div>' : ''}
            </div>
          </div>
        </div>
      </div>`;
    document.body.appendChild(container);
    const modalEl = document.getElementById(`${modalId}-inner`);
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }

  async function safeJson(res) {
    const ct = res.headers.get('content-type') || '';
    try {
      if (ct.includes('application/json')) {
        return await res.json();
      } else {
        const text = await res.text();
        return { ok: false, rawText: text, status: res.status, message: `Ожидался JSON, пришёл ${ct}` };
      }
    } catch (err) {
      try {
        const text = await res.text();
        return { ok: false, rawText: text, status: res.status, message: err.message };
      } catch (e) {
        return { ok: false, rawText: null, status: res.status, message: err.message };
      }
    }
  }

  window.__moveTask = moveTask;
});

document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.js-delete-variant');
    if (!btn) return;

    if (!confirm('Вы уверены, что хотите удалить вариант целиком?')) return;

    const url = btn.dataset.url;
    const redirectUrl = btn.dataset.redirect;

    try {
        const resp = await fetch(url, {
            method: 'DELETE',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await resp.json();

        if (!resp.ok || !data.ok) {
            alert(data.message || 'Ошибка удаления варианта');
            return;
        }

        window.location.href = redirectUrl;

    } catch (err) {
        console.error(err);
        alert('Ошибка сети');
    }
});
