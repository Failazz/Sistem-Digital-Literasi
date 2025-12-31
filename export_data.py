#!/usr/bin/env python3
"""
Script untuk export data dari database PostgreSQL ke CSV/Excel
"""

import os
import sys
from datetime import datetime
import pandas as pd

# Tambahkan path ke direktori ini
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import dari app
from app import app, db, Respondent, SurveyResponse

# Konfigurasi
EXPORT_FOLDER = 'exports'

def ensure_export_folder():
    """Buat folder export jika belum ada"""
    if not os.path.exists(EXPORT_FOLDER):
        os.makedirs(EXPORT_FOLDER)
        print(f"📁 Membuat folder: {EXPORT_FOLDER}")

def export_to_csv():
    """Export data ke CSV (PostgreSQL version)"""
    try:
        with app.app_context():
            # Query data menggunakan SQLAlchemy
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
            
            # Simpan ke CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{EXPORT_FOLDER}/survey_data_{timestamp}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            
            print(f"✅ Data berhasil diexport ke: {csv_filename}")
            print(f"📊 Jumlah baris: {len(df)}")
            
            return csv_filename
            
    except Exception as e:
        print(f"❌ Error export CSV: {e}")
        return None

def export_to_excel():
    """Export data ke Excel (PostgreSQL version)"""
    try:
        with app.app_context():
            respondents = Respondent.query.all()
            surveys = SurveyResponse.query.all()
            
            # Gabungan data
            data = []
            for response in surveys:
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
            
            # Simpan ke Excel
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"{EXPORT_FOLDER}/survey_data_{timestamp}.xlsx"
            
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Survey Data', index=False)
            
            print(f"✅ Data berhasil diexport ke: {excel_filename}")
            print(f"📊 Jumlah baris: {len(df)}")
            
            return excel_filename
            
    except Exception as e:
        print(f"❌ Error export Excel: {e}")
        return None

def show_statistics():
    """Tampilkan statistik database"""
    try:
        with app.app_context():
            total_respondents = Respondent.query.count()
            total_surveys = SurveyResponse.query.count()
            
            avg_score = 0
            if total_surveys > 0:
                total = db.session.query(db.func.sum(SurveyResponse.total_score)).scalar()
                avg_score = total / total_surveys
            
            print("=" * 50)
            print("📊 STATISTIK DATABASE POSTGRESQL")
            print("=" * 50)
            print(f"Total Responden: {total_respondents}")
            print(f"Total Survei: {total_surveys}")
            print(f"Rata-rata Skor: {avg_score:.2f}/95")
            print("=" * 50)
            
    except Exception as e:
        print(f"❌ Error statistik: {e}")

def main():
    """Menu utama"""
    print("=" * 50)
    print("📁 EXPORT DATA SURVEI LITERASI DIGITAL - POSTGRESQL")
    print("=" * 50)
    
    # Pastikan folder export ada
    ensure_export_folder()
    
    # Tampilkan statistik
    show_statistics()
    
    # Menu
    print("\nPilihan Export:")
    print("1. Export ke CSV")
    print("2. Export ke Excel")
    print("3. Export ke CSV dan Excel")
    print("4. Keluar")
    
    choice = input("\nPilih (1-4): ").strip()
    
    if choice == '1':
        export_to_csv()
    elif choice == '2':
        export_to_excel()
    elif choice == '3':
        export_to_csv()
        export_to_excel()
    elif choice == '4':
        print("Keluar...")
    else:
        print("Pilihan tidak valid!")
    
    input("\nTekan Enter untuk keluar...")

if __name__ == "__main__":
    main()