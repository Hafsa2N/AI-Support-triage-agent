# Support Triage Agent

## Overview
This repository implements a deterministic, corpus-grounded triage agent for support tickets across three domains:
- **HackerRank**
- **Claude**
- **Visa**

The agent uses only the provided local corpus in `data/` and produces structured outputs in `support_tickets/output.csv`.

## What this solution does
- Loads the local knowledge corpus from `data/`
- Builds a BM25 retrieval index over document text and metadata
- Infers the ticket domain from `Company` or ticket text
- Restricts search to the correct domain when possible
- Extracts a grounded answer snippet from the best matching document
- Classifies `request_type` using keyword-based intent rules
- Infers `product_area` from the matched document path or fallback text classification
- Escalates when the answer is weak or the ticket contains high-risk terms

## Files in `code/`
- `main.py`: entry point and ticket processing
- `corpus.py`: document loader and domain-aware retrieval
- `bm25.py`: deterministic BM25 ranking with metadata boosts
- `answer.py`: answer extraction and overlap scoring
- `classify.py`: product area and request type inference
- `utils.py`: corpus loading, tokenization, and helpers

## Setup
1. Open a terminal in the repository root:
   ```bash
   cd C:/Users/pc/Desktop/hackerrank-orchestrate-may26
   ```
2. Use Python 3.8+ (3.14 recommended).
3. No additional packages are required.

## Run
From the repository root:
```bash
python code/main.py --input support_tickets/support_tickets.csv --output support_tickets/output.csv --corpus data
```

Or from the `code/` directory:
```bash
cd code
python main.py --input ../support_tickets/support_tickets.csv --output ../support_tickets/output.csv --corpus ../data
```

## Output
The agent writes the required columns to `support_tickets/output.csv`:
- `id`
- `status`
- `product_area`
- `response`
- `justification`
- `request_type`

## Strategy
This solution is intentionally conservative and grounded:
- It only replies when a corpus-based answer is sufficiently strong.
- It escalates weak or high-risk tickets rather than guessing.
- It uses deterministic retrieval and rule-based classification.

## Evaluation fit
The implementation is designed to satisfy the hackathon rubric:
- **Grounded answers** from the provided corpus only
- **Deterministic behavior** with no external API calls
- **Structured output** matching required schema
- **Explicit escalation reasoning** for low-confidence or risky tickets

## Notes
- If `Company` is missing, the agent infers the domain from ticket text.
- `product_area` is derived from the matched document path where possible.
- `request_type` is a heuristic keyword classification with fallback to `product_issue`.
