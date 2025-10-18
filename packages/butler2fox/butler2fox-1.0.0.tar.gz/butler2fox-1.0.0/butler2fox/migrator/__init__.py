import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Type

from butler2fox.color import YELLOW
from butler2fox.gitlab import model as gl
from butler2fox.jenkins import model as jk


class NamingConvention(str, Enum):
    unchanged = "unchanged"
    snake = "snake"
    kebab = "kebab"
    camel = "camel"
    pascal = "pascal"

    def convert(self, name: str) -> str:
        if self == NamingConvention.unchanged:
            return name
        # split name into words
        lc_words = filter(lambda t: t, re.split(r"[^a-zA-Z0-9]+", name.lower()))
        match self:
            case NamingConvention.snake:
                return "_".join(lc_words)
            case NamingConvention.kebab:
                return "-".join(lc_words)
            case NamingConvention.camel:
                return lc_words[0] + "".join(map(str.capitalize, lc_words[1:]))
            case NamingConvention.pascal:
                return "".join(map(str.capitalize, lc_words))


@dataclass
class Options:
    job_naming_convention: NamingConvention = field(default=NamingConvention.unchanged)


class ObjChain(list):
    def last(self, cond: Type | Callable) -> any:
        if isinstance(cond, Type):

            def predicate(item):
                return isinstance(item, cond)
        elif isinstance(cond, Callable):
            predicate = cond
        else:

            def predicate():
                return False

        return next(filter(predicate, reversed(self)), None)


@dataclass
class ConversionContext:
    """Helper object that holds the Jenkins 2 GitLab model conversion context."""

    options: Options
    jk_chain: ObjChain = field(default_factory=ObjChain)
    gl_chain: ObjChain = field(default_factory=ObjChain)

    not_migrated_lines = 0

    def not_migrated(self, lines=1):
        self.not_migrated_lines += lines

    @property
    def jk_pipeline(self) -> jk.Pipeline:
        return self.jk_chain.last(jk.Pipeline)

    @property
    def gl_pipeline(self) -> gl.GlPipeline:
        return self.gl_chain.last(gl.GlPipeline)

    @property
    def gl_job(self) -> gl.GlJob:
        return self.gl_chain.last(gl.GlJob)

    def enter_script_ctx(self, obj: jk.Stage | jk.PostBlock):
        self.jk_chain.append(obj)
        self.script_ctx = []

    def leave_script_ctx(self):
        # flush current script ctx
        if self.script_ctx:
            post = self.jk_chain.last(jk.PostBlock)
            if post:
                # see: https://www.jenkins.io/doc/book/pipeline/syntax/#post
                match post.name:
                    case "always":
                        self.gl_job.after_script.extend(self.script_ctx)
                    case "aborted":
                        self.gl_job.after_script.append(
                            f'if [[ "$CI_JOB_STATUS" == "cancelled" ]]\nthen\n  {"\n  ".join(self.script_ctx)}\nfi'
                        )
                    case "regression" | "failure" | "unstable" | "unsuccessful":
                        self.gl_job.after_script.append(
                            f'if [[ "$CI_JOB_STATUS" == "failed" ]]\nthen\n  {"\n  ".join(self.script_ctx)}\nfi'
                        )
                    case _:
                        self.gl_job.after_script.append(
                            f'if [[ "$CI_JOB_STATUS" == "success" ]]\nthen\n  {"\n  ".join(self.script_ctx)}\nfi'
                        )
            else:
                self.gl_job.script.extend(self.script_ctx)

        # reset script ctx
        self.script_ctx = None
        self.jk_chain.pop()

    def add_script(self, script: str):
        if self.script_ctx is None:
            raise ValueError("Not in script context")
        self.script_ctx.append(script)

    @property
    def artifact_when(self) -> gl.GlArtifactWhen:
        post = self.jk_chain.last(jk.PostBlock)
        if post is None:
            return gl.GlArtifactWhen.on_success
        # see: https://www.jenkins.io/doc/book/pipeline/syntax/#post
        match post.name:
            case "always":
                return gl.GlArtifactWhen.always
            case "regression" | "aborted" | "failure" | "unstable" | "unsuccessful":
                return gl.GlArtifactWhen.on_failure
            case _:
                return gl.GlArtifactWhen.on_success


