document.addEventListener("DOMContentLoaded", () => {
    // Line Chart
    const lineChartCtx = document.getElementById("lineChartCanvas").getContext("2d");
    new Chart(lineChartCtx, {
        type: "line",
        data: {
            labels: ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"],
            datasets: [{
                label: "Payments",
                data: [5000, 10000, 15000, 20000, 25000, 30000],
                borderColor: "#4caf50",
                fill: false
            }]
        },
        options: {
            responsive: true
        }
    });

    // Pie Chart
    const pieChartCtx = document.getElementById("pieChartCanvas").getContext("2d");
    new Chart(pieChartCtx, {
        type: "pie",
        data: {
            labels: ["Payments Done", "Payments Pending"],
            datasets: [{
                data: [63, 25],
                backgroundColor: ["#4caf50", "#f44336"]
            }]
        },
        options: {
            responsive: true
        }
    });
});
