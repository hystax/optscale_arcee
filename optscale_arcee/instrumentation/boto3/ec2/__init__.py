from optscale_arcee.instrumentation.boto3.stats import (
    Ec2Stats,
    register_service,
)
from optscale_arcee.instrumentation.boto3.utils import (
    get_service_name,
    get_package_name,
)
from optscale_arcee.instrumentation.patch import patch, revert_patches

_SERVICE = get_service_name(__file__)
_PACKAGE = get_package_name(__file__)


def instrument():
    register_service(_SERVICE, Ec2Stats)
    revert_patches(_SERVICE)
    try:
        import botocore.client
    except ImportError:
        pass
    else:
        from optscale_arcee.instrumentation.boto3.wrapper import (
            create_api_method_wrapper,
        )

        # patch basic client methods
        patch(
            _PACKAGE,
            _SERVICE,
            botocore.client.ClientCreator,
            "_create_api_method",
            create_api_method_wrapper,
            is_service_patch=True,
        )

    try:
        import boto3.resources.factory
    except ImportError:
        pass
    else:
        from optscale_arcee.instrumentation.boto3.wrapper import (
            create_action_wrapper,
        )

        # patch resource actions
        patch(
            _PACKAGE,
            _SERVICE,
            boto3.resources.factory.ResourceFactory,
            "_create_action",
            create_action_wrapper,
            is_service_patch=True,
        )
