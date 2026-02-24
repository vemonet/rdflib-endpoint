import ast
import dataclasses
import inspect
import re
import textwrap
from dataclasses import dataclass
from typing import Any, Callable, get_args, get_origin

from rdflib import Namespace, URIRef


@dataclass
class CustomFunction:
    """Metadata for a custom SPARQL function registered via DatasetExt."""

    func: Callable[..., Any]
    func_type: str
    namespace: Namespace
    iri: URIRef


def snake_to_camel(name: str) -> str:
    """Convert snake_case string to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def snake_to_pascal(name: str) -> str:
    """Convert snake_case string to PascalCase."""
    return "".join(p.title() for p in name.split("_"))


def generate_docs(custom_functions: dict[str, CustomFunction], verbose: bool = False) -> str:
    """Generate markdown documentation for all registered custom functions.

    Parses each function's signature and docstring (description, Google-style
    Args section, and embedded ```sparql code blocks) to produce a Markdown
    reference document.
    """
    sections: list[str] = []
    for func_name, meta in custom_functions.items():
        func: Callable[..., Any] = meta.func
        func_type: str = meta.func_type
        iri: URIRef = meta.iri
        namespace: Namespace = meta.namespace
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or ""
        description, args_docs, returns_doc, sparql_examples = _parse_docstring(docstring)
        lines: list[str] = []
        prefix = _get_ns_prefix(namespace, sparql_examples)
        prefixed_iri = (
            f"{prefix}:{snake_to_pascal(func_name)}"
            if meta.func_type == "type_function"
            else f"{prefix}:{snake_to_camel(func_name)}"
        )
        lines.append(f"### `{prefixed_iri}`")
        lines.append("")
        if description:
            lines.append(description)
            lines.append("")
        lines.append(f"**IRI:** `{iri}`")
        if verbose:
            lines.append(f"**Namespace:** `{namespace}`")
            lines.append(f"**Function type:** {func_type.replace('_', ' ')}")
        lines.append("")
        params = sig.parameters
        # Inputs table
        if params and func_type != "predicate_function":
            in_col_header = "Arguments" if func_type == "extension_function" else "Predicate"
            lines.append("**Inputs:**")
            lines.append("")
            lines.append(f"| {in_col_header} | Type | Default | Description |")
            lines.append("|-----------------|------|---------|-------------|")
            for param_name, param in params.items():
                type_hint = _annotation_to_str(param.annotation)
                default_str = "*required*" if param.default is inspect.Parameter.empty else f"`{param.default!r}`"
                param_desc = args_docs.get(param_name, "")
                # For type_function use prefixed predicate IRI; others use Python name
                if func_type == "type_function":
                    col_name = f"`{prefix}:{snake_to_camel(param_name)}`"
                else:
                    col_name = f"`{param_name}`"
                lines.append(f"| {col_name} | `{type_hint}` | {default_str} | {param_desc} |")
            lines.append("")
        # Outputs table
        return_annotation = sig.return_annotation
        output_fields = _get_dataclass_output_fields(return_annotation)
        input_param_names = set(params.keys())
        if func_type == "predicate_function":
            if params:
                param_name, param = next(iter(params.items()))
                type_hint = _annotation_to_str(param.annotation)
                param_desc = args_docs.get(param_name, "")
                desc_suffix = f" — {param_desc}" if param_desc else ""
                lines.append(f"**Subject input:** `{param_name}` (`{type_hint}`){desc_suffix}")
                lines.append("")
            ret_str = _annotation_to_str(return_annotation)
            ret_desc_suffix = f" — {returns_doc}" if returns_doc else ""
            lines.append(f"**Object output:** `{prefixed_iri}` (`{ret_str}`){ret_desc_suffix}")
            lines.append("")
        elif func_type == "graph_function":
            graph_desc = f" — {returns_doc}" if returns_doc else ""
            lines.append(f"**Output:** `?g` (`Graph`){graph_desc}")
            lines.append("")
        else:
            out_col_header = "Variables" if func_type == "extension_function" else "Predicate"
            lines.append("**Outputs:**")
            lines.append("")
            lines.append(f"| {out_col_header} | Type | Description |")
            lines.append("|----------------------|------|-------------|")
            if func_type == "type_function":
                if output_fields:
                    for field_name, field_type, field_doc in output_fields:
                        if field_name in input_param_names:
                            continue
                        lines.append(f"| `{prefix}:{snake_to_camel(field_name)}` | `{field_type}` | {field_doc} |")
                else:
                    ret_str = _annotation_to_str(return_annotation)
                    lines.append(
                        f"| *(non-input predicates)* | `{ret_str}` | Any predicate in `{namespace}` not used as input |"
                    )
            elif func_type == "extension_function":
                if output_fields:
                    for i_f, (field_name, field_type, field_doc) in enumerate(output_fields):
                        var_label = "?var" if i_f == 0 else f"?var{snake_to_pascal(field_name)}"
                        lines.append(f"| `{var_label}` | `{field_type}` | {field_doc} |")
                else:
                    ret_str = _annotation_to_str(return_annotation)
                    lines.append(f"| `?var` | `{ret_str}` | {returns_doc} |")
            lines.append("")
        # Example
        for i, example in enumerate(sparql_examples):
            header = "**Example:**" if len(sparql_examples) == 1 else f"**Example {i + 1}:**"
            lines.append(header)
            lines.append("")
            lines.append("```sparql")
            lines.append(textwrap.dedent(example).strip())
            lines.append("```")
            lines.append("")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _annotation_to_str(annotation: Any) -> str:
    """Convert a type annotation to a compact string representation."""
    if annotation is inspect.Parameter.empty:
        return ""
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        origin_name = getattr(origin, "__name__", str(origin)).replace("typing.", "")
        if args:
            args_str = ", ".join(_annotation_to_str(a) for a in args)
            return f"{origin_name}[{args_str}]"
        return origin_name
    if hasattr(annotation, "__name__"):
        return str(annotation.__name__)
    return str(annotation).replace("typing.", "")


