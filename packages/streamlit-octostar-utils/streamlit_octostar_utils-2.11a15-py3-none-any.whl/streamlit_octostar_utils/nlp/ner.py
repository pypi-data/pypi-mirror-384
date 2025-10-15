import itertools
import math
from typing import Optional, List, Tuple

from iso639.exceptions import InvalidLanguageValue
from pydantic import BaseModel, ConfigDict, Field
from collections import Counter

from presidio_analyzer import AnalyzerEngine, BatchAnalyzerEngine, RecognizerRegistry, AnalysisExplanation, \
    EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts, NlpEngineProvider
import streamlit as st
import nltk
import pandas as pd
from flair.data import Sentence
from flair.models import SequenceTagger

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.nlp.stemmers import Stemmer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.utils import get_stop_words

from .language import alpha2_to_language

BASE_ALLOWED_LABELS = ["PERSON", "ORG", "LOC", "NORP", "GPE", "PRODUCT", "DATE", "PHONE", "IP_ADDRESS", "EMAIL", "URL",
                       "CRYPTO", "IBAN", "CREDIT_CARD", "US_SSN", "US_DRIVER_LICENSE", "US_PASSPORT", "MEDICAL_LICENSE"]

PRESIDIO_TO_BASE_ALIASES = {
    "PHONE_NUMBER": "PHONE",
    "EMAIL_ADDRESS": "EMAIL",
    "IBAN_CODE": "IBAN",
    "DRIVER_LICENSE": "US_DRIVER_LICENSE",
    "US_DRIVER_LICENSE": "US_DRIVER_LICENSE",
    "US_DRIVERS_LICENSE": "US_DRIVER_LICENSE",
    "PASSPORT": "US_PASSPORT",
    "CREDIT_CARD": "CREDIT_CARD",
    "URL": "URL",
    "IP_ADDRESS": "IP_ADDRESS",
    "CRYPTO": "CRYPTO",
    "CRYPTO_WALLET": "CRYPTO",
    "CRYPTO_WALLET_ADDRESS": "CRYPTO",
    "DATE_TIME": "DATE",
    "LOCATION": "LOC",
    "ORGANIZATION": "ORG",
}

BASE_TO_RECOGNIZER_EXPANSIONS = {
    "ORG": ["ORG", "ORGANIZATION"],
    "LOC": ["LOC", "LOCATION"],
    "PHONE": ["PHONE", "PHONE_NUMBER"],
    "EMAIL": ["EMAIL", "EMAIL_ADDRESS"],
    "IBAN": ["IBAN", "IBAN_CODE"],
    "US_DRIVER_LICENSE": ["US_DRIVER_LICENSE", "US_DRIVERS_LICENSE", "DRIVER_LICENSE"],
    "US_PASSPORT": ["US_PASSPORT", "PASSPORT"],
    "DATE": ["DATE", "DATE_TIME"],
    "PERSON": ["PERSON"],
    "URL": ["URL"],
    "IP_ADDRESS": ["IP_ADDRESS"],
    "CRYPTO": ["CRYPTO", "CRYPTO_WALLET", "CRYPTO_WALLET_ADDRESS"],
    "CREDIT_CARD": ["CREDIT_CARD"],
    "US_SSN": ["US_SSN"],
    "MEDICAL_LICENSE": ["MEDICAL_LICENSE"],
    "NORP": ["NORP"],
    "GPE": ["GPE"],
    "PRODUCT": ["PRODUCT"],
}

BASE_TO_ONTONOTES_LABELMAP = {"PER": "PERSON"}


