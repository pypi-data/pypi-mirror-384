import ast
import inspect

from tests.util import requires_grpclib  # noqa: F401


def check(generated_doc: str, type: str) -> None:
    assert f"Documentation of {type} 1" in generated_doc
    assert "other line 1" in generated_doc
    assert f"Documentation of {type} 2" in generated_doc
    assert "other line 2" in generated_doc
    assert f"Documentation of {type} 3" in generated_doc


def test_documentation(requires_grpclib) -> None:
    from .outputs.documentation.documentation import (
        Enum,
        ServiceBase,
        ServiceStub,
        Test,
    )

    check(Test.__doc__, "message")
    check(Test.__doc__, "oneof")

    source = inspect.getsource(Test)
    tree = ast.parse(source)
    check(tree.body[0].body[2].value.value, "field")

    check(Enum.__doc__, "enum")

    source = inspect.getsource(Enum)
    tree = ast.parse(source)
    check(tree.body[0].body[2].value.value, "variant")

    check(ServiceBase.__doc__, "service")
    check(ServiceBase.get.__doc__, "method")

    check(ServiceStub.__doc__, "service")
    check(ServiceStub.get.__doc__, "method")


def test_escaping(requires_grpclib) -> None:
    from .outputs.documentation.documentation import ComplexDocumentation

    ComplexDocumentation.__doc__ == """
    A comment with backslashes \\ and triple quotes \"\"\"
    Simple quotes are not escaped "
    """