def _parse_docstring(docstring: str) -> tuple[str, dict[str, str], str, list[str]]:
    """Parse a docstring into a description, per-argument descriptions, a return description, and SPARQL examples.

    Returns:
        description: The summary/body text before any section headers.
        args_docs: Mapping of parameter name -> description extracted from an Args section.
        returns_doc: Text from a Returns section (first non-blank line).
        sparql_examples: List of raw SPARQL query strings from ```sparql blocks.
    """
    # Extract all ```sparql blocks first
    sparql_examples = re.findall(r"```sparql\s*\n(.*?)```", docstring, re.DOTALL | re.IGNORECASE)
    # Remove all code fences so they don't pollute section parsing
    clean = re.sub(r"```.*?```", "", docstring, flags=re.DOTALL)
    # Known section headers (Google style)
    section_re = re.compile(
        r"^(Args|Arguments|Parameters|Returns|Return|Raises|Example|Examples|Note|Notes):\s*$", re.IGNORECASE
    )

    lines = clean.splitlines()
    description_lines: list[str] = []
    args_docs: dict[str, str] = {}
    returns_lines: list[str] = []
    in_description = True
    in_args = False
    in_returns = False
    current_arg: str | None = None
    current_arg_lines: list[str] = []

    def _flush_arg() -> None:
        if current_arg and current_arg_lines:
            args_docs[current_arg] = " ".join(current_arg_lines).strip()

    for line in lines:
        stripped = line.strip()
        # Detect section header
        if section_re.match(stripped):
            in_description = False
            in_args = stripped.lower().startswith(("args", "arguments", "parameters"))
            in_returns = stripped.lower().startswith(("return",))
            _flush_arg()
            current_arg = None
            current_arg_lines = []
            continue

        if in_description:
            description_lines.append(line.rstrip())
            continue

        if in_returns:
            if stripped:
                # Strip optional "TypeName: " or "TypeName[...]: " prefix from Google-style Returns
                returns_lines.append(re.sub(r"^[\w\[\], ]+:\s*", "", stripped))
            continue

        if in_args:
            # Detect a new arg: "    param_name: description" or "    param_name (type): description"
            arg_match = re.match(r"^    (\w+)(?:\s*\([^)]*\))?:\s*(.*)", line)
            if arg_match:
                _flush_arg()
                current_arg = arg_match.group(1)
                current_arg_lines = [arg_match.group(2)] if arg_match.group(2) else []
            elif current_arg and line.startswith("        "):
                # Continuation of current arg description
                current_arg_lines.append(stripped)
    _flush_arg()

    # Clean up description: strip trailing blank lines
    while description_lines and not description_lines[-1].strip():
        description_lines.pop()
    description = "\n".join(description_lines).strip()
    returns_doc = " ".join(returns_lines).strip()
    return description, args_docs, returns_doc, sparql_examples


