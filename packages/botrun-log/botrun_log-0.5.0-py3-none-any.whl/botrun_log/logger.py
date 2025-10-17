import os
import datetime as dt
import pytz
from .crypto_manager import CryptoManager
from .log_entry import TextLogEntry, AudioLogEntry, ImageLogEntry, VectorDBLogEntry
from .etl_manager import ETLManager
from .database_manager import DatabaseManager

class Logger:
    def __init__(self, department=None, str_aes_key=None, db_type='bigquery', credentials_path=None, pg_config=None, project_id=None, dataset_name=None):
        """
        Initializes a Logger object.

        Args:
            department (str): The department name.  If not provided, it will be retrieved from the environment variable 'BOTRUN_LOG_DEPARTMENT'.
            str_aes_key (str, optional): The AES key. If not provided, it will be retrieved from the environment variable 'BOTRUN_LOG_AES_KEY'.
            db_type (str, optional): The type of database to use ('bigquery' or 'postgresql').
            credentials_path (str, optional): The path to the service account credentials file for BigQuery. 
                If not provided, it will be retrieved from the environment variable 'BOTRUN_LOG_CREDENTIALS_PATH'.
            pg_config (dict, optional): The PostgreSQL configuration dictionary (only required if db_type is 'postgresql').
            project_id (str, optional): The Google Cloud project ID. If not provided, it will be retrieved from the environment variable 'BOTRUN_LOG_PROJECT_ID'.
            dataset_name (str, optional): The BigQuery dataset name. If not provided, it will be retrieved from the environment variable 'BOTRUN_LOG_DATASET_NAME'.

        Returns:
            None

        Raises:
            ValueError: If the provided db_type is invalid.
        """
        self.department = department or os.getenv('BOTRUN_LOG_DEPARTMENT')
        str_aes_key = str_aes_key or os.getenv('BOTRUN_LOG_AES_KEY')

        self.db_manager = DatabaseManager(db_type, pg_config, credentials_path, project_id, dataset_name)
        self.db_manager.initialize_database(self.department)

        self.crypto_manager = CryptoManager(str_aes_key)
        self.etl_manager = ETLManager(self.db_manager)

    def insert_text_log(self, log_entry: TextLogEntry):
        self._insert_log(log_entry, f"{self.department}_logs")

    def insert_audio_log(self, log_entry: AudioLogEntry):
        self._insert_log(log_entry, f"{self.department}_audio_logs")

    def insert_image_log(self, log_entry: ImageLogEntry):
        self._insert_log(log_entry, f"{self.department}_image_logs")

    def insert_vector_log(self, log_entry: VectorDBLogEntry):
        self._insert_log(log_entry, f"{self.department}_vector_logs")

    def _insert_log(self, log_entry, table_name):
        log_data = log_entry.to_dict()
        log_data["create_timestamp"] = dt.datetime.now(tz=pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")
        if log_data["action_details"]:
            log_data["action_details"] = self.crypto_manager.encrypt(log_data["action_details"])

        self.db_manager.insert_rows(table_name, [log_data])

    def clear_action_details_by_session(self, session_id: str, table_suffix: str = "_logs"):
        """
        Clear action_details field for all records with specific session_id

        Args:
            session_id: The session ID to clear
            table_suffix: Table suffix (default: "_logs")

        Returns:
            Dict containing:
                - success: bool
                - affected_rows: int
                - error: Optional[str]
        """
        try:
            # Only support BigQuery for now
            if self.db_manager.db_type != 'bigquery':
                return {
                    "success": False,
                    "affected_rows": 0,
                    "error": f"Unsupported db_type: {self.db_manager.db_type}"
                }

            # Construct full table ID
            table_id = f"{self.db_manager.project_id}.{self.db_manager.dataset_name}.{self.department}{table_suffix}"

            # Build UPDATE SQL with parameterized query
            query = f"""
            UPDATE `{table_id}`
            SET action_details = ''
            WHERE session_id = @session_id
            """

            # Use parameterized query to prevent SQL injection
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
                ]
            )

            # Execute query
            query_job = self.db_manager._client.query(query, job_config=job_config)
            query_job.result()  # Wait for completion

            return {
                "success": True,
                "affected_rows": query_job.num_dml_affected_rows,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "affected_rows": 0,
                "error": str(e)
            }

    def insert_pending_session_action_details_clear(self, session_id: str, user_department: str = None):
        """
        插入待清除的 session 記錄到 pending_session_action_details_clears table

        Args:
            session_id: 要清除的 session ID
            user_department: 使用者部門（可選）

        Returns:
            Dict: {"success": bool, "error": Optional[str]}
        """
        try:
            if self.db_manager.db_type != 'bigquery':
                return {
                    "success": False,
                    "error": f"Unsupported db_type: {self.db_manager.db_type}"
                }

            table_name = f"{self.department}_pending_session_action_details_clears"

            # 先檢查是否已經存在
            table_id = f"{self.db_manager.project_id}.{self.db_manager.dataset_name}.{table_name}"
            check_query = f"""
            SELECT session_id, status
            FROM `{table_id}`
            WHERE session_id = @session_id
            """

            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
                ]
            )

            check_result = list(self.db_manager._client.query(check_query, job_config=job_config).result())

            # 如果已存在且狀態是 pending 或 processing，則不重複插入
            if check_result:
                existing_status = check_result[0].status
                if existing_status in ['pending', 'processing']:
                    return {
                        "success": True,
                        "error": None,
                        "message": f"Session {session_id} already in {existing_status} status"
                    }

            # 插入新記錄
            log_data = {
                "session_id": session_id,
                "created_at": dt.datetime.now(tz=pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S"),
                "user_department": user_department or "",
                "status": "pending",
                "retry_count": 0,
                "last_retry_at": None,
                "error_message": None,
                "completed_at": None,
            }

            self.db_manager.insert_rows(table_name, [log_data])

            return {
                "success": True,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_pending_session_action_details_clears(self, min_age_minutes: int = 180, limit: int = 100):
        """
        取得超過指定時間且狀態為 pending 的清除記錄

        Args:
            min_age_minutes: 最小存在時間（分鐘），預設 180 分鐘（3小時）
            limit: 一次最多處理幾筆，避免超時

        Returns:
            List[Dict]: 待處理的 session_id 清單
        """
        try:
            if self.db_manager.db_type != 'bigquery':
                return []

            table_id = f"{self.db_manager.project_id}.{self.db_manager.dataset_name}.{self.department}_pending_session_action_details_clears"

            query = f"""
            SELECT session_id, created_at, user_department, retry_count
            FROM `{table_id}`
            WHERE status = 'pending'
            AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, MINUTE) >= @min_age_minutes
            AND retry_count < 3
            ORDER BY created_at ASC
            LIMIT @limit
            """

            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("min_age_minutes", "INT64", min_age_minutes),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )

            results = self.db_manager._client.query(query, job_config=job_config).result()

            return [
                {
                    "session_id": row.session_id,
                    "created_at": row.created_at,
                    "user_department": row.user_department,
                    "retry_count": row.retry_count
                }
                for row in results
            ]

        except Exception as e:
            print(f"Error in get_pending_session_action_details_clears: {str(e)}")
            return []

    def execute_pending_session_action_details_clear(self, session_id: str):
        """
        執行單一 session 的 action_details 清除
        並更新 pending_session_action_details_clears 的狀態

        Args:
            session_id: 要清除的 session ID

        Returns:
            Dict: {"success": bool, "affected_rows": int, "error": Optional[str]}
        """
        try:
            # 1. 先更新狀態為 processing
            self.update_pending_session_action_details_clear_status(
                session_id=session_id,
                status="processing"
            )

            # 2. 執行清除
            result = self.clear_action_details_by_session(session_id)

            # 3. 根據結果更新最終狀態
            if result["success"]:
                self.update_pending_session_action_details_clear_status(
                    session_id=session_id,
                    status="completed",
                    error_message=None
                )
            else:
                self.update_pending_session_action_details_clear_status(
                    session_id=session_id,
                    status="failed",
                    error_message=result["error"]
                )

            return result

        except Exception as e:
            # 發生異常時標記為 failed
            self.update_pending_session_action_details_clear_status(
                session_id=session_id,
                status="failed",
                error_message=str(e)
            )

            return {
                "success": False,
                "affected_rows": 0,
                "error": str(e)
            }

    def update_pending_session_action_details_clear_status(
        self,
        session_id: str,
        status: str,
        error_message: str = None
    ):
        """
        更新 pending_session_action_details_clear 記錄的狀態

        Args:
            session_id: session ID
            status: 新狀態 ('processing', 'completed', 'failed', 'pending')
            error_message: 錯誤訊息（可選）
        """
        try:
            if self.db_manager.db_type != 'bigquery':
                return

            table_id = f"{self.db_manager.project_id}.{self.db_manager.dataset_name}.{self.department}_pending_session_action_details_clears"

            # 根據狀態決定要更新的欄位
            if status == "completed":
                query = f"""
                UPDATE `{table_id}`
                SET status = @status,
                    completed_at = CURRENT_TIMESTAMP(),
                    error_message = NULL
                WHERE session_id = @session_id
                """
            elif status == "failed":
                query = f"""
                UPDATE `{table_id}`
                SET status = 'pending',
                    retry_count = retry_count + 1,
                    last_retry_at = CURRENT_TIMESTAMP(),
                    error_message = @error_message
                WHERE session_id = @session_id
                """
            elif status == "processing":
                query = f"""
                UPDATE `{table_id}`
                SET status = @status,
                    last_retry_at = CURRENT_TIMESTAMP()
                WHERE session_id = @session_id
                """
            else:  # pending or other
                query = f"""
                UPDATE `{table_id}`
                SET status = @status
                WHERE session_id = @session_id
                """

            from google.cloud import bigquery
            query_params = [
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id),
                bigquery.ScalarQueryParameter("status", "STRING", status)
            ]

            if error_message:
                query_params.append(
                    bigquery.ScalarQueryParameter("error_message", "STRING", error_message)
                )

            job_config = bigquery.QueryJobConfig(query_parameters=query_params)

            query_job = self.db_manager._client.query(query, job_config=job_config)
            query_job.result()

        except Exception as e:
            print(f"Error updating pending clear status: {str(e)}")

    # 其他方法如 analyze, init_etl_bq, etl_summary 等保持不變