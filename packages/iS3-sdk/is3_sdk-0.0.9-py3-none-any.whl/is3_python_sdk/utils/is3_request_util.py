import logging

import requests

from .logger import Logging

Logging()


class RequestUtil:
    @staticmethod
    def _request(method, url, **kwargs):
        """通用请求方法"""
        try:
            session = requests.Session()
            response = session.request(method, url, **kwargs)
            response.raise_for_status()
            logging.info(f"{method.upper()}请求成功: {response.url}")
            return response.json()
        except requests.HTTPError as http_err:
            logging.error(f"HTTP错误: {http_err}")
        except requests.ConnectionError as conn_err:
            logging.error(f"连接错误: {conn_err}")
        except requests.Timeout as timeout_err:
            logging.error(f"请求超时: {timeout_err}")
        except requests.RequestException as req_err:
            logging.error(f"请求错误: {req_err}")
        except ValueError as json_err:
            logging.error(f"JSON解析错误: {json_err}")
        return None

    @staticmethod
    def get(url, params=None, headers=None):
        return RequestUtil._request('get', url, params=params, headers=headers)

    @staticmethod
    def post(url, json=None, headers=None, data=None):
        return RequestUtil._request('post', url, json=json,  data=data,headers=headers)

    @staticmethod
    def put(url, json=None, headers=None, data=None):
        return RequestUtil._request('put', url, json=json, data=data,headers=headers)

    @staticmethod
    def delete(url, json=None, headers=None):
        return RequestUtil._request('delete', url, json=json, headers=headers)

    @staticmethod
    def post_with_file(url, headers=None, files=None, data=None):
        return RequestUtil._request('post', url, files=files,  data=data, headers=headers)

    @staticmethod
    def post_with_file_path(url, json=None, headers=None, files=None, data=None):
        return RequestUtil._request('post', url, json = json, files=files,  data=data,headers=headers)