def _unwrap_return_type(annotation: Any) -> Any:
    """Unwrap List[T] / list[T] to the inner type T; return annotation as-is otherwise."""
    if annotation is inspect.Parameter.empty:
        return None
    origin = get_origin(annotation)
    if origin is list:
        args = get_args(annotation)
        if args:
            return args[0]
    return annotation


def _get_dataclass_output_fields(return_annotation: Any) -> list[tuple[str, str, str]]:
    """Return (field_name, type_str, description) triples from a dataclass return type, or empty list.

    The description is read from a PEP 257 attribute docstring (a string literal
    immediately following the field), with ``dataclasses.field(metadata={"doc": "..."})``
    as a fallback.
    """
    inner: Any = _unwrap_return_type(return_annotation)
    if inner is None or not dataclasses.is_dataclass(inner):
        return []
    # field_docs = _get_field_docstrings(inner)
    field_docs: dict[str, str] = {}
    try:
        # Ensure we pass the class type, not an instance
        source = textwrap.dedent(inspect.getsource(inner if isinstance(inner, type) else inner.__class__))
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            body = node.body
            for i, stmt in enumerate(body):
                if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
                    continue
                field_name = stmt.target.id
                if i + 1 < len(body):
                    next_stmt = body[i + 1]
                    if (
                        isinstance(next_stmt, ast.Expr)
                        and isinstance(next_stmt.value, ast.Constant)
                        and isinstance(next_stmt.value.value, str)
                    ):
                        field_docs[field_name] = next_stmt.value.value.strip()
    except (OSError, TypeError, SyntaxError):
        pass
    return [
        (
            f.name,
            _annotation_to_str(f.type),
            str(field_docs.get(f.name) or (f.metadata.get("doc", "") if f.metadata else "")),
        )
        for f in dataclasses.fields(inner)
    ]


def _get_ns_prefix(namespace: Namespace, sparql_examples: list[str]) -> str:
    """Derive a short prefix string from a namespace URI.

    - Returns 'func' for the default SPARQL function namespace.
    - Otherwise, takes the last non-empty token after splitting on '/', '#', or ':'
      and removes non-alphanumeric characters.
    """
    ns = str(namespace)
    # Try to extract from examples query
    pattern = re.compile(r"PREFIX\s+(\w*):\s*<([^>]+)>", re.IGNORECASE)
    for example in sparql_examples:
        for match in pattern.finditer(example):
            prefix_label, uri = match.group(1), match.group(2)
            if uri == ns or uri.rstrip("#/") == ns.rstrip("#/"):
                return prefix_label
    # Split on common separators and take last non-empty token
    parts = [p for p in re.split(r"[#/:]", ns) if p]
    if not parts:
        return "ns"
    candidate = parts[-1]
    # Remove non-word characters and ensure it starts with a letter
    candidate = re.sub(r"[^0-9A-Za-z_]", "", candidate)
    if not candidate:
        return "func"
    # Lowercase first char to form a reasonable prefix
    return candidate[0].lower() + candidate[1:]