def convert_jk_var(jkvarname: str) -> str:
    # Jenkins base vars: https://www.jenkins.io/doc/book/pipeline/jenkinsfile/#using-environment-variables
    # Jenkins all vars: https://jenkins.thetaphi.de/env-vars.html/
    # GitLab variables: https://docs.gitlab.com/ci/variables/predefined_variables/
    match jkvarname:
        # Build vars
        case "BUILD_ID" | "BUILD_DISPLAY_NAME" | "BUILD_NUMBER":
            # The current build ID, identical to BUILD_NUMBER for builds created in Jenkins versions 1.597+.
            return "$CI_PIPELINE_IID"
        case "BUILD_TAG":
            # String of jenkins-${JOB_NAME}-${BUILD_NUMBER}. Convenient to put into a resource file, a jar file, etc for easier identification.
            return "$CI_PIPELINE_NAME"
        case "BUILD_URL":
            # The URL where the results of this build can be found (for example, http://buildserver/jenkins/job/MyJobName/17/).
            return "$CI_PIPELINE_URL"
        case "EXECUTOR_NUMBER":
            # The unique number that identifies the current executor (among executors of the same machine) performing this build. This is the number you see in the "build executor status", except that the number starts from 0, not 1.
            return "$CI_RUNNER_ID"
        # case "JAVA_HOME":
        #     # If your job is configured to use a specific JDK, this variable is set to the JAVA_HOME of the specified JDK. When this variable is set, PATH is also updated to include the bin subdirectory of JAVA_HOME.
        case "JENKINS_URL":
            # Full URL of Jenkins, such as https://example.com:port/jenkins/ (NOTE: only available if Jenkins URL set in "System Configuration").
            return "$CI_SERVER_URL"
        case "JOB_NAME":
            # Name of the project of this build, such as "foo" or "foo/bar".
            return "$CI_PROJECT_NAME"
        case "JOB_URL":
            return "$CI_PIPELINE_URL"
        case "NODE_NAME":
            # The name of the node the current build is running on. Set to 'master' for the Jenkins controller.
            return "$CI_RUNNER_DESCRIPTION"
        case "NODE_LABELS":
            return "$CI_RUNNER_TAGS"
        case "WORKSPACE":
            # The absolute path of the workspace
            return "$CI_PROJECT_DIR"
        case "WORKSPACE_TMP":
            return "/tmp/workdir"
        case "BRANCH_NAME":
            # return "$CI_COMMIT_REF_NAME"
            return "$CI_COMMIT_BRANCH"
        case "BRANCH_IS_PRIMARY":
            # TODO: not quite the same, but close enough
            return "$CI_DEFAULT_BRANCH"
        case "CI":
            return "$CI"
        # MR/PR vars
        case "CHANGE_ID":
            return "$CI_MERGE_REQUEST_IID"
        case "CHANGE_URL":
            return "$CI_MERGE_REQUEST_URL"
        case "CHANGE_TARGET":
            return "$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
        case "CHANGE_BRANCH":
            return "$CI_MERGE_REQUEST_SOURCE_BRANCH_NAME"
        case "CHANGE_TITLE":
            return "$CI_MERGE_REQUEST_TITLE"
        case "CHANGE_AUTHOR":
            return "$CI_COMMIT_AUTHOR"
        case "CHANGE_AUTHOR_DISPLAY_NAME":
            return "$GITLAB_USER_NAME"
        case "CHANGE_AUTHOR_EMAIL":
            return "$GITLAB_USER_EMAIL"
        # Git vars
        case "GIT_COMMIT":
            return "$CI_COMMIT_SHA"
        case "GIT_BRANCH" | "GIT_LOCAL_BRANCH":
            # return "$CI_COMMIT_REF_NAME"
            return "$CI_COMMIT_BRANCH"
        case "GIT_URL":
            return "$CI_REPOSITORY_URL"
        case "GIT_PREVIOUS_COMMIT" | "GIT_PREVIOUS_SUCCESSFUL_COMMIT":
            return "$CI_COMMIT_BEFORE_SHA"
        case "GIT_CHECKOUT_DIR":
            return "$CI_PROJECT_DIR"
        case "GIT_COMMITTER_NAME" | "GIT_AUTHOR_NAME":
            return "$GITLAB_USER_NAME"
        case "GIT_COMMITTER_EMAIL" | "GIT_AUTHOR_EMAIL":
            return "$GITLAB_USER_EMAIL"
    return f"${jkvarname}"


