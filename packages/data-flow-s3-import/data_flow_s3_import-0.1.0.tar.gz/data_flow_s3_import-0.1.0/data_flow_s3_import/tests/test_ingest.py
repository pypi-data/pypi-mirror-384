import json

import pytest

from data_flow_s3_import.ingest import DataFlowS3Ingest
from data_flow_s3_import.tests.utils import S3BotoResource


def test_attributes_and_init(mocker):
    s3r_mocked = S3BotoResource()
    mock_get_s3r = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest.get_s3_resource",
        return_value=s3r_mocked,
    )
    mock_process_all = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_all_workflow",
        return_value=None,
    )
    s3r = S3BotoResource()

    dfi = DataFlowS3Ingest(s3_resource=s3r, bucket_name="bucket_name")

    assert dfi.s3_resource == s3r
    assert dfi.bucket.name == "bucket_name"
    assert dfi.ingest_file == None
    assert dfi.other_files == []
    mock_get_s3r.assert_not_called()
    mock_process_all.assert_called_once()

    dfi = DataFlowS3Ingest(bucket_name="bucket_name")

    mock_get_s3r.assert_called_once()
    assert dfi.s3_resource == s3r_mocked
    assert dfi.bucket.name == "bucket_name"

    with pytest.raises(AttributeError):
        dfi = DataFlowS3Ingest()


def test_get_export_path(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_all_workflow",
        return_value=None,
    )

    class Test(DataFlowS3Ingest):
        export_path = "hello"
        export_directory = "world"

    dfi = Test(s3_resource=S3BotoResource(), bucket_name="bucket_name")
    assert dfi.get_export_path() == "hello/world"


def test_process_all_workflow(mocker):
    mock_get_files = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._get_files_to_ingest",
        return_value=None,
    )
    mock_preprocess = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest.preprocess_all", return_value=None
    )
    mock_process = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest.process_all", return_value=None
    )
    mock_postprocess = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest.postprocess_all", return_value=None
    )
    mock_cleanup = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._cleanup", return_value=None
    )

    DataFlowS3Ingest(s3_resource=S3BotoResource(), bucket_name="bucket_name")
    mock_get_files.assert_called_once()
    mock_preprocess.assert_not_called()
    mock_process.assert_not_called()
    mock_postprocess.assert_not_called()
    mock_cleanup.assert_not_called()

    mock_get_files.return_value = ["__file__"]
    mock_get_files.reset_mock()

    DataFlowS3Ingest(s3_resource=S3BotoResource(), bucket_name="bucket_name")
    mock_get_files.assert_called_once()
    mock_preprocess.assert_called_once()
    mock_process.assert_called_once()
    mock_postprocess.assert_called_once()
    mock_cleanup.assert_called_once()


def test_process_all(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._get_files_to_ingest",
        return_value=None,
    )
    mock_get_data = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._get_data_to_ingest",
        return_value=None,
    )
    mock_process_row = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest.process_row", return_value=None
    )

    dfi = DataFlowS3Ingest(s3_resource=S3BotoResource(), bucket_name="bucket_name")

    assert dfi.process_all() == None
    mock_get_data.assert_called_once()
    mock_process_row.assert_not_called()

    mock_get_data.return_value = ["__item__"]
    dfi.process_all()
    mock_process_row.assert_called_once_with(line="__item__")

    mock_process_row.reset_mock()
    mock_get_data.return_value = ["__item__", "", "_items_"]
    dfi.process_all()
    assert mock_process_row.call_count == 3


def test_process_row(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._get_files_to_ingest",
        return_value=None,
    )
    mock_process_obj = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_object_workflow",
        return_value=None,
    )

    dfi = DataFlowS3Ingest(s3_resource=S3BotoResource(), bucket_name="bucket_name")

    with pytest.raises(json.decoder.JSONDecodeError):
        dfi.process_row(line="")

    with pytest.raises(KeyError):
        dfi.process_row(line='{"type":67}')

    dfi.process_row(line='{"object":67}')
    mock_process_obj.assert_called_once_with(obj=67)


