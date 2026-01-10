from snownlp import SnowNLP

def sentiment_score_chinese(text: str) -> float:
    """
    Calculates sentiment score for Chinese text using SnowNLP.
    Returns a float between 0 (negative) and 1 (positive).
    """
    if not text:
        return 0.5 # Neutral
        
    try:
        s = SnowNLP(text)
        return s.sentiments
    except Exception as e:
        print(f"Error calculating sentiment: {e}")
        return 0.5