def migrate_pipeline(
    pipeline: jk.Pipeline, options=Options(), debug=False
) -> tuple[gl.GlPipeline, ConversionContext]:
    """See: https://docs.gitlab.com/ee/ci/migration/jenkins.html."""
    ctx = ConversionContext(options=options)
    ctx.jk_chain.append(pipeline)
    ctx.gl_chain.append(gl.GlPipeline())

    # global agent
    if pipeline.agent:
        ctx.jk_chain.append(pipeline.agent.agent)
        migrate_agent(pipeline.agent.agent, ctx.gl_pipeline.default, ctx)
        ctx.jk_chain.pop()

    # global environment
    if pipeline.environment:
        ctx.jk_chain.append(pipeline.environment)
        for ident, value in pipeline.environment.items():
            ctx.jk_chain.append(ident)
            if is_literal(value):
                ctx.gl_pipeline.variables[str(ident)] = convert_expr(value)
            elif isinstance(value, jk.FunctionCall) and value.name == "credentials":
                # this is a secret: add a comment !!
                name = value.args.get(0)
                ctx.gl_pipeline.variables[str(ident)] = (
                    f"//// 🔒 {ident} must be declared as a project CI/CD credential (formerly {name})"
                )
            else:
                ctx.gl_pipeline.variables[f"{ident}-comment"] = (
                    "//// 🚨 NOT MIGRATED: unsupported type"
                )
                ctx.not_migrated()
                ctx.gl_pipeline.variables[ident] = value
            ctx.jk_chain.pop()
        ctx.jk_chain.pop()

    # global options
    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#available-options
    if pipeline.options:
        ctx.jk_chain.append(pipeline.options)
        for optionFn in pipeline.options:
            ctx.jk_chain.append(optionFn)
            option = optionFn.name
            if option == "skipDefaultCheckout":
                ctx.gl_pipeline.variables["GIT_STRATEGY"] = "none"
            elif option == "disableConcurrentBuilds":
                abort_previous = optionFn.args.get("abortPrevious")
                if abort_previous:
                    ctx.gl_pipeline.default = gl.GlJob()
                    ctx.gl_pipeline.default.interruptible = True
            elif option == "retry":
                ctx.gl_pipeline.default = gl.GlJob()
                count = optionFn.args.get("count", posidx=0)
                ctx.gl_pipeline.default.retry = (
                    count
                    if count is not None
                    else "//// 🚨 NOT MIGRATED: missing count"
                )
            elif option == "timeout":
                time = optionFn.args.get("time", posidx=0)
                unit = optionFn.args.get("unit", dflt="minutes")
                if time:
                    ctx.gl_pipeline.default = gl.GlJob()
                    ctx.gl_pipeline.default.timeout = f"{time} {unit.lower()}"
            ctx.jk_chain.pop()
        ctx.jk_chain.pop()

    # global params
    if pipeline.parameters:
        ctx.jk_chain.append(pipeline.parameters)
        for paramFn in pipeline.parameters:
            ctx.jk_chain.append(paramFn)
            # param_type = paramFn.name # string | booleanParam | file | choice | password
            param_name = paramFn.args.get("name")
            param_desc = paramFn.args.get("description")
            param_dflt_arg = paramFn.args.get("defaultValue")
            param_dflt_val = param_dflt_arg if param_dflt_arg else ""
            if is_literal(param_dflt_val):
                ctx.gl_pipeline.variables[str(param_name)] = gl.GlExpandedVariable(
                    description=convert_expr(param_desc),
                    value=convert_expr(param_dflt_val),
                )
            else:
                ctx.gl_pipeline.variables[f"{param_name}-comment"] = (
                    "//// 🚨 NOT MIGRATED: unsupported type"
                )
                ctx.not_migrated()
                ctx.gl_pipeline.variables[str(param_name)] = str(param_dflt_val)
            ctx.jk_chain.pop()
        ctx.jk_chain.pop()

    # jobs
    migrate_stages(pipeline.stages, ctx)

    return ctx.gl_pipeline, ctx


