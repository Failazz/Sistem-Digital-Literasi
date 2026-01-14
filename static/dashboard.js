// static/dashboard.js - VERSI LENGKAP

let categoryChart, prodiChart, semesterChart, gaugeChart, trendChart;

document.addEventListener('DOMContentLoaded', function() {
    loadChartData();
    loadTopPerformers();
    loadProdiFilter(); // Load filter dropdown
    
    // Aktifkan Search dengan Enter
    const searchInput = document.getElementById('searchInput');
    if(searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') searchData();
        });
    }
});

// ==================== 1. SEARCH & FILTER FUNCTIONS ====================
async function loadProdiFilter() {
    try {
        const response = await fetch('/api/search-data?limit=1'); // Fetch dummy to get prodi list
        const data = await response.json();
        
        const select = document.getElementById('prodiFilter');
        if(select && data.prodi_list) {
            select.innerHTML = '<option>All Programs</option>'; // Reset
            data.prodi_list.forEach(prodi => {
                const option = document.createElement('option');
                option.value = prodi;
                option.textContent = prodi;
                select.appendChild(option);
            });
        }
    } catch (e) {
        console.error('Error loading filters:', e);
    }
}

async function searchData() {
    const q = document.getElementById('searchInput').value;
    const prodi = document.getElementById('prodiFilter').value;
    const sem = document.getElementById('semesterFilter').value;
    const tableDiv = document.getElementById('resultsTable');
    
    // UI Loading
    tableDiv.innerHTML = '<div class="text-center p-3"><i class="fas fa-spinner fa-spin"></i> Mencari data...</div>';
    
    try {
        // Build URL parameters
        const params = new URLSearchParams();
        if(q) params.append('q', q);
        if(prodi && prodi !== 'All Programs') params.append('prodi', prodi);
        if(sem && sem !== 'All Semesters') params.append('semester', sem);
        
        const response = await fetch(`/api/search-data?${params.toString()}`);
        const result = await response.json();
        
        // Update Result Count
        const countSpan = document.getElementById('resultsCount');
        if(countSpan) countSpan.textContent = `${result.data.length} data ditemukan`;

        if (result.data.length === 0) {
            tableDiv.innerHTML = '<div class="text-center p-4 text-muted"><i class="fas fa-search fa-2x mb-2"></i><p>Tidak ada data ditemukan.</p></div>';
            return;
        }

        // Render Table
        let html = `
        <div class="results-scroll">
            <table class="table">
                <thead>
                    <tr>
                        <th>Nama</th>
                        <th>NIM</th>
                        <th>Prodi</th>
                        <th>Skor</th>
                    </tr>
                </thead>
                <tbody>`;
                
        result.data.forEach(item => {
            // --- PERBAIKAN DI SINI ---
            // Backend sudah mengirim nilai 1-5, jadi langsung ambil saja.
            let scoreScale = parseFloat(item.total_score).toFixed(2);
            
            let badgeClass = 'badge-low'; // Merah
            
            // Logika pewarnaan (Skala 5)
            if(scoreScale >= 3.8) badgeClass = 'badge-high'; // Hijau
            else if(scoreScale >= 2.4) badgeClass = 'badge-medium'; // Kuning
            
            html += `
            <tr>
                <td><strong>${item.nama}</strong></td>
                <td>${item.nim}</td>
                <td>${item.prodi} <small class="text-muted">(Sem ${item.semester})</small></td>
                <td><span class="score-badge ${badgeClass}">${scoreScale} / 5.0</span></td>
            </tr>`;
        });
        
        html += '</tbody></table></div>';
        tableDiv.innerHTML = html;
        
    } catch (e) {
        console.error(e);
        tableDiv.innerHTML = '<div class="alert alert-error">Gagal memuat data.</div>';
    }
}

// ==================== 2. CHART FUNCTIONS ====================

async function loadChartData() {
    try {
        const response = await fetch('/api/chart-data');
        const data = await response.json();
        
        if(data.error) return;

        // Update Stats Cards
        if(document.getElementById('total-respondents')) 
            document.getElementById('total-respondents').textContent = data.total_respondents;
        
        createCategoryChart(data);
        createProdiChart(data);
        createSemesterChart(data);
        createGaugeChart(data.overall_average || 0);
        createTrendChart(data);
        renderImprovementAreas(data.improvement_areas);
        
    } catch (error) {
        console.error('Chart Error:', error);
    }
}

function createCategoryChart(data) {
    const ctx = document.getElementById('categoryChart')?.getContext('2d');
    if(!ctx) return;
    if(categoryChart) categoryChart.destroy();

    categoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.categories,
            datasets: [{
                data: data.averages,
                backgroundColor: data.averages.map(s => s>=3.8?'#4caf50':(s>=2.4?'#ffc107':'#ff5252')),
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, max: 5 } }
        }
    });
}

function createProdiChart(data) {
    const ctx = document.getElementById('prodiChart')?.getContext('2d');
    if(!ctx) return;
    if(prodiChart) prodiChart.destroy();

    prodiChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.program_studies,
            datasets: [{
                data: data.program_counts,
                backgroundColor: ['#4361ee', '#3a0ca3', '#7209b7', '#f72585', '#4cc9f0'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            cutout: '65%'
        }
    });
}

