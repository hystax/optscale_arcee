import optscale_arcee as arcee

with arcee.init("test", "simple"):
    arcee.tag("key", "value")
    arcee.tag("test1", "test2")
    arcee.milestone("just a milestone")
    arcee.model("model_key", "/src/simple.py")
    arcee.model_version("1.23.45-rc")
    arcee.model_version_alias("winner")
    arcee.model_version_tag("key", "value")
    arcee.send({"t": 2})
    arcee.artifact(
        "https://s3/ml-bucket/artifacts/AccuracyChart.png",
        "Accuracy line chart",
        "The dependence of accuracy on the time",
        {"env": "staging"})
    arcee.artifact_tag("https://s3/ml-bucket/artifacts/AccuracyChart.png",
                       "key", "value")
print(arcee.info())