def is_literal(expr) -> bool:
    return (
        (isinstance(expr, str) and not isinstance(expr, jk.Identifier))
        or isinstance(expr, bool)
        or isinstance(expr, int)
    )


def convert_expr(expr: any) -> str | None:
    if expr is None:
        return None
    if isinstance(expr, jk.Identifier):
        # a Jenkins/Groovy identifier becomes a GitLab variable
        return convert_jk_var(expr)
    if isinstance(expr, str):
        # expand and convert Groovy scriptlets
        def _replace_jk_vars(match: re.Match) -> str:
            type = match.group(1)
            name = match.group(2)
            if type == "env":
                return convert_jk_var(name)
            # fallback: use same name
            return f"${name}"

        return re.sub(
            r"\$\{(env|params)\.(\w+)\}",
            _replace_jk_vars,
            expr,
        )
    if isinstance(expr, bool) or isinstance(expr, int):
        # keep literals as is
        return expr
    if isinstance(expr, jk.FieldExpression):
        if expr.left == jk.env:
            return convert_jk_var(expr.field)
        if expr.left == jk.params:
            return f"${expr.field}"
        return f"{convert_expr(expr.left)}.{expr.field}"
    if isinstance(expr, jk.Arg):
        # recurse
        if expr.name:
            return f"{expr.name}: {convert_expr(expr.value)}"
        return convert_expr(expr.value)
    if isinstance(expr, jk.FunctionCall):
        # recurse
        return f"{expr.name}({', '.join(convert_expr(arg) for arg in expr.args)})"
    if isinstance(expr, jk.MethodExpression):
        # recurse
        return f"{convert_expr(expr.left)}.{expr.method}({', '.join(convert_expr(arg) for arg in expr.args)})"
    if isinstance(expr, jk.IndexExpression):
        # recurse
        return f"{convert_expr(expr.left)}.[{convert_expr(expr.index)}]"
    if isinstance(expr, jk.BinaryExpression):
        # recurse
        return f"{convert_expr(expr.left)} {expr.operator} {convert_expr(expr.right)}"
    return str(expr)


def ant_to_regex(ant_pattern: str) -> str:
    """
    Convert an ANT-style pattern to a regular expression pattern.
    """
    regex = ""
    i = 0
    length = len(ant_pattern)

    while i < length:
        c = ant_pattern[i]
        if c == "*":
            # Check if it's a double star
            if i + 1 < length and ant_pattern[i + 1] == "*":
                # Match zero or more directories
                regex += ".*"
                i += 2
            else:
                # Match zero or more characters except slash
                regex += "[^/]*"
                i += 1
        elif c == "?":
            # Match a single character except slash
            regex += "[^/]"
            i += 1
        elif c == ".":
            regex += r"\."
            i += 1
        elif c == "/":
            regex += "/"
            i += 1
        else:
            regex += re.escape(c)
            i += 1

    return "^" + regex + "$"


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#when
def convert_condition(cond: jk.WhenCondition) -> str:
    """Recusively converts a Jenkins when condition into a GitLab rule"""
    if isinstance(cond, jk.When):
        return " && ".join(map(convert_condition, cond.conditions()))
    if isinstance(cond, jk.WhenAll):
        return " && ".join(map(convert_condition, cond))
    if isinstance(cond, jk.WhenAny):
        return " || ".join(map(convert_condition, cond))
    if isinstance(cond, jk.WhenNot):
        # TODO: reduce with sub condition
        # '!' non supporté par GitLab
        return convert_condition(cond.condition.invert())
    if isinstance(cond, jk.WhenBranch) or isinstance(cond, jk.WhenTag):
        gitlab_var = (
            "CI_COMMIT_BRANCH" if isinstance(cond, jk.WhenBranch) else "CI_COMMIT_TAG"
        )
        match cond.comparator:
            case "EQUALS":
                return (
                    f"${gitlab_var} {'!=' if cond.inverted else '=='} '{cond.pattern}'"
                )
            case "GLOB":
                return f"${gitlab_var} {'!~' if cond.inverted else '=~'} '/{ant_to_regex(cond.pattern)}/'"
            case "REGEXP":
                return f"${gitlab_var} {'!~' if cond.inverted else '=~'} '/{cond.pattern}/'"
            case _:
                return f"[🚨 NOT MIGRATED: unsupported comp {cond}]"
    if isinstance(cond, jk.WhenEnvironment):
        return f"{convert_jk_var(cond.name)} == '{convert_expr(cond.value)}'"
    if isinstance(cond, jk.WhenTriggered):
        match cond.cause:
            case "SCMTrigger":
                return "$CI_PIPELINE_SOURCE == 'push'"
            case "TimerTrigger":
                return "$CI_PIPELINE_SOURCE == 'schedule'"
            case "BuildUpstreamCause":
                return "$CI_PIPELINE_SOURCE == 'parent_pipeline'"
            case "UserIdCause":
                return "$CI_PIPELINE_SOURCE == 'web'"
            case _:
                return f"[🚨 NOT MIGRATED: unsupported trigger {cond.cause}]"
    return f"[🚨 NOT MIGRATED: {cond}]"


