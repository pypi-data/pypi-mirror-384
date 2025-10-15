import os
import time
import traceback

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from google.api_core.exceptions import NotFound
import logging
import pandas as pd

logging.basicConfig(format='%(name)s - %(levelname)s -%(asctime)s- %(message)s', level=logging.INFO)


class BigQuery():
    def __init__(self, credential_json=None, scopes=None):
        if credential_json is not None:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_json

        if scopes == None:
            self.client = bigquery.Client()
        else:
            credentials = Credentials.from_service_account_info(credential_json, scopes=scopes)
            if credential_json is not None:
                self.client = bigquery.Client(credentials=credentials)
            else:
                self.client = bigquery.Client()

    def create_table(self, schema_cols_type: dict, table_id: str, partitioning_field_type: dict,
                     clustering_fields: list):

        schema = []

        for col, col_type in schema_cols_type.items():
            if col_type == "date":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.DATE)
                )
            elif col_type == "integer":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.INT64)
                )

            elif col_type == "float":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.FLOAT64)
                )

            elif col_type == "string":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.STRING)
                )
            elif col_type == "datetime":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.DATETIME)
                )

            elif col_type == "boolean":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.BOOLEAN)
                )
            elif col_type == "timestamp":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.TIMESTAMP)
                )

        table = bigquery.Table(table_id, schema=schema)
        table.clustering_fields = clustering_fields

        if partitioning_field_type and len(partitioning_field_type.keys()) == 1:
            for field, field_type in partitioning_field_type.items():
                if partitioning_field_type[field] == "month":
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.MONTH,
                        field=field
                    )
                elif partitioning_field_type[field] == "day":
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field=field
                    )
                elif partitioning_field_type[field] == "integer":
                    table.range_partitioning = bigquery.RangePartitioning(
                        field=field,
                        range_=bigquery.PartitionRange(start=0, end=1000000000, interval=100000),
                    )

        try:
            # Try to get the table
            self.client.get_table(table_id)
            print(f"Table {table_id} already exists.")
        except NotFound:
            # If table is not found, create it
            table = self.client.create_table(table)
            print(
                "Created clustered table {}.{}.{}".format(
                    table.project, table.dataset_id, table.table_id
                )
            )

    def execute_query(self, query: str):
        query_job = self.client.query(query)
        results_df = query_job.result().to_dataframe()  # Waits for job to complete.
        return results_df

    def dump_dataframe_to_bq_table(self, dataframe: pd.DataFrame, schema_cols_type: dict, table_id: str, mode: str):
        """Send a Slack message to a channel via a webhook.

        Args:
            dataframe(pandas dataframe): for dataframe to be dumped to bigquery
            schema_cols_type: {"date_start":"date", "id": "integer", "name": "string"}

            table_id (list): table_id in which dataframe need to be inserted e.g project_id.dataset.table_name = table_id
            mode(str): To append or replace the table - e.g mode = "append"  or mode="replace"
        Returns:
            returns as success message with number of inserted rows and table name
        """
        schema = []
        for col, col_type in schema_cols_type.items():
            if col_type == "date":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.DATE)
                )
            elif col_type == "integer":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.INTEGER)
                )
            elif col_type == "string":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.STRING)
                )
            elif col_type == "datetime":
                schema.append(
                    bigquery.SchemaField(col, bigquery.enums.SqlTypeNames.DATETIME)
                )

        if mode == "replace":
            write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        else:
            write_disposition = bigquery.WriteDisposition.WRITE_APPEND
        job_config = bigquery.LoadJobConfig(
            # Specify a (partial) schema. All columns are always written to the
            # table. The schema is used to assist in data type definitions.
            schema=schema,
            # Optionally, set the write disposition. BigQuery appends loaded rows
            # to an existing table by default, but with WRITE_TRUNCATE write
            # disposition it replaces the table with the loaded data.
            write_disposition=write_disposition,
        )

        if mode == "append":
            job_config.schema_update_options = [
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
            ]

        load_job = None
        retry_count = 0
        exception = None
        while load_job is None and retry_count < 5:
            try:
                load_job = self.client.load_table_from_dataframe(
                    dataframe, table_id, job_config=job_config
                )  # Make an API request.
                load_job.result()  # Wait for the job to complete.

                table = self.client.get_table(table_id)  # Make an API request.
                message = "Loaded {} rows and {} columns to {} ".format(load_job.output_rows,
                                                                        len(table.schema),
                                                                        table_id)
                logging.info(message)
                return message
            except Exception as e:
                exception = e
                retry_count += 1
                print(traceback.format_exc())
                time.sleep(5)
        raise Exception(f"BigQuery load job given exception in all the {retry_count} retries:  {exception}")

    def create_or_update_view(self, table_path, view_src):
        # Define the view configuration
        table = bigquery.Table(table_path)
        table.view_query = view_src
        try:
            existing_view = self.client.get_table(table)  # Try fetching the view
            logging.info(f"Updating existing view: {table}")
        except Exception:
            logging.info(f"Creating new view: {table}")

        # Create or update the view
        view = self.client.update_table(table, ["view_query"]) if "existing_view" in locals() else self.client.create_table(
            table)

        logging.info(f"View {table} has been created/updated successfully!")