import abc
import base64
import time
import urllib.parse
import collections
import weakref
from ..Scaffolding import ResourceManager
import hashlib
import zipfile
import os

__all__ = [
    "WebRequestHandler",
    "WebAPIConnection",
    "WebSubAPIConnection",
    "WebResourceManager",
    "GitHubReleaseManager",
    "ReleaseZIPManager"
]

class WebAPIError(IOError):
    ...

class WebRequestHandler:

    @classmethod
    def resolve_handler(cls, handler):
        if isinstance(handler, str):
            if handler == 'requests':
                import requests
                handler = cls.requests_request
            elif handler == 'urllib3':
                handler = cls.urllib3_request
            elif handler == 'default':
                handler = cls.default_request
            else:
                raise ValueError(f"don't know what to do with handler '{handler}'")
        return handler

    @classmethod
    def request(cls, method, url, json=None, handler=None, **params):
        response = None
        if json is not None and len(json) == 0:
            json = None
        if handler is not None:
            response = cls.resolve_handler(handler)(method, url, json=json, **params)
        else:
            try:
                response = cls.requests_request(method, url, json=json, **params)
            except ImportError:
                ...
            else:
                handler = 'requests'

            if response is None:
                try:
                    response = cls.urllib3_request(method, url, json=json, **params)
                except:
                    ...
                else:
                    handler = 'urllib3'

            if response is None:
                response = cls.default_request(method, url, json=json, **params)
                handler = 'default'

        return response, handler

    @classmethod
    def requests_request(cls, method, url, **params):
        import requests

        return requests.request(method, url, **params)

    @classmethod
    def urllib3_request(cls, method, url, **params):
        import urllib3

        return urllib3.request(method, url, **params)

    @classmethod
    def default_request(cls, method, url, data=None, headers=None, origin_req_host=None, unverifiable=False,
                        json=None, **params):
        import urllib.request, json as jsdump

        if json is not None:
            if data is None:
                data = jsdump.dumps(json).encode('utf-8')
            else:
                raise ValueError("can't get 'data' and 'json' arguments")


        return urllib.request.urlopen(
            urllib.request.Request(url,
                                   method=method,
                                   data=data,
                                   headers=headers,
                                   unverifiable=unverifiable,
                                   origin_req_host=origin_req_host
                                   ),
            **params
        )

    @classmethod
    def handle_response(cls, resp, headers):
        response, request_handler = resp
        if request_handler == 'requests':
            import requests
            response = response #type: requests.Request
            if response.status_code < 300:
                return response.json()
            else:
                raise WebAPIError(response.status_code, response.text, f"({response.url})")
        elif request_handler == 'urllib3':
            if response.status_code < 300:
                return response.json()
            else:
                raise WebAPIError(response.status_code, response.text, f"({response.url})")
        else:
            import json
            data = response.read()
            encoding = response.info().get_content_charset('utf-8')
            txt = data.decode(encoding)
            if response.status_code < 300:
                return json.loads(txt)
            else:
                raise WebAPIError(response.status_code, txt, f"({response.url})")

    @classmethod
    def read_response(cls, resp, decode=True):
        response, request_handler = resp
        if request_handler == 'requests':
            import requests
            response = response  # type: requests.Request
            if response.status_code < 300:
                if decode:
                    return response.text
                else:
                    return response.content
            else:
                raise WebAPIError(response.status_code, response.text, f"({response.url})")
        elif request_handler == 'urllib3':
            if response.status_code < 300:
                if decode:
                    return response.text
                else:
                    return response.content
            else:
                raise WebAPIError(response.status_code, response.text, f"({response.url})")
        else:
            data = response.read()
            if response.status_code < 300:
                if decode:
                    encoding = response.info().get_content_charset('utf-8')
                    return data.decode(encoding)
                else:
                    return data
            else:
                encoding = response.info().get_content_charset('utf-8')
                txt = data.decode(encoding)
                raise WebAPIError(response.status_code, txt, f"({response.url})")

