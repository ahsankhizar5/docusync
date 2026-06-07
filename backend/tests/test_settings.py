from app.settings import get_settings


def test_module_mapping_file_falls_back_when_env_path_is_missing(monkeypatch):
    monkeypatch.setenv("MODULE_MAPPING_PATH", "/var/config/module_mapping.json")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.requested_module_mapping_file.as_posix().endswith("/var/config/module_mapping.json")
    assert settings.module_mapping_file.exists()
    assert settings.module_mapping_file.name == "module_mapping.json"

    get_settings.cache_clear()
