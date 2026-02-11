"""RDFLib Dataset class with decorator-based SPARQL evaluation function registration.

This module provides a DatasetExt class that extends RDFLib's Dataset to enable
registering custom SPARQL evaluation functions using a decorator pattern similar to FastAPI.
"""

from __future__ import annotations

import contextlib
import inspect
from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Generator

from rdflib import RDF, Dataset, Graph, Literal, Namespace, URIRef, Variable
from rdflib.plugins.sparql import CUSTOM_EVALS
from rdflib.plugins.sparql.evaluate import evalBGP, evalPart
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.plugins.sparql.sparql import FrozenBindings, QueryContext, SPARQLError
from rdflib.term import Identifier


def _to_node(value: Any) -> Identifier:
    """Convert Python value to RDF node."""
    if isinstance(value, Identifier):
        return value
    if isinstance(value, URIRef):
        return value
    if isinstance(value, str) and value.startswith(("http://", "https://", "urn:")):
        return URIRef(value)
    return Literal(value)


def _to_python(value: Any) -> Any:
    """Convert RDF term to Python value."""
    if isinstance(value, Literal):
        return value.toPython()
    if isinstance(value, URIRef):
        return str(value)
    return value


def _get_expr_args(expr: Any) -> list[Any]:
    """Extract arguments from a SPARQL expression object."""
    if hasattr(expr, "expr"):
        return expr.expr or []
    if hasattr(expr, "args"):
        return expr.args or []
    if hasattr(expr, "arg"):
        return [expr.arg]
    return []


def _var_label(var: Variable) -> str:
    """Get the label of a SPARQL variable without the '?' prefix."""
    label = str(var)
    return label[1:] if label.startswith("?") else label


