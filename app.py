from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import os
import csv
from io import StringIO, BytesIO
import pandas as pd
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'survey-literasi-digital-2024-secret-key'

# ==================== KONFIGURASI DATABASE ====================
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'database.db')

print("=" * 70)
print("🚀 SISTEM SURVEI LITERASI DIGITAL")
print("=" * 70)
print(f"📁 Database: {database_path}")
print("=" * 70)

# Konfigurasi SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODEL DATABASE ====================
class Respondent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    nim = db.Column(db.String(20), unique=True, nullable=False)  # UNIQUE constraint
    prodi = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)

class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    respondent_id = db.Column(db.Integer, nullable=False)
    
    # Information & Data Literacy (4 pertanyaan)
    q1_info = db.Column(db.Integer, default=0)
    q2_info = db.Column(db.Integer, default=0)
    q3_info = db.Column(db.Integer, default=0)
    q4_info = db.Column(db.Integer, default=0)
    
    # Communication & Collaboration (4 pertanyaan)
    q5_comm = db.Column(db.Integer, default=0)
    q6_comm = db.Column(db.Integer, default=0)
    q7_comm = db.Column(db.Integer, default=0)
    q8_comm = db.Column(db.Integer, default=0)
    
    # Digital Content Creation (4 pertanyaan)
    q9_content = db.Column(db.Integer, default=0)
    q10_content = db.Column(db.Integer, default=0)
    q11_content = db.Column(db.Integer, default=0)
    q12_content = db.Column(db.Integer, default=0)
    
    # Security (4 pertanyaan)
    q13_security = db.Column(db.Integer, default=0)
    q14_security = db.Column(db.Integer, default=0)
    q15_security = db.Column(db.Integer, default=0)
    q16_security = db.Column(db.Integer, default=0)
    
    # Problem Solving (3 pertanyaan)
    q17_problem = db.Column(db.Integer, default=0)
    q18_problem = db.Column(db.Integer, default=0)
    q19_problem = db.Column(db.Integer, default=0)
    
    total_score = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.now)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

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
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            default_admin = Admin(username='admin', password=hashed_password)
            db.session.add(default_admin)
            db.session.commit()
            print("✅ Admin default dibuat - Username: admin, Password: admin123")

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
    """Membuat database dan tabel jika belum ada"""
    with app.app_context():
        try:
            if not os.path.exists(database_path):
                print("📁 Membuat database baru...")
                db.create_all()
                print(f"✅ Database berhasil dibuat: {database_path}")
            else:
                db.create_all()
                print(f"📁 Database sudah ada: {database_path}")
                
            test_connection()
            
        except Exception as e:
            print(f"❌ Error inisialisasi database: {e}")
            create_database_manual()

def test_connection():
    """Test koneksi database"""
    try:
        count = Respondent.query.count()
        print(f"📊 Data responden saat ini: {count} orang")
        return True
    except:
        print("⚠️  Database belum ada, akan dibuat...")
        return False

