import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aims_exam.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE admissions_roundresultsession ADD COLUMN passing_score real NOT NULL DEFAULT 24.0;")
    print("Column added successfully!")
except Exception as e:
    print("Error:", e)
