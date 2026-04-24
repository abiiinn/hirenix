import random
import urllib.request
import urllib.parse
import json
from .models import QuestionBank

FALLBACK_DOMAINS = [
    'Python programming', 'Java programming', 'JavaScript', 'C++', 'C#', 'Ruby programming', 
    'PHP', 'Swift programming', 'Go programming', 'Rust programming', 'TypeScript',
    'HTML', 'CSS', 'React framework', 'Angular framework', 'Vue.js', 'Django framework', 
    'Flask', 'Spring framework', 'Node.js', 'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 
    'Redis', 'Docker software', 'Kubernetes', 'Amazon Web Services', 'Git', 
    'Machine learning', 'Artificial intelligence', 'Linux', 'Agile software development', 
    'Data structures', 'Algorithms'
]

QUESTION_TEMPLATES = [
    "According to the web, which of the following best describes {domain}?",
    "Based on internet definitions, what is the primary function of {domain}?",
    "Which statement accurately represents the technology known as {domain}?",
]

import functools

@functools.lru_cache(maxsize=128)
def fetch_wiki_summary(query):
    """Pulls tech facts directly from the internet via Wikipedia's public API."""
    search_query = urllib.parse.quote(query + " software")
    url = f"https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exintro&explaintext&redirects=1&generator=search&gsrsearch={search_query}&gsrlimit=1"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            pages = data.get("query", {}).get("pages", {})
            if pages:
                page = list(pages.values())[0]
                extract = page.get("extract", "")
                sentences = extract.split(". ")
                if sentences:
                    summary = sentences[0]
                    if not summary.endswith("."):
                        summary += "."
                    return summary
    except Exception as e:
        print(f"Web pull error for {query}: {e}")
    return None

def generate_mcq_for_domain(domain, used_questions=None):
    """
    Dynamically generates an MCQ by pulling facts directly from the internet (Wikipedia).
    """
    if used_questions is None:
        used_questions = []
    
    # 1. Pull the true fact from the Web
    correct_fact = fetch_wiki_summary(domain)
    
    if not correct_fact:
        # Fallback to local DB if no internet connection or wiki fails
        return fallback_question(domain, used_questions)
        
    # 2. Pick 3 WRONG facts from OTHER domains
    other_domains = [d for d in FALLBACK_DOMAINS if d.lower().split()[0] not in domain.lower()]
    wrong_facts = []
    for d in random.sample(other_domains, 3):
        # Avoid hitting Wikipedia 30+ times per user which causes the page to infinitely load
        wrong_facts.append(f"It is a technology or methodology unrelated to {domain}, functioning primarily as {d}.")
    
    # 3. Choose a random template
    q_template = random.choice(QUESTION_TEMPLATES)
    question_text = q_template.format(domain=domain.upper())
    
    # 4. Shuffle options
    options = [correct_fact] + wrong_facts
    random.shuffle(options)
    
    correct_index = options.index(correct_fact)
    labels = ['A', 'B', 'C', 'D']
    correct_letter = labels[correct_index]
    
    # Check if we somehow already generated this exact templated question
    if any(u['question_text'] == question_text for u in used_questions):
        return fallback_question(domain, used_questions)
        
    return {
        'domain': domain,
        'question_text': question_text,
        'option_a': options[0],
        'option_b': options[1],
        'option_c': options[2],
        'option_d': options[3],
        'correct_option': correct_letter
    }

def fallback_question(domain, used_questions=None):
    if used_questions is None:
        used_questions = []
    
    used_texts = [u['question_text'].lower() for u in used_questions]
    
    questions = list(QuestionBank.objects.filter(domain__icontains=domain))
    valid_questions = [q for q in questions if q.question_text.lower() not in used_texts]
    
    if valid_questions:
        q = random.choice(valid_questions)
        return {
            'domain': q.domain,
            'question_text': q.question_text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'correct_option': q.correct_option,
        }
    
    # Generic fallback dynamic generator if nothing else exists
    general_topics = ["API Integration", "Database Design", "System Architecture", "Security Protocols", "Code Optimization"]
    safe_topic = random.choice(general_topics)
    q_text = f"Which is a core principle of {safe_topic}?"
    
    # Force variety so it doesn't fail on repeats
    return {
        'domain': domain,
        'question_text': q_text + f" (Context: {random.randint(100, 999)})",
        'option_a': "Ensuring loose coupling and high cohesion.",
        'option_b': "Maximizing global variable usage.",
        'option_c': "Avoiding version control.",
        'option_d': "Ignoring user security.",
        'correct_option': "A",
    }
