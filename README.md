# 🤖 AI Support Triage Agent

**🥇 Top 3.3% globally** – Ranked 422 out of 12,885 participants from 48 countries in HackerRank Orchestrate 2026.

This project implements a deterministic, pure‑Python AI agent that triages real‑world support tickets for three product domains: HackerRank, Claude, and Visa. Using only an offline corpus of documentation, the agent decides whether to reply with a grounded answer (exact quote from the corpus) or escalate to a human. The system is designed to be **safe, reproducible, and free of hallucinations**.    

---

## Problem Summary

Support teams receive tickets that may be routine FAQs or sensitive issues (fraud, account access, billing disputes). The agent must:

- Use **only** the provided local documentation (no internet, no external APIs).  
- Understand context, classify request type, and assign a product area.  
- Reply only when a relevant, non‑harmful answer exists in the corpus.  
- Escalate when the query is risky, ambiguous, or lacks documentation.  

---

## What This AI Agent Does

It’s a from‑scratch, deterministic terminal‑based AI agent that reads real customer support tickets (HackerRank, Claude, Visa) and decides:

- **Reply** – with an exact, grounded quote from the official documentation, plus a source citation.
- **Escalate** – to a human when the answer is uncertain, high‑risk, or out of scope.

The agent uses **no LLMs, no embeddings**. Every decision is transparent, reproducible, and safe.

---

## 🧠 How the Agent Thinks (Architecture)

The agent processes each ticket through a multi‑stage pipeline.

### 1. Domain Normalisation & Query Expansion  
- Infers the product domain (HackerRank/Claude/Visa) from the ticket or the `Company` field.
- Expands the query using a **corpus‑derived co‑occurrence matrix** – a lightweight, deterministic way to add synonyms (e.g., “money” ↔ “payment”) without external word lists.

### 2. BM25 Retrieval with Metadata Boosts
- Custom BM25 implementation (`k1=1.2`, `b=0.75`) – term frequency saturation + length normalisation.
- Boosts documents whose **title, breadcrumbs, description, or source URL** match query terms. This exploits the structure of support documentation.

### 3. Domain‑Filtered Search
- Retrieves top‑5 candidates but only accepts the first document that belongs to the ticket’s company (based on URL, breadcrumbs, or title).  
  *Prevents replying with wrong‑product docs (e.g., a Claude doc for a HackerRank ticket).*

### 4. Answer Extraction & Quality Gate
- Splits the document into sentences, scores each by term overlap with the original query, and picks the best sentence (adds next if short).
- **Dynamic overlap threshold** – short queries need higher overlap; long queries can accept lower overlap. This balances precision and recall.

### 5. High‑Risk Escalation Gate (Safety First)
- Scans every ticket for explicit patterns: credit card numbers, SSNs, fraud, identity theft, lost access by non‑admin, urgent billing.
- If any pattern fires → **escalate immediately**, overriding all other logic.

### 6. Output
- Produces a CSV with `id, status, product_area, response, justification, request_type`.

---
## Why This Architecture?  

Every design choice prioritises **safety, determinism, and grounding**.    

- **BM25 instead of embeddings or LLMs** – the corpus is fixed and keyword‑rich; BM25 is deterministic, requires no external models, and naturally handles term frequency saturation and length normalisation.  
- **Co‑occurrence expansion instead of external synonym lists** – the matrix is built entirely from the corpus, keeping the system self‑contained and free of outside bias.
- **Metadata boosts** – support documents are structured (titles, breadcrumbs). Boosting these signals dramatically improves retrieval without adding opaque black‑box components.  
- **Domain‑filtered search** – prevents the classic failure mode of answering a HackerRank ticket with a Claude document, even when keyword overlap is high.  
- **Rule‑based escalation instead of a risk score** – explicit patterns for credit cards, SSNs, fraud, etc., make the safety logic fully auditable and explainable to a human reviewer.  
---

## Key Design Decisions

