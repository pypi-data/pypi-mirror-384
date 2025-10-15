import json
from requests.models import Response


class ApiException(Exception):
    def __init__(self, status_code=None, content=None, text=None, data=None,
                 headers=None):
        super().__init__(status_code, content, text, data, headers)
        self.status_code = status_code
        self.content = content
        self.text = text
        self.data = data
        self.headers = headers

    def __str__(self):
        klass = self.__class__.__name__.lower()
        return f'[{klass}] [{self.status_code}] {self.text}'

    def _repr_pretty_(self, p, cycle):
        """
        for ipython / jupyter
        """
        klass = self.__class__.__name__.lower()
        if self.data:
            body = json.dumps(self.data, indent=2)
        else:
            body = self.text
        st_headers = ''
        if self.headers:
            st = json.dumps(self.headers, indent=2)
            st_headers = f'[{klass}] [{self.status_code}] / headers => {st}'
        p.text(f'[{klass}] [{self.status_code}] => {body}' + st_headers)
        p.text()

    @classmethod
    def from_response(cls, response: Response):
        try:
            return cls(
                response.status_code,
                response.content,
                response.text,
                response.json(),
                response.headers,
            )
        except json.JSONDecodeError:
            return cls(
                response.status_code,
                response.content,
                response.text,
                headers=response.headers,
            )
