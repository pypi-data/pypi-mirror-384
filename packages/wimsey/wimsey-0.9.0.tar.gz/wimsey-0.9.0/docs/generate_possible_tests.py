import json
import textwrap

import yaml

from wimsey.tests import _possible_tests

arg_examples = {
    "column": "column_a",
    "other_column": "column_b",
    "be_less_than": 500,
    "be_less_than_or_equal_to": 300,
    "be_exactly": 300,
    "be_greater_than": 500,
    "be_greater_than_or_equal_to": 500,
    "have": ["column_a"],
    "not_have": ["column_c"],
    "be": ["column_a", "column_b"],
    "not_be": ["column_a", "column_b", "column_c"],
    "be_one_of": ["int64", "float64"],
    "not_be_one_of": ["a", "b"],
    "match_regex": "at$",
}


def generate_doc(name: str, doc_string: str, annotations: dict) -> str:
    examples = arg_examples
    if name == "type_should":
        examples["be"] = "int64"
        examples["not_be"] = "string"
    annotations.pop("return")
    try:
        dict_eg = {k: examples[k] for k in annotations}
    except KeyError:
        msg = (
            f"Argument for function {name} can't be generated because it is "
            "not in examples within generate_possible_tests arg_examples, consider"
            " adding.\n For reference here is the list of attempted examples: "
            f"{annotations}"
        )
        raise KeyError(msg) from KeyError
    yaml_eg = yaml.dump({"test": name} | dict_eg)
    json_eg = json.dumps({"test": name} | dict_eg, indent=2)
    python_eg = f"""
from wimsey import test
from wimsey.tests import {name}

keywords = {json.dumps(dict_eg, indent=2)}

result = test(df, contract=[{name}(**keywords)])
    """
    return f"""
## {name}

{doc_string}

=== "yaml"
    ```yaml
{textwrap.indent(yaml_eg, "    ")}
    ```
=== "json"
    ```json
{textwrap.indent(json_eg, "    ")}
    ```
=== "python"
    ```python
{textwrap.indent(python_eg, "    ")}
    ```

<hr>
    """


if __name__ == "__main__":
    NL = "\n"
    file_doc: str = "# Test Catalogue 🧪\n"
    file_doc += (
        "This documentation is intended as an exaustive list of possible "
        "tests within Wimsey. Note that examples given intentionally use "
        "all possible keywords for demonstrative purposes. This isn't "
        "required, and you can give as many or as few keywords as you like "
        "with the exception of where `column` is required."
    )
    for test_name, test_generator in _possible_tests.items():
        test_doc_string = test_generator.__doc__
        assert isinstance(test_doc_string, str), (
            f"{test_generator.__name__} has no docstring, this is required for doc generation"
        )
        doc = generate_doc(
            test_name,
            " ".join(test_generator.__doc__.replace("\n", "").split()),
            test_generator.__annotations__,
        )
        file_doc += doc
    with open("docs/possible-tests.md", "w") as file:
        file.write(file_doc)
