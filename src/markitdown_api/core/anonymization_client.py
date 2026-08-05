"""The only module allowed to construct Presidio analyzer/anonymizer engines.

Scoped to Brazilian Portuguese (pt-BR) only: Presidio ships no built-in Portuguese
NLP model or Brazilian document recognizers, so both are configured explicitly here.
"""

from dataclasses import dataclass
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from validate_docbr import CNPJ, CPF

_LANGUAGE = "pt"
_SPACY_MODEL = "pt_core_news_lg"

_NLP_CONFIGURATION = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": _LANGUAGE, "model_name": _SPACY_MODEL}],
    "ner_model_configuration": {
        "model_to_presidio_entity_mapping": {
            "PER": "PERSON",
            "PERSON": "PERSON",
            "LOC": "LOCATION",
            "ORG": "ORGANIZATION",
            "MISC": "MISC",
        },
        "labels_to_ignore": ["ORGANIZATION", "MISC"],
    },
}


class _CpfRecognizer(PatternRecognizer):
    """Detects Brazilian CPF numbers, validated by their check digits."""

    PATTERNS = [Pattern("CPF (formatted)", r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", 0.4)]
    CONTEXT = ["cpf"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="CPF",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )
        self._validator = CPF()

    def validate_result(self, pattern_text: str) -> bool | None:
        return self._validator.validate(pattern_text)


class _CnpjRecognizer(PatternRecognizer):
    """Detects Brazilian CNPJ numbers, validated by their check digits."""

    PATTERNS = [
        Pattern("CNPJ (formatted)", r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", 0.4),
    ]
    CONTEXT = ["cnpj"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="CNPJ",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )
        self._validator = CNPJ()

    def validate_result(self, pattern_text: str) -> bool | None:
        return self._validator.validate(pattern_text)


class _RgRecognizer(PatternRecognizer):
    """Detects Brazilian RG (general registry) numbers.

    RG has no nationwide check-digit standard (each state issues its own format), so
    detection relies on format + surrounding context words rather than a checksum.
    """

    PATTERNS = [Pattern("RG (formatted)", r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dXx]\b", 0.2)]
    CONTEXT = ["rg", "identidade"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="RG",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )


class _BrPhoneRecognizer(PatternRecognizer):
    """Detects Brazilian landline/mobile phone numbers.

    Mobile numbers have an 8-digit local number prefixed by a leading `9`; landlines
    have a 7-digit local number that starts with a digit in `[2-5]`. Both patterns
    require non-digit boundaries so they don't match fragments of longer digit runs
    such as judicial process/case numbers.
    """

    PATTERNS = [
        Pattern(
            "BR mobile phone (formatted)",
            r"(?<!\d)(?:\+55[\s.-]?)?\(?[1-9]\d\)?[\s.-]?9[\s.-]?\d{4}[\s.-]?\d{4}(?!\d)",
            0.4,
        ),
        Pattern(
            "BR landline phone (formatted)",
            r"(?<!\d)(?:\+55[\s.-]?)?\(?[1-9]\d\)?[\s.-]?[2-5]\d{3}[\s.-]?\d{4}(?!\d)",
            0.3,
        ),
    ]
    CONTEXT = ["telefone", "celular", "contato"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="PHONE_NUMBER_BR",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )


@dataclass(slots=True, frozen=True)
class DetectedEntityInfo:
    entity_type: str
    start: int
    end: int
    score: float


@dataclass(slots=True, frozen=True)
class AnonymizedText:
    text: str
    entities: list[DetectedEntityInfo]


@dataclass(slots=True, frozen=True)
class _AnonymizationEngines:
    analyzer: AnalyzerEngine
    anonymizer: AnonymizerEngine


@lru_cache
def _get_engines() -> _AnonymizationEngines:
    """Build and cache the analyzer/anonymizer engines (NLP model load is expensive)."""
    nlp_engine = NlpEngineProvider(nlp_configuration=_NLP_CONFIGURATION).create_engine()

    registry = RecognizerRegistry(supported_languages=[_LANGUAGE])
    registry.load_predefined_recognizers(languages=[_LANGUAGE], nlp_engine=nlp_engine)
    # Drop the generic (non-Brazilian) phone recognizer: it overlaps and conflicts
    # with our BR-specific pattern instead of complementing it.
    registry.remove_recognizer("PhoneRecognizer")
    for recognizer in (
        _CpfRecognizer(),
        _CnpjRecognizer(),
        _RgRecognizer(),
        _BrPhoneRecognizer(),
    ):
        registry.add_recognizer(recognizer)

    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine, registry=registry, supported_languages=[_LANGUAGE]
    )
    return _AnonymizationEngines(analyzer=analyzer, anonymizer=AnonymizerEngine())


def analyze_and_anonymize(text: str) -> AnonymizedText:
    """Detect and redact PII in `text`, operating on raw character offsets.

    Because redaction is offset-based rather than a re-serialization of parsed
    content, this works unchanged for plain text, HTML, and Markdown alike: any
    surrounding markup is left untouched around the redacted spans.
    """
    if not text:
        return AnonymizedText(text=text, entities=[])

    engines = _get_engines()
    results = engines.analyzer.analyze(text=text, language=_LANGUAGE)
    anonymized = engines.anonymizer.anonymize(text=text, analyzer_results=results)

    entities = [
        DetectedEntityInfo(entity_type=r.entity_type, start=r.start, end=r.end, score=r.score)
        for r in results
    ]
    return AnonymizedText(text=anonymized.text, entities=entities)
