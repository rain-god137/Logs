import axios from 'axios';
import Chart from 'chart.js/auto';

document.addEventListener('DOMContentLoaded', async function () {
    
    // Attaining graph data
    let dateLabels = null
    let completionRate = null;
    let tasksAssigned = null;
    let tasksCompleted = null;

    try {
        const response = await axios.get('/api/index/graph');
        completionRate = response.data.completionRate;
        dateLabels = response.data.dateLabel;
        tasksAssigned = response.data.tasksAssigned;
        tasksCompleted = response.data.tasksCompleted;
    
    } catch (error) {
        console.error('Can\'t fetch graph data', error)
    }


    // Line Graph
    const ctxO = document.getElementById('myChart').getContext('2d');
    const myChart = new Chart(ctxO, {
        type: 'line',
        data: {
            labels: dateLabels,
            datasets: [{
                label: 'Task Completion Rate',
                data: completionRate,
                fill: false,
                borderColor: '#805cbf',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales : {
                y: {beginAtZero: true},
            },
        }
    });

    // Bar graph
    const ctx = document.getElementById('myChartBar').getContext('2d');
    const barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dateLabels,
            datasets: [
                {
                    label: 'Assigned',
                    data: tasksAssigned,
                    barThickness: 30,
                    backgroundColor: 'rgba(52, 52, 52, 0.51)',
                    borderRadius: 8,
                    borderSkipped: false,
                    grouped: false,
                },

                {
                    label: 'Completed',
                    data: tasksCompleted,
                    barThickness: 18,
                    backgroundColor: '#b68bff',
                    borderRadius: 8,
                    borderSkipped: false,
                    grouped: false,
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true },
            },
            datasets: {
                bar: {
                    categoryPercentage: 0.8,
                    barPercentage: 1.0
                }
            }
        }
    });
    
})