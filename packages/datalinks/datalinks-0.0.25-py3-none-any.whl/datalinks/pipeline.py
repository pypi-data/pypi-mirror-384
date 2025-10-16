from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Mapping, Any, List, ClassVar, Optional
import logging

import caseutil

_logger = logging.getLogger(__name__)


class StepTypes(Enum):
    """
    Represents different types of processing steps for data manipulation.

    This class enumerates various distinct processing types that can be
    used in DataLinks workflows. Each enumeration value signifies a specific
    stage in the broader data-processing pipeline.
    """
    TABLE = "table"
    ROWS = "rows"
    NORMALIZE = "normalise"
    VALIDATE = "validate"
    REVERSE_GEO = "reverseGeo"


class NormalizeModes(Enum):
    """
    Enumeration for normalization modes.

    This class represents different modes of data normalization
    used in the 'normalize' step. It provides three options
    for normalization: 'embeddings' for embedding-level normalization,
    'all-in-one' for holistic normalization, and 'field-by-field'
    for column-wise normalization.

    :ivar EMBEDDINGS: Mode for normalizing data on an embedding level.
    :type EMBEDDINGS: str
    :ivar ALL_IN_ONE: Mode for normalizing data holistically, treating
        the entire dataset as a single entity.
    :type ALL_IN_ONE: str
    :ivar FIELD_BY_FIELD: Mode for normalizing data column-by-column,
        focusing on individual fields independently.
    :type FIELD_BY_FIELD: str
    """
    EMBEDDINGS = "embeddings"
    ALL_IN_ONE = "all-in-one"
    FIELD_BY_FIELD = "field-by-field"


class ValidateModes(Enum):
    """
    Enumeration class that defines various validation modes.

    This class is designed to specify the modes of operation for the 'validate'
    step. The predefined modes include validation by rows, regular
    expressions, and fields.

    :ivar ROWS: Validation mode that focuses on rows.
    :type ROWS: str
    :ivar REGEX: Validation mode that utilizes regular expressions.
    :type REGEX: str
    :ivar FIELDS: Validation mode that focuses on columns.
    :type FIELDS: str
    """
    ROWS = "rows"
    REGEX = "regex"
    FIELDS = "fields"


@dataclass
class BaseStep:
    """
    Represents the base step within DataLinks.

    This class serves as the foundational step structure for various
    implementations. It includes methods to transform its data
    representation into a dictionary format, custom-processed with specific
    rules for attributes of Enum type. It is primarily designed as a metaclass.

    :ivar step_type: The type of the step, categorized using `StepTypes`.
    :type step_type: ClassVar[StepTypes]
    """
    step_type: ClassVar[StepTypes]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["type"] = self.step_type.value
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value
        return {caseutil.to_camel(key): value for key,value in data.items()}

@dataclass
class LlmStep(BaseStep):
    """
    Common class for pipeline steps that rely on LLM inference.

    :ivar model: The name of the model to use in the step.
    :type model: str
    :ivar provider: The identifier of the provider to be used (ollama, openai, etc)
    :type provider: str
    """
    model: Optional[str]
    provider: Optional[str]

@dataclass
class InferenceStep(BaseStep):
    """
    Represents the 'infer' step in the DataLinks workflow.

    :ivar derive_from: The identifier of the source field used in the inference step.
    :type derive_from: str
    """
    derive_from: str

@dataclass
class ProcessUnstructured(LlmStep, InferenceStep):
    """
    Use this step to infer a table from unstructured data.

    :ivar helper_prompt: A string that stores an optional helper
        prompt or additional guiding context specific to the table
        inference step.
    :type helper_prompt: str
    """
    step_type: ClassVar[StepTypes] = StepTypes.TABLE
    helper_prompt: str = ""

@dataclass
class ProcessStructured(InferenceStep):
    """
    Use this step to extract data that is already in tabular format (eg.: CSV).
    """
    step_type: ClassVar[StepTypes] = StepTypes.ROWS

@dataclass
class ReverseGeo(InferenceStep):
    """
    Use this step to perform reverse geolocation based on the source field.
    """
    step_type: ClassVar[StepTypes] = StepTypes.REVERSE_GEO

@dataclass
class Normalize(LlmStep):
    """
    Use this step to attempt normalisation of the extracted column names. Table
    inference across different unstructured data blocks may result in different field names
    for the same information, hence the need to normalize the column names.

    Encapsulates the configuration necessary to perform the 'normalize' step.
    It specifies the desired target columns, the mode of normalisation, and includes optional
    helper prompts to provide further instructions or context.

    :ivar target_cols: A mapping of the desired column names to an optional
                       description used as context.
    :type target_cols: Mapping[str, Optional[str]]
    :ivar mode: Specifies the normalisation mode to be applied.
    :type mode: NormalizeModes
    :ivar helper_prompt: Optional helper text or prompt information.
    :type helper_prompt: str
    """
    step_type: ClassVar[StepTypes] = StepTypes.NORMALIZE
    target_cols: Mapping[str, Optional[str]]
    mode: NormalizeModes
    helper_prompt: str = ""

@dataclass
class Validate(LlmStep):
    """
    Use this step to add data validation to the inference pipeline.

    :ivar mode: Indicates the mode of validation to be applied.
    :type mode: ValidateModes
    :ivar columns: List containing the column names which are used for validation.
    :type columns: List[str]
    """
    step_type: ClassVar[StepTypes] = StepTypes.VALIDATE
    mode: ValidateModes
    columns: List[str]


class Pipeline:
    """
    Represents a collection of sequential steps. Holds and manages the
    sequence of steps used for ingesting and/or enhancing data.

    :ivar steps: A collection of steps to be executed in sequence.
    :type steps: tuple[BaseStep, ...]
    """
    def __init__(self, *steps: BaseStep):
        self.steps = steps

    def to_list(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.steps]
