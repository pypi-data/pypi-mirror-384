import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.ths.concept.web.ths_company_info_web as ths_company_info_web
import mns_common.component.em.em_stock_info_api as em_stock_info_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.company.company_common_service_api as company_common_service_api
import mns_common.component.common_service_fun_api as common_service_fun_api
from loguru import logger

mongodb_util = MongodbUtil('27017')


def sync_company_remark_info():
    east_money_stock_info = em_stock_info_api.get_a_stock_info()
    de_listed_stock_list = company_common_service_api.get_de_list_company()
    east_money_stock_info = east_money_stock_info.loc[~(
        east_money_stock_info['symbol'].isin(de_listed_stock_list))]
    east_money_stock_info = common_service_fun_api.exclude_ts_symbol(east_money_stock_info)
    east_money_stock_info = east_money_stock_info.loc[~((east_money_stock_info['industry'] == '-')
                                                        & (east_money_stock_info['now_price'] == 0))]

    for stock_one in east_money_stock_info.itertuples():
        try:
            company_remark_info = ths_company_info_web.get_company_info(stock_one.symbol)
            company_remark_info['_id'] = stock_one.symbol
            company_remark_info['symbol'] = stock_one.symbol
            company_remark_info['remark'] = ''
            exist_company_remark_df = mongodb_util.find_query_data(db_name_constant.COMPANY_REMARK_INFO,
                                                                   query={"symbol": stock_one.symbol})
            if data_frame_util.is_not_empty(exist_company_remark_df):
                company_remark_info['remark'] = list(exist_company_remark_df['remark'])[0]
            mongodb_util.save_mongo(company_remark_info, db_name_constant.COMPANY_REMARK_INFO)
        except BaseException as e:

            logger.error("同步公司备注信息发生异常:{},{}", stock_one.symbol, e)


if __name__ == '__main__':
    sync_company_remark_info()
