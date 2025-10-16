import os
from google.cloud import bigquery
from google.oauth2 import service_account
import psycopg2

class DatabaseManager:
    def __init__(self, db_type='bigquery', pg_config=None, credentials_path=None, project_id=None, dataset_name=None):
        self.db_type = db_type.lower()
        self.project_id = project_id or os.getenv('BOTRUN_LOG_PROJECT_ID')
        self.dataset_name = dataset_name or os.getenv('BOTRUN_LOG_DATASET_NAME')

        if self.db_type == 'bigquery':
            self.credentials_path = credentials_path or os.getenv('BOTRUN_LOG_CREDENTIALS_PATH')
            self.credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
            self._client = bigquery.Client(credentials=self.credentials, project=self.project_id)
        elif self.db_type == 'postgresql':
            if pg_config is None:
                pg_config = {
                    'host': os.getenv('PG_HOST'),
                    'database': os.getenv('PG_DATABASE'),
                    'user': os.getenv('PG_USER'),
                    'password': os.getenv('PG_PASSWORD'),
                    'port': os.getenv('PG_PORT')
                }
                if not all(pg_config.values()):
                    raise ValueError("環境變數中缺少PostgreSQL config")
            self._conn = psycopg2.connect(**pg_config)
            self._cursor = self._conn.cursor()
        else:
            raise ValueError(f"Invalid db_type '{self.db_type}'. Supported values are 'bigquery' or 'postgresql'.")

    def initialize_database(self, department):
        if self.db_type == 'bigquery':
            self._init_bq(department)
            self._init_etl_bq()
            self._init_audio_bq(department)
            self._init_image_bq(department)
            self._init_vector_bq(department)
        elif self.db_type == 'postgresql':
            self._init_pg(department)
            self._init_etl_pg()
            self._init_audio_pg(department)
            self._init_image_pg(department)
            self._init_vector_pg(department)

    def execute_query(self, query, params=None):
        if self.db_type == 'bigquery':
            job_config = bigquery.QueryJobConfig()
            if params:
                job_config.query_parameters = params
            query_job = self._client.query(query, job_config=job_config)
            return query_job.result()
        elif self.db_type == 'postgresql':
            with self._conn.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    self._conn.commit()
                    return cursor.rowcount  # 返回受影響的行數

    def insert_rows(self, table_name, rows):
        if self.db_type == 'bigquery':
            table_ref = f"{self.project_id}.{self.dataset_name}.{table_name}"
            errors = self._client.insert_rows_json(table_ref, rows)
            if errors:
                raise Exception(f"Encountered errors while inserting rows: {errors}")
        elif self.db_type == 'postgresql':
            columns = rows[0].keys()
            values = [tuple(row[column] for column in columns) for row in rows]
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
            self._cursor.executemany(query, values)
            self._conn.commit()

    def _init_bq(self, department):
        dataset_id = f"{self.project_id}.{self.dataset_name}"
        table_id = f"{dataset_id}.{department}_logs"

        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "asia-east1"
        self._client.create_dataset(dataset, exists_ok=True)

        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED", description="時間戳"),
            bigquery.SchemaField("domain_name", "STRING", mode="REQUIRED", description="波特人網域"),
            bigquery.SchemaField("user_department", "STRING", mode="REQUIRED", description="使用者部門"),
            bigquery.SchemaField("user_name", "STRING", mode="REQUIRED", description="使用者帳號"),
            bigquery.SchemaField("source_ip", "STRING", mode="REQUIRED", description="使用者的IP地址"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED", description="工作階段ID"),
            bigquery.SchemaField("action_type", "STRING", mode="REQUIRED", description="操作類型"),
            bigquery.SchemaField("action_details", "STRING", mode="NULLABLE", description="操作內容，加密"),
            bigquery.SchemaField("model", "STRING", mode="NULLABLE", description="使用的模型"),
            bigquery.SchemaField("botrun", "STRING", mode="NULLABLE", description="Botrun 資訊"),
            bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE", description="使用者的客戶端資訊"),
            bigquery.SchemaField("resource_id", "STRING", mode="NULLABLE", description="資源ID（上傳的文件等）"),
            bigquery.SchemaField("developer", "STRING", mode="REQUIRED", description="寫入log的套件或開發者"),
            bigquery.SchemaField("ch_characters", "INT64", mode="REQUIRED", description="中文字元數"),
            bigquery.SchemaField("en_characters", "INT64", mode="REQUIRED", description="英數字元數"),
            bigquery.SchemaField("total_characters", "INT64", mode="REQUIRED", description="總字元數"),
            bigquery.SchemaField("create_timestamp", "TIMESTAMP", mode="REQUIRED", description="寫入BigQuery的時間戳"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(field="timestamp")
        self._client.create_table(table, exists_ok=True)

    def _init_pg(self, department):
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {department}_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            domain_name VARCHAR(255) NOT NULL,
            user_department VARCHAR(255) NOT NULL,
            user_name VARCHAR(255) NOT NULL,
            source_ip VARCHAR(255) NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            action_type VARCHAR(255) NOT NULL,
            action_details TEXT,
            model VARCHAR(255),
            botrun VARCHAR(255),
            user_agent VARCHAR(255),
            resource_id VARCHAR(255),
            developer VARCHAR(255) NOT NULL,
            ch_characters INT NOT NULL,
            en_characters INT NOT NULL,
            total_characters INT NOT NULL,
            create_timestamp TIMESTAMP NOT NULL
        );
        """
        self._cursor.execute(create_table_query)
        self._conn.commit()

    def _init_etl_bq(self):
        table_id = f"{self.project_id}.{self.dataset_name}.daily_character_usage"
        schema = [
            bigquery.SchemaField("date", "DATE", "REQUIRED", description="日期"),
            bigquery.SchemaField("department", "STRING", "REQUIRED", description="機關"),
            bigquery.SchemaField("user_name", "STRING", "REQUIRED", description="使用者帳號"),
            bigquery.SchemaField("ch_characters", "INT64", "REQUIRED", description="中文字元數"),
            bigquery.SchemaField("en_characters", "INT64", "REQUIRED", description="英文字元數"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        self._client.create_table(table, exists_ok=True)

    def _init_etl_pg(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS daily_character_usage (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            department VARCHAR(255) NOT NULL,
            user_name VARCHAR(255) NOT NULL,
            ch_characters INT NOT NULL,
            en_characters INT NOT NULL
        );
        """
        self._cursor.execute(create_table_query)
        self._conn.commit()

    def _init_audio_bq(self, department):
        table_id = f"{self.project_id}.{self.dataset_name}.{department}_audio_logs"
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("domain_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_department", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("source_ip", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("action_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("action_details", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("model", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("botrun", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("resource_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("developer", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("file_size_mb", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("create_timestamp", "TIMESTAMP", mode="REQUIRED"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(field="timestamp")
        self._client.create_table(table, exists_ok=True)

    def _init_image_bq(self, department):
        table_id = f"{self.project_id}.{self.dataset_name}.{department}_image_logs"
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("domain_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_department", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("source_ip", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("action_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("action_details", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("model", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("botrun", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("resource_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("developer", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("img_size_mb", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("create_timestamp", "TIMESTAMP", mode="REQUIRED"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(field="timestamp")
        self._client.create_table(table, exists_ok=True)

    def _init_vector_bq(self, department):
        table_id = f"{self.project_id}.{self.dataset_name}.{department}_vector_logs"
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("domain_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_department", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("source_ip", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("action_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("action_details", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("model", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("botrun", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("resource_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("developer", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("page_num", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("create_timestamp", "TIMESTAMP", mode="REQUIRED"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(field="timestamp")
        self._client.create_table(table, exists_ok=True)

    def _init_audio_pg(self, department):
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {department}_audio_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            domain_name VARCHAR(255) NOT NULL,
            user_department VARCHAR(255) NOT NULL,
            user_name VARCHAR(255) NOT NULL,
            source_ip VARCHAR(255) NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            action_type VARCHAR(255) NOT NULL,
            action_details TEXT,
            model VARCHAR(255),
            botrun VARCHAR(255),
            user_agent VARCHAR(255),
            resource_id VARCHAR(255),
            developer VARCHAR(255) NOT NULL,
            file_size_mb FLOAT NOT NULL,
            create_timestamp TIMESTAMP NOT NULL
        );
        """
        self._cursor.execute(create_table_query)
        self._conn.commit()

    def _init_image_pg(self, department):
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {department}_image_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            domain_name VARCHAR(255) NOT NULL,
            user_department VARCHAR(255) NOT NULL,
            user_name VARCHAR(255) NOT NULL,
            source_ip VARCHAR(255) NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            action_type VARCHAR(255) NOT NULL,
            action_details TEXT,
            model VARCHAR(255),
            botrun VARCHAR(255),
            user_agent VARCHAR(255),
            resource_id VARCHAR(255),
            developer VARCHAR(255) NOT NULL,
            img_size_mb FLOAT NOT NULL,
            create_timestamp TIMESTAMP NOT NULL
        );
        """
        self._cursor.execute(create_table_query)
        self._conn.commit()

    def _init_vector_pg(self, department):
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {department}_vector_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            domain_name VARCHAR(255) NOT NULL,
            user_department VARCHAR(255) NOT NULL,
            user_name VARCHAR(255) NOT NULL,
            source_ip VARCHAR(255) NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            action_type VARCHAR(255) NOT NULL,
            action_details TEXT,
            model VARCHAR(255),
            botrun VARCHAR(255),
            user_agent VARCHAR(255),
            resource_id VARCHAR(255),
            developer VARCHAR(255) NOT NULL,
            page_num INT NOT NULL,
            create_timestamp TIMESTAMP NOT NULL
        );
        """
        self._cursor.execute(create_table_query)
        self._conn.commit()

    def close(self):
        if self.db_type == 'postgresql':
            self._cursor.close()
            self._conn.close()