import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

from datetime import datetime
import pandas as pd
from loguru import logger
import mns_common.api.ths.concept.web.ths_company_info_web as ths_company_info_web
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.concept.ths_concept_common_service_api as ths_concept_common_service_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.api.kpl.symbol.kpl_real_time_quotes_api as kpl_real_time_quotes_api
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.api.kpl.constant.kpl_constant as kpl_constant
import mns_common.component.company.company_common_service_api as company_common_service_api
import mns_common.component.k_line.common.k_line_common_service_api as k_line_common_service_api
import mns_common.constant.db_name_constant as db_name_constant
from functools import lru_cache
import mns_scheduler.company_info.base.sync_company_hold_info_api as sync_company_hold_info_api

mongodb_util = MongodbUtil('27017')
# 分页大小
MAX_PAGE_NUMBER = 2000
import threading

# 定义一个全局锁，用于保护 result 变量的访问
result_lock = threading.Lock()
# 初始化 result 变量为一个空的 Pandas DataFrame
result = []


# 计算实际流通比例
def calculate_circulation_ratio(symbol):
    query = {"symbol": symbol}
    stock_gdfx_free_top_10 = mongodb_util.descend_query(query, 'stock_gdfx_free_top_10', "period", 10)
    if stock_gdfx_free_top_10.shape[0] == 0:
        mv_circulation_ratio = 1
    else:
        # 排除香港结算公司 大于5%减持不用发公告  香港中央结算    HKSCC
        stock_gdfx_free_top_10['is_hk'] = stock_gdfx_free_top_10['shareholder_name'].apply(
            lambda shareholder_name: "HK" if shareholder_name.startswith('香港中央结算') or shareholder_name.startswith(
                'HKSCC') else "A")

        # 持股大于5%      # 排除香港结算公司 大于5%减持不用发公告  香港中央结算    HKSCC
        stock_gdfx_free_top_10 = stock_gdfx_free_top_10.loc[
            (stock_gdfx_free_top_10['circulation_ratio'] >= 5) & (stock_gdfx_free_top_10['is_hk'] == 'A')]

        circulation_ratio = sum(stock_gdfx_free_top_10['circulation_ratio'])
        mv_circulation_ratio = round((100 - circulation_ratio) / 100, 2)
        # 防止错误数据
        if mv_circulation_ratio < 0:
            mv_circulation_ratio = 1
    return mv_circulation_ratio


def get_east_money_stock_info():
    all_real_time_quotes = em_stock_info_api.get_a_stock_info()
    all_real_time_quotes = all_real_time_quotes[['symbol',
                                                 'name',
                                                 "now_price",
                                                 'total_mv',
                                                 'flow_mv',
                                                 'pe_ttm',
                                                 'sz_sh',
                                                 'area',
                                                 'pb',
                                                 'list_date',
                                                 'ROE',
                                                 'total_share',
                                                 'flow_share',
                                                 'industry',
                                                 'amount',
                                                 "hk_stock_code",
                                                 "hk_stock_name",
                                                 'concept']]

    return all_real_time_quotes


def create_index():
    mongodb_util.create_index('company_info',
                              [("classification", 1)])
    mongodb_util.create_index('company_info',
                              [("industry", 1)])
    mongodb_util.create_index('company_info',
                              [("flow_mv", 1)])
    mongodb_util.create_index('company_info',
                              [("list_date", 1)])
    mongodb_util.create_index('company_info',
                              [("symbol", 1)])


# 同步公司基本信息

def sync_company_base_info(symbol_list):
    global result
    result = []
    create_index()
    east_money_stock_info = get_east_money_stock_info()
    de_listed_stock_list = company_common_service_api.get_de_list_company()
    east_money_stock_info = east_money_stock_info.loc[~(
        east_money_stock_info['symbol'].isin(de_listed_stock_list))]
    east_money_stock_info = common_service_fun_api.exclude_ts_symbol(east_money_stock_info)
    east_money_stock_info = east_money_stock_info.loc[~((east_money_stock_info['industry'] == '-')
                                                        & (east_money_stock_info['now_price'] == 0))]

    east_money_stock_info = common_service_fun_api.total_mv_classification(east_money_stock_info)
    east_money_stock_info = common_service_fun_api.classify_symbol(east_money_stock_info)

    # 将日期数值转换为日期时间格式
    east_money_stock_info['list_date_01'] = pd.to_datetime(east_money_stock_info['list_date'], format='%Y%m%d')

    # 开盘啦实时数据
    kpl_real_time_quotes = kpl_real_time_quotes_api.get_kpl_real_time_quotes()

    if symbol_list is not None:
        east_money_stock_info = east_money_stock_info.loc[east_money_stock_info['symbol'].isin(symbol_list)]
    count = east_money_stock_info.shape[0]
    page_number = round(count / MAX_PAGE_NUMBER, 0) + 1
    page_number = int(page_number)
    threads = []

    exist_company_df = mongodb_util.find_all_data(db_name_constant.COMPANY_INFO)

    # 创建多个线程来获取数据
    for page in range(page_number):  # 0到100页
        end_count = (page + 1) * MAX_PAGE_NUMBER
        begin_count = page * MAX_PAGE_NUMBER
        page_df = east_money_stock_info.iloc[begin_count:end_count]
        thread = threading.Thread(target=single_thread_sync_company_info,
                                  args=(page_df, kpl_real_time_quotes, exist_company_df))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    fail_df = east_money_stock_info.loc[east_money_stock_info['symbol'].isin(result)]
    single_thread_sync_company_info(fail_df, kpl_real_time_quotes, exist_company_df)


