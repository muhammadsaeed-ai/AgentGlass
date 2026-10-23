import unittest

from agentglass import Redactor


class RedactorTests(unittest.TestCase):
    def test_redacts_sensitive_keys_nested(self):
        source = {"config": {"api_key": "top-secret", "region": "eu"}, "password": "pw"}
        result = Redactor().sanitize(source)
        self.assertEqual(result["config"]["api_key"], "[REDACTED]")
        self.assertEqual(result["config"]["region"], "eu")
        self.assertEqual(result["password"], "[REDACTED]")
        self.assertEqual(source["password"], "pw")


    def test_redacts_generic_token_and_jwt_fields(self):
        result = Redactor().sanitize({
            "token": "opaque-token-value",
            "id_token": "id-token-value",
            "api_token": "api-token-value",
            "jwt": "jwt-value",
            "token_count": 3,
            "tokenizer": "keep-nonsecret-metadata",
        })
        self.assertEqual(result["token"], "[REDACTED]")
        self.assertEqual(result["id_token"], "[REDACTED]")
        self.assertEqual(result["api_token"], "[REDACTED]")
        self.assertEqual(result["jwt"], "[REDACTED]")
        self.assertEqual(result["token_count"], "[REDACTED]")
        self.assertEqual(result["tokenizer"], "keep-nonsecret-metadata")

    def test_redacts_secret_patterns_and_email(self):
        result = Redactor().sanitize({
            "message": "contact dev@example.com; key sk-abcdefghijklmnop; auth Bearer abcdefghijklmnop",
        })
        self.assertNotIn("dev@example.com", result["message"])
        self.assertNotIn("sk-abcdefghijklmnop", result["message"])
        self.assertNotIn("Bearer abcdefghijklmnop", result["message"])
        self.assertGreaterEqual(result["message"].count("[REDACTED]"), 3)

    def test_bounds_long_strings_and_collections(self):
        redactor = Redactor(max_string_length=32, max_items=2)
        self.assertIn("[TRUNCATED]", redactor.sanitize("x" * 100))
        self.assertEqual(redactor.sanitize([1, 2, 3]), [1, 2, "[TRUNCATED 1 ITEMS]"])

    def test_arbitrary_objects_are_not_repr_serialized(self):
        class Risky:
            def __repr__(self):
                return "secret=do-not-leak"
        self.assertEqual(Redactor().sanitize(Risky()), "[UNSUPPORTED_TYPE:Risky]")


if __name__ == "__main__":
    unittest.main()
