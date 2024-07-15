# Arcee
## *The OptScale ML profiling tool by Hystax*

Arcee is a tool that helps you to integrate ML tasks with [OptScale](https://my.optscale.com/).
This tool can automatically collect executor metadata from cloud and process stats.

## Installation
Arcee requires python 3.7+ to run.
To install the optscale_arcee package, use pip:
```sh
pip install optscale-arcee
```

## Import
Import the optscale_arcee module into your code as follows:
```sh
import optscale_arcee as arcee
```

## Initialization
To initialize the arcee collector you need to provide a profiling token and a task key for which you want to collect data.
To initialize the collector using a context manager, use the following code snippet:
```sh
with arcee.init(token, task_key):
    # some code
```
Example:
```sh
with arcee.init("00000000-0000-0000-0000-000000000000", "linear_regression"):
    # some code
```
This method automatically handles error catching and terminates arcee execution.

Alternatively, to get more control over error catching and execution finishing, you can initialize the collector using a corresponding method.
Note that this method will require you to manually handle errors or terminate arcee execution using the error and finish methods.
```sh
arcee.init(token, task_key)
# some code
arcee.finish()
# or in case of error
arcee.error()
```

To use custom endpoint and enable/disable ssl checks (enable self-signed ssl certificates support):
```sh
with arcee.init(token, task_key, endpoint_url="https://my.custom.endpoint:443/arcee/v2", ssl=False):
    # some code
```
Arcee daemon process periodically sends hardware and process data. Default heartbeat period is 1sec. However, arcee can be initialized with custom period:
```sh
with arcee.init(token, task_key, period=5):
    # some code
```

## Sending metrics
To send metrics, use the send method with the following metric:
- data (dict, required): a dictionary of metric names and their respective values (note that metric data values should be numeric).
```sh
arcee.send({"metric_key_1": value_1, "metric_key_2": value_2})
```
example:
```sh
arcee.send({"accuracy": 71.44, "loss": 0.37})
```

## Adding hyperparameters
To add hyperparameters, use the hyperparam method with the following parameters:
- key (str, required): the hyperparameter name.
- value (str | number, required): the hyperparameter value.
```sh
arcee.hyperparam(key, value)
```
example:
```sh
arcee.hyperparam("EPOCHS", 100)
```

## Tagging task run
To tag a run, use the tag method with the following metrics:
- key (str, required): the tag name.
- value (str | number, required): the tag value.
```sh
arcee.tag(key, value)
```
example:
```sh
arcee.tag("Algorithm", "Linear Learn Algorithm")
```

## Adding milestone
To add a milestone, use the milestone method with the following metric:
- name (str, required): the name of the milestone.
```sh
arcee.milestone(name)
```
example:
```sh
arcee.milestone("Download training data")
```

## Adding stage
To add a stage, use the stage method with the following metric:
- name (str, required): the name of the stage.
```sh
arcee.stage(name)
```
example:
```sh
arcee.stage("preparing")
```

## Logging datasets
To log a dataset, use the dataset method with the following parameter:
- path (str): the path of the dataset.
- name (str): the name of the dataset.
- description (str): the description of the dataset.
- labels (list): the list of labels of the dataset.
```
arcee.dataset(path, name, description, labels)
```
Example:
```
arcee.dataset("https://s3/ml-bucket/datasets/training_dataset.csv",
              name="Training dataset",
              description="Training dataset (100k rows)",
              labels=["training", "100k"])
```

## Creating models
To create a model, use the model method with the following parameters:
- key (str, required): the unique key of the model
- path (str, optional): the path of the run model
```
arcee.model(key, path)
```
example:
```
arcee.model("my_model", "/home/user/my_model")
```

## Setting model version
To set custom model version, use the model_version method with the following parameter:
- version (str, required): version name
```sh
arcee.model_version(version)
```
example:
```sh
arcee.model_version("1.2.3-release")
```

## Setting model version alias
To set model version alias, use the model_version_alias method with the following parameter:
- alias (str, required): alias name
```sh
arcee.model_version_alias(alias)
```
example:
```sh
arcee.model_version_alias("winner")
```

## Setting model version tag
To add tags to a model version, use the model_version_tag method with the following parameters:
- key (str, required): tag name
- value (str, required): tag value
```sh
arcee.model_version_tag(key, value)
```
example:
```sh
arcee.model_version_tag("env", "staging demo")
```

## Creating artifacts
To create an artifact, use the artifact method with the following parameters:
- path (str, required): the path of the run artifact
- name (str, optional): the name of the artifact
- description (str, optional): the description of the artifact
- tags (dict, optional): the tags of the artifact in format {"key": "value"}
```sh
arcee.artifact(path, name, description, tags)
```
example:
```sh
arcee.artifact("https://s3/ml-bucket/artifacts/AccuracyChart.png",
               name="Accuracy line chart",
               description="The dependence of accuracy on the time",
               tags={"env": "staging"})
```

## Setting artifact tag
To add tag to an artifact, use the artifact_tag method with the following parameters:
- path (str, required): the path of the run artifact
- key (str, required): tag name
- value (str, required): tag value
```sh
arcee.artifact_tag(path, key, value)
```
example:
```sh
arcee.artifact_tag("https://s3/ml-bucket/artifacts/AccuracyChart.png",
                   "env", "staging demo")
```

## Finishing task run
To finish a run, use the finish method.
```sh
arcee.finish()
```

## Failing task run
To fail a run, use the error method.
```sh
arcee.error()
```