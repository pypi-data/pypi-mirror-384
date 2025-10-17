from typing import (
    Dict,
    Tuple,
)

from django.apps import (
    apps,
)
from django.conf import (
    settings,
)

from enum import (
    Enum,
)


def get_default_value():
    """
    Получение значения пути по-умолчанию для варианта "Не указано"
    """
    if settings.BEHAVE_TEST_RECORDER__ENABLE:
        return str(
            settings.BEHAVE_TEST_RECORDER__PROJECT_ROOT_DIR_PATH /
            settings.BEHAVE_TEST_RECORDER__STORED_GENERATED_FILES_PATH
        )


def get_apps_configs():
    """
    Получить список конфигураций django-приложений проекта
    """
    if settings.BEHAVE_TEST_RECORDER__ENABLE:
        apps_configs = apps.get_app_configs()
    else:
        apps_configs = []

    return apps_configs


class DjangoAppsPathsEnum(object):
    """
    Перечисление путей django-apps и соответствующих им verbose_name,
    только если путь соответствует выбранному для записи приложению.
    """
    DEFAULT_PATH = get_default_value()

    values = {
        app.path: app.verbose_name
        for app in get_apps_configs()
        if str(settings.BEHAVE_TEST_RECORDER__MODULE_DIR_PATH) in app.path
    }
    values.update({
        DEFAULT_PATH: 'Не указано',
    })

    @classmethod
    def get_choices(cls):
        items = list(cls.values.items())
        items.sort(key=lambda i: i[1])

        return items


class RecordingTestStateEnum(Enum):
    """
    Перечисление состояний записи теста
    """

    NONE = 'Не начата'
    STARTED = 'Начата'
    ENDED = 'Завершена'
    ENDED_WO_SAVE = 'Завершена без сохранения'
    ERROR = 'Ошибка'

    @classmethod
    def get_roadmap(
        cls,
    ) -> Dict['RecordingTestStateEnum', Tuple['RecordingTestStateEnum']]:
        """
        Возвращает карту переходов состояний записи теста
        """
        return {
            cls.NONE: (
                cls.STARTED,
            ),
            cls.STARTED: (
                cls.STARTED,
                cls.ENDED,
                cls.ENDED_WO_SAVE,
            ),
        }

    @classmethod
    def get_state_roadmap(
        cls,
        state: 'RecordingTestStateEnum',
    ) -> Tuple['RecordingTestStateEnum']:
        """
        Возвращает дальнейшие состояния записи после текущего
        """
        state_roadmap = cls.get_roadmap()

        return state_roadmap[state]

    @classmethod
    def get_state_label(
        cls,
        state: 'RecordingTestStateEnum',
    ) -> str:
        """
        Возвращает подпись для кнопки перехода в состояние
        """
        return {
            cls.STARTED: 'Начать запись следующего шага',
            cls.ENDED: 'Завершить запись и сохранить',
            cls.ENDED_WO_SAVE: 'Завершить без сохранения',
        }[state]


class UsingLibraryEnum:
    DATETIME = 'datetime'
    DECIMAL = 'Decimal'
    JSON = 'json.'

    values = {
        DATETIME: 'import datetime',
        DECIMAL: 'from decimal import Decimal',
        JSON: 'import json',
    }


class ResponseTypeEnum:
    JSON = 'json'
    FILE_DOWNLOAD = 'file_download'
