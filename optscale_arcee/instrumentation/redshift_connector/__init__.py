from optscale_arcee.instrumentation.patch import patch, revert_patches
from optscale_arcee.instrumentation.utils import get_package_name

_PACKAGE = get_package_name(__file__)


def instrument():
    revert_patches(_PACKAGE)
    try:
        import redshift_connector
    except ImportError:
        pass
    else:
        from optscale_arcee.instrumentation.redshift_connector.wrapper import (
            close_wrapper,
        )

        patch(
            _PACKAGE,
            None,
            redshift_connector.core.Connection,
            "close",
            close_wrapper,
        )
