# app/control_plane/domain/templates/safety.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import yaml
from jinja2 import meta, nodes
from jinja2.visitor import NodeVisitor
from jinja2.exceptions import TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import StrictUndefined

from app.control_plane.domain.bundles.validator import bundle_dir


_ALLOWED_ROOT_VARS = {"rows", "meta", "policies"}
_ALLOWED_FILTERS = {
    "default",
    "lower",
    "upper",
    "title",
    "trim",
    "replace",
    "join",
    "length",
    "round",
}
_ALLOWED_FUNCTIONS: Set[str] = set()


@dataclass
class TemplateIssue:
    code: str
    message: str
    path: str


@dataclass
class TemplateResult:
    template_path: str
    status: str
    errors: List[Dict[str, Any]]


class _AnyAccess:
    def __getitem__(self, _: Any) -> "_AnyAccess":
        return self

    def __getattr__(self, _: str) -> "_AnyAccess":
        return self

    def __str__(self) -> str:
        return ""


class TemplateSafetyError(RuntimeError):
    pass


class TemplateSafetyValidator:
    def __init__(
        self,
        allowed_filters: Iterable[str] | None = None,
        allowed_functions: Iterable[str] | None = None,
    ) -> None:
        self.allowed_filters = set(allowed_filters or _ALLOWED_FILTERS)
        self.allowed_functions = set(allowed_functions or _ALLOWED_FUNCTIONS)

    def validate_bundle(self, tenant_id: str, bundle_id: str) -> Dict[str, Any]:
        bdir = bundle_dir(tenant_id, bundle_id)
        manifest_path = bdir / "manifest.yaml"
        if not manifest_path.exists():
            raise TemplateSafetyError(f"manifest not found: {manifest_path}")
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}

        paths = manifest.get("paths") or {}
        templates_dir = bdir / (paths.get("templates_dir") or "templates")
        entities_dir = bdir / (paths.get("entities_dir") or "entities")

        if not templates_dir.exists():
            return {
                "status": "fail",
                "templates_dir": str(templates_dir),
                "templates": [],
                "errors": [
                    {
                        "code": "templates_dir.missing",
                        "message": "templates_dir missing",
                        "path": str(templates_dir),
                    }
                ],
            }

        template_files = sorted(
            [p for p in templates_dir.rglob("*") if p.is_file() and not p.name.startswith(".")]
        )
        if not template_files:
            return {
                "status": "pass",
                "templates_dir": str(templates_dir),
                "templates": [],
                "errors": [],
            }

        results: List[TemplateResult] = []
        failures: List[Dict[str, Any]] = []

        for template_path in template_files:
            entity_fields = _load_entity_fields(entities_dir, template_path.stem)
            result = self._validate_template(template_path, entity_fields)
            results.append(result)
            if result.status != "pass":
                failures.extend(result.errors)

        status = "pass" if not failures else "fail"
        return {
            "status": status,
            "templates_dir": str(templates_dir),
            "templates": [r.__dict__ for r in results],
            "errors": failures,
        }

    def _validate_template(
        self, template_path: Path, entity_fields: Set[str] | None
    ) -> TemplateResult:
        errors: List[Dict[str, Any]] = []
        env = _sandbox_env(self.allowed_filters, self.allowed_functions)
        try:
            source = template_path.read_text(encoding="utf-8")
            ast = env.parse(source)
        except TemplateSyntaxError as exc:
            errors.append(
                {
                    "code": "template.syntax_error",
                    "message": f"{exc.message} (line {exc.lineno})",
                    "path": str(template_path),
                }
            )
            return TemplateResult(
                template_path=str(template_path), status="fail", errors=errors
            )

        undeclared = meta.find_undeclared_variables(ast)
        forbidden_roots = sorted([v for v in undeclared if v not in _ALLOWED_ROOT_VARS])
        if forbidden_roots:
            errors.append(
                {
                    "code": "template.undeclared_vars",
                    "message": f"undeclared variables not allowed: {forbidden_roots}",
                    "path": str(template_path),
                }
            )

        visitor = _TemplateSafetyVisitor(
            template_path=template_path,
            allowed_filters=self.allowed_filters,
            allowed_functions=self.allowed_functions,
            entity_fields=entity_fields,
        )
        visitor.visit(ast)
        errors.extend([e.__dict__ for e in visitor.errors])

        try:
            template = env.from_string(source)
            payload = _build_smoke_payload(entity_fields)
            template.render(**payload)
        except Exception as exc:
            errors.append(
                {
                    "code": "template.render_error",
                    "message": str(exc),
                    "path": str(template_path),
                }
            )

        status = "pass" if not errors else "fail"
        return TemplateResult(template_path=str(template_path), status=status, errors=errors)


