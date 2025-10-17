from textblob import TextBlob

def sentiment_score(text: str) -> str:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    if polarity > 0.1:
        return "Müsb?t ??"
    elif polarity < -0.1:
        return "M?nfi ??"
    else:
        return "Neytral ??"
