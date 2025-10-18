from enum import Enum


class Metrics(Enum):
    LabelStageGroups = 'LabelStageGroups'
    TimePerTask = 'TimePerTask'
    AnnotationStatus = 'AnnotationStatus'
    AnswerDistribution = 'AnswerDistribution'
    ConsensusRanges = 'ConsensusRanges'
    AssetSize = 'AssetSize'


class OrganizationRoles(Enum):
    Member = 'member'
    Admin = 'admin'


class ProjectRoles(Enum):
    Manager = 'Manager'
    Labeler = 'Labeler'
    Reviewer = 'Reviewer'
    Lead = 'Lead'


class StorageProvider(Enum):
    AWS = 'AWS'
    GCP = 'GCP'
    AZURE = 'AZURE'


class StorageFileTypes(Enum):
    BRUSH = 'brushes'
    MEDICAL_BRUSH = 'medicalBrushes'
    ASSET = 'assets'
    EXPORT = 'exports'
    INSTRUCTION = 'instructions'


class ExportTypes(Enum):
    TASK = 'task'
    ISSUE = 'issue'


class ExportFormats(Enum):
    JSON = 'json'
    NDJSON = 'ndjson'

