"""
Jenkinsfile parser (AST).

See Jenkinsfile syntax:
- https://www.jenkins.io/doc/book/pipeline/syntax/

See Groovy syntax:
- Lexer: https://github.com/daniellansun/groovy-antlr4-grammar-optimized/blob/master/src/main/antlr4/org/codehaus/groovy/parser/antlr4/GroovyLexer.g4
- Grammar: https://github.com/daniellansun/groovy-antlr4-grammar-optimized/blob/master/src/main/antlr4/org/codehaus/groovy/parser/antlr4/GroovyParser.g4
"""

from pathlib import Path

from arpeggio import (
    EOF,
    Kwd,
    Not,
    OneOrMore,
    Optional,
    ParserPython,
    ParseTreeNode,
    UnorderedGroup,
    ZeroOrMore,
)
from arpeggio import RegExMatch as _

EOL = "\n"


def COMMA():
    return ","


def RestOfLine():
    return _(r".*")


def Identifier():
    return _(r"[a-zA-Z$_][a-zA-Z0-9$_]*")


def Comment():
    return [_(r"//.*"), _(r"/\*.*?\*/", multiline=True)]


def DQString():
    return _(r'"[^"]*"')


def SQString():
    return _(r"'[^']*'")


def TDQString():
    return _('"""(.*?)"""', multiline=True)


def TSQString():
    return _("'''(.*?)'''", multiline=True)


# TODO: constant?
def NullLit():
    return Kwd("null")


def StringLit():
    return [TDQString, TSQString, DQString, SQString]


def BoolLit():
    return [Kwd("true"), Kwd("false")]


def NumberLit():
    return _("[0-9]+")


# see: https://github.com/daniellansun/groovy-antlr4-grammar-optimized/blob/master/src/main/antlr4/org/codehaus/groovy/parser/antlr4/GroovyParser.g4#L288
def Expression():
    return [FunctionCallParen, AtomExpression], ZeroOrMore(
        [BinaryExpression, MethodExpression, FieldExpression, IndexExpression]
    )


def AtomExpression():
    return [
        NullLit,
        BoolLit,
        StringLit,
        NumberLit,
        Identifier,
        Array,
        EmptyMap,
        Map,
    ]


# TODO?
# def UnaryExpression():
#     return (
#         [
#             Kwd("+"),
#             Kwd("-"),
#             Kwd("!"),
#         ],
#         Expression,
#     )

# def ParenExpression():
#     return "(", Expression, ")"


def BinaryExpression():
    return (
        [
            Kwd("+"),
            Kwd("-"),
            Kwd("*"),
            Kwd("/"),
            Kwd("%"),
            Kwd("&&"),
            Kwd("||"),
            Kwd("=="),
            Kwd("!="),
        ],
        Expression,
    )


def MethodExpression():
    return ".", Identifier, "(", ArgList, ")"


def FieldExpression():
    return ".", Identifier


def IndexExpression():
    return "[", Expression, "]"


def Arg():
    return Optional(Identifier, ":"), Expression


def ArgList():
    return ZeroOrMore(Arg, sep=COMMA), Optional(COMMA)


def EmptyMap():
    return "[", ":", "]"


def Map():
    return "[", OneOrMore(Identifier, ":", Expression, sep=COMMA), Optional(COMMA), "]"


def Array():
    return "[", ZeroOrMore(Expression, sep=COMMA), Optional(COMMA), "]"


def FunctionCallParen():
    return Identifier, "(", ArgList, ")"


def FunctionCallNoParen():
    return Identifier, ArgList


def FunctionCall():
    return [
        FunctionCallParen,
        FunctionCallNoParen,
    ]


def EnvEntry():
    return Identifier, "=", Expression


def DirectiveEntry():
    return Identifier, Expression


def DirectivesBlock():
    return (
        "{",
        ZeroOrMore(DirectiveEntry),
        "}",
    )


def SheBang():
    return "#!", _(r".*")


def K8sAgent():
    return (Kwd("kubernetes"), DirectivesBlock)


def DockerAgent():
    return (
        Kwd("docker"),
        [StringLit, DirectivesBlock],
    )


def DockerfileAgent():
    return (Kwd("dockerfile"), DirectivesBlock)


def NodeAgent():
    return (Kwd("node"), DirectivesBlock)


def LabelAgent():
    return Kwd("label"), Expression


def AgentBlock():
    return "{", [K8sAgent, DockerAgent, DockerfileAgent, NodeAgent, LabelAgent], "}"


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#agent
def Agent():
    return Kwd("agent"), [Kwd("any"), Kwd("none"), AgentBlock]


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#environment
def Environment():
    return (
        Kwd("environment"),
        "{",
        ZeroOrMore(EnvEntry),
        "}",
    )


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#parameters
def Parameters():
    return (
        Kwd("parameters"),
        "{",
        ZeroOrMore(FunctionCall),
        "}",
    )


def GroovyCode():
    return OneOrMore([GroovyBlock, _(r"[^{}]*", multiline=True)])


def GroovyBlock():
    return "{", GroovyCode, "}"


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#script
def ScriptStep():
    return (
        Kwd("script"),
        "{",
        GroovyCode,
        "}",
    )


