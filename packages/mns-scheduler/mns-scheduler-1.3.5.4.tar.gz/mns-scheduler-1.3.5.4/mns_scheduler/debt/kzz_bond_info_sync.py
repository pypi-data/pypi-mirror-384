import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.em.real_time.east_money_debt_api as east_money_debt_api
from datetime import datetime
import mns_common.constant.db_name_constant as db_name_constant
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')


# 同步可转债信息
def sync_debt_info():
    now_date = datetime.now()
    str_now_day = now_date.strftime('%Y-%m-%d')
    kzz_bond_info_df = east_money_debt_api.get_kzz_bond_info()
    kzz_bond_info_df = kzz_bond_info_df.fillna(0)
    kzz_bond_info_df['apply_date'] = kzz_bond_info_df['apply_date'].astype(str)
    kzz_bond_info_df['winning_date'] = kzz_bond_info_df['winning_date'].astype(str)
    kzz_bond_info_df['list_date'] = kzz_bond_info_df['list_date'].astype(str)
    kzz_bond_info_df['due_date'] = kzz_bond_info_df['due_date'].astype(str)
    kzz_bond_info_df = kzz_bond_info_df.loc[kzz_bond_info_df['due_date'] >= str_now_day]
    mongodb_util.remove_all_data(db_name_constant.KZZ_DEBT_INFO)
    kzz_bond_info_df['_id'] = kzz_bond_info_df['symbol']
    mongodb_util.insert_mongo(kzz_bond_info_df, db_name_constant.KZZ_DEBT_INFO)


if __name__ == '__main__':
    sync_debt_info()
