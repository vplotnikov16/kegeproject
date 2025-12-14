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

    try {
        const response = await fetch(`/attempts/${attemptState.attemptId}/data`);
        const jsonData = await response.json();

        attemptState.tasks = jsonData.tasks;

        attemptState.tasks.forEach(task => {
            if (task.current_answer) {
                attemptState.answers[task.variant_task_id] = task.current_answer;
            }
        });

        renderTaskSlides();
        setupEventListeners();
        updateStats();
        startTimer();

        if (!attemptState.isFinished) {
            showInfoSlide();
        }
    } catch (error) {
        console.error('Error loading attempt data:', error);
        alert('Ошибка при загрузке данных');
    }
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
    const currentAnswer = attemptState.answers[task.variant_task_id] || '';
    let answerHTML = '';

    if (task.answer_type === 'single') {
        answerHTML = `
            <div class="task-answer-section">
                <div class="answer-label">Ответ:</div>
                <input type="text"
                       class="answer-input task-answer"
                       data-variant-task-id="${task.variant_task_id}"
                       value="${currentAnswer}">
                <div class="save-indicator" id="indicator${task.variant_task_id}"></div>
            </div>
        `;
    }

    if (task.answer_type === 'double') {
        const answers = parseJSON(currentAnswer);
        answerHTML = `
            <div class="task-answer-section">
                <div class="answer-label">Ответы:</div>
                <div class="answer-inputs-row">
                    <input type="text"
                           class="answer-input task-answer-part"
                           data-variant-task-id="${task.variant_task_id}"
                           data-part="1"
                           value="${answers[1] || ''}">
                    <input type="text"
                           class="answer-input task-answer-part"
                           data-variant-task-id="${task.variant_task_id}"
                           data-part="2"
                           value="${answers[2] || ''}">
                </div>
                <div class="save-indicator" id="indicator${task.variant_task_id}"></div>
            </div>
        `;
    }

    let attachmentsHTML = '';
    if (task.attachments?.length) {
        attachmentsHTML = `
            <div class="task-attachments">
                ${task.attachments.map(a =>
                    `<a href="${a.url}" target="_blank">⬇ ${a.filename}</a>`
                ).join('')}
            </div>
        `;
    }

    return `
        <div class="task-slide">
            <div class="task-header">
                <div class="task-number">Задача №${task.number} (#${task.id})</div>
            </div>
            <div class="task-statement">${task.statement_html}</div>
            ${attachmentsHTML}
            ${answerHTML}
        </div>
    `;
}

function setupEventListeners() {
    document.querySelectorAll('.task-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const variantTaskId = parseInt(btn.dataset.variantTaskId);
            showTaskSlideByVariantId(variantTaskId);
        });
    });

    document.querySelectorAll('.task-answer').forEach(i =>
        i.addEventListener('blur', saveAnswer)
    );

    document.querySelectorAll('.task-answer-part').forEach(i =>
        i.addEventListener('blur', saveComplexAnswer)
    );

    document.getElementById('showInfoBtn')?.addEventListener('click', showInfoSlide);
    document.getElementById('infoBtn')?.addEventListener('click', showInfoSlide);

    bindFinishConfirmation('finishEarlyBtn', 'Вы уверены, что хотите завершить попытку?');
    bindFinishConfirmation('closeBtn', 'Вы уверены, что хотите завершить попытку?');
    bindFinishConfirmation('infoBtn', 'Вы уверены, что хотите завершить попытку?');
    bindFinishConfirmation('minimizeBtn', 'Вы уверены, что хотите завершить попытку?');
}

function showInfoSlide() {
    hideAllSlides();
    document.getElementById('infoSlide').classList.add('active');
    attemptState.currentVariantTaskId = null;
    updateTaskButtonStates();
}

function showTaskSlideByVariantId(variantTaskId) {
    hideAllSlides();

    const slide = document.getElementById(`taskSlide${variantTaskId}`);
    if (!slide) return;

    slide.classList.add('active');
    attemptState.currentVariantTaskId = variantTaskId;
    updateTaskButtonStates();
}

function hideAllSlides() {
    document.querySelectorAll('.slide').forEach(s =>
        s.classList.remove('active')
    );
}

function updateTaskButtonStates() {
    document.querySelectorAll('.task-btn').forEach(btn => {
        const id = parseInt(btn.dataset.variantTaskId);

        btn.classList.toggle(
            'active',
            id === attemptState.currentVariantTaskId
        );

        btn.classList.toggle(
            'answered',
            Boolean(attemptState.answers[id])
        );
    });
}

/* ===================== SAVE ANSWERS ===================== */

async function saveAnswer(e) {
    const input = e.target;
    const id = parseInt(input.dataset.variantTaskId);
    const text = input.value.trim();

    if (!attemptState.isFinished) {
        await saveAnswerToServer(id, text);
    }
}

async function saveComplexAnswer(e) {
    const id = parseInt(e.target.dataset.variantTaskId);
    const answers = {};

    document
        .querySelectorAll(`.task-answer-part[data-variant-task-id="${id}"]`)
        .forEach(i => {
            if (i.value.trim()) {
                answers[i.dataset.part] = i.value.trim();
            }
        });

    const text = Object.keys(answers).length
        ? JSON.stringify(answers)
        : '';

    if (!attemptState.isFinished) {
        await saveAnswerToServer(id, text);
    }
}

async function saveAnswerToServer(variantTaskId, answerText) {
    if (attemptState.isSaving) return;

    attemptState.isSaving = true;
    const indicator = document.getElementById(`indicator${variantTaskId}`);

    try {
        const res = await fetch(
            `/attempts/${attemptState.attemptId}/save-answer`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    variant_task_id: variantTaskId,
                    answer_text: answerText
                })
            }
        );

        if (res.ok) {
            attemptState.answers[variantTaskId] = answerText;
            updateStats();
            updateTaskButtonStates();
        }
    } finally {
        attemptState.isSaving = false;
    }
}

function updateStats() {
    const answered = Object.keys(attemptState.answers).length;
    const total = attemptState.tasks.length;
    document.getElementById('answeredLabel').textContent = `${answered}/${total}`;
}

function startTimer() {
    if (attemptState.isFinished) return;

    const end =
        attemptState.startedAt.getTime() +
        attemptState.duration * 1000;

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

function parseJSON(text) {
    try {
        return JSON.parse(text || '{}');
    } catch {
        return {};
    }
}

function confirmAndFinishAttempt(message = 'Вы уверены, что хотите завершить попытку?') {
    if (attemptState.isFinished) return;

    const confirmed = window.confirm(message);
    if (!confirmed) return;

    finishAttempt();
}

function bindFinishConfirmation(buttonId, message) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    btn.addEventListener('click', event => {
        event.preventDefault();
        confirmAndFinishAttempt(message);
    });
}
