import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
import mns_common.api.ths.zt.ths_stock_zt_pool_api as ths_stock_zt_pool_api
import mns_common.utils.data_frame_util as data_frame_util
from loguru import logger


def update_null_zt_reason(str_day):
    query = {"str_day": str_day, "$or": [{"zt_reason": "0", },
                                         {"zt_reason": ""},
                                         {"zt_reason": float('nan')}]}
    stock_zt_pool_df_null_zt_reason = mongodb_util.find_query_data('stock_zt_pool', query)
    if data_frame_util.is_empty(stock_zt_pool_df_null_zt_reason):
        return None
    no_reason_list = list(stock_zt_pool_df_null_zt_reason['symbol'])
    repeat_number = 0
    # 循环10次
    while len(no_reason_list) > 0 and repeat_number < 10:
        ths_zt_pool_df_data = ths_stock_zt_pool_api.get_zt_reason(str_day)
        for stock_zt_one in stock_zt_pool_df_null_zt_reason.itertuples():
            try:
                ths_pool_zt_reason_one_df = ths_zt_pool_df_data.loc[
                    ths_zt_pool_df_data['symbol'] == stock_zt_one.symbol]
                if data_frame_util.is_not_empty(ths_pool_zt_reason_one_df):
                    stock_zt_pool_df_one_df = stock_zt_pool_df_null_zt_reason.loc[
                        stock_zt_pool_df_null_zt_reason['symbol'] == stock_zt_one.symbol]
                    stock_zt_pool_df_one_df['zt_reason'] = list(ths_pool_zt_reason_one_df['zt_reason'])[0]
                    mongodb_util.save_mongo(stock_zt_pool_df_one_df, 'stock_zt_pool')
                    no_reason_list.remove(stock_zt_one.symbol)
            except BaseException as e:
                logger.error("出现异常:{},{}", stock_zt_one.symbol, e)
                continue
        repeat_number = repeat_number + 1

    return stock_zt_pool_df_null_zt_reason


if __name__ == '__main__':
    update_null_zt_reason('2024-12-12')
