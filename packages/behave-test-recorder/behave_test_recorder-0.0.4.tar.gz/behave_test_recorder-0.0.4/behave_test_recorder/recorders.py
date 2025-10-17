import json
import os
import pathlib
import uuid
from collections import (
    namedtuple,
)
from functools import (
    cached_property,
    wraps,
)
from pathlib import (
    Path,
)
from time import (
    sleep,
    time,
)
from typing import (
    Optional,
)

from django.conf import (
    settings,
)
from git import (
    Repo,
)

from behave_test_recorder.consts import (
    RECORDING_TASK_SESSION_KEY,
    STEPS_EXECUTED_BEFORE_RECORDING_FILE_NAME,
)
from behave_test_recorder.enums import (
    DjangoAppsPathsEnum,
    RecordingTestStateEnum,
    ResponseTypeEnum,
)
from behave_test_recorder.exceptions import (
    AppNotAvailableException,
    BehaveTestRecorderException,
)
from behave_test_recorder.exporters import (
    FeatureExporter,
    PyRequestExporter,
    StepChecksExporter,
    StepRequestExporter,
)
from behave_test_recorder.helpers import (
    get_behave_test_recorder_instance,
)
from behave_test_recorder.receivers import (
    response_context_storage,
)
from behave_test_recorder.strings import (
    RECORDING_IS_EXPIRED_ERROR,
    STEP_DEFINITION_WRONG_DIVIDER_COUNT,
    STEP_DEFINITION_WRONG_TABLE_FORMAT,
    STEP_DEFINITION_WRONG_TABLE_ROWS_COUNT,
    TEST_RECORDING_ALREADY_FINISHED_ERROR,
    TEST_RECORDING_EMPTY_STEP_ERROR,
    TEST_RECORDING_ERROR_ENDED,
    TEST_RECORDING_NO_RECORDER_REQUESTS,
)
from behave_test_recorder.utils import (
    template_rendered_connect,
    template_rendered_disconnect,
)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance

        return cls._instances[cls]


