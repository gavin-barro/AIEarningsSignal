document.addEventListener('DOMContentLoaded', function () {
    const labels = JSON.parse(document.getElementById('labels-data').textContent);
    const managementData = JSON.parse(document.getElementById('management-scores-data').textContent);
    const qnaData = JSON.parse(document.getElementById('qna-scores-data').textContent);

    new Chart(document.getElementById('sentimentChart'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Management Sentiment',
                    data: managementData,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Q&A Sentiment',
                    data: qnaData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Sentiment Scores Over Time'
                }
            },
            scales: {
                y: {
                    suggestedMin: 0,
                    suggestedMax: 1
                }
            }
        }
    });
});
