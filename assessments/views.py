from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import datetime
from jobs.models import Application
from .models import QuestionBank, CandidateMCQAttempt, VoiceInterview, VoiceQuestionResponse
from .utils import extract_domains_from_text
from .voice import process_voice_interview
import random
import os
from django.conf import settings
from pydub import AudioSegment

from .mcq_generator import generate_mcq_for_domain
from jobs.ats import extract_text_from_pdf, extract_skills_and_domains

@login_required
def take_mcq_test(request, app_id):
    app = get_object_or_404(Application, pk=app_id, candidate=request.user)
    
    if app.status != Application.Status.LEVEL1_PENDING:
        messages.warning(request, "This test is not currently available for you.")
        return redirect('dashboard')
        
    attempt, created = CandidateMCQAttempt.objects.get_or_create(application=app)
    
    if not created and attempt.passed:
        messages.info(request, "You have already passed Level 1.")
        return redirect('dashboard')
        
    if not attempt.questions_data:
        # Generate new questions dynamically using local AI
        resume_text = ""
        if app.candidate.candidate_profile.resume:
            try:
                resume_text = extract_text_from_pdf(app.candidate.candidate_profile.resume.path)
            except Exception as e:
                print(f"Error reading resume for MCQ GEN: {e}")
                
        # Extract domains from resume specifically
        domains = list(extract_skills_and_domains(resume_text))
        
        # Fallback to job domains if resume parsing missed stuff
        if len(domains) < 3:
            job_text = app.job.description + " " + app.job.requirements
            job_domains = extract_skills_and_domains(job_text)
            domains.extend(list(job_domains))
            
        if not domains:
            domains = ["Software Engineering"]
            
        random.shuffle(domains)
            
        # Generate 10 questions unique to this candidate's skill set
        selected_questions = []
        for i in range(10):
            # cycle through domains
            domain = domains[i % len(domains)]
            # Generate the question using the LLM logic
            q = generate_mcq_for_domain(domain, used_questions=selected_questions)
            q['id'] = i + 1 # Assign HTML frontend ID
            selected_questions.append(q)
            
        # Store securely to prevent re-rolls
        attempt.questions_data = selected_questions
        attempt.start_time = timezone.now()
        attempt.save()
    else:
        # Load from previously saved attempt
        selected_questions = attempt.questions_data
        # Fix for legacy attempts created before start_time was added
        if attempt.start_time is None:
            attempt.start_time = timezone.now()
            attempt.save(update_fields=['start_time'])
        
    # Calculate time left
    time_limit = datetime.timedelta(minutes=10)
    elapsed = timezone.now() - attempt.start_time
    time_left = max(0, (time_limit - elapsed).total_seconds())
    
    # If time is already up but they somehow got here, render a zero-time state
    if time_left <= 0:
        time_left = 0
        
    return render(request, 'assessments/mcq_test.html', {
        'app': app, 
        'questions': selected_questions,
        'time_left': int(time_left)
    })

@login_required
def submit_mcq_test(request, app_id):
    if request.method != 'POST':
        return redirect('dashboard')
        
    app = get_object_or_404(Application, pk=app_id, candidate=request.user)
    
    if app.status != Application.Status.LEVEL1_PENDING:
        return redirect('dashboard')
        
    try:
        attempt = CandidateMCQAttempt.objects.get(application=app)
    except CandidateMCQAttempt.DoesNotExist:
        messages.error(request, "No active test found.")
        return redirect('dashboard')
        
    questions = attempt.questions_data
    if not questions:
        messages.error(request, "Test session expired or invalid.")
        return redirect('dashboard')
        
    # Time verification (10 minutes + 30 sec buffer for network latency)
    time_limit = datetime.timedelta(minutes=10, seconds=30)
    
    # Fix for legacy attempts
    if attempt.start_time is None:
        attempt.start_time = timezone.now() - datetime.timedelta(minutes=10) # Assume expired if deeply legacy or treat gracefully
        attempt.save(update_fields=['start_time'])
        
    elapsed = timezone.now() - attempt.start_time
    
    if elapsed > time_limit:
        messages.warning(request, "Time expired. Only answers submitted within the 10-minute window have been recorded (if submitted automatically).")
        # Proceed with grading whatever they managed to submit, or treat all as incorrect if form is empty
        # Frontend auto-submit happens at 10m exactly, so getting here late means something went wrong, but we still grade what's in POST.
        
    correct_count = 0
    total_count = len(questions)
    
    for q in questions:
        # Answers posted as q_{id}
        answer = request.POST.get(f"q_{q['id']}")
        if answer == q['correct_option']:
            correct_count += 1
            
    score_percentage = (correct_count / total_count) * 100 if total_count > 0 else 0
    passed = score_percentage >= 60.0 # 60% threshold
    
    app.mcq_score = score_percentage
    if passed:
        app.status = Application.Status.LEVEL2_PENDING
        messages.success(request, f"Congratulations! You passed Level 1 with {score_percentage}%. You can now proceed to the Voice Interview.")
    else:
        app.status = Application.Status.LEVEL1_FAILED
        messages.error(request, f"You scored {score_percentage}%. Unfortunately, you did not pass Level 1.")
    
    app.save()
    
    # Update attempt record
    attempt.score = score_percentage
    attempt.passed = passed
    attempt.save()
    
    return redirect('dashboard')