def migrate_agent(
    agent: any,
    job: gl.GlJob,
    ctx: ConversionContext,
):
    # print(f"agent: {agent} ({type(agent).__class__.__name__})")
    if isinstance(agent, jk.DockerNamedAgent):
        job.image = gl.GlImage(name=convert_expr(agent.name))
    elif isinstance(agent, jk.DockerAgent):
        registryUrl = agent.get("registryUrl")
        image = convert_expr(agent.get("image"))
        job.image = gl.GlImage(
            name=f"{convert_expr(registryUrl)}/{image}" if registryUrl else image
        )
    elif isinstance(agent, jk.LabelAgent):
        job.tags.append("//// 🚧 migrated from label agent")
        job.tags.append(str(agent.name))
    else:
        job.tags.append("//// 🚨 NOT MIGRATED: unsupported agent")
        ctx.not_migrated()
        job.tags.append(str(agent))


def migrate_stages(
    stages: list[jk.Stage],
    ctx: ConversionContext,
):
    for stage in stages:
        ctx.jk_chain.append(stage)
        # A stage must have one and only one of steps, stages, parallel, or matrix.
        if stage.parallel is not None:
            migrate_stages(stage.parallel, ctx)
        elif stage.stages is not None:
            migrate_stages(stage.stages, ctx)
        elif stage.steps is not None:
            migrate_stage(stage, ctx)
        else:
            print(f"{YELLOW('WARNING')}: unknown stage type: {stage}", file=sys.stderr)
        ctx.jk_chain.pop()