def single_thread_sync_company_info(east_money_stock_info,
                                    kpl_real_time_quotes, exist_company_df):
    global result
    fail_list = []
    for company_one in east_money_stock_info.itertuples():
        try:
            # 同步公司控股子公司信息 异步执行
            sync_company_hold_info_api.sync_company_hold_info(company_one.symbol)

            company_info_type = ths_company_info_web.get_company_info_detail(company_one.symbol)
            company_info_type = set_kzz_debt(company_info_type, company_one.symbol)
            company_info_type['first_industry_code'] = company_info_type['hycode'].apply(
                lambda x: x[1:3] + '0000')
            company_info_type['second_industry_code'] = company_info_type['hy2code'].apply(
                lambda x: x[1:5] + '00')
            company_info_type['third_industry_code'] = company_info_type['hy3code'].apply(
                lambda x: x[1:7])
            # company_info_type['main_business_list'] = company_info_type['main_business_list']
            # company_info_type['most_profitable_business'] = company_info_type['most_profitable_business']
            # company_info_type['most_profitable_business_rate'] = company_info_type['most_profitable_business_rate']
            # company_info_type['most_profitable_business_profit'] = company_info_type['most_profitable_business_profit']
            #
            company_info_type['first_sw_industry'] = company_info_type['hy']
            company_info_type['second_sw_industry'] = company_info_type['hy2']
            company_info_type['third_sw_industry'] = company_info_type['hy3']
            # 保存申万行业信息
            save_sw_data(company_info_type)

            company_info_type['_id'] = company_one.symbol

            company_info_type['name'] = company_one.name

            company_info_type['em_industry'] = company_one.industry
            company_info_type['em_concept'] = company_one.concept

            company_info_type['hk_stock_code'] = company_one.hk_stock_code
            company_info_type['hk_stock_name'] = company_one.hk_stock_name

            company_info_type['now_price'] = company_one.now_price
            company_info_type['total_share'] = company_one.total_share
            company_info_type['flow_share'] = company_one.flow_share
            company_info_type['total_mv'] = company_one.total_mv
            company_info_type['flow_mv'] = company_one.flow_mv
            company_info_type['area'] = company_one.area
            company_info_type['list_date'] = company_one.list_date
            now_date = datetime.now()
            # 计算日期差值 距离现在上市时间
            company_info_type['diff_days'] = (now_date - company_one.list_date_01).days

            company_info_type['pe_ttm'] = company_one.pe_ttm
            company_info_type['pb'] = company_one.pb
            company_info_type['ROE'] = company_one.ROE
            company_info_type['flow_mv_sp'] = company_one.flow_mv_sp
            company_info_type['total_mv_sp'] = company_one.total_mv_sp
            company_info_type['flow_mv_level'] = company_one.flow_mv_level
            company_info_type['classification'] = company_one.classification
            company_info_type['mv_circulation_ratio'] = calculate_circulation_ratio(company_one.symbol)
            # 获取同花顺最新概念
            company_info_type = ths_concept_common_service_api.set_ths_concept(company_one.symbol, company_info_type)
            now_date = datetime.now()
            str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
            company_info_type['sync_date'] = str_now_date
            fix_symbol_industry_df = company_constant_data.get_fix_symbol_industry()
            if company_one.symbol in list(fix_symbol_industry_df['symbol']):
                # fix sw_industry
                company_info_type = company_constant_data.fix_symbol_industry(company_info_type, company_one.symbol)

            # todo fix industry
            company_info_type['industry'] = company_info_type['second_sw_industry']
            company_info_type['amount'] = company_one.amount

            company_info_type['kpl_plate_list_info'] = '-'
            company_info_type['kpl_plate_name'] = '-'
            company_info_type['kpl_most_relative_name'] = '-'
            now_date = datetime.now()
            str_day = now_date.strftime('%Y-%m-%d')
            deal_days = k_line_common_service_api.get_deal_days(str_day, company_one.symbol)
            company_info_type['deal_days'] = deal_days

            # 设置年报信息
            company_info_type = get_recent_year_income(company_one.symbol, company_info_type, exist_company_df)

            try:
                if data_frame_util.is_not_empty(kpl_real_time_quotes):
                    kpl_real_time_quotes_one = kpl_real_time_quotes.loc[
                        kpl_real_time_quotes['symbol'] == company_one.symbol]

                    if data_frame_util.is_not_empty(kpl_real_time_quotes_one):
                        company_info_type['kpl_plate_name'] = list(kpl_real_time_quotes_one['plate_name_list'])[0]
                        company_info_type['kpl_most_relative_name'] = \
                            list(kpl_real_time_quotes_one['most_relative_name'])[
                                0]
                    company_info_type = set_kpl_data(kpl_real_time_quotes_one, company_info_type, company_one)

                if bool(1 - ("kpl_plate_name" in company_info_type.columns)) or bool(
                        1 - ("kpl_most_relative_name" in company_info_type.columns)):
                    company_info_type['kpl_plate_name'] = ""
                    company_info_type['kpl_most_relative_name'] = ""
            except BaseException as e:
                logger.warning("设置开盘啦数据异常:{},{}", company_one.symbol, e)

            company_info_type = company_constant_data.filed_sort(company_info_type)
            mongodb_util.save_mongo(company_info_type.copy(), 'company_info_base')
            logger.info("同步公司信息完成:{}", company_one.symbol + '-' + company_one.name)
        except BaseException as e:
            fail_list.append(company_one.symbol)
            logger.error("同步公司信息发生异常:{},{}", company_one.symbol, e)
    with result_lock:
        # 使用锁来保护 result 变量的访问，将每页的数据添加到结果中
        result = fail_list


