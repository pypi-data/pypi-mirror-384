from typing import Mapping, TypedDict
import re
from commitizen import defaults
from commitizen.config.base_config import BaseConfig
from commitizen.cz.base import BaseCommitizen
from commitizen.cz.utils import multiple_line_breaker, required_validator
from commitizen.question import CzQuestion, Choice
from commitizen.cz.exceptions import CzException

__all__ = ["CustomConventionalCommitsCz"]


def _parse_subject(text: str) -> str:
    return required_validator(text.strip(".").strip(), msg="Subject is required.")


DEFAULT_PREFIX_CHOICES: dict[str, Choice] = {
    "fix": {
        "value": "fix",
        "name": "fix: A bug fix. Correlates with PATCH in SemVer",
        "key": "x",
    },
    "feat": {
        "value": "feat",
        "name": "feat: A new feature. Correlates with MINOR in SemVer",
        "key": "f",
    },
    "docs": {
        "value": "docs",
        "name": "docs: Documentation only changes",
        "key": "d",
    },
    "style": {
        "value": "style",
        "name": "style: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)",
        "key": "s",
    },
    "refactor": {
        "value": "refactor",
        "name": "refactor: A code change that neither fixes a bug nor adds a feature",
        "key": "r",
    },
    "perf": {
        "value": "perf",
        "name": "perf: A code change that improves performance",
        "key": "p",
    },
    "test": {
        "value": "test",
        "name": "test: Adding missing or correcting existing tests",
        "key": "t",
    },
    "build": {
        "value": "build",
        "name": "build: Changes that affect the build system or external dependencies (example scopes: pip, docker, npm)",
        "key": "b",
    },
    "ci": {
        "value": "ci",
        "name": "ci: Changes to CI configuration files and scripts (example scopes: GitLabCI)",
        "key": "c",
    },
}


class ConventionalCommitsAnswers(TypedDict):
    prefix: str
    scope: str
    subject: str
    body: str
    footer: str
    is_breaking_change: bool


