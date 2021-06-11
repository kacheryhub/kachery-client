from .taskfunction import find_taskfunction

class RegisteredTaskFunction:
    def __init__(self, *, task_function_id: str, channel: str) -> None:
        self._task_function_id = task_function_id
        self._channel = channel
    @property
    def task_function_id(self):
        return self._task_function_id
    @property
    def channel(self):
        return self._channel
    def run(self, *, kwargs: dict):
        f = find_taskfunction(self.task_function_id)
        if f is None:
            raise Exception(f'Unable to find task function: {self.task_function_id}')
        return f(**kwargs)