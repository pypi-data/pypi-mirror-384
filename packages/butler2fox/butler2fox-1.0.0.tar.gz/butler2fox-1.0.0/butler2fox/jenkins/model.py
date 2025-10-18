import sys
from dataclasses import dataclass

from arpeggio import ParseTreeNode, PTNodeVisitor


class JenkinsModelBuilder(PTNodeVisitor):
    # implement auto class mapping
    # def visit__default__(self, node: ParseTreeNode, children: list[any]):
    #     auto_type = type(node.rule_name)
    #     if auto_type:
    #         return auto_type(children)
    #     return super().visit__default__(node, children)

    def _dump(self, node: ParseTreeNode, children: list[any]):
        print(f"{node.rule_name}: {len(children)} children", file=sys.stderr)
        for child in children:
            print(f"- ({type(child).__name__}): {child}", file=sys.stderr)

    def visit_BoolLit(self, node: ParseTreeNode, children: list[any]):
        return node.value == "true"

    def visit_NumberLit(self, node: ParseTreeNode, children: list[any]):
        return int(node.value)

    def visit_Identifier(self, node: ParseTreeNode, children: list[any]):
        return Identifier(node.value)

    def visit_StringLit(self, node: ParseTreeNode, children: list[any]):
        if len(children) == 0:
            # empty string
            return ""
        # self._dump(node, children)
        quoted: str = children[0]
        if quoted.startswith("'''") or quoted.startswith('"""'):
            # multi-line string
            return unescape(quoted[3:-3], strip_indent=True)
        return unescape(quoted[1:-1])

    def visit_Arg(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return Arg(name=children[0] if len(children) >= 2 else None, value=children[-1])

    def visit_ArgList(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return Args(children)

    def visit_COMMA(self, node: ParseTreeNode, children: list[any]):
        # sink
        return None

    def visit_Array(self, node: ParseTreeNode, children: list[any]):
        return children

    def visit_EmptyMap(self, node: ParseTreeNode, children: list[any]):
        return dict()

    def visit_Map(self, node: ParseTreeNode, children: list[any]):
        return {children[idx]: children[idx + 1] for idx in range(0, len(children), 2)}

    def visit_FunctionCallParen(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return FunctionCall(
            name=children[0], args=children[1] if len(children) > 1 else Args()
        )

    def visit_FunctionCallNoParen(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return FunctionCall(
            name=children[0], args=children[1] if len(children) > 1 else Args()
        )

    def visit_BinaryExpression(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return BinaryExpression(
            operator=children[0],
            right=children[1],
        )

    def visit_MethodExpression(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return MethodExpression(
            method=children[0],
            args=children[1] if len(children) >= 2 else Args(),
        )

    def visit_FieldExpression(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return FieldExpression(
            field=children[0],
        )

    def visit_IndexExpression(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return IndexExpression(
            index=children[0],
        )

    def visit_Expression(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        # TODO: not quite exact (priority)
        for idx in range(len(children) - 1, 0, -1):
            children[idx].left = children[idx - 1]
        return children[-1]

    def visit_EnvEntry(self, node: ParseTreeNode, children: list[any]):
        return (children[0], children[1])

    def visit_DirectiveEntry(self, node: ParseTreeNode, children: list[any]):
        return (children[0], children[1])

    def visit_DirectivesBlock(self, node: ParseTreeNode, children: list[any]):
        return {key: value for key, value in children or {}}

    def visit_K8sAgent(self, node: ParseTreeNode, children: list[any]):
        return K8sAgent(children[0])

    def visit_DockerAgent(self, node: ParseTreeNode, children: list[any]):
        return (
            DockerNamedAgent(children[0])
            if isinstance(children[0], str)
            else DockerAgent(children[0])
        )

    def visit_DockerfileAgent(self, node: ParseTreeNode, children: list[any]):
        return DockerfileAgent(children[0])

    def visit_NodeAgent(self, node: ParseTreeNode, children: list[any]):
        return NodeAgent(children[0])

    def visit_LabelAgent(self, node: ParseTreeNode, children: list[any]):
        return LabelAgent(children[0])

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#agent
    def visit_Agent(self, node: ParseTreeNode, children: list[any]):
        return Agent(children[0])

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#environment
    def visit_Environment(self, node: ParseTreeNode, children: list[any]):
        return Environment({key: value for key, value in children})

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#parameters
    def visit_Parameters(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return Parameters(children)

    def visit_GroovyCode(self, node: ParseTreeNode, children: list[any]):
        return "".join(children)

    def visit_GroovyBlock(self, node: ParseTreeNode, children: list[any]):
        return "{" + children[0] + "}"

    def visit_ScriptStep(self, node: ParseTreeNode, children: list[any]):
        return ScriptStep(children[0])

    def visit_BlockStep(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return BlockStep(
            name=children[0],
            args=children[1],  # TODO: optional ?
            steps=children[2:],
        )

    def visit_Steps(self, node: ParseTreeNode, children: list[any]):
        return Steps(children)

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#parallel
    def visit_Parallel(self, node: ParseTreeNode, children: list[any]):
        return Parallel(children)

    def visit_PostBlock(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return PostBlock(children[0], children[1:])

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#post
    def visit_Post(self, node: ParseTreeNode, children: list[any]):
        return Post(children)

    def visit_WhenAll(self, node: ParseTreeNode, children: list[any]):
        return WhenAll(children)

    def visit_WhenAny(self, node: ParseTreeNode, children: list[any]):
        return WhenAny(children)

    def visit_WhenBeforeInput(self, node: ParseTreeNode, children: list[any]):
        return WhenBeforeInput(children[0])

    def visit_WhenBeforeAgent(self, node: ParseTreeNode, children: list[any]):
        return WhenBeforeAgent(children[0])

    def visit_WhenBeforeOptions(self, node: ParseTreeNode, children: list[any]):
        return WhenBeforeOptions(children[0])

    def visit_WhenBranch(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        args: Args = children[0]
        return WhenBranch(
            pattern=args.get("pattern", posidx=0),
            comparator=args.get("comparator", dflt="EQUALS"),
        )

    def visit_WhenEnvironment(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        args: Args = children[0]
        return WhenEnvironment(args.get("name"), args.get("value"))

    def visit_WhenEquals(self, node: ParseTreeNode, children: list[any]):
        args: Args = children[0]
        return WhenEquals(args.get("actual"), args.get("expected"))

    def visit_WhenChangeset(self, node: ParseTreeNode, children: list[any]):
        args: Args = children[0]
        return WhenChangeset(
            pattern=args.get("pattern", posidx=0),
            comparator=args.get("comparator", dflt="EQUALS"),
            case_sensitive=args.get("caseSensitive", dflt=False),
        )

    def visit_WhenChangeRequest(self, node: ParseTreeNode, children: list[any]):
        args: Args = children[0]
        return WhenChangeRequest(args)

    def visit_WhenNot(self, node: ParseTreeNode, children: list[any]):
        return WhenNot(children[0])

    def visit_WhenTag(self, node: ParseTreeNode, children: list[any]):
        args: Args = children[0]
        return WhenTag(
            pattern=args.get("pattern", posidx=0),
            comparator=args.get("comparator", dflt="EQUALS"),
        )

    def visit_WhenTriggered(self, node: ParseTreeNode, children: list[any]):
        args: Args = children[0]
        return WhenTriggered(args.get("cause", posidx=0))

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#when
    def visit_When(self, node: ParseTreeNode, children: list[any]):
        return When(children)

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#stage
    def visit_Stage(self, node: ParseTreeNode, children: list[any]):
        # print(f"visit_Stage: {node.rule_name}: {node.comments} children", file=sys.stderr)
        stage = Stage(name=children[0])
        for child in children[1:]:
            if isinstance(child, When):
                stage.when = child
            elif isinstance(child, FailFast):
                stage.fail_fast = child
            elif isinstance(child, Input):
                stage.input = child
            elif isinstance(child, Tools):
                stage.tools = child
            elif isinstance(child, Agent):
                stage.agent = child
            elif isinstance(child, Environment):
                stage.environment = child
            elif isinstance(child, Steps):
                stage.steps = child
            elif isinstance(child, Parallel):
                stage.parallel = child
            elif isinstance(child, Stages):
                stage.stages = child
            elif isinstance(child, Options):
                stage.options = child
            elif isinstance(child, Post):
                stage.post = child
            else:
                raise Exception(f"Unknown child: {child}")
        return stage

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#options
    def visit_Options(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return Options(children)

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#stages
    def visit_Stages(self, node: ParseTreeNode, children: list[any]):
        return Stages(children)

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#tools
    def visit_Tools(self, node: ParseTreeNode, children: list[any]):
        # self._dump(node, children)
        return Tools(children[0])

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#input
    def visit_Input(self, node: ParseTreeNode, children: list[any]):
        return Input(children[0])

    def visit_FailFast(self, node: ParseTreeNode, children: list[any]):
        return FailFast(children[0])

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#triggers
    def visit_Triggers(self, node: ParseTreeNode, children: list[any]):
        return Triggers(children)

    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#pipeline
    def visit_Pipeline(self, node: ParseTreeNode, children: list[any]):
        pipeline = Pipeline()
        for child in children:
            if isinstance(child, Agent):
                pipeline.agent = child
            elif isinstance(child, Environment):
                pipeline.environment = child
            elif isinstance(child, Parameters):
                pipeline.parameters = child
            elif isinstance(child, Stages):
                pipeline.stages = child
            elif isinstance(child, Options):
                pipeline.options = child
            elif isinstance(child, Post):
                pipeline.post = child
            elif isinstance(child, Tools):
                pipeline.tools = child
            elif isinstance(child, Triggers):
                pipeline.triggers = child
            else:
                raise ValueError(f"Unknown child: {child}")
        return pipeline


def unescape(raw: str, strip_indent=False) -> str:
    if strip_indent:
        lines = raw.splitlines()
        if len(lines) > 1:
            # count the min number of whitespaces over each line
            min_indent = min(len(line) - len(line.lstrip()) for line in lines[1:])
            # strip each line by the number of whitespaces
            raw = "\n".join(line[min_indent:] for line in lines)

    # then escape characters
    escaped = []
    esc = False
    for char in raw:
        if esc:
            if char == "n":
                escaped.append("\n")
            elif char == "t":
                escaped.append("\t")
            elif char == "r":
                escaped.append("\r")
            elif char == "'":
                escaped.append("'")
            elif char == '"':
                escaped.append('"')
            else:
                escaped.append("\\")
                escaped.append(char)
            esc = False
        elif char == "\\":
            esc = True
        else:
            escaped.append(char)

    return "".join(escaped)


# class BoolLit(bool, Literal):
#     pass

# class NumberLit(int, Literal):
#     pass


class Identifier(str):
    def __repr__(self):
        return self


env = Identifier("env")
params = Identifier("params")


@dataclass
class Arg:
    value: any
    name: str = None

    def __repr__(self):
        if self.name:
            return f"{self.name}: {self.value.__repr__()}"
        return self.value.__repr__()


class Args(list[Arg]):
    def get(self, key: str | int, posidx=None, dflt=None) -> any:
        """Looks for the given argument and returns its value or specified default value."""
        if isinstance(key, int):
            return self[key].value
        # return self.args[key]
        for arg in self:
            if arg.name == key:
                return arg.value
        if posidx is not None and posidx < len(self):
            return self[posidx].value
        return dflt

    def __repr__(self):
        return "[" + ", ".join(arg.__repr__() for arg in self) + "]"


class ChainedExpression:
    left: any = None


@dataclass
class BinaryExpression(ChainedExpression):
    operator: str
    right: any

    def __repr__(self):
        return f"{self.left.__repr__() if self.left else '?'} {self.operator} {self.right.__repr__()}"


@dataclass
class FieldExpression(ChainedExpression):
    field: Identifier

    def __repr__(self):
        return f"{self.left.__repr__() if self.left else '?'}.{self.field.__repr__()}"


@dataclass
class IndexExpression(ChainedExpression):
    index: any

    def __repr__(self):
        return f"{self.left.__repr__() if self.left else '?'}[{self.index.__repr__()}]"


@dataclass
class FunctionCall:
    name: str
    args: Args = None

    def __repr__(self):
        return f"{self.name}({', '.join(arg.__repr__() for arg in self.args)})"


@dataclass
class MethodExpression(ChainedExpression):
    method: str
    args: Args

    def __repr__(self):
        return f"{self.left.__repr__() if self.left else '?'}({', '.join(arg.__repr__() for arg in self.args)})"


class K8sAgent(dict[str, any]):
    def __repr__(self):
        return "kubernetes " + super().__repr__()


@dataclass
class DockerNamedAgent:
    name: any

    def __repr__(self):
        return f"docker {self.name.__repr__()}"


class DockerAgent(dict[str, any]):
    def __repr__(self):
        return "docker " + super().__repr__()


class DockerfileAgent(dict[str, any]):
    def __repr__(self):
        return "dockerfile " + super().__repr__()


class NodeAgent(dict[str, any]):
    def __repr__(self):
        return "node " + super().__repr__()


@dataclass
class LabelAgent:
    name: any

    def __repr__(self):
        return f"label {self.name.__repr__()}"


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#agent
@dataclass
class Agent:
    agent: K8sAgent | DockerAgent | DockerfileAgent | NodeAgent | LabelAgent | str


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#environment
class Environment(dict[str, any]):
    def __repr__(self):
        return "environment " + super().__repr__()


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#parameters
class Parameters(list[FunctionCall]):
    def __repr__(self):
        return "parameters " + super().__repr__()


# class CheckoutScmStep:
#     def __repr__(self):
#         return "checkout scm"


@dataclass
class BlockStep:
    name: str
    args: Args = None
    steps: list[any] = None

    def __repr__(self):
        return (
            f"{self.name}({', '.join(arg.__repr__() for arg in self.args)}) "
            + self.steps.__repr__()
        )


@dataclass
class ScriptStep:
    groovy: str

    def __repr__(self):
        return f"script {{{self.groovy}}}"


class Steps(list):
    def __repr__(self):
        return "steps " + super().__repr__()


@dataclass
class PostBlock:
    name: str
    steps: list[any] = None

    def __repr__(self):
        return self.name + " " + self.steps.__repr__()


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#post
class Post(list[PostBlock]):
    def __repr__(self):
        return "post " + super().__repr__()

    def get(self, name: str) -> PostBlock | None:
        return next(filter(lambda b: b.name == name, self), None)


class WhenQualifier:
    pass


@dataclass
class WhenBeforeInput(WhenQualifier):
    value: bool


@dataclass
class WhenBeforeAgent(WhenQualifier):
    value: bool


@dataclass
class WhenBeforeOptions(WhenQualifier):
    value: bool


class WhenCondition:
    def invert(self) -> any:
        pass


class WhenAll(WhenCondition, list[WhenCondition]):
    def __repr__(self):
        return self.__class__.__name__ + super().__repr__()

    def invert(self):
        return WhenAny(map(lambda c: c.invert(), self))


class WhenAny(WhenCondition, list[WhenCondition]):
    def __repr__(self):
        return self.__class__.__name__ + super().__repr__()

    def invert(self):
        return WhenAll(map(lambda c: c.invert(), self))


@dataclass
class WhenBranch(WhenCondition):
    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#built-in-conditions
    pattern: any
    comparator: str
    inverted = False

    def invert(self):
        inverted = WhenBranch(self.pattern, self.comparator)
        inverted.inverted = not self.inverted
        return inverted


@dataclass
class WhenEnvironment(WhenCondition):
    name: str
    value: any
    inverted = False

    def invert(self):
        inverted = WhenEnvironment(self.name, self.value)
        inverted.inverted = not self.inverted
        return inverted


@dataclass
class WhenExpression(WhenCondition):
    groovy: str
    inverted = False

    def invert(self):
        inverted = WhenExpression(self.name, self.value)
        inverted.inverted = not self.inverted
        return inverted


@dataclass
class WhenEquals(WhenCondition):
    actual: any
    expected: any
    inverted = False

    def invert(self):
        inverted = WhenEquals(self.actual, self.expected)
        inverted.inverted = not self.inverted
        return inverted


@dataclass
class WhenChangeset(WhenCondition):
    pattern: any
    comparator: str
    case_sensitive: bool
    inverted = False

    def invert(self):
        inverted = WhenChangeset(self.pattern, self.comparator, self.case_sensitive)
        inverted.inverted = not self.inverted
        return inverted


@dataclass
class WhenChangeRequest(WhenCondition):
    args: Args
    inverted = False

    def invert(self):
        inverted = WhenChangeRequest(self.args)
        inverted.inverted = not self.inverted
        return inverted


@dataclass
class WhenNot(WhenCondition):
    condition: WhenCondition

    def invert(self):
        return self.condition


@dataclass
class WhenTag(WhenCondition):
    # see: https://www.jenkins.io/doc/book/pipeline/syntax/#built-in-conditions
    pattern: any
    comparator: str
    inverted = False

    def invert(self):
        inverted = WhenTag(self.pattern, self.comparator)
        inverted.inverted = not self.inverted
        return inverted


@dataclass
class WhenTriggered(WhenCondition):
    cause: any
    detail = None
    inverted = False

    def invert(self):
        inverted = WhenTriggered(self.cause)
        inverted.inverted = not self.inverted
        return inverted


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#when
class When(list[WhenCondition | WhenQualifier]):
    def conditions(self) -> list[WhenCondition]:
        return [child for child in self if isinstance(child, WhenCondition)]


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#options
class Options(list[FunctionCall]):
    pass


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#tools
class Tools(dict[str, any]):
    pass


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#input
class Input(dict[str, any]):
    pass


@dataclass
class FailFast:
    value: bool


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#triggers
class Triggers(list[FunctionCall]):
    def __repr__(self):
        return self.__class__.__name__ + super().__repr__()


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#stage
@dataclass
class Stage:
    name: str
    when: When = None
    fail_fast: FailFast = None
    input: Input = None
    tools: Tools = None
    agent: Agent = None
    environment: Environment = None
    options: Options = None
    post: Post = None
    # exactly one of the 3 following...
    stages: "Stages" = None
    parallel: "Parallel" = None
    steps: Steps = None


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#parallel
class Parallel(list[Stage]):
    def __repr__(self):
        return self.__class__.__name__ + super().__repr__()


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#stages
class Stages(list[Stage]):
    def __repr__(self):
        return self.__class__.__name__ + super().__repr__()


# see: https://www.jenkins.io/doc/book/pipeline/syntax/#pipeline
@dataclass
class Pipeline:
    agent: Agent = None
    environment: Environment = None
    parameters: Parameters = None
    stages: Stages = None
    options: Options = None
    post: Post = None
    tools: Tools = None
    triggers: Triggers = None
