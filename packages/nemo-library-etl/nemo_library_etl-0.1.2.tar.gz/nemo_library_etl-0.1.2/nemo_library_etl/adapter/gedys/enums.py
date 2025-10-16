from enum import Enum


class GedysTransformStep(Enum):
    SENTIMENT = "10_sentiment_analysis"
    FLATTEN = "20_flatten"
    JOIN = "30_join"
