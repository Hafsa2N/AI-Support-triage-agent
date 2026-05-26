import re
from utils import tokenize

def extract_answer(document: str, query: str, max_chars: int = 500) -> str:
    qt = set(tokenize(query))
    if not qt:
        return document[:max_chars] if document else ""
    
    sentences = re.split(r'(?<=[.!?])\s+', document)
    if not sentences:
        sentences = [document]
    
    best = max(sentences, key=lambda s: sum(1 for t in qt if t in s.lower()), default="")
    if best:
        if len(best) < 80:
            idx = sentences.index(best)
            if idx + 1 < len(sentences):
                best = best + " " + sentences[idx+1]
        if len(best) > max_chars:
            best = best[:max_chars] + "..."
        return best
    return document[:max_chars]

def overlap_ratio(answer: str, query: str) -> float:
    q = set(tokenize(query))
    if not q:
        return 0.0
    a = set(tokenize(answer))
    return len(q & a) / len(q)