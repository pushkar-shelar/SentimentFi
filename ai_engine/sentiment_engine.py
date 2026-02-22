"""
SentimentFi — AI Sentiment Engine
==================================
Uses HuggingFace transformers pipeline to analyze crypto-related text
and produce a normalized sentiment score between -1.0 and +1.0.
"""

_sentiment_pipeline = None

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"


def _get_pipeline():
    """Lazy-load the HuggingFace sentiment-analysis pipeline."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        from transformers import pipeline  # noqa: PLC0415
        _sentiment_pipeline = pipeline(  # type: ignore
            "sentiment-analysis",
            model=MODEL_NAME,
        )
    return _sentiment_pipeline


def analyze_sentiment(texts: list[str]) -> float:
    """
    Analyze a list of text strings and return an aggregated sentiment score.

    Returns:
        float: Aggregated sentiment score in range [-1.0, +1.0].
    """
    result = analyze_sentiment_detailed(texts)
    return result["score"]


def analyze_sentiment_detailed(texts: list[str]) -> dict:
    """
    Analyze a list of texts and return a full breakdown for transparency.

    Returns a dict with:
        score        : float in [-1.0, +1.0]
        confidence   : average model confidence (0.0 - 1.0)
        bullish_count: number of POSITIVE signals
        bearish_count: number of NEGATIVE signals
        model        : model name used
        breakdown    : list of {text, label, confidence, contribution}
    """
    if not texts:
        return {
            "score": 0.0,
            "confidence": 0.0,
            "bullish_count": 0,
            "bearish_count": 0,
            "model": MODEL_NAME,
            "breakdown": [],
        }

    pipe = _get_pipeline()

    try:
        results = pipe(texts, truncation=True, max_length=512)
    except Exception as e:
        print(f"[SentimentEngine] Error during analysis: {e}")
        return {
            "score": 0.0,
            "confidence": 0.0,
            "bullish_count": 0,
            "bearish_count": 0,
            "model": MODEL_NAME,
            "breakdown": [],
        }

    total_score = 0.0
    total_confidence = 0.0
    bullish = 0
    bearish = 0
    breakdown = []

    for text, result in zip(texts, results):
        label = result["label"]
        confidence = result["score"]
        contribution = confidence if label == "POSITIVE" else -confidence

        total_score += contribution
        total_confidence += confidence

        if label == "POSITIVE":
            bullish += 1
        else:
            bearish += 1

        breakdown.append({
            "text": text[:80] + "..." if len(text) > 80 else text,
            "label": label,
            "confidence": round(confidence, 4),
            "contribution": round(contribution, 4),
        })

    n = len(results)
    avg_score = max(-1.0, min(1.0, total_score / n))
    avg_confidence = total_confidence / n

    return {
        "score": round(avg_score, 6),
        "confidence": round(avg_confidence, 4),
        "bullish_count": bullish,
        "bearish_count": bearish,
        "model": MODEL_NAME,
        "breakdown": breakdown,
    }
