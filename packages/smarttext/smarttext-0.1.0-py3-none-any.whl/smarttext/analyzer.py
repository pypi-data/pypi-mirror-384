import re
from collections import Counter
from .sentiment import sentiment_score
from .language_detect import detect_language

def word_count(text: str) -> int:
    words = re.findall(r'\b\w+\b', text.lower())
    return len(words)

def sentence_count(text: str) -> int:
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return len(sentences)

def avg_word_length(text: str) -> float:
    words = re.findall(r'\b\w+\b', text)
    if not words:
        return 0
    total_length = sum(len(w) for w in words)
    return round(total_length / len(words), 2)

def top_words(text: str, n: int = 5):
    words = re.findall(r'\b\w+\b', text.lower())
    stopwords = {'the', 'is', 'and', 'a', 'of', 'in', 'to', 'it', 'that'}
    filtered = [w for w in words if w not in stopwords]
    counts = Counter(filtered)
    return [w for w, _ in counts.most_common(n)]

def analyze(text: str):
    print("?? SmartText Analizi:")
    print(f"Söz sayi: {word_count(text)}")
    print(f"Cüml? sayi: {sentence_count(text)}")
    print(f"Orta söz uzunlugu: {avg_word_length(text)}")
    print(f"?n çox isl?n?n sözl?r: {top_words(text)}")
    print(f"Sentiment: {sentiment_score(text)}")
    print(f"Dil: {detect_language(text)}")
