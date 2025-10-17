from django.utils.deprecation import (
    MiddlewareMixin,
)

from behave_test_recorder.helpers import (
    get_behave_test_recorder_instance,
)
from behave_test_recorder.utils import (
    handle_app_not_available,
)


class TestRecordingMiddleware(MiddlewareMixin):
    """
    Middleware для записи каждого запроса в файл в случае если
    выполняется запись сценария.
    Так же сохраняется результат запроса для последующего создания проверок.
    """

    @handle_app_not_available
    def process_request(self, request):
        recorder = get_behave_test_recorder_instance()
        recorder.write_request(
            request=request,
        )

    @handle_app_not_available
    def process_response(self, request, response):
        recorder = get_behave_test_recorder_instance()
        recorder.save_response_data(
            request=request,
            response=response,
        )
        return response
