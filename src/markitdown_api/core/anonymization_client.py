"""The only module allowed to construct Presidio analyzer/anonymizer engines.

Scoped to Brazilian Portuguese (pt-BR) only: Presidio ships no built-in Portuguese
NLP model or Brazilian document recognizers, so both are configured explicitly here.
"""

import re
from dataclasses import dataclass
from functools import lru_cache

from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
    RecognizerResult,
)
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

_ADMIN_PREFIX_RE = re.compile(
    r"^(?:atividade|atividades|código|codigo|descrição|descricao|data|validade|emitido|"
    r"requerimento|lei|artigo|alvará|alvara|inscrição|inscricao|situação|situacao|"
    r"cadastro|contato|endereço|endereco|fone|tel|telefone|email|e-mail)\s*:\s*",
    re.IGNORECASE,
)

# Common Brazilian administrative and document false positives returned by generic spaCy NER
_SPACY_FALSE_POSITIVES = {
    "tel",
    "tel:",
    "telefone",
    "telefone:",
    "fone",
    "fone:",
    "fax",
    "fax:",
    "carga",
    "descarga",
    "armazéns",
    "armazens",
    "armazéns gerais",
    "armazens gerais",
    "mercadorias",
    "transporte",
    "logística",
    "logistica",
    "ind",
    "ind.",
    "com",
    "com.",
    "serviços",
    "servicos",
    "alvará",
    "alvara",
    "exceto",
    "nº",
    "n°",
    "no",
    "lei",
    "decreto",
    "portaria",
    "artigo",
    "art.",
    "validade",
    "abertura",
    "data",
    "vencimento",
    "emissão",
    "emissao",
    "cpf",
    "cnpj",
    "rg",
    "cep",
    "cnh",
    "ie",
    "im",
    "pis",
    "pasep",
    "prefeitura municipal",
    "prefeitura",
    "secretaria",
    "governo",
    "estado",
    "município",
    "municipio",
    "contato",
    "endereço",
    "endereco",
    "atividade",
    "descrição",
    "descricao",
    "observação",
    "observacao",
    "cadastro",
    "nome",
    "email",
    "e-mail",
}


