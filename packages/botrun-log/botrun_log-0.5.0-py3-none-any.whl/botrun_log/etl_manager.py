import pytz
import datetime as dt

class ETLManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def write_etl_summary(self, department, date=None):
        if date is None:
            tz = pytz.timezone('Asia/Taipei')
            date = (dt.datetime.now(tz) - dt.timedelta(days=1)).date().strftime('%Y-%m-%d')
            # how to fix: Query column 1 has type STRING which cannot be inserted into column date, which has type DATE at [4:13]

        if self.db_manager.db_type == 'bigquery':
            # 刪除已存在的相同日期和機關的資料
            delete_query = f"""
            DELETE FROM `{self.db_manager.dataset_name}.daily_character_usage`
            WHERE date = '{date}' AND department = '{department}'
            """
            self.db_manager.execute_query(delete_query)

            # 執行ETL查詢並插入新的資料
            insert_query = f"""
            INSERT INTO `{self.db_manager.dataset_name}.daily_character_usage` 
            (date, department, user_name, ch_characters, en_characters)
            SELECT
                DATE('{date}') as date,
                '{department}' as department,
                user_name,
                SUM(ch_characters) as ch_characters,
                SUM(en_characters) as en_characters
            FROM `{self.db_manager.dataset_name}.{department}_logs`
            WHERE DATE(timestamp) = '{date}'
            GROUP BY user_name
            """
        else:  # PostgreSQL
            # 刪除已存在的相同日期和機關的資料
            delete_query = f"""
            DELETE FROM daily_character_usage
            WHERE date = '{date}' AND department = '{department}'
            """
            self.db_manager.execute_query(delete_query)

            # 執行ETL查詢並插入新的資料
            insert_query = f"""
            INSERT INTO daily_character_usage (date, department, user_name, ch_characters, en_characters)
            SELECT
                '{date}' as date,
                '{department}' as department,
                user_name,
                SUM(ch_characters) as ch_characters,
                SUM(en_characters) as en_characters
            FROM {department}_logs
            WHERE DATE(timestamp) = '{date}'
            GROUP BY user_name
            """
        
        self.db_manager.execute_query(insert_query)

    def read_etl_summary(self, start_date: dt.date, end_date: dt.date, department: str = None, user_name: str = None):
        if self.db_manager.db_type == 'bigquery':
            query = f"""
            SELECT
                date,
                department,
                user_name,
                ch_characters,
                en_characters
            FROM `{self.db_manager.dataset_name}.daily_character_usage`
            WHERE date BETWEEN '{start_date}' AND '{end_date}'
            """
        else:  # PostgreSQL
            query = f"""
            SELECT
                date,
                department,
                user_name,
                ch_characters,
                en_characters
            FROM daily_character_usage
            WHERE date BETWEEN '{start_date}' AND '{end_date}'
            """

        #params = []
        if department:
            query += f" AND department = '{department}'"

        if user_name:
            query += f" AND user_name = '{user_name}'"

        results = self.db_manager.execute_query(query)
        return results