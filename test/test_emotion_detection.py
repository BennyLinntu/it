import unittest

from EmotionDetection.emotion_detection import EMOTIONS, emotion_detector


class TestEmotionDetection(unittest.TestCase):
    def test_original_capstone_examples(self):
        cases = {
            "I am glad this happened": "joy",
            "I am really mad about this": "anger",
            "I feel disgusted just hearing about this": "disgust",
            "I am so sad about this": "sadness",
            "I am really afraid that this will happen": "fear",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(
                    emotion_detector(text)["dominant_emotion"], expected
                )

    def test_scores_form_a_distribution(self):
        result = emotion_detector(
            "I am happy and excited, but also a little nervous."
        )
        self.assertEqual(set(EMOTIONS), {key for key in EMOTIONS})
        self.assertAlmostEqual(sum(result[emotion] for emotion in EMOTIONS), 1.0, 3)
        self.assertEqual(result["dominant_emotion"], "joy")
        self.assertGreater(result["confidence"], 0)

    def test_neutral_text_has_zero_scores(self):
        result = emotion_detector("The meeting starts at noon in room 4.")
        self.assertEqual(result["dominant_emotion"], "neutral")
        self.assertEqual(result["confidence"], 0)
        self.assertTrue(all(result[emotion] == 0 for emotion in EMOTIONS))

    def test_empty_text_is_invalid(self):
        result = emotion_detector("   ")
        self.assertIsNone(result["dominant_emotion"])
        self.assertTrue(all(result[emotion] is None for emotion in EMOTIONS))

    def test_negation_reduces_positive_signal(self):
        positive = emotion_detector("I am happy.")
        negated = emotion_detector("I am not happy.")
        self.assertEqual(positive["dominant_emotion"], "joy")
        self.assertNotEqual(negated["dominant_emotion"], "joy")

    def test_intensifier_increases_confidence(self):
        plain = emotion_detector("I am angry.")
        intense = emotion_detector("I am extremely furious.")
        self.assertEqual(intense["dominant_emotion"], "anger")
        self.assertGreaterEqual(intense["confidence"], plain["confidence"])


if __name__ == "__main__":
    unittest.main()
