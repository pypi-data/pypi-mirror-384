import datetime
import json
import logging
from typing import Any, Iterable, Iterator, Optional

import boto3
from django.db.models import Model
from django.db.models.manager import BaseManager
from smart_open import open as smart_open

from data_flow_s3_import.models import IngestedModel
from data_flow_s3_import.types import (
    PrimaryKey,
    S3BotoResource,
    S3Bucket,
    S3ObjectSummary,
)

logger = logging.getLogger(__name__)


class RequiredModelNotSet(Exception): ...


class DataFlowS3Ingest:
    date_format_mapping: dict[str, str] | None = None
    datetime_format_mapping: dict[str, str] | None = None
    export_bucket: str
    export_path: str
    export_directory: str
    delete_after_import: bool = True

    def __init__(
        self,
        s3_resource: S3BotoResource | None = None,
        bucket_name: str | None = None,
    ) -> None:
        self.s3_resource: S3BotoResource = s3_resource or self.get_s3_resource()
        if bucket_name is not None:
            self.export_bucket = bucket_name
        self.bucket: S3Bucket = self.s3_resource.Bucket(self.export_bucket)
        self.ingest_file: S3ObjectSummary | None = None
        self.other_files: list[S3ObjectSummary] = []

        return self._process_all_workflow()

    def get_s3_resource(self) -> S3BotoResource:
        """
        Hook for boto resource initialiser. Not required if object is initialised with resource.
        """
        return boto3.resource("s3")

    def get_export_path(self) -> str:
        """
        Get the bucket key prefix from the combination of env config and imported data type string
        """
        return f"{self.export_path}/{self.export_directory}"

    def preprocess_all(self) -> None:
        """
        A hook for pre-processing required before any rows in the active file are sent for processing.
        """
        ...

    def process_all(self):
        data: Iterator[str] | None = self._get_data_to_ingest()

        if data is None:
            logger.info(f"DataFlow S3 {self.__class__}: No data found to ingest")
            return

        for item in data:
            self.process_row(line=item)

    def postprocess_all(self) -> None:
        """
        A hook for any post-processing required after all row by processing is completed
        """
        ...

    def process_row(self, line: str) -> PrimaryKey:
        """
        Takes a row of the file, retrieves a dict of the instance it refers to and hands that off for processing
        """
        row: dict = json.loads(s=line)
        obj: dict = row["object"]  # standard for the Data Flow structure
        return self._process_object_workflow(obj=obj)

    def preprocess_object(self, obj: dict) -> None:
        """
        A hook for any pre-processing required before the main object is written to the DB
        """
        # Handle date fields
        if self.date_format_mapping:
            for field, format in self.date_format_mapping.items():
                obj[field] = self.process_date(obj[field], format)
        # Handle datetime fields
        if self.datetime_format_mapping:
            for field, format in self.datetime_format_mapping.items():
                obj[field] = self.process_datetime(obj[field], format)

    def process_object(self, obj: dict, **kwargs):
        raise NotImplementedError()

    def process_datetime(self, date_string: str, format: str) -> str:
        """
        A hook for processing non standard dates with time.
        """
        try:
            # Return date in ISO format
            return datetime.datetime.isoformat(
                datetime.datetime.strptime(date_string, format)
            )
        except:
            # Return date in unmodified format
            logger.warning(
                f"DataFlow S3 {self.__class__}: Failed to parse Date : {date_string} using format : {format} returning {date_string}"
            )
            self.on_date_mapping_error(date_string)
            return date_string

    def process_date(self, date_string: str, format: str) -> str:
        """
        A hook for processing non standard dates.
        """
        try:
            # Return date in ISO format
            return datetime.date.isoformat(
                datetime.datetime.strptime(date_string, format)
            )
        except:
            # Return date in unmodified format
            logger.warning(
                f"DataFlow S3 {self.__class__}: Failed to parse Date : {date_string} using format : {format} returning {date_string}"
            )
            self.on_date_mapping_error(date_string)
            return date_string

    def postprocess_object(self, obj: dict, **kwargs) -> None:
        """
        A hook for any post-processing required after the main object is written to the DB
        """
        ...

    def _process_all_workflow(self) -> None:
        logger.info(f"DataFlow S3 {self.__class__}: Starting S3 ingest")

        if not self._get_files_to_ingest():
            logger.info(f"DataFlow S3 {self.__class__}: No files to ingest")
            return

        self.preprocess_all()

        self.process_all()

        self.postprocess_all()

        self._cleanup()

    def _process_object_workflow(self, obj: dict) -> Any:
        """
        Takes a dict referring to a single model instance and saves that instance to the DB using the model manager method.
        """
        self.preprocess_object(obj=obj)

        output = self.process_object(obj=obj)

        self.postprocess_object(obj=obj)

        return output

    def _get_files_to_ingest(self) -> list:
        """
        Get all the files that "could" be ingested and order them by last
        modified date (oldest first)
        """
        logger.info(
            f"DataFlow S3 {self.__class__}: Reading files from bucket {self.bucket}"
        )
        files: Iterable[S3ObjectSummary] = self.bucket.objects.filter(
            Prefix=self.get_export_path()
        )

        sorted_files: list[S3ObjectSummary] = sorted(
            files, key=lambda x: x.last_modified, reverse=False
        )
        for file in sorted_files:
            file.source_key = f"s3://{file.bucket_name}/{file.key}"
            logger.info(
                f"DataFlow S3 {self.__class__}: Found S3 file with key {file.source_key}"
            )

        return sorted_files

    def _get_data_to_ingest(self) -> Iterator[str]:
        """Yields row by row from the most recent ingestable file"""
        # Get all files in the export directory
        files_to_process = self._get_files_to_ingest()

        if not len(files_to_process):
            return

        # Select the most recent file
        self.ingest_file = files_to_process[-1]
        self.other_files = files_to_process[:-1]

        # Read the file and yield each line
        with smart_open(
            self.ingest_file.source_key,
            "r",
            transport_params={
                "client": self.s3_resource.meta.client,
            },
            encoding="utf-8",
        ) as file_input_stream:
            logger.info(
                f"DataFlow S3 {self.__class__}: Processing file {self.ingest_file.source_key}"
            )
            for line in file_input_stream:
                yield line

    def _cleanup(self) -> None:
        """
        Delete all other files in the export directory except the ingested file
        """
        files_to_delete = []

        if self.other_files:
            files_to_delete.extend(self.other_files)

        delete_keys = [{"Key": file.key} for file in files_to_delete]

        if delete_keys and not self.delete_after_import:
            logger.info(
                f"DataFlow S3 {self.__class__}: NOT Deleting keys {delete_keys}"
            )
            return

        if delete_keys:
            logger.info(f"DataFlow S3 {self.__class__}: Deleting keys {delete_keys}")
            self.bucket.delete_objects(Delete={"Objects": delete_keys})

    def on_date_mapping_error(self, obj):
        """
        A hook for custom behaviour when a string date failes to be transformed to ISO correctly.
        """
        pass


