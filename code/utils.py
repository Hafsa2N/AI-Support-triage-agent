import re
import logging
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def infer_domain(file_path: Path, source_url: str = "") -> str:
    """Infer the support domain from the data folder path or source URL."""
    source = (source_url or '').lower()
    try:
        parts = [p.lower() for p in file_path.parts]
    except AttributeError:
        parts = str(file_path).lower().replace('\\', '/').split('/')

    if 'data' in parts:
        data_index = parts.index('data')
        if data_index + 1 < len(parts):
            candidate = parts[data_index + 1]
            if candidate in ('hackerrank', 'claude', 'visa'):
                return candidate

    path = str(file_path).lower().replace('\\', '/')
    if '/data/hackerrank/' in path or 'support.hackerrank.com' in source or 'help.hackerrank.com' in source:
        return 'hackerrank'
    if '/data/visa/' in path or 'visa.co.in' in source or '/visa/' in path or 'visa' in source:
        return 'visa'
    if '/data/claude/' in path or 'support.claude.com' in source or '/claude/' in path or 'claude' in source:
        return 'claude'
    return 'general'

def tokenize(text: str) -> List[str]:
    """Deterministic tokenizer: lowercase, keep words length >=2."""
    if not text:
        return []
    text = text.lower()
    return re.findall(r'\b[a-z0-9]{2,}\b', text)

def parse_front_matter(content: str) -> tuple[Dict[str, Any], str]:
    """Extract YAML front matter and return (metadata, body)."""
    if not content.startswith('---'):
        return {}, content
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    front = parts[1]
    body = parts[2]
    meta = {}
    for line in front.split('\n'):
        if ': ' in line:
            key, val = line.split(': ', 1)
            key = key.strip()
            val = val.strip()
            if key == 'breadcrumbs':
                import ast
                try:
                    val = ast.literal_eval(val)
                except:
                    val = []
            meta[key] = val
    return meta, body

def load_corpus(corpus_path: Path) -> List[Dict]:
    """Load all .txt, .md, .html files sorted by path, parse front matter."""
    documents = []
    files = sorted(corpus_path.rglob('*'))
    for file_path in files:
        if file_path.suffix.lower() in ('.txt', '.md', '.html'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw = f.read().strip()
                if not raw:
                    continue
                meta, body = parse_front_matter(raw)
                headers = []
                for line in body.split('\n'):
                    if line.startswith('#'):
                        headers.append(line.strip('# '))
                    elif line.strip().endswith(':'):
                        headers.append(line.strip(': '))
                source_url = meta.get('source_url', '')
                documents.append({
                    'path': str(file_path),
                    'content': body,
                    'title': meta.get('title', ''),
                    'breadcrumbs': meta.get('breadcrumbs', []),
                    'description': meta.get('description', ''),
                    'source_url': source_url,
                    'domain': infer_domain(file_path, source_url),
                    'headers': headers[:3],
                    'tokens': tokenize(body)
                })
            except Exception as e:
                logging.warning(f"Cannot read {file_path}: {e}")
    logging.info(f"Loaded {len(documents)} documents")
    return documents

def build_cooccurrence(documents: List[Dict], window: int = 5, decay: float = 0.9) -> Dict:
    """Build term co‑occurrence matrix with distance decay."""
    cooccur = defaultdict(lambda: defaultdict(float))
    for doc in documents:
        tokens = doc['tokens']
        for i, term in enumerate(tokens):
            start = max(0, i - window)
            end = min(len(tokens), i + window + 1)
            for j in range(start, end):
                if i != j:
                    distance = abs(i - j)
                    weight = decay ** (distance - 1)
                    cooccur[term][tokens[j]] += weight
    return cooccur

def expand_query(query_tokens: List[str], cooccur: Dict, top: int = 2) -> List[str]:
    """Add top co‑occurring terms to query (deterministic)."""
    expanded = set(query_tokens)
    for term in query_tokens:
        if term in cooccur:
            related = sorted(cooccur[term].items(), key=lambda x: (-x[1], x[0]))[:top]
            for rel_term, cnt in related:
                if cnt >= 1.0:
                    expanded.add(rel_term)
    return list(expanded)