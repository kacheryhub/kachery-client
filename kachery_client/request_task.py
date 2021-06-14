from typing import Any, Tuple, Union
from ._daemon_connection import _daemon_url
from ._misc import _http_post_json, _http_get_json

class OutgoingTaskRequest:
    def __init__(self, *, channel: str, task_id: str, task_function_type: str, task_result_url: Union[str, None], status: str, error_message: Union[str, None], query_result: Union[Any, None]):
        self._channel = channel
        self._task_id = task_id
        self._task_function_type = task_function_type
        self._task_result_url = task_result_url
        self._status = status
        self._error_message = error_message
        self._query_result = query_result
        self._downloaded_result: Union[Any, None] = None
    @property
    def status(self):
        return self._status
    @property
    def task_result_url(self):
        return self._task_result_url
    @property
    def task_result(self):
        if self._status != 'finished':
            raise Exception('Cannot get task result if status is not finished')
        if self._downloaded_result:
            return self._downloaded_result
        if not self._task_result_url:
            raise Exception('No task result url')
        self._downloaded_result = _http_get_json(self._task_result_url)
        return self._downloaded_result
    @property
    def query_result(self):
        if self._status != 'finished':
            raise Exception('Cannot get query result if status is not finished')
        return self._query_result
    @property
    def error_message(self):
        return self._error_message
    def wait(self, timeout_sec: float):
        if self._status not in ['finished', 'error']:
            daemon_url, headers = _daemon_url()
            # export type TaskWaitForTaskResultRequest = {
            #     channelName: ChannelName
            #     taskId: TaskId
            #     taskFunctionType: TaskFunctionType,
            #     timeoutMsec: DurationMsec
            # }
            url = f'{daemon_url}/task/waitForTaskResult'
            req_data = {
                'channelName': self._channel,
                'taskId': self._task_id,
                'taskFunctionType': self._task_function_type,
                'timeoutMsec': timeout_sec * 1000
            }
            x = _http_post_json(url, req_data, headers=headers)
            if not x['success']:
                print(x)
                raise Exception(f'Unable to wait on task')
            # export type TaskWaitForTaskResultResponse = {
            #     success: boolean
            #     status: TaskStatus
            #     errorMessage?: ErrorMessage
            #     taskResultUrl?: UrlString
            #     queryResult?: JSONValue
            # }
            self._status = x['status']
            self._task_result_url = x.get('taskResultUrl', None)
            self._error_message = x.get('errorMessage', None)
            self._query_result = x.get('queryResult', None)
        if self._status == 'error':
            raise Exception(f'Task error: {self._error_message}')
        if self._status == 'finished':
            if self._task_function_type == 'pure-calculation':
                return self.task_result
            elif self._task_function_type == 'query':
                return self.query_result
            elif self._task_function_type == 'action':
                return True
            else:
                raise Exception(f'Unexpected function type: {self._task_function_type}')
        return None

def request_task(*, task_function_id: str, task_kwargs: dict, task_function_type: str, channel: str) -> OutgoingTaskRequest:
    daemon_url, headers = _daemon_url()
    url = f'{daemon_url}/task/requestTask'
    # export type TaskRequestTaskRequest = {
    #     channelName: ChannelName
    #     taskFunctionId: TaskFunctionId
    #     taskKwargs: TaskKwargs
    #     taskFunctionType: TaskFunctionType
    #     timeoutMsec: DurationMsec
    # }
    req_data = {
        'channelName': channel,
        'taskFunctionId': task_function_id,
        'taskKwargs': task_kwargs,
        'taskFunctionType': task_function_type,
        'timeoutMsec': 1000
    }
    x = _http_post_json(url, req_data, headers=headers)
    # export type TaskRequestTaskResponse = {
    #     success: boolean
    #     taskId: TaskId,
    #     status: TaskStatus
    #     errorMessage?: ErrorMessage
    #     taskResultUrl?: UrlString
    #     queryResult?: JSONValue
    # }
    if not x['success']:
        raise Exception(f'Unable to load task result')
    status = x['status']
    task_id = x['taskId']
    task_result_url = x.get('taskResultUrl', None)
    query_result = x.get('queryResult', None)
    error_message = x.get('errorMessage', None)
    return OutgoingTaskRequest(channel=channel, task_id=task_id, task_function_type=task_function_type, task_result_url=task_result_url, status=status, error_message=error_message, query_result=query_result)