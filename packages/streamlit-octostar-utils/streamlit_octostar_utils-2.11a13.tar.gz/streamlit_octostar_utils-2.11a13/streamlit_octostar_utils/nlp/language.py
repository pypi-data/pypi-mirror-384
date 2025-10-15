import re
from typing import Optional

import py3langid as langid

from iso639 import Lang
from iso639.exceptions import InvalidLanguageValue

FLAIR_MODELS = {
    "en": "flair/ner-english-large",
    "es": "flair/ner-spanish-large",
    "de": "flair/ner-german-large",
    "nl": "flair/ner-dutch-large",
    "multi": "flair/ner-multi",                     # English, German, French, Spanish
    "multi-fast": "flair/ner-multi-fast",           # English, German, Dutch, Spanish
}

SPACY_MODELS = {
    "en": "en_core_web_sm",
    "es": "es_core_news_sm",
    "fr": "fr_core_news_sm",
    "de": "de_core_news_sm",
    "it": "it_core_news_sm"
}


def alpha2_to_language(alpha2: str) -> str:
    if not alpha2:
        raise ValueError("Language code must be a non-empty string.")
    return Lang(alpha2).name


def language_to_alpha2(language_name: str) -> str:
    if not language_name:
        raise ValueError("Language name must be a non-empty string.")

    name = re.sub(r'\b\w+', lambda m: m.group(0).capitalize(), language_name)
    return Lang(name).pt1


def detect_language(text, min_confidence=None):
    detector = langid.langid.LanguageIdentifier.from_pickled_model(
        langid.langid.MODEL_FILE, norm_probs=True
    )
    detected_lang, confidence = detector.classify(text)
    if min_confidence and confidence < min_confidence:
        return None, confidence
    detected_lang = alpha2_to_language(detected_lang)
    return detected_lang, confidence


def is_language_available(language: Optional[str], type: str) -> bool:
    if not language:
        return False

    try:
        lang_code = language_to_alpha2(language)

    except InvalidLanguageValue:
        lang_code = language

    match type:
        case "spacy":
            return SPACY_MODELS.get(lang_code, None) is not None

        case "flair":
            return FLAIR_MODELS.get(lang_code, None) is not None


def load_language_model(language, type):
    from flair.models import SequenceTagger
    from spacy_download import load_spacy

    match type:
        case "spacy":
            if is_language_available(language, "spacy"):
                model_name = SPACY_MODELS.get(language_to_alpha2(language), SPACY_MODELS["en"])
                return load_spacy(model_name)

            raise Exception(f"SpaCy model for language '{language}' is not available.")

        case "flair":
            if is_language_available(language, "flair"):
                model_name = FLAIR_MODELS.get(language, "flair/ner-multi")
                return SequenceTagger.load(model_name)

            raise Exception(f"Flair model for language '{language}' is not available.")
