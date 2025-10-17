import json
import os
import shutil
import uuid
from pathlib import (
    Path,
)
from pprint import (
    pformat,
)
from typing import (
    List,
    Optional,
)

from django.conf import (
    settings,
)
from django.http.request import (
    QueryDict,
)
from isort.api import (
    sort_code_string,
)

from behave_test_recorder.base_exporters import (
    BaseExporter,
    BasePyExporter,
    ExistedFileBaseExporter,
)
from behave_test_recorder.consts import (
    FILES_DIR,
    TAB_STR,
)
from behave_test_recorder.enums import (
    ResponseTypeEnum,
)
from behave_test_recorder.helpers import (
    get_behave_test_recorder_instance,
)


class PyRequestExporter(BasePyExporter):
    """
    Экспортер запроса в виде объекта класса AppRequest.
    """

    def __init__(
        self,
        *args,
        request,
        module_path: Path,
        context_declaration_map: dict,
        request_unique_mixin: str,
        request_path_ending: str,
        comment: str = None,
        **kwargs,
    ):
        """
        Args:
            request: Объект django-запроса.
            module_path: путь до директории с записанными тестами
            context_declaration_map: Словарь соответствия ACD-параметров.
            request_unique_mixin: Строка уникальный идентификатор запроса.
            request_path_ending: Строка последней части url-адреса запроса.
        """
        super().__init__(*args, **kwargs)

        self._request = request
        self._module_path = module_path
        self._context_declaration_map = context_declaration_map
        self._request_unique_mixin = request_unique_mixin
        self._request_path_ending = request_path_ending
        self._is_os_used = False
        self._comment = comment
        self._recorder = get_behave_test_recorder_instance()

    def _prepare_imports(
        self,
        content: str,
    ) -> List[str]:
        """
        Подготовка импортов для вывода в фикстуре
        """
        parent_imports = super()._prepare_imports(content)

        if self._is_os_used:
            parent_imports.append('import os')

        imports = [
            *parent_imports,
        ]

        return imports

    def _get_pure_request_path(self):
        """
        Возвращает чистый url без корневого url приложения,
        если корневой url используется.
        """
        if (
            self._recorder.project_root_url and
            self._request.path.startswith(self._recorder.project_root_url)
        ):
            path = self._request.path.replace(self._recorder.project_root_url, '', 1)
        else:
            path = self._request.path

        return path

    def _prepare_parameters(self) -> dict:
        """Подготавливает и возвращает преобразованные параметры для запроса."""
        parameters = QueryDict("", mutable=True)
        parameters_of_request = getattr(self._request, self._request.method, None)

        if parameters_of_request is not None:
            parameters.update(parameters_of_request)

        if self._request.FILES:
            self._is_os_used = True
            files_path = self._module_path / FILES_DIR

            if not files_path.exists():
                os.mkdir(files_path)

            for key, value in self._request.FILES.items():
                for file_el in self._request.FILES.getlist(key):
                    save_file_path = shutil.copyfile(
                        value.temporary_file_path(),
                        os.path.join(
                            files_path, f'{self._request_unique_mixin}_{file_el.name}'
                        )
                    )

                    parameters.update(
                        {
                            key: f"open(os.path.join(os.path.dirname(__file__), os.pardir, '{FILES_DIR}', '{os.path.basename(save_file_path)}'), 'rb')"
                        }
                    )

            for key, value in parameters.items():
                if len(parameters.getlist(key)) > 1:
                    temp_el_list = []
                    for file_el in parameters.getlist(key):
                        temp_el_list.append(file_el)
                    pre_content = f'[\n{TAB_STR * 4}'
                    post_content = f'{TAB_STR * 3}]'
                    list_params = f',\n{TAB_STR * 4}'.join(temp_el_list)
                    parameters.update(
                        {
                         key: f'{pre_content}{list_params},\n{post_content}'.replace('"', '')
                        }
                    )


        return parameters

    def _add_parameter(self, name, param_type, value, pre_content, is_json_value) -> None:
        """
        Добавление наименования и значения параметра в pre_content

        Args:
            name: Наименование параметра
            param_type: Тип параметра
            value: Значение параметра
            pre_content: Список итоговых строк
            is_json_value: Является ли значение параметра json-строкой
        """

        if value.startswith('open') or value.startswith('[\n'):
            pre_content.append(f'{TAB_STR * 3}\'{name}\': {value},')
        elif is_json_value:
            pre_content.append(f'{TAB_STR * 3}\'{name}\': {repr(value)},')
        else:
            pre_content.append(f'{TAB_STR * 3}\'{name}\': \'{value}\',')

    def _get_function_declaration(self) -> str:
        """
        Возвращает строку объявления функции загрузки
        """
        return 'def request_loader(context):'

    def _get_function_comment(self) -> str:
        """
        Возвращает комментарий для функции загрузки
        """
        return f'{TAB_STR}"""\n{TAB_STR}{self._comment}\n{TAB_STR}"""' if self._comment else ''

    def _get_app_request(self) -> str:
        """Возвращает исходный код запроса."""
        pre_content = [
            f'{TAB_STR}response = context.AppRequest(',
            f'{TAB_STR * 2}path=\'{self._get_pure_request_path()}\',',
            f'{TAB_STR * 2}method=\'{self._request.method}\',',
            f'{TAB_STR * 2}context=context,',
            f'{TAB_STR * 2}parameters={{',
        ]

        parameters = self._prepare_parameters()

        for name, value in parameters.items():
            param_type = self._context_declaration_map.get(name)

            if name in settings.BEHAVE_TEST_RECORDER__EXCLUDED_PARAMS:
                continue

            is_json_value = False

            if value.startswith('[') or value.startswith('{'):
                try:
                    json.loads(value)
                    is_json_value = True
                except ValueError:
                    pass

            self._add_parameter(
                name,
                param_type, 
                value,
                pre_content,
                is_json_value,
            )

        pre_content.extend([
            f'{TAB_STR * 2}}},',
            f'{TAB_STR}).execute()',
            '',
            f'{TAB_STR}setattr(context, \'response_{self._request_unique_mixin}_{self._request_path_ending}\', response)',  # noqa
        ])

        content = '\n'.join(pre_content)

        return content

    def _prepare_function_components(self) -> List[str]:
        """
        Подготавливает составляющие функции для дальнейшей конкатинации.
        """
        components = [
            self._get_function_declaration(),
            self._get_function_comment(),
            self._get_app_request(),
        ]

        return components