- **BM25 over TF‑IDF or embeddings** – BM25 saturates term frequency (diminishing returns for repeated keywords) and normalises for document length (preferring short, precise FAQs). It is deterministic and requires no external models.  
- **Metadata boosts** – By parsing YAML front matter from each `.md` file, the agent can bias retrieval towards documents whose titles or breadcrumbs strongly match the query. This exploits the structure of support documentation.  
- **Corpus‑only query expansion** – The co‑occurrence matrix is built at startup from the corpus itself, providing synonym handling without external word lists.  
- **Rule‑based escalation** – Instead of a black‑box risk score, explicit regex patterns for sensitive content make the safety logic fully explainable and auditable.  

---

## Output

The agent produces exactly the columns required by the problem statement:

| id | status   | product_area | response | justification | request_type |
|----|----------|--------------|----------|---------------|---------------|
| 1  | replied  | connectors   | Based on our documentation: For more information... 📚 Source: (from corpus data link) | BM25=51.25, domain=claude, overlap=0.30 | product_issue |
| 27 | replied  | hackerrank   | Based on our documentation: You can modify user roles by clicking the three dots... 📚 Source: (from corpus data link) | BM25=25.68, domain=hackerrank, overlap=0.33 | product_issue |

---
## Repository Structure

This repository contains only the solution code. The proprietary corpus and ticket CSV files are not included.
<img width="460" height="200" alt="image" src="https://github.com/user-attachments/assets/10aa6294-9c35-49a6-9c5e-68d88cd67679" />

## Setup & Prerequisites  
### 1. Download the Official HackerRank Starter Kit 
You must obtain the proprietary corpus and ticket CSVs from the official contest page. The starter repository is available at:

https://github.com/interviewstreet/hackerrank-orchestrate-may26

Clone it to your local machine: 
```bash
git clone https://github.com/interviewstreet/hackerrank-orchestrate-may26.git  
cd hackerrank-orchestrate-may26
```

### 2. Place This Solution Inside the Starter Kit
Copy the contents of this repository (the code and this README.md) into the starter kit’s root directory. The final structure should look like:

<img width="740" height="540" alt="Screenshot 2026-05-26 230221" src="https://github.com/user-attachments/assets/0d2876cc-ef72-473b-8b54-44a9bda8be6b" />


Note: The official starter kit already contains a code/ folder. This solution works perfectly when placed at the root level, beside data/ and support_tickets/.  

### 3. Python Version
The agent requires Python 3.8+. No additional packages are needed – just the standard library.

### Running the Agent
From the root of the starter kit (where data/ and support_tickets/ reside), run:  
python main.py --input support_tickets/support_tickets.csv --output support_tickets/output.csv --corpus data

Or, if you prefer to keep the code inside the code/ folder:  
python code/main.py --input support_tickets/support_tickets.csv --output support_tickets/output.csv --corpus data

## Results
After processing, the agent will print a summary like:  
Loaded 773 documents  
Processing 29/29  
Done. 20 replied, 9 escalated.  

9 escalations (all due to high‑risk content, low retrieval confidence, or out‑of‑scope queries)  
Zero hallucinations – every reply was a direct corpus quote  
Deterministic output – running the agent twice yields identical results  
The output CSV will be written to support_tickets/output.csv.  
<img width="1800" height="530" alt="Screenshot 2026-05-26 195856" src="https://github.com/user-attachments/assets/9098e455-8b74-4e06-9737-39ad19d77f44" />

## Strategy
This solution is intentionally conservative and grounded:  
- It only replies when a corpus-based answer is sufficiently strong.  
- It escalates weak or high-risk tickets rather than guessing.  

## Recognition
This performance was recognised with a **Global Rank 422 out of 12,885 participants** (top 3.3%) in HackerRank Orchestrate 2026, a 24‑hour solo AI agent hackathon with participants from 48 countries.  
<img width="790" height="480" alt="image" src="https://github.com/user-attachments/assets/c9c3552c-d5d1-4e39-8371-b0c8db991563" />


# Acknowledgments
HackerRank for organising this challenging and inspiring hackathon.  
The global community of 12,885 developers who made the competition so competitive and rewarding.  
Hafsa Nayeem– Built for HackerRank Orchestrate 2026.  


“The hardest part wasn’t building the agent – it was teaching it when to stay silent.”
