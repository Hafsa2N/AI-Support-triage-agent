#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path
from typing import Optional

from answer import extract_answer, overlap_ratio
from classify import classify_product, classify_request_type
from corpus import CorpusIndex
from utils import setup_logging

COMPANY_DOMAINS = {'hackerrank': 'hackerrank', 'claude': 'claude', 'visa': 'visa'}


def get_field(row, *names):
    for name in names:
        for key, value in row.items():
            if key.lower() == name.lower():
                return value
    return ""


def normalize_company(company_hint: str) -> Optional[str]:
    if not company_hint:
        return None
    hint = company_hint.strip().lower()
    if hint == 'none':
        return None
    for name, domain in COMPANY_DOMAINS.items():
        if name in hint:
            return domain
    return None


def pick_best_document(corpus_index: CorpusIndex, query: str, company_domain: Optional[str]):
    if company_domain:
        domain_candidates = corpus_index.search(query, top_k=5, expanded=True, domains=[company_domain])
        if domain_candidates:
            return domain_candidates[0]
        return None, 0.0

    global_candidates = corpus_index.search(query, top_k=5, expanded=True)
    if global_candidates:
        return global_candidates[0]
    return None, 0.0


HIGH_RISK_KEYWORDS = [
    'fraud', 'stolen', 'unauthorized', 'identity theft', 'lost card', 'refund',
    'chargeback', 'cancel', 'cancelled', 'blocked', 'suspended', 'dispute',
    'legal', 'attorney', 'emergency', 'compromise', 'breach', 'security',
    'service outage', 'account locked', 'access denied', 'hack', 'scam', 'risk'
]


def is_high_risk(text: str) -> bool:
    text = text.lower()
    return any(keyword in text for keyword in HIGH_RISK_KEYWORDS)


def infer_product_area(best_doc: dict | None) -> str:
    if not best_doc:
        return 'general'
    path = best_doc.get('path', '').replace('\\', '/').lower()
    segments = [segment for segment in path.split('/') if segment and segment not in ('data', 'claude', 'hackerrank', 'visa')]
    if not segments:
        return best_doc.get('domain', 'general')
    candidate = segments[0]
    if len(segments) > 1 and segments[1] not in ('support', 'docs', 'help'):
        candidate = segments[1]
    if candidate.endswith('.md') or any(char.isdigit() for char in candidate):
        return best_doc.get('domain', 'general')
    return candidate.replace('_', ' ').replace('-', ' ')


def format_response(answer: str, source: str) -> str:
    return f"Based on our documentation:\n\n{answer}\n\n📚 Source: {source}"


def is_answer_good(answer: str, query: str, score: float) -> bool:
    if not answer or len(answer.strip()) < 40:
        return False
    overlap = overlap_ratio(answer, query)
    if score < 25:
        return False
    if score < 30:
        return overlap >= 0.20
    return overlap >= 0.10

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--corpus', default='../data')
    args = parser.parse_args()
    
    setup_logging()
    print("Loading corpus...")
    try:
        corpus_index = CorpusIndex(Path(args.corpus))
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    print(f"Loaded {len(corpus_index.documents)} documents")
    
    # Read tickets
    tickets = []
    with open(args.input, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            if 'id' not in row or not row['id']:
                row['id'] = str(i)
            tickets.append(row)
    
    output_rows = []
    total = len(tickets)
    for idx, ticket in enumerate(tickets, 1):
        print(f"Processing {idx}/{total}", end='\r')
        issue = get_field(ticket, 'issue', 'Issue')
        subject = get_field(ticket, 'subject', 'Subject')
        company = get_field(ticket, 'company', 'Company')
        full_text = f"{subject} {issue}".strip()
        
        if not full_text:
            output_rows.append({
                'id': ticket['id'],
                'status': 'replied',
                'product_area': 'general',
                'response': 'No issue provided. Please provide details.',
                'justification': 'Empty ticket',
                'request_type': 'invalid'
            })
            continue
        
        company_domain = normalize_company(company)
        if company_domain is None:
            inferred = classify_product(full_text, company)
            if inferred in COMPANY_DOMAINS:
                company_domain = inferred

        best_idx, best_score = pick_best_document(corpus_index, full_text, company_domain)
        best_doc = corpus_index.get_document(best_idx) if best_idx is not None else None
        best_answer = extract_answer(best_doc['content'], full_text) if best_doc else ''
        risk = is_high_risk(full_text)
        answer_usable = best_doc and is_answer_good(best_answer, full_text, best_score)
        product_area = infer_product_area(best_doc)
        if product_area == 'general':
            product_area = classify_product(full_text, company)

        if answer_usable and (not risk or best_score >= 35):
            req_type, _ = classify_request_type(full_text)
            source = Path(best_doc['path']).name
            output_rows.append({
                'id': ticket['id'],
                'status': 'replied',
                'product_area': product_area,
                'response': format_response(best_answer, source),
                'justification': f"BM25={best_score:.2f}, domain={best_doc.get('domain','general')}, overlap={overlap_ratio(best_answer, full_text):.2f}",
                'request_type': req_type
            })
        else:
            escalation_reason = 'No reliable answer'
            if risk and answer_usable:
                escalation_reason = 'High-risk query requires human review'
            output_rows.append({
                'id': ticket['id'],
                'status': 'escalated',
                'product_area': product_area,
                'response': f"Your request has been escalated. Reference: {ticket['id']}",
                'justification': f"{escalation_reason} (score={best_score:.2f}, domain={(best_doc.get('domain') if best_doc else 'none')}, overlap={overlap_ratio(best_answer, full_text):.2f})",
                'request_type': 'product_issue'
            })
    
    print(f"\nWriting to {args.output}...")
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'status', 'product_area', 'response', 'justification', 'request_type']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    escalated = sum(1 for r in output_rows if r['status'] == 'escalated')
    print(f"Done. {len(output_rows)-escalated} replied, {escalated} escalated.")

if __name__ == '__main__':
    main()