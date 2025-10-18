import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TextIO

import yaml

# ugly trick to disable tags
yaml.emitter.Emitter.prepare_tag = lambda self, tag: ""

# render enums as their string
yaml.Dumper.add_multi_representer(
    Enum,
    yaml.representer.SafeRepresenter.represent_str,
)


def str_presenter(dumper: yaml.Dumper, data: str):
    """configures yaml for dumping multiline strings
    Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data"""
    style = None
    if data.find("\n") >= 0:
        # multiline string
        style = "|"
    elif data.find("'") >= 0:
        style = '"'
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(
    str, str_presenter
)  # to use with safe_dum


class YamlBaseCompact(yaml.YAMLObject):
    """Base YAML Object class that doesn't render null fields."""

    def __getstate__(self):
        return {k: v for (k, v) in self.__dict__.items() if v}

    def __bool__(self):
        return len(self.__getstate__()) > 0


class GlRuleWhen(str, Enum):
    """see: https://docs.gitlab.com/ci/yaml/#ruleswhen."""

    on_success = "on_success"
    """(default): Run the job only when no jobs in earlier stages fail."""
    on_failure = "on_failure"
    """Run the job only when at least one job in an earlier stage fails."""
    never = "never"
    """Don't run the job regardless of the status of jobs in earlier stages."""
    always = "always"
    """Run the job regardless of the status of jobs in earlier stages."""
    manual = "manual"
    """Add the job to the pipeline as a manual job. The default value for allow_failure changes to false."""
    delayed = "delayed"
    """Add the job to the pipeline as a delayed job."""


class GlArtifactWhen(str, Enum):
    """see: https://docs.gitlab.com/ci/yaml/#artifactswhen."""

    on_success = "on_success"
    """(default): Upload artifacts only when the job succeeds."""
    on_failure = "on_failure"
    """Upload artifacts only when the job fails."""
    always = "always"
    """Always upload artifacts (except when jobs time out). For example, when uploading artifacts required to troubleshoot failing tests."""


class GlJobWhen(str, Enum):
    """see: https://docs.gitlab.com/ci/yaml/#when."""

    on_success = "on_success"
    """(default): Run the job only when no jobs in earlier stages fail."""
    on_failure = "on_failure"
    """Run the job only when at least one job in an earlier stage fails."""
    always = "always"
    """Run the job regardless of the status of jobs in earlier stages."""
    never = "never"
    """Don't run the job regardless of the status of jobs in earlier stages. Can only be used in a rules section or workflow: rules."""
    manual = "manual"
    """Add the job to the pipeline as a manual job."""
    delayed = "delayed"
    """Add the job to the pipeline as a delayed job."""


class GlPullPolicy(str, Enum):
    """see: https://docs.gitlab.com/ci/yaml/#imagepull_policy."""

    if_not_present = "if-not-present"
    always = "always"
    never = "never"


@dataclass
class GlExpandedVariable(YamlBaseCompact):
    """see: https://docs.gitlab.com/ci/yaml/#default-variables."""

    description: str = None
    value: str = None
    options: list[str] = None
    expand: bool = None


@dataclass
class GlRule(YamlBaseCompact):
    """see: https://docs.gitlab.com/ci/yaml/#rules."""

    if_: str = field(repr=False)
    when: str = None
    allow_failure: bool = None
    variables: dict[str, str | GlExpandedVariable] = field(default_factory=dict)
    interruptible: bool = None
    needs: list[str] = field(default_factory=list)


@dataclass
class GlImage(YamlBaseCompact):
    """see: https://docs.gitlab.com/ci/yaml/#image."""

    name: str = None
    entrypoint: list[str] = field(default_factory=list)
    docker: dict[str, str] = field(default_factory=dict)
    pull_policy: GlPullPolicy = None


@dataclass
class GlArtifacts(YamlBaseCompact):
    """see: https://docs.gitlab.com/ci/yaml/#artifacts."""

    name: str = None
    when: GlArtifactWhen = None
    paths: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    reports: dict[str, str] = field(default_factory=dict)


@dataclass
class GlWorflow(YamlBaseCompact):
    name: str = None
    rules: list[GlRule] = field(default_factory=list)


@dataclass
class GlJob(YamlBaseCompact):
    """see: https://docs.gitlab.com/ci/yaml/#job-keywords."""

    image_comment: str = None
    image: GlImage = None
    stage: str = None
    tags_comment: str = None
    tags: list[str] = field(default_factory=list)
    variables_comment: str = None
    variables: dict[str, str] = field(default_factory=dict)
    before_script: list[str] = field(default_factory=list)
    script: list[str] = field(default_factory=list)
    after_script: list[str] = field(default_factory=list)
    when_comment: str = None
    when: GlJobWhen = None
    allow_failure: any = None
    rules: list[GlRule] = field(default_factory=list)
    artifacts: GlArtifacts = field(default_factory=GlArtifacts)
    interruptible: bool = None
    resource_group: str = None
    retry: int = None
    timeout: str = None
    # cache

    def __bool__(self):
        return len(self.before_script) + len(self.script) + len(self.after_script) > 0


# yaml.add_representer(GlJob, clean_representer)


@dataclass
class GlPipeline(YamlBaseCompact):
    workflow: GlWorflow = field(default_factory=GlWorflow)
    default: GlJob = field(default_factory=GlJob)
    stages: list[str] = field(default_factory=list)
    variables: dict[str, str | GlExpandedVariable] = field(default_factory=dict)
    jobs: dict[str, GlJob] = field(default_factory=dict)

    def __getstate__(self):
        # Mixin jobs and regular fields
        state = {}
        effective_stages = set(job.stage for job in self.jobs.values() if job)
        if self.workflow:
            state["workflow"] = self.workflow
        if self.default:
            state["default"] = self.default
        if self.stages:
            state["stages"] = [
                stage for stage in self.stages if stage in effective_stages
            ]
        if self.variables:
            state["variables"] = self.variables
        # inline jobs but omit empty ones
        state.update(
            {
                name: (job if job else f"//// ℹ️ stage '{name}' omitted (empty)")
                for (name, job) in self.jobs.items()
            }
        )
        return state

    def dump(self, stream: TextIO):
        """Serialize this GitLab pipeline model to YAML."""
        gitlab_ci = yaml.dump(
            data=self, sort_keys=False, width=1000, allow_unicode=True
        )
        # then post process the YAML

        # 1: unfold comments
        def _unfold_comment(match: re.Match):
            # replace '//' with '#'
            comment = match.group(2)
            is_quoted = comment.endswith("'") or comment.endswith('"')
            if is_quoted:
                # remove closing quote
                comment = comment[0:-1]
                # unescape specials chars
                comment = comment.replace("''", "'")
                comment = comment.replace("\\n", "\n")
                comment = comment.replace("\\r", "\r")
                comment = comment.replace("\\t", "\t")
            # finally, indent and comment block
            prefix = f"{match.group(1)}# "
            return re.sub(r"^", prefix, comment, flags=re.MULTILINE)

        gitlab_ci = re.sub(
            r"^( *).*//// (.*)$", _unfold_comment, gitlab_ci, flags=re.MULTILINE
        )

        # 2: rename 'if_' to 'if'
        gitlab_ci = gitlab_ci.replace("if_:", "if:")

        # dump to stream
        stream.write(gitlab_ci)
        stream.flush()
