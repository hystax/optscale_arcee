_packages = []

try:
    from optscale_arcee.instrumentation import boto3

    _packages.append(boto3)
except ImportError:
    pass


def instrument():
    for package in _packages:
        package.instrument()
