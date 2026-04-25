import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aims_exam.settings")
django.setup()

from admissions.models import OnlineAttempt, AdmissionCycle

print("All AdmissionCycles:")
for cycle in AdmissionCycle.objects.all():
    print(f"Cycle ID {cycle.id}: {cycle.name} | tab_switch_action={cycle.tab_switch_action} | enable_tab_warnings={cycle.enable_tab_warnings} | max_tab_switches={cycle.max_tab_switches}")

print("\nRecent OnlineAttempts:")
for attempt in OnlineAttempt.objects.order_by('-started_at')[:3]:
    print(f"Attempt ID {attempt.id} | student={attempt.student} | status={attempt.status} | warnings={attempt.total_warnings} | locked={attempt.lock_reason}")
