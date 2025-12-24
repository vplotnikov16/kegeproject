let attemptState = {
    attemptId: null,
    variantId: null,
    duration: 0,
    startedAt: null,
    finishedAt: null,
    tasks: [],
    answers: {},
    currentVariantTaskId: null,
    timerInterval: null,
    isSaving: false,
    isFinished: false
};

async function initializeAttempt(data) {
    attemptState.attemptId = data.attemptId;
    attemptState.variantId = data.variantId;
    attemptState.duration = data.duration;
    attemptState.startedAt = new Date(data.startedAt);
    attemptState.finishedAt = data.finishedAt ? new Date(data.finishedAt) : null;
    attemptState.isFinished = !!attemptState.finishedAt;

    const res = await fetch(`/attempts/${attemptState.attemptId}/data`);
    const json = await res.json();

    attemptState.tasks = json.tasks;

    attemptState.tasks.forEach(t => {
        if (t.current_answer) {
            attemptState.answers[t.variant_task_id] = t.current_answer;
        }
    });

    renderTaskSlides();
    setupEventListeners();
    updateStats();
    startTimer();
    showInfoSlide();
}

function renderTaskSlides() {
    const container = document.getElementById('taskSlidesContainer');
    container.innerHTML = '';

    attemptState.tasks.forEach(task => {
        const slide = document.createElement('div');
        slide.className = 'slide';
        slide.id = `taskSlide${task.variant_task_id}`;
        slide.innerHTML = createTaskSlideHTML(task);
        container.appendChild(slide);
    });
}

function createTaskSlideHTML(task) {
    const { rows, cols } = getTableShapeByTaskNumber(task.number);
    const saved = parseCSV(attemptState.answers[task.variant_task_id]);

    let table = '<table class="answer-table"><tbody>';

    for (let r = 0; r < rows; r++) {
        table += '<tr>';
        for (let c = 0; c < cols; c++) {
            const val = saved[r]?.[c] || '';
            table += `
                <td>
                    <input type="text"
                           class="answer-cell"
                           data-variant-task-id="${task.variant_task_id}"
                           data-row="${r}"
                           data-col="${c}"
                           value="${val}">
                </td>
            `;
        }
        table += '</tr>';
    }

    table += '</tbody></table>';

    // Рендеринг вложений (если есть)
    let attachmentsHTML = '';
    if (task.attachments && task.attachments.length > 0) {
        attachmentsHTML = '<div class="task-attachments">';
        attachmentsHTML += '<div class="attachments-title">Вложения:</div>';
        attachmentsHTML += '<div class="attachments-list">';

        task.attachments.forEach(attachment => {
            const sizeKB = attachment.size ? Math.round(attachment.size / 1024) : 0;

            attachmentsHTML += `
                <a href="${attachment.download_url}"
                   class="attachment-item"
                   download="${attachment.filename}"
                   target="_blank">
                    <div class="attachment-info">
                        <div class="attachment-name">${attachment.filename} (${sizeKB} КБ)</div>
                    </div>
                </a>
            `;
        });

        attachmentsHTML += '</div></div>';
    }

    return `
        <div class="task-slide">
            <div class="task-header">
                <div class="task-number">Задача №${task.number}</div>
            </div>
            <div class="task-statement">${task.statement_html}</div>
            ${attachmentsHTML}
            <div class="task-answer-section">
                ${table}
                <button class="save-answer-btn"
                        data-variant-task-id="${task.variant_task_id}">
                    Сохранить ответ
                </button>
            </div>
        </div>
    `;
}

function getTableShapeByTaskNumber(n) {
    if (n >= 1 && n <= 16) return { rows: 1, cols: 1 };
    if (n === 17 || n === 18) return { rows: 1, cols: 2 };
    if (n === 19) return { rows: 1, cols: 3 };
    if (n >= 22 && n <= 24) return { rows: 1, cols: 1 };
    if (n === 25) return { rows: 10, cols: 2 };
    if (n === 26) return { rows: 1, cols: 2 };
    if (n === 27) return { rows: 2, cols: 2 };
    return { rows: 1, cols: 1 };
}

function setupEventListeners() {
    document.querySelectorAll('.task-btn').forEach(btn => {
        btn.addEventListener('click', () =>
            showTaskSlideByVariantId(parseInt(btn.dataset.variantTaskId))
        );
    });

    document.addEventListener('input', e => {
        if (e.target.classList.contains('answer-cell')) {
            e.target.value = e.target.value.replace(/[^a-zA-Z0-9а-яА-Я]/g, '');
        }
    });

    document.addEventListener('click', e => {
        if (e.target.classList.contains('save-answer-btn')) {
            saveTableAnswer(e.target.dataset.variantTaskId);
        }
    });

    bindFinishConfirmation('finishEarlyBtn');
    bindFinishConfirmation('closeBtn');
    bindFinishConfirmation('infoBtn');
    bindFinishConfirmation('minimizeBtn');

    document.getElementById('showInfoBtn')?.addEventListener('click', showInfoSlide);
}

