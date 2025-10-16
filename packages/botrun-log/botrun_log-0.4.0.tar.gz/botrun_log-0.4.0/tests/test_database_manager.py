import pytest
import os
from dotenv import load_dotenv
from botrun_log.database_manager import DatabaseManager

# 加載 .env 文件
load_dotenv()

@pytest.fixture
def db_manager_bq():
    credentials_path = os.getenv('BOTRUN_LOG_CREDENTIALS_PATH')
    project_id = os.getenv('BOTRUN_LOG_PROJECT_ID')
    dataset_name = os.getenv('BOTRUN_LOG_DATASET_NAME')
    
    print(f"Credentials path: {credentials_path}")
    print(f"Project ID: {project_id}")
    print(f"Dataset name: {dataset_name}")
    
    return DatabaseManager(
        db_type='bigquery',
        credentials_path=credentials_path,
        project_id=project_id,
        dataset_name=dataset_name
    )

@pytest.fixture
def db_manager_pg():
    return DatabaseManager(
        db_type='postgresql',
        pg_config={
            'dbname': 'botrun_db',
            'user': 'botrun_user',
            'password': 'botrun_password',
            'host': 'localhost',
            'port': '5432'
        }
    )

def test_initialize_database_bq(db_manager_bq):
    print(f"Project ID: {db_manager_bq.project_id}")
    print(f"Dataset name: {db_manager_bq.dataset_name}")
    db_manager_bq.initialize_database('testdbmanager_department_1')
    # 檢查是否成功創建了資料集和表格
    query = f"""
    SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.__TABLES__` 
    WHERE table_id IN (
        'testdbmanager_department_1_logs', 
        'testdbmanager_department_1_audio_logs', 
        'testdbmanager_department_1_image_logs', 
        'testdbmanager_department_1_vector_logs', 
        'daily_character_usage'
    )
    """
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] == 5

def test_initialize_database_pg(db_manager_pg):
    db_manager_pg.initialize_database('testdbmanager_department_1')
    # 檢查是否成功創建了表格
    query = """
    SELECT COUNT(*) FROM information_schema.tables 
    WHERE table_name IN (
        'testdbmanager_department_1_logs', 
        'testdbmanager_department_1_audio_logs', 
        'testdbmanager_department_1_image_logs', 
        'testdbmanager_department_1_vector_logs', 
        'daily_character_usage'
    )
    """
    result = db_manager_pg.execute_query(query)
    assert result[0][0] == 5

def test_execute_query_bq(db_manager_bq):
    query = "SELECT 1"
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] == 1

def test_execute_query_pg(db_manager_pg):
    query = "SELECT 1"
    result = db_manager_pg.execute_query(query)
    assert result[0][0] == 1

def test_insert_rows_bq(db_manager_bq):
    db_manager_bq.initialize_database('testdbmanager_department_1')
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.testdbmanager_department_1_logs`"
    result = db_manager_bq.execute_query(query)
    count_before_insert = next(result)[0]
    rows = [
        {
            "timestamp": "2023-08-22T12:00:00Z",
            "domain_name": "test.com",
            "user_department": "testdbmanager_department_1",
            "user_name": "test_user",
            "source_ip": "127.0.0.1",
            "session_id": "test_session",
            "action_type": "test_action",
            "developer": "test_developer",
            "ch_characters": 10,
            "en_characters": 20,
            "total_characters": 30,
            "create_timestamp": "2023-08-22T12:00:00Z"
        }
    ]
    db_manager_bq.insert_rows('testdbmanager_department_1_logs', rows)
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.testdbmanager_department_1_logs`"
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] == count_before_insert+1

def test_insert_rows_pg(db_manager_pg):
    db_manager_pg.initialize_database('testdbmanager_department_1')
    query = "SELECT COUNT(*) FROM testdbmanager_department_1_logs"
    count_before_insert = db_manager_pg.execute_query(query)[0][0]
    rows = [
        {
            "timestamp": "2023-08-22T12:00:00Z",
            "domain_name": "test.com",
            "user_department": "testdbmanager_department_1",
            "user_name": "test_user",
            "source_ip": "127.0.0.1",
            "session_id": "test_session",
            "action_type": "test_action",
            "developer": "test_developer",
            "ch_characters": 10,
            "en_characters": 20,
            "total_characters": 30,
            "create_timestamp": "2023-08-22T12:00:00Z"
        }
    ]
    db_manager_pg.insert_rows('testdbmanager_department_1_logs', rows)
    query = "SELECT COUNT(*) FROM testdbmanager_department_1_logs"
    result = db_manager_pg.execute_query(query)
    assert result[0][0] == count_before_insert+1

def test_insert_audio_rows_bq(db_manager_bq):
    db_manager_bq.initialize_database('testdbmanager_department_1')
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.testdbmanager_department_1_audio_logs`"
    result = db_manager_bq.execute_query(query)
    count_before_insert = next(result)[0]
    rows = [
        {
            "timestamp": "2023-08-22T12:00:00Z",
            "domain_name": "test.com",
            "user_department": "testdbmanager_department_1",
            "user_name": "test_user",
            "source_ip": "127.0.0.1",
            "session_id": "test_session",
            "action_type": "test_action",
            "developer": "test_developer",
            "file_size_mb": 10.5,
            "create_timestamp": "2023-08-22T12:00:00Z"
        }
    ]
    db_manager_bq.insert_rows('testdbmanager_department_1_audio_logs', rows)
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.testdbmanager_department_1_audio_logs`"
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] == count_before_insert+1

