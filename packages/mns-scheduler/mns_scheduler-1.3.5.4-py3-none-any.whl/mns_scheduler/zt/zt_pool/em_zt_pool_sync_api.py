import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import mns_common.api.akshare.stock_zt_pool_api as stock_zt_pool_api
import mns_common.utils.date_handle_util as date_handle_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.company.company_common_service_api as company_common_service_api
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import mns_common.api.ths.zt.ths_stock_zt_pool_v2_api as ths_stock_zt_pool_v2_api
import mns_common.component.zt.zt_common_service_api as zt_common_service_api
import mns_common.component.em.em_real_time_quotes_api as em_real_time_quotes_api
from datetime import datetime
import mns_common.api.ths.company.ths_company_info_api as ths_company_info_api
import mns_common.component.cookie.cookie_info_service as cookie_info_service

'''
东方财富涨停池
'''

mongodb_util = MongodbUtil('27017')

ZT_FIELD = ['_id', 'symbol', 'name', 'now_price', 'chg', 'first_closure_time',
            'last_closure_time', 'connected_boards_numbers',
            'zt_reason', 'zt_analysis', 'closure_funds',
            # 'closure_funds_per_amount', 'closure_funds_per_flow_mv',
            'frying_plates_numbers',
            # 'statistics_detail', 'zt_type', 'market_code',
            'statistics',
            # 'zt_flag',
            'industry', 'first_sw_industry',
            'second_sw_industry',
            'third_sw_industry', 'ths_concept_name',
            'ths_concept_code', 'ths_concept_sync_day', 'em_industry',
            'mv_circulation_ratio', 'ths_concept_list_info', 'kpl_plate_name',
            'kpl_plate_list_info', 'company_type', 'diff_days', 'amount',
            'list_date',
            'exchange', 'flow_mv', 'total_mv',
            'classification', 'flow_mv_sp', 'total_mv_sp', 'flow_mv_level',
            'amount_level', 'new_stock', 'list_date_01', 'index', 'str_day', 'main_line']