function showInfoSlide() {
    hideAllSlides();
    document.getElementById('infoSlide').classList.add('active');
    attemptState.currentVariantTaskId = null;
    updateTaskButtonStates();
}

function showTaskSlideByVariantId(id) {
    hideAllSlides();
    document.getElementById(`taskSlide${id}`)?.classList.add('active');
    attemptState.currentVariantTaskId = id;
    updateTaskButtonStates();
}

function hideAllSlides() {
    document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
}

function updateTaskButtonStates() {
    document.querySelectorAll('.task-btn').forEach(btn => {
        const id = parseInt(btn.dataset.variantTaskId);
        btn.classList.toggle('active', id === attemptState.currentVariantTaskId);
        btn.classList.toggle('answered', Boolean(attemptState.answers[id]));
    });
}

async function saveTableAnswer(variantTaskId) {
    if (attemptState.isSaving || attemptState.isFinished) return;
    attemptState.isSaving = true;

    const cells = document.querySelectorAll(
        `.answer-cell[data-variant-task-id="${variantTaskId}"]`
    );

    const matrix = [];
    cells.forEach(cell => {
        const r = parseInt(cell.dataset.row);
        const c = parseInt(cell.dataset.col);
        if (!matrix[r]) matrix[r] = [];
        matrix[r][c] = cell.value || '';
    });

    const csv = matrix.map(r => r.join(',')).join('\n');

    await fetch(`/attempts/${attemptState.attemptId}/save-answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            variant_task_id: variantTaskId,
            answer_text: csv
        })
    });

    attemptState.answers[variantTaskId] = csv;
    updateStats();
    updateTaskButtonStates();
    attemptState.isSaving = false;
}

function updateStats() {
    // Подсчёт общего количества задач с учётом задачи 19
    let totalTasks = 0;
    attemptState.tasks.forEach(task => {
        if (task.number === 19) {
            totalTasks += 3;  // Задача 19 = 3 задачи
        } else {
            totalTasks += 1;
        }
    });

    // Подсчёт отвеченных задач
    let answeredCount = 0;

    for (const [variantTaskId, answerText] of Object.entries(attemptState.answers)) {
        if (!answerText || !answerText.trim()) continue;

        // Найти задачу по variant_task_id
        const task = attemptState.tasks.find(t => t.variant_task_id == variantTaskId);
        if (!task) continue;

        if (task.number === 19) {
            // Для задачи 19 считаем каждую заполненную ячейку
            const filled = countFilledCellsInCSV(answerText);
            answeredCount += filled;
        } else {
            // Для остальных задач: если есть хотя бы одна заполненная ячейка = ответ дан
            if (hasAnyFilledCell(answerText)) {
                answeredCount += 1;
            }
        }
    }

    document.getElementById('answeredLabel').textContent = `${answeredCount}/${totalTasks}`;
}

/**
 * Подсчитать количество заполненных ячеек в CSV-ответе для задачи 19
 * Формат CSV: "A,B,C" где каждая непустая ячейка считается
 */
function countFilledCellsInCSV(csv) {
    if (!csv || !csv.trim()) return 0;

    const cells = csv.split(',').map(c => c.trim());
    return cells.filter(c => c.length > 0).length;
}

/**
 * Проверить, есть ли хотя бы одна заполненная ячейка в CSV-ответе
 * Для задач с таблицами (кроме 19): любая заполненная ячейка = ответ дан
 */
function hasAnyFilledCell(csv) {
    if (!csv || !csv.trim()) return false;

    // Парсим CSV
    const rows = csv.split('\n');
    for (const row of rows) {
        const cells = row.split(',');
        if (cells.some(c => c.trim().length > 0)) {
            return true;
        }
    }
    return false;
}


function startTimer() {
    if (attemptState.isFinished) return;

    const end = attemptState.startedAt.getTime() + attemptState.duration * 1000;

    attemptState.timerInterval = setInterval(() => {
        const diff = end - Date.now();
        if (diff <= 0) return finishAttempt();

        const h = String(Math.floor(diff / 3600000)).padStart(2, '0');
        const m = String(Math.floor(diff % 3600000 / 60000)).padStart(2, '0');
        const s = String(Math.floor(diff % 60000 / 1000)).padStart(2, '0');
        document.getElementById('timer').textContent = `${h}:${m}:${s}`;
    }, 1000);
}

async function finishAttempt() {
    clearInterval(attemptState.timerInterval);
    await fetch(`/attempts/${attemptState.attemptId}/finish`, { method: 'POST' });
    window.location.href = `/attempts/${attemptState.attemptId}/results-page`;
}

function confirmAndFinishAttempt(msg = 'Вы уверены, что хотите завершить попытку?') {
    if (!attemptState.isFinished && confirm(msg)) finishAttempt();
}

function bindFinishConfirmation(id) {
    document.getElementById(id)?.addEventListener('click', e => {
        e.preventDefault();
        confirmAndFinishAttempt();
    });
}

function parseCSV(text) {
    if (!text) return [];
    return text.split('\n').map(r => r.split(','));
}
