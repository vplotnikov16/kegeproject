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
  const selectAllBtn = document.getElementById('select-all-btn');

  function parseKimKey(key) {
    if (!key) return [];
    if (key.includes('-')) {
      const [a, b] = key.split('-', 2).map(n => parseInt(n, 10));
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
    const el = document.querySelector(`#kim-count-${key}`);
    if (el) {
      el.disabled = !enabled;
      return;
    }
    parseKimKey(key).forEach(n => {
      const e = document.querySelector(`#kim-count-${n}`);
      if (e) e.disabled = !enabled;
    });
  }

  function updateGenerateState() {
    generateBtn.disabled = !kimCheckboxes.some(cb => cb.checked);
  }

  function getSelectAllState() {
    const checkedCount = kimCheckboxes.filter(cb => cb.checked).length;
    if (checkedCount === 0) return 'unchecked';
    if (checkedCount === kimCheckboxes.length) return 'checked';
    return 'partial';
  }

  function updateSelectAllUI() {
    if (!selectAllBtn) return;

    const state = getSelectAllState();
    selectAllBtn.classList.remove(
      'btn-outline-secondary',
      'btn-secondary',
      'btn-success'
    );

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
      setCountEnabledForKey(cb.dataset.kim, checked);
    });
    updateGenerateState();
    updateSelectAllUI();
  }

  if (selectAllBtn) {
    selectAllBtn.addEventListener('click', () => {
      const state = getSelectAllState();
      setAllCheckboxes(state !== 'checked');
    });
  }

  kimCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      const key = cb.dataset.kim;
      const checked = cb.checked;

      setCountEnabledForKey(key, checked);

      parseKimKey(key).forEach(n => {
        const ind = document.querySelector(`#kim-${n}`);
        if (ind && ind !== cb) ind.checked = checked;
      });

      updateGenerateState();
      updateSelectAllUI();
    });
  });

  updateGenerateState();
  updateSelectAllUI();

    if (searchBtn) {
      searchBtn.addEventListener('click', async () => {
        const id = searchInput.value.trim();

        if (!id) {
          variantsList.innerHTML = '<div class="alert alert-warning p-2">Введите ID варианта</div>';
          return;
        }

        await fetchVariantById(id);
      });
    }

    if (searchInput) {
      searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          searchBtn?.click();
        }
      });
    }

    if (listAllBtn) {
      listAllBtn.addEventListener('click', async () => {
        variantsList.innerHTML = '<div class="text-muted small">Загрузка списка вариантов…</div>';
        variantPreviewCard.classList.add('d-none');

        try {
          const res = await fetch('/variants/search?all=1');
          const data = await res.json();

          if (!data.ok) {
            variantsList.innerHTML = `<div class="alert alert-warning p-2">${data.message || 'Ошибка загрузки'}</div>`;
            return;
          }

          renderVariantsList(data.variants);
        } catch (err) {
          variantsList.innerHTML = `<div class="alert alert-danger p-2">Ошибка: ${err.message}</div>`;
        }
      });
    }

  function collectSelection() {
    const selection = [];
    kimCheckboxes.forEach(cb => {
      if (!cb.checked) return;
      const key = cb.dataset.kim;
      const nums = parseKimKey(key);
      const groupCount = document.querySelector(`#kim-count-${key}`);

      if (groupCount) {
        const cnt = Math.max(1, parseInt(groupCount.value, 10) || 1);
        nums.forEach(n => selection.push({ kim: n, count: cnt }));
      } else {
        nums.forEach(n => {
          const el = document.querySelector(`#kim-count-${n}`);
          const cnt = Math.max(1, parseInt(el?.value, 10) || 1);
          selection.push({ kim: n, count: cnt });
        });
      }
    });
    return selection;
  }

  function renderVariantsList(items) {
    variantsList.innerHTML = '';
    if (!items || items.length === 0) {
      variantsList.innerHTML = '<div class="text-muted small">Ничего не найдено</div>';
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

  async function fetchVariantById(id) {
    variantsList.innerHTML = `<div class="text-muted small">Загрузка варианта #${id}…</div>`;
    variantPreviewCard.classList.add('d-none');

    try {
      const res = await fetch(`/variants/search?id=${id}`);
      const data = await res.json();

      if (!data.ok) {
        variantsList.innerHTML = `<div class="alert alert-warning p-2">${data.message}</div>`;
        return;
      }

      showVariantPreview(data.variant);
    } catch (err) {
      variantsList.innerHTML = `<div class="alert alert-danger p-2">${err}</div>`;
    }
  }

  function showVariantPreview(v) {
    variantsList.innerHTML = '';
    variantTasks.innerHTML = '';
    variantPreviewCard.classList.remove('d-none');

    variantTitle.textContent = `Вариант #${v.id}`;
    variantMeta.textContent = `${v.tasks.length} задач · ${v.source || ''}`;

    v.tasks.forEach(t => {
      const col = document.createElement('div');
      col.className = 'col-12';
      col.innerHTML = `
        <div class="task-card">
          <strong>№${t.number}</strong>
          <div class="small text-muted">${sanitizePreview(t.preview)}</div>
        </div>`;
      variantTasks.appendChild(col);
    });

    openVariantBtn.onclick = () => location.href = `/variants/view_variant/${v.id}`;
    startExamBtn.onclick = () => location.href = `/variants/start_exam/${v.id}`;
  }

  function sanitizePreview(html) {
    return (html || '')
      .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
      .replace(/<\/?[^>]+>/g, '')
      .substring(0, 800);
  }

  window.__collectVariantSelection = collectSelection;

});
