from typing import List
from pydantic import BaseModel

class TopicClassification(BaseModel):
    type: str
    confidence: float
    keywords: List[str]

# Subject keywords for UAE K-12 curriculum
SUBJECT_KEYWORDS = {
    'mathematics': [
        'math', 'algebra', 'geometry', 'calculus', 'trigonometry', 'statistics',
        'probability', 'equation', 'formula', 'solve', 'calculate', 'number',
        'fraction', 'decimal', 'percentage', 'graph', 'function'
    ],
    'physics': [
        'physics', 'force', 'energy', 'motion', 'gravity', 'electricity',
        'magnetism', 'wave', 'light', 'sound', 'heat', 'temperature',
        'velocity', 'acceleration', 'mass', 'weight', 'pressure'
    ],
    'chemistry': [
        'chemistry', 'chemical', 'element', 'compound', 'molecule', 'atom',
        'reaction', 'acid', 'base', 'ph', 'solution', 'mixture',
        'periodic table', 'bond', 'electron', 'proton', 'neutron'
    ],
    'biology': [
        'biology', 'cell', 'organism', 'photosynthesis', 'respiration',
        'genetics', 'dna', 'evolution', 'ecosystem', 'plant', 'animal',
        'bacteria', 'virus', 'protein', 'enzyme', 'hormone'
    ],
    'arabic': [
        'arabic', 'عربي', 'نحو', 'صرف', 'بلاغة', 'أدب', 'شعر', 'نثر',
        'قواعد', 'إملاء', 'خط', 'تعبير', 'قراءة', 'كتابة'
    ],
    'english': [
        'english', 'grammar', 'vocabulary', 'writing', 'reading',
        'literature', 'essay', 'poem', 'story', 'novel', 'verb',
        'noun', 'adjective', 'sentence', 'paragraph'
    ],
    'social_studies': [
        'history', 'geography', 'culture', 'society', 'government',
        'economics', 'politics', 'civilization', 'uae', 'emirates',
        'middle east', 'arab', 'islam', 'tradition'
    ],
    'islamic_education': [
        'islam', 'islamic', 'quran', 'hadith', 'prophet', 'allah',
        'prayer', 'fasting', 'hajj', 'zakat', 'faith', 'muslim',
        'mosque', 'sunnah', 'iman', 'jihad', 'shariah'
    ]
}

def classify_topic(text: str) -> TopicClassification:
    """
    Classify the topic of a given text based on UAE K-12 curriculum subjects.
    
    Args:
        text: The input text to classify
        
    Returns:
        TopicClassification with type, confidence, and keywords
    """
    text_lower = text.lower()
    
    # Count keyword matches for each subject
    subject_scores = {}
    matched_keywords = {}
    
    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = 0
        matches = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += 1
                matches.append(keyword)
        
        if score > 0:
            subject_scores[subject] = score
            matched_keywords[subject] = matches
    
    # Determine the best matching subject
    if subject_scores:
        best_subject = max(subject_scores.items(), key=lambda x: x[1])
        total_keywords = sum(len(keywords) for keywords in SUBJECT_KEYWORDS.values())
        confidence = min(best_subject[1] / 5.0, 1.0)  # Normalize to max 1.0
        
        return TopicClassification(
            type=best_subject[0],
            confidence=confidence,
            keywords=matched_keywords[best_subject[0]]
        )
    
    # Default to general if no matches
    return TopicClassification(
        type="general",
        confidence=0.1,
        keywords=[]
    )