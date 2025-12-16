document.addEventListener('DOMContentLoaded', function () {
  const kimCheckboxes = Array.from(document.querySelectorAll('.kim-checkbox'));
  const generateBtn = document.getElementById('generate-btn');
  const variantsList = document.getElementById('variants-list');
  const searchBtn = document.getElementById('search-btn');
  const searchInput = document.getElementById('search-number');
  const listAllBtn = document.getElementById('list-all-btn');
  const variantPreviewCard = document.getElementById('variant-preview');
  const variantTitle = document.getElementById('variant-title');
  const variantMeta = document.getElementById('variant-meta');
  const variantTasks = document.getElementById('variant-tasks');
  const openVariantBtn = document.getElementById('open-variant-btn');
  const startExamBtn = document.getElementById('start-exam-btn');

  function parseKimKey(key) {
    if (!key) return [];
    if (key.includes('-')) {
      const [a, b] = key.split('-', 2).map(s => parseInt(s, 10));
      if (Number.isFinite(a) && Number.isFinite(b) && b >= a) {
        const out = [];
        for (let i = a; i <= b; i++) out.push(i);
        return out;
      }
      return [];
    }
    const n = parseInt(key, 10);
    return Number.isFinite(n) ? [n] : [];
  }

  function setCountEnabledForKey(key, enabled) {
    const groupEl = document.querySelector(`#kim-count-${key}`);
    if (groupEl) {
      if (enabled) groupEl.removeAttribute('disabled'); else groupEl.setAttribute('disabled', 'disabled');
      return;
    }
    const nums = parseKimKey(String(key));
    nums.forEach(n => {
      const el = document.querySelector(`#kim-count-${n}`);
      if (!el) return;
      if (enabled) el.removeAttribute('disabled'); else el.setAttribute('disabled', 'disabled');
    });
  }

  function updateGenerateState() {
    if (!generateBtn) return;
    const any = kimCheckboxes.some(cb => cb.checked);
    generateBtn.disabled = !any;
  }

  kimCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      const key = String(cb.dataset.kim);
      const checked = cb.checked;
      setCountEnabledForKey(key, checked);

      const nums = parseKimKey(key);
      nums.forEach(n => {
        const individualCb = document.querySelector(`#kim-${n}`);
        if (individualCb && individualCb !== cb) {
          individualCb.checked = checked;
        }
      });

      updateGenerateState();
    });
  });

  updateGenerateState();

  function collectSelection() {
    const selection = [];
    kimCheckboxes.forEach(cb => {
      if (!cb.checked) return;
      const key = String(cb.dataset.kim);
      const nums = parseKimKey(key);
      const groupCountEl = document.querySelector(`#kim-count-${key}`);
      if (groupCountEl) {
        const raw = groupCountEl.value;
        const cnt = Math.max(1, parseInt(raw, 10) || 1);
        nums.forEach(n => selection.push({ kim: n, count: cnt }));
      } else {
        nums.forEach(n => {
          const el = document.querySelector(`#kim-count-${n}`);
          const raw = el ? el.value : '1';
          const cnt = Math.max(1, parseInt(raw, 10) || 1);
          selection.push({ kim: n, count: cnt });
        });
      }
    });
    return selection;
  }

  function renderVariantsList(items) {
    if (!variantsList) return;
    variantsList.innerHTML = '';
    if (!items || items.length === 0) {
      variantsList.innerHTML = `<div class="text-muted small">Ничего не найдено</div>`;
      return;
    }
    items.forEach(v => {
      const el = document.createElement('button');
      el.type = 'button';
      el.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
      el.textContent = `Вариант #${v.id} — ${v.task_count} задач`;
      const meta = document.createElement('small');
      meta.className = 'text-muted';
      meta.textContent = v.source ? ` ${v.source}` : '';
      el.appendChild(meta);
      el.addEventListener('click', () => fetchVariantById(v.id));
      variantsList.appendChild(el);
    });
  }

  if (listAllBtn) {
    listAllBtn.addEventListener('click', async () => {
      if (!variantsList) return;
      variantsList.innerHTML = '<div class="text-muted small">Загрузка…</div>';
      try {
        const res = await fetch('/variants/search?all=1');
        const data = await res.json();
        if (data.ok) renderVariantsList(data.variants);
        else variantsList.innerHTML = `<div class="alert alert-warning p-2">${data.message || 'Неизвестная ошибка'}</div>`;
      } catch (err) {
        variantsList.innerHTML = `<div class="alert alert-danger p-2">Ошибка: ${err}</div>`;
      }
    });
  }

  if (searchBtn) {
    searchBtn.addEventListener('click', () => {
      const id = parseInt(searchInput.value, 10);
      if (!id) {
        if (variantsList) variantsList.innerHTML = `<div class="alert alert-warning p-2">Введите корректный id варианта</div>`;
        return;
      }
      fetchVariantById(id);
    });
  }

  async function fetchVariantById(id) {
    if (!variantsList || !variantPreviewCard) return;
    variantsList.innerHTML = '';
    variantPreviewCard.classList.add('d-none');
    variantsList.innerHTML = `<div class="text-muted small">Загрузка варианта #${id}…</div>`;
    try {
      const res = await fetch(`/variants/search?id=${encodeURIComponent(id)}`);
      const data = await res.json();
      if (!res.ok || !data.ok) {
        variantsList.innerHTML = `<div class="alert alert-warning p-2">${data.message || 'Вариант не найден'}</div>`;
        return;
      }
      const v = data.variant;
      showVariantPreviewFromTasks(v.tasks, v.id, v.source, v.created_at);
    } catch (err) {
      variantsList.innerHTML = `<div class="alert alert-danger p-2">Ошибка: ${err}</div>`;
    }
  }

  function showVariantPreviewFromTasks(tasks, variantId, source, createdAt) {
    if (!variantsList || !variantPreviewCard || !variantTasks) return;
    variantsList.innerHTML = '';
    variantTasks.innerHTML = '';
    variantPreviewCard.classList.remove('d-none');
    variantTitle.textContent = `Вариант ${variantId ? ('#' + variantId) : '(предпросмотр)'}`;
    variantMeta.textContent = `${tasks.length} задач · ${source || ''} ${createdAt ? '· ' + createdAt : ''}`;
    tasks.forEach(t => {
      const col = document.createElement('div');
      col.className = 'col-12';
      const card = document.createElement('div');
      card.className = 'task-card';
      card.innerHTML = `<div class="d-flex justify-content-between align-items-start">
          <div><strong>№${t.number}</strong> <small class="text-muted"> (id:${t.id})</small></div>
          <div><a class="btn btn-sm btn-outline-primary" href="/tasks/view_task/${t.id}">К задаче</a></div>
        </div>
        <div class="mt-2"><div class="small text-muted">${sanitizePreview(t.preview)}</div></div>`;
      col.appendChild(card);
      variantTasks.appendChild(col);
    });
    if (openVariantBtn) {
      openVariantBtn.onclick = function () {
        if (variantId) window.location.href = `/variants/view_variant/${variantId}`;
      };
    }
    if (startExamBtn) {
      startExamBtn.onclick = function () {
        if (variantId) window.location.href = `/variants/start_exam/${variantId}`;
      };
    }
  }

  function sanitizePreview(html) {
    if (!html) return '';
    return html.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
               .replace(/<\/?[^>]+(>|$)/g, '')
               .substring(0, 800);
  }

  async function openTaskQuickView(taskId) {
    try {
      const res = await fetch(`/variants/task/${taskId}`);
      const data = await res.json();
      if (res.ok && data.ok) showTaskModal(data.task);
      else alert(data.message || 'Не удалось получить задачу');
    } catch (err) {
      alert('Ошибка: ' + err);
    }
  }

  function showTaskModal(task) {
    const html = `<div><h5>Задача №${task.number} (id: ${task.id})</h5>
      <div class="mt-2">${task.statement_html || ''}</div>
      <hr>
      <div><strong>Ответ:</strong> ${task.answer || ''}</div></div>`;
    if (typeof bootstrap !== 'undefined') {
      const modalId = 'tmpTaskModal';
      let container = document.getElementById(modalId);
      if (container) container.remove();
      container = document.createElement('div');
      container.id = modalId;
      container.innerHTML = `<div class="modal fade" tabindex="-1" id="${modalId}-inner">
        <div class="modal-dialog modal-lg modal-dialog-scrollable">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Задача №${task.number}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">${task.statement_html || ''}<hr><strong>Ответ:</strong> ${task.answer || ''}</div>
          </div>
        </div>
      </div>`;
      document.body.appendChild(container);
      const modalEl = document.getElementById(`${modalId}-inner`);
      const modal = new bootstrap.Modal(modalEl);
      modal.show();
    } else {
      const w = window.open("", "_blank", "width=800,height=600,scrollbars=yes");
      w.document.write(html);
      w.document.close();
    }
  }

  window.__collectVariantSelection = collectSelection;
});
