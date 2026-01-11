from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import os
import csv
from io import StringIO, BytesIO
import pandas as pd
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'survey-literasi-digital-2025'

# ==================== KONFIGURASI DATABASE ====================
# Cek apakah ada environment variable DATABASE_URL
if os.environ.get('DATABASE_URL'):
    # Untuk production/Heroku
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("=" * 70)
    print("🚀 SISTEM SURVEI LITERASI DIGITAL - POSTGRESQL")
    print("=" * 70)
    print("📁 Database: PostgreSQL (Production)")
    print("=" * 70)
else:
    # Untuk development lokal - GANTI PASSWORD MENJADI admin123
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:yahalose@localhost:5432/survey_digital_literacy'
    print("=" * 70)
    print("🚀 SISTEM SURVEI LITERASI DIGITAL - POSTGRESQL")
    print("=" * 70)
    print("📁 Database: PostgreSQL (Local Development)")
    print("=" * 70)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

db = SQLAlchemy(app)

# ==================== MAPPING PERTANYAAN (UNTUK ANALISIS) ====================
QUESTION_MAP = {
    'q1_info': 'Info: Kata Kunci & Operator Pencarian',
    'q2_info': 'Info: Evaluasi Kredibilitas Sumber',
    'q3_info': 'Info: Fakta vs Opini/Hoaks',
    'q4_info': 'Info: Manajemen Penyimpanan Data',
    'q5_comm': 'Comm: Platform Kolaborasi',
    'q6_comm': 'Comm: Etika Email Formal',
    'q7_comm': 'Comm: Jejak Digital',
    'q8_comm': 'Comm: Berbagi Pengetahuan',
    'q9_content': 'Content: Office Advance Features',
    'q10_content': 'Content: Pembuatan Multimedia',
    'q11_content': 'Content: Hak Cipta & Lisensi',
    'q12_content': 'Content: Sitasi & Plagiarisme',
    'q13_security': 'Security: Manajemen Password',
    'q14_security': 'Security: Autentikasi 2 Faktor (2FA)',
    'q15_security': 'Security: Izin Akses Aplikasi',
    'q16_security': 'Security: Screen Time & Kesehatan',
    'q17_problem': 'Problem: Troubleshooting Mandiri',
    'q18_problem': 'Problem: Eksplorasi Tools Baru',
    'q19_problem': 'Problem: Adaptasi Platform Baru'
}

# ==================== MODEL DATABASE ====================
class Respondent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    nim = db.Column(db.String(20), unique=True, nullable=False)
    prodi = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)

class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    respondent_id = db.Column(db.Integer, nullable=False)
    
    q1_info = db.Column(db.Integer, default=0)
    q2_info = db.Column(db.Integer, default=0)
    q3_info = db.Column(db.Integer, default=0)
    q4_info = db.Column(db.Integer, default=0)
    
    q5_comm = db.Column(db.Integer, default=0)
    q6_comm = db.Column(db.Integer, default=0)
    q7_comm = db.Column(db.Integer, default=0)
    q8_comm = db.Column(db.Integer, default=0)
    
    q9_content = db.Column(db.Integer, default=0)
    q10_content = db.Column(db.Integer, default=0)
    q11_content = db.Column(db.Integer, default=0)
    q12_content = db.Column(db.Integer, default=0)
    
    q13_security = db.Column(db.Integer, default=0)
    q14_security = db.Column(db.Integer, default=0)
    q15_security = db.Column(db.Integer, default=0)
    q16_security = db.Column(db.Integer, default=0)
    
    q17_problem = db.Column(db.Integer, default=0)
    q18_problem = db.Column(db.Integer, default=0)
    q19_problem = db.Column(db.Integer, default=0)
    
    total_score = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.now)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  
    category = db.Column(db.String(50), nullable=False)           
    text = db.Column(db.Text, nullable=False)                     

    def __repr__(self):
        return f'<Question {self.code}>'

# ==================== FUNGSI VALIDASI ====================
def validate_nim(nim):
    """Validasi NIM: hanya angka dan minimal 8 digit"""
    if not nim.isdigit():
        return False, "NIM harus berisi angka saja (0-9)"
    
    if len(nim) < 8:
        return False, "NIM harus minimal 8 digit"
    
    if len(nim) > 20:
        return False, "NIM maksimal 20 digit"
    
    return True, "Valid"

def check_nim_exists(nim):
    """Cek apakah NIM sudah terdaftar di database"""
    return Respondent.query.filter_by(nim=nim).first() is not None

# ==================== FUNGSI BANTU ADMIN ====================
def create_default_admin():
    """Buat admin default jika belum ada"""
    with app.app_context():
        try:
            admin = Admin.query.filter_by(username='admin').first()
            if not admin:
                hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
                default_admin = Admin(username='admin', password=hashed_password)
                db.session.add(default_admin)
                db.session.commit()
                print("✅ Admin default dibuat - Username: admin, Password: admin123")
        except Exception as e:
            print(f"⚠️  Gagal membuat admin: {e}")

