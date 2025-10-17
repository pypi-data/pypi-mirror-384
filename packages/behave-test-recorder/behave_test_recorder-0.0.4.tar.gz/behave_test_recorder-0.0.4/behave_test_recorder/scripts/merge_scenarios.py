import argparse
import sys
from pathlib import (
    Path,
)


def merge(feature_files_path: str, feature_files_list: str = '', final_file_name: str = '', deleting_raw: bool = False):
    """
    Перенос и объединение feature-файлов в общий feature-файл

    Args:
        feature_files_path: путь до директории features/ в которой требуется объединить feature-файлы в один
        feature_files_list: строка имён feature-файлов для объединения, разделённых запятой (без расширения .feature),
                            если не указана, то объединяет все feature-файлы в директории в один.
        final_file_name: имя итогового feature-файла (без расширения .feature). Если параметр не указан,
                         то файлы объединяются в файл с именем верхнего модуля относительно директории features/
        deleting_raw: если True, то удаляет исходные feature файлы. False по-умолчанию.

    Returns:
        None

    """
    # создаётся имя для итогового файла
    if not final_file_name:
        # [-2] указывает на имя верхнего модуля относительно директории features/
        final_file_name = Path(feature_files_path).parts[-2]
    final_file_name = f'{final_file_name}.feature'
    # проверка существует ли итоговый файл
    final_file_exists = Path(feature_files_path).joinpath(final_file_name).exists()

    if not feature_files_list:
        feature_files_list = sorted(Path(feature_files_path).glob('*.feature'))
        feature_files_list = [el.name for el in feature_files_list]
        if final_file_name in feature_files_list:
            feature_files_list.remove(final_file_name)

    else:
        feature_files_list = feature_files_list.split(',')
        feature_files_list = sorted([f'{el}.feature' for el in feature_files_list])
        if final_file_name in feature_files_list:
            raise AssertionError('Итоговый файл не может быть в списке!')

    with open(Path(feature_files_path).joinpath(final_file_name), 'a+') as final_file:
        if final_file_exists:
            # проверяет есть ли пустая строка в конце дополняемого файла
            final_file.seek(final_file.tell()-1)
            got_empty_line = final_file.read() == '\n'
        else:
            got_empty_line = False

        # переменные для проверки необходимости записи строки '# language:' и 'Функционал:' в файл
        got_language = final_file_exists
        got_description = final_file_exists

        for filename in feature_files_list:
            with open(Path(feature_files_path).joinpath(filename), 'r') as iter_file:
                for line in iter_file:
                    if (
                        ('# language:' in line and got_language) or
                        ('Функционал:' in line and got_description)
                    ):
                        continue

                    if '# language:' in line:
                        got_language = True
                    elif 'Функционал:' in line:
                        got_description = True

                    if got_empty_line and line == '\n':
                        got_empty_line = False
                        continue

                    final_file.write(line)

    if deleting_raw:
        for filename in feature_files_list:
            Path(feature_files_path).joinpath(filename).unlink()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise AssertionError('Не хватает обязательного параметра feature_files_path!')

    parser = argparse.ArgumentParser(description='Перенос и объединение feature-файлов в общий feature-файл')

    parser.add_argument('feature_files_path', help='путь до директории features/', type=str)
    parser.add_argument('--feature_files_list', help='исходные feature-файлы через запятую, без .feature', type=str)
    parser.add_argument('--final_file_name', help='имя итогового feature-файла (без расширения .feature)', type=str)
    parser.add_argument('--deleting_raw', help='когда True - удаляет исходные feature файлы', type=bool)

    args = parser.parse_args()
    merge(**vars(args))
