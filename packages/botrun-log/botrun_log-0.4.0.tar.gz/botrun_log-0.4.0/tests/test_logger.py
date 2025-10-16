import pytest
from botrun_log.log_entry import TextLogEntry, AudioLogEntry, ImageLogEntry, VectorDBLogEntry
from botrun_log.logger import Logger
from datetime import datetime
import os

def test_insert_text_log_bigquery(db_manager_bq, department):
    logger = Logger(department=department)
    log_entry = TextLogEntry(
        timestamp=datetime.now().isoformat(),
        domain_name='botrun.ai',
        user_department=department,
        user_name="user_1",
        source_ip="127.0.0.1",
        session_id="session_1",
        action_type="交談",
        developer="JcXGTcW",
        action_details="~!@#$%^&*()_+台灣No.1",
        model="gpt-4o",
        botrun="波程.botrun",
        user_agent="user_agent",
        resource_id="resource_1"
    )
    logger.insert_text_log(log_entry)
    
    # 驗證插入是否成功
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.{department}_logs` WHERE user_name = 'user_1'"
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] > 0

def test_insert_audio_log_bigquery(db_manager_bq, department):
    logger = Logger(department=department)
    log_entry = AudioLogEntry(
        timestamp=datetime.now().isoformat(),
        domain_name='botrun.ai',
        user_department=department,
        user_name="user_2",
        source_ip="127.0.0.1",
        session_id="session_2",
        action_type="上傳音檔",
        developer="JcXGTcW",
        action_details="音檔文件上傳",
        model="whisper-1",
        botrun="波程.botrun",
        user_agent="user_agent",
        resource_id="audio_1",
        file_size_mb=20
    )
    logger.insert_audio_log(log_entry)
    
    # 驗證插入是否成功
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.{department}_audio_logs` WHERE user_name = 'user_2'"
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] > 0

def test_insert_image_log_bigquery(db_manager_bq, department):
    logger = Logger(department=department)
    log_entry = ImageLogEntry(
        timestamp=datetime.now().isoformat(),
        domain_name='botrun.ai',
        user_department=department,
        user_name="user_3",
        source_ip="127.0.0.1",
        session_id="session_3",
        action_type="上傳圖片",
        developer="JcXGTcW",
        action_details="圖片文件上傳",
        model="dall-e-3",
        botrun="波程.botrun",
        user_agent="user_agent",
        resource_id="image_1",
        img_size_mb=1.5
    )
    logger.insert_image_log(log_entry)
    
    # 驗證插入是否成功
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.{department}_image_logs` WHERE user_name = 'user_3'"
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] > 0

def test_insert_vector_log_bigquery(db_manager_bq, department):
    logger = Logger(department=department)
    log_entry = VectorDBLogEntry(
        timestamp=datetime.now().isoformat(),
        domain_name='botrun.ai',
        user_department=department,
        user_name="user_4",
        source_ip="127.0.0.1",
        session_id="session_4",
        action_type="向量操作",
        developer="JcXGTcW",
        action_details="向量資料庫操作",
        model="text-embedding-ada-002",
        botrun="波程.botrun",
        user_agent="user_agent",
        resource_id="1AE5_wQsEretANgmgIFAkSVY5JUepZ767",
        page_num=10
    )
    logger.insert_vector_log(log_entry)
    
    # 驗證插入是否成功
    query = f"SELECT COUNT(*) FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.{department}_vector_logs` WHERE user_name = 'user_4'"
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] > 0

def test_insert_text_log_postgresql(db_manager_pg, department):
    logger = Logger(db_type='postgresql', pg_config={
            'dbname': os.getenv('BOTRUN_LOG_PG_DBNAME', 'botrun_db'),
            'user': os.getenv('BOTRUN_LOG_PG_USER', 'botrun_user'),
            'password': os.getenv('BOTRUN_LOG_PG_PASSWORD', 'botrun_password'),
            'host': os.getenv('BOTRUN_LOG_PG_HOST', 'localhost'),
            'port': os.getenv('BOTRUN_LOG_PG_PORT', '5432')
        }, department=department)
    log_entry = TextLogEntry(
        timestamp=datetime.now().isoformat(),
        domain_name='botrun.ai',
        user_department=department,
        user_name="user_5",
        source_ip="127.0.0.1",
        session_id="session_5",
        action_type="交談",
        developer="JcXGTcW",
        action_details="~!@#$%^&*()_+台灣No.1",
        model="gpt-4o",
        botrun="波程.botrun",
        user_agent="user_agent",
        resource_id="resource_5"
    )
    logger.insert_text_log(log_entry)
    
    # 驗證插入是否成功
    query = f"SELECT COUNT(*) FROM {department}_logs WHERE user_name = 'user_5'"
    result = db_manager_pg.execute_query(query)
    assert result[0][0] > 0