class FlairRecognizer(EntityRecognizer):
    ENTITIES = [
        "LOC",
        "PERSON",
        "ORG",
    ]

    DEFAULT_EXPLANATION = "Identified as {} by Flair's Named Entity Recognition"

    CHECK_LABEL_GROUPS = [
        ({"LOC"}, {"LOC", "LOCATION"}),
        ({"PERSON"}, {"PER", "PERSON"}),
        ({"ORG"}, {"ORG", "ORGANIZATION"}),
    ]

    PRESIDIO_EQUIVALENCES = {
        "PER": "PERSON",
        "LOC": "LOC",
        "ORG": "ORG"
    }

    def __init__(
            self,
            model: SequenceTagger = None,
            supported_language: str = "en",
            supported_entities: Optional[List[str]] = None,
            check_label_groups: Optional[Tuple[set, set]] = None,
    ):
        self.check_label_groups = (
            check_label_groups if check_label_groups else self.CHECK_LABEL_GROUPS
        )

        supported_entities = supported_entities if supported_entities else self.ENTITIES
        self.model = model

        super().__init__(
            supported_entities=supported_entities,
            supported_language=supported_language,
            name="Flair Analytics",
        )

    def load(self) -> None:
        pass

    def get_supported_entities(self) -> List[str]:
        return self.supported_entities

    def analyze(self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None) -> List[RecognizerResult]:
        results = []

        sentences = Sentence(text)
        self.model.predict(sentences)

        if not entities:
            entities = self.supported_entities

        for entity in entities:
            if entity not in self.supported_entities:
                continue

            for ent in sentences.get_spans("ner"):
                if not self.__check_label(
                        entity, ent.labels[0].value, self.check_label_groups
                ):
                    continue
                textual_explanation = self.DEFAULT_EXPLANATION.format(
                    ent.labels[0].value
                )
                explanation = self.build_flair_explanation(
                    round(ent.score, 2), textual_explanation
                )
                flair_result = self._convert_to_recognizer_result(ent, explanation)

                results.append(flair_result)

        return results

    def build_flair_explanation(self, original_score: float, explanation: str) -> AnalysisExplanation:
        explanation = AnalysisExplanation(
            recognizer=self.__class__.__name__,
            original_score=original_score,
            textual_explanation=explanation,
        )
        return explanation

    def _convert_to_recognizer_result(self, entity, explanation) -> RecognizerResult:
        entity_type = self.PRESIDIO_EQUIVALENCES.get(entity.tag, entity.tag)
        flair_score = round(entity.score, 2)

        flair_results = RecognizerResult(
            entity_type=entity_type,
            start=entity.start_position,
            end=entity.end_position,
            score=flair_score,
            analysis_explanation=explanation,
        )

        return flair_results

    @staticmethod
    def __check_label(
            entity: str, label: str, check_label_groups: Tuple[set, set]
    ) -> bool:
        return any(
            [entity in egrp and label in lgrp for egrp, lgrp in check_label_groups]
        )


def normalize_label(label: str) -> str:
    return PRESIDIO_TO_BASE_ALIASES.get(label, label)


def expand_entities_for_analyzer(entities_list):
    expanded = set()
    for e in entities_list:
        vals = BASE_TO_RECOGNIZER_EXPANSIONS.get(e, [e])
        for v in vals:
            expanded.add(v)
    return list(expanded)


def _sumy__get_best_sentences(sentences, rating, *args, **kwargs):
    from operator import attrgetter
    from sumy.summarizers._summarizer import SentenceInfo

    rate = rating
    if isinstance(rating, dict):
        assert not args and not kwargs
        rate = lambda s: rating[s]
    infos = (SentenceInfo(s, o, rate(s, *args, **kwargs)) for o, s in enumerate(sentences))
    infos = sorted(infos, key=attrgetter("rating"), reverse=True)
    return tuple((i.sentence, i.rating, i.order) for i in infos)


def _sumy__lsa_call(summarizer, document):
    summarizer._ensure_dependecies_installed()
    dictionary = summarizer._create_dictionary(document)
    if not dictionary:
        return ()
    matrix = summarizer._create_matrix(document, dictionary)
    matrix = summarizer._compute_term_frequency(matrix)
    from numpy.linalg import svd as singular_value_decomposition

    u, sigma, v = singular_value_decomposition(matrix, full_matrices=False)
    ranks = iter(summarizer._compute_ranks(sigma, v))
    return _sumy__get_best_sentences(document.sentences, lambda s: next(ranks))


def _sumy__luhn_call(summarizer, document):
    words = summarizer._get_significant_words(document.words)
    return _sumy__get_best_sentences(document.sentences, summarizer.rate_sentence, words)


def get_nltk_tokenizer(language: str) -> Tokenizer:
    try:
        nltk_lang = alpha2_to_language(language).lower()

    except InvalidLanguageValue:
        nltk_lang = language

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")

    return Tokenizer(nltk_lang)


