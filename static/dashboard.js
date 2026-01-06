// ===== CHART FUNCTIONS =====
let categoryChart, prodiChart, semesterChart, gaugeChart, trendChart;

async function loadChartData() {
    try {
        console.log('Loading chart data...');
        
        // Cek apakah sudah login
        if (!document.getElementById('categoryChart')) {
            console.warn('Chart container not found, skipping chart load');
            return;
        }
        
        const response = await fetch('/api/chart-data');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            console.error('Error from API:', data.error);
            showError('Failed to load chart data: ' + data.error);
            return;
        }
        
        // Update statistics
        updateDashboardStats(data);
        
        // Create charts
        createCategoryChart(data);
        createProdiChart(data);
        createSemesterChart(data);
        createGaugeChart(data.overall_average || 0);
        createTrendChart(data);
        
        console.log('Charts loaded successfully');
        
    } catch (error) {
        console.error('Error loading chart data:', error);
        showError('Network error loading chart data: ' + error.message);
        
        // Fallback: create empty charts
        createEmptyCharts();
    }
}

function updateDashboardStats(data) {
    // Update elements only if they exist
    const elements = {
        'total-respondents': data.total_respondents || 0,
        'total-surveys': data.total_surveys || 0,
        'overallScore': data.overall_average ? data.overall_average.toFixed(1) : '0.0'
    };
    
    for (const [id, value] of Object.entries(elements)) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
}

function createEmptyCharts() {
    // Create empty charts when data fails to load
    const emptyData = {
        categories: ['Information', 'Communication', 'Content', 'Security', 'Problem Solving'],
        averages: [0, 0, 0, 0, 0],
        overall_average: 0,
        program_studies: [],
        program_counts: [],
        semester_labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4', 'Sem 5', 'Sem 6', 'Sem 7', 'Sem 8'],
        semester_distribution: [0, 0, 0, 0, 0, 0, 0, 0],
        total_respondents: 0,
        total_surveys: 0
    };
    
    createCategoryChart(emptyData);
    createProdiChart(emptyData);
    createSemesterChart(emptyData);
    createGaugeChart(0);
}