import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
import pandas as pd
from datetime import datetime
from loguru import logger
import mns_scheduler.company_info.constant.company_constant_data as company_constant_data
import mns_common.constant.db_name_constant as db_name_constant
import mns_scheduler.concept.ths.detaill.ths_concept_detail_api as ths_concept_detail_api
import mns_scheduler.company_info.base.sync_company_base_info_api as company_info_sync_api
import mns_common.utils.data_frame_util as data_frame_util

mongodb_util = MongodbUtil('27017')
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.company.company_common_service_api as company_common_service_api


# 修改行业信息
def clean_company_info(symbol):
    if symbol is not None:
        query = {"symbol": symbol}
        company_info = mongodb_util.find_query_data('company_info_base', query)
    else:
        company_info = mongodb_util.find_all_data('company_info_base')

    company_info = company_constant_data.fix_second_industry(company_info)

    company_info = company_info.set_index(['second_sw_industry'], drop=False)

    # 修改行业名称
    del company_info['industry']
    # fix industry  name
    industry_final_fix_df = company_constant_data.get_fix_industry_name_df()
    industry_final_fix_df = industry_final_fix_df.set_index(['second_sw_industry'], drop=True)
    company_info = pd.merge(company_info, industry_final_fix_df, how='outer',
                            left_index=True, right_index=True)

    # 将申万第三行业做为行业 拆分过大的二级行业 主要有通用设备 和专业设备
    company_info = company_constant_data.fix_industry_use_sw_third(company_info.copy())
    company_info['industry'] = company_info['industry'].fillna('综合')
    company_info = company_constant_data.filed_sort(company_info)
    company_info['company_type'] = company_info['business_nature']

    # 将list_date列中的所有NaN值设置为99990909
    company_info.fillna({'list_date': 20990909.0}, inplace=True)

    # 将日期数值转换为日期时间格式
    company_info['list_date_01'] = pd.to_datetime(company_info['list_date'], format='%Y%m%d')

    company_info['list_date'] = company_info['list_date'].apply(
        lambda x: pd.to_numeric(x, errors="coerce"))

    now_date = datetime.now()

    # 计算日期差值 距离现在上市时间
    company_info['diff_days'] = company_info.apply(
        lambda row: (now_date - row['list_date_01']).days, axis=1)

    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    company_info['sync_date'] = str_now_date

    try:
        # 次新股
        sub_stock = ths_concept_detail_api.get_ths_concept_detail('885598', None)
        sub_stock_symbol_list = list(sub_stock['symbol'])
    except BaseException as e:
        logger.error("出现异常:{},{}", symbol, e)
        query = {'concept_code': 885598}
        ths_stock_concept_detail = mongodb_util.find_query_data(db_name_constant.THS_STOCK_CONCEPT_DETAIL, query)
        sub_stock_symbol_list = list(ths_stock_concept_detail['symbol'])
    company_info.loc[:, 'sub_stock'] = False
    company_info.loc[company_info['symbol'].isin(sub_stock_symbol_list), 'sub_stock'] = True

    try:
        company_info.dropna(subset=['symbol'], axis=0, inplace=True)
        company_info.dropna(subset=['_id'], axis=0, inplace=True)
        ths_stock_industry_detail_df = mongodb_util.find_all_data(db_name_constant.THS_STOCK_INDUSTRY_DETAIL)
        if data_frame_util.is_not_empty(ths_stock_industry_detail_df):
            ths_stock_industry_detail_df = ths_stock_industry_detail_df[
                ['symbol', 'ths_industry_name', 'ths_industry_code']]
            ths_stock_industry_detail_df = ths_stock_industry_detail_df.set_index(['symbol'], drop=True)
            company_info = company_info.set_index(['_id'], drop=False)
            company_info = pd.merge(company_info, ths_stock_industry_detail_df, how='outer',
                                    left_index=True, right_index=True)
            company_info['ths_industry_code'] = company_info['ths_industry_code'].fillna('0')
            company_info['ths_industry_name'] = company_info['ths_industry_name'].fillna('异常')

        else:
            company_info['ths_industry_code'] = '0'
            company_info['ths_industry_name'] = '异常'
        mongodb_util.save_mongo(company_info, db_name_constant.COMPANY_INFO)
        # 保存历史数据
        save_company_info_his(company_info)
    except BaseException as e:
        logger.error("出现异常:{},{}", symbol, e)

    return company_info


def save_company_info_his(company_info_df):
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    company_info_df['symbol'] = company_info_df['_id']
    company_info_df['str_day'] = str_day
    company_info_df['_id'] = company_info_df['_id'] + "_" + str_day
    remove_query = {'str_day': str_day}
    tag = mongodb_util.remove_data(remove_query, db_name_constant.COMPANY_INFO_HIS)
    success = tag.acknowledged
    if success:
        mongodb_util.save_mongo(company_info_df, db_name_constant.COMPANY_INFO_HIS)


# 更新新上市公司信息
def new_company_info_update():
    east_money_stock_info = company_info_sync_api.get_east_money_stock_info()
    new_stock = common_service_fun_api.get_new_stock(east_money_stock_info.copy())
    for company_one in new_stock.itertuples():
        try:
            company_info_sync_api.sync_company_base_info([company_one.symbol])
            clean_company_info(company_one.symbol)

        except BaseException as e:
            logger.error("出现异常:{}", e)
    company_common_service_api.company_info_industry_cache_clear


if __name__ == '__main__':
    clean_company_info(None)
