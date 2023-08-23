from optscale_arcee.instrumentation.boto3.stats import (
    S3Stats, register_service)
from optscale_arcee.instrumentation.boto3.utils import (
    get_service_name, get_package_name)
from optscale_arcee.instrumentation.patch import patch, revert_patches

_SERVICE = get_service_name(__file__)
_PACKAGE = get_package_name(__file__)

_S3_TRANSFER_METHODS = [
    'download_file', 'download_fileobj',
    'upload_file', 'upload_fileobj',
    'copy']
# bucket upload\download methods are wrappers over s3 transfer methods
_BUCKET_METHODS = ['bucket_load']
# object upload\download methods are wrappers over s3 transfer methods
_OBJECT_METHODS = ['object_summary_load']
_STREAMING_BODY_METHODS = ['read', 'readline', 'readlines']


def instrument():
    register_service(_SERVICE, S3Stats)
    revert_patches(_SERVICE)
    try:
        import botocore.client
    except ImportError:
        pass
    else:
        from optscale_arcee.instrumentation.boto3.wrapper import (
            create_api_method_wrapper)

        # patch basic client methods
        patch(_PACKAGE, _SERVICE, botocore.client.ClientCreator,
              '_create_api_method', create_api_method_wrapper,
              is_service_patch=True)

    try:
        import boto3.resources.factory
    except ImportError:
        pass
    else:
        from optscale_arcee.instrumentation.boto3.wrapper import (
            create_action_wrapper)

        # patch resource actions
        patch(_PACKAGE, _SERVICE, boto3.resources.factory.ResourceFactory,
              '_create_action', create_action_wrapper,
              is_service_patch=True)

    try:
        import boto3.s3.inject
    except ImportError:
        pass
    else:
        from optscale_arcee.instrumentation.boto3.wrapper import (
            injected_methods_wrapper)

        # patch client based injected methods
        for method in _S3_TRANSFER_METHODS + _BUCKET_METHODS + _OBJECT_METHODS:
            patch(_PACKAGE, _SERVICE, boto3.s3.inject,
                  method, injected_methods_wrapper,
                  is_service_patch=True)

    try:
        import s3transfer.futures
    except ImportError:
        pass
    else:
        from optscale_arcee.instrumentation.boto3.wrapper import submit_wrapper
        # patch default ThreadPoolExecutor to be able to map inners calls
        # to injected methods
        patch(_PACKAGE, _SERVICE, s3transfer.futures.BoundedExecutor,
              'submit', submit_wrapper)

    try:
        import s3transfer.tasks
    except ImportError:
        pass
    else:
        from optscale_arcee.instrumentation.boto3.wrapper import (
            task_call_wrapper)

        # patch s3 task __call__ to be able to map inners calls
        # to injected methods
        patch(_PACKAGE, _SERVICE, s3transfer.tasks.Task,
              '__call__', task_call_wrapper)

    try:
        import botocore.response
    except ImportError:
        pass
    else:
        from optscale_arcee.instrumentation.boto3.wrapper import (
            streaming_body_read_wrapper)

        # patch StreamingBody to count downloaded bytes
        for method in _STREAMING_BODY_METHODS:
            patch(_PACKAGE, _SERVICE, botocore.response.StreamingBody,
                  method, streaming_body_read_wrapper,
                  is_service_patch=True)