def BlockStep():
    return (
        Identifier,
        Optional("(", ArgList, ")"),
        "{",
        ZeroOrMore(Step),
        "}",
    )


def Step():
    return [ScriptStep, BlockStep, FunctionCall]


def Steps():
    return Kwd("steps"), "{", ZeroOrMore(Step), "}"


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#parallel
def Parallel():
    return Kwd("parallel"), "{", ZeroOrMore(Stage), "}"


def PostBlock():
    return (
        [
            Kwd("always"),
            Kwd("changed"),
            Kwd("fixed"),
            Kwd("regression"),
            Kwd("aborted"),
            Kwd("failure"),
            Kwd("success"),
            Kwd("unstable"),
            Kwd("unsuccessful"),
            Kwd("cleanup"),
        ],
        "{",
        ZeroOrMore(Step),
        "}",
    )


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#post
def Post():
    return Kwd("post"), "{", ZeroOrMore(PostBlock), "}"


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#when
def WhenAll():
    return Kwd("allOf"), "{", OneOrMore(WhenCondition), "}"


def WhenAny():
    return Kwd("anyOf"), "{", OneOrMore(WhenCondition), "}"


def WhenBeforeInput():
    return Kwd("beforeInput"), Expression  # usually a litteral bool


def WhenBeforeAgent():
    return Kwd("beforeAgent"), Expression  # usually a litteral bool


def WhenBeforeOptions():
    return Kwd("beforeOptions"), Expression  # usually a litteral bool


def WhenBranch():
    return Kwd("branch"), ArgList


def WhenEnvironment():
    return Kwd("environment"), ArgList


def WhenExpression():
    return Kwd("expression"), "{", GroovyCode, "}"


def WhenEquals():
    return Kwd("equals"), ArgList


def WhenChangeset():
    return Kwd("changeset"), ArgList


def WhenChangeRequest():
    return Kwd("changeRequest"), ArgList


def WhenNot():
    return Kwd("not"), "{", OneOrMore(WhenCondition), "}"


def WhenTag():
    return Kwd("tag"), ArgList


def WhenTriggered():
    return Kwd("triggeredBy"), ArgList


def WhenQualifiers():
    return [WhenBeforeInput, WhenBeforeOptions, WhenBeforeAgent]


def WhenCondition():
    return [
        WhenExpression,
        WhenBranch,
        WhenEnvironment,
        WhenChangeset,
        WhenChangeRequest,
        WhenEquals,
        WhenTag,
        WhenTriggered,
        WhenNot,
        WhenAll,
        WhenAny,
    ]


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#when
def When():
    return (
        Kwd("when"),
        "{",
        OneOrMore([WhenQualifiers, WhenCondition]),
        "}",
    )


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#stage
def Stage():
    return (
        Kwd("stage"),
        "(",
        StringLit,
        ")",
        "{",
        UnorderedGroup(
            Optional(When),
            Optional(FailFast),
            Optional(Input),
            Optional(Tools),
            Optional(Agent),
            Optional(Environment),
            Optional([Steps, Parallel, Stages]),
            Optional(Options),
            Optional(Post),
        ),
        "}",
    )


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#options
def Options():
    return Kwd("options"), "{", ZeroOrMore(FunctionCall), "}"


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#stages
def Stages():
    return Kwd("stages"), "{", ZeroOrMore(Stage), "}"


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#tools
def Tools():
    return Kwd("tools"), DirectivesBlock


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#input
def Input():
    return Kwd("input"), DirectivesBlock


def FailFast():
    return Kwd("failFast"), BoolLit


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#triggers
def Triggers():
    return Kwd("triggers"), "{", ZeroOrMore(FunctionCall), "}"


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#pipeline
def Pipeline():
    return (
        Kwd("pipeline"),
        "{",
        UnorderedGroup(
            Optional(Agent),
            Optional(Environment),
            Optional(Parameters),
            Optional(Stages),
            Optional(Options),
            Optional(Post),
            Optional(Tools),
            Optional(Triggers),
        ),
        "}",
    )


def JunkBeforePipeline():
    return Not(Kwd("pipeline"), "{"), RestOfLine


def JunkAfterPipeline():
    return RestOfLine


def Jenkinsfile():
    return (
        Optional(SheBang),
        ZeroOrMore(JunkBeforePipeline),
        Pipeline,
        ZeroOrMore(JunkAfterPipeline),
        EOF,
    )


def parse(jenkinsfile: any, filename: str = None) -> ParseTreeNode:
    if isinstance(jenkinsfile, str):
        text = jenkinsfile
        filename = filename or "-"
    elif isinstance(jenkinsfile, Path):
        filename = filename or str(jenkinsfile)
        with jenkinsfile.open("r") as jenkinsfile_reader:
            text = jenkinsfile_reader.read()
    else:  # TextIOWrapper from argparse
        text = jenkinsfile.read()
        filename = filename or jenkinsfile.name

    return ParserPython(
        language_def=Jenkinsfile,
        comment_def=Comment,
        reduce_tree=False,
        debug=False,
        # ws="\t\r ",
    ).parse(text, filename)