class CustomConventionalCommitsCz(BaseCommitizen):
    bump_pattern = defaults.BUMP_PATTERN
    bump_map = {
        r"^.+!$": defaults.MAJOR,
        r"^BREAKING[\-\ ]CHANGE": defaults.MAJOR,
        r"^feat": defaults.MINOR,
        r"^fix": defaults.PATCH,
        r"^refactor": defaults.PATCH,
        r"^perf": defaults.PATCH,
    }
    bump_map_major_version_zero = {
        r"^.+!$": defaults.MINOR,
        r"^BREAKING[\-\ ]CHANGE": defaults.MINOR,
        r"^feat": defaults.MINOR,
        r"^fix": defaults.PATCH,
        r"^refactor": defaults.PATCH,
        r"^perf": defaults.PATCH,
    }
    change_type_map = {
        "feat": "Feat",
        "fix": "Fix",
        "refactor": "Refactor",
        "perf": "Perf",
    }
    changelog_pattern = defaults.BUMP_PATTERN

    def __init__(self, config: BaseConfig) -> None:
        super().__init__(config)
        self.scope_pattern: str = self.config.settings.get("scope_pattern", r"[^()\r\n]*")
        self.scope_optional: bool = self.config.settings.get("scope_optional", True)
        self.change_types: list[str] = self.config.settings.get(
            "change_types",
            [
                "build",
                "bump",
                "chore",
                "ci",
                "docs",
                "feat",
                "fix",
                "perf",
                "refactor",
                "revert",
                "style",
                "test",
            ],
        )
        self.commit_parser = (
            r"^((?P<change_type>"
            + (r"|".join(self.change_types))
            + r")(?:\((?P<scope>"
            + self.scope_pattern
            + r")\)|\()?(?P<breaking>!)?|\w+!):\s(?P<message>.*)?"
        )

    def parse_scope(self, text: str) -> str:
        scope = re.match(self.scope_pattern, text.strip())
        if not scope:
            raise CzException(f"Scope must match pattern {self.schema_pattern}")
        return scope.group(0)

    def questions(self) -> list[CzQuestion]:
        return [
            {
                "type": "list",
                "name": "prefix",
                "message": "Select the type of change you are committing",
                "choices": [
                    DEFAULT_PREFIX_CHOICES.get(
                        change_type,
                        {
                            "value": change_type,
                            "name": change_type,
                            "key": change_type,
                        },
                    )
                    for change_type in self.change_types
                ],
            },
            {
                "type": "input",
                "name": "scope",
                "message": ("What is the scope of this change? (class or file name): (press [enter] to skip)\n"),
                "filter": self.parse_scope,
            },
            {
                "type": "input",
                "name": "subject",
                "filter": _parse_subject,
                "message": ("Write a short and imperative summary of the code changes: (lower case and no period)\n"),
            },
            {
                "type": "input",
                "name": "body",
                "message": (
                    "Provide additional contextual information about the code changes: (press [enter] to skip)\n"
                ),
                "filter": multiple_line_breaker,
            },
            {
                "type": "confirm",
                "name": "is_breaking_change",
                "message": "Is this a BREAKING CHANGE? Correlates with MAJOR in SemVer",
                "default": False,
            },
            {
                "type": "input",
                "name": "footer",
                "message": (
                    "Footer. Information about Breaking Changes and "
                    "reference issues that this commit closes: (press [enter] to skip)\n"
                ),
            },
        ]

    def message(self, answers: Mapping[str, str]) -> str:
        prefix = answers["prefix"]
        scope = answers["scope"]
        subject = answers["subject"]
        body = answers["body"]
        footer = answers["footer"]
        is_breaking_change = answers["is_breaking_change"]

        if scope:
            scope = f"({scope})"
        if body:
            body = f"\n\n{body}"
        if is_breaking_change:
            footer = f"BREAKING CHANGE: {footer}"
        if footer:
            footer = f"\n\n{footer}"

        return f"{prefix}{scope}: {subject}{body}{footer}"

    def example(self) -> str:
        return "fix: correct minor typos in code\n\nsee the issue for details on the typos fixed\n\ncloses issue #12"

    def schema(self) -> str:
        return "<type>(<scope>): <subject>\n<BLANK LINE>\n<body>\n<BLANK LINE>\n(BREAKING CHANGE: )<footer>"

    def schema_pattern(self) -> str:
        return (
            r"(?s)"  # To explicitly make . match new line
            r"(" + "|".join(self.change_types) + r")"  # type
            r"(\("
            + self.scope_pattern
            + r"\))"
            + ("?" if self.scope_optional else "")  # scope
            + r"!?"
            r": "
            r"([^\n\r]+)"  # subject
            r"((\n\n.*)|(\s*))?$"
        )

    def info(self) -> str:
        return """\
The commit contains the following structural elements, to communicate
intent to the consumers of your library:

fix: a commit of the type fix patches a bug in your codebase
(this correlates with PATCH in semantic versioning).

feat: a commit of the type feat introduces a new feature to the codebase
(this correlates with MINOR in semantic versioning).

BREAKING CHANGE: a commit that has the text BREAKING CHANGE: at the beginning of
its optional body or footer section introduces a breaking API change
(correlating with MAJOR in semantic versioning).
A BREAKING CHANGE can be part of commits of any type.

Others: commit types other than fix: and feat: are allowed,
like chore:, docs:, style:, refactor:, perf:, test:, and others.

We also recommend improvement for commits that improve a current
implementation without adding a new feature or fixing a bug.

Notice these types are not mandated by the conventional commits specification,
and have no implicit effect in semantic versioning (unless they include a BREAKING CHANGE).

A scope may be provided to a commit's type, to provide additional contextual
information and is contained within parenthesis, e.g., feat(parser): add ability to parse arrays.

<type>[optional scope]: <description>

[optional body]

[optional footer]
"""
