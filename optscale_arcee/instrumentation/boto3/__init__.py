_services = []

try:
    from optscale_arcee.instrumentation.boto3 import s3

    _services.append(s3)
except ImportError:
    pass

try:
    from optscale_arcee.instrumentation.boto3 import ec2

    _services.append(ec2)
except ImportError:
    pass


def instrument():
    for service in _services:
        service.instrument()
