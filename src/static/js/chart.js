document.addEventListener('DOMContentLoaded', () => {
    let labels = JSON.parse(document.getElementById('labels-data').textContent);
    let scores = JSON.parse(document.getElementById('scores-data').textContent);

    let ctx = document.getElementById('sentimentChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Management Sentiment Score',
                data: scores,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1
                }
            }
        }
    });
});