class APIAuthentication(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def prep_request(self, url_params, **kwargs):
        ...

    @classmethod
    def resolve_auth(cls, auth_data):
        if hasattr(auth_data, 'prep_request'):
            return auth_data
        elif auth_data is None:
            return NoAuth()
        elif isinstance(auth_data, str):
            return BearerTokenAuth(auth_data)
        elif (
                not hasattr(auth_data, 'items')
                and len(auth_data) == 2
                and all(isinstance(x, str) for x in auth_data)
        ):
            return BasicAuth(*auth_data)
        else:
            return cls.dispatch_auth(auth_data)

    auth_types = {}
    @classmethod
    def get_auth_dispatch(cls):
        return dict({
            ('username', 'password'):BasicAuth,
            ('header', 'value'):HeaderValueAuth,
            ('token',):BearerTokenAuth,
        }, **cls.auth_types)
    @classmethod
    def dispatch_auth(cls, opts):
        for params, auth_type in sorted(
                cls.get_auth_dispatch().items(),
                key=lambda kt:-len(kt[0])
        ):
            if params is not None and all(p in opts for p in params):
                return auth_type(**opts)
        else:
            raise ValueError(f"can't dispatch auth type on {opts}")

class NoAuth(APIAuthentication):
    def prep_request(self, url_params, **kwargs):
        return url_params, kwargs

class HeaderValueAuth(APIAuthentication):
    def __init__(self, header, value):
        self.key = header
        self.val = value

    def prep_request(self, url_params, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers[self.key] = self.val
        return url_params, dict(kwargs, headers=headers)


class BasicAuth(APIAuthentication):
    """
    Does any site still use this???
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def prep_request(self, url_params, headers=None, **kwargs):
        if headers is None:
            headers = {}
        key = base64.urlsafe_b64encode(f'{self.username}:{self.password}'.encode()).decode()
        headers['Authentication'] = f'Basic {key}'
        return url_params, dict(kwargs, headers=headers)

class BearerTokenAuth(APIAuthentication):
    def __init__(self, token, encoded=True):
        if not encoded:
            base64.urlsafe_b64encode(token.encode()).decode()
        self.token = token

    def prep_request(self, url_params, headers=None, **kwargs):
        if headers is None:
            headers = {}
        headers['Authentication'] = f'Bearer {self.token}'
        return url_params, dict(kwargs, headers=headers)



class WebAPIConnection:
    """
    Base class for super simple web api interactions, use something better designed in general
    """

    def __init__(self, auth_info, history_length=None, log_requests=False, request_delay_time=None):
        self.auth = APIAuthentication.resolve_auth(auth_info)
        self.history = collections.deque(maxlen=history_length)
        self.subapi_instances = {}
        self.log_requests = log_requests
        self.delay = request_delay_time
        self._last_request = None

    default_content_type='application/json'
    default_return_type='application/json'
    def prep_headers(self, headers, content_type=None, return_type=None):
        if headers is None:
            headers = {}
        headers = headers.copy()
        if content_type is None:
            content_type = self.default_content_type
        if return_type is None:
            return_type = self.default_return_type
        if 'Content-Type' not in headers:
            headers['Content-Type'] = content_type
        if 'Accept' not in headers:
            headers['Accept'] = return_type
        return headers

    default_request_handler = WebRequestHandler
    def do_request(self,
                   method,
                   root,
                   *path,
                   query=None,
                   headers=None,
                   content_type=None,
                   return_type=None,
                   handler=None,
                   delay_time=None,
                   json=None,
                   data=None,
                   **urllib3_request_kwargs
                   ):
        if delay_time is None:
            delay_time = self.delay
        if delay_time is not None:
            if self._last_request is None:
                self._last_request = time.process_time() - delay_time
            proc_time = time.process_time()
            delay = proc_time - self._last_request
            if delay < self.delay:
                time.sleep(self.delay - delay)
            self._last_request = proc_time
        url_params = self.get_endpoint_params(root, path, query)
        url_params, urllib3_request_kwargs = self.auth.prep_request(url_params,
                                                                    headers=headers,
                                                                    json=json, data=data,
                                                                    **urllib3_request_kwargs)
        if 'headers' in urllib3_request_kwargs:
            headers = urllib3_request_kwargs['headers']
            del urllib3_request_kwargs['headers']
        if 'data' in urllib3_request_kwargs:
            data = urllib3_request_kwargs['data']
            del urllib3_request_kwargs['data']
        if 'json' in urllib3_request_kwargs:
            json = urllib3_request_kwargs['json']
            del urllib3_request_kwargs['json']

        headers = self.prep_headers(headers, content_type=content_type, return_type=return_type)
        url = urllib.parse.urlunsplit(url_params).rstrip("/")
        if handler is None:
            handler = self.default_request_handler
        if self.log_requests:
            print(method, url, json, headers)
        resp = handler.request(method, url,
                               headers=headers,
                               json=json, data=data,
                               **urllib3_request_kwargs)
        self.history.append(resp)
        return handler.handle_response(resp, headers)

    def get(self,
            root,
            *path,
            query=None,
            **urllib3_request_kwargs):
        return self.do_request('GET', root, *path, query=query, **urllib3_request_kwargs)

    def post(self,
             root,
             *path,
             query=None,
             **urllib3_request_kwargs):
        return self.do_request('POST', root, *path, query=query, **urllib3_request_kwargs)

    def delete(self,
               root,
               *path,
               query=None,
               **urllib3_request_kwargs):
        return self.do_request('DELETE', root, *path, query=query, **urllib3_request_kwargs)

    request_base = None
    def get_endpoint_params(self, root, path, query=None, base=None, fragment=None):
        if fragment is None:
            fragment = ''
        if query is None:
            query = ''
        elif not isinstance(query, str):
            query = urllib.parse.urlencode(query)
        if base is None:
            base = self.request_base
        if base is not None:
            root = urllib.parse.urljoin(base.rstrip('/')+"/", root)
        parse_root = urllib.parse.urlsplit(root)
        if isinstance(path, str):
            path = (path,)
        path = urllib.parse.urljoin(parse_root.path.rstrip('/')+"/",
                                    "/".join(urllib.parse.quote(s.strip("/")) for s in path)
                                    )
        return (
            parse_root.scheme,
            parse_root.netloc,
            path,
            query,
            fragment
        )

    def get_subapi(self, extension):
        if extension not in self.subapi_instances:
            self.subapi_instances[extension] = WebSubAPIConnection(extension, self)
        return self.subapi_instances[extension]

class WebSubAPIConnection(WebAPIConnection):
    def __init__(self, path_extension, root_api:WebAPIConnection):
        super().__init__(root_api.auth,
                         log_requests=root_api.log_requests,
                         request_delay_time=root_api.delay
                         )
        self.history = root_api.history
        self.request_base = urllib.parse.urljoin(root_api.request_base.rstrip('/')+"/", path_extension, allow_fragments=True)

class WebResourceManager(ResourceManager):
    default_resource_name = 'links'
    default_request_handler = WebRequestHandler
    def __init__(self, *, request_handler=None, **opts):
        if request_handler is None:
            request_handler = self.default_request_handler
        self.request_handler = request_handler
        super().__init__(**opts)
    def get_resource_filename(self, name):
        basename = urllib.parse.urlsplit(name).path.split('/')[-1]
        return '{}-{}'.format(basename, hashlib.md5(name.encode()).hexdigest())
    def download_link(self, link):
        return self.request_handler.read_response(
            self.request_handler.request("GET", link),
            decode=False
        )
    resource_function = download_link


class ReleaseZIPManager(WebResourceManager):
    default_resource_name = 'releases'
    location_env_var = 'GITHUB_RELEASE_DIR'
    use_temporary = True

    @classmethod
    def parse_semver(cls, version_string):
        return tuple(
            int(t)
            for t in version_string.rsplit('v', 1)[-1].split('.')
        )

    @classmethod
    def make_semver(cls, version):
        return 'v' + '.'.join(str(v) for v in version)

    @classmethod
    def parse_name_version(cls, filename):
        name, version = filename.rsplit('-', 1)[0].rsplit('v', 1)
        return name, cls.parse_semver(version)

    def list_resources(self):
        base_list = super().list_resources()
        resource_list = {}
        for filename, filepath in base_list.items():
            try:
                name, version = self.parse_name_version(filename)
            except ValueError:
                pass
            else:
                if name not in resource_list: resource_list[name] = {}
                resource_list[name][version] = filepath
        return resource_list
    def save_resource(self, loc, val):
        super().save_resource(loc, val)
        with zipfile.ZipFile(loc) as zip_extractor:
            dirs = zip_extractor.namelist()
            github_dirname = dirs[0]
            cwd = os.getcwd()
            try:
                os.chdir(self.location)
                zip_extractor.extractall(members=[d for d in dirs if d.startswith(github_dirname)])
                try:
                    os.remove(loc)
                except:
                    raise
                else:
                    os.rename(github_dirname, loc)
            finally:
                os.chdir(cwd)


class GitHubReleaseManager(WebAPIConnection):
    request_base = 'https://api.github.com/'
    resource_key = "zipball_url"
    release_manager_class = ReleaseZIPManager

    def __init__(self, token=None, request_delay_time=None, release_manager=None, **opts):
        if release_manager is None:
            release_manager = self.release_manager_class()
        self.release_manager = release_manager
        self.update_existing_releases()
        super().__init__({'header':'apikey', 'value':token}, request_delay_time=request_delay_time, **opts)


    blacklist_repos = [
        '.github'
    ]
    def list_repos(self, owner):
        return {
            r['name']:r
            for r in self.get('orgs', owner, 'repos')
            if r['name'] not in self.blacklist_repos
        }

    def list_releases(self, owner, repo):
        return {
            r['tag_name']:r
            for r in self.get('repos', owner, repo, 'releases')
        }
    def latest_release(self, owner, repo):
        return self.get('repos', owner, repo, 'releases', 'latest')

    # release_loc = None
    # def download_release(self, release_dict, where=None):
    #     with urllib.request.urlopen(release_dict['zipball_url']) as f:
    #         zip = f.read()

    release_cache = {}
    def update_existing_releases(self):
        release_list = self.release_manager.list_resources()
        for name, version_list in release_list.items():
            if name not in self.release_cache: self.release_cache[name] = {}
            self.release_cache[name].update(version_list)

    @classmethod
    def format_repo_key(cls, owner, name):
        return f"{owner}/{name}"
    def resolve_resource_url(self, v):
        return v[self.resource_key]
    def get_release_list(self, owner, name, update=None):
        key = self.format_repo_key(owner, name)
        if update or (update is None and key not in self.release_cache):
            self.release_cache[key] = {
                self.release_manager.parse_semver(k): self.resolve_resource_url(v)
                for k, v in self.list_releases(owner, name).items()
            }
        elif name not in self.release_cache:
            self.update_existing_releases()
        if name not in self.release_cache:
            raise ValueError(f"couldn't find any potential releases for {name}")
        return self.release_cache[name]