import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

from core.config import settings

# Comprehensive skills database organized by category
SKILLS_DB = {
    # Programming Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'ruby', 'go', 'golang',
    'rust', 'swift', 'kotlin', 'scala', 'php', 'perl', 'r', 'matlab', 'dart', 'lua',
    'objective-c', 'shell', 'bash', 'powershell', 'groovy', 'haskell', 'elixir', 'clojure',
    'visual basic', 'assembly', 'fortran', 'cobol', 'julia',

    # Frontend
    'react', 'react.js', 'reactjs', 'angular', 'angularjs', 'vue', 'vue.js', 'vuejs',
    'svelte', 'next.js', 'nextjs', 'nuxt.js', 'nuxtjs', 'gatsby', 'html', 'html5',
    'css', 'css3', 'sass', 'scss', 'less', 'tailwind', 'tailwindcss', 'bootstrap',
    'material ui', 'mui', 'chakra ui', 'styled-components', 'webpack', 'vite',
    'jquery', 'redux', 'mobx', 'zustand', 'ember',

    # Backend & Frameworks
    'node.js', 'nodejs', 'express', 'express.js', 'django', 'flask', 'fastapi',
    'spring', 'spring boot', 'asp.net', '.net', 'dotnet', 'rails', 'ruby on rails',
    'laravel', 'symfony', 'gin', 'fiber', 'nest.js', 'nestjs', 'graphql', 'rest',
    'restful', 'grpc', 'soap', 'microservices',

    # Databases
    'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'cassandra',
    'dynamodb', 'sqlite', 'oracle', 'sql server', 'mariadb', 'couchdb', 'neo4j',
    'elasticsearch', 'firebase', 'firestore', 'supabase', 'cockroachdb',
    'influxdb', 'timescaledb', 'snowflake', 'bigquery',

    # Cloud & DevOps
    'aws', 'amazon web services', 'azure', 'gcp', 'google cloud', 'docker',
    'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'circleci',
    'github actions', 'gitlab ci', 'ci/cd', 'nginx', 'apache',
    'heroku', 'vercel', 'netlify', 'digitalocean', 'cloudflare',
    'lambda', 'serverless', 'ecs', 'eks', 'fargate', 's3', 'ec2',
    'cloudformation', 'pulumi', 'vagrant', 'helm', 'istio', 'prometheus',
    'grafana', 'datadog', 'new relic', 'splunk', 'elk stack',

    # AI / ML / Data Science
    'machine learning', 'deep learning', 'artificial intelligence', 'ai', 'ml',
    'natural language processing', 'nlp', 'computer vision', 'cv',
    'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'xgboost',
    'lightgbm', 'catboost', 'hugging face', 'transformers', 'bert', 'gpt',
    'llm', 'large language models', 'rag', 'langchain', 'openai',
    'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly',
    'tableau', 'power bi', 'data analysis', 'data science', 'data engineering',
    'data visualization', 'statistical analysis', 'statistics',
    'feature engineering', 'model deployment', 'mlops', 'spark', 'pyspark',
    'hadoop', 'airflow', 'dbt', 'etl', 'data pipeline', 'data warehousing',
    'neural networks', 'cnn', 'rnn', 'lstm', 'gan', 'reinforcement learning',
    'recommendation systems', 'time series', 'anomaly detection',
    'opencv', 'yolo', 'object detection', 'image classification',

    # Mobile
    'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic',
    'swift ui', 'swiftui', 'jetpack compose',

    # Testing
    'jest', 'mocha', 'cypress', 'selenium', 'pytest', 'unittest', 'junit',
    'testng', 'playwright', 'puppeteer', 'postman', 'tdd', 'bdd',
    'integration testing', 'unit testing', 'end-to-end testing', 'qa',

    # Version Control & Collaboration
    'git', 'github', 'gitlab', 'bitbucket', 'svn', 'mercurial',
    'jira', 'confluence', 'trello', 'asana', 'slack', 'notion',

    # Security
    'cybersecurity', 'penetration testing', 'owasp', 'oauth', 'jwt',
    'ssl', 'tls', 'encryption', 'authentication', 'authorization',
    'sso', 'ldap', 'active directory',

    # Architecture & Patterns
    'system design', 'design patterns', 'solid', 'oop', 'functional programming',
    'event-driven', 'message queue', 'rabbitmq', 'kafka', 'sqs', 'pub/sub',
    'distributed systems', 'caching', 'load balancing', 'api design',
    'domain-driven design', 'clean architecture', 'monolith', 'saga pattern',

    # Soft Skills / Methodologies
    'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'six sigma',
    'project management', 'team leadership', 'communication',
    'problem solving', 'critical thinking', 'time management',
    'stakeholder management', 'cross-functional',

    # Other Tech
    'linux', 'unix', 'windows', 'macos', 'embedded systems', 'iot',
    'blockchain', 'web3', 'smart contracts', 'solidity',
    'ar', 'vr', 'augmented reality', 'virtual reality', 'unity', 'unreal engine',
    'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator',
    'ux', 'ui', 'ui/ux', 'user experience', 'user interface', 'wireframing',
    'prototyping', 'responsive design', 'accessibility', 'a11y',
    'seo', 'google analytics', 'excel', 'vba',
}

