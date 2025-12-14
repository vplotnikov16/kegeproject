let attemptState = {
    attemptId: null,
    variantId: null,
    duration: 0,
    startedAt: null,
    finishedAt: null,
    tasks: [],
    answers: {},
    currentTaskIndex: -1,
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

    attemptState.tasks.forEach((task, index) => {
        const slide = document.createElement('div');
        slide.className = 'slide';
        slide.id = `taskSlide${task.variant_task_id}`;
        slide.innerHTML = createTaskSlideHTML(task, index);
        container.appendChild(slide);
    });
}

function createTaskSlideHTML(task, index) {
    let answerHTML = '';
    const currentAnswer = attemptState.answers[task.variant_task_id] || '';

    if (task.answer_type === 'single') {
        answerHTML = `
            <div class="task-answer-section">
                <div class="answer-label">Ответ:</div>
                <input type="text" class="answer-input task-answer" 
                    data-variant-task-id="${task.variant_task_id}" 
                    value="${currentAnswer}" 
                    placeholder="Введите ответ">
                <div class="save-indicator" id="indicator${task.variant_task_id}"></div>
            </div>
        `;
    } else if (task.answer_type === 'double') {
        const answers = parseComplexAnswer(currentAnswer);
        answerHTML = `
            <div class="task-answer-section">
                <div class="answer-label">Ответы:</div>
                <div class="answer-inputs-row">
                    <input type="text" class="answer-input task-answer-part" 
                        data-variant-task-id="${task.variant_task_id}" 
                        data-part="1" 
                        value="${answers[1] || ''}" 
                        placeholder="Ответ 1">
                    <input type="text" class="answer-input task-answer-part" 
                        data-variant-task-id="${task.variant_task_id}" 
                        data-part="2" 
                        value="${answers[2] || ''}" 
                        placeholder="Ответ 2">
                </div>
                <div class="save-indicator" id="indicator${task.variant_task_id}"></div>
            </div>
        `;
    } else if (task.answer_type === 'table') {
        answerHTML = createTableAnswerHTML(task, currentAnswer);
    }

    let attachmentsHTML = '';
    if (task.attachments && task.attachments.length > 0) {
        attachmentsHTML = `
            <div class="task-attachments">
                <p>Крепления:</p>
                ${task.attachments.map(att => `
                    <a href="${att.url}" class="attachment-link" target="_blank">⬇️ ${att.filename}</a>
                `).join('')}
            </div>
        `;
    }

    return `
        <div class="task-slide">
            <div class="task-header">
                <div class="task-number">КИМ № ${task.number}</div>
            </div>
            <div class="task-statement">${task.statement_html}</div>
            ${attachmentsHTML}
            ${answerHTML}
        </div>
    `;
}

function createTableAnswerHTML(task, currentAnswer) {
    const answers = parseTableAnswer(currentAnswer);
    const rows = task.answer_count || 10;
    const cols = 2;

    let tableHTML = `
        <div class="task-answer-section">
            <div class="answer-label">Ответы:</div>
            <table class="answer-table">
                <thead>
                    <tr>
                        <th>Но строки</th>
    `;
    
    for (let col = 1; col <= cols; col++) {
        tableHTML += `<th>Ответ ${col}</th>`;
    }
    
    tableHTML += `
                    </tr>
                </thead>
                <tbody>
    `;

    for (let row = 1; row <= rows; row++) {
        tableHTML += `
            <tr>
                <td>${row}</td>
        `;
        for (let col = 1; col <= cols; col++) {
            const value = answers[row] && answers[row][col] ? answers[row][col] : '';
            tableHTML += `
                <td>
                    <input type="text" class="table-answer" 
                        data-variant-task-id="${task.variant_task_id}" 
                        data-row="${row}" 
                        data-col="${col}" 
                        value="${value}">
                </td>
            `;
        }
        tableHTML += `
            </tr>
        `;
    }

    tableHTML += `
                </tbody>
            </table>
            <div class="save-indicator" id="indicator${task.variant_task_id}"></div>
        </div>
    `;

    return tableHTML;
}

function parseComplexAnswer(answerText) {
    if (!answerText) return {};
    try {
        return JSON.parse(answerText);
    } catch (e) {
        return {};
    }
}

function parseTableAnswer(answerText) {
    if (!answerText) return {};
    try {
        return JSON.parse(answerText);
    } catch (e) {
        return {};
    }
}

function setupEventListeners() {
    document.querySelectorAll('.task-btn').forEach((btn, index) => {
        btn.addEventListener('click', () => showTaskSlide(index));
    });

    document.getElementById('showInfoBtn').addEventListener('click', showInfoSlide);
    document.getElementById('infoBtn').addEventListener('click', showInfoSlide);

    document.getElementById('finishEarlyBtn').addEventListener('click', () => {
        document.getElementById('finishModal').classList.add('active');
    });
    document.getElementById('confirmFinishBtn').addEventListener('click', finishAttempt);

    document.querySelectorAll('.task-answer').forEach(input => {
        input.addEventListener('blur', saveAnswer);
    });

    document.querySelectorAll('.task-answer-part').forEach(input => {
        input.addEventListener('blur', saveComplexAnswer);
    });

    document.querySelectorAll('.table-answer').forEach(input => {
        input.addEventListener('blur', saveTableAnswer);
    });

    document.getElementById('closeBtn').addEventListener('click', () => {
        if (confirm('Вы действительно хотите выйти от экзамена?')) {
            window.history.back();
        }
    });

    document.getElementById('minimizeBtn').addEventListener('click', () => {
        const sidebar = document.querySelector('.attempt-sidebar');
        sidebar.classList.toggle('mobile-visible');
    });
}