def test_insert_audio_log_postgresql(db_manager_pg, department):
    logger = Logger(db_type='postgresql', pg_config={
            'dbname': os.getenv('BOTRUN_LOG_PG_DBNAME', 'botrun_db'),
            'user': os.getenv('BOTRUN_LOG_PG_USER', 'botrun_user'),
            'password': os.getenv('BOTRUN_LOG_PG_PASSWORD', 'botrun_password'),
            'host': os.getenv('BOTRUN_LOG_PG_HOST', 'localhost'),
            'port': os.getenv('BOTRUN_LOG_PG_PORT', '5432')
        }, department=department)
    log_entry = AudioLogEntry(
        timestamp=datetime.now().isoformat(),
        domain_name='botrun.ai',
        user_department=department,
        user_name="user_6",
        source_ip="127.0.0.1",
        session_id="session_6",
        action_type="上傳音檔",
        developer="JcXGTcW",
        action_details="音檔文件上傳",
        model="whisper-1",
        botrun="波程.botrun",
        user_agent="user_agent",
        resource_id="audio_2",
        file_size_mb=20
    )
    logger.insert_audio_log(log_entry)
    
    # 驗證插入是否成功
    query = f"SELECT COUNT(*) FROM {department}_audio_logs WHERE user_name = 'user_6'"
    result = db_manager_pg.execute_query(query)
    assert result[0][0] > 0

def test_insert_image_log_postgresql(db_manager_pg, department):
    logger = Logger(db_type='postgresql', pg_config={
            'dbname': os.getenv('BOTRUN_LOG_PG_DBNAME', 'botrun_db'),
            'user': os.getenv('BOTRUN_LOG_PG_USER', 'botrun_user'),
            'password': os.getenv('BOTRUN_LOG_PG_PASSWORD', 'botrun_password'),
            'host': os.getenv('BOTRUN_LOG_PG_HOST', 'localhost'),
            'port': os.getenv('BOTRUN_LOG_PG_PORT', '5432')
        }, department=department)
    log_entry = ImageLogEntry(
        timestamp=datetime.now().isoformat(),
        domain_name='botrun.ai',
        user_department=department,
        user_name="user_7",
        source_ip="127.0.0.1",
        session_id="session_7",
        action_type="上傳圖片",
        developer="JcXGTcW",
        action_details="圖片文件上傳",
        model="dall-e-3",
        botrun="波程.botrun",
        user_agent="user_agent",
        resource_id="image_2",
        img_size_mb=1.5
    )
    logger.insert_image_log(log_entry)
    
    # 驗證插入是否成功
    query = f"SELECT COUNT(*) FROM {department}_image_logs WHERE user_name = 'user_7'"
    result = db_manager_pg.execute_query(query)
    assert result[0][0] > 0

def test_insert_vector_log_postgresql(db_manager_pg, department):
    logger = Logger(db_type='postgresql', pg_config={
            'dbname': os.getenv('BOTRUN_LOG_PG_DBNAME', 'botrun_db'),
            'user': os.getenv('BOTRUN_LOG_PG_USER', 'botrun_user'),
            'password': os.getenv('BOTRUN_LOG_PG_PASSWORD', 'botrun_password'),
            'host': os.getenv('BOTRUN_LOG_PG_HOST', 'localhost'),
            'port': os.getenv('BOTRUN_LOG_PG_PORT', '5432')
        }, department=department)
    log_entry = VectorDBLogEntry(
        timestamp=datetime.now().isoformat(),
        domain_name='botrun.ai',
        user_department=department,
        user_name="user_8",
        source_ip="127.0.0.1",
        session_id="session_8",
        action_type="向量操作",
        developer="JcXGTcW",
        action_details="向量資料庫操作",
        model="text-embedding-ada-002",
        botrun="波程.botrun",
        user_agent="user_agent",
        resource_id="1AE5_wQsEretANgmgIFAkSVY5JUepZ767",
        page_num=200
    )
    logger.insert_vector_log(log_entry)
    
    # 驗證插入是否成功
    query = f"SELECT COUNT(*) FROM {department}_vector_logs WHERE user_name = 'user_8'"
    result = db_manager_pg.execute_query(query)
    assert result[0][0] > 0

def test_invalid_db_type_logger():
    with pytest.raises(ValueError, match="Invalid db_type"):
        Logger(db_type='invalid_db_type')