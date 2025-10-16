import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.ths.company.ths_company_info_api as ths_company_info_api
import mns_common.component.cookie.cookie_info_service as cookie_info_service
import mns_common.utils.data_frame_util as data_frame_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
from datetime import datetime
from mns_common.utils.async_fun import async_fun
from loguru import logger

mongodb_util = MongodbUtil('27017')


# 同步公司控股子公司信息
@async_fun
def sync_company_hold_info(symbol):
    try:
        ths_cookie = cookie_info_service.get_ths_cookie()
        company_hold_info_df = ths_company_info_api.get_company_hold_info(symbol, ths_cookie)

        now_date = datetime.now()
        sync_str_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
        if data_frame_util.is_not_empty(company_hold_info_df):
            query = {'symbol': symbol}
            result = mongodb_util.remove_data(query, db_name_constant.COMPANY_HOLDING_INFO)
            if result.acknowledged:
                company_hold_info_df['sync_str_date'] = sync_str_date
                mongodb_util.insert_mongo(company_hold_info_df, db_name_constant.COMPANY_HOLDING_INFO)
    except BaseException as e:
        logger.error("同步公司控股子公司信息:{},{}", symbol, e)


if __name__ == '__main__':
    sync_company_hold_info('300085')
