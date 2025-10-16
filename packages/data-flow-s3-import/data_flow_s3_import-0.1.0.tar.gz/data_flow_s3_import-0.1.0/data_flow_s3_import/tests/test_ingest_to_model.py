import pytest

from data_flow_s3_import.ingest import DataFlowS3IngestToModel, RequiredModelNotSet
from data_flow_s3_import.tests.utils import S3BotoResource


def test_init_and_attributes(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_all_workflow",
        return_value=None,
    )
    dfm = DataFlowS3IngestToModel(
        s3_resource=S3BotoResource(), bucket_name="bucket_name"
    )
    assert dfm.imported_pks == None
    assert dfm.bucket.name == "bucket_name"


def test_get_model(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_all_workflow",
        return_value=None,
    )
    dfm = DataFlowS3IngestToModel(
        s3_resource=S3BotoResource(), bucket_name="bucket_name"
    )

    with pytest.raises(RequiredModelNotSet):
        assert dfm.get_model()

    dfm.model = "__model__"  # type: ignore
    assert dfm.get_model() == "__model__"


def test_get_model_manager(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_all_workflow",
        return_value=None,
    )
    model = mocker.Mock()
    get_model = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3IngestToModel.get_model",
        return_value=model,
    )
    dfm = DataFlowS3IngestToModel(
        s3_resource=S3BotoResource(), bucket_name="bucket_name"
    )
    assert dfm.get_model_manager() == model.objects
    get_model.assert_called_once_with()


def test_process_all(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3IngestToModel._get_files_to_ingest",
        return_value=None,
    )
    mock_get_data = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3IngestToModel._get_data_to_ingest",
        return_value=[],
    )
    mock_process_row = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3IngestToModel.process_row",
        return_value="-pk-",
    )

    dfm = DataFlowS3IngestToModel(
        s3_resource=S3BotoResource(), bucket_name="bucket_name"
    )

    assert dfm.process_all() == None
    assert dfm.imported_pks == []
    mock_get_data.assert_called_once()
    mock_process_row.assert_not_called()

    mock_get_data.return_value = ["__item__"]
    dfm.process_all()
    assert dfm.imported_pks == ["-pk-"]
    mock_process_row.assert_called_once_with(line="__item__")

    mock_process_row.reset_mock()
    mock_get_data.return_value = ["__item__", "", "_items_"]
    dfm.process_all()
    assert dfm.imported_pks == ["-pk-", "-pk-", "-pk-"]
    assert mock_process_row.call_count == 3


def test_process_object(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_all_workflow",
        return_value=None,
    )
    manager = mocker.Mock()
    instance = mocker.Mock()
    manager.update_or_create.return_value = (instance, True)
    mock_get_manager = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3IngestToModel.get_model_manager",
        return_value=manager,
    )
    dfm = DataFlowS3IngestToModel(
        s3_resource=S3BotoResource(), bucket_name="bucket_name"
    )
    dfm.mapping = {
        "first_field": "first",
        "second_field": "second",
        "third_field": "third",
    }
    dfm.model = mocker.Mock()

    with pytest.raises(KeyError):
        dfm.process_object(
            {
                "first": 34,
                "second": 992,
                "three": "Joseph",
                "pk": "__pk__",
            },
        )

    dfm.mapping = {
        "first_field": "first",
        "second_field": "second",
        "third_field": "three",
    }
    with pytest.raises(KeyError):
        dfm.process_object(
            {
                "first": 34,
                "second": 992,
                "pk": "__pk__",
            },
        )

    with pytest.raises(KeyError):
        dfm.process_object(
            {
                "first": 34,
                "second": 992,
                "three": "Joseph",
                "pk": "__pk__",
            },
        )

    dfm.identifier_field_name = "pk"
    dfm.identifier_field_object_mapping = "pk"
    mock_get_manager.reset_mock()
    ret = dfm.process_object(
        {
            "first": 34,
            "second": 992,
            "three": "Joseph",
            "pk": "__pk__",
        },
    )
    assert ret == instance.pk
    mock_get_manager.assert_called_once()
    manager.update_or_create.assert_called_once_with(
        pk="__pk__",
        defaults={
            "first_field": 34,
            "second_field": 992,
            "third_field": "Joseph",
            "exists_in_last_import": True,
        },
    )

    dfm.model_uses_baseclass = False
    manager.update_or_create.reset_mock()

    dfm.process_object(
        {
            "first": 34,
            "second": 992,
            "three": "Joseph",
            "pk": "__pk__",
        },
    )
    manager.update_or_create.assert_called_once_with(
        pk="__pk__",
        defaults={
            "first_field": 34,
            "second_field": 992,
            "third_field": "Joseph",
        },
    )


def test_cleanup(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_all_workflow",
        return_value=None,
    )
    mock_super_cleanup = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._cleanup",
        return_value=None,
    )
    mock_mark_deleted = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3IngestToModel.mark_deleted_upstream",
        return_value=None,
    )
    dfm = DataFlowS3IngestToModel(
        s3_resource=S3BotoResource(), bucket_name="bucket_name"
    )

    dfm._cleanup()
    mock_mark_deleted.assert_called_once_with()
    mock_super_cleanup.assert_called_once_with()

    mock_mark_deleted.reset_mock()
    mock_super_cleanup.reset_mock()
    dfm.model_uses_baseclass = False

    dfm._cleanup()
    mock_mark_deleted.assert_not_called()
    mock_super_cleanup.assert_called_once_with()


def test_mark_deleted_upstream(mocker):
    mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3Ingest._process_all_workflow",
        return_value=None,
    )
    manager = mocker.Mock()
    mock_qs = mocker.Mock()
    manager.exclude.return_value = mock_qs
    mock_get_manager = mocker.patch(
        "data_flow_s3_import.ingest.DataFlowS3IngestToModel.get_model_manager",
        return_value=manager,
    )
    dfm = DataFlowS3IngestToModel(
        s3_resource=S3BotoResource(), bucket_name="bucket_name"
    )
    dfm.imported_pks = [1, 2, 3]

    dfm.mark_deleted_upstream()
    mock_get_manager.assert_called_once_with()
    manager.exclude.assert_called_once_with(pk__in=[1, 2, 3])
    mock_qs.update.assert_called_once_with(exists_in_last_import=False)
