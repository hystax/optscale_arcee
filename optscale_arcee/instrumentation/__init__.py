_packages = []

try:
    from optscale_arcee.instrumentation import boto3
    from optscale_arcee.instrumentation import redshift_connector

    _packages.append(boto3)
    _packages.append(redshift_connector)
except ImportError:
    pass


def instrument():
    for package in _packages:
        package.instrument()
