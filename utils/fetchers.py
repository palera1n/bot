import json
import urllib

import aiohttp
from aiocache import cached

client_session = None


@cached(ttl=3600)
async def get_ios_cfw():
    """Gets all apps on ios.cfw.guide

    Returns
    -------
    dict
        "ios, jailbreaks, devices"
    """

    async with client_session.get("https://api.appledb.dev/main.json") as resp:
        if resp.status == 200:
            data = await resp.json()

    return data


@cached(ttl=3600)
async def get_ipsw_firmware_info(version: str):
    """Gets all apps on ios.cfw.guide

    Returns
    -------
    dict
        "ios, jailbreaks, devices"
    """

    async with client_session.get(f"https://api.ipsw.me/v4/ipsw/{version}") as resp:
        if resp.status == 200:
            data = await resp.json()
            return data

        return []


@cached(ttl=600)
async def get_dstatus_components():
    async with client_session.get("https://discordstatus.com/api/v2/components.json") as resp:
        if resp.status == 200:
            components = await resp.json()
            return components


@cached(ttl=600)
async def get_dstatus_incidents():
    async with client_session.get("https://discordstatus.com/api/v2/incidents.json") as resp:
        if resp.status == 200:
            incidents = await resp.json()
            return incidents


async def canister_search_package(query):
    """Search for a tweak in Canister's catalogue

    Parameters
    ----------
    query : str
        "Query to search for"

    Returns
    -------
    list
        "List of packages that Canister found matching the query"

    """

#    async with client_session.get(f'https://api.canister.me/v1/community/packages/search?query={urllib.parse.quote(query)}&searchFields=identifier,name&responseFields=identifier,header,tintColor,name,price,description,packageIcon,repository.uri,repository.name,author,maintainer,latestVersion,nativeDepiction,depiction') as resp:
     async with client_session.get(f'https://api.canister.me/v2/jailbreak/package/search?q={urllib.parse.quote(query)}&limit=250'):
        if resp.status == 200:
            response = json.loads(await resp.text())
            if response.get('status') == "Successful":
                return response.get('data')
            else:
                return None
        else:
            return None


async def canister_search_repo(query):
    """Search for a repo in Canister's catalogue

    Parameters
    ----------
    query : str
        "Query to search for"

    Returns
    -------
    list
        "List of repos that Canister found matching the query"

    """

    async with client_session.get(f'https://api.canister.me/v1/community/repositories/search?query={urllib.parse.quote(query)}') as resp:
        if resp.status == 200:
            response = json.loads(await resp.text())
            if response.get('status') == "Successful":
                return response.get('data')
            else:
                return None
        else:
            return None


@cached(ttl=3600)
async def canister_fetch_repos():
    async with client_session.get('https://api.canister.me/v1/community/repositories/search?ranking=1,2,3,4,5') as resp:
        if resp.status == 200:
            response = await resp.json(content_type=None)
            return response.get("data")

        return None


@cached(ttl=3600)
async def fetch_scam_urls():
    async with client_session.get("https://raw.githubusercontent.com/SlimShadyIAm/Anti-Scam-Json-List/main/antiscam.json") as resp:
        if resp.status == 200:
            obj = json.loads(await resp.text())
            return obj


async def init_client_session():
    global client_session
    client_session = aiohttp.ClientSession()
