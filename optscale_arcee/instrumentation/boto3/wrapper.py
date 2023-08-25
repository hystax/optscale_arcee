import inspect
import logging
import os

from optscale_arcee.instrumentation.boto3.stats import (
    count_downloaded_bytes, count_uploaded_bytes, count_file, count_method,
    is_service_registered, count_files)
from optscale_arcee.instrumentation.boto3.utils import (
    ThreadedMethodsTracker, get_service_name)
from optscale_arcee.instrumentation.patch import update_wrapper


CALLER_FUNCTION_NAME = f'_{get_service_name(__file__)}_caller_function'
LOG = logging.getLogger(__name__)


def map_values_to_params(func, *args, **kwargs) -> dict:
    signature = inspect.signature(func)
    params = signature.bind(*args, **kwargs)
    # TODO: set defaults also if not passed
    return params.arguments


def is_threaded_method() -> bool:
    # inner method may be called in separate thread of task executor
    return ThreadedMethodsTracker().get() is not None


def is_rewrapped_method(distance: int = 1) -> bool:
    # distance between current func stack and tracking wrapper
    # default value is set for the following case:
    # 0 - this func
    # 1 - rewrapped candidate frame
    res = False
    stack = inspect.stack()
    if len(stack) > distance + 1:
        wrapper_frame = stack[distance]
        upper_frames = stack[distance + 1:]
        # calling wrapped method inside another wrapped method
        res |= any(map(lambda x:
                       x.filename == wrapper_frame.filename and
                       x.function == wrapper_frame.function,
                       upper_frames))
    return res


def upload_part(
        service: str, params: dict, is_threaded: bool, is_rewrapped: bool
):
    # always count uploaded bytes
    count_uploaded_bytes(service, len(params['kwargs'].get('Body', {})))


def delete_object(
        service: str, params: dict, is_threaded: bool, is_rewrapped: bool
):
    if is_threaded or is_rewrapped:
        return
    count_file(service, params['kwargs']['Bucket'], params['kwargs']['Key'])


def delete_objects(
        service: str, params: dict, is_threaded: bool, is_rewrapped: bool
):
    if is_threaded or is_rewrapped:
        return
    filenames = list(map(
        lambda x: x['Key'], params['kwargs']['Delete']['Objects']))
    if 'Bucket' not in params['kwargs']:
        bucket = params['self'].name
    else:
        bucket = params['kwargs']['Bucket']
    count_files(service, bucket, filenames)


def get(
        service: str, params: dict, is_threaded: bool, is_rewrapped: bool
):
    if is_threaded or is_rewrapped:
        return
    # Bucket and key are properties of Object (s3.Object)
    count_file(service, params['self'].bucket_name, params['self'].key)


def delete(
        service: str, params: dict, is_threaded: bool, is_rewrapped: bool
):
    if is_threaded or is_rewrapped:
        return
    # Bucket and key are properties of Object (s3.Object)
    count_file(service, params['self'].bucket_name, params['self'].key)


def copy_object(
        service: str, params: dict, is_threaded: bool, is_rewrapped: bool
):
    if is_threaded or is_rewrapped:
        return
    # all "simple" methods params are kwargs
    count_file(service, params['kwargs']['CopySource']['Bucket'],
               params['kwargs']['CopySource']['Key'])
    # 'Key' on download_fileobj, upload_file, upload_fileobj
    count_file(service, params['kwargs']['Bucket'],
               params['kwargs']['Key'])


def put_object(
        service: str, params: dict, is_threaded: bool, is_rewrapped: bool
):
    if not is_threaded and not is_rewrapped:
        # Bucket may be property of Bucket object (s3.Bucket)
        if 'Bucket' not in params['kwargs']:
            bucket = params['self'].name
        else:
            bucket = params['kwargs']['Bucket']
        # count file if method called directly
        count_file(service, bucket, params['kwargs']['Key'])
    if not is_rewrapped:
        # count in direct and threaded calls (part of complex method) cases
        try:
            count_uploaded_bytes(
                service, len(params['kwargs'].get('Body', '')))
        except Exception as ex:  # typically TypeError
            LOG.debug('%s - %s', type(ex), str(ex))
            if hasattr(params['kwargs'].get('Body', ''), 'name'):
                count_uploaded_bytes(
                    service, os.stat(params['kwargs']['Body'].name).st_size)


