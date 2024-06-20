# Arcee
## *The OptScale ML profiling tool by Hystax*

Arcee is a tool that helps you to integrate ML tasks with [OptScale](https://my.optscale.com/).
This tool can automatically collect executor metadata from cloud and process stats.

## Installation
Arcee requires python 3.7+ to run.
```sh
pip install optscale-arcee
```

## Usage
First of all you need to import and init arcee in your code:
```sh
import optscale_arcee as arcee
```

```sh
# init arcee using context manager syntax
with arcee.init('token', 'task_key'):
    # some code
```

To use custom endpoint and enable\disable ssl checks (supports using self-signed ssl certificates):
```sh
with arcee.init('token', 'task_key', endpoint_url='https://my.custom.endpoint:443/arcee/v2', ssl=False):
    # some code
```

Alternatively arcee can be initialized via function call. However manual finish is required:
```sh
arcee.init('token', 'task_key')
# some code
arcee.finish()
```

Or in error case:
```sh
arcee.init('token', 'task_key')
# some code
arcee.error()
```

To send stats:
```sh
arcee.send({"loss": 2.0012, "iter": 2, "epoch": 1})
```
(key should be string, value - int or float, multiple values can be sent)

To add tags to model run (key, value):
```sh
arcee.tag("project", "torchvision demo")
```

To add milestones:
```sh
arcee.milestone("Download test data")
```

To add stages:
```sh
arcee.stage("calculation")
```

To add hyperparameters:
```sh
arcee.hyperparam("epochs", 5)
```

## Logging datasets
To log a dataset, use the dataset method with the following parameter:
- path (str): the path of the dataset.
```
arcee.dataset("dataset_path")
```

## Models
To create a model, use the model method with the following parameters:
- key (str): the unique key of the model
- path (str): the path of the run model
```
arcee.model("my_model", "/home/user/my_model")
```

To set a custom model version, use the model_version method with the following parameter:
- version (str): version name
```
arcee.model_version("1.2.3-release")
```

To set a model version alias, use the model_version_alias method with the following parameter:
- alias (str): alias name
```
arcee.model_version_alias("winner")
```

To add tags to model version (key, value):
```
arcee.model_version_tag("env", "staging demo")
```

## Artifacts
To create an artifact, use the artifact method with the following parameters:
- path (str): the path of the run artifact
- name (str): the name of the artifact
- description (str): the description of the artifact
- tags (str): the tags of the artifact in format {"key": "value"}
```
arcee.artifact("https://s3/ml-bucket/artifacts/AccuracyChart.png",
               name="Accuracy line chart",
               description="The dependence of accuracy on the time",
               tags={"env": "staging"})
```

To add tags to existing artifact (path, key, value):
```
arcee.artifact_tag("https://s3/ml-bucket/artifacts/AccuracyChart.png",
                   "env", "staging demo")
```