def test_insert_audio_rows_pg(db_manager_pg):
    db_manager_pg.initialize_database('testdbmanager_department_1')
    query = "SELECT COUNT(*) FROM testdbmanager_department_1_audio_logs"
    count_before_insert = db_manager_pg.execute_query(query)[0][0]
    rows = [
        {
            "timestamp": "2023-08-22T12:00:00Z",
            "domain_name": "test.com",
            "user_department": "testdbmanager_department_1",
            "user_name": "test_user",
            "source_ip": "127.0.0.1",
            "session_id": "test_session",
            "action_type": "test_action",
            "developer": "test_developer",
            "file_size_mb": 10.5,
            "create_timestamp": "2023-08-22T12:00:00Z"
        }
    ]
    db_manager_pg.insert_rows('testdbmanager_department_1_audio_logs', rows)
    query = "SELECT COUNT(*) FROM testdbmanager_department_1_audio_logs"
    result = db_manager_pg.execute_query(query)
    assert result[0][0] == count_before_insert+1

def test_insert_image_rows_bq(db_manager_bq):
    db_manager_bq.initialize_database('testdbmanager_department_1')
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.testdbmanager_department_1_image_logs`"
    result = db_manager_bq.execute_query(query)
    count_before_insert = next(result)[0]
    rows = [
        {
            "timestamp": "2023-08-22T12:00:00Z",
            "domain_name": "test.com",
            "user_department": "testdbmanager_department_1",
            "user_name": "test_user",
            "source_ip": "127.0.0.1",
            "session_id": "test_session",
            "action_type": "test_action",
            "developer": "test_developer",
            "img_size_mb": 2.5,
            "create_timestamp": "2023-08-22T12:00:00Z"
        }
    ]
    db_manager_bq.insert_rows('testdbmanager_department_1_image_logs', rows)
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.testdbmanager_department_1_image_logs`"
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] == count_before_insert+1

def test_insert_image_rows_pg(db_manager_pg):
    db_manager_pg.initialize_database('testdbmanager_department_1')
    query = "SELECT COUNT(*) FROM testdbmanager_department_1_image_logs"
    count_before_insert = db_manager_pg.execute_query(query)[0][0]
    rows = [
        {
            "timestamp": "2023-08-22T12:00:00Z",
            "domain_name": "test.com",
            "user_department": "testdbmanager_department_1",
            "user_name": "test_user",
            "source_ip": "127.0.0.1",
            "session_id": "test_session",
            "action_type": "test_action",
            "developer": "test_developer",
            "img_size_mb": 2.5,
            "create_timestamp": "2023-08-22T12:00:00Z"
        }
    ]
    db_manager_pg.insert_rows('testdbmanager_department_1_image_logs', rows)
    query = "SELECT COUNT(*) FROM testdbmanager_department_1_image_logs"
    result = db_manager_pg.execute_query(query)
    assert result[0][0] == count_before_insert+1

def test_insert_vector_rows_bq(db_manager_bq):
    db_manager_bq.initialize_database('testdbmanager_department_1')
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.testdbmanager_department_1_vector_logs`"
    result = db_manager_bq.execute_query(query)
    count_before_insert = next(result)[0]
    rows = [
        {
            "timestamp": "2023-08-22T12:00:00Z",
            "domain_name": "test.com",
            "user_department": "testdbmanager_department_1",
            "user_name": "test_user",
            "source_ip": "127.0.0.1",
            "session_id": "test_session",
            "action_type": "test_action",
            "developer": "test_developer",
            "page_num": 5,
            "create_timestamp": "2023-08-22T12:00:00Z"
        }
    ]
    db_manager_bq.insert_rows('testdbmanager_department_1_vector_logs', rows)
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.testdbmanager_department_1_vector_logs`"
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] == count_before_insert+1

def test_insert_vector_rows_pg(db_manager_pg):
    db_manager_pg.initialize_database('testdbmanager_department_1')
    query = "SELECT COUNT(*) FROM testdbmanager_department_1_vector_logs"
    count_before_insert = db_manager_pg.execute_query(query)[0][0]
    rows = [
        {
            "timestamp": "2023-08-22T12:00:00Z",
            "domain_name": "test.com",
            "user_department": "testdbmanager_department_1",
            "user_name": "test_user",
            "source_ip": "127.0.0.1",
            "session_id": "test_session",
            "action_type": "test_action",
            "developer": "test_developer",
            "page_num": 5,
            "create_timestamp": "2023-08-22T12:00:00Z"
        }
    ]
    db_manager_pg.insert_rows('testdbmanager_department_1_vector_logs', rows)
    query = "SELECT COUNT(*) FROM testdbmanager_department_1_vector_logs"
    result = db_manager_pg.execute_query(query)
    assert result[0][0] == count_before_insert+1
