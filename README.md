# Arcee
## *The OptScale ML profiling tool by Hystax*

Arcee is a tool that hepls you to integrate ML tasks with [OptScale](https://my.optscale.com/).
This tool can automatically collect executor metadata from cloud and process stats.

## Installation
Arcee requires python 3.7+ to run.
```sh
pip install optscale-arcee
```

## Import
Import the optscale_arcee module into your code as follows:
```
import optscale_arcee as arcee
```

## Initialization
To initialize the collector using a context manager, use the following code snippet:
```
with arcee.init("token", "model_key"):
    # some code
```

This method automatically handles error catching and terminates arcee execution.

Alternatively, to get more control over error catching and execution finishing, you can 
initialize the collector using a corresponding method. Note that this method will 
require you to manually handle errors or terminate arcee execution using the error
and finish methods.
```
arcee.init("token", "model_key"):
# some code
arcee.finish()
# or in case of error
arcee.error()
```

To use custom endpoint and enable\disable ssl checks (enable self-signed ssl certificates support):
```
with arcee.init("token", "model_key", endpoint_url="https://my.custom.endpoint:443/arcee/v2", ssl=False):
    # some code
```

Arcee daemon process periodically sends hardware & process info. Default heartbeat period is 1sec. However, 
arcee can be initialized with custom period:
```
with arcee.init("token", "model_key", period=5):
    # some code
```

## Sending metrics
To send metrics, use the send method with the following parameter:
- data (dict): a dictionary of metric names and their respective values (note that metric data values should be numeric).
```
arcee.send({"parameter_key_1": value_1, "parameter_key_2": value_2})
```

## Tagging model runs
To tag a model run, use the tag method with the following parameters:
- key (str): the tag name.
- value (str | number): the tag value.
```
arcee.tag("tag_key", "tag_value")
```

## Adding milestone
To add a milestone, use the milestone method with the following parameter:
- name (str): the name of the milestone.
```
arcee.milestone("milestone_name")
```

## Adding stage
To add a stage, use the stage method with the following parameter:
- name (str): the name of the stage.
```
arcee.stage("stage_name")
```

## Finishing model run
To finish a model run, use the finish method.
```
arcee.finish()
```

## Failing model run
To fail a model run, use the error method.
```
arcee.error()
```

## Instrumenting external packages
To enable all supported packages instrumentation, use base instrument method.
```
from optscale_arcee.instrumentation import instrument

instrument()
```

To enable specific package instrumentation, use package related instrument method.
```
from optscale_arcee.instrumentation import boto3 as arcee_boto3

arcee_boto3.instrument()
```

To enable service instrumentation in terms of specific package, use service related instrument method.
```
from optscale_arcee.instrumentation.boto3 import s3 as arcee_s3

arcee_s3.instrument()
```