def save_zt_info(str_day):
    if bool(1 - trade_date_common_service_api.is_trade_day(str_day)):
        return None

    stock_em_zt_pool_df_data = stock_zt_pool_api.stock_em_zt_pool_df(
        date_handle_util.no_slash_date(str_day))

    # fix 涨停池没有的股票
    stock_em_zt_pool_df_data = sync_miss_zt_data(stock_em_zt_pool_df_data.copy(), str_day)

    stock_em_zt_pool_df_data = common_service_fun_api.total_mv_classification(stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data = common_service_fun_api.classify_symbol(stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data = common_service_fun_api.symbol_amount_simple(stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data = company_common_service_api.amendment_industry(stock_em_zt_pool_df_data.copy())
    # 主线标记 复盘用
    stock_em_zt_pool_df_data['main_line'] = '无'
    # 上个交易交易日涨停股票
    last_trade_day_zt_df = zt_common_service_api.get_last_trade_day_zt(str_day)

    try:
        # 同花顺问财涨停池
        ths_zt_pool_df_data = ths_stock_zt_pool_v2_api.get_ths_stock_zt_reason_with_cache(str_day)

        # del stock_em_zt_pool_df_data['ths_concept_name']
        # del stock_em_zt_pool_df_data['ths_concept_code']
        for stock_one in stock_em_zt_pool_df_data.itertuples():
            try:

                # 设置连板数目
                stock_em_zt_pool_df_data = set_connected_boards_numbers(stock_em_zt_pool_df_data.copy(),
                                                                        stock_one.symbol, last_trade_day_zt_df.copy())

                ths_zt_pool_one_df = ths_zt_pool_df_data.loc[ths_zt_pool_df_data['symbol'] == stock_one.symbol]
                if data_frame_util.is_empty(ths_zt_pool_one_df):
                    stock_em_zt_pool_df_data['zt_reason'] = '0'
                    continue
                stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == stock_one.symbol, 'zt_reason'] = \
                    list(ths_zt_pool_one_df['zt_reason'])[0]

                first_closure_time = list(ths_zt_pool_one_df['first_closure_time'])[0]
                first_closure_time = first_closure_time.replace(":", "")

                stock_em_zt_pool_df_data.loc[
                    stock_em_zt_pool_df_data['symbol'] == stock_one.symbol, 'first_closure_time'] = first_closure_time

                zt_analysis = ths_company_info_api.get_company_hot_info(stock_one.symbol,
                                                                        cookie_info_service.get_ths_cookie())
                stock_em_zt_pool_df_data.loc[
                    stock_em_zt_pool_df_data['symbol'] == stock_one.symbol, 'zt_analysis'] = zt_analysis

            except BaseException as e:
                stock_em_zt_pool_df_data['zt_reason'] = '0'
                logger.error("出现异常:{}", e)
    except BaseException as e:
        stock_em_zt_pool_df_data['zt_reason'] = '0'
        logger.error("出现异常:{}", e)
    stock_em_zt_pool_df_data['first_closure_time'] = stock_em_zt_pool_df_data['first_closure_time'].str.strip()
    stock_em_zt_pool_df_data['list_date'] = stock_em_zt_pool_df_data['list_date'].apply(
        lambda x: pd.to_numeric(x, errors="coerce"))

    stock_em_zt_pool_df_data['new_stock'] = False
    # 将日期数值转换为日期时间格式
    stock_em_zt_pool_df_data['list_date_01'] = pd.to_datetime(stock_em_zt_pool_df_data['list_date'], format='%Y%m%d')
    str_day_date = date_handle_util.str_to_date(str_day, '%Y-%m-%d')
    # 计算日期差值 距离现在上市时间
    stock_em_zt_pool_df_data['diff_days'] = stock_em_zt_pool_df_data.apply(
        lambda row: (str_day_date - row['list_date_01']).days, axis=1)
    # 上市时间小于100天为新股
    stock_em_zt_pool_df_data.loc[
        stock_em_zt_pool_df_data["diff_days"] < 100, ['new_stock']] \
        = True
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data.dropna(subset=['diff_days'], axis=0, inplace=False)

    # 按照"time"列进行排序，同时将值为0的数据排到最末尾
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data.sort_values(by=['first_closure_time'])

    # 重置索引，并将排序结果保存到新的"index"列中

    stock_em_zt_pool_df_data['str_day'] = str_day
    stock_em_zt_pool_df_data['_id'] = stock_em_zt_pool_df_data['symbol'] + "_" + str_day

    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data[ZT_FIELD]

    stock_em_zt_pool_df_data.drop_duplicates('symbol', keep='last', inplace=True)

    exist_zt_pool_today = mongodb_util.find_query_data('stock_zt_pool', {'str_day': str_day})
    if data_frame_util.is_empty(exist_zt_pool_today):
        mongodb_util.save_mongo(stock_em_zt_pool_df_data, 'stock_zt_pool')
    else:
        exist_zt_pool_today_not_nan = exist_zt_pool_today.loc[exist_zt_pool_today['zt_reason'] != '0']

        stock_em_zt_pool_df_data = stock_em_zt_pool_df_data.loc[:, ~stock_em_zt_pool_df_data.columns.duplicated()]
        stock_em_zt_pool_df_data_new = stock_em_zt_pool_df_data.loc[~(
            stock_em_zt_pool_df_data['symbol'].isin(exist_zt_pool_today_not_nan['symbol']))]
        if data_frame_util.is_not_empty(stock_em_zt_pool_df_data_new):
            mongodb_util.save_mongo(stock_em_zt_pool_df_data_new, 'stock_zt_pool')
    return stock_em_zt_pool_df_data


# 设置连板数目
def set_connected_boards_numbers(stock_em_zt_pool_df_data, symbol, last_trade_day_zt_df):
    connected_boards_df_copy = last_trade_day_zt_df.loc[
        last_trade_day_zt_df['symbol'].isin(stock_em_zt_pool_df_data['symbol'])]
    connected_boards_df = connected_boards_df_copy.copy()
    connected_boards_df['connected_boards_numbers'] = connected_boards_df['connected_boards_numbers'] + 1

    connected_boards_df_one = connected_boards_df.loc[connected_boards_df['symbol'] == symbol]
    if data_frame_util.is_not_empty(connected_boards_df_one):
        stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, 'connected_boards_numbers'] = \
            list(connected_boards_df_one['connected_boards_numbers'])[0]

        stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, 'main_line'] = \
            list(connected_boards_df_one['main_line'])[0]

    return stock_em_zt_pool_df_data