class DataFlowS3IngestToModel(DataFlowS3Ingest):
    model: type[IngestedModel]
    model_uses_baseclass: bool = True
    identifier_field_name: str = "id"
    identifier_field_object_mapping: str = "id"
    mapping: dict[str, str]
    imported_pks: Optional[list[PrimaryKey]] = None

    def get_model(self) -> type[IngestedModel]:
        """Get model object to create for each row"""
        try:
            return self.model
        except AttributeError:
            raise RequiredModelNotSet()

    def get_model_manager(self) -> BaseManager[Model]:
        """Get manager to use for Django data creation methods"""
        return self.get_model().objects

    def process_all(self):
        self.imported_pks: list[PrimaryKey] = []
        for item in self._get_data_to_ingest():
            created_updated_pk: PrimaryKey = self.process_row(line=item)
            # Don't add failed rows to the PK list
            if created_updated_pk is not None:
                self.imported_pks.append(created_updated_pk)

    def process_object(self, obj: dict, **kwargs) -> PrimaryKey:
        """
        Takes a dict referring to a single model instance and saves that instance to the DB using the model manager method.
        """
        # Handle empty string values like "" for default fields
        defaults = {
            key: None if obj[value] == "" else obj[value]
            for key, value in self.mapping.items()
        }

        if self.model_uses_baseclass:
            defaults["exists_in_last_import"] = True

        kwargs = {"defaults": defaults}
        # Handle empty string values like "" against primary key
        mapped_value = obj[self.identifier_field_object_mapping]
        kwargs[self.identifier_field_name] = (
            None if mapped_value == "" else mapped_value
        )

        try:

            instance, _ = self.get_model_manager().update_or_create(**kwargs)  # type: ignore

            logger.info(
                f"DataFlow S3 {self.__class__}: Added {self.model} record for"
                + f" {getattr(instance, self.identifier_field_name)}"
            )

            return getattr(instance, self.identifier_field_name)

        except BaseException as error:
            logger.error(
                f"DataFlow S3 {self.__class__}: Failed to create {self.model} record for "
                + f"{kwargs[self.identifier_field_name]} , Reason: {error}"
            )
            self.on_model_mapping_error(kwargs)

        return None

    def _cleanup(self) -> None:
        if self.imported_pks is None:
            logger.info(
                f"DataFlow S3 {self.__class__}: Nothing has been imported,"
                + " so nothing to clean up"
            )

        if self.model_uses_baseclass:
            self.mark_deleted_upstream()

        return super()._cleanup()

    def mark_deleted_upstream(self) -> None:
        """Mark the objects that are no longer in the S3 file."""
        logger.info(
            f"DataFlow S3 {self.__class__}: Marking models deleted upstream {self.imported_pks}"
        )
        self.get_model_manager().exclude(pk__in=self.imported_pks).update(  # type: ignore
            exists_in_last_import=False
        )

    def on_model_mapping_error(self, obj):
        """
        A hook for custom behaviour when a object failes to be mapped to a Django model correctly.
        """
        pass
