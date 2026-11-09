"""Offline, lexicon-based emotion detection.

The original capstone called a hosted Watson endpoint. That service is no longer
reliable, so this module keeps the same public contract but scores text locally.
"""

from __future__ import annotations

import re
from collections import defaultdict

EMOTIONS = ("anger", "disgust", "fear", "joy", "sadness")

LEXICON = {
    "anger": {
        "angry", "anger", "mad", "furious", "rage", "hate", "hated", "annoyed",
        "annoying", "irritated", "irritating", "frustrated", "frustrating",
        "hostile", "outraged", "bitter", "resent", "resentful", "offended",
        "insulted", "betrayed", "unfair", "stupid", "idiot", "damn",
    },
    "disgust": {
        "disgusted", "disgusting", "disgust", "gross", "revolting", "nasty",
        "sickening", "repulsive", "awful", "vile", "creepy", "yuck", "yucky",
        "horrible", "appalling", "shameful", "dirty", "rotten", "putrid",
    },
    "fear": {
        "afraid", "scared", "scary", "fear", "fearful", "terrified", "terrifying",
        "anxious", "anxiety", "worried", "worry", "nervous", "panic", "panicked",
        "dread", "dreading", "horrified", "uneasy", "threatened", "unsafe",
        "danger", "dangerous", "frightened", "frightening",
    },
    "joy": {
        "happy", "happiness", "glad", "joy", "joyful", "delighted", "delightful",
        "excited", "exciting", "love", "loved", "lovely", "wonderful", "great",
        "amazing", "fantastic", "cheerful", "pleased", "thrilled", "smile",
        "smiling", "fun", "enjoy", "enjoyed", "enjoyable", "awesome", "brilliant",
        "perfect", "beautiful", "grateful", "thankful", "proud",
    },
    "sadness": {
        "sad", "sadness", "unhappy", "depressed", "depressing", "miserable",
        "cry", "crying", "cried", "heartbroken", "disappointed",
        "disappointing", "lonely", "grief", "grieving", "sorrow", "upset",
        "gloomy", "hurt", "hopeless", "empty", "lost", "regret", "regretful",
    },
}

NEGATIONS = {
    "not", "never", "no", "hardly", "barely", "isn't", "isnt", "wasn't",
    "wasnt", "don't", "dont", "doesn't", "doesnt", "didn't", "didnt", "can't",
    "cant", "couldn't", "couldnt", "wouldn't", "wouldnt", "shouldn't",
    "shouldnt", "ain't", "aint", "without",
}

INTENSIFIERS = {
    "very", "really", "so", "extremely", "incredibly", "super", "deeply",
    "totally", "absolutely", "utterly", "completely", "highly", "truly",
}

DIMINISHERS = {
    "slightly", "somewhat", "mildly", "barely", "kind", "sort", "little",
    "bit", "fairly", "rather",
}

WORD_RE = re.compile(r"[a-zA-Z]+(?:'[a-zA-Z]+)?")

EMOTION_EMOJI = {
    "anger": "😠",
    "disgust": "🤢",
    "fear": "😨",
    "joy": "😄",
    "sadness": "😢",
    "neutral": "😐",
}


def _empty_result(dominant=None):
    result = {emotion: None if dominant is None else 0.0 for emotion in EMOTIONS}
    result["dominant_emotion"] = dominant
    return result


def _tokenize(text):
    return [token.lower() for token in WORD_RE.findall(text)]


def _intensity_for(previous_tokens):
    multiplier = 1.0
    for token in previous_tokens[-2:]:
        if token in INTENSIFIERS:
            multiplier *= 1.55
        elif token in DIMINISHERS:
            multiplier *= 0.55
    return multiplier


def emotion_detector(text_to_analyze):
    """Return normalized scores and the dominant emotion.

    The return shape matches the original project: five emotion keys plus
    ``dominant_emotion``. ``confidence`` and ``word_count`` are additive.
    """
    if not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
        return _empty_result()

    tokens = _tokenize(text_to_analyze)
    raw = defaultdict(float)
    negate_next = 0

    for index, token in enumerate(tokens):
        if token in NEGATIONS:
            negate_next = 2
            continue

        for emotion, words in LEXICON.items():
            if token not in words:
                continue

            weight = 1.0 + min(len(token), 10) / 25
            weight *= _intensity_for(tokens[max(0, index - 2):index])
            if negate_next > 0:
                weight *= -0.8
            raw[emotion] += weight
            break

        if negate_next > 0:
            negate_next -= 1

    positive = {emotion: max(0.0, raw.get(emotion, 0.0)) for emotion in EMOTIONS}
    total = sum(positive.values())

    if total <= 0:
        result = {emotion: 0.0 for emotion in EMOTIONS}
        result.update({
            "dominant_emotion": "neutral",
            "confidence": 0.0,
            "word_count": len(tokens),
            "emoji": EMOTION_EMOJI["neutral"],
        })
        return result

    scores = {
        emotion: round(score / total, 4) for emotion, score in positive.items()
    }
    dominant = max(scores, key=scores.get)

    result = {emotion: scores[emotion] for emotion in EMOTIONS}
    result.update({
        "dominant_emotion": dominant,
        "confidence": scores[dominant],
        "word_count": len(tokens),
        "emoji": EMOTION_EMOJI[dominant],
    })
    return result