def sync_miss_zt_data(stock_em_zt_pool_df_data, str_day):
    now_date = datetime.now()
    now_day = now_date.strftime('%Y-%m-%d')
    if now_day == str_day:
        real_time_quotes_all_stocks_df = em_real_time_quotes_api.get_real_time_quotes_now(None, None)
        real_time_quotes_all_stocks_df = real_time_quotes_all_stocks_df.loc[
            (real_time_quotes_all_stocks_df['wei_bi'] == 100) & (real_time_quotes_all_stocks_df['chg'] >= 9)]
        miss_zt_data_df_copy = real_time_quotes_all_stocks_df.loc[~(
            real_time_quotes_all_stocks_df['symbol'].isin(stock_em_zt_pool_df_data['symbol']))]
        miss_zt_data_df = miss_zt_data_df_copy.copy()
        if data_frame_util.is_not_empty(miss_zt_data_df):
            miss_zt_data_df['buy_1_num'] = miss_zt_data_df['buy_1_num'].astype(float)
            miss_zt_data_df['now_price'] = miss_zt_data_df['now_price'].astype(float)
            miss_zt_data_df['closure_funds'] = round(miss_zt_data_df['buy_1_num'] * 100 * miss_zt_data_df['now_price'],
                                                     2)

            company_info_industry_df = company_common_service_api.get_company_info_name()
            company_info_industry_df = company_info_industry_df.loc[
                company_info_industry_df['_id'].isin(miss_zt_data_df['symbol'])]

            company_info_industry_df = company_info_industry_df[['_id', 'industry', 'name']]

            company_info_industry_df = company_info_industry_df.set_index(['_id'], drop=True)
            miss_zt_data_df = miss_zt_data_df.set_index(['symbol'], drop=False)

            miss_zt_data_df = pd.merge(miss_zt_data_df, company_info_industry_df, how='outer',
                                       left_index=True, right_index=True)

            miss_zt_data_df = miss_zt_data_df[[
                'symbol',
                'name',
                'chg',
                'now_price',
                'amount',
                'flow_mv',
                'total_mv',
                'exchange',
                'industry',
                'closure_funds'

            ]]
            miss_zt_data_df['index'] = 10000
            miss_zt_data_df['first_closure_time'] = '150000'
            miss_zt_data_df['last_closure_time'] = '150000'
            miss_zt_data_df['statistics'] = '1/1'
            miss_zt_data_df['frying_plates_numbers'] = 0
            miss_zt_data_df['connected_boards_numbers'] = 0

            stock_em_zt_pool_df_data = pd.concat([miss_zt_data_df, stock_em_zt_pool_df_data])
        return stock_em_zt_pool_df_data
    else:
        return stock_em_zt_pool_df_data


if __name__ == '__main__':
    save_zt_info('2025-05-14')
# from datetime import datetime
#
# if __name__ == '__main__':
#
#     sync_date = date_handle_util.add_date_day('20240110', 0)
#
#     now_date = datetime.now()
#
#     str_now_day = sync_date.strftime('%Y-%m-%d')
#
#     while now_date > sync_date:
#         try:
#             save_zt_info(str_now_day)
#             sync_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(str_now_day), 1)
#             print(str_now_day)
#             str_now_day = sync_date.strftime('%Y-%m-%d')
#
#         except BaseException as e:
#             sync_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(str_now_day), 1)
#             str_now_day = sync_date.strftime('%Y-%m-%d')
