from botrun_log.etl_manager import ETLManager
from datetime import date, timedelta

def test_write_etl_summary_bigquery(db_manager_bq, department):
    db_manager_bq.initialize_database(department)
    etl_manager = ETLManager(db_manager_bq)
    test_date = date.today()
    etl_manager.write_etl_summary(department, test_date)
    
    # Verify if the write was successful
    query = f"""
    SELECT COUNT(*) 
    FROM `{db_manager_bq.project_id}.{db_manager_bq.dataset_name}.daily_character_usage` 
    WHERE date = '{test_date}' AND department = '{department}'
    """
    result = db_manager_bq.execute_query(query)
    assert next(result)[0] > 0


def test_read_etl_summary_bigquery(db_manager_bq, department):
    etl_manager = ETLManager(db_manager_bq)
    test_date = date.today()
    results = etl_manager.read_etl_summary(test_date, test_date, department)
    assert len(list(results)) > 0

def test_write_etl_summary_postgresql(db_manager_pg, department):
    etl_manager = ETLManager(db_manager_pg)
    test_date = date.today()
    etl_manager.write_etl_summary(department, test_date)
    
    # Verify if the write was successful
    query = f"""
    SELECT COUNT(*) 
    FROM daily_character_usage 
    WHERE date = '{test_date}' AND department = '{department}'
    """
    print(query)
    result = db_manager_pg.execute_query(query)
    assert result[0][0] > 0

def test_read_etl_summary_postgresql(db_manager_pg, department):
    etl_manager = ETLManager(db_manager_pg)
    test_date = date.today()
    results = etl_manager.read_etl_summary(test_date, test_date, department)
    assert len(results) > 0