HANDLER_FUNCTIONS = {
    'upload_part': upload_part,
    'delete_object': delete_object,
    'delete_objects': delete_objects,
    'get': get,
    'delete': delete,
    'copy_object': copy_object,
    'put_object': put_object
}


def method_wrapper(service, original):
    def _method(*args, **kwargs):
        res = original(*args, **kwargs)
        is_threaded = is_threaded_method()
        is_rewrapped = is_rewrapped_method()
        if not is_threaded and not is_rewrapped:
            count_method(service, original.__name__)
        handler_func = HANDLER_FUNCTIONS.get(original.__name__)
        if handler_func:
            params = map_values_to_params(original, *args, **kwargs)
            handler_func(service, params, is_threaded, is_rewrapped)
        return res
    return _method


def create_action_wrapper(service, original, *args, **kwargs):
    action = original(*args, **kwargs)
    service_context = map_values_to_params(
        original, *args, **kwargs).get('service_context')
    if not service_context:
        return action
    resource_service = getattr(service_context, 'service_name', None)
    if not is_service_registered(resource_service):
        return action
    if resource_service != service:
        return action
    wrapped_action = method_wrapper(service, action)
    return update_wrapper(wrapped_action, action)


def create_api_method_wrapper(service, original, *args, **kwargs):
    api_method = original(*args, **kwargs)
    service_model = map_values_to_params(
        original, *args, **kwargs).get('service_model')
    if not service_model:
        return api_method
    client_service = getattr(service_model, 'service_name', None)
    if not is_service_registered(client_service):
        return api_method
    if client_service != service:
        return api_method
    wrapped_api_method = method_wrapper(service, api_method)
    return update_wrapper(wrapped_api_method, api_method)


def injected_methods_wrapper(service, original, *args, **kwargs):
    res = original(*args, **kwargs)
    # ignore specific injected methods which call list_buckets and head_object
    if original.__name__ not in ['bucket_load', 'object_summary_load']:
        count_method(service, original.__name__)
    params = map_values_to_params(original, *args, **kwargs)
    if 'Key' in params and 'Bucket' in params:
        if original.__name__ == 'copy':
            # on copy handle source and target
            count_file(service, params['CopySource']['Bucket'],
                       params['CopySource']['Key'])
        count_file(service, params['Bucket'], params['Key'])
    return res


def submit_wrapper(original, *args, **kwargs):
    # if task is submitted from submitted task
    caller_function = ThreadedMethodsTracker().get()
    if caller_function is None:
        # if task is submitted from main thread
        # typically is submitted from base wrapped method (injected)
        stack = inspect.stack()
        caller_function = None
        for idx, frame in enumerate(stack):
            # if wrapped then call already counted
            if frame.function == 'injected_methods_wrapper':
                caller_function = stack[idx - 1].function
                break
    # setting attribute to pass caller function name
    # inside task __call__ method
    params = map_values_to_params(original, *args, **kwargs)
    if caller_function:
        setattr(params['task'], CALLER_FUNCTION_NAME, caller_function)
    future = original(**params)
    return future


def task_call_wrapper(original, *args, **kwargs):
    cls_self = args[0]
    if hasattr(cls_self, CALLER_FUNCTION_NAME):
        with ThreadedMethodsTracker().manage_method(
                getattr(cls_self, CALLER_FUNCTION_NAME)):
            res = original(*args, **kwargs)
    else:
        res = original(*args, **kwargs)
    return res


def streaming_body_read_wrapper(service, original, *args, **kwargs):
    res = original(*args, **kwargs)
    count_downloaded_bytes(service, len(res))
    return res
