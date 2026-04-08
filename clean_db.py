import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aims_exam.settings')
django.setup()

from accounts.models import User
from admissions.models import ExternalSchool, AdmissionCandidate, AdmissionRegistration, AdmissionResult, AdmissionUploadSession, OnlineAttempt

print("Starting deep clean...")

# 1. Delete all students. This will CASCADE delete their User records and standard related models.
students_deleted, _ = User.objects.filter(role='student').delete()
print(f"Deleted students: {students_deleted}")

# 2. Delete all loose Admission related records (if any didn't cascade)
cand_del, _ = AdmissionCandidate.objects.all().delete()
print(f"Deleted extra candidates: {cand_del}")

reg_del, _ = AdmissionRegistration.objects.all().delete()
print(f"Deleted extra registrations: {reg_del}")

res_del, _ = AdmissionResult.objects.all().delete()
print(f"Deleted extra results: {res_del}")

sess_del, _ = AdmissionUploadSession.objects.all().delete()
print(f"Deleted admission upload sessions: {sess_del}")

# 3. Delete exam attempts
att_del, _ = OnlineAttempt.objects.all().delete()
print(f"Deleted online attempts: {att_del}")

# 4. Delete school registry
school_del, _ = ExternalSchool.objects.all().delete()
print(f"Deleted External Schools registry: {school_del}")

print("Clean successful! AdmissionCycles, Questions, and subject splits are totally untouched. Admin users remain intact.")
