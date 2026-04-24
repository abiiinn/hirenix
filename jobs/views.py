from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import User
from .models import Job, Application
from .ats import extract_text_from_pdf, calculate_ats_score

from django.db.models import Q

def job_list(request):
    jobs = Job.objects.filter(status=Job.Status.OPEN).order_by('-created_at')
    
    query = request.GET.get('q')
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company__username__icontains=query) |
            Q(company__company_profile__company_name__icontains=query)
        ).distinct()
        
    return render(request, 'jobs/list.html', {'jobs': jobs, 'query': query})

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    has_applied = False
    
    if request.user.is_authenticated and request.user.role == 'CANDIDATE':
        has_applied = Application.objects.filter(candidate=request.user, job=job).exists()
        
    return render(request, 'jobs/detail.html', {'job': job, 'has_applied': has_applied})

@login_required
def job_create(request):
    if request.user.role != 'COMPANY':
        messages.error(request, "Only companies can post jobs.")
        return redirect('home')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        salary = request.POST.get('salary')
        deadline = request.POST.get('deadline')
        hr_assignee_id = request.POST.get('hr_assignee')
        
        if not deadline:
            deadline = None
            
        hr_assignee = None
        if hr_assignee_id:
            hr_assignee = User.objects.filter(id=hr_assignee_id, role='HR').first()
        
        Job.objects.create(
            company=request.user,
            title=title,
            description=description,
            requirements=requirements,
            salary=salary,
            deadline=deadline,
            hr_assignee=hr_assignee,
            status=Job.Status.OPEN
        )
        messages.success(request, "Job posted successfully!")
        return redirect('jobs:list')
        
    hr_users = User.objects.filter(role='HR')
    if hasattr(request.user, 'company_profile'):
        hr_users = hr_users.filter(company_profile__company=request.user)
        
    return render(request, 'jobs/create.html', {'hr_users': hr_users})

@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, company=request.user)
    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.description = request.POST.get('description')
        job.requirements = request.POST.get('requirements')
        job.salary = request.POST.get('salary')
        
        deadline = request.POST.get('deadline')
        job.deadline = deadline if deadline else None
        
        hr_assignee_id = request.POST.get('hr_assignee')
        if hr_assignee_id:
            job.hr_assignee = User.objects.filter(id=hr_assignee_id, role='HR').first()
        else:
            job.hr_assignee = None
            
        job.save()
        messages.success(request, "Job updated successfully!")
        return redirect('dashboard')
        
    hr_users = User.objects.filter(role='HR')
    if hasattr(request.user, 'company_profile'):
        hr_users = hr_users.filter(company_profile__company=request.user)
        
    return render(request, 'jobs/edit.html', {'job': job, 'hr_users': hr_users})

@login_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk, company=request.user)
    if request.method == 'POST':
        job.delete()
        messages.success(request, "Job deleted successfully!")
        return redirect('dashboard')
    
    # Optional GET confirmation, but we will use a POST form/modal in UI
    return redirect('dashboard')

@login_required
def job_apply(request, pk):
    if request.user.role != 'CANDIDATE':
        messages.error(request, "Only candidates can apply for jobs.")
        return redirect('jobs:detail', pk=pk)
        
    job = get_object_or_404(Job, pk=pk)
    
    if Application.objects.filter(candidate=request.user, job=job).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('jobs:detail', pk=pk)
        
    if job.is_expired:
        messages.error(request, "This job has expired and is no longer accepting applications.")
        return redirect('jobs:detail', pk=pk)
        
    if request.method == 'POST':
        profile = request.user.candidate_profile
        
        if not profile.resume:
            messages.error(request, "Please upload your resume in your Profile before applying.")
            return redirect('jobs:detail', pk=pk)
            
        try:
            resume_text = extract_text_from_pdf(profile.resume.path)
            job_text = job.description + " " + job.requirements
            ats_score = calculate_ats_score(resume_text, job_text)
        except Exception as e:
            ats_score = 0.0
            print(f"Failed ATS calculation: {e}")
            
        # Auto-promote to MCQ if ATS match is decent (>= 40%)
        initial_status = Application.Status.LEVEL1_PENDING if ats_score >= 40.0 else Application.Status.ATS_REJECTED
            
        Application.objects.create(
            candidate=request.user,
            job=job,
            status=initial_status,
            ats_score=ats_score
        )
        messages.success(request, f"Successfully applied for {job.title}. Your application is under review.")
        return redirect('jobs:detail', pk=pk)
        
    return redirect('jobs:detail', pk=pk)

@login_required
def job_rankings(request, pk):
    if request.user.role != 'COMPANY':
        messages.error(request, "Only companies can view applicant rankings.")
        return redirect('dashboard')
        
    job = get_object_or_404(Job, pk=pk, company=request.user)
    applications = list(job.applications.all())
    
    # Sort primarily by MCQ score (Level 1), then fallback to ATS match score
    # Use 0.0 as default if mcq_score or ats_score is None
    ranked_apps = sorted(
        applications, 
        key=lambda x: (getattr(x, 'mcq_score', 0.0) or 0.0, getattr(x, 'ats_score', 0.0) or 0.0), 
        reverse=True
    )
    
    # Inject rank index into the objects for the template
    for idx, app in enumerate(ranked_apps, start=1):
        app.rank_position = idx
        
    return render(request, 'jobs/rankings.html', {'job': job, 'ranked_apps': ranked_apps})
