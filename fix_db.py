import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aims_exam.settings")
django.setup()

from zipgrade.models import ZipGradeExam
from zipgrade.views import _recalculate_subject_results

# Find all exams
exams = ZipGradeExam.objects.all()
print(f"Found {exams.count()} exams. Recalculating subject results properly...")

recalculated = 0
for exam in exams:
    _recalculate_subject_results(exam)
    recalculated += 1

print(f"Recalculated {recalculated} exams. Subject percentages are now accurate based on keys.")
