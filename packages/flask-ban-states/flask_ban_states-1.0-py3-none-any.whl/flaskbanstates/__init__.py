"""Библиотека для жесткой блокировки неугодных стран во flask-приложении. Полезная утилита (наверное)!"""
import requests
import aiohttp
import flask
import json

class Banner:
    def is_banned(self):
        if len(self.results) > 200:
            self.results.clear()
        if flask.request.endpoint in self.whitelisted_endpoint:
            print(f'{flask.request.endpoint} в белом списке. Не отправляем запрос.')
            return None
        ip = flask.request.remote_addr
        info = requests.get(f'http://ip-api.com/json/{ip}', verify=False)
        if not info.json().get('countryCode'):
            print(f'Fuck! It\'s the local IP-address! Check your fucking nginx/proxy.')
        else:
            for r in self.results:
                if r["ip"] == ip:
                    if r["status"] == 'normal':
                        print(f'{ip} is normal!')
                        return None
                    else:
                        print(f'{ip} was banned by the Flask-Banner.')
                        if self.type_response == 'json':
                            if isinstance(self.return_response, str):
                                return flask.jsonify(json.loads(self.return_response)), 403
                            return flask.jsonify(self.return_response), 403
                        else:
                            return self.return_response, 403
            if info.json().get('countryCode') in self.banned_countries:
                print(f'{ip} was banned by the Flask-Banner.')
                self.results.append({"ip":ip, "status":"banned"})
                if self.type_response == 'json':
                    if isinstance(self.return_response, str):
                        return flask.jsonify(json.loads(self.return_response)), 403
                    return flask.jsonify(self.return_response), 403
                else:
                    return self.return_response, 403
            else:
                print(f'{ip} is normal!')
                self.results.append({"ip":ip, "status":"normal"})

    def __init__(self, app: flask.Flask, banned_countries: list[str] = [], return_response = {"ok":False, "error":"Forbidden 403."}, type_response: str = 'json', whitelisted_endpoint: list[str] = []):
        """Синхронный Banner.\napp: flask-app.\nbanned_countries: заблокированные коды стран.\nreturn_response: json/html код.\ntype_response: json/html.\nwhitelisted_endpoint: белый список функций (эндпоинтов), доступных в любом случае!"""
        print('BANNER WAS STARTED.')
        self.app = app
        self.banned_countries = banned_countries
        self.return_response = return_response
        self.type_response = type_response
        self.results = []
        self.whitelisted_endpoint = whitelisted_endpoint
        self.app.before_request(self.is_banned)

class AsyncBanner:
    async def is_banned(self):
        if len(self.results) > 200:
            self.results.clear()
        if flask.request.endpoint in self.whitelisted_endpoint:
            print(f'{flask.request.endpoint} в белом списке. Не отправляем запрос.')
            return None
        ip = flask.request.remote_addr
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://ip-api.com/json/{ip}') as info:
                data = await info.json()
        if not data.get('countryCode'):
            print(f'Fuck! It\'s the local IP-address! Check your fucking nginx/proxy.')
        else:
            for r in self.results:
                if r["ip"] == ip:
                    if r["status"] == 'normal':
                        print(f'{ip} is normal!')
                        return None
                    else:
                        print(f'{ip} was banned by the Flask-Banner.')
                        if self.type_response == 'json':
                            if isinstance(self.return_response, str):
                                return flask.jsonify(json.loads(self.return_response)), 403
                            return flask.jsonify(self.return_response), 403
                        else:
                            return self.return_response, 403
        if data.get('countryCode') in self.banned_countries:
            print(f'{ip} was banned by the Flask-Banner.')
            self.results.append({"ip": ip, "status": "banned"})
            if self.type_response == 'json':
                if isinstance(self.return_response, str):
                    return flask.jsonify(json.loads(self.return_response)), 403
                return flask.jsonify(self.return_response), 403
            else:
                return self.return_response, 403
        else:
            print(f'{ip} is normal!')
            self.results.append({"ip": ip, "status": "normal"})

    def __init__(self, app: flask.Flask, banned_countries: list[str] = [], return_response = {"ok": False, "error": "Forbidden 403."}, type_response: str = 'json', whitelisted_endpoint: list[str] = []):
        """Асинхронный Banner.\napp: flask-app.\nbanned_countries: заблокированные коды стран.\nreturn_response: json/html код.\ntype_response: json/html.\nwhitelisted_endpoint: белый список функций (эндпоинтов), доступных в любом случае!\n\nFLASK ДОЛЖЕН БЫТЬ ПЕРЕУСТАНОВЛЕН С `pip install flask[async]`!"""
        print('BANNER WAS STARTED.')
        self.app = app
        self.banned_countries = banned_countries
        self.return_response = return_response
        self.type_response = type_response
        self.whitelisted_endpoint = whitelisted_endpoint
        self.results = []
        self.app.before_request(self.is_banned)