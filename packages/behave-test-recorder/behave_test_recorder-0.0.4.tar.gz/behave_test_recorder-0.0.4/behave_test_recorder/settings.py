from pathlib import (
    Path,
)

from django.template import (
    Template,
)
from django.test.utils import (
    instrumented_test_render,
)


def patch_template_renderer():
    """Патчит метод рендеринга шаблона отправкой сигнала.

    В сигнале передаётся контекст рендеригна, нужный для сохранения результата запроса при записи.
    """
    Template._render = instrumented_test_render


def init(conf):
    MIDDLEWARE = ()

    PROJECT_ROOT_URL = ''
    PROJECT_DOWNLOADS_URL = ''
    PROJECT_DOWNLOADS_DIR = ''
    EXCLUDED_URLS = []
    PROJECT_ROOT_DIR_PATH = None
    RECORDING_EXPIRE = None
    MODULE_DIR_PATH = None
    EXCLUDED_PARAMS = []
    STORED_GENERATED_FILES_PATH = None
    COMMIT_GENERATED_FILES = False
    TASK_ID_FIELD_TEMPLATE = None
    RECORDER_CLASS = None

    ENABLE = conf.get_bool(
        'behave_test_recorder',
        'ENABLE',
    )
    if ENABLE:
        patch_template_renderer()

        BEHAVE_TEST_RECORDER_MIDDLEWARE = conf.get(
            'behave_test_recorder',
            'MIDDLEWARE',
        )

        PROJECT_ROOT_URL = conf.get(
            'behave_test_recorder',
            'PROJECT_ROOT_URL'
        )

        PROJECT_DOWNLOADS_URL = conf.get(
            'behave_test_recorder',
            'PROJECT_DOWNLOADS_URL'
        )

        PROJECT_DOWNLOADS_DIR = conf.get(
            'behave_test_recorder',
            'PROJECT_DOWNLOADS_DIR'
        )

        if BEHAVE_TEST_RECORDER_MIDDLEWARE:
            MIDDLEWARE = (
                BEHAVE_TEST_RECORDER_MIDDLEWARE,
            )

        excluded_urls = conf.get(
            'behave_test_recorder',
            'EXCLUDED_URLS',
        )
        if excluded_urls:
            EXCLUDED_URLS = [s.strip() for s in excluded_urls.split(',')]

        PROJECT_ROOT_DIR_PATH = conf.get(
            'behave_test_recorder',
            'PROJECT_ROOT_DIR_PATH'
        )

        MODULE_DIR_PATH = conf.get(
            'behave_test_recorder',
            'MODULE_DIR_PATH'
        )

        RECORDING_EXPIRE = conf.get_int(
            'behave_test_recorder',
            'RECORDING_EXPIRE',
        ) or 3600

        if not all((
            PROJECT_ROOT_DIR_PATH,
            RECORDING_EXPIRE,
        )):
            raise Exception(
                'Для работы модуля behave_test_recorder требуется '
                'указать значения параметров PROJECT_ROOT_DIR_PATH и '
                'RECORDING_EXPIRE в секции [behave_test_recorder] project.conf'
            )

        PROJECT_ROOT_DIR_PATH = Path(
            PROJECT_ROOT_DIR_PATH
        )

        if MODULE_DIR_PATH:
            MODULE_DIR_PATH = Path(MODULE_DIR_PATH)
        else:
            MODULE_DIR_PATH = PROJECT_ROOT_DIR_PATH

        excluded_params = conf.get(
            'behave_test_recorder',
            'EXCLUDED_PARAMS',
        )
        if excluded_params:
            EXCLUDED_PARAMS = [
                s.strip()
                for s in excluded_params.split(',')
            ]

        # Относительный путь к директории, в которую будет осуществляться
        # сохранение артефактов создаваемых в процессе записи теста
        STORED_GENERATED_FILES_PATH = conf.get(
            'behave_test_recorder',
            'STORED_GENERATED_FILES_PATH',
        ) or 'behave_test_recorder_storage'

        COMMIT_GENERATED_FILES = conf.get_bool(
            'behave_test_recorder',
            'COMMIT_GENERATED_FILES',
        )

        # Шаблон поля номера задачи JIRA
        TASK_ID_FIELD_TEMPLATE = conf.get(
            'behave_test_recorder',
            'TASK_ID_FIELD_TEMPLATE',
        ) or '^(BOZIK|BOBUH|BOAIP)-\d{1,5}$'

        RECORDER_CLASS = conf.get(
            'behave_test_recorder',
            'RECORDER_CLASS',
        ) or 'behave_test_recorder.recorders.BehaveTestRecorder'

    return {
        'MIDDLEWARE': MIDDLEWARE,

        'ENABLE': ENABLE,
        'PROJECT_ROOT_URL': PROJECT_ROOT_URL,
        'PROJECT_DOWNLOADS_URL': PROJECT_DOWNLOADS_URL,
        'PROJECT_DOWNLOADS_DIR': PROJECT_DOWNLOADS_DIR,
        'EXCLUDED_URLS': EXCLUDED_URLS,  # noqa
        'PROJECT_ROOT_DIR_PATH': PROJECT_ROOT_DIR_PATH,  # noqa
        'RECORDING_EXPIRE': RECORDING_EXPIRE,  # noqa
        'MODULE_DIR_PATH': MODULE_DIR_PATH,
        'EXCLUDED_PARAMS': EXCLUDED_PARAMS,
        'STORED_GENERATED_FILES_PATH': STORED_GENERATED_FILES_PATH,
        'COMMIT_GENERATED_FILES': COMMIT_GENERATED_FILES,
        'TASK_ID_FIELD_TEMPLATE': TASK_ID_FIELD_TEMPLATE,
        'RECORDER_CLASS': RECORDER_CLASS,
    }
