import os
import re

from esi.openapi_clients import ESIClientProvider

from django.core.management.base import BaseCommand

from esi import __title__, __url__, __version__, stubs, __build_date__

# OpenAPI Types to Python
TYPE_MAP = {
    "integer": "int",
    "number": "float",
    "string": "str",
    "boolean": "bool",
    "array": "list[Any]",
    "object": "dict[str, Any]",
}


def sanitize_class_name(name: str) -> str:
    """Convert a tag into a valid Python class name."""
    sanitized = re.sub(r'[^0-9a-zA-Z_]', '_', name.strip())
    if sanitized and not sanitized[0].isalpha():
        sanitized = f"_{sanitized}"
    return sanitized


def sanitize_operation_class(name: str) -> str:
    return re.sub(r'[^0-9a-zA-Z_]', '', name[0].upper() + name[1:] + "Operation")


def schema_to_type(schema) -> str:
    """Convert an OpenAPI schema to a Python type hint."""
    if not schema:
        return "Any"
    schema_type = getattr(schema, "type", None)
    if schema_type == "array":
        items_schema = getattr(schema, "items", None)
        inner = schema_to_type(items_schema)
        return f"list[{inner}]"
    if schema_type == "object":
        return "dict[str, Any]"
    return TYPE_MAP.get(schema_type, "Any")


