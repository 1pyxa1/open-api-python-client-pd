import pandas as pd

from openapi_client import openapi
from openapi_genclient.api_client import ApiClient
from openapi_genclient.configuration import Configuration


class OpenApiPd(openapi.OpenApi):

    def __init__(self, token, brocker_id):
        self.host = 'https://api-invest.tinkoff.ru/openapi/'
        self.conf = Configuration(host=self.host)
        self.conf.access_token = token
        self.brocker_id = brocker_id
        super().__init__(ApiClient(configuration=self.conf))

    def get_currencies(self):
        """ Возвращает текущие деньги на счёту """
        res = self.portfolio.portfolio_currencies_get(broker_account_id=self.brocker_id)

        series_list = []
        for curr in res.to_dict()['payload']['currencies']:
            series_list.append(pd.Series(curr))

        return pd.DataFrame(series_list)