function createSemesterChart(data) {
    const ctx = document.getElementById('semesterChart')?.getContext('2d');
    if(!ctx) return;
    if(semesterChart) semesterChart.destroy();

    semesterChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['1', '2', '3', '4', '5', '6', '7', '8'],
            datasets: [{
                data: data.semester_distribution,
                backgroundColor: '#4361ee',
                borderRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { display: false }, x: { grid: { display: false } } }
        }
    });
}

function createGaugeChart(score) {
    const ctx = document.getElementById('gaugeChart')?.getContext('2d');
    if(!ctx) return;
    if(gaugeChart) gaugeChart.destroy();

    // Update Text UI
    const scoreEl = document.getElementById('overallScore');
    const labelEl = document.getElementById('gaugeLevel');
    
    let color = '#4caf50';
    let text = 'Tinggi';
    
    if(score < 3.8) { color = '#ffc107'; text = 'Sedang'; }
    if(score < 2.4) { color = '#ff5252'; text = 'Rendah'; }

    if(scoreEl) { scoreEl.textContent = score.toFixed(2); scoreEl.style.color = color; }
    if(labelEl) { labelEl.textContent = text; labelEl.style.color = color; }

    gaugeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Score', 'Gap'],
            datasets: [{
                data: [score, 5 - score],
                backgroundColor: [color, '#eee'],
                borderWidth: 0,
                circumference: 180,
                rotation: 270,
                borderRadius: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '85%', // Lingkaran lebih tipis
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
    });
}

function createTrendChart(data) {
    const ctx = document.getElementById('trendChart')?.getContext('2d');
    if(!ctx) return;
    if(trendChart) trendChart.destroy();

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.trend_labels || [],
            datasets: [{
                label: 'Skor Harian',
                data: data.trend_data || [],
                borderColor: '#4361ee',
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(67, 97, 238, 0.1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { min: 1, max: 5 }, x: { grid: { display: false } } }
        }
    });
}

// ==================== 3. OTHER FUNCTIONS ====================

async function loadTopPerformers() {
    try {
        const response = await fetch('/api/top-performers');
        const data = await response.json();
        const container = document.getElementById('topPerformers');
        
        if(container && data.top_performers) {
            let html = '';
            data.top_performers.forEach((p, i) => {
                html += `
                <li>
                    <div class="performer-info">
                        <span class="rank">${i+1}</span>
                        <div><strong>${p.nama}</strong><br><small>${p.prodi}</small></div>
                    </div>
                    <span class="area-score">${(p.score/19).toFixed(1)}</span>
                </li>`;
            });
            container.innerHTML = html || '<p class="text-center p-3 text-muted">Belum ada data.</p>';
        }
    } catch(e) { console.error(e); }
}

function renderImprovementAreas(areas) {
    const container = document.getElementById('improvementAreas');
    if(!container) return;
    
    if(areas && areas.length) {
        let html = '';
        areas.forEach(area => {
            let width = (area.score / 5) * 100;
            let color = area.score < 3 ? 'bg-danger' : 'bg-warning';
            html += `
            <li>
                <div style="width:100%">
                    <div class="d-flex justify-content-between mb-1">
                        <span style="font-size:12px;font-weight:600">${area.topic}</span>
                        <span style="font-size:12px">${area.score}</span>
                    </div>
                    <div class="progress" style="height:6px;background:#eee;border-radius:3px">
                        <div class="progress-bar" style="width:${width}%;background:${area.score<3?'#ff5252':'#ffc107'}"></div>
                    </div>
                </div>
            </li>`;
        });
        container.innerHTML = html;
    } else {
        container.innerHTML = '<p class="text-center p-3 text-muted">Belum ada data analisis.</p>';
    }
}

// Fungsi Modal
function showDeleteModal() { document.getElementById('deleteModal').classList.add('active'); }
function closeDeleteModal() { document.getElementById('deleteModal').classList.remove('active'); }
function confirmDeleteAll() {
    return document.getElementById('confirmText').value === 'DELETE_ALL_2024';
}

// Fungsi untuk tombol Reset di Data Management
function resetFilters() {
    // Reset input text
    const searchInput = document.getElementById('searchInput');
    if(searchInput) searchInput.value = '';
    
    // Reset dropdowns ke index 0
    const prodi = document.getElementById('prodiFilter');
    if(prodi) prodi.selectedIndex = 0;
    
    const sem = document.getElementById('semesterFilter');
    if(sem) sem.selectedIndex = 0;
    
    // Jalankan pencarian ulang (kosong) untuk refresh tabel
    searchData();
}