def _snake_to_camel(name: str) -> str:
    """Convert snake_case string to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def _snake_to_pascal(name: str) -> str:
    """Convert snake_case string to PascalCase."""
    return "".join(p.title() for p in name.split("_"))


class DatasetExt(Dataset):
    """Dataset with decorator-based custom SPARQL evaluation function registration."""

    _tmp_graph_uris: set[Identifier]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._tmp_graph_uris = set()

    def _register_tmp_graph(self, graph_uri: Identifier) -> None:
        """Register a temporary graph URI for cleanup."""
        self._tmp_graph_uris.add(graph_uri)

    def _cleanup_tmp_graphs(self) -> None:
        """Clean up temporary graphs created during a `graph_function` execution."""
        if not self._tmp_graph_uris:
            return
        for graph_uri in list(self._tmp_graph_uris):
            ctx = self.get_context(graph_uri)
            with contextlib.suppress(Exception):
                ctx.remove((None, None, None))
                self.remove_context(ctx)
        self._tmp_graph_uris.clear()

    def query(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return super().query(*args, **kwargs)
        finally:
            self._cleanup_tmp_graphs()

    def type_function(
        self,
        namespace: Namespace,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a custom triple pattern evaluated by a python function.

        The function is selected by a subject typed as the class named after the
        function (PascalCase) in the provided namespace.

        Args:
            namespace: Base namespace used to infer input/output predicate IRIs.
        """
        ns_uri_str = str(namespace)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # Extract argument predicates from arg names (and defaults)
            arg_predicates: dict[str, URIRef] = {}
            arg_defaults: dict[str, Any] = {}
            signature = inspect.signature(func)
            for param_name, param in signature.parameters.items():
                if param_name not in arg_predicates:
                    arg_predicates[param_name] = namespace[_snake_to_camel(param_name)]
                if param.default is not inspect._empty:
                    arg_defaults[param_name] = param.default

            arg_predicate_by_iri: dict[URIRef, str] = {iri: name for name, iri in arg_predicates.items()}
            arg_predicate_set = set(arg_predicates.values())
            class_iri = namespace[_snake_to_pascal(func.__name__)]

            def custom_eval_func(ctx: QueryContext, part: CompValue) -> Generator[FrozenBindings, None, None]:
                """Create the custom eval function for this specific function based on the provided function and its signature."""
                if part.name != "BGP":
                    raise NotImplementedError()
                triples: list[tuple[Identifier, Identifier, Identifier]] = list(part.triples)
                # Find if this BGP contains our function class
                func_subject: Identifier | None = None
                for subj, pred, obj in triples:
                    if pred == RDF.type and obj == class_iri:
                        func_subject = subj
                        break
                if func_subject is None:
                    raise NotImplementedError()
                # This BGP is for us, return the generator
                return _eval_function(ctx, triples, func_subject)

            def _eval_function(
                ctx: QueryContext,
                triples: list[tuple[Identifier, Identifier, Identifier]],
                func_subject: Identifier,
            ) -> Generator[FrozenBindings, None, None]:
                """Evaluate a custom pattern function call."""
                # Separate our function's triples from the rest
                our_triples: list[tuple[Identifier, Identifier, Identifier]] = []
                other_triples: list[tuple[Identifier, Identifier, Identifier]] = []
                for triple in triples:
                    if triple[0] == func_subject:
                        our_triples.append(triple)
                    else:
                        other_triples.append(triple)

                # Precompute output vars (static across bindings)
                output_vars: dict[URIRef, Variable] = {}
                input_triples: list[tuple[str, Identifier]] = []
                for _, pred, obj in our_triples:
                    if isinstance(pred, URIRef) and pred in arg_predicate_by_iri:
                        input_triples.append((arg_predicate_by_iri[pred], obj))
                    elif (
                        isinstance(pred, URIRef)
                        and isinstance(obj, Variable)
                        and str(pred).startswith(ns_uri_str)
                        and pred not in arg_predicate_set
                    ):
                        output_vars[pred] = obj

                # Get initial bindings from other triples (this chains to other custom evals)
                initial_bindings = list(evalBGP(ctx, other_triples)) if other_triples else [ctx.solution()]

                # Process our function for each binding
                for bindings in initial_bindings:
                    # Extract inputs
                    inputs: dict[str, Any] = {}
                    missing_required = False
                    for arg_name, obj in input_triples:
                        value = bindings.get(obj) if isinstance(obj, Variable) else obj
                        if value is None:
                            if arg_name in arg_defaults:
                                inputs[arg_name] = arg_defaults[arg_name]
                                continue
                            missing_required = True
                            break
                        inputs[arg_name] = _to_python(value)
                    if missing_required:
                        continue
                    # Fill defaults for missing inputs
                    for arg_name, default_value in arg_defaults.items():
                        if arg_name not in inputs:
                            inputs[arg_name] = default_value
                    # Skip if missing required inputs
                    if any(arg_name not in inputs for arg_name in arg_predicates):
                        continue
                    # Call the function
                    try:
                        result = func(**inputs)
                    except Exception as e:
                        print(f"Error in custom function {func.__name__}: {e}")
                        continue
                    # Normalize results to list
                    if inspect.isgenerator(result):
                        results = list(result)
                    elif isinstance(result, list):
                        results = result
                    else:
                        results = [result]
                    results = [asdict(r) if is_dataclass(r) and not isinstance(r, type) else r for r in results]

                    # Yield bindings for each result
                    for res in results:
                        new_bindings: dict[Variable, Identifier] = dict(bindings)
                        if isinstance(res, dict):
                            for key, value in res.items():
                                if isinstance(value, list):
                                    raise SPARQLError(
                                        "Pattern function list outputs are not supported; return a list of results instead"
                                    )
                                out_pred = namespace[_snake_to_camel(str(key))]
                                if out_pred not in output_vars:
                                    continue
                                new_bindings[output_vars[out_pred]] = _to_node(value)
                        else:
                            if len(output_vars) == 1:
                                out_pred = next(iter(output_vars))
                                new_bindings[output_vars[out_pred]] = _to_node(res)
                        yield FrozenBindings(ctx, new_bindings)

            # Register with RDFLib using function name as key
            CUSTOM_EVALS[f"type_{func.__name__}"] = custom_eval_func
            return func

        return decorator

    def predicate_function(
        self,
        namespace: Namespace,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        # ) -> Callable[[Callable[[str], str | list[str]]], Callable[[str], str | list[str]]]:
        """Decorator to register a custom predicate evaluated by a python function.

        The function takes the subject as input and returns the object(s).
        The predicate IRI is generated from the function name (camelCase) + namespace.

        Args:
            namespace: Base namespace used to infer the predicate IRI.
        """

        def decorator(func: Callable[[str], str | list[str]]) -> Callable[[str], str | list[str]]:
            # Generate predicate IRI from function name
            predicate_iri = namespace[_snake_to_camel(func.__name__)]

            def custom_eval_func(ctx: QueryContext, part: CompValue) -> Generator[FrozenBindings, None, None]:
                """Create the custom eval function for this specific predicate."""
                if part.name != "BGP":
                    raise NotImplementedError()
                triples: list[tuple[Identifier, Identifier, Identifier]] = list(part.triples)
                if not any(pred == predicate_iri for _, pred, _ in triples):
                    raise NotImplementedError()
                return _eval_predicate(ctx, triples)

            def _eval_predicate(
                ctx: QueryContext,
                triples: list[tuple[Identifier, Identifier, Identifier]],
            ) -> Generator[FrozenBindings, None, None]:
                """Evaluate a custom predicate pattern call."""
                our_triples = [triple for triple in triples if triple[1] == predicate_iri]
                other_triples = [triple for triple in triples if triple[1] != predicate_iri]
                initial_bindings = list(evalBGP(ctx, other_triples)) if other_triples else [ctx.solution()]
                for bindings in initial_bindings:
                    binding_candidates: list[FrozenBindings] = [bindings]
                    for subj, _, obj in our_triples:
                        next_candidates: list[FrozenBindings] = []
                        for binding in binding_candidates:
                            subj_value = binding.get(subj) if isinstance(subj, Variable) else subj
                            if subj_value is None:
                                continue
                            try:
                                result = func(_to_python(subj_value))
                            except Exception as exc:
                                print(f"Error in custom predicate {func.__name__}: {exc}")
                                continue

                            if inspect.isgenerator(result):
                                results = list(result)
                            elif isinstance(result, list):
                                results = result
                            else:
                                results = [result]

                            for res in results:
                                node = _to_node(res)
                                if isinstance(obj, Variable):
                                    if obj in binding and binding[obj] != node:
                                        continue
                                    new_bindings = dict(binding)
                                    new_bindings[obj] = node
                                    next_candidates.append(FrozenBindings(ctx, new_bindings))
                                else:
                                    if node == obj:
                                        next_candidates.append(binding)
                        binding_candidates = next_candidates
                        if not binding_candidates:
                            break

                    yield from binding_candidates

            # Register with RDFLib
            CUSTOM_EVALS[f"predicate_{func.__name__}"] = custom_eval_func
            return func

        return decorator

    def extension_function(
        self,
        namespace: Namespace,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a custom [SPARQL extension function](https://www.w3.org/TR/sparql12-query/#extensionFunctions).

        The function can then be used in SPARQL queries as:
        `BIND(<namespace + function_name>(args...) AS ?var)`

        Args:
            namespace: Base namespace used to infer the function IRI.
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            iri_value = namespace[_snake_to_camel(func.__name__)]

            def _eval_extension_function(ctx: QueryContext, part: CompValue) -> list[Any]:
                """Evaluate a custom extension function call."""
                if part.name != "Extend":
                    raise NotImplementedError()
                if not (hasattr(part.expr, "iri") and part.expr.iri == iri_value):
                    raise NotImplementedError()

                expr_args = _get_expr_args(part.expr)
                query_results: list[Any] = []
                for eval_part in evalPart(ctx, part.p):
                    eval_ctx = eval_part.forget(ctx, _except=part._vars)
                    args = []
                    for arg_expr in expr_args:
                        arg_value = _eval(arg_expr, eval_ctx)
                        if isinstance(arg_value, SPARQLError):
                            raise arg_value
                        args.append(_to_python(arg_value))

                    try:
                        result = func(*args)
                    except Exception as exc:
                        raise SPARQLError(str(exc)) from exc

                    # Normalize results to list
                    if inspect.isgenerator(result):
                        results = list(result)
                    elif isinstance(result, list):
                        results = result
                    else:
                        results = [result]

                    for res in results:
                        if is_dataclass(res) and not isinstance(res, type):
                            res_dict = asdict(res)
                            if not res_dict:
                                raise SPARQLError("Extension function dataclass result is empty")
                            base_var = part.var
                            base_label = _var_label(base_var)
                            # Take `value` field as default output if exists, otherwise first field
                            base_field = "value" if "value" in res_dict else next(iter(res_dict.keys()))
                            bindings: dict[Variable, Identifier] = {base_var: _to_node(res_dict[base_field])}
                            for field_name, field_value in res_dict.items():
                                if field_name == base_field:
                                    continue
                                var_name = f"{base_label}{_snake_to_pascal(field_name)}"
                                bindings[Variable(var_name)] = _to_node(field_value)
                            query_results.append(eval_part.merge(bindings))
                        else:
                            query_results.append(eval_part.merge({part.var: _to_node(res)}))
                return query_results

            CUSTOM_EVALS[str(iri_value)] = _eval_extension_function
            return func

        return decorator

    def graph_function(
        self,
        namespace: Namespace,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a custom graph-producing SPARQL extension function.

        The function can then be used in SPARQL queries as:
        `BIND(<namespace + function_name>(args...) AS ?g)` and queried with `GRAPH ?g`.

        Args:
            namespace: Base namespace used to infer the function and graph IRIs.
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            iri_value = namespace[_snake_to_camel(func.__name__)]
            graph_uri = namespace[f"graph/{func.__name__}"]

            def _eval_graph_function(ctx: QueryContext, part: CompValue) -> list[Any]:
                """Evaluate a custom graph function call."""
                if part.name != "Extend":
                    raise NotImplementedError()
                if not (hasattr(part.expr, "iri") and part.expr.iri == iri_value):
                    raise NotImplementedError()

                expr_args = _get_expr_args(part.expr)
                query_results: list[Any] = []
                for eval_part in evalPart(ctx, part.p):
                    eval_ctx = eval_part.forget(ctx, _except=part._vars)
                    args = []
                    for arg_expr in expr_args:
                        arg_value = _eval(arg_expr, eval_ctx)
                        if isinstance(arg_value, SPARQLError):
                            raise arg_value
                        args.append(_to_python(arg_value))

                    try:
                        added_graph: Graph = func(*args)
                    except Exception as exc:
                        raise SPARQLError(str(exc)) from exc

                    if not isinstance(added_graph, Graph):
                        raise SPARQLError("graph_function must return an rdflib Graph")

                    graph_in_dataset = self.get_context(graph_uri)
                    for s, p, o in added_graph:
                        graph_in_dataset.add((s, p, o))
                    self._register_tmp_graph(graph_uri)
                    query_results.append(eval_part.merge({part.var: _to_node(graph_uri)}))
                return query_results

            CUSTOM_EVALS[f"graph_{func.__name__}"] = _eval_graph_function
            return func

        return decorator