from .models import QuestionBank, CandidateMCQAttempt, VoiceInterview, VoiceQuestionResponse
from .mcq_generator import fetch_wiki_summary

@login_required
def take_voice_test(request, app_id):
    app = get_object_or_404(Application, pk=app_id, candidate=request.user)
    
    if app.status != Application.Status.LEVEL2_PENDING:
        messages.warning(request, "This test is not currently available for you.")
        return redirect('dashboard')
        
    interview, created = VoiceInterview.objects.get_or_create(application=app)
    
    if not created and interview.passed:
        messages.info(request, "You have already passed Level 2.")
        return redirect('dashboard')
        
    # Generate 5 Questions if starting fresh or if it crashed mid-generation
    if interview.responses.count() < 5:
        interview.responses.all().delete()
        # Question 1: Behavioral Intro
        VoiceQuestionResponse.objects.create(
            interview=interview,
            question_number=1,
            question_text="Please introduce yourself. Briefly describe your background and what makes you a strong candidate for this role.",
            is_technical=False
        )
        
        # Extract skills for Tech Questions 2-5
        resume_text = ""
        if app.candidate.candidate_profile.resume:
            try:
                resume_text = extract_text_from_pdf(app.candidate.candidate_profile.resume.path)
            except Exception:
                pass
                
        domains = list(extract_skills_and_domains(resume_text))
        if len(domains) < 4:
            job_text = app.job.description + " " + app.job.requirements
            domains.extend(list(extract_skills_and_domains(job_text)))
            
        if not domains:
            domains = ["Software Engineering"]
            
        # Select up to 4 distinct domains for technical assessment
        random.shuffle(domains)
        tech_topics = []
        for d in domains:
            if d.lower() not in tech_topics:
                tech_topics.append(d.lower())
            if len(tech_topics) >= 4:
                break
                
        # Fill gaps with general tech if ATS extracted obscure stuff
        fallback_topics = ['python', 'git', 'database_design', 'agile']
        while len(tech_topics) < 4:
            tech_topics.append(fallback_topics.pop())
            
        # Create Question 2-5
        for i, topic in enumerate(tech_topics, start=2):
            q_text = f"Technical Scenario: Can you describe your practical experience with {topic.upper()}? Explain a problem you successfully solved using its core features."
            
            VoiceQuestionResponse.objects.create(
                interview=interview,
                question_number=i,
                question_text=q_text,
                expected_answer="", # No longer used for comparison scoring
                is_technical=True
            )
            
    # Find the next unanswered question
    pending_question = interview.responses.filter(audio_file='').order_by('question_number').first()
    
    if not pending_question:
        # All 5 answered, calculate final score
        calculate_final_voice_score(request, app, interview)
        return redirect('dashboard')
        
    progress_percent = ((pending_question.question_number - 1) / 5) * 100
        
    return render(request, 'assessments/voice_test.html', {
        'app': app,
        'question': pending_question,
        'progress': progress_percent
    })

