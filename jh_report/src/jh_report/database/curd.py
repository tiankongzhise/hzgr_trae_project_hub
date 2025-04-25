from tkzs_bd_db_tool import get_session,init_db
from .models import JhCostNewTable
from ..utils import format_db_query_data

class DbClient(object):
    def __init__(self):
        init_db()
        
    def query_jh_cost_new_table(self):
        with get_session() as session:
            db_data = session.query(JhCostNewTable).all()
            result = format_db_query_data(db_data)
        return result
    
    def insert_jh_cost_new_table(self,item_list:list):
        try:
            with get_session() as session:
                session.bulk_insert_mappings(JhCostNewTable, item_list)
            return True
        except Exception as e:
            print(e)
            return False
        
