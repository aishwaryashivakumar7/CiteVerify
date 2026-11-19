
import unittest

from backend.verification.verifier import verify_claim


class TestCiteVerify(unittest.TestCase):

    # Test 1: Valid scientific claim
    def test_valid_claim(self):

        result = verify_claim(
            claim="Machine learning is used in healthcare.",
            doi="10.1126/science.aaa8415"
        )

        self.assertIn(
            result["status"],
            [
                "SUPPORTED",
                "PARTIALLY SUPPORTED",
                "UNSUPPORTED",
                "CONTRADICTORY",
                "POTENTIALLY OUTDATED",
                "NEEDS REVIEW"
            ]
        )

        self.assertGreaterEqual(result["confidence"], 0)
        self.assertLessEqual(result["confidence"], 100)

    # Test 2: Empty claim
    def test_empty_claim(self):

        with self.assertRaises(ValueError):

            verify_claim(
                claim="",
                doi="10.1126/science.aaa8415"
            )

    # Test 3: Empty DOI
    def test_empty_doi(self):

        with self.assertRaises(ValueError):

            verify_claim(
                claim="Machine learning is used in healthcare.",
                doi=""
            )

    # Test 4: Invalid DOI
    def test_invalid_doi(self):

        result = verify_claim(
            claim="Machine learning is used in healthcare.",
            doi="invalid-doi"
        )

        self.assertEqual(
            result["status"],
            "NEEDS REVIEW"
        )

        self.assertTrue(result["review_required"])

    # Test 5: Check output structure
    def test_result_structure(self):

        result = verify_claim(
            claim="Machine learning is used in healthcare.",
            doi="10.1126/science.aaa8415"
        )

        required_fields = [
            "status",
            "confidence",
            "explanation",
            "evidence",
            "review_required",
            "paper_title",
            "doi",
            "publication_year"
        ]

        for field in required_fields:

            self.assertIn(field, result)


if __name__ == "__main__":

    print("\nCITEVERIFY AUTOMATED TESTING STARTED\n")

    unittest.main(verbosity=2)