// ==================== QUESTION MANAGEMENT ====================
// 1. Load Data ke Tabel
async function loadQuestions() {
    const tbody = document.getElementById('questionTableBody');
    if (!tbody) return; 
    
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Loading data...</td></tr>';

    try {
        const res = await fetch('/api/questions');
        const data = await res.json();
        
        let html = '';
        if(data.length === 0) {
            html = '<tr><td colspan="4" class="text-center">Belum ada pertanyaan.</td></tr>';
        } else {
            data.forEach(q => {
                // Escape tanda kutip agar aman
                const safeText = q.text.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                
                html += `
                <tr>
                    <td><span class="badge" style="background:#eee; color:#333; padding:5px;">${q.code}</span></td>
                    <td><strong>${q.category}</strong></td>
                    <td>${q.text}</td>
                    
                    <td style="white-space: nowrap; width: 1%;">
                        <div style="display: flex; gap: 5px; justify-content: flex-start;">
                            
                            <button onclick="editQuestion(${q.id}, '${q.code}', '${q.category}', '${safeText}')" 
                                    class="btn-sm" 
                                    title="Edit Soal"
                                    style="background:#ffc107; color:black; border:none; padding:6px 10px; cursor:pointer; border-radius:4px; display:flex; align-items:center; gap:5px;">
                                <i class="fas fa-edit"></i> <span>Edit</span>
                            </button>
                            
                            <button onclick="deleteQuestion(${q.id}, '${safeText}')" 
                                    class="btn-sm" 
                                    title="Hapus Soal"
                                    style="background:#dc3545; color:white; border:none; padding:6px 10px; cursor:pointer; border-radius:4px; display:flex; align-items:center; gap:5px;">
                                <i class="fas fa-trash"></i> <span>Hapus</span>
                            </button>

                        </div>
                    </td>
                </tr>`;
            });
        }
        tbody.innerHTML = html;
    } catch (e) {
        console.error(e);
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Gagal memuat data.</td></tr>';
    }
}

// 2. Fungsi Hapus Soal (BARU)
async function deleteQuestion(id, text) {
    if(!confirm(`⚠️ Apakah Anda yakin ingin menghapus pertanyaan ini?\n\n"${text}"\n\nTindakan ini tidak dapat dibatalkan.`)) {
        return;
    }

    try {
        const res = await fetch(`/api/questions/${id}`, {
            method: 'DELETE'
        });
        
        const result = await res.json();

        if(res.ok) {
            alert("✅ Pertanyaan berhasil dihapus!");
            loadQuestions(); // Refresh tabel otomatis
        } else {
            alert("❌ Gagal menghapus: " + (result.error || 'Terjadi kesalahan'));
        }
    } catch (e) {
        console.error(e);
        alert("❌ Error koneksi ke server.");
    }
}

// Modal Functions
function openQuestionModal() {
    document.getElementById('questionForm').reset();
    document.getElementById('qId').value = '';
    document.getElementById('modalTitle').innerText = 'Tambah Pertanyaan';
    document.getElementById('questionModal').classList.add('active');
}

function closeQuestionModal() {
    document.getElementById('questionModal').classList.remove('active');
}

function editQuestion(id, code, cat, text) {
    document.getElementById('qId').value = id;
    document.getElementById('qCode').value = code;
    document.getElementById('qCategory').value = cat;
    document.getElementById('qText').value = text;
    document.getElementById('modalTitle').innerText = 'Edit Pertanyaan';
    document.getElementById('questionModal').classList.add('active');
}

// Form Submit Handler
document.getElementById('questionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const id = document.getElementById('qId').value;
    const url = id ? `/api/questions/${id}` : '/api/questions';
    const method = id ? 'PUT' : 'POST';
    
    const payload = {
        code: document.getElementById('qCode').value,
        category: document.getElementById('qCategory').value,
        text: document.getElementById('qText').value
    };

    const res = await fetch(url, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });

    if(res.ok) {
        closeQuestionModal();
        loadQuestions();
        alert('Berhasil disimpan!');
    } else {
        alert('Gagal menyimpan.');
    }
});

// ==================== NAVIGATION LOGIC (PENTING) ====================
function showSection(sectionId) {
    // 1. Sembunyikan semua section (Hanya satu kali deklarasi)
    const sections = document.querySelectorAll('.dashboard-section');
    sections.forEach(section => {
        section.classList.remove('active');
        section.style.display = 'none';
    });

    // 2. Tampilkan section yang dipilih
    const targetId = sectionId + '-section';
    const targetSection = document.getElementById(targetId);
    
    if (targetSection) {
        targetSection.classList.add('active');
        targetSection.style.display = 'block';
        
        // --- LOGIC PER HALAMAN ---
        if (sectionId === 'data') {
            // Load data untuk halaman Data Management
            if(typeof loadProdiFilter === 'function') loadProdiFilter();
            if(typeof searchData === 'function') searchData();
        } 
        else if (sectionId === 'questions') {
            // Load data untuk halaman Kelola Soal (PENTING)
            if(typeof loadQuestions === 'function') {
                loadQuestions(); 
            } else {
                console.error("Fungsi loadQuestions belum ada!");
            }
        }
        else if (sectionId === 'charts' || sectionId === 'dashboard') {
            // Refresh chart jika diperlukan (Optional)
            if(typeof loadChartData === 'function') loadChartData();
        }
    }

    // 3. Update warna tombol Sidebar
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`.sidebar-menu a[href="#${sectionId}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}