class _CpfRecognizer(PatternRecognizer):
    """Detects Brazilian CPF numbers (formatted and unformatted), validated by checksum."""

    PATTERNS = [
        Pattern("CPF (formatted)", r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", 0.5),
        Pattern("CPF (unformatted)", r"(?<!\d)\d{11}(?!\d)", 0.2),
    ]
    CONTEXT = ["cpf", "cadastro de pessoas físicas", "documento", "titular"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="CPF",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )
        self._validator = CPF()

    def validate_result(self, pattern_text: str) -> bool | None:
        digits = "".join(c for c in pattern_text if c.isdigit())
        return self._validator.validate(digits)


class _CnpjRecognizer(PatternRecognizer):
    """Detects Brazilian CNPJ numbers (formatted and unformatted), validated by checksum."""

    PATTERNS = [
        Pattern("CNPJ (formatted)", r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", 0.5),
        Pattern("CNPJ (unformatted)", r"(?<!\d)\d{14}(?!\d)", 0.2),
    ]
    CONTEXT = ["cnpj", "cadastro nacional da pessoa jurídica", "empresa", "matriz", "filial"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="CNPJ",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )
        self._validator = CNPJ()

    def validate_result(self, pattern_text: str) -> bool | None:
        digits = "".join(c for c in pattern_text if c.isdigit())
        return self._validator.validate(digits)


class _RgRecognizer(PatternRecognizer):
    """Detects Brazilian RG (general registry) numbers."""

    PATTERNS = [Pattern("RG (formatted)", r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dXx]\b", 0.3)]
    CONTEXT = ["rg", "identidade", "registro geral", "ssp", "documento"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="RG",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )


class _BrPhoneRecognizer(PatternRecognizer):
    """Detects Brazilian landline/mobile phone numbers, toll-free numbers, and number lists."""

    PATTERNS = [
        Pattern(
            "BR phone with DDD",
            r"(?<!\d)(?:\+55[\s.-]?)?\(?[1-9]\d\)?[\s.-]?(?:9[\s.-]?\d{4}|\d{4})[\s.-]?\d{4}(?!\d)",
            0.6,
        ),
        Pattern(
            "BR toll-free / special phone",
            r"(?<!\d)(?:0800|0300|4004|3003)[\s.-]?\d{3,4}[\s.-]?\d{3,4}(?!\d)",
            0.7,
        ),
        Pattern(
            "BR local phone list item",
            r"(?<=[/\s,.-])(?:9\d{4}|\d{4})[-\s]?\d{4}(?!\d)",
            0.35,
        ),
    ]
    CONTEXT = [
        "telefone",
        "telefones",
        "celular",
        "celulares",
        "fone",
        "fones",
        "tel",
        "tels",
        "contato",
        "contatos",
        "whatsapp",
        "whats",
        "ramal",
        "fax",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="PHONE_NUMBER_BR",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )


class _CepRecognizer(PatternRecognizer):
    """Detects Brazilian Postal Codes (CEP)."""

    PATTERNS = [Pattern("CEP", r"\b\d{5}-?\d{3}\b", 0.4)]
    CONTEXT = [
        "cep",
        "código postal",
        "codigo postal",
        "endereço",
        "endereco",
        "logradouro",
        "bairro",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="CEP",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )


class _CompanyBrRecognizer(PatternRecognizer):
    """Detects Brazilian corporate legal entity names by legal suffixes and context."""

    _SUFFIXES = (
        r"(?:LTDA|EIRELI|S/?A|S\.A\.|M\.E\.|ME|EPP|E\.P\.P\.|MEI|M\.E\.I\.|EIRL|INC\.?|"
        r"LLC|SOCIEDADE\s+(?:AN[ÔO]NIMA|LIMITADA|SIMPLES)|COMPANHIA)"
    )
    _WORDS = r"[A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ0-9&.\'-]+"

    PATTERNS = [
        Pattern(
            "BR Company suffix",
            rf"\b{_WORDS}(?:[ \t]+{_WORDS})*[ \t]+{_SUFFIXES}\b",
            0.75,
        ),
    ]
    CONTEXT = [
        "razão social",
        "razao social",
        "nome empresarial",
        "denominação social",
        "denominacao social",
        "empresa",
        "contratada",
        "contratante",
        "cedente",
        "sacado",
        "favorecido",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="ORGANIZATION",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )


class _AddressBrRecognizer(PatternRecognizer):
    """Detects Brazilian street addresses with common roadway prefixes."""

    _PREFIXES = (
        r"(?:Rua|R\b\.?|Avenida|Av\b\.?|Alameda|Al\b\.?|Travessa|Tv\b\.?|Rodovia|Rod\b\.?|"
        r"Estrada|Estr\b\.?|Praça|Pça\b\.?|Largo|Via|Quadra|QD|Viela)"
    )
    _STREET_CHARS = r"[A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑa-záàâãéèêíïóôõöúçñ\d\s\'.\-,]+?"
    _NUMBER = r"(?:,\s*(?:nº|n°|n\.º|num|número|no\.?)?\s*\d+[^,\n\r]*)?"

    PATTERNS = [
        Pattern(
            "BR Street Address",
            rf"\b{_PREFIXES}\s+{_STREET_CHARS}{_NUMBER}(?=[,\n\r\-–]|$|\s*-\s*CEP)",
            0.6,
        ),
    ]
    CONTEXT = [
        "endereço",
        "endereco",
        "logradouro",
        "rua",
        "avenida",
        "bairro",
        "complemento",
        "localizado",
        "situado",
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="LOCATION",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )


class _CnjProcessRecognizer(PatternRecognizer):
    """Detects Brazilian CNJ Judicial Lawsuit/Process numbers."""

    PATTERNS = [
        Pattern("CNJ Process Number", r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b", 0.85),
    ]
    CONTEXT = ["processo", "autos", "cnj", "ação", "judicial", "vara", "tribunal"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="PROCESS_NUMBER_CNJ",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=_LANGUAGE,
        )


class _VehiclePlateBrRecognizer(PatternRecognizer):
    """Detects Brazilian vehicle license plates (Mercosul and legacy format)."""

    PATTERNS = [
        Pattern("Mercosul Plate", r"\b[A-Z]{3}[0-9][A-Z][0-9]{2}\b", 0.6),
        Pattern("Old BR Plate", r"\b[A-Z]{3}-\d{4}\b", 0.6),
    ]
    CONTEXT = ["placa", "veículo", "veiculo", "carro", "moto", "caminhão", "chassi", "renavam"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="VEHICLE_PLATE_BR",
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
        _CepRecognizer(),
        _CompanyBrRecognizer(),
        _AddressBrRecognizer(),
        _CnjProcessRecognizer(),
        _VehiclePlateBrRecognizer(),
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

    # Clean results: split multi-line merged entities, strip administrative labels,
    # and filter false positives
    filtered_results: list[RecognizerResult] = []
    for r in results:
        raw_span = text[r.start : r.end]
        current_offset = r.start
        for line in raw_span.split("\n"):
            line_len = len(line)
            stripped_line = line.strip()
            if stripped_line:
                lead_spaces = len(line) - len(line.lstrip())
                sub_start = current_offset + lead_spaces
                sub_end = sub_start + len(stripped_line)

                # Strip administrative labels if present at start of line
                prefix_match = _ADMIN_PREFIX_RE.match(stripped_line)
                if prefix_match:
                    prefix_len = len(prefix_match.group(0))
                    val_str = stripped_line[prefix_len:]
                    val_lead = len(val_str) - len(val_str.lstrip())
                    val = val_str.strip()
                    sub_start = sub_start + prefix_len + val_lead
                    sub_end = sub_start + len(val)
                    check_val = val.lower()
                else:
                    check_val = stripped_line.lower()

                if check_val not in _SPACY_FALSE_POSITIVES and len(check_val) > 1:
                    filtered_results.append(
                        RecognizerResult(
                            entity_type=r.entity_type,
                            start=sub_start,
                            end=sub_end,
                            score=r.score,
                        )
                    )
            current_offset += line_len + 1

    anonymized = engines.anonymizer.anonymize(text=text, analyzer_results=filtered_results)

    entities = [
        DetectedEntityInfo(entity_type=r.entity_type, start=r.start, end=r.end, score=r.score)
        for r in filtered_results
    ]
    return AnonymizedText(text=anonymized.text, entities=entities)
