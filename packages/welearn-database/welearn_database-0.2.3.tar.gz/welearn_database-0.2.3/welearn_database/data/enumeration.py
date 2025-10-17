from enum import Enum, auto, StrEnum


class Step(Enum):
    URL_RETRIEVED = "url_retrieved"
    DOCUMENT_SCRAPED = "document_scraped"
    DOCUMENT_VECTORIZED = "document_vectorized"
    DOCUMENT_CLASSIFIED_SDG = "document_classified_sdg"
    DOCUMENT_CLASSIFIED_NON_SDG = "document_classified_non_sdg"
    DOCUMENT_KEYWORDS_EXTRACTED = "document_with_keywords"
    DOCUMENT_IN_QDRANT = "document_in_qdrant"
    DOCUMENT_IS_INVALID = "document_is_invalid"
    KEPT_FOR_TRACE = "kept_for_trace"
    DOCUMENT_IS_IRRETRIEVABLE = "document_is_irretrievable"

class Counter(Enum):
    HIT = auto()

class DbSchemaEnum(StrEnum):
    GRAFANA = auto()
    AGENT_RELATED = auto()
    CORPUS_RELATED = auto()
    DOCUMENT_RELATED = auto()
    USER_RELATED = auto()

class ContextType(StrEnum):
    INTRODUCTION = auto()
    TARGET = auto()
    SUBJECT = auto()