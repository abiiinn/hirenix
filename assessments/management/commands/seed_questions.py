from django.core.management.base import BaseCommand
from assessments.models import QuestionBank

class Command(BaseCommand):
    help = 'Seeds the database with domain-specific MCQs'

    def handle(self, *args, **kwargs):
        questions = [
            # Python
            {
                'domain': 'python',
                'question_text': 'What is the output of `print(2 ** 3)` in Python?',
                'options': ['6', '8', '9', 'Error'],
                'correct': 'B'
            },
            {
                'domain': 'python',
                'question_text': 'Which of the following data types is immutable in Python?',
                'options': ['List', 'Dictionary', 'Set', 'Tuple'],
                'correct': 'D'
            },
            {
                'domain': 'python',
                'question_text': 'What keyword is used to handle exceptions in Python?',
                'options': ['catch', 'except', 'handle', 'error'],
                'correct': 'B'
            },
            # Django
            {
                'domain': 'django',
                'question_text': 'In Django, which command creates a new app?',
                'options': ['django-admin createapp', 'python manage.py newapp', 'python manage.py startapp', 'django-admin newapp'],
                'correct': 'C'
            },
            {
                'domain': 'django',
                'question_text': 'What is the default template engine in Django?',
                'options': ['Jinja2', 'DjangoTemplates', 'Mako', 'Cheetah'],
                'correct': 'B'
            },
            {
                'domain': 'django',
                'question_text': 'Which method is called when an object is saved in Django ORM?',
                'options': ['.commit()', '.update()', '.save()', '.write()'],
                'correct': 'C'
            },
            # React
            {
                'domain': 'react',
                'question_text': 'What hook is used to manage state in a functional component?',
                'options': ['useEffect', 'useState', 'useContext', 'useReducer'],
                'correct': 'B'
            },
            # General
            {
                'domain': 'general',
                'question_text': 'What does HTTP stand for?',
                'options': ['Hyper Text Transport Protocol', 'Hypertext Transfer Protocol', 'Hyper Text Transfer Program', 'Hyperlink Transfer Protocol'],
                'correct': 'B'
            },
            {
                'domain': 'general',
                'question_text': 'Which of these is a version control system?',
                'options': ['Docker', 'Git', 'Jenkins', 'Nginx'],
                'correct': 'B'
            },
            {
                'domain': 'general',
                'question_text': 'What does API stand for?',
                'options': ['Application Programming Interface', 'Application Program Internet', 'Automated Program Integration', 'Automated Programming Interface'],
                'correct': 'A'
            },
        ]

        count = 0
        for q in questions:
            obj, created = QuestionBank.objects.get_or_create(
                question_text=q['question_text'],
                defaults={
                    'domain': q['domain'],
                    'option_a': q['options'][0],
                    'option_b': q['options'][1],
                    'option_c': q['options'][2],
                    'option_d': q['options'][3],
                    'correct_option': q['correct']
                }
            )
            if created:
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} questions into QuestionBank.'))
