import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModuleMapping:
    module: str
    path_prefixes: list[str]
    notion_target_id: str
    fallback_docs: str


def load_mappings(path: Path) -> list[ModuleMapping]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ModuleMapping(
            module=item["module"],
            path_prefixes=item["path_prefixes"],
            notion_target_id=item["notion_target_id"],
            fallback_docs=item.get("fallback_docs", ""),
        )
        for item in data.get("modules", [])
    ]


def select_mapping(changed_files: list[str], mappings: list[ModuleMapping]) -> ModuleMapping | None:
    for changed_file in changed_files:
        normalized = changed_file.replace("\\", "/")
        for mapping in mappings:
            if any(normalized.startswith(prefix) for prefix in mapping.path_prefixes):
                return mapping
    return mappings[0] if mappings else None
