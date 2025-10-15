from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class CrossOutputPaths:
    python_types_output: str
    typescript_types_output: str
    typescript_routes_output_by_endpoint: dict[str, str]
    typespec_files_input: list[str]