class StepDefinition:
    """
    Класс для проверки и преобразования сырого описания шага
    в подходящее для экспорта
    """

    BEHAVE_STEP_KEYWORDS = (
        'Дано',
        'Когда',
        'То',
        'И',
        'Но',
    )

    def __init__(self, raw_step_definition, has_passed_steps=False) -> None:
        """
        Args:
            raw_step_definition: сырое описание шага сценария
            has_passed_steps: флаг наличия прошедших шагов
        """
        self._raw_step_definition = raw_step_definition.strip()
        self._has_passed_steps = has_passed_steps
        self._raw_step = None
        self._raw_table = None

        self.keyword = None
        self.name = None
        self.table = None
        self._postfix = None
        self._number = None

        self.split_step_data()

        self.prepare_step()
        self.prepare_step_table()

        super().__init__()

    def __str__(self) -> str:
        return (
            f'{self.keyword} {self.name}\n{self.table}'
            if self.table else
            f'{self.keyword} {self.name}'
        )

    def split_step_data(self):
        """
        Разделение сырого описания шага на шаг и табличные данные
        """
        self._raw_step, *self._raw_table = self._raw_step_definition.split('\n')

    def prepare_step(self):
        """
        Проверить ключевые слова в шаге отправленном пользователем,
        и преобразовать ключевое слово шага к формату feature-файла
        """
        step = ' '.join(self._raw_step.split())

        if step.endswith(':'):
            step = step[:-1]

        for keyword in self.BEHAVE_STEP_KEYWORDS:
            if step.startswith(f'{keyword} '):
                break
            elif step.lower().startswith(f'{keyword} '.lower()):
                step = f'{keyword} {step[len(keyword)+1:]}'
                break
        else:
            if self._has_passed_steps:
                keyword = 'И'
            else:
                keyword = 'Дано'

            step = f'{keyword} {step}'

        self.keyword = keyword
        self.name = step.replace(f'{keyword} ', '', 1)

    @staticmethod
    def validate_table_row(row, max_dividers_count):
        """Проверка строки таблицы на соответствие формату

        Args:
            row: строка таблицы
            max_dividers_count: максимальное количество разделителей по строкам
                в таблице
        """
        error = None
        row_dividers_count = row.count('|')

        if not (
            row.startswith('|') and
            row.endswith('|')
        ):
            error = BehaveTestRecorderException(
                STEP_DEFINITION_WRONG_TABLE_FORMAT
            )
        elif (
            row_dividers_count < 2 or
            row_dividers_count != max_dividers_count
        ):
            error = STEP_DEFINITION_WRONG_DIVIDER_COUNT

        return error

    def prepare_step_table(self):
        """
        Проверка и подготовка табличных данных описания шага
        """
        step_table = [tr.strip() for tr in self._raw_table if tr.strip()]

        if len(step_table) == 1:
            raise BehaveTestRecorderException(
                STEP_DEFINITION_WRONG_TABLE_ROWS_COUNT.format(
                    '\n'.join(step_table)
                )
            )

        elif step_table:

            max_dividers_count = max(tr.count('|') for tr in step_table)

            step_table_info = [
                {
                    'div_count': tr.count('|'),
                    'text': tr,
                    'error': self.validate_table_row(tr, max_dividers_count)
                }
                for tr in step_table
            ]

            rows_errors = ''.join(
                f'<br/><br/>Не корректная строка: {tr["text"]}<br/>{tr["error"]}'
                for tr in step_table_info
                if tr['error']
            )

            if rows_errors:
                raise BehaveTestRecorderException(
                    f'Не корректный формат таблицы параметров: {rows_errors}'
                )

            self.table = '\n'.join(step_table)
        else:
            self.table = None

    @property
    def to_feature(self) -> str:
        """
        Описание шага при вставке в feature файл
        """
        return (
            f'{self.keyword} {self.name}{self.postfix}\n{self.table}'
            if self.table else
            f'{self.keyword} {self.name}{self.postfix}'
        )

    @property
    def postfix(self) -> str:
        """
        Постфикс шага
        """
        return (
            f' [{self._number}]{self._postfix}'
            if self._number else
            self._postfix
        )

    @postfix.setter
    def postfix(self, value: str):
        """
        Устанавливает постфикс. Убирает из имени шага постфикс, если он там уже есть.
        """
        self._postfix = f' ({value})'

        if self.name.endswith(self._postfix):
            self.name = self.name[0:-len(self._postfix)]


class PassedStepsList(list):
    """Хранилище пройденных шагов записи."""

    def __contains__(self, step: StepDefinition):
        """Переопределен для сравнения шагов по атрибуту name."""

        return step.name in map(lambda s: s.name, self)

    def count_by_name(self, step: StepDefinition) -> int:
        """Возвращает количество шагов с одинаковым наименованием шага."""

        return [s.name for s in self].count(step.name)


