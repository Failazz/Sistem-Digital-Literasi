#!/usr/bin/env python3
"""
Script untuk export data dari database SQLite ke CSV/Excel
Jalankan: python export_data.py
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

# Konfigurasi
DATABASE_FILE = 'database.db'
EXPORT_FOLDER = 'exports'

def ensure_export_folder():
    """Buat folder export jika belum ada"""
    if not os.path.exists(EXPORT_FOLDER):
        os.makedirs(EXPORT_FOLDER)
        print(f"📁 Membuat folder: {EXPORT_FOLDER}")

def export_to_csv():
    """Export data ke CSV"""
    try:
        # Koneksi ke database
        conn = sqlite3.connect(DATABASE_FILE)
        
        # Query data gabungan
        query = '''
        SELECT 
            r.id, r.nama, r.nim, r.prodi, r.semester, r.timestamp,
            s.q1, s.q2, s.q3, s.q4, s.q5, s.q6, s.q7, s.q8, s.q9, s.q10,
            s.total_score, s.timestamp as survey_timestamp
        FROM respondent r
        JOIN survey_response s ON r.id = s.respondent_id
        ORDER BY r.id
        '''
        
        df = pd.read_sql_query(query, conn)
        
        # Simpan ke CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{EXPORT_FOLDER}/survey_data_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        conn.close()
        
        print(f"✅ Data berhasil diexport ke: {csv_filename}")
        print(f"📊 Jumlah baris: {len(df)}")
        
        return csv_filename
        
    except Exception as e:
        print(f"❌ Error export CSV: {e}")
        return None

def export_to_excel():
    """Export data ke Excel"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        
        # Ambil data terpisah untuk sheet berbeda
        respondents_df = pd.read_sql_query("SELECT * FROM respondent", conn)
        surveys_df = pd.read_sql_query("SELECT * FROM survey_response", conn)
        
        # Gabungan data
        query = '''
        SELECT 
            r.id, r.nama, r.nim, r.prodi, r.semester,
            s.q1, s.q2, s.q3, s.q4, s.q5, s.q6, s.q7, s.q8, s.q9, s.q10,
            s.total_score
        FROM respondent r
        JOIN survey_response s ON r.id = s.respondent_id
        '''
        combined_df = pd.read_sql_query(query, conn)
        
        # Simpan ke Excel dengan multiple sheets
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"{EXPORT_FOLDER}/survey_data_{timestamp}.xlsx"
        
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            respondents_df.to_excel(writer, sheet_name='Respondents', index=False)
            surveys_df.to_excel(writer, sheet_name='Survey Responses', index=False)
            combined_df.to_excel(writer, sheet_name='Combined Data', index=False)
        
        conn.close()
        
        print(f"✅ Data berhasil diexport ke: {excel_filename}")
        print(f"📊 Sheets: Respondents ({len(respondents_df)}), Surveys ({len(surveys_df)})")
        
        return excel_filename
        
    except Exception as e:
        print(f"❌ Error export Excel: {e}")
        return None

def show_statistics():
    """Tampilkan statistik database"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Hitung jumlah data
        cursor.execute("SELECT COUNT(*) FROM respondent")
        total_respondents = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM survey_response")
        total_surveys = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(total_score) FROM survey_response")
        avg_score = cursor.fetchone()[0] or 0
        
        print("=" * 50)
        print("📊 STATISTIK DATABASE")
        print("=" * 50)
        print(f"Total Responden: {total_respondents}")
        print(f"Total Survei: {total_surveys}")
        print(f"Rata-rata Skor: {avg_score:.2f}/50")
        print(f"File Database: {DATABASE_FILE}")
        print(f"Ukuran File: {os.path.getsize(DATABASE_FILE)} bytes")
        print("=" * 50)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error statistik: {e}")

def main():
    """Menu utama"""
    print("=" * 50)
    print("📁 EXPORT DATA SURVEI LITERASI DIGITAL")
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