function showInfoSlide() {
    hideAllSlides();
    document.getElementById('infoSlide').classList.add('active');
    attemptState.currentTaskIndex = -1;
    updateTaskButtonStates();
}

function showTaskSlide(index) {
    hideAllSlides();
    const task = attemptState.tasks[index];
    document.getElementById(`taskSlide${task.variant_task_id}`).classList.add('active');
    attemptState.currentTaskIndex = index;
    updateTaskButtonStates();
}

function hideAllSlides() {
    document.querySelectorAll('.slide').forEach(slide => {
        slide.classList.remove('active');
    });
}
function updateTaskButtonStates() {
    document.querySelectorAll('.task-btn').forEach((btn, index) => {
        const variantTaskId = parseInt(btn.dataset.variantTaskId);

        if (index === attemptState.currentTaskIndex) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }

        if (attemptState.answers[variantTaskId]) {
            btn.classList.add('answered');
        } else {
            btn.classList.remove('answered');
        }
    });
}

async function saveAnswer(event) {
    const input = event.target;
    const variantTaskId = parseInt(input.dataset.variantTaskId);
    const answerText = input.value.trim();

    if (!attemptState.isFinished) {
        await saveAnswerToServer(variantTaskId, answerText);
    }
}

async function saveComplexAnswer(event) {
    const input = event.target;
    const variantTaskId = parseInt(input.dataset.variantTaskId);
    const part = parseInt(input.dataset.part);

    const answers = {};
    document.querySelectorAll(`.task-answer-part[data-variant-task-id="${variantTaskId}"]`).forEach(inp => {
        const p = parseInt(inp.dataset.part);
        const val = inp.value.trim();
        if (val) {
            if (!answers[p]) answers[p] = {};
            answers[p] = val;
        }
    });

    const answerText = Object.keys(answers).length > 0 ? JSON.stringify(answers) : '';

    if (!attemptState.isFinished) {
        await saveAnswerToServer(variantTaskId, answerText);
    }
}

async function saveTableAnswer(event) {
    const input = event.target;
    const variantTaskId = parseInt(input.dataset.variantTaskId);
    const row = parseInt(input.dataset.row);
    const col = parseInt(input.dataset.col);

    const answers = {};
    document.querySelectorAll(`.table-answer[data-variant-task-id="${variantTaskId}"]`).forEach(inp => {
        const r = parseInt(inp.dataset.row);
        const c = parseInt(inp.dataset.col);
        const val = inp.value.trim();
        if (val) {
            if (!answers[r]) answers[r] = {};
            answers[r][c] = val;
        }
    });

    const answerText = Object.keys(answers).length > 0 ? JSON.stringify(answers) : '';

    if (!attemptState.isFinished) {
        await saveAnswerToServer(variantTaskId, answerText);
    }
}

async function saveAnswerToServer(variantTaskId, answerText) {
    if (attemptState.isSaving) return;

    attemptState.isSaving = true;
    const indicator = document.getElementById(`indicator${variantTaskId}`);
    if (indicator) {
        indicator.textContent = 'Сохранение...';
        indicator.className = 'save-indicator saving';
    }

    try {
        const response = await fetch(`/attempts/${attemptState.attemptId}/save-answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                variant_task_id: variantTaskId,
                answer_text: answerText
            })
        });

        if (response.ok) {
            attemptState.answers[variantTaskId] = answerText;
            updateStats();
            updateTaskButtonStates();
            
            if (indicator) {
                indicator.textContent = 'Сохранено';
                indicator.className = 'save-indicator saved';
                setTimeout(() => {
                    indicator.textContent = '';
                }, 2000);
            }
        } else {
            const data = await response.json();
            if (indicator) {
                indicator.textContent = 'Ошибка';
                indicator.className = 'save-indicator error';
            }
            console.error('Error saving answer:', data);
        }
    } catch (error) {
        if (indicator) {
            indicator.textContent = 'Ошибка сети';
            indicator.className = 'save-indicator error';
        }
        console.error('Network error:', error);
    } finally {
        attemptState.isSaving = false;
    }
}

function updateStats() {
    const answered = Object.keys(attemptState.answers).length;
    const total = attemptState.tasks.length;
    document.getElementById('answeredCount').textContent = answered;
    document.getElementById('answeredLabel').textContent = `${answered}/${total} ответов`;
}

function startTimer() {
    const startTime = attemptState.startedAt.getTime();
    const duration = attemptState.duration * 1000;
    const endTime = startTime + duration;

    function updateTimer() {
        const now = new Date().getTime();
        const remaining = endTime - now;

        if (remaining <= 0) {
            clearInterval(attemptState.timerInterval);
            document.getElementById('timer').textContent = '00:00:00';
            finishAttempt();
            return;
        }

        const hours = Math.floor(remaining / (1000 * 60 * 60));
        const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((remaining % (1000 * 60)) / 1000);

        const timerDisplay = document.getElementById('timer');
        timerDisplay.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        timerDisplay.classList.remove('warning', 'critical');
        if (remaining < 5 * 60 * 1000) {
            timerDisplay.classList.add('critical');
        } else if (remaining < 15 * 60 * 1000) {
            timerDisplay.classList.add('warning');
        }
    }

    updateTimer();
    attemptState.timerInterval = setInterval(updateTimer, 1000);
}

async function finishAttempt() {
    document.getElementById('finishModal').classList.remove('active');

    try {
        const response = await fetch(`/attempts/${attemptState.attemptId}/finish`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            attemptState.isFinished = true;
            clearInterval(attemptState.timerInterval);
            window.location.href = `/attempts/${attemptState.attemptId}/results-page`;
        } else {
            alert('Ошибка при завершении экзамена');
        }
    } catch (error) {
        console.error('Error finishing attempt:', error);
        alert('Ошибка сети');
    }
}
