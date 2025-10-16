# botrun-log

**botrun-log** 是一個用於將操作記錄儲存到 Google BigQuery 和 PostgreSQL 的 Python 套件，並提供 ETL 操作功能。此套件適用於記錄使用者行為，並能進行資料的分析和統計。

## 特色

- 支援 Google BigQuery 與 PostgreSQL 資料庫
- 針對機關和使用者的每日字元使用量進行 ETL 操作
- ~~支援加密操作細節，並使用 Google KMS 進行密鑰管理~~ 待開發
- 支援多種操作類型的記錄和字元統計


## 安裝

### 使用 pip 安裝

```bash
pip install botrun-log
```

### 安裝開發環境需求

如果你想進行套件的開發或測試，可以使用以下命令安裝額外的開發需求：

```bash
pip install -e .[dev]
```

## 環境變數設定與使用方式

botrun-log 支援從環境變數或直接通過參數設置config。環境變數會在初始化 Logger 時自動讀取。如果同時設置了環境變數和輸入參數，參數的優先級更高。

### 環境變數

對於 BigQuery：

- BOTRUN_LOG_CREDENTIALS_PATH: service account 憑證檔案的路徑
- BOTRUN_LOG_PROJECT_ID: Google Cloud 專案 ID
- BOTRUN_LOG_DATASET_NAME: BigQuery 資料集名稱

對於 PostgreSQL：

- BOTRUN_LOG_PG_DBNAME: PostgreSQL DB 名稱
- BOTRUN_LOG_PG_USER: PostgreSQL DB username
- BOTRUN_LOG_PG_PASSWORD: PostgreSQL DB password
- BOTRUN_LOG_PG_HOST: PostgreSQL DB主機 IP
- BOTRUN_LOG_PG_PORT: PostgreSQL DB主機 port

共通的環境變數：

- BOTRUN_LOG_DEPARTMENT: 部門名稱，用於建立資料表和進行資料分析

### 初始化 Logger

botrun-log 支援兩種資料庫：Google BigQuery 和 PostgreSQL。以下是兩種資料庫的初始化方式：

#### 使用 Google BigQuery

```python
from botrun_log import Logger

# 使用環境變數
logger_bq = Logger(db_type='bigquery', department='your_department')

# 或者直接提供參數
logger_bq = Logger(
    db_type='bigquery',
    department='your_department',
    credentials_path='/path/to/your/credentials.json',
    project_id='your_project_id',
    dataset_name='your_dataset_name'
)
```

#### 使用 PostgreSQL

```python
from botrun_log import Logger

# 使用環境變數
logger_pg = Logger(db_type='postgresql', department='your_department')

# 或者直接提供參數
logger_pg = Logger(
    db_type='postgresql',
    department='your_department',
    pg_config={
        'dbname': 'botrun_db',
        'user': 'botrun_user',
        'password': 'botrun_password',
        'host': 'localhost',
        'port': '5432'
    }
)
```

在這兩種初始化方式中，你可以選擇使用環境變數或直接提供參數。使用環境變數時，請確保你已經正確設置了相應的環境變數。直接提供參數時，你需要填寫所有必要的配置信息。

初始化完成後，你就可以使用 `logger` 對象來插入各種類型的日誌記錄了。

### 插入記錄

botrun-log 支援四種類型的記錄：文字、音訊、圖片和向量資料庫操作。以下是各種記錄的插入方式：

#### 文字記錄

```python
from botrun_log import TextLogEntry
from datetime import datetime

text_log = TextLogEntry(
    timestamp=datetime.now().isoformat(),
    domain_name='botrun.ai',
    user_department='your_department',
    user_name='user_1',
    source_ip='127.0.0.1',
    session_id='session_1',
    action_type='交談',
    developer='JcXGTcW',
    action_details='使用者輸入的文字',
    model='gpt-4o',
    botrun='波程.botrun',
    user_agent='user_agent',
    resource_id='resource_1'
)

logger.insert_text_log(text_log)
```

#### 音訊記錄

```python
from botrun_log import AudioLogEntry

audio_log = AudioLogEntry(
    timestamp=datetime.now().isoformat(),
    domain_name='botrun.ai',
    user_department='your_department',
    user_name='user_2',
    source_ip='127.0.0.1',
    session_id='session_2',
    action_type='上傳音檔',
    developer='JcXGTcW',
    action_details='音檔文件上傳',
    model='whisper-1',
    botrun='波程.botrun',
    user_agent='user_agent',
    resource_id='audio_1',
    file_size_mb=20
)

logger.insert_audio_log(audio_log)
```

#### 圖片記錄