def set_kpl_data(kpl_real_time_quotes_one, company_info_type, company_one):
    if data_frame_util.is_not_empty(kpl_real_time_quotes_one):
        company_info_type['kpl_plate_name'] = list(kpl_real_time_quotes_one['plate_name_list'])[0]
        company_info_type['kpl_most_relative_name'] = list(kpl_real_time_quotes_one['most_relative_name'])[
            0]
        symbol = company_one.symbol

        query = {'symbol': symbol, "index_class": kpl_constant.FIRST_INDEX}
        kpl_best_choose_index_detail = mongodb_util.find_query_data('kpl_best_choose_index_detail', query)
        if data_frame_util.is_not_empty(kpl_best_choose_index_detail):
            kpl_best_choose_index_detail = kpl_best_choose_index_detail[[
                "plate_code",
                "plate_name",
                "first_plate_code",
                "first_plate_name",
                "index_class"
            ]]

            # 去除空格
            kpl_best_choose_index_detail['plate_name'] = kpl_best_choose_index_detail['plate_name'].str.replace(' ', '')
            # 去除空格
            kpl_best_choose_index_detail['first_plate_name'] = kpl_best_choose_index_detail[
                'first_plate_name'].str.replace(' ', '')

            company_info_type.loc[:, 'kpl_plate_list_info'] = kpl_best_choose_index_detail.to_string(index=False)
    return company_info_type


# 获取可转债信息
@lru_cache(maxsize=None)
def get_kzz_debt_info():
    query = {}
    kzz_debt_info_df = mongodb_util.find_query_data(db_name_constant.KZZ_DEBT_INFO, query)
    kzz_debt_info_df = kzz_debt_info_df[[
        'symbol',
        'name',
        'stock_code',
        'apply_date',
        'list_date',
        'due_date'
    ]]
    return kzz_debt_info_df


def set_kzz_debt(df, symbol):
    kzz_debt_info_df_all = get_kzz_debt_info()
    kzz_debt_info_df = kzz_debt_info_df_all.loc[kzz_debt_info_df_all['stock_code'] == symbol]
    df.loc[:, 'kzz_debt_list'] = ''
    if data_frame_util.is_not_empty(kzz_debt_info_df):
        kzz_debt_info_df_list = kzz_debt_info_df.to_dict(orient='records')
        df.at[0, 'kzz_debt_list'] = kzz_debt_info_df_list
    return df


