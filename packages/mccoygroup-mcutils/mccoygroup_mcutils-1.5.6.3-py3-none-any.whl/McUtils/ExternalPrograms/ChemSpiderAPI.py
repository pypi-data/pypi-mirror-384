
import os
from .WebAPI import *

__all__ = [
    "ChemSpiderAPI"
]

class ChemSpiderAPI(WebAPIConnection):
    """
    It is better in general to just use the ChemSpiderPy package, but this works for now
    """

    request_base = 'https://api.rsc.org/compounds/v1'
    api_key_env_var = "CHEM_SPIDER_APIKEY"
    def __init__(self, token=None, request_delay_time=None,  **opts):
        token = self.get_chemspider_apikey(token)
        super().__init__({'header':'apikey', 'value':token}, request_delay_time=request_delay_time, **opts)

    @classmethod
    def get_chemspider_apikey(cls, token):
        if token is None:
            token = os.environ.get(cls.api_key_env_var)
        return token

    @property
    def filter(self):
        return self.get_subapi('filter')

    @property
    def records(self):
        return self.get_subapi('records')

    @property
    def lookups(self):
        return self.get_subapi('lookups')

    @property
    def tool(self):
        return self.get_subapi('tool')

    def handle_filter_query(self, query_id, count=1, start=0, **polling_opts):
        res = self.filter.get(f'{query_id}/results', query=dict(count=count, start=start))
        return res
        # https: // api.rsc.org / compounds / v1
        # / filter / {queryId} / results

    def apply_filter_query(self, filter_path, retries=None, timeout=None, request_delay_time=None, **opts):
        base_query = self.filter.post(filter_path, json=opts)
        if 'queryId' in base_query:
            # TODO: handle status?
            request_delay_time = request_delay_time
            return self.handle_filter_query(base_query['queryId'], retries=retries, timeout=timeout)
        else:
            raise ValueError("`queryId` not in filter JSON")

    default_molecule_fields = [
        "CommonName",
        "SMILES",
        "InChI"
    ]
    def get_info(self, ids, fields=None, **opts):
        if fields is None:
            fields = self.default_molecule_fields
        elif isinstance(fields, str):
            fields = [fields]
        return self.records.post("batch", json=dict(recordIds=ids, fields=fields), **opts)['records']

    _name_cache = {}
    def get_compounds_by_name(self, name, return_ids=False, fields=None, **opts):
        if name not in self._name_cache:
            self._name_cache[name] = self.apply_filter_query('name', name=name, **opts)
        ids = self._name_cache[name]['results']
        if return_ids:
            return ids
        else:
            return self.get_info(ids, fields=fields)


        # payload = {"name": "aspirin",
        #            "orderBy": "default",
        #            "orderDirection": "default"}
        #
        # headers = {"apikey": "*your_API_Key*",
        #            "Content-Type": "application/json",
        #            "Accept": "application/json"}
        #
        # response = requests.post(url, json=payload, headers=headers)
        # print(response.json())
        # )