class _TemplateSafetyVisitor(NodeVisitor):
    def __init__(
        self,
        template_path: Path,
        allowed_filters: Set[str],
        allowed_functions: Set[str],
        entity_fields: Set[str] | None,
    ) -> None:
        self.template_path = template_path
        self.allowed_filters = allowed_filters
        self.allowed_functions = allowed_functions
        self.entity_fields = entity_fields
        self.errors: List[TemplateIssue] = []
        self.row_vars: Set[str] = set()

    def visit_For(self, node: nodes.For) -> None:
        if _is_rows_iter(node.iter):
            for name in _extract_target_names(node.target):
                self.row_vars.add(name)
        self.generic_visit(node)

    def visit_Filter(self, node: nodes.Filter) -> None:
        if node.name not in self.allowed_filters:
            self._error(
                "template.filter_not_allowed",
                f"filter '{node.name}' not allowed",
            )
        self.generic_visit(node)

    def visit_Call(self, node: nodes.Call) -> None:
        name = _resolve_call_name(node.node)
        if name is None or name not in self.allowed_functions:
            self._error(
                "template.call_not_allowed",
                "function calls are not allowed",
            )
        self.generic_visit(node)

    def visit_Include(self, node: nodes.Include) -> None:
        self._error("template.include_not_allowed", "include is not allowed")
        self.generic_visit(node)

    def visit_Import(self, node: nodes.Import) -> None:
        self._error("template.import_not_allowed", "import is not allowed")
        self.generic_visit(node)

    def visit_FromImport(self, node: nodes.FromImport) -> None:
        self._error("template.import_not_allowed", "from import is not allowed")
        self.generic_visit(node)

    def visit_Extends(self, node: nodes.Extends) -> None:
        self._error("template.extends_not_allowed", "extends is not allowed")
        self.generic_visit(node)

    def visit_Getattr(self, node: nodes.Getattr) -> None:
        self._check_attribute(node, node.attr)
        self.generic_visit(node)

    def visit_Getitem(self, node: nodes.Getitem) -> None:
        key = _const_key(node.arg)
        if key is not None:
            self._check_attribute(node, key)
        self.generic_visit(node)

    def _check_attribute(self, node: nodes.Node, attr: str) -> None:
        if attr.startswith("_") or "__" in attr:
            self._error(
                "template.attribute_not_allowed",
                f"attribute '{attr}' not allowed",
            )
            return

        base = _resolve_base_name(node)
        if base == "policies" and not _is_policies_output_chain(node):
            self._error(
                "template.policies_scope_not_allowed",
                "policies access must be under policies.output",
            )
            return

        if base in self.row_vars or base == "rows":
            if self.entity_fields is None:
                return
            if attr not in self.entity_fields:
                self._error(
                    "template.field_not_allowed",
                    f"field '{attr}' not allowed by entity schema",
                )

    def _error(self, code: str, message: str) -> None:
        self.errors.append(
            TemplateIssue(code=code, message=message, path=str(self.template_path))
        )


def _sandbox_env(allowed_filters: Set[str], allowed_functions: Set[str]) -> SandboxedEnvironment:
    env = SandboxedEnvironment(undefined=StrictUndefined, autoescape=False)
    env.filters = {k: v for k, v in env.filters.items() if k in allowed_filters}
    env.globals = {k: v for k, v in env.globals.items() if k in allowed_functions}
    return env


def _build_smoke_payload(entity_fields: Set[str] | None) -> Dict[str, Any]:
    if entity_fields:
        row = {field: f"__{field}__" for field in sorted(entity_fields)}
        rows = [row]
    else:
        rows = [_AnyAccess()]
    return {
        "rows": rows,
        "meta": {"request_id": "smoke"},
        "policies": {"output": {"format": "text"}},
    }


def _load_entity_fields(entities_dir: Path, entity_id: str) -> Set[str] | None:
    if not entities_dir.exists():
        return None
    for ext in ("yaml", "yml", "json"):
        path = entities_dir / f"{entity_id}.{ext}"
        if not path.exists():
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        fields = doc.get("fields")
        if isinstance(fields, list):
            parsed = {str(f) for f in fields if str(f).strip()}
            return parsed or None
    return None


def _is_rows_iter(node: nodes.Node) -> bool:
    name = _resolve_base_name(node)
    return name == "rows"


def _extract_target_names(node: nodes.Node) -> Set[str]:
    names: Set[str] = set()
    if isinstance(node, nodes.Name):
        names.add(node.name)
    elif isinstance(node, nodes.Tuple):
        for item in node.items:
            names.update(_extract_target_names(item))
    return names


def _resolve_call_name(node: nodes.Node) -> str | None:
    if isinstance(node, nodes.Name):
        return node.name
    return None


def _const_key(node: nodes.Node) -> str | None:
    if isinstance(node, nodes.Const) and isinstance(node.value, str):
        return node.value
    return None


def _resolve_base_name(node: nodes.Node) -> str | None:
    if isinstance(node, nodes.Name):
        return node.name
    if isinstance(node, nodes.Getattr):
        return _resolve_base_name(node.node)
    if isinstance(node, nodes.Getitem):
        return _resolve_base_name(node.node)
    return None


def _is_policies_output_chain(node: nodes.Node) -> bool:
    if isinstance(node, nodes.Getattr):
        if isinstance(node.node, nodes.Name) and node.node.name == "policies":
            return node.attr == "output"
        return _is_policies_output_chain(node.node)
    if isinstance(node, nodes.Getitem):
        return _is_policies_output_chain(node.node)
    return False
