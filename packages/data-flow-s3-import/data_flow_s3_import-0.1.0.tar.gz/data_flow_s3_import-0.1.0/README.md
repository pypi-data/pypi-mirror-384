# Data Flow S3 Importer

> This package helps Python and Django projects import data exposed by Data Flow into an S3 bucket.

Data Flow is a data pipeline service that can be made to write data into S3 buckets for ingestion by client applications.

This package will use boto to connect to the given bucket, find the right location within the bucket and read the list of files in there.

It will then take a single file and process it line by line, expecting a JSON object with an 'object' key containing a single entity on each line:

```json
...
{"object": {...}}
...
```

It is possible to override the base class for plain python projects, or the subclass for Django projects.

The subclass will process each object into an instance of the given model, which will be saved to the DB.

If the model inherits from the provided `IngestedModel`, any instances not included in the most recent fetch will be flagged as deleted upstream and won't by default appear in the queryset, although they won't be deleted.

## Usage

Make a subclass for each of the record sets you want to import.

### Plain python

If you're not using Django, or you want full control over how your models are synced (for example you don't want to use queryset methods to update them) then you should subclass the `DataFlowS3Ingest` ingester class.

This class provides various hooks for configuration and processing; the config you'll need can be applied in the subclass attributes as follows

```py
from data_flow_s3_import.ingest import DataFlowS3Ingest

class MyIngest(DataFlowS3Ingest):
    export_bucket = "my_bucket_name"
    export_path = "bucket_import_type_prefix"
    export_directory = "ingested_data_prefix/"

    def get_s3_resource(self):
        # this should return a configured and instantiated boto3 S3 resource
```

You will then want to override `process_object` and/or the other hooks in the class provided as suits your requirements.

Instantiating the class will run the ingestion automatically.

### Standard Django models

If you're using Django and want to have your import process automated, start by making a custom model in your app, extending `IngestedModel`

```py
from data_flow_s3_import.models import IngestedModel

class MyIngestedModel(IngestedModel):
    ...
```

You will also want to subclass the `DataFlowS3IngestToModel` importer, setting the mapping dictionary with the key being the model field name and the value being the imported data column name

```py
from data_flow_s3_import.ingest import DataFlowS3IngestToModel

class MyModelIngest(DataFlowS3IngestToModel):
    model = MyIngestedModel
    mapping = {
        "id": "importedColumns:id",
        "name": "importedColumns:NameField",
    }
```

And then simply instantiate your class and the ingestion will run automatically, syncing your models with the ingested records

```py
MyModelIngest(s3_resource=boto_s3_instance, bucket_name="my_bucket")
```

You will also need to configure the S3, bucket and path information as in the plain python implementation.
