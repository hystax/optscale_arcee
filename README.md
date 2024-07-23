# Arcee
## *The OptScale ML profiling tool by Hystax*

Arcee is a tool that helps you to integrate ML tasks with [OptScale](https://my.optscale.com/).
This tool can automatically collect executor metadata from the cloud and process stats.

## Installation
Arcee requires Python 3.7+ to run.
To install the `optscale_arcee` package, use pip:
```sh
pip install optscale-arcee
```

## Import
Import the `optscale_arcee` module into your code as follows:
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
Note that this method will require you to manually handle errors or terminate arcee execution using the `error` and `finish` methods.
```sh
arcee.init(token, task_key)
# some code
arcee.finish()
# or in case of error
arcee.error()
```

To use a custom endpoint and enable/disable SSL checks (enable self-signed SSL certificates support):
```sh
with arcee.init(token, task_key, endpoint_url="https://my.custom.endpoint:443/arcee/v2", ssl=False):
    # some code
```
Arcee daemon process periodically sends hardware and process data. The default heartbeat period is 1 second. However, arcee can be initialized with a custom period:
```sh
with arcee.init(token, task_key, period=5):
    # some code
```

## Sending metrics
To send metrics, use the `send` method with the following parameter:
- data (dict, required): a dictionary of metric names and their respective values (note that metric data values should be numeric).
```sh
arcee.send({ "metric_key_1": value_1, "metric_key_2": value_2 })
```
Example:
```sh
arcee.send({ "accuracy": 71.44, "loss": 0.37 })
```

## Adding hyperparameters
To add hyperparameters, use the `hyperparam` method with the following parameters:
- key (str, required): the hyperparameter name.
- value (str | number, required): the hyperparameter value.
```sh
arcee.hyperparam(key, value)
```
Example:
```sh
arcee.hyperparam("EPOCHS", 100)
```

## Tagging task run
To tag a run, use the `tag` method with the following parameters:
- key (str, required): the tag name.
- value (str | number, required): the tag value.
```sh
arcee.tag(key, value)
```
Example:
```sh
arcee.tag("Algorithm", "Linear Learn Algorithm")
```

## Adding milestone
To add a milestone, use the `milestone` method with the following parameter:
- name (str, required): the milestone name.
```sh
arcee.milestone(name)
```
Example:
```sh
arcee.milestone("Download training data")
```

## Adding stage
To add a stage, use the `stage` method with the following parameter:
- name (str, required): the stage name.
```sh
arcee.stage(name)
```
Example:
```sh
arcee.stage("preparing")
```

## Logging datasets
To log a dataset, use the `dataset` method with the following parameters:
- path (str, required): the dataset path.
- name (str, optional): the dataset name.
- description (str, optional): the dataset description.
- labels (list, optional): the dataset labels.
```sh
arcee.dataset(path, name, description, labels)
```
Example:
```sh
arcee.dataset("https://s3/ml-bucket/datasets/training_dataset.csv",
              name="Training dataset",
              description="Training dataset (100k rows)",
              labels=["training", "100k"])
```

## Creating models
To create a model, use the `model` method with the following parameters:
- key (str, required): the unique model key.
- path (str, optional): the run model path.
```sh
arcee.model(key, path)
```
Example:
```sh
arcee.model("my_model", "/home/user/my_model")
```

## Setting model version
To set a custom model version, use the `model_version` method with the following parameter:
- version (str, required): the version name.
```sh
arcee.model_version(version)
```
Example:
```sh
arcee.model_version("1.2.3-release")
```

## Setting model version alias
To set a model version alias, use the `model_version_alias` method with the following parameter:
- alias (str, required): the alias name.
```sh
arcee.model_version_alias(alias)
```
Example:
```sh
arcee.model_version_alias("winner")
```

## Setting model version tag
To add tags to a model version, use the `model_version_tag` method with the following parameters:
- key (str, required): the tag name.
- value (str, required): the tag value.
```sh
arcee.model_version_tag(key, value)
```
Example:
```sh
arcee.model_version_tag("env", "staging demo")
```

## Creating artifacts
To create an artifact, use the `artifact` method with the following parameters:
- path (str, required): the run artifact path.
- name (str, optional): the artifact name.
- description (str, optional): the artifact description.
- tags (dict, optional): the artifact tags.
```sh
arcee.artifact(path, name, description, tags)
```
Example:
```sh
arcee.artifact("https://s3/ml-bucket/artifacts/AccuracyChart.png",
               name="Accuracy line chart",
               description="The dependence of accuracy on the time",
               tags={"env": "staging"})
```

## Setting artifact tag
To add a tag to an artifact, use the `artifact_tag` method with the following parameters:
- path (str, required): the run artifact path.
- key (str, required): the tag name.
- value (str, required): the tag value.
```sh
arcee.artifact_tag(path, key, value)
```
Example:
```sh
arcee.artifact_tag("https://s3/ml-bucket/artifacts/AccuracyChart.png",
                   "env", "staging demo")
```

## Finishing task run
To finish a run, use the `finish` method.
```sh
arcee.finish()
```

## Failing task run
To fail a run, use the `error` method.
```sh
arcee.error()
```