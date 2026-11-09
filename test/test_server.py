import unittest

from server import create_app


class TestEmotionServer(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()

    def test_index_and_health(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Read between", response.data)

        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["ok"], True)

    def test_api_analyze(self):
        response = self.client.post(
            "/api/analyze",
            json={"text": "I am thrilled and so happy about this!"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["dominant_emotion"], "joy")
        self.assertIn("scores", body)
        self.assertEqual(set(body["scores"]), {"anger", "disgust", "fear", "joy", "sadness"})

    def test_api_requires_text(self):
        response = self.client.post("/api/analyze", json={})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["ok"])

    def test_api_rejects_long_text(self):
        response = self.client.post("/api/analyze", json={"text": "a" * 5001})
        self.assertEqual(response.status_code, 413)

    def test_legacy_text_endpoint(self):
        response = self.client.get(
            "/emotionDetector", query_string={"textToAnalyze": "I am really afraid."}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"dominant emotion is fear", response.data.lower())

    def test_legacy_json_endpoint(self):
        response = self.client.get(
            "/emotionDetector",
            query_string={"textToAnalyze": "I am furious", "format": "json"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["dominant_emotion"], "anger")

    def test_legacy_invalid_text(self):
        response = self.client.get("/emotionDetector", query_string={"textToAnalyze": ""})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
