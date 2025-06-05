document.addEventListener('DOMContentLoaded', function() {
    // Get data from the script tags
    let labels = JSON.parse(document.getElementById('labels-data').textContent);
    let managementScores = JSON.parse(document.getElementById('management-scores-data').textContent);
    let qnaScores = JSON.parse(document.getElementById('qna-scores-data').textContent);

    // Get the canvas context
    let ctx = document.getElementById('sentimentChart').getContext('2d');

    // Create the chart
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Management Sentiment Score',
                    data: managementScores,
                    borderColor: '#4CAF50', // Green
                    backgroundColor: 'rgba(76, 175, 80, 0.2)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Q&A Sentiment Score',
                    data: qnaScores,
                    borderColor: '#2196F3', // Blue
                    backgroundColor: 'rgba(33, 150, 243, 0.2)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    title: {
                        display: true,
                        text: 'Sentiment Score'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Quarter'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
});