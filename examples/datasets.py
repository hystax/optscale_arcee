import optscale_arcee as arcee
import time
with arcee.init("test", "simple"):
    dataset = arcee.Dataset(key='test_dataset', description='test dataset')

    # adding file
    dataset.add_file(path=__file__)

    # log new dataset_version (with file)
    arcee.log_dataset(dataset)
    print('Actual dataset version: ', dataset._version)

    # downloading
    dataset.download()

    # remove file from dataset
    dataset.remove_file(path=__file__)

    # log new dataset_version (without files)
    arcee.log_dataset(dataset)
    print('Actual dataset version: ', dataset._version)