def migrate_stage(
    stage: jk.Stage,
    ctx: ConversionContext,
) -> gl.GlJob:
    # determine stage name (retrieve first parallel parent stage)
    containing_stage = (
        ctx.jk_chain.last(
            lambda obj: isinstance(obj, jk.Stage) and obj.parallel is not None
        )
        or stage
    )
    stage_name = ctx.options.job_naming_convention.convert(containing_stage.name)
    # ensure stage is declared
    if stage_name not in ctx.gl_pipeline.stages:
        ctx.gl_pipeline.stages.append(stage_name)
    # create job
    job = gl.GlJob(stage=stage_name)
    ctx.gl_chain.append(job)
    # steps = stage.steps
    # agent
    if stage.agent:
        ctx.jk_chain.append(stage.agent.agent)
        migrate_agent(stage.agent.agent, job, ctx)
        ctx.jk_chain.pop()

    # options
    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#available-options
    if stage.options:
        ctx.jk_chain.append(stage.options)
        for optionFn in stage.options:
            ctx.jk_chain.append(optionFn)
            option = optionFn.name
            if option == "skipDefaultCheckout":
                ctx.gl_pipeline.variables["GIT_STRATEGY"] = "none"
            elif option == "disableConcurrentBuilds":
                abort_previous = optionFn.args.get("abortPrevious")
                if abort_previous:
                    job.interruptible = True
            elif option == "retry":
                count = optionFn.args.get("count", posidx=0)
                job.retry = (
                    count
                    if count is not None
                    else "//// 🚨 NOT MIGRATED: missing count"
                )
            elif option == "timeout":
                time = optionFn.args.get("time", posidx=0)
                unit = optionFn.args.get("unit", dflt="minutes")
                job.timeout = f"{time} {unit.lower()}"
            ctx.jk_chain.pop()
        ctx.jk_chain.pop()

    # environment
    if stage.environment:
        ctx.jk_chain.append(stage.environment)
        for ident, value in stage.environment.items():
            ctx.jk_chain.append(ident)
            if is_literal(value):
                job.variables[str(ident)] = convert_expr(value)
            elif isinstance(value, jk.FunctionCall) and value.name == "credentials":
                # this is a secret: add a comment !!
                name = value.args.get(0)
                job.variables[str(ident)] = (
                    f"//// 🔒 {ident} must be declared as a project CI/CD credential (formerly {name})"
                )
            else:
                job.variables[f"{ident}-comment"] = (
                    "//// 🚨 NOT MIGRATED: unsupported type"
                )
                ctx.not_migrated()
                job.variables[str(ident)] = str(value)
            ctx.jk_chain.pop()
        ctx.jk_chain.pop()

    # input
    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#input
    if stage.input:
        ctx.jk_chain.append(stage.input)
        params = stage.input.get("parameters")
        if params:
            job.when_comment = f"//// 🚨 NOT MIGRATED: input parameters required\n{'\n - '.join(params)}"
            ctx.not_migrated(len(params))
        else:
            job.when_comment = "//// 🚧 blocking input"
        job.when = gl.GlJobWhen.manual
        ctx.jk_chain.pop()

    # tools
    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#tools
    if stage.tools:
        for tool in stage.tools.keys():
            job.before_script.append(f"//// 🚨 NOT MIGRATED: install {tool}")
            ctx.not_migrated()
            job.before_script.append(f"install {stage.tools[tool]}")

    migrate_steps(stage, ctx)

    # when rules
    if stage.when and stage.when.conditions():
        conds = stage.when.conditions()
        top_cond = None
        if len(conds) == 1:
            top_cond = conds[0]
        while isinstance(top_cond, jk.WhenNot):
            top_cond = top_cond.invert()
        if isinstance(top_cond, jk.WhenAny):
            # split into single job rules
            for cond in top_cond:
                ctx.jk_chain.append(cond)
                job.rules.append(gl.GlRule(if_=convert_condition(cond)))
                ctx.jk_chain.pop()
        else:
            # one single rule
            ctx.jk_chain.append(stage.when)
            job.rules.append(gl.GlRule(if_=convert_condition(stage.when)))
            ctx.jk_chain.pop()

    # post (artifacts)
    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#post
    if stage.post:
        ctx.jk_chain.append(stage.post)
        for post in stage.post:
            migrate_steps(post, ctx)
        ctx.jk_chain.pop()

    ctx.gl_chain.pop()
    # finally add job to pipeline
    job_name = ctx.options.job_naming_convention.convert(stage.name)
    ctx.gl_pipeline.jobs[job_name] = job
    return job


def migrate_steps(
    steps_holder: jk.Stage | jk.BlockStep,
    ctx: ConversionContext,
) -> gl.GlJob:
    # steps
    from butler2fox.migrator import steps as m_steps

    # ctx.jk_chain.append(post)
    ctx.enter_script_ctx(steps_holder)
    for step in steps_holder.steps:
        ctx.jk_chain.append(step)
        if isinstance(step, jk.FunctionCall):
            # find migrator function from m_steps module
            step_migrator = getattr(m_steps, step.name, None)
            if step_migrator:
                step_migrator(step, ctx)
            else:
                ctx.add_script("//// 🚨 NOT MIGRATED: unsupported function")
                ctx.not_migrated()
                ctx.add_script(str(step))
        elif isinstance(step, jk.BlockStep):
            # find migrator function from m_steps module
            step_migrator = getattr(m_steps, step.name, None)
            if step_migrator:
                step_migrator(step, ctx)
            else:
                ctx.add_script("//// 🚨 NOT MIGRATED: unsupported block step")
                ctx.not_migrated()
                ctx.add_script(str(step))
        elif isinstance(step, jk.ScriptStep):
            ctx.add_script("//// 🚨 NOT MIGRATED: unsupported Groovy")
            ctx.not_migrated(step.groovy.count("\n"))
            ctx.add_script(
                "\n".join([line.strip() for line in step.groovy.split("\n")])
            )
        else:
            ctx.add_script("//// 🚨 NOT MIGRATED: unsupported type")
            ctx.not_migrated()
            ctx.add_script(str(step))
        ctx.jk_chain.pop()
    ctx.leave_script_ctx()
    # ctx.jk_chain.pop()
