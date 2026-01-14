// static/admin.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    loadChartData();
    
    // Initialize search filters
    loadProdiFilter();
    
    // Set up event listeners
    document.getElementById('searchInput').addEventListener('keyup', function(e) {
        if (e.key === 'Enter') {
            searchData();
        }
    });
});

// ===== CHART FUNCTIONS =====

let categoryChart, prodiChart, semesterChart, gaugeChart;

async function loadChartData() {
    try {
        const response = await fetch('/api/chart-data');
        const data = await response.json();
        
        if (data.error) {
            console.error('Error loading chart data:', data.error);
            return;
        }
        
        // Update statistics
        document.getElementById('total-respondents').textContent = data.total_respondents;
        document.getElementById('total-surveys').textContent = data.total_surveys;
        
        // Create charts
        createCategoryChart(data);
        createProdiChart(data);
        createSemesterChart(data);
        createGaugeChart(data.overall_average);
        
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

function createCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    // Destroy existing chart if exists
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    // Define colors based on score
    const backgroundColors = data.averages.map(score => {
        if (score < 2.4) return '#FF5252'; // Red for low
        if (score < 3.8) return '#FFC107'; // Yellow for medium
        return '#4CAF50'; // Green for high
    });
    
    categoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.categories,
            datasets: [{
                label: 'Rata-rata Skor',
                data: data.averages,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.8', '1')),
                borderWidth: 1,
                borderRadius: 5,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Skor: ${context.raw.toFixed(2)}/5.0`;
                        }
                    }
                },
                datalabels: {
                    color: '#333',
                    font: {
                        weight: 'bold'
                    },
                    formatter: function(value) {
                        return value.toFixed(1);
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 5,
                    title: {
                        display: true,
                        text: 'Skor (1-5)'
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45
                    }
                }
            }
        }
    });
}

function createProdiChart(data) {
    const ctx = document.getElementById('prodiChart').getContext('2d');
    
    if (prodiChart) {
        prodiChart.destroy();
    }
    
    // Color palette
    const colors = [
        '#4361ee', '#3a0ca3', '#7209b7', '#f72585',
        '#4cc9f0', '#560bad', '#b5179e', '#4895ef',
        '#3f37c9', '#3a0ca3', '#4361ee'
    ];
    
    prodiChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.program_studies,
            datasets: [{
                data: data.program_counts,
                backgroundColor: colors,
                borderWidth: 1,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((context.raw / total) * 100);
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

function createSemesterChart(data) {
    const ctx = document.getElementById('semesterChart').getContext('2d');
    
    if (semesterChart) {
        semesterChart.destroy();
    }
    
    semesterChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.semester_labels,
            datasets: [{
                label: 'Jumlah Mahasiswa',
                data: data.semester_distribution,
                backgroundColor: 'rgba(67, 97, 238, 0.7)',
                borderColor: 'rgba(67, 97, 238, 1)',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Jumlah Mahasiswa'
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function createGaugeChart(score) {
    const ctx = document.getElementById('gaugeChart').getContext('2d');
    
    if (gaugeChart) {
        gaugeChart.destroy();
    }
    
    // Determine color based on score
    let gaugeColor;
    if (score < 2.4) gaugeColor = '#FF5252';
    else if (score < 3.8) gaugeColor = '#FFC107';
    else gaugeColor = '#4CAF50';
    
    // Update gauge value display
    document.getElementById('gaugeValue').textContent = score.toFixed(1);
    document.getElementById('gaugeValue').style.color = gaugeColor;
    
    gaugeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 5 - score],
                backgroundColor: [gaugeColor, '#f0f0f0'],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            cutout: '75%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        }
    });
}

// ===== SEARCH & FILTER FUNCTIONS =====

async function loadProdiFilter() {
    try {
        const response = await fetch('/api/search-data');
        const data = await response.json();
        
        const prodiFilter = document.getElementById('prodiFilter');
        data.prodi_list.forEach(prodi => {
            const option = document.createElement('option');
            option.value = prodi;
            option.textContent = prodi;
            prodiFilter.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading prodi filter:', error);
    }
}

async function searchData() {
    const searchTerm = document.getElementById('searchInput').value;
    const prodiFilter = document.getElementById('prodiFilter').value;
    const semesterFilter = document.getElementById('semesterFilter').value;
    
    // Show loading
    document.getElementById('searchResults').style.display = 'block';
    document.getElementById('resultsTable').innerHTML = '<div style="text-align: center; padding: 20px;"><span class="loading"></span> Mencari data...</div>';
    
    try {
        // Build query string
        let query = `/api/search-data?`;
        if (searchTerm) query += `q=${encodeURIComponent(searchTerm)}&`;
        if (prodiFilter) query += `prodi=${encodeURIComponent(prodiFilter)}&`;
        if (semesterFilter) query += `semester=${encodeURIComponent(semesterFilter)}`;
        
        const response = await fetch(query);
        const data = await response.json();
        
        if (data.error) {
            document.getElementById('resultsTable').innerHTML = `<div class="alert alert-error">❌ ${data.error}</div>`;
            return;
        }
        
        // Update results info
        document.getElementById('resultsInfo').innerHTML = 
            `<strong>${data.total || data.data.length}</strong> data ditemukan`;
        
        // Build results table
        if (data.data.length === 0) {
            document.getElementById('resultsTable').innerHTML = 
                '<div style="text-align: center; padding: 20px; color: #666;">Tidak ada data yang ditemukan</div>';
            return;
        }
        
        let tableHTML = `
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Nama</th>
                        <th>NIM</th>
                        <th>Prodi</th>
                        <th>Semester</th>
                        <th>Avg Score</th>
                        <th>Tanggal</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.data.forEach(item => {
            // --- PERBAIKAN LOGIKA SKOR DI SINI ---
            // Backend sudah mengirim nilai 1-5 (misal 4.25), jadi JANGAN DIBAGI LAGI.
            const scoreVal = parseFloat(item.total_score);
            
            // Logika Warna Badge (Skala 5)
            let scoreClass = 'badge-low';
            if (scoreVal >= 3.8) scoreClass = 'badge-high';      // Hijau
            else if (scoreVal >= 2.4) scoreClass = 'badge-medium'; // Kuning
            
            tableHTML += `
                <tr>
                    <td><strong>${item.nama}</strong></td>
                    <td>${item.nim}</td>
                    <td>${item.prodi}</td>
                    <td>Semester ${item.semester}</td>
                    <td><span class="score-badge ${scoreClass}">${scoreVal.toFixed(2)} / 5.0</span></td>
                    <td>${item.timestamp}</td>
                </tr>
            `;
        });
        
        tableHTML += `
                </tbody>
            </table>
        `;
        
        document.getElementById('resultsTable').innerHTML = tableHTML;
        
    } catch (error) {
        console.error('Error searching data:', error);
        document.getElementById('resultsTable').innerHTML = 
            '<div class="alert alert-error">❌ Error saat mencari data</div>';
    }
}

// ===== REFRESH CHART DATA =====
function refreshCharts() {
    // Show loading indicator on charts
    document.getElementById('categoryChart').style.opacity = '0.5';
    document.getElementById('prodiChart').style.opacity = '0.5';
    
    loadChartData();
    
    // Reset opacity after a delay
    setTimeout(() => {
        document.getElementById('categoryChart').style.opacity = '1';
        document.getElementById('prodiChart').style.opacity = '1';
    }, 1000);
}

// ===== EXPORT FILTERED DATA =====
function exportFilteredData(format) {
    const searchTerm = document.getElementById('searchInput').value;
    const prodiFilter = document.getElementById('prodiFilter').value;
    const semesterFilter = document.getElementById('semesterFilter').value;
    
    let url = `/export/${format}?`;
    if (searchTerm) url += `q=${encodeURIComponent(searchTerm)}&`;
    if (prodiFilter) url += `prodi=${encodeURIComponent(prodiFilter)}&`;
    if (semesterFilter) url += `semester=${encodeURIComponent(semesterFilter)}`;
    
    window.location.href = url;
}