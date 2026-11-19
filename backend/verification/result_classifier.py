
VALID_STATUSES = [
    "SUPPORTED",
    "PARTIALLY SUPPORTED",
    "UNSUPPORTED",
    "CONTRADICTORY",
    "POTENTIALLY OUTDATED",
    "NEEDS REVIEW"
]


def classify_result(ai_result):

    if not isinstance(ai_result, dict):
        raise ValueError("AI result must be a dictionary")

    status = ai_result.get("status", "")

    status = str(status).strip().upper().replace("_", " ")

    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid verification status: {status}")

    confidence = ai_result.get("confidence", 0)

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        raise ValueError("Confidence must be a number")

    if not 0 <= confidence <= 100:
        raise ValueError("Confidence must be between 0 and 100")

    explanation = str(
        ai_result.get("explanation", "")
    ).strip()

    evidence = str(
        ai_result.get("evidence", "")
    ).strip()

    result = {
        "status": status,
        "confidence": confidence,
        "explanation": explanation,
        "evidence": evidence,
        "review_required": status == "NEEDS REVIEW"
    }

    return result


if __name__ == "__main__":

    sample_result = {
        "status": "NEEDS REVIEW",
        "confidence": 0,
        "explanation": "Human assessment is required.",
        "evidence": "Sample research abstract."
    }

    print(classify_result(sample_result))
