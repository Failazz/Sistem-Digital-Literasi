#!/usr/bin/env python3
# Import seed_questions
from app import app, db, Admin, Respondent, SurveyResponse, Question, seed_questions
from werkzeug.security import generate_password_hash

with app.app_context():
    print("Menghapus semua tabel...")
    db.drop_all()
    
    print("Membuat ulang tabel...")
    db.create_all()
    
    print("Membuat admin default...")
    hashed = generate_password_hash('rahasiadapur', method='pbkdf2:sha256')
    db.session.add(Admin(username='admin', password=hashed))
    
    # INI YANG KEMARIN KURANG:
    print("Mengisi Soal (Seeding)...")
    seed_questions()  # Panggil fungsi yang sudah kita perbaiki teksnya
    
    db.session.commit()
    
    print("="*60)
    print("DATABASE BERHASIL DIRESET & DIISI SOAL LENGKAP!")
    print(f"   Jumlah Soal: {Question.query.count()}")
    print("="*60)