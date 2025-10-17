from davidkhala.utils.http_request import Request, default_on_response


class API(Request):
    def __init__(self, key: str):
        super().__init__()
        self.key = key

        def on_response(response):
            r = default_on_response(response)
            if r['status'] != '1':
                raise r
            else:
                return r

        self.on_response = on_response

    def request(self, url, method: str, params=None, data=None, json=None) -> dict:
        if params is None:
            params = {}
        params['key'] = self.key
        return super().request(url, method, params, data, json)

    def tips(self, address: str):
        params = {
            'keywords': address
        }
        r = self.request('https://restapi.amap.com/v3/assistant/inputtips', 'GET', params)

        def _fn(tip: dict):
            l: str = tip.pop('location')
            lng, lat = map(float, l.split(','))
            tip['longitude'] = lng
            tip['latitude'] = lat
            return tip

        return [_fn(tip) for tip in r['tips']]

