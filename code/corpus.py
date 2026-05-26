from pathlib import Path
from collections import defaultdict
from utils import load_corpus, build_cooccurrence, tokenize, expand_query
from bm25 import BM25

class CorpusIndex:
    def __init__(self, corpus_path: Path):
        self.documents = load_corpus(corpus_path)
        if not self.documents:
            raise ValueError(f"No documents found in {corpus_path}")
        self.bm25 = BM25(self.documents)
        self.cooccur = build_cooccurrence(self.documents)
        self.domain_index = defaultdict(list)
        for idx, doc in enumerate(self.documents):
            self.domain_index[doc.get('domain', 'general')].append(idx)
    
    def search(self, query: str, top_k: int = 3, expanded: bool = True, domains: list[str] | None = None):
        if expanded:
            qt = tokenize(query)
            expanded_terms = expand_query(qt, self.cooccur, top=2)
            query = ' '.join(expanded_terms)
        doc_ids = None
        if domains:
            doc_ids = []
            for domain in domains:
                doc_ids.extend(self.domain_index.get(domain, []))
            if not doc_ids:
                return []
        return self.bm25.search(query, top_k, doc_ids=doc_ids)
    
    def get_document(self, idx: int):
        return self.documents[idx]
    
    def jaccard_search(self, query: str, top_k: int = 1):
        """Fallback: Jaccard similarity on token sets (length‑insensitive)."""
        qt = set(tokenize(query))
        if not qt:
            return []
        scores = []
        for i, doc in enumerate(self.documents):
            dt = set(doc['tokens'])
            inter = len(qt & dt)
            union = len(qt | dt)
            score = inter / union if union else 0
            scores.append((i, score))
        scores.sort(key=lambda x: (-x[1], x[0]))
        return scores[:top_k]