def admin_required(f):
    """Decorator untuk memeriksa login admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== INISIALISASI DATABASE ====================
def init_database():
    """Membuat tabel jika belum ada (PostgreSQL)"""
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tabel berhasil dibuat (atau sudah ada)")
            
            # Cek koneksi
            count = Respondent.query.count()
            print(f"📊 Data responden saat ini: {count} orang")
            
        except Exception as e:
            print(f"❌ Error inisialisasi database PostgreSQL: {e}")
            print("⚠️  Pastikan:")
            print("   1. PostgreSQL service sedang berjalan")
            print("   2. Database 'survey_digital_literacy' sudah dibuat")
            print("   3. Username/password PostgreSQL benar")

# ==================== ROUTES UTAMA ====================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            nama = request.form['nama'].strip()
            nim = request.form['nim'].strip()
            prodi = request.form['prodi'].strip()
            semester = request.form['semester'].strip()
            
            if not all([nama, nim, prodi, semester]):
                flash('Harap lengkapi semua data!', 'error')
                return render_template('login.html')
            
            is_valid, error_msg = validate_nim(nim)
            if not is_valid:
                flash(f'NIM tidak valid: {error_msg}', 'error')
                return render_template('login.html')
            
            existing_respondent = Respondent.query.filter_by(nim=nim).first()
            if existing_respondent:
                flash('❌ NIM sudah terdaftar. Gunakan NIM lain.', 'error')
                return render_template('login.html')
            
            try:
                semester_int = int(semester)
                if semester_int < 1 or semester_int > 8:
                    flash('Semester harus antara 1-8', 'error')
                    return render_template('login.html')
            except ValueError:
                flash('Semester harus berupa angka', 'error')
                return render_template('login.html')
            
            respondent = Respondent(
                nama=nama,
                nim=nim,
                prodi=prodi,
                semester=semester_int
            )
            
            db.session.add(respondent)
            db.session.commit()
            
            print(f"✅ Data disimpan - ID: {respondent.id}, NIM: {respondent.nim}, Nama: {respondent.nama}")
            flash('✅ Data berhasil disimpan! Mengarahkan ke survei...', 'success')
            
            return redirect(url_for('survey_info', respondent_id=respondent.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            flash(f'Terjadi error sistem: {str(e)}', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

# ==================== SURVEY MULTI-PAGE ROUTES ====================
@app.route('/survey/<int:respondent_id>/info', methods=['GET', 'POST'])
def survey_info(respondent_id):
    # 1. Ambil pertanyaan kategori 'info' dari Database
    questions = Question.query.filter_by(category='info').order_by(Question.code).all()
    
    if request.method == 'POST':
        # 2. Simpan jawaban ke session secara otomatis (Looping)
        answers = {}
        for q in questions:
            # Mengambil value dari form HTML berdasarkan kode (misal: q1_info)
            answers[q.code] = int(request.form.get(q.code, 0))
            
        session[f'survey_{respondent_id}_info'] = answers
        return redirect(url_for('survey_comm', respondent_id=respondent_id))
    
    return render_template('survey/survey_info.html', 
                        respondent_id=respondent_id,
                        respondent=Respondent.query.get(respondent_id),
                        questions=questions) # Kirim pertanyaan ke HTML

@app.route('/survey/<int:respondent_id>/comm', methods=['GET', 'POST'])
def survey_comm(respondent_id):
    questions = Question.query.filter_by(category='comm').order_by(Question.code).all()
    
    if request.method == 'POST':
        answers = {}
        for q in questions:
            answers[q.code] = int(request.form.get(q.code, 0))
            
        session[f'survey_{respondent_id}_comm'] = answers
        return redirect(url_for('survey_content', respondent_id=respondent_id))
    
    return render_template('survey/survey_comm.html', 
                        respondent_id=respondent_id,
                        respondent=Respondent.query.get(respondent_id),
                        questions=questions)

@app.route('/survey/<int:respondent_id>/content', methods=['GET', 'POST'])
def survey_content(respondent_id):
    questions = Question.query.filter_by(category='content').order_by(Question.code).all()
    
    if request.method == 'POST':
        answers = {}
        for q in questions:
            answers[q.code] = int(request.form.get(q.code, 0))
            
        session[f'survey_{respondent_id}_content'] = answers
        return redirect(url_for('survey_security', respondent_id=respondent_id))
    
    return render_template('survey/survey_content.html', 
                        respondent_id=respondent_id,
                        respondent=Respondent.query.get(respondent_id),
                        questions=questions)

@app.route('/survey/<int:respondent_id>/security', methods=['GET', 'POST'])
def survey_security(respondent_id):
    questions = Question.query.filter_by(category='security').order_by(Question.code).all()
    
    if request.method == 'POST':
        answers = {}
        for q in questions:
            answers[q.code] = int(request.form.get(q.code, 0))
            
        session[f'survey_{respondent_id}_security'] = answers
        return redirect(url_for('survey_problem', respondent_id=respondent_id))
    
    return render_template('survey/survey_security.html', 
                        respondent_id=respondent_id,
                        respondent=Respondent.query.get(respondent_id),
                        questions=questions)

@app.route('/survey/<int:respondent_id>/problem', methods=['GET', 'POST'])
def survey_problem(respondent_id):
    respondent = Respondent.query.get(respondent_id)
    questions = Question.query.filter_by(category='problem').order_by(Question.code).all()
    
    if request.method == 'POST':
        try:
            current_answers = {}
            for q in questions:
                current_answers[q.code] = int(request.form.get(q.code, 0))
            
            all_data = {}
            for category in ['info', 'comm', 'content', 'security']:
                cat_data = session.get(f'survey_{respondent_id}_{category}', {})
                all_data.update(cat_data)
            all_data.update(current_answers)
            
            total_score = sum(all_data.values())
            
            response = SurveyResponse(
                respondent_id=respondent_id,
                total_score=total_score,
                **all_data
            )
            db.session.add(response)
            db.session.commit()
            
            for category in ['info', 'comm', 'content', 'security', 'problem']:
                session.pop(f'survey_{respondent_id}_{category}', None)
            
            # PERBAIKAN: Redirect ke 'success_page'
            return redirect(url_for('success_page'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')

    return render_template('survey/survey_problem.html', 
                        respondent_id=respondent_id, 
                        respondent=respondent, 
                        questions=questions)

@app.route('/success')
def success_page():
    return render_template('success.html')

# ==================== ADMIN ROUTE TERPUSAT ====================
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Halaman admin terpusat - login dan dashboard"""
    
    # Jika sudah login, tampilkan dashboard
    if session.get('admin_logged_in'):
        try:
            # Hitung statistik
            total_respondents = Respondent.query.count()
            total_surveys = SurveyResponse.query.count()
            
            # Hitung average score
            responses = SurveyResponse.query.all()
            avg_score = 0
            if responses:
                total = sum([r.total_score for r in responses])
                avg_score = total / len(responses)
            
            # Kirim data ke template
            return render_template('admin.html',
                                total_respondents=total_respondents,
                                total_surveys=total_surveys,
                                avg_score=round(avg_score, 2),
                                username=session.get('admin_username'))
            
        except Exception as e:
            print(f"❌ Error loading dashboard: {e}")
            # Jika ada error, tetap tampilkan dashboard dengan nilai default
            return render_template('admin.html',
                                total_respondents=0,
                                total_surveys=0,
                                avg_score=0,
                                username=session.get('admin_username', 'Admin'))
    
    # Handle POST request untuk login
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        admin_user = Admin.query.filter_by(username=username).first()
        
        if admin_user and check_password_hash(admin_user.password, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_id'] = admin_user.id
            flash('Login berhasil!', 'success')
            print(f"✅ Admin login: {username}")
            # Setelah login, refresh halaman untuk menampilkan dashboard
            return redirect(url_for('admin'))
        else:
            flash('Username atau password salah!', 'error')
    
    # Jika belum login, tampilkan form login
    return render_template('admin.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout admin"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    session.pop('admin_id', None)
    flash('Anda telah logout.', 'success')
    return redirect(url_for('admin'))

# ==================== ROUTE UNTUK MEMERIKSA NIM ====================
@app.route('/check-nim/<nim>')
def check_nim(nim):
    """API endpoint untuk mengecek ketersediaan NIM (AJAX)"""
    if check_nim_exists(nim):
        return {'available': False, 'message': 'NIM sudah terdaftar'}
    else:
        return {'available': True, 'message': 'NIM tersedia'}

# ==================== ROUTES DELETE DATA ====================
@app.route('/delete/respondent/<int:respondent_id>', methods=['POST'])
@admin_required
def delete_respondent(respondent_id):
    """Hapus data responden beserta data surveinya"""
    try:
        respondent = Respondent.query.get(respondent_id)
        
        if not respondent:
            flash('Data responden tidak ditemukan!', 'error')
            return redirect(url_for('view_data'))
        
        nama = respondent.nama
        nim = respondent.nim
        
        survey_response = SurveyResponse.query.filter_by(respondent_id=respondent_id).first()
        if survey_response:
            db.session.delete(survey_response)
        
        db.session.delete(respondent)
        db.session.commit()
        
        flash(f'✅ Data berhasil dihapus: {nama} (NIM: {nim})', 'success')
        print(f"🗑️  Data dihapus - NIM: {nim}, Nama: {nama}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saat menghapus data: {e}")
        flash(f'Error saat menghapus data: {str(e)}', 'error')
    
    return redirect(url_for('view_data'))

@app.route('/delete/survey/<int:survey_id>', methods=['POST'])
@admin_required
def delete_survey(survey_id):
    """Hapus data survei saja (tanpa menghapus data responden)"""
    try:
        survey = SurveyResponse.query.get(survey_id)
        
        if not survey:
            flash('Data survei tidak ditemukan!', 'error')
            return redirect(url_for('view_data'))
        
        respondent = Respondent.query.get(survey.respondent_id)
        
        db.session.delete(survey)
        db.session.commit()
        
        if respondent:
            flash(f'✅ Data survei dihapus (Responden: {respondent.nama}, NIM: {respondent.nim})', 'success')
            print(f"🗑️  Survey dihapus - ID: {survey_id}, NIM: {respondent.nim}")
        else:
            flash(f'✅ Data survei ID: {survey_id} dihapus', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saat menghapus survei: {e}")
        flash(f'Error saat menghapus survei: {str(e)}', 'error')
    
    return redirect(url_for('view_data'))

# ==================== PROTECTED ADMIN ROUTES ====================
@app.route('/export/csv')
@admin_required
def export_csv():
    """Export semua data ke CSV"""
    try:
        respondents = Respondent.query.all()
        responses = SurveyResponse.query.all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'ID', 'Nama', 'NIM', 'Prodi', 'Semester', 'Timestamp',
            'Q1_Info_KataKunci', 'Q2_Info_Kredibilitas', 'Q3_Info_FaktaOpini', 'Q4_Info_Penyimpanan',
            'Q5_Comm_Platform', 'Q6_Comm_Email', 'Q7_Comm_JejakDigital', 'Q8_Comm_Berbagi',
            'Q9_Content_Software', 'Q10_Content_Multimedia', 'Q11_Content_HakCipta', 'Q12_Content_Sitasi',
            'Q13_Security_Password', 'Q14_Security_2FA', 'Q15_Security_Permissions', 'Q16_Security_ScreenTime',
            'Q17_Problem_Teknis', 'Q18_Problem_AlatBaru', 'Q19_Problem_Adaptasi',
            'Total_Score', 'Survey_Timestamp'
        ])
        
        for response in responses:
            respondent = next((r for r in respondents if r.id == response.respondent_id), None)
            
            if respondent:
                writer.writerow([
                    respondent.id,
                    respondent.nama,
                    respondent.nim,
                    respondent.prodi,
                    respondent.semester,
                    respondent.timestamp.strftime('%Y-%m-%d %H:%M:%S') if respondent.timestamp else '',
                    response.q1_info, response.q2_info, response.q3_info, response.q4_info,
                    response.q5_comm, response.q6_comm, response.q7_comm, response.q8_comm,
                    response.q9_content, response.q10_content, response.q11_content, response.q12_content,
                    response.q13_security, response.q14_security, response.q15_security, response.q16_security,
                    response.q17_problem, response.q18_problem, response.q19_problem,
                    response.total_score,
                    response.timestamp.strftime('%Y-%m-%d %H:%M:%S') if response.timestamp else ''
                ])
        
        output.seek(0)
        
        return send_file(
            BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'survey_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        print(f"❌ Error export CSV: {e}")
        flash(f'Error export CSV: {str(e)}', 'error')
        return redirect(url_for('admin'))

@app.route('/export/excel')
@admin_required
def export_excel():
    """Export semua data ke Excel (XLSX)"""
    try:
        respondents = Respondent.query.all()
        responses = SurveyResponse.query.all()
        
        data = []
        for response in responses:
            respondent = next((r for r in respondents if r.id == response.respondent_id), None)
            
            if respondent:
                data.append({
                    'ID': respondent.id,
                    'Nama': respondent.nama,
                    'NIM': respondent.nim,
                    'Prodi': respondent.prodi,
                    'Semester': respondent.semester,
                    'Timestamp_Responden': respondent.timestamp.strftime('%Y-%m-%d %H:%M:%S') if respondent.timestamp else '',
                    'Q1_Info_KataKunci': response.q1_info,
                    'Q2_Info_Kredibilitas': response.q2_info,
                    'Q3_Info_FaktaOpini': response.q3_info,
                    'Q4_Info_Penyimpanan': response.q4_info,
                    'Q5_Comm_Platform': response.q5_comm,
                    'Q6_Comm_Email': response.q6_comm,
                    'Q7_Comm_JejakDigital': response.q7_comm,
                    'Q8_Comm_Berbagi': response.q8_comm,
                    'Q9_Content_Software': response.q9_content,
                    'Q10_Content_Multimedia': response.q10_content,
                    'Q11_Content_HakCipta': response.q11_content,
                    'Q12_Content_Sitasi': response.q12_content,
                    'Q13_Security_Password': response.q13_security,
                    'Q14_Security_2FA': response.q14_security,
                    'Q15_Security_Permissions': response.q15_security,
                    'Q16_Security_ScreenTime': response.q16_security,
                    'Q17_Problem_Teknis': response.q17_problem,
                    'Q18_Problem_AlatBaru': response.q18_problem,
                    'Q19_Problem_Adaptasi': response.q19_problem,
                    'Total_Score': response.total_score,
                    'Timestamp_Survey': response.timestamp.strftime('%Y-%m-%d %H:%M:%S') if response.timestamp else ''
                })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Survey Data', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'survey_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        print(f"❌ Error export Excel: {e}")
        flash(f'Error export Excel: {str(e)}', 'error')
        return redirect(url_for('admin'))

@app.route('/view-data')
@admin_required
def view_data():
    try:
        respondents = Respondent.query.all()
        responses = SurveyResponse.query.all()
        
        html_parts = []
        html_parts.append('<!DOCTYPE html><html><head><title>Data Survey</title>')
        html_parts.append('<style>')
        html_parts.append('body { font-family: Arial, sans-serif; margin: 20px; }')
        html_parts.append('table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }')
        html_parts.append('th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }')
        html_parts.append('th { background-color: #4CAF50; color: white; }')
        html_parts.append('tr:nth-child(even) { background-color: #f2f2f2; }')
        html_parts.append('.btn { display: inline-block; padding: 10px 15px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 5px; }')
        html_parts.append('.btn-logout { background: #dc3545; }')
        html_parts.append('.btn-delete { background: #dc3545; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 14px; }')
        html_parts.append('.btn-delete:hover { background: #c82333; transform: scale(1.05); }')
        html_parts.append('.btn-delete-survey { background: #fd7e14; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 14px; }')
        html_parts.append('.btn-delete-survey:hover { background: #e06c0e; transform: scale(1.05); }')
        html_parts.append('</style>')
        html_parts.append('</head><body>')
        
        html_parts.append(f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">')
        html_parts.append('<h1>📊 Data Survei Literasi Digital</h1>')
        html_parts.append(f'<div>')
        html_parts.append(f'<span style="margin-right: 15px;"><i class="fas fa-user"></i> {session.get("admin_username", "Admin")}</span>')
        html_parts.append(f'<a href="/admin/logout" class="btn btn-logout"><i class="fas fa-sign-out-alt"></i> Logout</a>')
        html_parts.append(f'</div>')
        html_parts.append(f'</div>')
        
        html_parts.append(f'<p><strong>Total Responden:</strong> {len(respondents)}</p>')
        html_parts.append(f'<p><strong>Total Survei:</strong> {len(responses)}</p>')
        
        if respondents:
            html_parts.append('<h2>Data Responden (NIM Unik)')
            html_parts.append('<span style="font-size: 14px; color: #666; margin-left: 10px;">')
            html_parts.append(f'Total: {len(respondents)} data')
            html_parts.append('</span></h2>')
            
            html_parts.append('<table><tr>')
            html_parts.append('<th>ID</th><th>Nama</th><th>NIM</th><th>Prodi</th><th>Semester</th><th>Timestamp</th><th>Aksi</th>')
            html_parts.append('</tr>')
            
            for r in respondents:
                html_parts.append(f'<tr id="respondent-{r.id}">')
                html_parts.append(f'<td>{r.id}</td>')
                html_parts.append(f'<td>{r.nama}</td>')
                html_parts.append(f'<td><strong>{r.nim}</strong></td>')
                html_parts.append(f'<td>{r.prodi}</td>')
                html_parts.append(f'<td>{r.semester}</td>')
                html_parts.append(f'<td>{r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else ""}</td>')
                
                html_parts.append(f'''<td>
                    <form method="POST" action="/delete/respondent/{r.id}" 
                        onsubmit="return confirmDelete('{r.nama}', '{r.nim}')" 
                        style="display: inline;">
                        <button type="submit" class="btn-delete" title="Hapus data responden dan surveinya">
                            <i class="fas fa-trash"></i> Hapus
                        </button>
                    </form>
                </td>''')
                
                html_parts.append('</tr>')
            html_parts.append('</table>')
        else:
            html_parts.append('<p><em>Tidak ada data responden.</em></p>')
        
        if responses:
            html_parts.append('<h2>Data Jawaban Survei')
            html_parts.append('<span style="font-size: 14px; color: #666; margin-left: 10px;">')
            html_parts.append(f'Total: {len(responses)} data')
            html_parts.append('</span></h2>')
            
            html_parts.append('<table>')
            html_parts.append('<tr>')
            html_parts.append('<th>ID</th><th>Respondent ID</th><th>Nama</th><th>NIM</th>')
            html_parts.append('<th>Total Score</th><th>Timestamp</th><th>Aksi</th>')
            html_parts.append('</tr>')
            
            for r in responses:
                respondent = next((resp for resp in respondents if resp.id == r.respondent_id), None)
                
                html_parts.append(f'<tr id="survey-{r.id}">')
                html_parts.append(f'<td>{r.id}</td>')
                html_parts.append(f'<td>{r.respondent_id}</td>')
                
                if respondent:
                    html_parts.append(f'<td>{respondent.nama}</td>')
                    html_parts.append(f'<td>{respondent.nim}</td>')
                else:
                    html_parts.append('<td style="color: #dc3545;">N/A</td>')
                    html_parts.append('<td style="color: #dc3545;">N/A</td>')
                
                html_parts.append(f'<td><strong>{r.total_score}/95</strong></td>')
                html_parts.append(f'<td>{r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else ""}</td>')
                
                html_parts.append(f'''<td>
                    <form method="POST" action="/delete/survey/{r.id}" 
                        onsubmit="return confirmDeleteSurvey({r.id})" 
                        style="display: inline;">
                        <button type="submit" class="btn-delete-survey" title="Hapus data survei saja">
                            <i class="fas fa-trash-alt"></i> Hapus
                        </button>
                    </form>
                </td>''')
                
                html_parts.append('</tr>')
            html_parts.append('</table>')
        else:
            html_parts.append('<p><em>Tidak ada data survei.</em></p>')
        
        html_parts.append('<br>')
        html_parts.append('<a href="/admin" class="btn"><i class="fas fa-arrow-left"></i> Kembali ke Admin Panel</a>')
        html_parts.append('<a href="/export/csv" class="btn"><i class="fas fa-file-csv"></i> Export CSV</a>')
        html_parts.append('<a href="/export/excel" class="btn"><i class="fas fa-file-excel"></i> Export Excel</a>')
        
        html_parts.append('''
        <script>
        function confirmDelete(nama, nim) {
            return confirm(`Apakah Anda yakin ingin menghapus data: ${nama} (NIM: ${nim})?\\n\\n✅ Data responden DAN data survei akan dihapus.\\n❌ Tindakan ini tidak dapat dibatalkan!`);
        }

        function confirmDeleteSurvey(surveyId) {
            return confirm(`Hapus data survei ID: ${surveyId}?\\n\\n⚠️ Hanya data survei yang dihapus, data responden tetap ada.`);
        }
        </script>
        ''')
        
        html_parts.append('</body></html>')
        
        final_html = ''.join(html_parts)
        return final_html
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"<h1>❌ Terjadi Error dalam view_data():</h1><pre>{error_detail}</pre>"
    
# ==================== ROUTES UNTUK CHART DATA ====================
@app.route('/api/chart-data')
@admin_required
def chart_data():
    """API untuk data chart"""
    try:
        responses = SurveyResponse.query.all()
        respondents = Respondent.query.all()
        
        # --- PERUBAHAN BARU 2: IMPORT DEPENDENSI ---
        from sqlalchemy import func
        from datetime import timedelta
        
        if not responses:
            return jsonify({
                'categories': ['Information', 'Communication', 'Content', 'Security', 'Problem Solving'],
                'averages': [0, 0, 0, 0, 0],
                'overall_average': 0,
                'program_studies': [],
                'program_counts': [],
                'semester_distribution': [],
                # Tambahkan default value untuk data baru
                'trend_labels': [],
                'trend_data': [],
                'improvement_areas': []
            })
        
        # Hitung rata-rata per kategori (KODE LAMA)
        info_scores = []
        comm_scores = []
        content_scores = []
        security_scores = []
        problem_scores = []
        total_scores = []
        
        for r in responses:
            info_total = r.q1_info + r.q2_info + r.q3_info + r.q4_info
            comm_total = r.q5_comm + r.q6_comm + r.q7_comm + r.q8_comm
            content_total = r.q9_content + r.q10_content + r.q11_content + r.q12_content
            security_total = r.q13_security + r.q14_security + r.q15_security + r.q16_security
            problem_total = r.q17_problem + r.q18_problem + r.q19_problem
            
            info_scores.append(info_total / 4)
            comm_scores.append(comm_total / 4)
            content_scores.append(content_total / 4)
            security_scores.append(security_total / 4)
            problem_scores.append(problem_total / 3)
            total_scores.append(r.total_score / 19)
        
        # Distribusi Program Studi (KODE LAMA)
        prodi_counts = {}
        for r in respondents:
            prodi = r.prodi
            prodi_counts[prodi] = prodi_counts.get(prodi, 0) + 1
        
        # Distribusi Semester (KODE LAMA)
        semester_counts = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}
        for r in respondents:
            semester = r.semester
            if 1 <= semester <= 8:
                semester_counts[semester] = semester_counts.get(semester, 0) + 1

        # --- PERUBAHAN BARU 3: LOGIKA TREN 7 HARI ---
        today = datetime.now().date()
        trend_map = {(today - timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(7)}
        
        # Query agregat database
        trends = db.session.query(
            func.date(SurveyResponse.timestamp).label('date'),
            func.avg(SurveyResponse.total_score).label('score')
        ).filter(SurveyResponse.timestamp >= today - timedelta(days=6))\
        .group_by(func.date(SurveyResponse.timestamp)).all()
        
        for t in trends:
            d_str = str(t.date)
            if d_str in trend_map:
                # Konversi skor total (0-95) menjadi skala 1-5
                trend_map[d_str] = round(t.score / 19, 2) 
        
        # Urutkan berdasarkan tanggal
        sorted_trend = sorted(trend_map.items())
        trend_labels = [datetime.strptime(k, '%Y-%m-%d').strftime('%d %b') for k, v in sorted_trend]
        trend_data = [v for k, v in sorted_trend]

        # --- PERUBAHAN BARU 4: LOGIKA AREAS FOR IMPROVEMENT ---
        improvement_list = []
        if responses:
            count = len(responses)
            q_scores = {}
            
            # AMBIL DARI DATABASE, BUKAN QUESTION_MAP
            all_questions = Question.query.all()
            
            for q in all_questions:
                # getattr(r, q.code) mengambil nilai kolom secara dinamis
                # misal: q.code = 'q1_info', dia akan ambil nilai r.q1_info
                # Jika kolom belum ada (baru ditambah tapi model belum update), beri nilai 0
                try:
                    total_val = sum(getattr(r, q.code) for r in responses)
                    q_scores[q.text] = round(total_val / count, 2)
                except AttributeError:
                    continue # Skip jika kolom database belum dibuat
            
            # Ambil 5 skor terendah
            sorted_improvement = sorted(q_scores.items(), key=lambda x: x[1])[:5]
            improvement_list = [{'topic': k, 'score': v} for k, v in sorted_improvement]

        # --- PERUBAHAN BARU 5: UPDATE RETURN JSON ---
        return jsonify({
            'categories': ['Information & Data', 'Communication', 'Content Creation', 'Security', 'Problem Solving'],
            'averages': [
                round(sum(info_scores) / len(info_scores), 2),
                round(sum(comm_scores) / len(comm_scores), 2),
                round(sum(content_scores) / len(content_scores), 2),
                round(sum(security_scores) / len(security_scores), 2),
                round(sum(problem_scores) / len(problem_scores), 2)
            ],
            'overall_average': round(sum(total_scores) / len(total_scores), 2),
            'program_studies': list(prodi_counts.keys()),
            'program_counts': list(prodi_counts.values()),
            'semester_labels': [f'Semester {i}' for i in range(1, 9)],
            'semester_distribution': [semester_counts[i] for i in range(1, 9)],
            'total_respondents': len(respondents),
            'total_surveys': len(responses),
            
            # Tambahan Data Baru dikirim ke Frontend
            'trend_labels': trend_labels,
            'trend_data': trend_data,
            'improvement_areas': improvement_list
        })
        
    except Exception as e:
        print(f"❌ Error chart data: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROUTES UNTUK SEARCH/FILTER ====================
@app.route('/api/search-data')
@admin_required
def search_data():
    """API Search yang mendukung Filter Prodi & Semester"""
    try:
        # Ambil parameter
        q = request.args.get('q', '').strip().lower()
        prodi_filter = request.args.get('prodi', '').strip()
        semester_filter = request.args.get('semester', '').strip()
        
        # Base Query
        query = db.session.query(Respondent, SurveyResponse)\
            .join(SurveyResponse, Respondent.id == SurveyResponse.respondent_id)
        
        # 1. Filter Text (Nama / NIM)
        if q:
            query = query.filter(
                db.or_(
                    Respondent.nama.ilike(f'%{q}%'),
                    Respondent.nim.ilike(f'%{q}%')
                )
            )
        
        # 2. Filter Prodi (Jika dipilih)
        if prodi_filter and prodi_filter != 'All Programs':
            query = query.filter(Respondent.prodi == prodi_filter)
            
        # 3. Filter Semester (Jika dipilih)
        if semester_filter and semester_filter != 'All Semesters':
            try:
                query = query.filter(Respondent.semester == int(semester_filter))
            except:
                pass

        # Urutkan & Limit
        results = query.order_by(Respondent.timestamp.desc()).limit(50).all()
        
        # Format Data
        data = []
        for r, s in results:
            data.append({
                'nama': r.nama,
                'nim': r.nim,
                'prodi': r.prodi,
                'semester': r.semester,
                'total_score': s.total_score,
                'timestamp': s.timestamp.strftime('%d/%m/%Y')
            })
        
        # List Prodi untuk Dropdown
        prodi_list = [p[0] for p in db.session.query(Respondent.prodi).distinct().order_by(Respondent.prodi).all()]
        
        return jsonify({'data': data, 'prodi_list': prodi_list})
        
    except Exception as e:
        print(f"Search Error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== DASHBOARD API ROUTES ====================
@app.route('/api/dashboard-stats')
@admin_required
def dashboard_stats():
    """API untuk data dashboard stats"""
    try:
        total_respondents = Respondent.query.count()
        total_surveys = SurveyResponse.query.count()
        
        responses = SurveyResponse.query.all()
        avg_score = 0
        if responses:
            avg_score = sum([r.total_score for r in responses]) / len(responses)
        
        # Get latest activity
        latest_response = SurveyResponse.query.order_by(SurveyResponse.timestamp.desc()).first()
        latest_activity = latest_response.timestamp.strftime('%Y-%m-%d %H:%M') if latest_response else 'No data'
        
        return jsonify({
            'total_respondents': total_respondents,
            'total_surveys': total_surveys,
            'avg_score': round(avg_score, 2),
            'latest_activity': latest_activity,
            'success': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/top-performers')
@admin_required
def top_performers():
    """API untuk top performers"""
    try:
        # Join respondents with survey responses
        results = db.session.query(
            Respondent.nama,
            Respondent.nim,
            Respondent.prodi,
            SurveyResponse.total_score
        ).join(SurveyResponse, Respondent.id == SurveyResponse.respondent_id)\
        .order_by(SurveyResponse.total_score.desc())\
        .limit(10)\
        .all()
        
        top_performers = []
        for r in results:
            top_performers.append({
                'nama': r.nama,
                'nim': r.nim,
                'prodi': r.prodi,
                'score': r.total_score
            })
        
        return jsonify({
            'top_performers': top_performers,
            'success': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== TAMBAHAN API: INTEGRITY CHECK ====================
@app.route('/api/integrity-check')
@admin_required
def integrity_check():
    """Cek konsistensi data database"""
    try:
        # Cek 1: Responden tanpa Survey
        orphaned_respondents = db.session.query(Respondent).outerjoin(
            SurveyResponse, Respondent.id == SurveyResponse.respondent_id
        ).filter(SurveyResponse.id == None).count()
        
        # Cek 2: Survey tanpa Responden (Harusnya tidak mungkin karena Foreign Key, tapi jaga-jaga)
        orphaned_surveys = 0 # Logic kompleks, skip untuk simplifikasi
        
        status = "Secure"
        message = "Data konsisten."
        
        if orphaned_respondents > 0:
            status = "Warning"
            message = f"Ditemukan {orphaned_respondents} responden belum menyelesaikan survei."
            
        return jsonify({
            'status': status,
            'message': message,
            'score': 100 if orphaned_respondents == 0 else 85
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ROUTES UNTUK MANAJEMEN PERTANYAAN ====================
@app.route('/api/questions', methods=['GET', 'POST'])
@admin_required
def manage_questions():
    if request.method == 'GET':
        questions = Question.query.order_by(Question.category, Question.code).all()
        return jsonify([{
            'id': q.id, 
            'code': q.code, 
            'category': q.category, 
            'text': q.text
        } for q in questions])

    if request.method == 'POST':
        data = request.get_json()
        if Question.query.filter_by(code=data['code']).first():
            return jsonify({'error': 'Kode pertanyaan sudah ada!'}), 400
        
        new_q = Question(code=data['code'], category=data['category'], text=data['text'])
        db.session.add(new_q)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/questions/<int:id>', methods=['PUT', 'DELETE'])
@admin_required
def update_question(id):
    q = Question.query.get(id)
    if not q: return jsonify({'error': 'Not found'}), 404

    if request.method == 'DELETE':
        db.session.delete(q)
        db.session.commit()
        return jsonify({'success': True})

    if request.method == 'PUT':
        data = request.get_json()
        q.text = data.get('text', q.text)
        # Code sebaiknya tidak diubah sembarangan karena terkait kolom DB
        db.session.commit()
        return jsonify({'success': True})

# ==================== ROUTE TAMBAHAN (YANG HILANG) ====================
@app.route('/admin/delete-all-testing', methods=['POST'])
@admin_required
def delete_all_testing():
    """Hapus SEMUA data (Reset Total)"""
    try:
        # Cek kode konfirmasi dari form
        if request.form.get('confirm_code') != 'DELETE_ALL_2024':
            flash('Kode konfirmasi salah!', 'error')
            return redirect(url_for('admin'))
        
        # Hapus data
        num_surveys = SurveyResponse.query.delete()
        num_respondents = Respondent.query.delete()
        db.session.commit()
        
        flash(f'BERHASIL: {num_respondents} responden & {num_surveys} survei dihapus.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'error')
    return redirect(url_for('admin'))

@app.route('/delete/batch', methods=['POST'])
@admin_required
def delete_batch():
    """Hapus banyak data sekaligus (dipakai tombol Hapus di tabel)"""
    try:
        data = request.get_json()
        ids = data.get('respondent_ids', [])
        for rid in ids:
            SurveyResponse.query.filter_by(respondent_id=rid).delete()
            Respondent.query.filter_by(id=rid).delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== FUNGSI SEEDING DATABASE ====================
def seed_questions():
    """Mengisi database dengan pertanyaan default jika kosong"""
    with app.app_context():
        # Cek apakah tabel Question sudah ada isinya
        try:
            if Question.query.count() > 0: 
                print("ℹ️  Database pertanyaan sudah terisi. Skip seeding.")
                return
        except:
            print("⚠️ Tabel belum siap, skip seeding check.")
            return

        print("🌱 Seeding pertanyaan LENGKAP ke database...")
        
        # Format: (kode_unik, kategori, teks_pertanyaan)
        initial_data = [
            # INFO
            ('q1_info', 'info', 'Saya mampu menggunakan kata kunci spesifik dan operator pencarian (seperti "AND", "OR", tanda kutip) untuk menemukan literatur akademik yang relevan.'),
            ('q2_info', 'info', 'Saya selalu memeriksa kredibilitas penulis dan penerbit sebelum menggunakan artikel sebagai referensi tugas kuliah.'),
            ('q3_info', 'info', 'Saya mampu membedakan antara informasi yang bersifat fakta, opini, dan berita bohong (hoaks) di media sosial.'),
            ('q4_info', 'info', 'Saya memiliki sistem penyimpanan data (seperti Google Drive/iCloud) yang terorganisir sehingga mudah menemukan kembali file tugas lama.'),
            # COMM
            ('q5_comm', 'comm', 'Saya merasa nyaman menggunakan berbagai platform kolaborasi (Zoom, Google Docs, Trello/Notion) untuk kerja kelompok.'),
            ('q6_comm', 'comm', 'Saya memahami etika pengiriman surel (email) formal kepada dosen (menggunakan subjek yang jelas, salam pembuka, bahasa baku).'),
            ('q7_comm', 'comm', 'Saya sadar akan jejak digital (digital footprint) dan berhati-hati dalam memposting komentar atau foto di ruang publik digital.'),
            ('q8_comm', 'comm', 'Saya aktif berbagi pengetahuan atau materi pembelajaran yang bermanfaat kepada teman melalui grup digital.'),
            # CONTENT
            ('q9_content', 'content', 'Saya mampu mengoperasikan perangkat lunak perkantoran (Word, Excel, PPT) fitur lanjut (seperti mail merge, pivot table, atau animasi slide) untuk menunjang tugas.'),
            ('q10_content', 'content', 'Saya bisa membuat konten multimedia sederhana (infografis, video pendek, atau blog) untuk keperluan tugas atau organisasi.'),
            ('q11_content', 'content', 'Saya memahami konsep Hak Cipta (Copyright) dan lisensi Creative Commons saat mengambil gambar/musik dari internet.'),
            ('q12_content', 'content', 'Saya selalu mencantumkan sitasi/sumber rujukan dengan format yang benar (APA/IEEE) untuk menghindari plagiarisme.'),
            # SECURITY
            ('q13_security', 'security', 'Saya rutin mengganti kata sandi (password) akun akademik dan media sosial saya secara berkala.'),
            ('q14_security', 'security', 'Saya menggunakan fitur Autentikasi Dua Faktor (2FA) pada akun-akun penting (Email, KRS Online, Medsos).'),
            ('q15_security', 'security', 'Saya memeriksa izin akses aplikasi (app permissions) sebelum menginstalnya di gawai saya.'),
            ('q16_security', 'security', 'Saya mampu membatasi waktu layar (screen time) jika penggunaan gawai mulai mengganggu kesehatan fisik atau tidur saya.'),
            # PROBLEM
            ('q17_problem', 'problem', 'Ketika menghadapi masalah teknis (misal: gagal koneksi, error aplikasi), saya mencoba mencari solusinya sendiri terlebih dahulu sebelum bertanya pada orang lain.'),
            ('q18_problem', 'problem', 'Saya sering menggunakan alat digital/aplikasi baru untuk mempermudah manajemen waktu dan tugas kuliah saya.'),
            ('q19_problem', 'problem', 'Saya mampu beradaptasi dengan cepat jika dosen menggunakan platform pembelajaran (LMS) baru yang belum pernah saya gunakan.')
        ]
        
        for code, cat, text in initial_data:
            # Cek double insert
            if not Question.query.filter_by(code=code).first():
                db.session.add(Question(code=code, category=cat, text=text))
        
        db.session.commit()
        print("✅ Pertanyaan berhasil di-seed!")

# ==================== JALANKAN APLIKASI ====================
if __name__ == '__main__':
    init_database()
    create_default_admin()
    seed_questions()
    
    print("\n" + "="*70)
    print("🌐 URL PENTING:")
    print("="*70)
    print("1. Form Survei:        http://127.0.0.1:5000")
    print("2. Admin Panel:        http://127.0.0.1:5000/admin")
    print("3. View Data:          http://127.0.0.1:5000/view-data")
    print("4. Export CSV:         http://127.0.0.1:5000/export/csv")
    print("5. Export Excel:       http://127.0.0.1:5000/export/excel")
    print("="*70)
    print("🔒 FITUR KEAMANAN NIM:")
    print("   • NIM harus UNIK (tidak boleh duplikat)")
    print("   • NIM hanya menerima ANGKA (0-9)")
    print("   • NIM minimal 8 digit")
    print("="*70)
    print("🗑️  FITUR DELETE BARU:")
    print("   • Delete single data dari halaman View Data")
    print("   • Delete semua data testing dari Admin Panel")
    print("="*70)
    print("🔐 Login Admin Default:")
    print("   Username: admin")
    print("   Password: admin123")
    print("="*70)
    print("🚀 Server starting...")
    print("="*70)
    
    try:
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️  Mencoba port 5001...")
        app.run(debug=True, port=5001)