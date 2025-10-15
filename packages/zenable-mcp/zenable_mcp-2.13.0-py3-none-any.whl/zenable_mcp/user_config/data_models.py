import logging
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

LOG = logging.getLogger(__name__)


class FindingType(str, Enum):
    bug = "bug"
    readability = "readability"
    performance = "performance"
    complexity = "complexity"
    security = "security"
    inconsistency = "inconsistency"
    accessibility = "accessibility"
    mistake = "mistake"


class CheckConfig(BaseModel):
    """
    Configuration for the check command.

    Parameters:
        patterns:
            List of patterns to include files for checking. Supports:
            - Exact filename matches (e.g., "main.py")
            - Glob patterns (e.g., "**/*.py", "src/**/*.js")
            When invoked as a hook, these patterns act as filters for files passed by the IDE.
        exclude_patterns:
            List of patterns to exclude files from checking. Supports:
            - Exact filename matches (e.g., "test.py")
            - Glob patterns (e.g., "**/test_*.py", "**/*.test.js")
    """

    model_config = ConfigDict(strict=True, extra="allow")

    patterns: list[str]
    exclude_patterns: list[str]


class CommentsConfig(BaseModel):
    """
    Configuration for controlling which comments are posted during reviews.

    Parameters:
        taking_a_look:
            Whether to post the "Taking a look" comment at the start of reviews.
            Default: True (comment is posted)
        no_findings:
            Whether to post the "Nice work" comment when no issues are found.
            Default: True (comment is posted)
    """

    model_config = ConfigDict(strict=True, extra="allow")

    taking_a_look: bool = True
    no_findings: bool = True


class PreflightConfig(BaseModel):
    """
    Configuration to optionally skip reviews before reviewing based on static checks.

    Parameters:
        enabled:
            Whether to enable the preflight feature. Default: False (disabled)
        max_changed_lines:
            The maximum total number of changed lines (additions + deletions) allowed
            before skipping the review. If not provided while enabled, the preflight will
            fail-open and allow reviews.
    """

    model_config = ConfigDict(strict=True, extra="allow")

    enabled: bool = False
    max_changed_lines: int = 2500


class FindingTypeConfig(BaseModel):
    """
    Configuration for controlling each finding type.
    """

    model_config = ConfigDict(strict=True, extra="allow")

    hide: bool


class PRQualityFilterConfig(BaseModel):
    """
    Configuration for controlling which PR quality dimensions are evaluated.
    """

    model_config = ConfigDict(strict=True, extra="allow")

    enabled: bool = False
    quality_threshold: float = Field(default=0.5, ge=0, le=1)


class PRReviewsConfig(BaseModel):
    """
    Configuration for pull request reviews.

    Parameters:
        skip_filenames:
            Set of patterns to skip files. Supports:
            - Exact filename matches (e.g., "package-lock.json")
            - Glob patterns (e.g., "**/*.rbi", "foo/**/*.pyc")
            - Negation patterns with ! prefix (e.g., "!keep-this.json")
            Note: When using negation patterns, order matters - the last matching
            pattern wins. Consider using a list in config files to preserve order.
        skip_branches:
            Regex of branch names to skip. You can use python regex to match the branch names.
        comments:
            Configuration for controlling which comments are posted during reviews.
        findings:
            Configuration for controlling each finding type.
    """

    model_config = ConfigDict(strict=True, extra="allow")

    skip_filenames: list[str]
    skip_branches: set[str]
    comments: Optional[CommentsConfig] = None
    findings: dict[FindingType, FindingTypeConfig]
    preflight: PreflightConfig
    pr_quality_filter: PRQualityFilterConfig


class UserConfig(BaseModel):
    """
    Main user configuration model.
    """

    model_config = ConfigDict(strict=True, extra="allow")

    pr_reviews: PRReviewsConfig
    check: Optional[CheckConfig] = None


### Models for parsing ###


def ensure_findingtype_config(values: dict[str, Any]) -> dict[str, Any]:
    """
    Cast the findings keys to the right enum value case insensitive. If the enum is not found, it
    will be added to extra_fields.
    """
    # {'skip_filenames': ['file1.txt', 'file2.py', '**/*.md'], 'skip_branches': ['update'], 'findings': {'security': {'show': True}, 'performance': {'show': False}}}
    if "findings" not in values:
        return values

    findings = values["findings"]
    casted_findings = {}
    extra_findings = {}
    for key, value in findings.items():
        enum_key = key.lower()
        if enum_key in FindingType.__members__:
            casted_findings[FindingType(enum_key)] = value
            continue
        extra_findings[key] = value

    values["findings"] = casted_findings
    # If the key is not a valid FindingType, we can't add it to findings, but we can move it to
    # extra_findings and store it as an extra field.
    for key, value in extra_findings.items():
        values[f"extra_finding_{key}"] = value

    return values


### TOML models ###


class _CommentsTomlConfig(CommentsConfig):
    """
    Internal class modelling the representation of a comments config in a TOML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Everything is optional
    taking_a_look: Optional[bool] = None
    no_findings: Optional[bool] = None


class _CheckTomlConfig(CheckConfig):
    """
    Internal class modelling the representation of a check config in a TOML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Everything is optional
    patterns: Optional[list[str]] = None
    exclude_patterns: Optional[list[str]] = None


