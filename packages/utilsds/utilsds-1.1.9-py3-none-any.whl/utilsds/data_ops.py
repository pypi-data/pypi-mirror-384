"""
Class to handle data operations
"""

import json
import warnings
from pathlib import Path
from typing import Any

import cloudpickle as pickle
import pandas as pd
from google.cloud import bigquery, bigquery_storage, storage


class DataOperations:
    """
    A class for handling data operations locally and with Google Cloud services (BigQuery and Cloud Storage).

    Parameters
    ----------
    project : str
        Google Cloud project ID for initializing clients.
    """

    SUPPORTED_FILE_TYPES = [".pkl", ".json", ".csv", ".html", ".sql"]
    SUPPORTED_WRITE_DISPOSITIONS = ["TRUNCATE", "APPEND", "EMPTY"]

    def __init__(self, project: str):
        self.bq_client = bigquery.Client(project=project)
        self.bq_storage_client = bigquery_storage.BigQueryReadClient()
        self.gcs_client = storage.Client(project=project)
        self.bigquery = bigquery

    def dry_run(self, query: str) -> None:
        """
        Dry run a query to estimate data processed.

        Parameters
        ----------
        query: str
            SQL query to dry run
        """

        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

        query_job = self.bq_client.query(query, job_config=job_config)

        print(f"Estimated data processed: {self.format_bytes(query_job.total_bytes_processed)}")

    def load_bq_details(self, source: str, get_view_query: bool = False) -> str | None:
        """
        Get detailed information about a BigQuery table including schema, row count,
        creation time, expiration time, and other metadata.
        For views, the view query can be returned.

        Parameters
        ----------
        source : str
            Full table ID in format 'project.dataset.table'
        get_view_query: bool, optional
            If True, the view query will be returned.
        """
        table_obj = self.bq_client.get_table(source)

        print(f"Full ID: {table_obj.full_table_id}")
        print(f"Type: {table_obj.table_type}")
        print(f"Created: {table_obj.created.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Last Modified: {table_obj.modified.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        print("\n=== Schema ===")
        print("Column Name".ljust(30) + "Type".ljust(15) + "Mode")
        print("-" * 55)
        for field in table_obj.schema:
            print(f"{field.name.ljust(30)}{field.field_type.ljust(15)}{field.mode}")

        if table_obj.table_type == "TABLE":
            print(f"Row Count: {table_obj.num_rows:,}")
            print(f"Size: {self.format_bytes(table_obj.num_bytes)}")

            if table_obj.time_partitioning:
                print("\n=== Partitioning ===")
                print(f"Type: {table_obj.time_partitioning.type_}")
                print(f"Field: {table_obj.time_partitioning.field}")

            if table_obj.clustering_fields:
                print("\n=== Clustering ===")
                print(f"Clustering Fields: {', '.join(table_obj.clustering_fields)}")

        elif table_obj.table_type == "VIEW" and get_view_query:
            return str(table_obj.view_query)

        return None

    def save_bq_view(self, destination: str, sql: str, local_path: str | None = None) -> None:
        """
        Save view to BigQuery

        Parameters
        ----------
        destination: str
            BigQuery destination table ID
        query: str
            SQL query to create view
        local_path: str, optional
            If provided, the view will be saved locally at this path.
        """

        self.dry_run(sql)

        view = bigquery.Table(destination)
        view.view_query = sql
        view = self.bq_client.create_table(view, exists_ok=True)

        print(f"View {view.table_id} created successfully.")

        if local_path:
            self.save_local_file(local_path, sql)

    def load_bq_data(
        self,
        source: str,
        destination: bool = False,
        local_path: str | None = None,
    ) -> pd.DataFrame:
        """
        Returns data from BigQuery as DataFrame, either from a table/view or SQL file.

        Parameters
        ----------
        source: str
            Supported types: table/view ID (performs SELECT *), path to SQL file, or a direct SQL query.
        destination: bool, optional
            If True, saves query results in a temporary table and prints its ID (default: False)
        local_path: str, optional
            If provided, the data will be saved locally at this path.

        Returns
        ----------
        pd.DataFrame
            Data from the query.
        """
        if Path(source).suffix.lower() == ".sql":
            with open(source, "r") as f:
                sql = f.read()
        elif source.strip().upper().startswith("SELECT"):
            sql = source
        else:
            sql = f"SELECT * FROM `{source}`"

        job_config_params = {"use_query_cache": True}
        if not destination:
            job_config_params["destination"] = None  # type: ignore

        job_config = bigquery.QueryJobConfig(**job_config_params)

        query_job = self.bq_client.query(
            sql,
            job_config=job_config,
        )

        results = query_job.to_dataframe(bqstorage_client=self.bq_storage_client)

        print(f"Bytes processed: {self.format_bytes(query_job.total_bytes_processed)}")
        print(f"Bytes billed: {self.format_bytes(query_job.total_bytes_billed)}")

        if destination:
            temp_table = query_job.destination.to_api_repr()
            temp_table_id = f"{temp_table['projectId']}.{temp_table['datasetId']}.{temp_table['tableId']}"
            print(f"Temp table ID: {temp_table_id}")

        if local_path:
            self.save_local_file(local_path, results)
        return results

    def load_bq_procedure(
        self, procedure_name: str, parameters: list[Any] | None = None, local_path: str | None = None
    ) -> pd.DataFrame | None:
        """
        Calls a stored procedure in BigQuery. If the procedure returns data, it is returned as a DataFrame.

        Parameters
        ----------
        procedure_name: str
            Name of the stored procedure to call.
        parameters: list, optional
            List of parameters to pass to the procedure.
        local_path: str, optional
            If provided, the data will be saved locally at this path.

        Returns
        ----------
        pd.DataFrame
            Result of the procedure call. Returns None if procedure doesn't output any data.

        Raises
        ----------
        Warning
            If the procedure execution was successful but didn't return any data.
        """
        try:
            param_str = ", ".join(parameters) if parameters else ""
            sql = f"""
            CALL `{procedure_name}`({param_str})
            """

            query_job = self.bq_client.query(sql)

            if query_job.result().total_rows > 0:
                results = query_job.to_dataframe()
                if local_path:
                    self.save_local_file(local_path, results)
                return results
            else:
                warnings.warn(
                    f"Procedure {procedure_name} executed successfully but didn't return any data.", stacklevel=2
                )
                return None
        except Exception as e:
            raise Exception(f"Error executing procedure {procedure_name}: {str(e)}") from e

    def save_bq_table(
        self,
        df: pd.DataFrame,
        table: str,
        write: str,
        schema: list[bigquery.SchemaField] | None = None,
        partition_field: str | None = None,
        partition_type: bigquery.TimePartitioningType | None = None,
        clustering_fields: list[str] | None = None,
        local_path: str | None = None,
    ) -> None:
        """
        Function to write dataframe to BigQuery table

        Parameters
        ----------
        df: pd.DataFrame
            Dataframe to write.
        table: string
            Table ID in BigQuery to write dataframe.
        write: str
            Write disposition for the job ('TRUNCATE', 'APPEND', 'EMPTY')
        schema: list[bigquery.SchemaField], optional
            List of BigQuery SchemaField objects defining the schema.
            If None, the schema will be automatically inferred from the DataFrame.
        partition_field: str, optional
            Field to use for table partitioning.
        partition_type: bigquery.TimePartitioningType, optional
            Type of partitioning to use (DAY, HOUR, MONTH, YEAR).
        clustering_fields: list[str], optional
            List of columns to use for clustering. Maximum of 4 columns.
        local_path: str, optional
            If provided, the data will be saved locally at this path.
        """

        write_map = {
            "TRUNCATE": bigquery.WriteDisposition.WRITE_TRUNCATE,
            "APPEND": bigquery.WriteDisposition.WRITE_APPEND,
            "EMPTY": bigquery.WriteDisposition.WRITE_EMPTY,
        }

        if schema:
            table_ref = bigquery.Table(table, schema=schema)
        else:
            table_ref = bigquery.Table(table)

        if write.upper() not in self.SUPPORTED_WRITE_DISPOSITIONS:
            raise ValueError(
                f"Unsupported write disposition. Supported dispositions are: {self.SUPPORTED_WRITE_DISPOSITIONS}"
            )

        if (partition_field or partition_type) and not schema:
            raise ValueError("Schema must be provided when using table partitioning")

        if (partition_field is None) != (partition_type is None):
            raise ValueError("Both partition_field and partition_type must be provided together")

        if clustering_fields is not None and len(clustering_fields) > 4:
            raise ValueError("BigQuery supports a maximum of 4 clustering fields")

        if partition_field and partition_type:
            table_ref.time_partitioning = bigquery.TimePartitioning(type_=partition_type, field=partition_field)

        if clustering_fields:
            table_ref.clustering_fields = clustering_fields

        self.bq_client.create_table(table_ref, exists_ok=True)

        job_config = bigquery.LoadJobConfig(write_disposition=write_map[write.upper()], schema=schema)

        job = self.bq_client.load_table_from_dataframe(df, table, job_config=job_config)
        job.result()

        self.load_bq_details(table)

        if local_path:
            self.save_local_file(local_path, df)

    def delete_bq_data(self, target: str, where_clause: str | None = None) -> None:
        """
        Delete data from BigQuery table.

        Parameters
        ----------
        target: str
            Name of table/view to delete data from. Without WHERE clause, the entire target is deleted.
        where_clause: str, optional
            Where clause (starting with WHERE) to filter data for deletion, for tables only.
        """
        if where_clause:
            count_sql = f"""
            SELECT COUNT(*) as count
            FROM `{target}`
            {where_clause}
            """
            count_result = self.bq_client.query(count_sql).result()
            affected_rows = next(iter(count_result))[0]

            sql = f"""
            DELETE FROM `{target}` {where_clause}
            """
            query_job = self.bq_client.query(sql)
            query_job.result()
            print(f"Successfully deleted {affected_rows:,} rows from {target}.")
        else:
            try:
                self.bq_client.delete_table(target)
                print(f"{target} successfully deleted.")
            except Exception as e:
                raise Exception(f"Error deleting table {target}: {str(e)}") from e

    def save_gcs_bucket(self, bucket_name: str) -> None:
        """
        Create a new Google Cloud Storage bucket.

        Parameters
        ----------
        bucket_name: str
            Name of the bucket to create
        """
        try:
            bucket = self.gcs_client.bucket(bucket_name)
            bucket.storage_class = "STANDARD"
            bucket.create(location="eu")
            bucket.iam_configuration.public_access_prevention = "enforced"
            bucket.iam_configuration.uniform_bucket_level_access_enabled = True

            print(f"Bucket {bucket_name} created successfully.")
        except Exception as e:
            raise Exception(f"Error creating bucket {bucket_name}: {str(e)}") from e

    def load_gcs_details(self, bucket_name: str) -> list[str]:
        """
        List all files in a Google Cloud Storage bucket.

        Parameters
        ----------
        bucket_name: str
            Name of the bucket to list files from
        prefix: str, optional
            Filter results to files that begin with this prefix

        Returns
        -------
        list[str]
            List of blob names in the bucket
        """
        try:
            bucket = self.gcs_client.bucket(bucket_name)
            blobs = bucket.list_blobs()
            return [blob.name for blob in blobs]
        except Exception as e:
            raise Exception(f"Error listing bucket {bucket_name}: {str(e)}") from e

    def save_gcs_file(
        self, bucket_name: str, destination_blob_name: str, content: Any, local_path: str | None = None
    ) -> None:
        """
        Function to save content to a specific path on Google Cloud Storage.

        Parameters
        ----------
        bucket_name: str
            Name of the bucket on GCS where the file will be saved.
        destination_blob_name: str
            Path in the bucket to save the file.
        content: any
            The content to be saved.
        local_path: str, optional
            If provided, the file will be saved locally at this path.
        """
        try:
            bucket = self.gcs_client.bucket(bucket_name)
            if not bucket.exists():
                print(f"Bucket {bucket_name!r} does not exist. Creating new bucket...")
                self.save_gcs_bucket(bucket_name)

            blob = bucket.blob(destination_blob_name)

            match Path(destination_blob_name).suffix:
                case ".html":
                    content_type = "text/html"
                case ".json":
                    content_type = "application/json"
                    if not isinstance(content, str):
                        content = json.dumps(content, ensure_ascii=False, indent=2)
                case ".pkl":
                    content_type = "application/octet-stream"
                    if not isinstance(content, bytes):
                        content = pickle.dumps(content)
                case ".csv":
                    content_type = "text/csv"
                    if not isinstance(content, str):
                        try:
                            content = content.to_csv(index=False)
                        except AttributeError as e:
                            raise ValueError(
                                f"Unsupported file type. Supported types are: {self.SUPPORTED_FILE_TYPES}"
                            ) from e
                case ".sql":
                    content_type = "text/plain"
                    if not isinstance(content, str):
                        raise ValueError("SQL content must be a string")
                case _:
                    raise ValueError(f"Unknown file type. Supported types are: {self.SUPPORTED_FILE_TYPES}")

            blob.upload_from_string(content, content_type=content_type)

            if local_path:
                self.save_local_file(local_path, content)

        except Exception as e:
            raise Exception(f"Error saving file to GCS: {str(e)}") from e

    def load_gcs_file(
        self,
        bucket_name: str,
        destination_blob_name: str,
        local_path: str | None = None,
        force_csv: bool = False,
    ) -> object:
        """
        Function to read a file from a specific path on Google Cloud Storage.

        Parameters
        ----------
        bucket_name: str
            Name of bucket on GCS, where file is written.
        destination_blob_name: str
            Path in bucket to read file.
        local_path: str, optional
            If provided, the file will be saved locally at this path.
        force_csv: bool, optional
            If True, forces reading the file as CSV regardless of extension.
            Useful for DVC files without extension. Default is False.

        Returns
        ----------
        object
            The object read from the file, or None if operation is cancelled.
        """
        bucket = self.gcs_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        while not blob.exists():
            available_files = self.load_gcs_details(bucket_name)
            files_str = "\n- ".join([""] + available_files) if available_files else " (empty bucket)"
            print(f"File {destination_blob_name!r} not found in bucket {bucket_name!r}.")
            print(f"Available files:{files_str}")

            new_name = input(
                "\nPlease check the current output and enter a correct file name (or press Enter to cancel): "
            )
            if not new_name.strip():
                print("Operation cancelled.")
                return None

            destination_blob_name = new_name
            blob = bucket.blob(destination_blob_name)

        file_type = Path(destination_blob_name).suffix

        with blob.open(mode="rb") as file:
            if force_csv:
                try:
                    content = pd.read_csv(file)
                except Exception as e:
                    raise ValueError(f"Could not read file as CSV: {str(e)}") from e
            else:
                if not file_type:
                    raise ValueError(
                        f"File has no extension. Use force_csv=True to read as CSV or provide a file with extension. "
                        f"Supported types are: {self.SUPPORTED_FILE_TYPES}"
                    )

                match file_type:
                    case ".pkl":
                        content = pickle.load(file)
                    case ".json":
                        content = json.load(file)
                    case ".csv":
                        content = pd.read_csv(file)
                    case ".html":
                        content = file.read()
                    case ".sql":
                        content = file.read()
                    case _:
                        raise ValueError(
                            f"Cannot detect file type from {destination_blob_name}. "
                            f"Supported types are: {self.SUPPORTED_FILE_TYPES}"
                        )

        if local_path:
            self.save_local_file(local_path, content)

        return content

    @staticmethod
    def format_bytes(bytes_size: int) -> str:
        """
        Convert bytes to readable string.

        Parameters
        ----------
        bytes_size : int
            Size in bytes

        Returns
        -------
        str
            Formatted string with appropriate unit
        """
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(bytes_size)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.2f} {units[unit_index]}"

    @staticmethod
    def save_local_file(file_path: str, content: Any) -> None:
        """Save content to a file in various formats.

        Parameters
        ----------
        file_path : str
            The path where the file will be saved.
        content : any
            The content to save.
            Supported file types: .pkl, .json, .csv, .html, .sql
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        match Path(file_path).suffix.lower():
            case ".pkl":
                with open(file_path, "wb") as f:
                    pickle.dump(content, f)
            case ".json":
                with open(file_path, "w") as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            case ".csv":
                if not isinstance(content, pd.DataFrame):
                    try:
                        content = pd.DataFrame(content)
                    except Exception as e:
                        raise ValueError(
                            f"Unsupported file type. Supported types are: {DataOperations.SUPPORTED_FILE_TYPES}"
                        ) from e
                content.to_csv(file_path, index=False)
            case ".html" | ".sql":
                mode = "wb" if isinstance(content, bytes) else "w"
                with open(file_path, mode) as f:
                    f.write(content)
            case _:
                raise ValueError(f"Unsupported file type. Supported types are: {DataOperations.SUPPORTED_FILE_TYPES}")

    @staticmethod
    def load_local_file(file_path: str) -> Any:
        """Read a file from a local path.

        Parameters
        ----------
        file_path : str
            The path to the file to read.
            Supported file types: .pkl, .json, .csv, .html, .sql

        Returns
        -------
        any
            The content of the file in appropriate format based on file type.

        Raises
        ------
        ValueError
            If the file type is not supported.
        """
        file_type = Path(file_path).suffix.lower()

        match file_type:
            case ".pkl":
                with open(file_path, "rb") as f:
                    content = pickle.load(f)
            case ".json":
                with open(file_path, "r") as f:
                    content = json.load(f)
            case ".csv":
                content = pd.read_csv(file_path)
            case ".html" | ".sql":
                with open(file_path, "r") as f:
                    content = f.read()
            case _:
                raise ValueError(f"Unsupported file type. Supported types are: {DataOperations.SUPPORTED_FILE_TYPES}")

        return content
