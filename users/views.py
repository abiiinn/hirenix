from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, CandidateProfile, CompanyProfile

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username') # can be email or username in frontend
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'users/login.html')

def register_view(request):
    if request.method == 'POST':
        role = request.POST.get('role') # 'COMPANY' or 'CANDIDATE'
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect('users:register')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return redirect('users:register')
            
        user = User.objects.create_user(username=username, email=email, password=password)
        
        if role == 'COMPANY':
            user.role = 'COMPANY'
            user.save()
            company_name = request.POST.get('company_name', username)
            CompanyProfile.objects.create(user=user, company_name=company_name)
        else:
            user.role = 'CANDIDATE'
            user.save()
            CandidateProfile.objects.create(user=user)
            
        login(request, user)
        messages.success(request, "Registration successful! Welcome to Hirenix.")
        return redirect('home')
        
    return render(request, 'users/register.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('users:login')

@login_required
def create_hr_view(request):
    if request.user.role != User.Role.COMPANY:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect('users:create_hr')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
        else:
            hr_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=User.Role.HR
            )
            # Create company profile for HR mapping to this company
            CompanyProfile.objects.create(
                user=hr_user,
                company_name=request.user.company_profile.company_name,
                description="HR Representation",
                company=request.user  # Link HR to the parent Company
            )
            messages.success(request, f"HR User '{username}' created successfully.")
            return redirect('dashboard')
            
    return render(request, 'users/create_hr.html')

@login_required
def profile_view(request):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only candidates have a profile dashboard.")
        return redirect('dashboard')
        
    profile = request.user.candidate_profile
    
    if request.method == 'POST':
        profile.bio = request.POST.get('bio', profile.bio)
        profile.skills = request.POST.get('skills', profile.skills)
        
        if 'resume' in request.FILES:
            profile.resume = request.FILES['resume']
            
        profile.save()
        messages.success(request, "Candidate dashboard updated successfully.")
        return redirect('users:profile')
        
    return render(request, 'users/profile.html', {'profile': profile})
