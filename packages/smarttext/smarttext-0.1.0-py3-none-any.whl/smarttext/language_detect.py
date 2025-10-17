from langdetect import detect

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        langs = {
            "en": "Ingilis dili",
            "az": "Az?rbaycan dili",
            "ru": "Rus dili",
            "tr": "Türk dili",
            "fr": "Fransiz dili"
        }
        return langs.get(lang, lang)
    except:
        return "T?yin edil? bilm?di"
