"""See: https://www.jenkins.io/doc/pipeline/steps/workflow-basic-steps/"""

import json

from butler2fox.jenkins import model as jk
from butler2fox.migrator import ConversionContext, convert_expr


# =====================================================================================================================
# === Core Steps
# =====================================================================================================================
# see: https://www.jenkins.io/doc/pipeline/steps/core/#archiveartifacts-archive-the-artifacts
def archiveArtifacts(step: jk.FunctionCall, ctx: ConversionContext):
    job = ctx.gl_job
    artifacts = step.args.get("artifacts", posidx=0, dflt="")
    job.artifacts.paths.extend(map(convert_expr, artifacts.split(",")))
    excludes = step.args.get("excludes")
    if excludes:
        job.artifacts.paths.extend(map(convert_expr, excludes.split(",")))
    # TODO? who has the priority between post and onlyIfSuccessful?
    # onlyIfSuccessful = step.args.get("onlyIfSuccessful") or False
    job.artifacts.when = ctx.artifact_when


# =====================================================================================================================
# === Basic Steps
# =====================================================================================================================
# see: https://www.jenkins.io/doc/pipeline/steps/workflow-basic-steps/#deletedir-recursively-delete-the-current-directory-from-the-workspace
def deleteDir(step: jk.FunctionCall, ctx: ConversionContext):
    ctx.add_script(f"rm -rf {convert_expr(step.args.get('dir', posidx=0))}")


# see: https://www.jenkins.io/doc/pipeline/steps/workflow-basic-steps/#echo-print-message
def echo(step: jk.FunctionCall, ctx: ConversionContext):
    ctx.add_script(f'echo "{convert_expr(step.args.get("message", posidx=0))}"')


# see: https://www.jenkins.io/doc/pipeline/steps/workflow-basic-steps/#error-error-signal
def error(step: jk.FunctionCall, ctx: ConversionContext):
    ctx.add_script(f'echo "[ERROR] {convert_expr(step.args.get("message", posidx=0))}"')
    ctx.add_script("exit 1")


# see: https://www.jenkins.io/doc/pipeline/steps/workflow-basic-steps/#unstable-set-stage-result-to-unstable
def unstable(step: jk.FunctionCall, ctx: ConversionContext):
    # emit message, fail but also allow script to fail
    job = ctx.gl_job
    job.allow_failure = {"exit_codes": 255}
    ctx.add_script(f'echo "[WARN] {convert_expr(step.args.get("message", posidx=0))}"')
    ctx.add_script("exit 255")


# https://www.jenkins.io/doc/pipeline/steps/workflow-basic-steps/#sleep-sleep
def sleep(step: jk.FunctionCall, ctx: ConversionContext):
    time = int(step.args.get("time", posidx=0))
    unit = str(step.args.get("unit", dflt="SECONDS")).upper()
    match unit:
        case "NANOSECONDS":
            seconds = time / 1000000000
        case "MICROSECONDS":
            seconds = time / 1000000
        case "MILLISECONDS":
            seconds = time / 1000
        case "SECONDS":
            seconds = time
        case "MINUTES":
            seconds = time * 60
        case "HOURS":
            seconds = time * 60 * 60
        case "DAYS":
            seconds = time * 60 * 60 * 24
        case _:
            ctx.add_script(f"//// ⚠️ unrecognized unit: '{unit}'")
            seconds = time
    # emit message, fail but also allow script to fail
    ctx.add_script(f"sleep {seconds}")


# TODO:
# sleep
# mail (echo)
# stash/unstash (cache ?!)
# writefile


# see: https://www.jenkins.io/doc/pipeline/steps/workflow-basic-steps/#archive-archive-artifacts
def archive(step: jk.FunctionCall, ctx: ConversionContext):
    job = ctx.gl_job
    includes = step.args.get("includes", posidx=0, dflt="")
    job.artifacts.paths.extend(map(convert_expr, includes.split(",")))
    excludes = step.args.get("excludes")
    if excludes:
        job.artifacts.paths.extend(map(convert_expr, excludes.split(",")))
    job.artifacts.when = ctx.artifact_when


# see: https://www.jenkins.io/doc/pipeline/steps/workflow-basic-steps/#stash-stash-some-files-to-be-used-later-in-the-build
def stash(step: jk.FunctionCall, ctx: ConversionContext):
    job = ctx.gl_job
    # name = step.args.get("name", posidx=0)
    # job.artifacts.paths.append(f"//// was stash {name}")
    includes = step.args.get("includes", dflt="**")
    job.artifacts.paths.extend(map(convert_expr, includes.split(",")))
    excludes = step.args.get("excludes")
    if excludes:
        job.artifacts.paths.extend(map(convert_expr, excludes.split(",")))
    job.artifacts.when = ctx.artifact_when


