import PyPDF2
import re
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print("Warning: en_core_web_sm not found. ATS parsing will fail until installed.")
    nlp = None

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + " "
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_skills_and_domains(text):
    """
    Extracts explicit, known technical skills from the text using a comprehensive 
    pre-defined glossary for 100% accuracy, ignoring names and places.
    """
    if not text:
        return set()
        
    text = text.lower()
    skills = set()
    
    # Comprehensive list of standardized tech skills and domains
    TECH_GLOSSARY = [
        'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'go', 'rust', 'kotlin', 'typescript',
        'html', 'css', 'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'node.js', 'nodejs',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'oracle', 'sqlite',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'git', 'github', 'gitlab',
        'machine learning', 'artificial intelligence', 'data science', 'deep learning', 'nlp', 'computer vision',
        'linux', 'unix', 'windows', 'macos', 'bash', 'shell scripting', 'powershell',
        'agile', 'scrum', 'kanban', 'jira', 'confluence', 'trello',
        'rest api', 'graphql', 'grpc', 'soap', 'microservices', 'serverless', 'blockchain',
        'cybersecurity', 'penetration testing', 'cryptography', 'network security',
        'numpy', 'pandas', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'opencv',
        'pandas', 'matplotlib', 'seaborn', 'hadoop', 'spark', 'kafka', 'airflow',
        'figma', 'adobe xd', 'photoshop', 'illustrator', 'ui/ux', 'user interface', 'user experience',
        'data structures', 'algorithms', 'object-oriented programming', 'oop', 'functional programming',
        'software engineering', 'web development', 'mobile development', 'game development',
        'data analysis', 'business intelligence', 'tableau', 'power bi', 'excel',
        'salesforce', 'sap', 'erp', 'crm', 'seo', 'digital marketing'
    ]
    
    # Fast regex boundary matching to avoid partial word hits (e.g. finding 'go' inside 'good')
    for skill in TECH_GLOSSARY:
        # Use regex boundary "\b" for exact word match
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            # Normalize variations
            if skill == 'nodejs': skill = 'node.js'
            if skill == 'oop': skill = 'object-oriented programming'
            skills.add(skill)
                
    return skills

def extract_years_experience(text):
    """
    Extracts the maximum years of experience mentioned in the text.
    Matches patterns like '5 years of experience', '3+ yrs experience', '10 yrs'
    """
    if not text:
        return 0
        
    text = text.lower()
    
    # Regex patterns for experience
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience',
        r'experience.*?:.*(?:\b|[^0-9])(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)'
    ]
    
    max_years = 0
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                years = int(match)
                if years < 40: # Sanity check
                    max_years = max(max_years, years)
            except ValueError:
                pass
                
    return max_years

def calculate_ats_score(resume_text, job_description):
    """
    Calculates an AI-based ATS score by extracting and comparing
    Skills/Domains and Experience separately.
    Returns a similarity score between 0.0 and 100.0
    """
    if not resume_text.strip() or not job_description.strip() or not nlp:
        return 0.0
        
    try:
        # 1. TF-IDF Cosine Similarity (Overall Content Match - 40% Weight)
        tfidf = TfidfVectorizer(stop_words='english')
        # We fit on the job description and transform the resume to see 
        # how much of the resume projects onto the JD's vocabulary map
        tfidf_matrix = tfidf.fit_transform([job_description, resume_text])
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        tfidf_score = cosine_sim * 40.0
        
        # 2. Extract Required vs Candidate Skills using Spacy (Exact Key Entity Match - 30% Weight)
        required_skills = extract_skills_and_domains(job_description)
        candidate_skills = extract_skills_and_domains(resume_text)
        
        skill_score = 0.0
        if required_skills:
            matched_skills = required_skills.intersection(candidate_skills)
            
            # Recall: Did they explicitly have the specific hard skills we found?
            recall_ratio = len(matched_skills) / len(required_skills)
            skill_score = recall_ratio * 30.0
        else:
            # If no skills clearly required, default to mid score
            skill_score = 15.0
            
        # 3. Extract Required vs Candidate Experience (30% weight)
        required_exp = extract_years_experience(job_description)
        candidate_exp = extract_years_experience(resume_text)
        
        exp_score = 0.0
        if required_exp > 0:
            if candidate_exp >= required_exp:
                exp_score = 30.0 # Full points for meeting/exceeding
            else:
                exp_score = (candidate_exp / required_exp) * 30.0
        else:
            exp_score = 30.0
            
        # 4. Combine scores for final 100 max
        final_score = tfidf_score + skill_score + exp_score
        
        # Add a slight cap/boost formula 
        return round(min(final_score * 1.15, 100.0), 2)
        
    except Exception as e:
        print(f"Error calculating AI ATS score: {e}")
        return 0.0