class BehaveTestRecorder(metaclass=SingletonMeta):
    """
    Устройство для осуществления записи теста

    Запускается при начале записи теста. Хранит
    время запуска, номер задачи и директорию, в которую будут складироваться
    результирующие файлы. Если запись производится дольше отведенного времени,
    то работа прекращается
    """

    RequestData = namedtuple("RequestData", [
        'request',
        'file_path',
        'unique_mixin',
        'path_postfix',
    ])
    ResponseData = namedtuple("ResponseData", [
        'type',
        'content',
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._state = RecordingTestStateEnum.NONE
        self._passed_steps = PassedStepsList()

        self._task_id: Optional[str] = None

        self._testlink_id: Optional[str] = None
        self.testlink_sync = False
        self.testlink_need_update = False
        self.testlink_testcase = None
        self.testlink_steps = []

        self.steps_for_recording = []
        self._scenario_name: Optional[str] = None
        self._current_step: Optional[StepDefinition] = None
        self._storage_dir_path: Optional[Path] = None
        self._steps_file_path: Optional[Path] = None
        self._checks_file_path: Optional[Path] = None
        self.steps_checks_module_name: Optional[str] = None
        self.storage_module_path: Optional[str] = None
        self.feature_name: Optional[str] = None
        self._timestamp: Optional[int] = None
        self._processed_requests = set()
        self._requests_data = []
        self._response_data = {}
        self.steps_executed_before_recording = []
        self.need_to_commit_files = settings.BEHAVE_TEST_RECORDER__COMMIT_GENERATED_FILES

        self._check_steps_executed_before_recording()

    @property
    def project_root_url(self):
        """Корневой url проекта."""

        return settings.BEHAVE_TEST_RECORDER__PROJECT_ROOT_URL

    @property
    def project_downloads_url(self):
        """Адрес url проекта для загрузки файлов."""

        return settings.BEHAVE_TEST_RECORDER__PROJECT_DOWNLOADS_URL

    @property
    def project_downloads_dir(self):
        """Путь в файловой системе проекта к директории файлов для загрузки."""

        return settings.BEHAVE_TEST_RECORDER__PROJECT_DOWNLOADS_DIR

    @cached_property
    def excluded_urls_for_recording(self):
        """Список исключаемых из записи url."""

        return [
            f'{self.project_root_url}{url_path}'
            for url_path in settings.BEHAVE_TEST_RECORDER__EXCLUDED_URLS
        ]

    def _check_steps_executed_before_recording(self):
        """Проверяет есть ли файл с выполненными шагами. Если да - загружает в steps_executed_before_recording.

        """
        path = Path(DjangoAppsPathsEnum.DEFAULT_PATH, STEPS_EXECUTED_BEFORE_RECORDING_FILE_NAME)
        if path.exists():
            with open(path) as file:
                self.steps_executed_before_recording = json.loads(file.read())

    @property
    def is_not_started(self) -> bool:
        """
        Запись еще не начата
        """
        return self._state == RecordingTestStateEnum.NONE

    @property
    def is_started(self) -> bool:
        """
        Запись начата
        """
        return (
            self._state != RecordingTestStateEnum.NONE and
            not (self.is_ended or self.is_error_ended)
        )

    @property
    def is_ended(self) -> bool:
        """
        Запись окончена. Повторную запись можно производить только после
        перезапуска приложения с новой БД
        """
        return self._state == RecordingTestStateEnum.ENDED or self.is_ended_wo_save

    @property
    def is_ended_wo_save(self) -> bool:
        """
        Запись завершена без сохранения записанных данных.
        """
        return self._state == RecordingTestStateEnum.ENDED_WO_SAVE

    @property
    def is_error_ended(self) -> bool:
        """
        Запись завершена из-за ошибки.
        """
        return self._state == RecordingTestStateEnum.ERROR

    @property
    def current_step(self) -> str:
        """
        Текущий шаг записи теста
        """
        return str(self._current_step)

    @current_step.setter
    def current_step(self, step: StepDefinition):
        """
        Устанавливает текущий шаг, задает постфикс
        """
        step.postfix = self.lower_testlink_id
        self._current_step = step

    @property
    def current_step_wo_keyword(self) -> str:
        """
        Текущий шаг записи теста без использования ключевого слова в начале
        """
        return f'{self._current_step.name}{self._current_step.postfix}'

    @property
    def current_state(self) -> RecordingTestStateEnum:
        """
        Состояние записи теста
        """
        return self._state

    @property
    def is_expired(self) -> bool:
        """
        Является ли запись просроченной или нет
        """
        now = int(time())

        return (now - self._timestamp) > settings.BEHAVE_TEST_RECORDER__RECORDING_EXPIRE  # noqa

    @property
    def passed_steps(self) -> PassedStepsList[StepDefinition]:
        """
        Список пройденных шагов теста
        """
        return self._passed_steps

    @property
    def passed_steps_str(self):
        return [str(step) for step in self._passed_steps]

    @property
    def _is_check_step(self) -> bool:
        """
        Является ли текущий шаг шагом проверки.
        (То, или То ... И ...)
        """
        is_check_step = False

        if self.current_step.startswith('То'):
            is_check_step = True
        elif self.current_step.startswith('И'):
            # Проверим предыдущие шаги, если в серии предыдущих шагов
            # первым встречается шаг начинающийся на То,
            # значит текущий шаг - тоже проверочный
            for step in self.passed_steps[::-1]:
                step = str(step)
                if step.startswith('Когда') or step.startswith('Дано'):
                    break
                elif step.startswith('То'):
                    is_check_step = True
                    break

        return is_check_step

    @property
    def task_id(self) -> str:
        """
        Номер задачи в Jira
        """
        return self._task_id

    @property
    def lower_task_id(self) -> str:
        """
        Номер задачи в нижнем регистре с заменой дефиса на нижнее подчеркивание

        BOBUH-1 -> bobuh_1
        """
        return self._task_id.lower().replace('-', '_')

    @property
    def lower_testlink_id(self) -> str:
        """
        Номер сценария из testlink в нижнем регистре
        с заменой нижнего подчеркивания на дефис.
        """
        return self._testlink_id.lower().replace('_', '-')

    @property
    def underscore_testlink_id(self) -> str:
        """
        Номер сценария из testlink в нижнем регистре
        с заменой символа дефиса на нижнее подчеркивание.
        """
        return self.lower_testlink_id.replace('-', '_')

    @property
    def scenario_name(self) -> str:
        """
        Возвращает наименование сценария
        """
        return self._scenario_name

    @property
    def storage_dir_path(self) -> Optional[Path]:
        """
        Путь до директории хранилища артефактов записи теста
        """
        return self._storage_dir_path

    @property
    def requests_data(self) -> list:
        """
        Данные запросов текущего шага записи теста.
        Содержат объект запроса, путь к файлу Python-фикстур, hash-постфикс запроса.
        """
        return self._requests_data

    @property
    def response_data(self) -> dict:
        """
        Необработанные данные результатов запросов текущего шага.
        """
        return self._response_data

    def clean_pycache(self):
        """Удалить .pyc-файлы и __pycache__ в хранилище записанных файлов.

        Чтобы .pyc не попали в коммит.
        """
        for p in pathlib.Path(self._storage_dir_path).rglob('*.py[co]'):
            p.unlink()
        for p in pathlib.Path(self._storage_dir_path).rglob('__pycache__'):
            p.rmdir()

    def _commit_changes(self):
        """
        Коммитит и пушит изменения в отдельную созданную ветку,
        соответствующую номеру задачи, репозитория проекта, для которого
        производилась запись теста.
        После всех действий возвращает репозиторий на изначальную ветку.
        """
        repo = Repo(
            path=settings.BEHAVE_TEST_RECORDER__PROJECT_ROOT_DIR_PATH,
        )

        init_branch = repo.active_branch

        unique_mixin = uuid.uuid4().hex[:6]
        new_branch_name = f'behave_test_recorder/{self._task_id}-{unique_mixin}'

        new_branch = repo.create_head(
            path=new_branch_name,
        )
        new_branch.checkout(
            force=True,
        )

        if new_branch != repo.active_branch:
            raise BehaveTestRecorderException(
                'Не удалось переключиться на созданную ветку'
            )

        self.clean_pycache()

        repo.index.add(
            items=str(self._storage_dir_path),
        )
        repo.index.commit(
            message=(
                f'{self._task_id}. Автоматический коммит записи '
                f'автотеста сценария "{self._scenario_name}".'
            ),
        )
        origin = repo.remote()
        repo.git.push('--set-upstream', origin, repo.head.ref)

        # переключимся обратно на изначальную ветку
        init_branch.checkout()

    def cleanup(self):
        """Удаляет все записанные данные.

        Срабатывает только если включена настройка коммита изменений в репозиторий.
        Сначала удаляет неотслеживаемые файлы. Затем отменяет изменения в отслеживаемых.
        """
        if self.need_to_commit_files:
            repo = Repo(
                path=settings.BEHAVE_TEST_RECORDER__PROJECT_ROOT_DIR_PATH,
            )
            if repo.is_dirty(untracked_files=True):
                for untracked_file_rel_path in repo.untracked_files:
                    os.remove(settings.BEHAVE_TEST_RECORDER__PROJECT_ROOT_DIR_PATH / Path(untracked_file_rel_path))

            if repo.is_dirty():
                repo.head.reset(working_tree=True)

    def check_start_db_state(self):
        pass

    def start(
        self,
        task_id: str,
        module_path: str,
        scenario_name: str,
        scenario_step: str,
        testlink_id=None,
    ):
        """
        Запуск записи теста
        """
        self.check_start_db_state()

        # Перед стартом убираем существующие изменения из репозитория.
        self.cleanup()

        scenario_step = StepDefinition(scenario_step)

        self._state = RecordingTestStateEnum.STARTED
        self._task_id = task_id.replace(' ', '_')

        if testlink_id:
            self._testlink_id = testlink_id.replace(' ', '-')
        else:
            self._testlink_id = f'untagged_{uuid.uuid4().hex[:6]}'

        self._scenario_name = scenario_name
        self.current_step = scenario_step
        self._timestamp = int(time())

        self.feature_name = f'{DjangoAppsPathsEnum.values[module_path]}'
        self.storage_module_path = module_path.replace(
            os.path.abspath(settings.BEHAVE_TEST_RECORDER__PROJECT_ROOT_DIR_PATH) + '/',
            ''
        ).replace('/', '.')

        self._storage_dir_path = Path(module_path) / 'features'

        self.steps_checks_module_name = f'checks_{self.underscore_testlink_id}'

        steps_dir_path = self._storage_dir_path / 'steps'
        self._steps_file_path = steps_dir_path / f'steps_{self.underscore_testlink_id}.py'
        self._checks_file_path = steps_dir_path / f'{self.steps_checks_module_name}.py'

        os.makedirs(
            name=steps_dir_path,
            exist_ok=True,
        )

        steps_init_py_path = steps_dir_path / '__init__.py'
        features_init_py_path = self._storage_dir_path / '__init__.py'

        for path in (features_init_py_path, steps_init_py_path, self._steps_file_path):
            open(path, 'a').close()

    def wait_for_requests_ended(self):
        """Ожидание завершения запросов текущего шага.

        Перед переключением шага требуется дождаться когда запросы текущего шага завершатся.
        """
        countdown = 120

        while True:
            if countdown == 0:
                raise BehaveTestRecorderException(
                    'Превышено время ожидания завершения запроса!'
                )

            if self._processed_requests:
                sleep(1)
                countdown -= 1
            else:
                break

    def next_step(
        self,
        state: RecordingTestStateEnum,
        next_scenario_step: str,
        current_scenario_step: str,
    ):
        """Переход к следующему шагу записи теста

        Args:
            state: статус в который переводим рекордер
            next_scenario_step: Описание следующего шага
            current_scenario_step: Описание текущего записываемого шага
        """
        self.wait_for_requests_ended()

        if state != RecordingTestStateEnum.ENDED_WO_SAVE and not self.requests_data:
            raise BehaveTestRecorderException(TEST_RECORDING_NO_RECORDER_REQUESTS)

        if self.steps_for_recording:
            self.steps_for_recording.pop(0)

        current_scenario_step = current_scenario_step.strip()

        if (
            current_scenario_step
            and current_scenario_step != str(self._current_step)
        ):
            # Если есть изменения в описании текущего шага - учитываем их
            self.current_step = StepDefinition(
                raw_step_definition=current_scenario_step,
                has_passed_steps=len(self.passed_steps) > 0,
            )

        if self._current_step in self.passed_steps:
            self._current_step._number = self.passed_steps.count_by_name(self._current_step) + 1

        self._state = state

        next_scenario_step_definition = None

        if self.is_started:
            if next_scenario_step:
                next_scenario_step_definition = StepDefinition(
                    raw_step_definition=next_scenario_step,
                    has_passed_steps=True,
                )
            else:
                raise BehaveTestRecorderException(TEST_RECORDING_EMPTY_STEP_ERROR)

        check_function_name = None

        if (
            self._is_check_step
            and self._requests_data
        ):
            step_checks_exporter = self._get_step_checks_exporter()

            step_checks_exporter.to_file(
                file_path=str(self._checks_file_path)
            )
            check_function_name = step_checks_exporter.check_function_name

        step_request_exporter = StepRequestExporter(
            recorder=self,
            check_function_name=check_function_name,
        )
        step_request_exporter.to_file(
            file_path=str(self._steps_file_path)
        )

        self._passed_steps.append(self._current_step)

        if self.is_ended:
            self.end()
        else:
            self.current_step = next_scenario_step_definition

        self._requests_data.clear()
        self._response_data.clear()

    def end(self):
        """Завершает процесс записи, если выбрано, сохраняет результаты записи и отправляет в репозиторий.

        Либо удаляет записанные данные если указан соответствующий статус рекордера."""
        if self.is_ended_wo_save:
            self.cleanup()
        else:
            feature_exporter = FeatureExporter(
                recorder=self,
            )
            feature_exporter.to_file()

            if self.testlink_sync:
                self.testlink_need_update = self.passed_steps_str != self.testlink_steps

            if self.need_to_commit_files:
                self._commit_changes()

        self._set_recorder_end_state(RecordingTestStateEnum.ENDED)

    def _set_recorder_end_state(self, state):
        """Переводит рекордер в завершающий статус и сбрасывает параметры.

        Args:
            state: Статус рекордера
        """
        self._state = state
        self._task_id = None
        self._timestamp = None
        self._storage_dir_path = None

    def error_end(self):
        """Завершает процесс записи при возникновении ошибки."""
        self.cleanup()
        self._set_recorder_end_state(RecordingTestStateEnum.ERROR)

    def _get_request_exporter(self, request, context_declaration_map, unique_mixin, path_postfix, comment=None):
        py_request_exporter = PyRequestExporter(
            request=request,
            module_path=self._storage_dir_path,
            context_declaration_map=context_declaration_map,
            request_unique_mixin=unique_mixin,
            request_path_ending=path_postfix,
            comment=comment,
        )
        return py_request_exporter

    def _get_step_checks_exporter(self):
        step_checks_exporter = StepChecksExporter(
            recorder=self,
            module_path=self._storage_dir_path,
        )

        return step_checks_exporter

    def _get_context_declaration_map(self, path):
        return {}

    def _write_request(
        self,
        request,
    ):
        """Запись данных запроса.

        Формирование файла-фикстуры для отправки запроса.

        Args:
            request: Объект Django-запроса.
        """
        context_declaration_map = self._get_context_declaration_map(request.path)
        unique_mixin = uuid.uuid4().hex[:6]
        path_postfix = request.path.replace('-', '_').split('/')[-1]

        py_request_exporter = self._get_request_exporter(
            request,
            context_declaration_map,
            unique_mixin,
            path_postfix,
        )

        requests_dir = self._storage_dir_path / f'{self.underscore_testlink_id}_requests'

        os.makedirs(
            name=requests_dir,
            exist_ok=True,
        )

        init_py_path = str(requests_dir / '__init__.py')

        open(init_py_path, 'a').close()

        file_name = (
            f'request_'
            f'{len(self.passed_steps)}_'
            f'{len(self.requests_data)}_'
            f'{unique_mixin}_'
            f'{path_postfix}.py'
        )
        request_file_path = requests_dir / file_name

        py_request_exporter.to_file(
            file_path=str(request_file_path),
            request_unique_mixin=unique_mixin,
        )

        self._requests_data.append(
            self.RequestData(
                request=request,
                file_path=request_file_path,
                unique_mixin=unique_mixin,
                path_postfix=path_postfix,
            )
        )

    def appropriate_request(self, request):
        """
        Дополнительное условие для проверки, что запрос подходит
        """
        return True

    def check_request(self, request) -> bool:
        """
        Проверка возможности записи запроса.
        """
        if (
            self.is_started and
            RECORDING_TASK_SESSION_KEY not in request.session
        ):
            raise AppNotAvailableException(
                'Запись теста уже выполняется. Доступ к приложению заблокирован.'
            )

        is_request_appropriate = (
            self.is_started and
            RECORDING_TASK_SESSION_KEY in request.session and
            self.appropriate_request(request) and
            not (
                request.path in self.excluded_urls_for_recording or
                request.path.startswith(self.project_downloads_url)
            )
        )

        return is_request_appropriate

    def write_request(
        self,
        request,
    ):
        """Запись данных запроса.

        Args:
            request: Объект Django-запроса.
        """
        if self.check_request(request):
            self._processed_requests.add(id(request))

            try:
                self._write_request(
                    request=request,
                )
            except Exception as e:
                self.error_end()
                raise e

            if self._is_check_step:
                # Если это шаг проверки - включаем запись контекста рендера
                template_rendered_connect(request)

    def save_response_data(
        self,
        request,
        response,
    ):
        """Сохранение результата запроса для последующего использования проверок в шагах.

        В случае ответа сгенерированного с помощью рендеринга шаблона (не json), если доступен контекст, сохраняем его.

        Args:
            request: Объект Django-запроса.
            response: Объект Django-ответа на запрос.
        """
        request_id = id(request)

        if request_id in self._processed_requests:
            self._processed_requests.remove(request_id)

        if (
            self.check_request(request) and
            self._is_check_step
        ):
            template_rendered_disconnect(request)
            context = response_context_storage.pop(request_id, None)

            self._response_data[request_id] = self.define_response_data(response, context)

    def define_response_data(self, response, context):
        """Возвращает данные ответа.

        Args:
            response: объект HttpResponse;
            context: Django context.

        Returns:
            Объект self.ResponseData соответствующего типа.
        """
        response_data = self.define_file_download_response_data(response)

        if not response_data:
            response_data = self.define_json_response_data(response)

        return response_data

    def define_file_download_response_data(self, response):
        """Возвращает данные если ответ содержит путь для скачивания файла.

        Args:
            response: объект HttpResponse.

        Returns:
            Объект self.ResponseData.
        """
        if self.project_downloads_url in response.content.decode('utf-8'):
            response_data = self.ResponseData(
                type=ResponseTypeEnum.FILE_DOWNLOAD,
                content=response.content,
            )
        else:
            response_data = None

        return response_data

    def define_json_response_data(self, response):
        """Возвращает данные если это json.

        Args:
            response: объект HttpResponse.

        Returns:
            Объект self.ResponseData.
        """
        try:
            json.loads(response.content)
        except ValueError:
            response_data = None
        else:
            response_data = self.ResponseData(
                type=ResponseTypeEnum.JSON,
                content=response.content
            )

        return response_data


def check_recorder_status(exception_class=BehaveTestRecorderException):
    """Декоратор проверяет статус рекордера.

    В случае если время отведённое на запись истекло, либо произошло другое непредвиденное исключение
    - очистим все записанные данные.

    Args:
        exception_class: класс исключения используемый для вызова

    Raises:
        Если запись уже завершена.
        Если запись начата, но время отведённое на выполнение записи истекло.
        Если запись завершена из-за ошибки.
    """
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            recorder = get_behave_test_recorder_instance()

            if recorder.is_ended:
                raise exception_class(TEST_RECORDING_ALREADY_FINISHED_ERROR)
            elif recorder.is_error_ended:
                raise exception_class(TEST_RECORDING_ERROR_ENDED)

            if recorder.is_started and recorder.is_expired:
                recorder.cleanup()
                raise exception_class(RECORDING_IS_EXPIRED_ERROR)
            else:
                try:
                    result = func(
                        *args,
                        recorder=recorder,
                        **kwargs,
                    )
                except BehaveTestRecorderException as e:
                    raise exception_class(e.exception_message)
                except Exception as e:
                    recorder.error_end()
                    raise e

                return result

        return wrapper

    return decorator
