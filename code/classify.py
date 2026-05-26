import re
from typing import Tuple

PRODUCT_KEYWORDS = {
    'hackerrank': ['assessment', 'coding', 'hackerrank', 'interview', 'test', 'problem',
                   'screen', 'settings', 'invite', 'candidates', 'resume', 'certificate',
                   'billing', 'payment', 'subscription', 'recruiter', 'candidate', 'job', 'score', 'editor', 'compiler', 'report'],
    'claude': ['claude', 'anthropic', 'ai', 'assistant', 'prompt', 'model', 'api', 'bedrock',
               'privacy', 'workspace', 'team', 'training', 'pricing', 'billing', 'security', 'data', 'policy', 'integration'],
    'visa': ['visa', 'payment', 'card', 'transaction', 'charge', 'refund', 'fraud', 'dispute',
             'atm', 'merchant', 'travel', 'support', 'authorization', 'billing', 'purchase', 'statement'],
}

REQUEST_KEYWORDS = {
    'bug': [
        'bug', 'crash', 'error', 'not working', 'broken', 'failing', 'exception',
        'site is down', 'not responding', 'unable to', 'cannot', "can't", 'failed',
        'login failed', 'payment failed', 'timeout', 'disconnect', 'blocked', 'locked out',
        'issue with', 'problem with', 'does not work', 'doesn\'t work'
    ],
    'feature_request': [
        'feature request', 'would like', 'can you add', 'please add', 'suggestion',
        'enhancement', 'improve', 'would be great if', 'it would be great if',
        'request', 'wish', 'better support', 'more details'
    ],
    'invalid': [r'^.{0,10}$', r'\basdf\b', r'\bspam\b', r'\bthank you\b', r'\bthanks\b',
                r'\bhello\b', r'\bgood morning\b', r'\bgood afternoon\b', r'\bhi\b'],
}

def classify_product(text: str, company_hint: str) -> str:
    if company_hint and company_hint.lower() != 'none':
        return company_hint.lower()
    text_lower = text.lower()
    scores = {prod: sum(1 for kw in kwlist if kw in text_lower) for prod, kwlist in PRODUCT_KEYWORDS.items()}
    best = max(scores, key=lambda p: (scores[p], p))
    if scores[best] == 0:
        return 'general'
    return best

def classify_request_type(text: str) -> Tuple[str, float]:
    if len(text.strip()) < 10:
        return 'invalid', 0.9
    text_lower = text.lower()
    for req_type, patterns in REQUEST_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return req_type, 0.7
    return 'product_issue', 0.5