import optscale_arcee as arcee

with arcee.init("test", "simple"):
    arcee.tag("key", "value")
    arcee.tag("test1", "test2")
    arcee.milestone("just a milestone")
    arcee.send({"t": 2})
print(arcee.info())