# =====================================================================================================================
# === SCM Steps
# =====================================================================================================================
# see: https://www.jenkins.io/doc/pipeline/steps/workflow-scm-step/#pipeline-scm-step
def checkout(step: jk.FunctionCall, ctx: ConversionContext):
    # nothing to do as the checkout is implicit with GitLab
    pass


# =====================================================================================================================
# === Node & Processes Steps
# =====================================================================================================================
# see: https://www.jenkins.io/doc/pipeline/steps/workflow-durable-task-step/#sh-shell-script
def sh(step: jk.FunctionCall, ctx: ConversionContext):
    ctx.add_script(convert_expr(step.args.get("script", posidx=0).strip()))


def powershell(step: jk.FunctionCall, ctx: ConversionContext):
    sh(step, ctx)


def pwsh(step: jk.FunctionCall, ctx: ConversionContext):
    sh(step, ctx)


def bat(step: jk.FunctionCall, ctx: ConversionContext):
    sh(step, ctx)


def dir(step: jk.FunctionCall, ctx: ConversionContext):
    ctx.add_script(f"cd {convert_expr(step.args.get('path', posidx=0).strip())}")
    # TODO: dir can be a block command; cd - after


# =====================================================================================================================
# === JUnit Steps
# =====================================================================================================================
# see: https://www.jenkins.io/doc/pipeline/steps/junit/#junit-archive-junit-formatted-test-results
def junit(step: jk.FunctionCall, ctx: ConversionContext):
    job = ctx.gl_job
    if "junit" not in job.artifacts.reports:
        job.artifacts.reports["junit"] = []
    job.artifacts.reports["junit"].append(
        convert_expr(step.args.get("testResults", posidx=0))
    )
    job.artifacts.when = ctx.artifact_when


# =====================================================================================================================
# === HTML Publisher Steps
# =====================================================================================================================
# see: https://www.jenkins.io/doc/pipeline/steps/htmlpublisher/#publishhtml-publish-html-reports
def publishHTML(step: jk.FunctionCall, ctx: ConversionContext):
    # all we have to do is to keep 'reportFiles' as a job artifact
    job = ctx.gl_job
    target = step.args.get("target", posidx=0)
    report_dir = target.get("reportDir")
    report_files = target.get("reportFiles")
    job.artifacts.paths.extend(
        [f"{report_dir}/{convert_expr(file)}" for file in report_files.split(",")]
    )


# =====================================================================================================================
# === Slack Notification Plugin Steps
# =====================================================================================================================
# see: https://www.jenkins.io/doc/pipeline/steps/slack/#slacksend-send-slack-message
# !! Uses Slack API (an not WebHook): https://docs.slack.dev/messaging/sending-and-scheduling-messages#publishing
def slackSend(step: jk.FunctionCall, ctx: ConversionContext):
    base_url = convert_expr(step.args.get("baseUrl", dflt="https://slack.com"))
    if "SLACK_TOKEN" not in ctx.gl_pipeline.variables:
        ctx.gl_pipeline.variables["SLACK_TOKEN"] = (
            "//// 🔒 set in your project/group variables"
        )
    json_data = {}
    # see: https://docs.slack.dev/tools/node-slack-sdk/reference/webhook/interfaces/IncomingWebhookSendArguments/
    message = convert_expr(step.args.get("message"))
    if message:
        json_data["text"] = message
    channel = convert_expr(step.args.get("channel"))
    if channel:
        json_data["channel"] = channel
    username = convert_expr(step.args.get("username"))
    if username:
        json_data["username"] = username
    icon_emoji = convert_expr(step.args.get("iconEmoji"))
    if icon_emoji:
        json_data["icon_emoji"] = icon_emoji

    ctx.add_script("//// ℹ️ slackSend (requires curl)")
    json_data_escaped = json.dumps(json_data).replace('"', '\\"')
    ctx.add_script(
        f'curl -X POST -H "Content-Type: application/json; charset=utf-8" -H "Authorization: Bearer $SLACK_TOKEN" --data "{json_data_escaped}" "{base_url}/api/chat.postMessage"'
    )


# =====================================================================================================================
# === Milestone Steps
# =====================================================================================================================
# see: https://www.jenkins.io/doc/pipeline/steps/pipeline-milestone-step/#milestone-the-milestone-step-forces-all-builds-to-go-through-in-order
def milestone(step: jk.FunctionCall, ctx: ConversionContext):
    # choice to convert a milestone into an interruptible job
    ordinal = convert_expr(step.args.get("ordinal", dflt=0))
    label = convert_expr(step.args.get("label"))
    ctx.gl_job.resource_group = label or f"milestone-{ordinal}"


def not_supported(step: jk.FunctionCall, ctx: ConversionContext):
    ctx.add_script(f"//// ℹ️ {step.name} not supported by GitLab")


def logContains(step: jk.FunctionCall, ctx: ConversionContext):
    not_supported(step, ctx)


def logDoesNotContain(step: jk.FunctionCall, ctx: ConversionContext):
    not_supported(step, ctx)
