from tkzs_bd_db_tool import get_session,init_db
from .models import JhCostNewTable,CardTable,VisitTable,SignUpTable
from ..utils import format_db_query_data,process_objects_with_conflicts

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
        
    def insert_jh_card_table(self,item_list:list):
        try:
            with get_session() as session:
                new_card_datas = process_objects_with_conflicts(session,CardTable,[CardTable(item) for item in item_list])
                new_card_dict = [item.to_dict() for item in new_card_datas]
                # session.bulk_save_objects(new_card_datas)
                session.bulk_insert_mappings(CardTable, new_card_dict)
            return True
        except Exception as e:
            print(e)
            return False
    
    def insert_jh_visit_table(self,item_list:list):
        try:
            with get_session() as session:
                new_visit_datas = process_objects_with_conflicts(session,VisitTable,[VisitTable(item) for item in item_list])
                new_visit_dict = [item.to_dict() for item in new_visit_datas]
                session.bulk_insert_mappings(VisitTable, new_visit_dict)
                # session.bulk_save_objects(new_visit_datas)
            return True
        except Exception as e:
            print(e)
            return False
    
    def insert_jh_sign_up_table(self,item_list:list):
        try:
            with get_session() as session:
                new_sign_up_datas = process_objects_with_conflicts(session,SignUpTable,[SignUpTable(item) for item in item_list])
                new_sign_up_dict = [item.to_dict() for item in new_sign_up_datas]
                session.bulk_insert_mappings(SignUpTable, new_sign_up_dict)
                # session.bulk_save_objects(new_sign_up_datas)
            return True
        except Exception as e:
            print(e)
            return False
