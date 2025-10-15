import json
from datetime import datetime
from typing import Any, Callable, Iterable

from airflow.hooks.base import BaseHook
from airflow.models import TaskInstance
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from elasticsearch import Elasticsearch


def chunks(lst, n) -> Iterable[list]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class ElasticsearchCustomHook(BaseHook):
    conn_name_attr = "elasticsearch_conn_id"
    default_conn_name = "elasticsearch_default"
    conn_type = "elasticsearch_custom"
    hook_name = "ElasticsearchCustom"

    def __init__(self, conn_id: str):
        super().__init__()
        self.conn_id = conn_id

    def get_conn(self) -> Any:
        conn = self.get_connection(self.conn_id)
        hosts = [f'https://{conn.host}:{conn.port}']
        api_key = conn.get_password()

        client = Elasticsearch(hosts=hosts, api_key=api_key, **conn.extra_dejson)
        return client


class ElasticsearchBulkOperator(PythonOperator):
    """Выполняет bulk, формируемый в python_callable"""

    CHUNK_SIZE = 100

    def __init__(
            self,
            conn_id: str,
            index_name: str,
            python_callable: Callable,
            *args,
            **kwargs,
    ):
        super().__init__(*args, python_callable=python_callable, **kwargs)
        self.conn_id = conn_id
        self.index_name = index_name

    def execute_callable(self):
        hook = ElasticsearchCustomHook(self.conn_id)

        with hook.get_conn() as conn:
            bulk = self.python_callable(
                *self.op_args,
                **self.op_kwargs,
            )

            if bulk:
                for chunk in chunks(bulk, self.CHUNK_SIZE * 2):
                    result = conn.bulk(index=self.index_name, body=chunk)
                    self.check_errors(result)
            else:
                print("No data")

    @staticmethod
    def check_errors(result):
        if result["errors"]:
            errors = []

            for item in result["items"]:
                operation = next(iter(item))

                error_info = item[operation].get("error")

                if error_info and error_info.get("type") != "document_missing_exception":
                    errors.append(
                        {"operation": operation, "id": item[operation]["_id"], "error": error_info}
                    )
            if errors:
                raise ValueError(f"Bulk operation failed with errors: {errors}")


class ElasticSaveOperator(ElasticsearchBulkOperator):

    def __init__(
            self,
            conn_id: str,
            xcom_key: str,
            index_name: str,
            updated_prefix=None,
            is_upsert: bool = False,
            *args,
            **kwargs,
    ):
        super().__init__(
            conn_id=conn_id,
            index_name=index_name,
            python_callable=self.create_bulk,
            *args,
            **kwargs,
        )

        self.xcom_key = xcom_key
        self.updated_prefix = updated_prefix
        self.is_upsert = is_upsert

    def create_bulk(self, ti: TaskInstance) -> list[dict]:
        bulk = []
        item_jsons = ti.xcom_pull(key=self.xcom_key, map_indexes=ti.map_index)

        for item_json in item_jsons:
            item = json.loads(item_json)
            _id = item.pop("_id")

            updated_key = (
                f"{self.updated_prefix or ''}updated_at"
            )
            item[updated_key] = datetime.now().isoformat()

            bulk.append({"update": {"_id": _id}})
            bulk.append({"doc": item, "doc_as_upsert": self.is_upsert})

        return bulk


class ElasticSaveS3Operator(ElasticsearchBulkOperator):

    def __init__(
            self,
            elastic_conn_id: str,
            s3_conn_id: str,
            index_name: str,
            updated_prefix=None,
            is_upsert: bool = False,
            xcom_key: str = None, xcom_template_key: str = None, xcom_params: dict = None,
            *args,
            **kwargs,
    ):
        super().__init__(
            conn_id=elastic_conn_id,
            index_name=index_name,
            python_callable=self.create_bulk,
            *args,
            **kwargs,
        )

        self.s3_conn_id = s3_conn_id
        self.xcom_key = xcom_key
        self.xcom_template_key = xcom_template_key
        self.xcom_params = xcom_params
        self.updated_prefix = updated_prefix
        self.is_upsert = is_upsert

    def get_data(self, ti: TaskInstance) -> dict | list[dict]:
        if self.xcom_key:
            s3_key = ti.xcom_pull(key=self.xcom_key, map_indexes=ti.map_index)
        else:
            s3_key = ti.xcom_pull(key=self.xcom_template_key, map_indexes=ti.map_index).format(**self.xcom_params)

        s3_hook = S3Hook(aws_conn_id=self.s3_conn_id)
        s3_conn = s3_hook.get_conn()

        obj = s3_conn.get_object(Bucket="airflow", Key=s3_key)
        data = obj["Body"].read().decode("utf-8")
        return json.loads(data)

    def create_bulk(self, ti: TaskInstance) -> list[dict]:
        bulk = []
        items = self.get_data(ti)

        for item in items:
            _id = item.pop("_id")

            updated_key = (
                f"{self.updated_prefix if self.updated_prefix else ''}updated_at"
            )
            item[updated_key] = datetime.now().isoformat()

            bulk.append({"update": {"_id": _id}})
            bulk.append({"doc": item, "doc_as_upsert": self.is_upsert})

        return bulk