class _FindingTypeTomlConfig(FindingTypeConfig):
    """
    Internal class modelling the representation of a finding type config in a TOML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Everything is optional
    hide: Optional[bool] = None


class _PreflightTomlConfig(PreflightConfig):
    """
    Internal class modelling the representation of a size guard config in a TOML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Everything is optional
    enabled: Optional[bool] = None
    max_changed_lines: Optional[int] = None


class _PRQualityFilterTomlConfig(PRQualityFilterConfig):
    """
    Internal class modelling the representation of a PR quality filter config in a TOML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    enabled: Optional[bool] = None
    quality_threshold: Optional[float] = None


class _PRTomlConfig(PRReviewsConfig):
    """
    Internal class modelling the representation of a PR reviews config in a TOML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Right now is the same as UserConfig, but everything is optional
    skip_filenames: Optional[list[str]] = None
    skip_branches: Optional[set[str]] = None
    comments: Optional[_CommentsTomlConfig] = None
    findings: Optional[dict[FindingType, _FindingTypeTomlConfig]] = None
    preflight: Optional[_PreflightTomlConfig] = None
    pr_quality_filter: Optional[_PRQualityFilterTomlConfig] = None

    @model_validator(mode="before")
    def ensure_findings(cls, data: dict[str, Any]) -> dict[str, Any]:
        return ensure_findingtype_config(data)


class _UserTomlConfig(UserConfig):
    """
    Internal class modelling the representation of a user config in a TOML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Right now is the same as UserConfig, but everything is optional
    pr_reviews: Optional[_PRTomlConfig] = None
    check: Optional[_CheckTomlConfig] = None


### YAML models ###


class _CommentsYamlConfig(CommentsConfig):
    """
    Internal class modelling the representation of a comments config in a YAML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Everything is optional
    taking_a_look: Optional[bool] = None
    no_findings: Optional[bool] = None


class _CheckYamlConfig(CheckConfig):
    """
    Internal class modelling the representation of a check config in a YAML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Everything is optional
    patterns: Optional[list[str]] = None
    exclude_patterns: Optional[list[str]] = None


class _FindingTypeYamlConfig(FindingTypeConfig):
    """
    Internal class modelling the representation of a finding type config in a YAML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Everything is optional
    hide: Optional[bool] = None


class _PreflightYamlConfig(PreflightConfig):
    """
    Internal class modelling the representation of a size guard config in a YAML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Everything is optional
    enabled: Optional[bool] = None
    max_changed_lines: Optional[int] = None


class _PRQualityFilterYamlConfig(PRQualityFilterConfig):
    """
    Internal class modelling the representation of a PR quality filter config in a YAML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Everything is optional
    enabled: Optional[bool] = None
    quality_threshold: Optional[float] = None


class _PRYamlConfig(PRReviewsConfig):
    """
    Internal class modelling the representation of a PR reviews config in a YAML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Right now is the same as UserConfig, but everything is optional
    skip_filenames: Optional[list[str]] = None
    skip_branches: Optional[set[str]] = None
    comments: Optional[_CommentsYamlConfig] = None
    findings: Optional[dict[FindingType, _FindingTypeYamlConfig]] = None
    preflight: Optional[_PreflightYamlConfig] = None
    pr_quality_filter: Optional[_PRQualityFilterYamlConfig] = None

    @model_validator(mode="before")
    def ensure_findings(cls, data: Any) -> dict[str, Any]:
        return ensure_findingtype_config(data)


class _UserYamlConfig(UserConfig):
    """
    Internal class modelling the representation of a user config in a YAML file.
    """

    # Leave strict False so pydantic can cast from the parser types to this model types
    model_config = ConfigDict(strict=False, extra="allow")

    # Right now is the same as UserConfig, but everything is optional
    pr_reviews: Optional[_PRYamlConfig] = None
    check: Optional[_CheckYamlConfig] = None


try:
    _default_finding_type_config = FindingTypeConfig(
        hide=False,
    )
except ValidationError as e:
    LOG.exception("Failed to create default findings config.")
    raise e

try:
    # Make sure to update the corresponding user-facing documentation if this changes
    DEFAULT_PR_REVIEWS_CONFIG = PRReviewsConfig(
        skip_filenames=[
            "conda-lock.yml",
            "bun.lock",
            "go.mod",
            "requirements.txt",
            "uv.lock",
            ".terraform.lock.hcl",
            "Gemfile.lock",
            "package-lock.json",
            "yarn.lock",
            "composer.lock",
            "poetry.lock",
            "pdm.lock",
            "Cargo.lock",
            "go.sum",
            "Package.resolved",
            "Podfile.lock",
            "mix.lock",
            "*.ico",
            "*.jpeg",
            "*.jpg",
            "*.png",
            "*.svg",
        ],
        skip_branches=set(),
        comments=CommentsConfig(),
        findings={
            finding_type: _default_finding_type_config for finding_type in FindingType
        },
        preflight=PreflightConfig(),
        pr_quality_filter=PRQualityFilterConfig(),
    )
except ValidationError as e:
    LOG.exception("Failed to create default PR reviews config.")
    raise e

try:
    DEFAULT_CONFIG = UserConfig(pr_reviews=DEFAULT_PR_REVIEWS_CONFIG)
except ValidationError as e:
    LOG.exception("Failed to create default user config.")
    raise e