def create_database_manual():
    """Buat database manual dengan sqlite3 (fallback)"""
    import sqlite3
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS respondent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                nim TEXT NOT NULL UNIQUE,  -- UNIQUE constraint
                prodi TEXT NOT NULL,
                semester INTEGER NOT NULL,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_response (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                respondent_id INTEGER NOT NULL,
                q1_info INTEGER DEFAULT 0,
                q2_info INTEGER DEFAULT 0,
                q3_info INTEGER DEFAULT 0,
                q4_info INTEGER DEFAULT 0,
                q5_comm INTEGER DEFAULT 0,
                q6_comm INTEGER DEFAULT 0,
                q7_comm INTEGER DEFAULT 0,
                q8_comm INTEGER DEFAULT 0,
                q9_content INTEGER DEFAULT 0,
                q10_content INTEGER DEFAULT 0,
                q11_content INTEGER DEFAULT 0,
                q12_content INTEGER DEFAULT 0,
                q13_security INTEGER DEFAULT 0,
                q14_security INTEGER DEFAULT 0,
                q15_security INTEGER DEFAULT 0,
                q16_security INTEGER DEFAULT 0,
                q17_problem INTEGER DEFAULT 0,
                q18_problem INTEGER DEFAULT 0,
                q19_problem INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database manual berhasil dibuat!")
    except Exception as e:
        print(f"❌ Gagal membuat database manual: {e}")

# ==================== ROUTES UTAMA ====================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # Ambil data dari form
            nama = request.form['nama'].strip()
            nim = request.form['nim'].strip()
            prodi = request.form['prodi'].strip()
            semester = request.form['semester'].strip()
            
            # Validasi dasar
            if not all([nama, nim, prodi, semester]):
                flash('Harap lengkapi semua data!', 'error')
                return render_template('login.html')
            
            # Validasi NIM: hanya angka
            is_valid, error_msg = validate_nim(nim)
            if not is_valid:
                flash(f'NIM tidak valid: {error_msg}', 'error')
                return render_template('login.html')
            
            # Cek apakah NIM sudah terdaftar - VALIDASI DI SINI
            existing_respondent = Respondent.query.filter_by(nim=nim).first()
            if existing_respondent:
                flash('❌ NIM sudah terdaftar. Gunakan NIM lain.', 'error')
                return render_template('login.html')
            
            # Validasi semester
            try:
                semester_int = int(semester)
                if semester_int < 1 or semester_int > 8:
                    flash('Semester harus antara 1-8', 'error')
                    return render_template('login.html')
            except ValueError:
                flash('Semester harus berupa angka', 'error')
                return render_template('login.html')
            
            # Simpan ke database
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
            
            # Redirect ke halaman pertama survei
            return redirect(url_for('survey_info', respondent_id=respondent.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            flash(f'Terjadi error sistem: {str(e)}', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

# ==================== SURVEY MULTI-PAGE ROUTES ====================
# [Kode route survei multi-halaman tetap sama seperti sebelumnya]
# ... (kode survey_info, survey_comm, survey_content, survey_security, survey_problem)

@app.route('/survey/<int:respondent_id>/info', methods=['GET', 'POST'])
def survey_info(respondent_id):
    """Halaman 1: Information & Data Literacy"""
    respondent = Respondent.query.get(respondent_id)
    if not respondent:
        flash('Data responden tidak ditemukan!', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        try:
            session[f'survey_{respondent_id}_info'] = {
                'q1': int(request.form.get('q1', 0)),
                'q2': int(request.form.get('q2', 0)),
                'q3': int(request.form.get('q3', 0)),
                'q4': int(request.form.get('q4', 0))
            }
            return redirect(url_for('survey_comm', respondent_id=respondent_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('survey/survey_info.html', 
                          respondent_id=respondent_id,
                          respondent=respondent)

@app.route('/survey/<int:respondent_id>/comm', methods=['GET', 'POST'])
def survey_comm(respondent_id):
    """Halaman 2: Communication & Collaboration"""
    respondent = Respondent.query.get(respondent_id)
    if not respondent:
        flash('Data responden tidak ditemukan!', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        try:
            session[f'survey_{respondent_id}_comm'] = {
                'q5': int(request.form.get('q5', 0)),
                'q6': int(request.form.get('q6', 0)),
                'q7': int(request.form.get('q7', 0)),
                'q8': int(request.form.get('q8', 0))
            }
            return redirect(url_for('survey_content', respondent_id=respondent_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('survey/survey_comm.html',
                          respondent_id=respondent_id,
                          respondent=respondent)

@app.route('/survey/<int:respondent_id>/content', methods=['GET', 'POST'])
def survey_content(respondent_id):
    """Halaman 3: Digital Content Creation"""
    respondent = Respondent.query.get(respondent_id)
    if not respondent:
        flash('Data responden tidak ditemukan!', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        try:
            session[f'survey_{respondent_id}_content'] = {
                'q9': int(request.form.get('q9', 0)),
                'q10': int(request.form.get('q10', 0)),
                'q11': int(request.form.get('q11', 0)),
                'q12': int(request.form.get('q12', 0))
            }
            return redirect(url_for('survey_security', respondent_id=respondent_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('survey/survey_content.html',
                          respondent_id=respondent_id,
                          respondent=respondent)

@app.route('/survey/<int:respondent_id>/security', methods=['GET', 'POST'])
def survey_security(respondent_id):
    """Halaman 4: Security"""
    respondent = Respondent.query.get(respondent_id)
    if not respondent:
        flash('Data responden tidak ditemukan!', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        try:
            session[f'survey_{respondent_id}_security'] = {
                'q13': int(request.form.get('q13', 0)),
                'q14': int(request.form.get('q14', 0)),
                'q15': int(request.form.get('q15', 0)),
                'q16': int(request.form.get('q16', 0))
            }
            return redirect(url_for('survey_problem', respondent_id=respondent_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('survey/survey_security.html',
                          respondent_id=respondent_id,
                          respondent=respondent)

@app.route('/survey/<int:respondent_id>/problem', methods=['GET', 'POST'])
def survey_problem(respondent_id):
    """Halaman 5: Problem Solving (TERAKHIR)"""
    respondent = Respondent.query.get(respondent_id)
    if not respondent:
        flash('Data responden tidak ditemukan!', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        try:
            session[f'survey_{respondent_id}_problem'] = {
                'q17': int(request.form.get('q17', 0)),
                'q18': int(request.form.get('q18', 0)),
                'q19': int(request.form.get('q19', 0))
            }
            
            all_answers = {}
            for category in ['info', 'comm', 'content', 'security', 'problem']:
                cat_data = session.get(f'survey_{respondent_id}_{category}', {})
                all_answers.update(cat_data)
            
            total_score = sum(all_answers.values())
            
            response = SurveyResponse(
                respondent_id=respondent_id,
                q1_info=all_answers.get('q1', 0),
                q2_info=all_answers.get('q2', 0),
                q3_info=all_answers.get('q3', 0),
                q4_info=all_answers.get('q4', 0),
                q5_comm=all_answers.get('q5', 0),
                q6_comm=all_answers.get('q6', 0),
                q7_comm=all_answers.get('q7', 0),
                q8_comm=all_answers.get('q8', 0),
                q9_content=all_answers.get('q9', 0),
                q10_content=all_answers.get('q10', 0),
                q11_content=all_answers.get('q11', 0),
                q12_content=all_answers.get('q12', 0),
                q13_security=all_answers.get('q13', 0),
                q14_security=all_answers.get('q14', 0),
                q15_security=all_answers.get('q15', 0),
                q16_security=all_answers.get('q16', 0),
                q17_problem=all_answers.get('q17', 0),
                q18_problem=all_answers.get('q18', 0),
                q19_problem=all_answers.get('q19', 0),
                total_score=total_score
            )
            
            db.session.add(response)
            db.session.commit()
            
            for category in ['info', 'comm', 'content', 'security', 'problem']:
                session.pop(f'survey_{respondent_id}_{category}', None)
            
            print(f"✅ Survey lengkap disimpan - ID: {response.id}, NIM: {respondent.nim}, Score: {total_score}")
            flash('Survey berhasil disimpan! Terima kasih.', 'success')
            
            return redirect(url_for('success'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            flash(f'Terjadi error: {str(e)}', 'error')
    
    return render_template('survey/survey_problem.html',
                          respondent_id=respondent_id,
                          respondent=respondent)

@app.route('/success')
def success():
    return render_template('success.html')

# ==================== ADMIN ROUTE TERPUSAT ====================
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Halaman admin terpusat - login dan dashboard dalam satu halaman"""
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin_user = Admin.query.filter_by(username=username).first()
        
        if admin_user and check_password_hash(admin_user.password, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_id'] = admin_user.id
            flash('Login berhasil!', 'success')
            print(f"✅ Admin login: {username}")
        else:
            flash('Username atau password salah!', 'error')
    
    if session.get('admin_logged_in'):
        try:
            total_respondents = Respondent.query.count()
            total_surveys = SurveyResponse.query.count()
            
            responses = SurveyResponse.query.all()
            avg_score = 0
            if responses:
                avg_score = sum([r.total_score for r in responses]) / len(responses)
            
            return render_template('admin.html',
                                 total_respondents=total_respondents,
                                 total_surveys=total_surveys,
                                 avg_score=round(avg_score, 2),
                                 username=session.get('admin_username'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return render_template('admin.html', login_form=True)
    else:
        return render_template('admin.html', login_form=True)

@app.route('/admin/logout')
def admin_logout():
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

# ==================== PROTECTED ADMIN ROUTES ====================
# [Kode export csv, export excel, dan view_data tetap sama seperti sebelumnya]
# ... (kode export_csv, export_excel, view_data)

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
            html_parts.append('<h2>Data Responden (NIM Unik)</h2>')
            html_parts.append('<table><tr><th>ID</th><th>Nama</th><th>NIM</th><th>Prodi</th><th>Semester</th><th>Timestamp</th></tr>')
            for r in respondents:
                html_parts.append(f'<tr><td>{r.id}</td><td>{r.nama}</td><td><strong>{r.nim}</strong></td><td>{r.prodi}</td><td>{r.semester}</td><td>{r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else ""}</td></tr>')
            html_parts.append('</table>')
        else:
            html_parts.append('<p><em>Tidak ada data responden.</em></p>')
        
        if responses:
            html_parts.append('<h2>Data Jawaban Survei</h2>')
            html_parts.append('<table>')
            html_parts.append('<tr>')
            html_parts.append('<th>ID</th><th>Respondent ID</th><th>NIM</th>')
            html_parts.append('<th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th>')
            html_parts.append('<th>Q5</th><th>Q6</th><th>Q7</th><th>Q8</th>')
            html_parts.append('<th>Q9</th><th>Q10</th><th>Q11</th><th>Q12</th>')
            html_parts.append('<th>Q13</th><th>Q14</th><th>Q15</th><th>Q16</th>')
            html_parts.append('<th>Q17</th><th>Q18</th><th>Q19</th>')
            html_parts.append('<th>Total Score</th><th>Timestamp</th>')
            html_parts.append('</tr>')
            
            for r in responses:
                respondent = next((resp for resp in respondents if resp.id == r.respondent_id), None)
                nim = respondent.nim if respondent else "N/A"
                
                html_parts.append('<tr>')
                html_parts.append(f'<td>{r.id}</td><td>{r.respondent_id}</td><td>{nim}</td>')
                html_parts.append(f'<td>{r.q1_info}</td><td>{r.q2_info}</td><td>{r.q3_info}</td><td>{r.q4_info}</td>')
                html_parts.append(f'<td>{r.q5_comm}</td><td>{r.q6_comm}</td><td>{r.q7_comm}</td><td>{r.q8_comm}</td>')
                html_parts.append(f'<td>{r.q9_content}</td><td>{r.q10_content}</td><td>{r.q11_content}</td><td>{r.q12_content}</td>')
                html_parts.append(f'<td>{r.q13_security}</td><td>{r.q14_security}</td><td>{r.q15_security}</td><td>{r.q16_security}</td>')
                html_parts.append(f'<td>{r.q17_problem}</td><td>{r.q18_problem}</td><td>{r.q19_problem}</td>')
                html_parts.append(f'<td>{r.total_score}</td><td>{r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else ""}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
        else:
            html_parts.append('<p><em>Tidak ada data survei.</em></p>')
        
        html_parts.append('<br>')
        html_parts.append('<a href="/admin" class="btn"><i class="fas fa-arrow-left"></i> Kembali ke Admin Panel</a>')
        html_parts.append('<a href="/export/csv" class="btn"><i class="fas fa-file-csv"></i> Export CSV</a>')
        html_parts.append('<a href="/export/excel" class="btn"><i class="fas fa-file-excel"></i> Export Excel</a>')
        
        html_parts.append('</body></html>')
        
        final_html = ''.join(html_parts)
        return final_html
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"<h1>❌ Terjadi Error dalam view_data():</h1><pre>{error_detail}</pre>"

# ==================== JALANKAN APLIKASI ====================
if __name__ == '__main__':
    init_database()
    create_default_admin()
    
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