#!/usr/bin/env python3
from app import app, db, Admin, Respondent, SurveyResponse
from werkzeug.security import generate_password_hash

with app.app_context():
    print("🗑️  Menghapus semua tabel...")
    db.drop_all()
    
    print("🔄 Membuat ulang tabel...")
    db.create_all()
    
    print("👤 Membuat admin default...")
    hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
    admin = Admin(username='admin', password=hashed_password)
    db.session.add(admin)
    db.session.commit()
    
    print("="*60)
    print("✅ DATABASE BERHASIL DIRESET!")
    print(f"   Username: admin")
    print(f"   Password: admin123")
    print("="*60)
    
    # Verifikasi
    admin_check = Admin.query.first()
    print(f"🔍 Admin di database: {admin_check.username}")
    print(f"🔍 Panjang hash: {len(admin_check.password)} karakter")