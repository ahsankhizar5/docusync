from pathlib import Path

from app.services.mapping import load_mappings, select_mapping


def test_select_mapping_matches_prefix():
    mappings = load_mappings(Path("../config/module_mapping.json"))

    selected = select_mapping(["backend/app/main.py"], mappings)

    assert selected is not None
    assert selected.module == "Backend API"


def test_select_mapping_matches_public_production_modules():
    mappings = load_mappings(Path("../config/module_mapping.json"))

    backend = select_mapping(["docusync/backend/app/main.py"], mappings)
    frontend = select_mapping(["docusync/frontend/app/page.tsx"], mappings)
    config = select_mapping(["docusync/config/module_mapping.json"], mappings)

    assert backend is not None
    assert backend.module == "Backend API"
    assert frontend is not None
    assert frontend.module == "Frontend Dashboard"
    assert config is not None
    assert config.module == "General Config and Project Docs"
