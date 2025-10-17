import os
from abc import (
    ABCMeta,
    abstractmethod,
)
from typing import (
    List,
    Optional,
)

from django.conf import (
    settings,
)
from isort.api import (
    sort_code_string,
)

from behave_test_recorder.enums import (
    UsingLibraryEnum,
)


class BaseExporter(metaclass=ABCMeta):
    """
    Абстрактный класс создания экспортеров
    """

    @abstractmethod
    def to_string(
        self,
        *args,
        **kwargs,
    ) -> str:
        pass

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
            raise ValueError()

        content = self.to_string(*args, **kwargs)

        if content:
            dir_path = os.path.split(file_path)[0]

            os.makedirs(
                dir_path,
                exist_ok=True,
            )

            with open(file_path, 'w') as f:
                f.write(content)
        else:
            print(
                f'File with path "{file_path}" can not create with empty '
                f'content!'
            )

            file_path = ''

        return file_path


class BasePyExporter(BaseExporter):
    """
    Базовый Python-экспортер
    """

    @abstractmethod
    def _get_function_declaration(self) -> str:
        """
        Возвращает строку объявления функции
        """
        pass

    def _prepare_libraries_imports(
        self,
        content: str,
    ) -> List[str]:
        """
        Подготавливает импорты библиотек
        """
        libraries_imports = []

        for key_word in UsingLibraryEnum.values.keys():
            if key_word in content:
                libraries_imports.append(
                    UsingLibraryEnum.values[key_word]
                )

        return libraries_imports

    def _prepare_imports(
        self,
        content: str,
    ) -> List[str]:
        libraries_imports = self._prepare_libraries_imports(
            content=content,
        )

        imports = [
            *libraries_imports,
        ]

        return imports

    def _add_imports(
        self,
        content: str,
    ) -> str:
        """
        Добавление и сортировка импортов
        """
        imports = self._prepare_imports(
            content=content,
        )

        content_with_imports = '\n'.join(
            [
                *imports,
                content,
            ]
        )

        return content_with_imports

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

    def _prepare_function_components(self) -> List[str]:
        """
        Подготавливает составляющие функции для дальнейшей конкатинации
        """
        components = [
            self._get_function_declaration(),
        ]

        return components

    def _prepare_function_loader_content(self) -> str:
        """
        Генерирует исходный код функции загрузки предыстории
        """
        components = self._prepare_function_components()

        pre_content = []

        for component in components:
            if component:
                pre_content.extend([component, ''])

        content = '\n'.join(pre_content)

        return content

    def to_string(
        self,
        *args,
        **kwargs,
    ) -> str:
        """
        Возвращает строку содержащую функцию factory_loader с фабриками в тебе
        и импортами всех необходимых фабрик и классов сторонних библиотек
        """
        content = self._prepare_function_loader_content()

        content = self._add_imports(
            content=content,
        )

        content = self._sort_imports(
            content=content,
        )

        return content

    def to_file(
        self,
        *args,
        file_path: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Формирование Python-фикстуры
        """
        if not file_path.endswith('.py'):
            raise ValueError(
                'Python fuxture path have not .py extension - "{fixture_path}"!'.format(
                    fixture_path=file_path,
                )
            )

        return super().to_file(
            *args,
            file_path=file_path,
            **kwargs,
        )


class ExistedFileBaseExporter(BaseExporter, metaclass=ABCMeta):
    """
    Экспортер который дополняет файл в случае если файл уже существует.
    """

    def to_file(
        self,
        *args,
        file_path: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Вывод результата экспорта в файл.
        Если файл уже существует, получим его содержимое для последующего экспорта в файл.
        """
        existed_file_content = ''

        if os.path.exists(file_path):
            with open(file_path) as steps_file:
                existed_file_content = steps_file.read()

        result_file_path = super().to_file(
            *args,
            existed_file_content=existed_file_content,
            file_path=file_path,
            **kwargs,
        )

        return result_file_path
