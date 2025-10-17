import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.component.proxies.proxy_common_api as proxy_common_api
from mns_common.db.MongodbUtil import MongodbUtil
from loguru import logger
import mns_common.api.em.real_time.east_money_stock_a_v2_api as east_money_stock_a_v2_api
import mns_common.api.em.real_time.east_money_debt_api as east_money_debt_api
import mns_common.api.em.real_time.east_money_etf_api as east_money_etf_api
import mns_common.api.em.real_time.east_money_stock_hk_api as east_money_stock_hk_api
import mns_common.constant.extra_income_db_name as extra_income_db_name
import mns_common.component.cookie.cookie_info_service as cookie_info_service

import mns_common.api.em.real_time.east_money_stock_us_api as east_money_stock_us_api

mongodb_util = MongodbUtil('27017')


def sync_all_em_stock_info():
    logger.info("同步东方财富a,etf,kzz,us,hk,信息开始")
    proxy_ip = proxy_common_api.generate_proxy_ip_api(5)
    proxies = {"https": proxy_ip}
    try:
        # 这里需要使用详情接口 获取全量数据
        em_a_stock_info_df = east_money_stock_a_v2_api.get_all_real_time_quotes(proxies)
        em_a_stock_info_df['_id'] = em_a_stock_info_df['symbol']
        mongodb_util.save_mongo(em_a_stock_info_df, extra_income_db_name.EM_A_STOCK_INFO)
    except BaseException as e:
        logger.error("同步东方财富A股信息异常:{}", e)
    try:
        em_etf_info = east_money_etf_api.get_etf_real_time_quotes(proxies)
        em_etf_info['_id'] = em_etf_info['symbol']
        mongodb_util.save_mongo(em_etf_info, extra_income_db_name.EM_ETF_INFO)
    except BaseException as e:
        logger.error("同步东方财富ETF信息异常:{}", e)

    try:
        em_kzz_info = east_money_debt_api.get_debt_real_time_quotes(proxies)

        em_kzz_info['_id'] = em_kzz_info['symbol']
        mongodb_util.save_mongo(em_kzz_info, extra_income_db_name.EM_KZZ_INFO)
    except BaseException as e:
        logger.error("同步东方财富可转债信息异常:{}", e)

    em_cookie = cookie_info_service.get_em_cookie()
    try:
        em_hk_stock_info = east_money_stock_hk_api.get_hk_real_time_quotes(em_cookie, proxies)
        em_hk_stock_info['_id'] = em_hk_stock_info['symbol']
        mongodb_util.save_mongo(em_hk_stock_info, extra_income_db_name.EM_HK_STOCK_INFO)
    except BaseException as e:
        logger.error("同步东方财富港股信息异常:{}", e)

    try:
        em_cookie = cookie_info_service.get_em_cookie()
        em_us_stock_info = east_money_stock_us_api.get_us_stock_real_time_quotes(em_cookie, proxies)
        em_us_stock_info['_id'] = em_us_stock_info['symbol']
        mongodb_util.save_mongo(em_us_stock_info, extra_income_db_name.EM_US_STOCK_INFO)
        em_us_etf_info = em_us_stock_info.loc[(em_us_stock_info['amount'] != 0) & (em_us_stock_info['total_mv'] == 0)]
        em_us_etf_info = em_us_etf_info.sort_values(by=['amount'], ascending=False)
        mongodb_util.save_mongo(em_us_etf_info, extra_income_db_name.EM_US_ETF_INFO)

    except BaseException as e:
        logger.error("同步东方财富美股信息异常:{}", e)
    logger.info("同步东方财富a,etf,kzz,us,hk,信息完成")


if __name__ == '__main__':
    sync_all_em_stock_info()
    # em_cookie = cookie_info_service.get_em_cookie()
    # em_us_stock_info = east_money_stock_us_api.get_us_stock_real_time_quotes(em_cookie, None)
    # em_us_stock_info['_id'] = em_us_stock_info['symbol']
    # mongodb_util.save_mongo(em_us_stock_info, db_name_constant.EM_US_STOCK_INFO)