# Multi-word skills sorted by length descending so we match longest first
MULTI_WORD_SKILLS = sorted(
    [s for s in SKILLS_DB if ' ' in s or '/' in s or '.' in s],
    key=len,
    reverse=True
)
SINGLE_WORD_SKILLS = {s for s in SKILLS_DB if ' ' not in s and '/' not in s and '.' not in s}


class NLPEngine:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            # If not downloaded, download it and then load (though we did it in requirements script)
            import spacy.cli
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        self.model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)

    def extract_skills(self, text: str) -> list[str]:
        """Extract skills from text by matching against the comprehensive skills database."""
        text_lower = text.lower()
        found_skills = set()

        # 1. Match multi-word / compound skills first (longest match wins)
        for skill in MULTI_WORD_SKILLS:
            # Use word boundary matching for accuracy
            pattern = r'(?:^|[\s,;()\[\]|/])' + re.escape(skill) + r'(?:$|[\s,;()\[\]|/.])'
            if re.search(pattern, text_lower):
                found_skills.add(skill)

        # 2. Match single-word skills with word boundaries
        for skill in SINGLE_WORD_SKILLS:
            if len(skill) <= 2:
                # Very short skills (AI, ML, R, C, QA) need exact boundary matching
                pattern = r'(?:^|[\s,;()\[\]|/])' + re.escape(skill) + r'(?:$|[\s,;()\[\]|/.])'
                if re.search(pattern, text_lower):
                    found_skills.add(skill)
            else:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.add(skill)

        # Normalize: title-case each skill for display
        normalized = set()
        for skill in found_skills:
            # Keep acronyms uppercase
            if skill.upper() == skill or len(skill) <= 3:
                normalized.add(skill.upper())
            else:
                normalized.add(skill.title())

        return sorted(list(normalized))

    def extract_name(self, text: str) -> str:
        doc = self.nlp(text[:1000]) # Look at the top of the text
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        return "Unknown Candidate"

    def extract_education_keywords(self, text: str) -> dict:
        """Extract education-related information from text."""
        text_lower = text.lower()
        result = {
            "degrees": [],
            "fields": [],
            "institutions_mentioned": False
        }

        # Degree levels
        degree_patterns = {
            "PhD": [r'\bph\.?d\b', r'\bdoctorate\b', r'\bdoctoral\b'],
            "Master's": [r"\bmaster'?s?\b", r'\bm\.?s\.?\b', r'\bm\.?a\.?\b', r'\bmba\b', r'\bm\.?tech\b', r'\bm\.?sc\b'],
            "Bachelor's": [r"\bbachelor'?s?\b", r'\bb\.?s\.?\b', r'\bb\.?a\.?\b', r'\bb\.?tech\b', r'\bb\.?sc\b', r'\bb\.?e\.?\b', r'\bbeng\b'],
            "Associate's": [r"\bassociate'?s?\b"],
            "Diploma": [r'\bdiploma\b'],
            "Certification": [r'\bcertif(?:ied|ication|icate)\b'],
        }

        for degree, patterns in degree_patterns.items():
            for p in patterns:
                if re.search(p, text_lower):
                    if degree not in result["degrees"]:
                        result["degrees"].append(degree)
                    break

        # Fields of study
        fields = [
            'computer science', 'software engineering', 'information technology',
            'data science', 'electrical engineering', 'mechanical engineering',
            'mathematics', 'statistics', 'physics', 'economics', 'finance',
            'business administration', 'marketing', 'psychology',
            'biomedical', 'biotechnology', 'chemistry', 'biology',
            'civil engineering', 'chemical engineering', 'aerospace',
            'artificial intelligence', 'machine learning', 'cybersecurity',
        ]
        for field in fields:
            if field in text_lower:
                result["fields"].append(field.title())

        # Check for university/institution mentions
        institution_keywords = ['university', 'college', 'institute', 'school', 'academy', 'iit', 'mit', 'stanford']
        for kw in institution_keywords:
            if kw in text_lower:
                result["institutions_mentioned"] = True
                break

        return result

    def extract_experience_years(self, text: str) -> float:
        """Try to extract years of experience from resume text."""
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'(?:experience|exp)\s*(?:of\s*)?(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:in\s+)',
        ]
        max_years = 0
        for p in patterns:
            matches = re.findall(p, text.lower())
            for m in matches:
                try:
                    years = int(m)
                    if 0 < years < 50:  # sanity check
                        max_years = max(max_years, years)
                except:
                    pass
        return float(max_years)

    def get_embedding(self, text: str):
        return self.model.encode(text)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        score = cosine_similarity([emb1], [emb2])[0][0]
        return float(max(0.0, min(1.0, score)))

nlp_engine = NLPEngine()
