'''
open_api_python_client_pd
"""""""""""""""""""""""""

Модуль класса OpenApiPd, который является надстройкой для Tinkoff Invest
OpenAPI SDK для Python https://github.com/Awethon/open-api-python-client,
добавляет методы для работы с Pandas

Основной репозиторий API
https://github.com/TinkoffCreditSystems/invest-openapi/
'''

__author__ = 'syshchenko'

from datetime import date

import pandas as pd
from openapi_client import openapi
from openapi_genclient.api_client import ApiClient
from openapi_genclient.configuration import Configuration


class OpenApiPd(openapi.OpenApi):
    '''
    Класс явлется надстройкой для Tinkoff Invest OpenAPI SDK для Python,
    добавляет методы для работы с Pandas
    '''
    def __init__(self, token: str, brocker_id: int):
        self.host = 'https://api-invest.tinkoff.ru/openapi/'
        self.conf = Configuration(host=self.host)
        self.conf.access_token = token
        self.brocker_id = brocker_id
        super().__init__(ApiClient(configuration=self.conf))

    def get_currencies(self) -> pd.DataFrame:
        """ Возвращает текущие ДС на счёту """
        res = self.portfolio.portfolio_currencies_get(
            broker_account_id=self.brocker_id)

        series_list = []
        for curr in res.to_dict()['payload']['currencies']:
            series_list.append(pd.Series(curr))

        return pd.DataFrame(series_list)

    def get_operations(self, dt_from: date, dt_to: date) -> pd.DataFrame:
        '''Возвращает операции и детальную инфо и покупке в двух DataFrame'''
        res = self.operations.operations_get(
            _from=dt_from, to=dt_to, broker_account_id=self.brocker_id)

        series_list = []
        for ops in res.to_dict()['payload']['operations']:
            series_list.append(pd.Series(ops))

        dfr = pd.DataFrame(series_list)
        dfr['IX'] = dfr.index

        # разворачиваем столбец с значением комиссии в словаре в отдельные
        # столбцы удаляем trades
        operations = pd.concat(
            [dfr.drop(['commission', 'trades'], axis=1),
             dfr['commission'].apply(pd.Series).add_prefix('commission_')],
            axis=1, verify_integrity=True)

        series_list = []
        for row in list(zip(dfr['IX'], dfr['trades'])):
            if row[1]:
                for trade in row[1]:
                    ser = pd.Series(trade)
                    ser['IX'] = row[0]
                    series_list.append(ser)

        trades = pd.DataFrame(series_list)

        return operations, trades

    def get_portfolio(self):
        '''Возвращает текущее состояние портфеля'''
        # FIXME: проверить, почему не возвращает ETF
        res = self.portfolio.portfolio_get(broker_account_id=self.brocker_id)

        series_list = []
        for pos in res.to_dict()['payload']['positions']:
            series_list.append(pd.Series(pos))

        dfr = pd.DataFrame(series_list)

        positions = pd.concat(
            [dfr.drop([
                'average_position_price',
                'expected_yield',
                'average_position_price_no_nkd'
                ], axis=1),
             dfr['average_position_price'].apply(pd.Series).add_prefix('app_'),
             dfr['expected_yield'].apply(pd.Series).add_prefix('exp_yield_'),
             dfr['average_position_price_no_nkd'].apply(pd.Series).add_prefix(
                 'app_no_nkd_'), ],
            axis=1,
            verify_integrity=True)

        positions['app_total'] = positions['app_value'] * positions['balance']
        positions['app_no_nkd_total'] = positions['app_no_nkd_value'] * \
            positions['balance']
        positions['exp_yield_total'] = positions['app_total'] + \
            positions['exp_yield_value']
        positions['curr_yield'] = positions['exp_yield_total'] / \
            positions['app_total'] - 1

        return positions
