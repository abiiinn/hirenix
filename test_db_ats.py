import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirenix_prj.settings')
django.setup()

from jobs.models import Application
from jobs.ats import extract_skills_and_domains, extract_years_experience, extract_text_from_pdf, calculate_ats_score

apps = Application.objects.all()
for a in apps:
    jd_text = a.job.description + " " + a.job.requirements
    req_skills = extract_skills_and_domains(jd_text)
    
    resume_path = a.candidate.candidate_profile.resume.path
    resume_text = extract_text_from_pdf(resume_path)
    res_skills = extract_skills_and_domains(resume_text)
    
    score = calculate_ats_score(resume_text, jd_text)
    
    print(f"\nUser: {a.candidate.username}")
    print(f"Req Skills ({len(req_skills)}):", list(req_skills)[:10])
    print(f"Res Skills ({len(res_skills)}):", list(res_skills)[:10])
    print(f"Matched ({len(req_skills.intersection(res_skills))})")
    print(f"Final Score: {score}")