class NERObject(BaseModel):
    name: str
    label: str
    score: float = 0.0
    start: int
    count: int
    context: str | None = None
    comentions: list[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")

    def __repr__(self):
        return f"NERObject(label={self.label},name={self.name})"


def postprocess_ner(entities: list[NERObject], whitelisted_labels=None, max_entities=None):
    if whitelisted_labels is not None:
        entities = [e for e in entities if e.label in whitelisted_labels]
    entities = sorted(entities, key=lambda x: x.name)
    final_entities = []
    for _, group in itertools.groupby(entities, key=lambda x: x.name):
        group = list(group)
        best_entity = max(group, key=lambda x: x.score * x.count)
        merged_data = {
            "name": best_entity.name,
            "label": best_entity.label,
            "score": best_entity.score,
            "context": best_entity.context,
            "count": sum(e.count for e in group),
            "start": best_entity.start,
        }
        all_fields = best_entity.model_fields.keys()
        for field in all_fields:
            if field in merged_data:
                continue
            values = [getattr(e, field, None) for e in group if getattr(e, field, None) is not None]
            if not values:
                continue
            if isinstance(values[0], list):
                merged_data[field] = list(set(itertools.chain.from_iterable(values or [])))
            else:
                merged_data[field] = getattr(best_entity, field, None)
        final_entities.append(NERObject(**merged_data))
    final_entities = sorted(final_entities, key=lambda x: x.score * x.count, reverse=True)
    if max_entities and len(final_entities) > max_entities:
        final_entities = final_entities[:max_entities]
    return final_entities


def build_presidio_analyzer(language: str, engine_type: str = "spacy", model=None) -> AnalyzerEngine:
    registry = RecognizerRegistry()

    if engine_type == "flair":
        flair_recognizer = FlairRecognizer(
            model=model,
            supported_language=language
        )
        registry.add_recognizer(flair_recognizer)

        default_registry = RecognizerRegistry()
        default_registry.load_predefined_recognizers(languages=[language])

        flair_handled_entities = {"PERSON", "LOC", "ORG"}

        for recognizer in default_registry.recognizers:
            recognizer_entities = set(recognizer.supported_entities) if hasattr(recognizer, 'supported_entities') else set()

            if recognizer_entities and recognizer_entities.issubset(flair_handled_entities):
                continue

            registry.add_recognizer(recognizer)

        return AnalyzerEngine(registry=registry)

    else:
        registry.load_predefined_recognizers(languages=[language])

        if model is None:
            raise ValueError("SpaCy model name must be provided")

        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": language, "model_name": model}],
        }

        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()

        return AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry
        )


def analyze_column_sample(column_values: pd.Series, analyzer: AnalyzerEngine, language: str,
                          entities: Optional[List[str]], score_threshold: float) -> Optional[str]:
    sample_values = column_values.dropna().head(50)

    if sample_values.empty:
        return None

    entity_counter = Counter()

    for value in sample_values:
        text = str(value).strip()

        if not text:
            continue

        results = analyzer.analyze(
            text=text,
            language=language,
            entities=(expand_entities_for_analyzer(entities) if entities else None)
        )

        for result in results:
            if result.score >= score_threshold:
                entity_counter[normalize_label(result.entity_type)] += 1

    if not entity_counter:
        return None

    most_common = entity_counter.most_common(1)[0]
    total_detections = sum(entity_counter.values())

    if most_common[1] > total_detections * 0.5:
        return most_common[0]

    return most_common[0] if entity_counter else None


def analyze_dataframe_optimized(df: pd.DataFrame, analyzer: AnalyzerEngine, language: str,
                                entities: Optional[List[str]] = None, score_threshold: float = 0.5) -> List[NERObject]:
    ner_objects = []

    for column_name in df.columns:
        entity_type = analyze_column_sample(
            df[column_name],
            analyzer,
            language,
            entities,
            score_threshold
        )

        if entity_type:
            for idx, value in df[column_name].dropna().items():
                text = str(value).strip()

                if text:
                    ner_objects.append(NERObject(
                        name=text[:100],
                        label=entity_type,
                        score=0.9,
                        start=0,
                        count=1,
                        context=text[:100]
                    ))

    return ner_objects


def compute_ner_presidio(
        text_or_df,
        language,
        analyzer,
        entities=None,
        score_threshold=0.5,
        context_width=150,
        with_comentions=True,
        with_context=True,
        batch_size=32,
        n_process=4
):
    if isinstance(text_or_df, pd.DataFrame):
        if len(text_or_df) >= 100:
            return analyze_dataframe_optimized(text_or_df, analyzer, language, entities, score_threshold)

        else:
            texts = []

            for col in text_or_df.columns:
                for idx, value in text_or_df[col].dropna().items():
                    text_value = str(value).strip()

                    if text_value:
                        texts.append(text_value)

            text = "\n".join(texts)

    elif isinstance(text_or_df, list):
        text = text_or_df
        batch_analyzer = BatchAnalyzerEngine(analyzer_engine=analyzer)

        results_generator = batch_analyzer.analyze_iterator(
            texts=text,
            language=language,
            batch_size=batch_size,
            n_process=n_process,
            entities=(expand_entities_for_analyzer(entities) if entities else None),
        )

        all_results = list(results_generator)
        ner_objects = []

        for text_item, results in zip(text, all_results):
            for result in results:
                if result.score >= score_threshold:
                    context_start = max(0, result.start - 30)
                    context_end = min(len(text_item), result.end + 30)
                    context = text_item[context_start:context_end] if with_context else None

                    ner_objects.append(NERObject(
                        name=text_item[result.start:result.end],
                        label=normalize_label(result.entity_type),
                        score=float(result.score),
                        start=int(result.start),
                        count=1,
                        context=context
                    ))

        return ner_objects

    else:
        text = text_or_df

    results = analyzer.analyze(
        text=text,
        language=language,
        entities=(expand_entities_for_analyzer(entities) if entities else None)
    )

    ner_objects = []

    for result in results:
        if result.score >= score_threshold:
            context_start = max(0, result.start - math.floor(context_width / 2))
            context_end = min(len(text), result.end + math.ceil(context_width / 2))
            context = text[context_start:context_end] if with_context else None

            ner_objects.append(NERObject(
                name=text[result.start:result.end],
                label=normalize_label(result.entity_type),
                score=float(result.score),
                start=int(result.start),
                count=1,
                context=context
            ))

    if with_comentions:
        for i in range(len(ner_objects)):
            entity = ner_objects[i]
            comentions = [
                ner_objects[j].name
                for j in range(len(ner_objects))
                if j != i and abs(ner_objects[j].start - entity.start) < math.ceil(context_width / 2)
            ]
            ner_objects[i].comentions = comentions

    return ner_objects


