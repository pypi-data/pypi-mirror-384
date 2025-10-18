from typing import Tuple, Any

import requests
from functools import cached_property
class MediaWikiSession(requests.Session):
    """Session adapter that provides login information to MediaWiki""" 
    def __init__(self, access_token: str, apiurl: str):
        """apiurl typically https://example.com/api.php"""
        super().__init__()
        self.access_token = access_token
        self.apiurl = apiurl

        # Apply OAuth bearer headers to all requests
        self.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        })

    @cached_property
    def edit_token(self) -> str:
        """Edit token for future use"""
        params = {
            "action": "query",
            "meta": "tokens",
            "format": "json"
        }
        resp = self.get(self.apiurl, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data['query']['tokens']['csrftoken']

    @staticmethod
    def parse_yaml(config_file: str) -> Tuple[Any,'MediaWikiSession']:
        """Return parsed yaml and MediaWikiSession object"""
        import yaml
        with open(config_file) as f:
            cfg = yaml.safe_load(f)
        mw = cfg['mediawiki']
        url = mw['url']
        with open(mw['access token']) as f:
            token = f.read().strip()
        return cfg, MediaWikiSession(token, url)
        return session
