import re

# A basic list of known tech domains we might have in our QuestionBank
KNOWN_DOMAINS = [
    'python', 'django', 'react', 'javascript', 'html', 'css', 
    'machine learning', 'data science', 'sql', 'postgres', 'aws', 
    'docker', 'kubernetes', 'java', 'c++', 'go', 'ruby'
]

def extract_domains_from_text(text):
    """
    Extracts known tech domains from job descriptions.
    """
    text = text.lower()
    
    # Extract alpha-numeric words and common tech terms
    words = re.findall(r'[a-z0-9\+]+', text)
    
    extracted = set()
    for domain in KNOWN_DOMAINS:
        if domain in text:  # Simple subtitle match for multi-word like "machine learning"
            extracted.add(domain)
        elif domain in words:
            extracted.add(domain)
            
    # Default to general if nothing found
    if not extracted:
        extracted.add('general')
        
    return list(extracted)