def test_process_object_workflow(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._get_files_to_ingest",
        return_value=None,
    )
    mock_preprocess_obj = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest.preprocess_object",
        return_value=None,
    )
    mock_process_obj = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest.process_object", return_value=None
    )
    mock_postprocess_obj = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest.postprocess_object",
        return_value=None,
    )

    dfi = DataFlowS3Ingest(s3_resource=S3BotoResource(), bucket_name="bucket_name")
    dfi._process_object_workflow({"__object__": 9886})

    mock_preprocess_obj.assert_called_once_with(obj={"__object__": 9886})
    mock_process_obj.assert_called_once_with(obj={"__object__": 9886})
    mock_postprocess_obj.assert_called_once_with(obj={"__object__": 9886})


def test_get_files_to_ingest(mocker):
    class File:
        def __init__(self, key, modified, bucket):
            self.key = key
            self.last_modified = modified
            self.bucket_name = bucket

    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_all_workflow",
        return_value=None,
    )
    mock_get_path = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest.get_export_path",
        return_value="__path__",
    )
    bucket = mocker.Mock()
    bucket.objects.filter.return_value = []

    dfi = DataFlowS3Ingest(s3_resource=S3BotoResource(), bucket_name="bucket_name")
    dfi.bucket = bucket

    assert dfi._get_files_to_ingest() == []

    bucket.objects.filter.return_value = [
        File(key="one", modified=99, bucket="__bucket__"),
        File(key="two", modified=66, bucket="bucket"),
        File(key="three", modified=0, bucket="B"),
        File(key="four", modified=999, bucket="BBB"),
    ]
    ret = dfi._get_files_to_ingest()
    assert ret[0].key == "three"
    assert ret[0].source_key == "s3://B/three"
    assert ret[1].key == "two"
    assert ret[1].source_key == "s3://bucket/two"
    assert ret[2].key == "one"
    assert ret[2].source_key == "s3://__bucket__/one"
    assert ret[3].key == "four"
    assert ret[3].source_key == "s3://BBB/four"


def test_get_data_to_ingest(mocker):
    class File:
        def __init__(self, key):
            self.source_key = key

    mock_get_files = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._get_files_to_ingest",
        return_value=[],
    )
    data_lines = ["line 1", "line 2", "line 3"]
    iter = mocker.Mock()
    iter.return_value = data_lines
    mock_smart_open = mocker.patch(
        "data_flow_s3_import.ingest.smart_open",
        return_value=mocker.Mock(__next__=iter, __enter__=iter, __exit__=mocker.Mock()),
    )

    s3r = S3BotoResource()
    dfi = DataFlowS3Ingest(s3_resource=s3r, bucket_name="bucket_name")

    ret = dfi._get_data_to_ingest()
    assert list(ret) == []
    mock_smart_open.assert_not_called()

    files = [File("__newest_file__"), File("__file2__"), File("__oldest_file__")]
    mock_get_files.return_value = files

    i = 1
    for ret in list(dfi._get_data_to_ingest()):  # type: ignore
        assert ret == f"line {i}"
        i += 1

    assert dfi.ingest_file == files[2]
    assert len(dfi.other_files) == 2
    assert files[1] in dfi.other_files
    assert files[0] in dfi.other_files
    mock_smart_open.assert_called_once_with(
        "__oldest_file__",
        "r",
        transport_params={"client": s3r.meta.client},
        encoding="utf-8",
    )


def test_cleanup(mocker):
    class File:
        def __init__(self, key):
            self.key = key

    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._get_files_to_ingest",
        return_value=None,
    )

    dfi = DataFlowS3Ingest(s3_resource=S3BotoResource(), bucket_name="bucket_name")
    dfi.delete_after_import = False
    dfi.bucket = mocker.Mock()

    dfi._cleanup()
    dfi.bucket.delete_objects.assert_not_called()

    file1 = File(key="one")
    file2 = File(key="two")
    file3 = File(key="three")
    dfi.ingest_file = file1

    dfi._cleanup()
    dfi.bucket.delete_objects.assert_not_called()

    dfi.delete_after_import = True
    dfi._cleanup()
    dfi.bucket.delete_objects.assert_not_called()

    dfi.other_files = [file2, file3]
    dfi.bucket.delete_objects.reset_mock()
    dfi._cleanup()
    dfi.bucket.delete_objects.assert_called_once_with(
        Delete={"Objects": [{"Key": "two"}, {"Key": "three"}]}
    )