def get_extractive_summary(text, language, max_chars, fast=False, with_scores=False):
    tokenizer = get_nltk_tokenizer(language)
    stemmer = Stemmer(language)
    parser = PlaintextParser.from_string(text, tokenizer)
    if fast:
        summarizer = LuhnSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(language)
        scored_sentences = iter(_sumy__luhn_call(summarizer, parser.document))
    else:
        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(language)
        scored_sentences = iter(_sumy__lsa_call(summarizer, parser.document))
    summary = []
    summary_chars = 0
    summary_chars_penultimate = 0
    while summary_chars < max_chars:
        try:
            next_sentence = next(scored_sentences)
            summary.append(next_sentence)
            summary_chars_penultimate = summary_chars
            summary_chars += len(" " + next_sentence[0]._text)
        except StopIteration:
            break
    summary = sorted(summary, key=lambda x: x[2])
    summary = [(sentence[0]._text, sentence[1]) for sentence in summary]
    if summary_chars > max_chars:
        summary[-1] = (
            summary[-1][0][: max_chars - summary_chars_penultimate],
            summary[-1][1],
        )
    if not with_scores:
        summary = " ".join([s[0] for s in summary])
    else:
        min_score = min([s[1] for s in summary]) if summary else 0
        max_score = max([min_score] + [s[1] for s in summary])
        score_range = 1 if min_score == max_score else (max_score - min_score)
        summary = [(s[0], (s[1] - min_score) / score_range) for s in summary]
    return summary


def ner_pipe(
        text_or_df,
        language,
        model,
        engine_type="spacy",
        fast=False,
        compression_ratio="auto",
        with_scores=False,
        with_comentions=True,
        with_context=True,
        entities=None,
        score_threshold=0.5,
        batch_size=32,
        n_process=4
):
    if with_scores:
        raise NotImplementedError("with_scores functionality is not implemented yet")

    analyzer = build_presidio_analyzer(
        language=language,
        engine_type=engine_type,
        model=model,
    )

    if isinstance(text_or_df, pd.DataFrame):
        ner = compute_ner_presidio(
            text_or_df,
            language,
            analyzer,
            entities,
            score_threshold,
            with_comentions=with_comentions,
            with_context=with_context,
            batch_size=batch_size,
            n_process=n_process
        )
    else:
        text = text_or_df

        if compression_ratio == "auto":
            compression_ratio = max(1.0, len(text) / 15000) if fast else 1.0

        if compression_ratio > 1.0:
            sentences = get_extractive_summary(text, language, int(len(text) / compression_ratio), fast=fast,
                                               with_scores=True)
            text = " ".join([s[0] for s in sentences])

        ner = compute_ner_presidio(
            text,
            language,
            analyzer,
            entities,
            score_threshold,
            with_comentions=with_comentions,
            with_context=with_context,
            batch_size=batch_size,
            n_process=n_process
        )

    return ner


def get_ner_handler(
        language,
        model,
        engine_type="spacy",
        fast=False,
        entities=None,
        score_threshold=0.5,
        batch_size=32,
        n_process=4
):
    try:
        get_nltk_tokenizer(language)
    except LookupError:
        language = "en"

    return lambda text_or_df, compression_ratio="auto", with_scores=False, with_comentions=True, with_context=True: ner_pipe(
        text_or_df,
        language,
        model,
        engine_type,
        fast,
        compression_ratio,
        with_scores,
        with_comentions,
        with_context,
        entities,
        score_threshold,
        batch_size,
        n_process
    )


@st.cache_resource
def get_cached_ner_handler(language, model):
    return get_ner_handler(language, model)
