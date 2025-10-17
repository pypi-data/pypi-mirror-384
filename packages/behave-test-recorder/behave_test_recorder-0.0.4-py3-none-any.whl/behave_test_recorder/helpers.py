import json
from collections import (
    namedtuple,
)
from pathlib import (
    Path,
)
from typing import (
    List,
)

from behave_bo.enums import (
    StepTypeEnum,
)
from django.conf import (
    settings,
)

from behave_test_recorder.consts import (
    STEPS_EXECUTED_BEFORE_RECORDING_FILE_NAME,
)


STEP_TYPES = {
    'Дано': StepTypeEnum.GIVEN,
    'Когда': StepTypeEnum.WHEN,
    'То': StepTypeEnum.THEN,
}

Row = namedtuple('Row', ['cells'])
Table = namedtuple('Table', ['headings', 'rows'])
TestlinkStep = namedtuple('Step', ['step_type', 'keyword', 'name', 'table'])


def prepare_table(table_str: str) -> Table:
    """Выполняет обработку таблицы для рендеринга перед обновлением в testlink

    Args:
        table_str: Таблица в виде строки (gherkin формата)

    Returns:
        Таблица с атрибутами необходимыми для рендеринга.

    """
    def cells_of(row: str) -> list:
        """
        Преобразует строку(с разделителем | ) в список ячеек.
        """
        return [cell.strip() for cell in row.split('|')[1:-1]]

    headings, *rows = table_str.strip().split('\n')

    return Table(
        headings=cells_of(headings),
        rows=[Row(cells=cells_of(row)) for row in rows]
    )


def prepare_steps_for_testlink_update(recorded_steps: List) -> List[TestlinkStep]:
    """Выполняет обработку шагов для рендеринга перед обновлением в testlink.

    Args:
        recorded_steps: Список записанных шагов.

    Returns:
        Список шагов с атрибутами необходимыми для рендеринга.

    """
    step_type = StepTypeEnum.GIVEN
    steps = []
    for step in recorded_steps:
        step_type = STEP_TYPES.get(step.keyword, step_type)

        table = None
        if step.table:
            table = prepare_table(step.table)

        steps.append(
            TestlinkStep(
                step_type=step_type,
                keyword=step.keyword,
                name=step.name,
                table=table,
            )
        )

    return steps


def save_steps_as_json_for_recorder(steps: List):
    """Сохраняет шаги behave в формате json для дальнейшего использования в рекордере.

    Args:
        steps: список шагов behave_bo.model.Step

    """
    steps_list = []
    for step in steps:
        if step.table:
            table = [step.table.headings] + [row.cells for row in step.table.rows]
            table = '\n'.join([f'| {" | ".join(row)} |' for row in table])
            steps_list.append(f'{step.keyword} {step.name}\n{table}')
        else:
            steps_list.append(f'{step.keyword} {step.name}')

    path = Path(
        settings.BEHAVE_TEST_RECORDER__PROJECT_ROOT_DIR_PATH /
        settings.BEHAVE_TEST_RECORDER__STORED_GENERATED_FILES_PATH,
    )
    path.mkdir(parents=True, exist_ok=True)

    with open(path / STEPS_EXECUTED_BEFORE_RECORDING_FILE_NAME, 'w') as file:
        file.write(json.dumps(steps_list))


def get_behave_test_recorder_instance():
    recorder_cls = settings.BEHAVE_TEST_RECORDER__RECORDER_CLASS
    recorder_cls_path = recorder_cls.split('.')
    # Allow for relative paths
    if len(recorder_cls_path) > 1:
        extractor_module_name = '.'.join(recorder_cls_path[:-1])
    else:
        extractor_module_name = '.'
    extractor_module = __import__(extractor_module_name, {}, {}, recorder_cls_path[-1])
    behave_recorder_class = getattr(extractor_module, recorder_cls_path[-1])
    return behave_recorder_class()
