from tkzs_bd_db_tool import get_session
from tkzs_bd_db_tool import models

def get_user_name():
    with get_session() as session:
        user_name =[item[0] for item in session.query(models.BdAdCenterBindTable.user_name).all()]
    return user_name

if __name__ == '__main__':
    print(get_user_name())