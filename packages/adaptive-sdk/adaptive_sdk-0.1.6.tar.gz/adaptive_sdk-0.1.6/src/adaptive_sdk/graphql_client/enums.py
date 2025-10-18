from enum import Enum

class AbcampaignStatus(str, Enum):
    """@public"""
    WARMUP = 'WARMUP'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'
    CANCELLED = 'CANCELLED'

class AuthProviderKind(str, Enum):
    """@public"""
    OIDC = 'OIDC'

class BillingCycle(str, Enum):
    """@public"""
    YEARLY = 'YEARLY'

class CompletionGroupBy(str, Enum):
    """@public"""
    MODEL = 'MODEL'
    PROMPT = 'PROMPT'

class CompletionSource(str, Enum):
    """@public"""
    LIVE = 'LIVE'
    OFFLINE = 'OFFLINE'
    AUTOMATION = 'AUTOMATION'
    DATASET = 'DATASET'
    EVALUATION = 'EVALUATION'

class ComputePoolCapability(str, Enum):
    """@public"""
    INFERENCE = 'INFERENCE'
    JOB = 'JOB'

class DatasetKind(str, Enum):
    """@public"""
    PROMPT = 'PROMPT'
    PROMPT_COMPLETION = 'PROMPT_COMPLETION'
    PROMPT_COMPLETION_FEEDBACK = 'PROMPT_COMPLETION_FEEDBACK'
    PREFERENCE = 'PREFERENCE'

class DatasetSource(str, Enum):
    """@public"""
    UPLOADED = 'UPLOADED'
    GENERATED = 'GENERATED'
    GENERATING = 'GENERATING'
    FILTERED = 'FILTERED'

class DateBucketUnit(str, Enum):
    """@public"""
    HOUR = 'HOUR'
    DAY = 'DAY'
    WEEK = 'WEEK'
    MONTH = 'MONTH'
    QUARTER = 'QUARTER'
    YEAR = 'YEAR'
    NO_GROUP_BY_DATE = 'NO_GROUP_BY_DATE'

class ExternalModelProviderName(str, Enum):
    """@public"""
    AZURE = 'AZURE'
    OPEN_AI = 'OPEN_AI'
    GOOGLE = 'GOOGLE'
    ANTHROPIC = 'ANTHROPIC'
    NVIDIA = 'NVIDIA'

class FeedbackType(str, Enum):
    """@public"""
    DIRECT = 'DIRECT'
    COMPARISON = 'COMPARISON'

class GraderTypeEnum(str, Enum):
    """@public"""
    JUDGE = 'JUDGE'
    PREBUILT = 'PREBUILT'
    REMOTE = 'REMOTE'
    CUSTOM = 'CUSTOM'

class HarmonyStatus(str, Enum):
    """@public"""
    ONLINE = 'ONLINE'
    OFFLINE = 'OFFLINE'

class JobArtifactKind(str, Enum):
    """@public"""
    EVALUATION = 'EVALUATION'
    CUSTOM = 'CUSTOM'
    DATASET = 'DATASET'

class JobKind(str, Enum):
    """@public"""
    TRAINING = 'TRAINING'
    EVALUATION = 'EVALUATION'
    DATASET_GENERATION = 'DATASET_GENERATION'
    MODEL_CONVERSION = 'MODEL_CONVERSION'
    CUSTOM = 'CUSTOM'

class JobStatus(str, Enum):
    """@public"""
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELED = 'CANCELED'

class JobStatusOutput(str, Enum):
    """@public"""
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    DONE = 'DONE'
    CANCELLED = 'CANCELLED'
    ERROR = 'ERROR'

class JudgeCapability(str, Enum):
    """@public"""
    TRAINING = 'TRAINING'
    EVALUATION = 'EVALUATION'

class MetricAggregation(str, Enum):
    """@public"""
    AVERAGE = 'AVERAGE'
    SUM = 'SUM'
    COUNT = 'COUNT'

class MetricKind(str, Enum):
    """@public"""
    SCALAR = 'SCALAR'
    BOOL = 'BOOL'

class MetricScoringType(str, Enum):
    """@public"""
    HIGHER_IS_BETTER = 'HIGHER_IS_BETTER'
    LOWER_IS_BETTER = 'LOWER_IS_BETTER'

class ModelKindFilter(str, Enum):
    """@public"""
    Embedding = 'Embedding'
    Generation = 'Generation'

class ModelOnline(str, Enum):
    """@public"""
    ONLINE = 'ONLINE'
    PENDING = 'PENDING'
    OFFLINE = 'OFFLINE'
    ERROR = 'ERROR'

class ModelserviceStatus(str, Enum):
    """@public"""
    PENDING = 'PENDING'
    ONLINE = 'ONLINE'
    OFFLINE = 'OFFLINE'
    DETACHED = 'DETACHED'
    TURNED_OFF = 'TURNED_OFF'
    ERROR = 'ERROR'

class OpenAIModel(str, Enum):
    """@public"""
    GPT41 = 'GPT41'
    GPT4O = 'GPT4O'
    GPT4O_MINI = 'GPT4O_MINI'
    O1 = 'O1'
    O1_MINI = 'O1_MINI'
    O3_MINI = 'O3_MINI'
    O4_MINI = 'O4_MINI'
    O3 = 'O3'
    GPT4 = 'GPT4'
    GPT4_TURBO = 'GPT4_TURBO'
    GPT3_5_TURBO = 'GPT3_5_TURBO'
    GPT5 = 'GPT5'
    GPT5_MINI = 'GPT5_MINI'
    GPT5_NANO = 'GPT5_NANO'
    GPT41_MINI = 'GPT41_MINI'

class PrebuiltCriteriaKey(str, Enum):
    """@public"""
    FAITHFULNESS = 'FAITHFULNESS'
    ANSWER_RELEVANCY = 'ANSWER_RELEVANCY'
    CONTEXT_RELEVANCY = 'CONTEXT_RELEVANCY'

class Protocol(str, Enum):
    """@public"""
    HTTP = 'HTTP'

class ProviderName(str, Enum):
    """@public"""
    AZURE = 'AZURE'
    OPEN_AI = 'OPEN_AI'
    HARMONY = 'HARMONY'
    GOOGLE = 'GOOGLE'
    ANTHROPIC = 'ANTHROPIC'
    NVIDIA = 'NVIDIA'

class RemoteEnvStatus(str, Enum):
    """@public"""
    ONLINE = 'ONLINE'
    OFFLINE = 'OFFLINE'

class SelectionTypeInput(str, Enum):
    """@public"""
    ALL = 'ALL'
    RANDOM = 'RANDOM'
    LAST = 'LAST'

class SortDirection(str, Enum):
    """@public"""
    ASC = 'ASC'
    DESC = 'DESC'

class TimeseriesInterval(str, Enum):
    """@public"""
    HOUR = 'HOUR'
    DAY = 'DAY'
    WEEK = 'WEEK'
    MONTH = 'MONTH'
    QUARTER = 'QUARTER'
    YEAR = 'YEAR'
    MILLENNIUM = 'MILLENNIUM'

class UnitPosition(str, Enum):
    """@public"""
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'