from copy import (
    copy,
)

from django.test.utils import (
    ContextList,
)

from behave_test_recorder.consts import (
    RECORDING_TASK_SESSION_KEY,
)


response_context_storage = {}


def store_render_contexts(request_id, signal, sender, template, context, **kwargs):
    """Обрабатывает сигнал рендеринга шаблона.

    Сохраняет контекст рендеринга запроса в хранилище response_context_storage.

    Args:
        request_id: Идентификатор объекта django-запроса.
        signal: Объект django-сигнала.
        sender: Объект отправителя, в нашем случае объект класса Template.
        template: Объект класса Template.
        context: Объект django-контекста для рендеринга шаблона (объекта класса Template).
    """
    if request_id in response_context_storage:
        response_context_storage[request_id].append(copy(context))
    else:
        context_list = ContextList()
        context_list.append(copy(context))
        response_context_storage[request_id] = context_list


def logout_while_test_recording(user, request, **kwargs):
    """Обрабатывет сигнал логаута во время работающей записи теста.

    Если запись осуществляется - заполним в ключ в объект сессии,
    чтобы далее корректно продолжать запись запросов.

    Args:
        user: Объект django-модели пользователя.
        request: Объект django-запроса.
    """
    from behave_test_recorder.helpers import (
        get_behave_test_recorder_instance,
    )
    recorder = get_behave_test_recorder_instance()
    if (
        recorder.is_started and
        RECORDING_TASK_SESSION_KEY not in request.session
    ):
        request.session[RECORDING_TASK_SESSION_KEY] = recorder.task_id
