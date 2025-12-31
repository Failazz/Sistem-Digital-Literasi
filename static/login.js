/* static/login.js */

// Fungsi untuk validasi NIM secara real-time
function validateNIM() {
    const nimInput = document.getElementById('nim');
    const nimError = document.getElementById('nim-error');
    const nimValue = nimInput.value;
    
    // Hanya izinkan input angka
    nimInput.value = nimValue.replace(/[^0-9]/g, '');
    
    // Reset error message
    nimError.textContent = '';
    nimError.style.display = 'none';
    nimInput.classList.remove('error');
    
    // Validasi jika field tidak kosong
    if (nimValue.trim() !== '') {
        // Validasi hanya angka
        if (!/^\d+$/.test(nimValue)) {
            nimError.textContent = '❌ NIM hanya boleh berisi angka (0-9)';
            nimError.style.display = 'block';
            nimInput.classList.add('error');
            return false;
        }
        
        // Validasi panjang NIM
        if (nimValue.length < 8) {
            nimError.textContent = '❌ NIM harus minimal 8 digit';
            nimError.style.display = 'block';
            nimInput.classList.add('error');
            return false;
        }
        
        if (nimValue.length > 20) {
            nimError.textContent = '❌ NIM maksimal 20 digit';
            nimError.style.display = 'block';
            nimInput.classList.add('error');
            return false;
        }
        
        // Jika valid, tampilkan pesan sukses
        nimError.innerHTML = '✅ Format NIM valid';
        nimError.style.color = '#28a745';
        nimError.style.display = 'block';
        nimInput.classList.add('success');
        return true;
    }
    
    return false;
}

// Fungsi validasi nama
function validateNama() {
    const namaInput = document.getElementById('nama');
    const namaError = document.getElementById('nama-error');
    const namaValue = namaInput.value.trim();
    
    namaError.textContent = '';
    namaError.style.display = 'none';
    namaInput.classList.remove('error');
    
    if (namaValue !== '') {
        if (namaValue.length < 3) {
            namaError.textContent = '❌ Nama minimal 3 karakter';
            namaError.style.display = 'block';
            namaInput.classList.add('error');
            return false;
        }
        
        if (namaValue.length > 100) {
            namaError.textContent = '❌ Nama maksimal 100 karakter';
            namaError.style.display = 'block';
            namaInput.classList.add('error');
            return false;
        }
        
        namaError.innerHTML = '✅ Nama valid';
        namaError.style.color = '#28a745';
        namaError.style.display = 'block';
        namaInput.classList.add('success');
        return true;
    }
    
    return false;
}

// Fungsi validasi form lengkap sebelum submit
function validateForm() {
    const nimValid = validateNIM();
    const namaValid = validateNama();
    const prodiValid = document.getElementById('prodi').value !== '';
    const semesterValid = document.getElementById('semester').value !== '';
    
    // Tampilkan error untuk prodi jika kosong
    const prodiError = document.getElementById('prodi-error');
    if (!prodiValid) {
        prodiError.textContent = '❌ Pilih program studi';
        prodiError.style.display = 'block';
    } else {
        prodiError.style.display = 'none';
    }
    
    // Tampilkan error untuk semester jika kosong
    const semesterError = document.getElementById('semester-error');
    if (!semesterValid) {
        semesterError.textContent = '❌ Pilih semester';
        semesterError.style.display = 'block';
    } else {
        semesterError.style.display = 'none';
    }
    
    return nimValid && namaValid && prodiValid && semesterValid;
}

// Fungsi konfirmasi untuk menghapus semua data testing
function confirmDeleteAll() {
    const code = prompt(`⚠️  PERINGATAN: HAPUS SEMUA DATA ⚠️

Untuk mengonfirmasi penghapusan SEMUA data:
• ${total_respondents} Responden
• ${total_surveys} Data Survei

Ketik: DELETE_ALL_2024

Data yang dihapus TIDAK DAPAT dikembalikan!`);

    if (code === "DELETE_ALL_2024") {
        document.getElementById("confirmCode").value = code;
        return true;
    } else {
        alert("❌ Kode konfirmasi salah! Data tidak dihapus.");
        return false;
    }
}

// Auto-hide flash messages after 5 seconds
setTimeout(() => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.5s ease';
        setTimeout(() => alert.remove(), 500);
    });
}, 5000);

// Event Listeners (dijalankan setelah DOM load)
document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Validasi saat Submit
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                // Scroll ke error pertama
                const firstError = document.querySelector('.error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
                return false;
            }
            
            // UI Update saat submit sukses
            document.querySelector('.progress-fill').style.width = '100%';
            document.querySelector('.progress-text span:last-child').textContent = '100%';
            
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses...';
            
            return true;
        });
    }
    
    // 2. Event listeners input real-time
    const namaInput = document.getElementById('nama');
    if (namaInput) {
        namaInput.addEventListener('input', validateNama);
        namaInput.addEventListener('blur', validateNama);
    }

    const nimInput = document.getElementById('nim');
    if (nimInput) {
        nimInput.addEventListener('blur', validateNIM);
        // Auto-focus
        nimInput.focus();
    }
    
    // 3. Clear error saat dropdown berubah
    document.getElementById('prodi').addEventListener('change', function() {
        document.getElementById('prodi-error').style.display = 'none';
    });
    
    document.getElementById('semester').addEventListener('change', function() {
        document.getElementById('semester-error').style.display = 'none';
    });
    
    // 4. Animasi input focus
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'translateY(-2px)';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'translateY(0)';
        });
    });

    // 5. Hilangkan Flash Messages otomatis
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        });
    }, 5000);
});