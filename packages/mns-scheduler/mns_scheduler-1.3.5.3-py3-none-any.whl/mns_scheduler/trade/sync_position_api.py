import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.component.deal.deal_service_api as deal_service_api
import pandas as pd
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.constant.db_name_constant as db_name_constant
import datetime

from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')


# 同步持仓
def sync_position():
    now_date = datetime.datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    query_exist = {'str_day': str_day}
    if mongodb_util.exist_data_query(db_name_constant.POSITION_STOCK, query_exist):
        return None
    position_list = deal_service_api.get_position('easy_trader')
    position_df = pd.DataFrame(position_list)
    position_df = position_df.rename(columns={"明细": "detail",
                                              "序号": "index",
                                              "证券代码": "symbol",
                                              "证券名称": "name",
                                              "持仓数量": "open_position",
                                              "可用数量": "available_position",
                                              "冻结数量": "frozen_position",
                                              "参考成本价": "cost_price",
                                              "当前价": "now_price",
                                              "浮动盈亏": "floating_profit_loss",
                                              "盈亏比例(%)": "profit_loss_percent",
                                              "最新市值": "flow_mv",
                                              "当日盈亏": "today_profit_loss",
                                              "当日盈亏比(%)": "today_profit_loss_percent",
                                              "仓位占比(%)": "position_ratio",
                                              "持股天数": "holding_days",
                                              "当日买入": "day_buy",
                                              "当日卖出": "day_sell",
                                              "交易市场": "market"
                                              })
    if data_frame_util.is_not_empty(position_df):
        position_df["_id"] = position_df['symbol'] + '-' + str_day
        position_df["str_day"] = str_day
        position_df["valid"] = True
        mongodb_util.save_mongo(position_df, db_name_constant.POSITION_STOCK)


if __name__ == '__main__':
    sync_position()