class StepChecksExporter(ExistedFileBaseExporter):
    """
    Экспортер проверок шага сценария,
    в виде проверок ответа каждого запроса выполненного в шаге.
    """

    def __init__(
        self,
        *args,
        recorder,
        module_path,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._recorder = recorder
        self._module_path = module_path
        self.check_function_name = None

    @classmethod
    def make_assert_statement(cls, assert_type, left, right, commented=False):
        """Формирует assert выражение заданного типа.

        Args:
            assert_type: Тип проверки.
            left: Получение проверяемых данных.
            right: Записанные эталонные данные.
            commented: Указывает, что нужно закомментировать выражение.

        Returns:
            Assert выражение.
        """
        number_sign = '# ' if commented else ''

        if not isinstance(right, str):
            right = pformat(right, width=1000000)

        return (
            f'{number_sign}{TAB_STR}context.test.{assert_type}(\n'
            f'{number_sign}{TAB_STR * 2}{left}, {right},\n'
            f'{number_sign}{TAB_STR})'
        )

    def make_json_equal_assert_statement(self, left, right, commented=False):
        """Формирует assert выражение типа assertJSONEqualWithExclusion.

        Args:
            left: Способ получения данных при выполнении теста в виде py-выражения;
            right: Записанные эталонные данные;
            commented: Указывает, что нужно закомментировать выражение.

        Returns:
            Выражение assertJSONEqualWithExclusion.
        """

        return self.make_assert_statement(
            assert_type='assertJSONEqualWithExclusion',
            left=left,
            right=right,
            commented=commented,
        )

    def make_file_equal_assert_statement(self, left, right):
        """

        Args:
            left: Способ получения данных при выполнении теста в виде py-выражения;
            right: Записанные эталонные данные.

        Returns:
            Выражение assertFileEqual.
        """
        if path_to_saved_file := self.copy_download_file_to_work_dir(right):
            assert_statement = self.make_assert_statement(
                assert_type='assertFileEqual',
                left=left,
                right=f'"{FILES_DIR}/{os.path.basename(path_to_saved_file)}"',
            )
        else:
            assert_statement = self.make_assert_statement(
                assert_type='assertFileEqual',
                left=left,
                right='""',
                commented=True,
            )
            assert_statement = (
                f'{assert_statement}\n'
                f'{TAB_STR}raise Exception(\'Не удалось получить наименование файла!\')'
            )

        return assert_statement

    def create_default_raise_statement(self, postfix):
        """Формирует raise выражение.

        Args:
            postfix: Идентификатор ответа.

        Returns:
            Raise выражение.
        """
        assert_statement = self.make_json_equal_assert_statement(
            left=f'context.response_{postfix}.content',
            right={},
            commented=True,
        )

        return (
            f'{assert_statement}\n'
            f'{TAB_STR}raise Exception(\'Не удалось сформировать assert выражение '
            f'для context.response_{postfix}.content!\')'
        )

    def _prepare_function_content(self):
        """Формирование тела функции с проверками результата каждого запроса."""
        unique_mixin = uuid.uuid4().hex[:6]
        self.check_function_name = f'check_step_{unique_mixin}'

        current_step_wo_keyword = self._recorder.current_step_wo_keyword

        if current_step_wo_keyword.endswith('"'):
            current_step_wo_keyword += f'\n{TAB_STR}'

        pre_content = [
            f'def {self.check_function_name}(context):',
            f'{TAB_STR}"""{current_step_wo_keyword}"""',
        ]

        checks_content = []

        for request_data in self._recorder.requests_data:
            postfix = f'{request_data.unique_mixin}_{request_data.path_postfix}'

            response_data = self._recorder.response_data.get(id(request_data.request))

            py_statement = self.create_assert_statement(response_data, postfix)
            if not py_statement:
                py_statement = self.create_default_raise_statement(postfix)

            checks_content.append(py_statement)

        if checks_content:
            pre_content.extend(checks_content)
        else:
            pre_content.append(f'{TAB_STR}raise Exception(\'Созданная функция не содержит проверок!\')')

        content = '\n'.join(pre_content)

        return content

    def get_download_file_name(self, response_data):
        """Получает наименование файла из ответа.

        Для каждого проекта нужно переопределение метода в соответствии с реализацией.

        Args:
            response_data: Данные ответа.

        Returns:
            Наименование файла.
        """

        return ''

    def copy_download_file_to_work_dir(self, response_data):
        """Копирует файл из директории проекта в директорию хранения файлов будущего теста.

        Args:
            response_data: Данные ответа.

        Returns:
            Путь к директории хранения файла или False.
        """
        path_to_saved_file = False

        if download_file_name := self.get_download_file_name(response_data):
            save_dir = self._module_path / FILES_DIR
            if not save_dir.exists():
                os.mkdir(save_dir)

            path_to_saved_file = shutil.copyfile(
                os.path.join(self._recorder.project_downloads_dir, download_file_name),
                os.path.join(save_dir, download_file_name.replace('/', '_'))
            )

        return path_to_saved_file

    def create_assert_statement(self, response_data, postfix):
        """Формирует assert выражение в соответствии с типом ответа.

        Args:
            response_data: Данные ответа.
            postfix: Идентификатор ответа.

        Returns:
            Assert выражение.
        """
        if response_data.type == ResponseTypeEnum.JSON:
            assert_statement = self.make_json_equal_assert_statement(
                left=f'context.response_{postfix}.content',
                right=json.loads(response_data.content),
            )

        elif response_data.type == ResponseTypeEnum.FILE_DOWNLOAD:
            assert_statement = self.make_file_equal_assert_statement(
                left=f'context, context.test.get_content_file(context.response_{postfix}.content)',
                right=response_data,
            )
        else:
            assert_statement = None

        return assert_statement

    def to_string(
        self,
        *args,
        **kwargs,
    ) -> str:
        pre_content = [
            kwargs.get('existed_file_content', ''),
            self._prepare_function_content(),
            '',
            '',
        ]

        content = '\n'.join(pre_content).lstrip()

        return content


class StepRequestExporter(ExistedFileBaseExporter):
    """
    Экспортер шага сценария состоящего из запросов к приложению в виде файла
    содержашего реализацию шага
    """

    def __init__(
        self,
        *args,
        recorder,
        check_function_name=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._recorder = recorder
        self._check_function_name = check_function_name

        self._request_loaders = []

    def _prepare_imports(self) -> str:
        """
        Формирование блока импортов загрузчиков запросов и функции проверки шага.
        """
        pre_content = [f'from behave_bo import (\n{TAB_STR}step,\n)']

        for request_data in self._recorder.requests_data:
            path_parts = request_data.file_path.parts

            request_module_name = path_parts[-1].split('.')[0]
            request_loader_alias = f'{request_module_name}_loader'

            self._request_loaders.append(request_loader_alias)

            pre_content.append(
                f'from {self._recorder.storage_module_path}.features.'
                f'{path_parts[-2]}.{request_module_name} '
                f'import request_loader as {request_loader_alias}'
            )

        if self._check_function_name:
            pre_content.append(
                f'from {self._recorder.storage_module_path}.features.'
                f'steps.{self._recorder.steps_checks_module_name} '
                f'import {self._check_function_name}'
            )

        content = '\n'.join(pre_content)

        return content

    def _prepare_function_content(self):
        """
        Формирование тела функции
        """
        current_step_wo_keyword = self._recorder.current_step_wo_keyword

        pre_content = [
            f'@step(\'{current_step_wo_keyword}\')',
            'def step_impl(context):  # pylint: disable=E0102'
        ]

        for request_loader in self._request_loaders:
            pre_content.append(f'{TAB_STR}{request_loader}(context)')

        if self._check_function_name:
            pre_content.append(f'{TAB_STR}{self._check_function_name}(context)')
        elif not self._request_loaders:
            pre_content.append(f'{TAB_STR}pass')

        content = '\n'.join(pre_content)

        return content

    def _sort_imports(
        self,
        content: str,
    ):
        """
        Сортировка импортов при помощи isort
        """
        return sort_code_string(
            code=content,
            config=settings.ISORT_CONFIG,
        )

    def to_string(
        self,
        *args,
        **kwargs,
    ) -> str:
        pre_content = [
            self._prepare_imports(),
            kwargs.get('existed_file_content', ''),
            '',
            self._prepare_function_content(),
            '',
        ]

        content = self._sort_imports(
            content='\n'.join(pre_content)
        )

        return content


class FeatureExporter(BaseExporter):
    """
    Экспортер пройденных этапов в виде feature-файла
    """
    FEATURE_TAB_STR = '  '

    def __init__(
        self,
        *args,
        recorder,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._recorder = recorder

    def to_string(
        self,
        *args,
        **kwargs,
    ) -> str:
        pre_content = [
            '# language: ru',
            '',
            f'Функционал: {self._recorder.feature_name}',
            '',
            f'{self.FEATURE_TAB_STR}@{self._recorder.lower_testlink_id}',
            f'{self.FEATURE_TAB_STR}Сценарий: {self._recorder.scenario_name}',
        ]

        all_steps = (
            self._recorder.steps_executed_before_recording +
            [passed_step.to_feature for passed_step in self._recorder.passed_steps]
        )

        for step in all_steps:
            step = step.replace(
                '\n',
                f'\n{self.FEATURE_TAB_STR * 3}'
            )
            pre_content.append(
                f'{self.FEATURE_TAB_STR * 2}{step}'
            )

        content = '\n'.join(pre_content)

        return content

    def to_file(
        self,
        *args,
        file_path: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Вывод результата экспорта в файл
        """
        if not file_path:
            file_path = str(
                self._recorder.storage_dir_path /
                f'{self._recorder.underscore_testlink_id}.feature'
            )

        result_file_path = super().to_file(
            *args,
            file_path=file_path,
            **kwargs,
        )

        return result_file_path
