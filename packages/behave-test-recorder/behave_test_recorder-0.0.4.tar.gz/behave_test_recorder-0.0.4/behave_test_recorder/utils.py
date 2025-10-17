import ast
from functools import (
    partial,
    wraps,
)

from django.http import (
    HttpResponseForbidden,
)
from django.test import (
    signals,
)

from behave_test_recorder.exceptions import (
    AppNotAvailableException,
)
from behave_test_recorder.receivers import (
    store_render_contexts,
)


key_template = "template-render-{}"


def template_rendered_connect(request):
    """Подключает обработчик к сигналу рендеринга шаблона конкрентног запроса.

    Args:
        request: Объект django-запроса.
    """
    on_template_render = partial(store_render_contexts, id(request))

    signals.template_rendered.connect(
        on_template_render,
        weak=False,
        dispatch_uid=key_template.format(id(request)),
    )


def template_rendered_disconnect(request):
    """Отключает обработчик к сигналу рендеринга шаблона.

    Args:
        request: Объект django-запроса.
    """
    signals.template_rendered.disconnect(
        dispatch_uid=key_template.format(id(request))
    )


def handle_app_not_available(func):
    """Декоратор для обработки исключения недоступости приложения."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(
                *args,
                **kwargs,
            )
        except AppNotAvailableException as exc:
            result = HttpResponseForbidden(str(exc))

        return result

    return wrapper


def literal_eval(pks):
    """Выполняет строку содержащую python-выражение.

    Args:
        pks: набор ID в виде строки или другого объекта
    """

    if isinstance(pks, str):
        pks = ast.literal_eval(pks)

    return pks
