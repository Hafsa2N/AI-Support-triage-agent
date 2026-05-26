import math
from collections import Counter
from typing import List, Tuple
from utils import tokenize

class BM25:
    def __init__(self, documents: List[dict], k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.avgdl = sum(len(doc['tokens']) for doc in documents) / len(documents)
        
        self.doc_term_freqs = []
        term_doc_count = Counter()
        for doc in documents:
            tf = Counter(doc['tokens'])
            self.doc_term_freqs.append(tf)
            term_doc_count.update(set(doc['tokens']))
        
        N = len(documents)
        self.idf = {}
        for term, df in term_doc_count.items():
            self.idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)
    
    def score(self, query_tokens: List[str], doc_idx: int) -> float:
        doc = self.documents[doc_idx]
        doc_len = len(doc['tokens'])
        base = 0.0
        for term in set(query_tokens):
            if term not in self.idf:
                continue
            tf = self.doc_term_freqs[doc_idx].get(term, 0)
            if tf == 0:
                continue
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            base += self.idf[term] * (numerator / denominator)
        
        # Metadata boosts
        boost = 0.0
        # Title boost
        title_tokens = tokenize(doc.get('title', ''))
        boost += sum(self.idf.get(t, 0) for t in set(query_tokens) if t in title_tokens) * 2.0
        # Breadcrumbs boost
        bread_text = ' '.join(doc.get('breadcrumbs', []))
        bread_tokens = tokenize(bread_text)
        boost += sum(self.idf.get(t, 0) for t in set(query_tokens) if t in bread_tokens) * 1.5
        # Description boost
        desc_tokens = tokenize(doc.get('description', ''))
        boost += sum(self.idf.get(t, 0) for t in set(query_tokens) if t in desc_tokens) * 1.2
        # Source URL boost (exact product name)
        url = doc.get('source_url', '').lower()
        if 'claude' in url and any(t in ['claude', 'anthropic'] for t in query_tokens):
            boost += 2.0
        if 'hackerrank' in url and any(t in ['hackerrank', 'hiring', 'test'] for t in query_tokens):
            boost += 2.0
        if 'visa' in url and any(t in ['visa', 'card', 'payment'] for t in query_tokens):
            boost += 2.0
        
        return base + boost
    
    def search(self, query: str, top_k: int = 3, doc_ids: list[int] | None = None) -> List[Tuple[int, float]]:
        tokens = tokenize(query)
        if not tokens:
            return []
        if doc_ids is None:
            doc_ids = list(range(len(self.documents)))
        scores = [(i, self.score(tokens, i)) for i in doc_ids]
        scores.sort(key=lambda x: (-x[1], x[0]))
        return scores[:top_k]