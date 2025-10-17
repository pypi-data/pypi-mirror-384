from logging import getLogger
from importlib import import_module
from os import path, walk, sep
from pathlib import Path
from typing import Mapping

from zapp.features.core.settings import (
    LOCATORS_DIR,
    LOCATORS_FILE_POSTFIX,
)

_EM_LOCATOR_NOT_FOUND = "Не найден локатор с именем {}. Убедитесь, что локатор добавлен в один из файлов {}*{}"

log = getLogger(__name__)

_MODULE_NAME_SEPARATOR = "."


def import_locators(
    locators_dir: str = LOCATORS_DIR,
    locators_file_postfix: str = LOCATORS_FILE_POSTFIX,
    attr_name: str = "locators",
):
    locators = {}
    for current_dir, _, files in walk(locators_dir):
        normalized_dir_path = path.normpath(current_dir)
        for file in files:
            if file.endswith(locators_file_postfix):
                file_name_without_extension = Path(file).stem
                file_path = path.join(normalized_dir_path, file_name_without_extension)
                module_name = file_path.replace(sep, _MODULE_NAME_SEPARATOR)
                module = import_module(module_name)
                imported_locators = getattr(module, attr_name, None)

                if imported_locators and isinstance(imported_locators, Mapping):
                    overridden_keys = locators.keys() & imported_locators.keys()
                    locators.update(imported_locators)

                    if overridden_keys:
                        log.warning(
                            "Обнаружены пересечения в словарях локаторов, проверьте поля %s. Один из "
                            "дубликатов в файле %s",
                            overridden_keys,
                            file,
                        )

    return locators


_LOCATORS = import_locators()


def get_locator(target: str) -> str:
    result = _LOCATORS.get(target, None)
    if result is None:
        raise AttributeError(
            _EM_LOCATOR_NOT_FOUND.format(target, LOCATORS_DIR, LOCATORS_FILE_POSTFIX)
        )
    return result
