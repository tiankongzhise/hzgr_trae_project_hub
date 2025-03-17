from src import init_db,get_session
from src import models


class TestDateBase(object):

    def test_init_db(self):
        init_db()
        print('init_db success')

    def test_oauth_token(self):
        with get_session() as session:
            rsp = session.query(models.BdAuthTokenTable).all()
            session.commit()
        for temp in rsp:
            print(temp)
    def test_BdAdMaterialTransferTable(self):
        with get_session() as session:
            rsp = session.query(models.BdAdMaterialTransferTable).all()
            session.commit()
        for temp in rsp:
            print(temp)
    def test_BdAdCenterBindTable(self):
        with get_session() as session:
            rsp = session.query(models.BdAdCenterBindTable).all()
            session.commit()
        for temp in rsp:
            print(temp)
    def test_LeadsNoticePush(self):
        with get_session() as session:
            rsp = session.query(models.LeadsNoticePush).all()
            for temp in rsp:
                print(temp)
            session.commit()

    def test_BaiduAccoutCostRrport(self):
        with get_session() as session:
            rsp = session.query(models.BaiduAccoutCostRrport).all()
            for temp in rsp:
                print(temp)
            session.commit()


if __name__ == '__main__':
    test_item = TestDateBase()
    # test_item.test_init_db()
    # test_item.test_oauth_token()
    # test_item.test_BdAdMaterialTransferTable()
    # test_item.test_BdAdCenterBindTable()
    # test_item.test_LeadsNoticePush()
    test_item.test_BaiduAccoutCostRrport()