class Command(BaseCommand):
    help = "Generate ESI Stubs from the current ESI spec with correct type hints."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=None,
            help="Custom output path for the generated ESI stub file (default: stubs.pyi next to openapi_clients.py).",
        )
        parser.add_argument(
            "--compatibility_date",
            default=__build_date__,
            help="Compatibility Date to build ESI Stubs from.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting ESI stub generation...")

        stub_api = ESIClientProvider(
            ua_appname=__title__,
            ua_url=__url__,
            ua_version=__version__,
            compatibility_date=options["compatibility_date"]
        )

        stub_api = stub_api.client.api

        base_path = os.path.dirname(stubs.__file__)
        output_path = options["output"] or os.path.join(base_path, "stubs.pyi")

        self.stdout.write(f"Outputting to: {output_path}")

        spec_root = stub_api._root
        with open(output_path, "w", encoding="utf-8") as f:
            # File headers
            f.write("# flake8: noqa=E501\n")
            f.write("# Auto Generated do not edit\n")
            # Python Imports
            f.write("from typing import Any\n\n")
            f.write("from esi.openapi_clients import EsiOperation\n")
            f.write("from esi.models import Token\n\n\n")

            operation_classes = {}

            for tag in sorted(stub_api._operationindex._tags.keys()):
                # ESI Operation
                # The various methods called on an ESI Operation
                # result(), Results(), Results_Localized() etc. all live here
                ops = stub_api._operationindex._tags[tag]
                for nm, op in sorted(ops._operations.items()):
                    op_type = op[0]
                    op_obj = op[2]
                    docstring = (op_obj.description or op_obj.summary or "").replace("\n", " ").strip()
                    op_class_name = sanitize_operation_class(nm)

                    response_type = "Any"
                    try:
                        match op_type:
                            case "post":
                                resp_201 = op_obj.responses.get("201")
                                if resp_201 and "application/json" in resp_201.content:
                                    response_type = schema_to_type(resp_201.content["application/json"].schema_)
                            case "put" | "delete":
                                response_type = "None"
                            case _:
                                resp_200 = op_obj.responses.get("200")
                                if resp_200 and "application/json" in resp_200.content:
                                    response_type = schema_to_type(resp_200.content["application/json"].schema_)

                    except Exception:
                        response_type = "Any"

                    results_type = response_type if response_type.startswith("list[") else f"list[{response_type}]"

                    if op_class_name not in operation_classes:
                        f.write(f"class {op_class_name}(EsiOperation):\n")
                        if response_type != "None":
                            f.write("    \"\"\"EsiOperation, use result(), results() or results_localized()\"\"\"\n")
                        else:
                            f.write("    \"\"\"EsiOperation, use result()\"\"\"\n")

                        # result()
                        f.write(f"    def result(self, use_etag: bool = True, return_response: bool = False, force_refresh: bool = False, use_cache: bool = True, **extra) -> {response_type}:\n")  # noqa: E501
                        f.write(f"        \"\"\"{docstring}\"\"\"\n") if docstring else None
                        f.write("        ...\n\n")
                        if response_type != "None":
                            # We only need the extra utility functions if its actually an endpoint that returns data
                            # results()
                            f.write(f"    def results(self, use_etag: bool = True, return_response: bool = False, force_refresh: bool = False, use_cache: bool = True, **extra) -> {results_type}:\n")  # noqa: E501
                            f.write(f"        \"\"\"{docstring}\"\"\"\n") if docstring else None
                            f.write("        ...\n\n")

                            # results_localized()
                            f.write(f"    def results_localized(self, languages: list[str] | str | None = None, **extra) -> dict[str, {results_type}]:\n")
                            f.write(f"        \"\"\"{docstring}\"\"\"\n") if docstring else None
                            f.write("        ...\n\n\n")

                        operation_classes[op_class_name] = True

            f.write("class ESIClientStub:\n")
            for tag in sorted(stub_api._operationindex._tags.keys()):
                # ESI ESIClientStub
                # The various ESI Tags and Operations
                ops = stub_api._operationindex._tags[tag]
                class_name = f"_{sanitize_class_name(tag)}"
                f.write(f"    class {class_name}:\n")
                for nm, op in sorted(ops._operations.items()):
                    op_obj = op[2]
                    effective_security = (
                        getattr(op_obj, "security", None) or getattr(spec_root, "security", None)
                    )

                    def _has_oauth2(sec) -> bool:
                        data = sec if isinstance(sec, dict) else getattr(sec, "root", None)
                        if not isinstance(data, dict):
                            return False
                        return any(k.lower() == "oauth2" for k in data)

                    needs_oauth = any(_has_oauth2(s) for s in (effective_security or []))

                    params = ["self"]
                    optional_params = []
                    if getattr(op_obj, "requestBody", None):
                        params.append(f"body: {schema_to_type(op_obj.requestBody.content['application/json'].schema_)}")

                    for p in getattr(op_obj, "parameters", []):
                        required = getattr(p, "required", False)
                        schema_type_value = getattr(getattr(p, "schema_", None), "type", None)
                        if isinstance(schema_type_value, str):
                            param_type = TYPE_MAP.get(schema_type_value, "Any")
                        else:
                            param_type = "Any"
                        default = ""
                        if not required:
                            param_type = f"{param_type} | None"
                            default = " = ..."
                        param_name = p.name.replace("-", "_")
                        if param_name == "authorization" and needs_oauth:
                            # Skip the Authorization Parameter, we inject this at HTTP Header Level
                            continue
                        if required:
                            params.append(f"{param_name}: {param_type}{default}")
                        else:
                            optional_params.append(f"{param_name}: {param_type}{default}")
                    if needs_oauth:
                        # Here, we add our own custom param instead of the earlier Authorization
                        # Our library will pick this up and use it later
                        params.append("token: Token")
                    optional_params.append("**kwargs: Any")
                    params_str = ", ".join(params + optional_params)
                    op_class_name = sanitize_operation_class(nm)
                    docstring = (op_obj.description or op_obj.summary or "").replace("\n", " ").strip()

                    if docstring:
                        f.write(f"        def {nm}({params_str}) -> {op_class_name}:\n")
                        f.write(f"            \"\"\"{docstring}\"\"\"\n")
                        f.write("            ...\n\n")
                    else:
                        f.write(f"        def {nm}({params_str}) -> {op_class_name}: ...\n")
                f.write(f"\n    {sanitize_class_name(tag)}: {class_name} = {class_name}()\n\n")

        self.stdout.write(self.style.SUCCESS(f"ESI stubs written to {output_path}"))
