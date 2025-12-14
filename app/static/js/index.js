const scoreDistCtx = document.getElementById('scoreDistributionChart').getContext('2d');
const scoreData = {{ dashboard_data.score_distribution|safe }};

new Chart(scoreDistCtx, {
    type: 'doughnut',
    data: {
        labels: Object.keys(scoreData),
        datasets: [{
            data: Object.values(scoreData),
            backgroundColor: [
                '#ff6b6b',
                '#ffa500',
                '#ffd93d',
                '#6bcf7f',
                '#4ade80'
            ],
            borderColor: '#fff',
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 15,
                    font: { size: 12 }
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.label + ': ' + context.parsed + ' попыт' + (context.parsed === 1 ? 'а' : (context.parsed > 4 || context.parsed === 0 ? 'ок' : 'и'));
                    }
                }
            }
        }
    }
});

// Weekly Scores Chart
const weeklyScoresCtx = document.getElementById('weeklyScoresChart').getContext('2d');
const weeklyData = {{ dashboard_data.weekly_scores|safe }};

if (weeklyData.length > 0) {
    const labels = weeklyData.map(w => w.week_start + ' - ' + w.week_end);
    const scores = weeklyData.map(w => w.average_score);
    const attempts = weeklyData.map(w => w.attempt_count);

    new Chart(weeklyScoresCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Средний балл (%)',
                data: scores,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    labels: { font: { size: 12 } }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            return 'Попыток: ' + attempts[context.dataIndex];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { callback: function(value) { return value + '%'; } }
                }
            }
        }
    });
} else {
    // Show "No data" message
    const noDataCtx = document.getElementById('weeklyScoresChart');
    noDataCtx.style.display = 'none';
    noDataCtx.parentElement.innerHTML += '<div class="empty-state"><p>Недостаточно данных для отображения графика</p></div>';
}