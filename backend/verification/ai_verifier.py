
import requests
import json


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

VALID_STATUSES = [
    "SUPPORTED",
    "PARTIALLY SUPPORTED",
    "UNSUPPORTED",
    "CONTRADICTORY",
    "POTENTIALLY OUTDATED",
    "NEEDS REVIEW"
]


def verify_with_ai(prompt, source_evidence):

    print("CITEVERIFY: AI VERIFICATION STARTED")

    if not source_evidence or not source_evidence.strip():
        raise ValueError("Source evidence cannot be empty.")

    strict_instructions = """

IMPORTANT VERIFICATION RULES:

1. Use ONLY the research evidence supplied in the prompt.
2. Never introduce outside facts or examples.
3. Do not invent studies, statistics or medical applications.
4. Every evidence quotation must be copied exactly
   from the supplied research evidence.
5. If the evidence does not establish the claim,
   do not mark it as SUPPORTED.
6. If evidence is insufficient, choose NEEDS REVIEW.
7. Confidence must reflect the strength of the evidence,
   not how certain you sound.

Return valid JSON only.

Use this exact structure:

{
    "status": "NEEDS REVIEW",
    "confidence": 0,
    "explanation": "Explanation based only on the evidence.",
    "evidence": [
        "Exact quotation copied from the research evidence."
    ]
}

Allowed statuses:
SUPPORTED,
PARTIALLY SUPPORTED,
UNSUPPORTED,
CONTRADICTORY,
POTENTIALLY OUTDATED,
NEEDS REVIEW
"""

    final_prompt = prompt + strict_instructions

    payload = {
        "model": MODEL_NAME,
        "prompt": final_prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        response_data = response.json()

        ai_response = response_data.get("response", "")

        if not ai_response:
            raise ValueError("AI returned an empty response.")

        result = json.loads(ai_response)

        # Validate required fields
        required_fields = [
            "status",
            "confidence",
            "explanation",
            "evidence"
        ]

        for field in required_fields:

            if field not in result:
                raise ValueError(
                    f"Missing AI response field: {field}"
                )

        # Validate status
        status = str(result["status"]).strip().upper().replace("_", " ")

        if status not in [
            item.replace("_", " ")
            for item in VALID_STATUSES
        ]:
            raise ValueError("AI returned an invalid status.")

        # Validate confidence
        confidence = float(result["confidence"])

        if not 0 <= confidence <= 100:
            raise ValueError("Invalid confidence value.")

        # Normalize evidence into a list
        evidence_quotes = result["evidence"]

        if isinstance(evidence_quotes, str):
            evidence_quotes = [evidence_quotes]

        if not isinstance(evidence_quotes, list):
            raise ValueError("Invalid evidence format.")

        if not all(
            isinstance(quote, str)
            for quote in evidence_quotes
        ):
            raise ValueError("Evidence quotations must be text.")

        evidence_quotes = [
            quote.strip()
            for quote in evidence_quotes
            if quote.strip()
        ]

        # Verify every quotation against original evidence
        for quote in evidence_quotes:

            if quote not in source_evidence:

                print(
                    "CITEVERIFY: UNVERIFIED AI EVIDENCE DETECTED"
                )

                return {
                    "status": "NEEDS REVIEW",
                    "confidence": 0,
                    "explanation": (
                        "The AI generated an evidence quotation "
                        "that could not be matched exactly to "
                        "the original research text."
                    ),
                    "evidence": ""
                }

        # Standardize result for result_classifier.py
        final_result = {
            "status": status,
            "confidence": confidence,
            "explanation": str(result["explanation"]).strip(),
            "evidence": "\n\n".join(evidence_quotes)
        }

        print("CITEVERIFY: AI RESPONSE VALIDATED")

        return final_result

    except requests.exceptions.RequestException as error:

        raise RuntimeError(
            f"Could not connect to Ollama: {error}"
        )

    except json.JSONDecodeError:

        raise ValueError("AI returned invalid JSON.")

    except (TypeError, ValueError) as error:

        raise ValueError(
            f"Invalid AI verification response: {error}"
        )


# --------------------------------------------------
# Test AI verifier
# --------------------------------------------------

if __name__ == "__main__":

    sample_evidence = (
        "Machine learning methods are used in health "
        "care for evidence-based decision-making."
    )

    sample_prompt = """
    SCIENTIFIC CLAIM:
    Machine learning is used in healthcare.

    RESEARCH EVIDENCE:
    Machine learning methods are used in health
    care for evidence-based decision-making.

    Determine whether the evidence supports the claim.
    """

    try:

        result = verify_with_ai(
            sample_prompt,
            sample_evidence
        )

        print("\nAI VERIFICATION RESULT:")

        print(
            json.dumps(
                result,
                indent=4
            )
        )

    except (RuntimeError, ValueError) as error:

        print("\nERROR:", error)