```python
from botrun_log import ImageLogEntry

image_log = ImageLogEntry(
    timestamp=datetime.now().isoformat(),
    domain_name='botrun.ai',
    user_department='your_department',
    user_name='user_3',
    source_ip='127.0.0.1',
    session_id='session_3',
    action_type='上傳圖片',
    developer='JcXGTcW',
    action_details='圖片文件上傳',
    model='dall-e-3',
    botrun='波程.botrun',
    user_agent='user_agent',
    resource_id='image_1',
    img_size_mb=1.5
)

logger.insert_image_log(image_log)
```

#### 向量資料庫操作記錄

```python
from botrun_log import VectorDBLogEntry

vector_log = VectorDBLogEntry(
    timestamp=datetime.now().isoformat(),
    domain_name='botrun.ai',
    user_department='your_department',
    user_name='user_4',
    source_ip='127.0.0.1',
    session_id='session_4',
    action_type='向量操作',
    developer='JcXGTcW',
    action_details='向量資料庫操作',
    model='text-embedding-ada-002',
    botrun='波程.botrun',
    user_agent='user_agent',
    resource_id='1AE5_wQsEretANgmgIFAkSVY5JUepZ767',
    page_num=10
)

logger.insert_vector_log(vector_log)
```

### 執行 ETL 操作

```python
from botrun_log import ETLManager
from datetime import date

etl_manager = ETLManager(db_manager)
etl_manager.write_etl_summary(department='your_department', date=date(2023, 8, 22))
```

### 讀取 ETL 結果

```python
results = etl_manager.read_etl_summary(
    start_date=date(2023, 8, 1),
    end_date=date(2023, 8, 31),
    department='your_department'
)

for result in results:
    print(result)
```

## 資料表欄位說明

### 文字記錄表 ({department}_logs)

- `timestamp`: 操作的時間戳 (TIMESTAMP)
- `domain_name`: 操作所屬的網域名稱 (STRING)
- `user_department`: 使用者所屬的部門或機關 (STRING)
- `user_name`: 使用者的名稱或帳號 (STRING)
- `source_ip`: 發出操作請求的 IP 地址 (STRING)
- `session_id`: 當前操作的工作階段 ID (STRING)
- `action_type`: 操作類型 (STRING)
- `developer`: 記錄這次操作的開發者名稱或寫入記錄的套件名稱 (STRING)
- `action_details`: 操作的具體內容 (STRING)
- `model`: 使用的模型名稱 (STRING)
- `botrun`: 使用的 botrun 版本 (STRING)
- `user_agent`: 使用者的客戶端資訊 (STRING)
- `resource_id`: 與此次操作相關的資源 ID (STRING)
- `ch_characters`: 中文字元數量 (INTEGER)
- `en_characters`: 英文字元數量 (INTEGER)
- `total_characters`: 總字元數量 (INTEGER)
- `create_timestamp`: 記錄創建時間 (TIMESTAMP)

### 音訊記錄表 ({department}_audio_logs)

包含與文字記錄表相同的欄位，另外增加：

- `file_size_mb`: 音訊檔案大小 (FLOAT)

### 圖片記錄表 ({department}_image_logs)

包含與文字記錄表相同的欄位，另外增加：

- `img_size_mb`: 圖片檔案大小 (FLOAT)

### 向量資料庫操作記錄表 ({department}_vector_logs)

包含與文字記錄表相同的欄位，另外增加：

- `page_num`: 操作的頁數 (INTEGER)

### ETL 摘要表 (daily_character_usage)

- `date`: 日期 (DATE)
- `department`: 部門或機關 (STRING)
- `user_name`: 使用者名稱 (STRING)
- `ch_characters`: 中文字元使用量 (INTEGER)
- `en_characters`: 英文字元使用量 (INTEGER)

## 欄位必填與選填說明

### 必填欄位

- `timestamp`: 操作的時間戳
- `domain_name`: 操作所屬的網域名稱
- `user_department`: 使用者所屬的部門或機關
- `user_name`: 使用者的名稱或帳號
- `source_ip`: 發出操作請求的 IP 地址
- `session_id`: 當前操作的工作階段 ID
- `action_type`: 操作類型
- `developer`: 記錄這次操作的開發者名稱或寫入記錄的套件名稱
- `model`: 使用的模型名稱
- `botrun`: 使用的 botrun 版本

### 選填欄位

- `action_details`: 操作的具體內容
- `user_agent`: 使用者的客戶端資訊
- `resource_id`: 與此次操作相關的資源 ID

對於特定類型的記錄，還有以下必填欄位：

- 音訊記錄：`file_size_mb`
- 圖片記錄：`img_size_mb`
- 向量資料庫操作記錄：`page_num`

## 測試

套件使用 `pytest` 進行單元測試。你可以在專案根目錄執行以下命令來跑測試：

```bash
pytest
```

## 貢獻

歡迎貢獻！如有問題或建議，請透過 [issues](https://github.com/bohachu/bigquery_log_jc/issues) 頁面與我們聯繫。

## 授權

此專案採用 [MIT License](https://opensource.org/licenses/MIT) 授權。