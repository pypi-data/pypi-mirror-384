import pytest
from dotenv import load_dotenv
import os
from botrun_log.crypto_manager import CryptoManager
from botrun_log.database_manager import DatabaseManager

# 加載 .env 文件
load_dotenv()

@pytest.fixture
def aes_key():
    return os.getenv('BOTRUN_LOG_AES_KEY')

@pytest.fixture
def crypto_manager(aes_key):
    return CryptoManager(aes_key)

@pytest.fixture
def db_manager_bq():
    return DatabaseManager(
        db_type='bigquery',
        credentials_path=os.getenv('BOTRUN_LOG_CREDENTIALS_PATH'),
        project_id=os.getenv('BOTRUN_LOG_PROJECT_ID'),
        dataset_name=os.getenv('BOTRUN_LOG_DATASET_NAME')
    )

@pytest.fixture
def db_manager_pg():
    return DatabaseManager(
        db_type='postgresql',
        pg_config={
            'dbname': os.getenv('BOTRUN_LOG_PG_DBNAME', 'botrun_db'),
            'user': os.getenv('BOTRUN_LOG_PG_USER', 'botrun_user'),
            'password': os.getenv('BOTRUN_LOG_PG_PASSWORD', 'botrun_password'),
            'host': os.getenv('BOTRUN_LOG_PG_HOST', 'localhost'),
            'port': os.getenv('BOTRUN_LOG_PG_PORT', '5432')
        }
    )

@pytest.fixture
def department():
    return os.getenv('BOTRUN_LOG_DEPARTMENT', 'test_org')