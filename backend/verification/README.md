
# CiteVerify - AI Verification Module

## 1. Overview

The verification module checks whether scientific claims are supported by research paper evidence.

It retrieves research papers, extracts relevant evidence, uses an AI model to evaluate claims, and classifies verification results.

## 2. Technologies Used

- Python
- Ollama
- Llama 3.2 (3B)
- Crossref API
- OpenAlex API
- Requests
- PyMuPDF

## 3. Module Files

| File | Responsibility |
|---|---|
| prompts.py | Generates AI verification prompts |
| paper_retriever.py | Searches research papers using Crossref |
| evidence_retriever.py | Retrieves abstracts and available PDF evidence |
| evidence_matcher.py | Identifies relevant evidence passages |
| ai_verifier.py | Sends verification prompts to the local AI model |
| result_classifier.py | Validates and classifies AI results |
| verifier.py | Integrates all verification components |
| test_verifier.py | Runs automated verification tests |

## 4. Verification Workflow

1. Receive a scientific claim and DOI.
2. Retrieve research paper information.
3. Retrieve available research evidence.
4. Identify relevant evidence passages.
5. Generate an AI verification prompt.
6. Send the prompt to the Ollama Llama 3.2 model.
7. Validate the AI response and evidence quotations.
8. Classify the verification result.
9. Return the final verification report.

## 5. Supported Verification Statuses

- SUPPORTED
- PARTIALLY SUPPORTED
- UNSUPPORTED
- CONTRADICTORY
- POTENTIALLY OUTDATED
- NEEDS REVIEW

## 6. Installation Requirements

Install the Python dependencies:

```bash
pip install requests pymupdf
```

Install Ollama and download the model:

```bash
ollama pull llama3.2:3b
```

Ollama must be running before AI verification.

## 7. Running the Verification Module

Run from the main project directory:

```bash
python -m backend.verification.verifier
```

## 8. Running Automated Tests

```bash
python -m unittest backend.verification.test_verifier -v
```

## 9. Input Format

The verification module accepts:

- Scientific claim
- DOI of the research paper

Example:

```python
result = verify_claim(
    claim="Machine learning is used in healthcare.",
    doi="10.1126/science.aaa8415"
)
```

## 10. Output Format

The module returns a dictionary containing:

```json
{
    "status": "SUPPORTED",
    "confidence": 80.0,
    "explanation": "The evidence supports the scientific claim.",
    "evidence": "Exact research evidence quotation.",
    "review_required": false,
    "paper_title": "Research paper title",
    "doi": "10.xxxx/example",
    "publication_year": 2015,
    "evidence_source": "OpenAlex",
    "evidence_type": "ABSTRACT",
    "relevant_passages": []
}
```

## 11. Error Handling

The module handles:

- Empty scientific claims
- Missing DOI
- Invalid DOI
- Unavailable research evidence
- AI connection failures
- Invalid AI responses
- Unverified evidence quotations

When automated verification cannot be completed, the result is classified as NEEDS REVIEW.

## 12. Important Limitation

AI-generated classifications and confidence scores are automated assessments, not scientifically calibrated conclusions.

Human review is required for uncertain or high-impact claims.