# 保存申万行业分类
def save_sw_data(company_info_type):
    now_date = datetime.now()
    hour = now_date.hour
    if hour <= 15:
        return company_info_type
    first_sw_info = company_info_type[[
        'first_sw_industry',
        'first_industry_code'
    ]].copy()

    first_sw_info.loc[:, "industry_code"] = first_sw_info['first_industry_code']
    first_sw_info.loc[:, "_id"] = first_sw_info['first_industry_code']
    first_sw_info.loc[:, "second_sw_industry"] = 0
    first_sw_info.loc[:, "third_sw_industry"] = 0
    first_sw_info.loc[:, "second_industry_code"] = 0
    first_sw_info.loc[:, "third_industry_code"] = 0
    first_sw_info = first_sw_info[[
        "_id",
        "industry_code",
        'first_industry_code',
        'first_sw_industry',
        'second_industry_code',
        'second_sw_industry',
        'third_industry_code',
        'third_sw_industry'
    ]]
    mongodb_util.save_mongo(first_sw_info, 'sw_industry')

    second_sw_info = company_info_type[[
        'first_industry_code',
        'first_sw_industry',
        'second_sw_industry',
        'second_industry_code',
    ]].copy()

    second_sw_info.loc[:, "industry_code"] = second_sw_info['second_industry_code']
    second_sw_info.loc[:, "_id"] = second_sw_info['industry_code']

    second_sw_info.loc[:, "third_sw_industry"] = 0
    second_sw_info.loc[:, "third_sw_industry"] = 0
    second_sw_info.loc[:, "third_industry_code"] = 0
    second_sw_info = second_sw_info[[
        "_id",
        "industry_code",
        'first_industry_code',
        'first_sw_industry',
        'second_industry_code',
        'second_sw_industry',
        'third_industry_code',
        'third_sw_industry'
    ]]
    mongodb_util.save_mongo(second_sw_info, 'sw_industry')

    third_sw_info = company_info_type[[
        'first_industry_code',
        'first_sw_industry',
        'second_industry_code',
        'second_sw_industry',
        'third_industry_code',
        'third_sw_industry'
    ]].copy()

    third_sw_info.loc[:, "industry_code"] = third_sw_info['third_industry_code']

    third_sw_info.loc[:, "_id"] = third_sw_info['industry_code']

    third_sw_info = third_sw_info[[
        "_id",
        "industry_code",
        'first_industry_code',
        'first_sw_industry',
        'second_industry_code',
        'second_sw_industry',
        'third_industry_code',
        'third_sw_industry'
    ]]
    mongodb_util.save_mongo(third_sw_info, 'sw_industry')


# 获取最近年报收入
def get_recent_year_income(symbol, company_info_type, exist_company_df):
    now_date = datetime.now()
    hour = now_date.hour
    # if hour <= 15:
    #     exist_company_one_df = exist_company_df.loc[exist_company_df['_id'] == symbol]
    #     if data_frame_util.is_not_empty(exist_company_one_df):
    #         company_info_type['operate_profit'] = list(exist_company_one_df['operate_profit'])[0]
    #         company_info_type['total_operate_income'] = list(exist_company_one_df['total_operate_income'])[0]
    #         if 'operate_date_name' in exist_company_one_df:
    #             company_info_type['operate_date_name'] = list(exist_company_one_df['total_operate_income'])[0]
    #         else:
    #             company_info_type['operate_date_name'] = '暂无年报'
    #     else:
    #         company_info_type['operate_profit'] = 0
    #         company_info_type['total_operate_income'] = 0
    #         company_info_type['operate_date_name'] = '暂无年报'
    #     return company_info_type
    query = {'symbol': symbol, "REPORT_TYPE": "年报"}
    em_stock_profit = mongodb_util.descend_query(query, db_name_constant.EM_STOCK_PROFIT, 'REPORT_DATE', 1)
    if data_frame_util.is_not_empty(em_stock_profit):
        company_info_type['operate_profit'] = list(em_stock_profit['OPERATE_PROFIT'])[0]
        company_info_type['operate_date_name'] = list(em_stock_profit['REPORT_DATE_NAME'])[0]
        total_operate_income = list(em_stock_profit['TOTAL_OPERATE_INCOME'])[0]
        # 金融机构大多收入计入在这个字段中
        if total_operate_income == 0:
            total_operate_income = list(em_stock_profit['OPERATE_INCOME'])[0]

        company_info_type['total_operate_income'] = total_operate_income
    else:
        company_info_type['operate_profit'] = 0
        company_info_type['total_operate_income'] = 0
        company_info_type['operate_date_name'] = '暂无年报'
    company_info_type['operate_profit'] = round(
        company_info_type['operate_profit'] / common_service_fun_api.HUNDRED_MILLION, 2)
    company_info_type['total_operate_income'] = round(
        company_info_type['total_operate_income'] / common_service_fun_api.HUNDRED_MILLION, 2)
    return company_info_type


import mns_scheduler.company_info.constant.company_constant_data as company_constant_data

if __name__ == '__main__':
    # sync_company_base_info()
    # fix_company_industry()
    # calculate_circu_ratio("601069")
    # sync_company_base_info()
    # 300293
    # sync_company_base_info(None)
    # new_company_info_update()
    # query = {"total_operate_income": 0}
    # un_report_company_info = mongodb_util.find_query_data(db_name_constant.COMPANY_INFO, query)
    # symbol_list = list(un_report_company_info['symbol'])
    sync_company_base_info(None)
    # group_by_industry()
