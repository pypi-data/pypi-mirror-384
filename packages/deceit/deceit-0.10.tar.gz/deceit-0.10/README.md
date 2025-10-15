# deceit

## introduction

boilerplate requests code for creating simple api clients.  includes
a standard requests retry adapter for retrying errors 429, 502, 503, and 504,
and a base api exceptions class that can be used for api-specific error 
handling.  includes hooks that can be used to add request and response 
logging to a database if needed for debugging / traceability.

named after a group of lapwings.  pax avium.

## usage

```python
from deceit.api_client import ApiClient
from deceit.exceptions import ApiException


class AirflowException(ApiException):
    pass

class AirflowApiClient(ApiClient):
    def __init__(self, *args, default_timeout=None, **kwargs):
        super().__init__(
            *args, base_url='http://localhost:8080/api/v1',
            default_timeout=default_timeout,
            exception_class=AirflowException,
            **kwargs)
        self.session.auth = ('username', 'password')

    def connections(self):
        return self.get('connections')
        
```

## anchoring off of base url

if you provide a `base_url` to the constructor of `ApiClient`, all 
calls to the `ApiClient.send` function will be anchored to the `base_url`.
In the `AirflowApiClient` example above, the `get` to the `connections`
endpoint will use `posixpath.join` to construct the full url, e.g.,
`http://localhost:8080/api/v1/connections`.  It is important to note 
that deceit uses `posixpath.join` not `urllib.parse.urljoin`.  
So make sure not to prefix anchored routes with `/`.

## presend and postsend

The `deceit`-ful `ApiClient` includes hooks for doing `presend` and 
`postsend` actions.  If you subclass `ApiClient` and override `presend`, 
you can perform actions such as logging the `requests.PreparedRequest` 
or adding an hmac signature.  If you subclass `ApiClient` and override
`postsend` you can add additional post-request, pre-exception handling, 
such as logging the request / response cycle.  `presend` takes 
one parameter, the `requests.PreparedRequest`, while `postsend` takes
two parameters, the `requests.PreparedRequest` and the 
`requests.models.Response`.

## timeout

You can set the default timeout to use with requests by including
the `default_timeout` parameter to the `ApiClient` constructor.

## contributing

### prerequisites

* python3.9 or python3.10
* docker-compose
* internet connection

### getting started

standard avian setup using `make`

```bash
cd /path/to/deceit
make setup
make test
```