@login_required
def submit_voice_test(request, app_id):
    if request.method != 'POST':
        return redirect('dashboard')
        
    app = get_object_or_404(Application, pk=app_id, candidate=request.user)
    
    if app.status != Application.Status.LEVEL2_PENDING:
        return redirect('dashboard')
        
    question_id = request.POST.get('question_id')
    question = get_object_or_404(VoiceQuestionResponse, id=question_id, interview__application=app)
        
    audio_file = request.FILES.get('audio_data')
    if not audio_file:
        messages.error(request, "No audio data received.")
        return redirect('assessments:voice_test', app_id=app.id)

    # Basic backend enforcement of ~1 minute (limit file to 2.5MB)
    if audio_file.size > 2.5 * 1024 * 1024:
        messages.error(request, "Audio file is too large. Please keep your answer under 1 minute.")
        return redirect('assessments:voice_test', app_id=app.id)

    # Save to a temporary webm file
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_voice')
    os.makedirs(temp_dir, exist_ok=True)
    
    webm_path = os.path.join(temp_dir, f"q_{question.id}.webm")
    wav_path = os.path.join(temp_dir, f"q_{question.id}.wav")
    
    with open(webm_path, 'wb+') as destination:
        for chunk in audio_file.chunks():
            destination.write(chunk)
            
    # CRITICAL FIX: Save the audio file immediately.
    # This ensures the 'audio_file' field is populated, so the interview
    # state advances to the next question even if AI transcription fails.
    question.audio_file = audio_file
    question.save()
            
    try:
        # Convert webm to wav since Vosk needs wav
        audio = AudioSegment.from_file(webm_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(wav_path, format="wav")
        
        # Process the WAV file locally
        fluency_score, confidence_score, transcription = process_voice_interview(wav_path)
        technical_score = 0.0
        
        # If it's a technical question, calculate a score based strictly on what the candidate answered
        if question.is_technical:
            from jobs.ats import extract_skills_and_domains
            import re
            
            # Count how many meaningful technical terms they successfully used in their answer
            skills_mentioned = extract_skills_and_domains(transcription.lower())
            keyword_score = len(skills_mentioned) * 15.0 # 15 points per valid tech keyword
            
            # Factor in the depth/length of their answer (if they give a 1-word answer, it's bad)
            word_count = len(re.findall(r'\w+', transcription))
            length_score = min((word_count / 30.0) * 40.0, 40.0) # Up to 40 max points for explaining > 30 words
            
            technical_score = min(keyword_score + length_score, 100.0)
            print(f"Candidate scored {technical_score} on Tech Q. Keywords: {skills_mentioned}, Length: {word_count}")
                
        # Update Question Record with scores
        question.transcription = transcription
        question.fluency_score = fluency_score
        question.confidence_score = confidence_score
        question.technical_score = technical_score
        question.save()
        
    except Exception as e:
        messages.warning(request, "Audio saved successfully, but AI analysis experienced a temporary issue.")
        print(f"Audio processing error: {e}")
    finally:
        if os.path.exists(webm_path):
            os.remove(webm_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

    # Loop back to next question
    return redirect('assessments:voice_test', app_id=app.id)
    
def calculate_final_voice_score(request, app, interview):
    responses = interview.responses.all()
    
    total_f = sum(r.fluency_score for r in responses)
    total_c = sum(r.confidence_score for r in responses)
    tech_responses = [r for r in responses if r.is_technical]
    total_t = sum(r.technical_score for r in tech_responses)
    
    avg_fluency = total_f / 5.0
    avg_confidence = total_c / 5.0
    avg_tech = total_t / 4.0 if tech_responses else 0.0
    
    interview.overall_fluency = round(avg_fluency, 2)
    interview.overall_confidence = round(avg_confidence, 2)
    interview.overall_technical_score = round(avg_tech, 2)
    
    # Pass candidate to Level 3 HR Interview only if they meet the threshold
    passed = (avg_fluency >= 40.0 and avg_tech >= 40.0)
    interview.passed = passed
    interview.save()
    
    app.voice_fluency_score = interview.overall_fluency
    app.voice_confidence_score = interview.overall_confidence
    
    if passed:
        app.status = Application.Status.LEVEL3_PENDING
        messages.success(request, f"Voice Interview Passed! You have advanced to Level 3. Fluency: {round(avg_fluency)}%, Tech Accuracy: {round(avg_tech)}%")
    else:
        app.status = Application.Status.LEVEL2_FAILED
        messages.error(request, f"Voice Interview Failed. Fluency: {round(avg_fluency)}%, Tech Accuracy: {round(avg_tech)}%")
        
    app.save()

@login_required
def voice_detail(request, app_id):
    app = get_object_or_404(Application, pk=app_id)
    
    # Simple auth check: only the hiring company, the assigned HR, or admin should see this
    if request.user.role not in ['COMPANY', 'HR', 'ADMIN']:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
        
    try:
        interview = VoiceInterview.objects.get(application=app)
    except VoiceInterview.DoesNotExist:
        messages.error(request, "No voice interview data found.")
        return redirect('core:company_dashboard')
        
    responses = interview.responses.all()
    
    return render(request, 'assessments/voice_detail.html', {
        'app': app,
        'interview': interview,
        'responses': responses
    })
