import json

import requests

from boa.environment import Address

SESSION = requests.Session()


def fetch_abi_from_etherscan(
    address: str, uri: str = "https://api.etherscan.io/api", api_key: str = None
):
    # check if `address` is a proxy contract
    address = Address(_get_implementation_address(address, uri, api_key))

    # fetch ABI of `address`
    params = dict(module="contract", action="getabi", address=address)
    if api_key is not None:
        params["apikey"] = api_key

    res = SESSION.get(uri, params=params)
    res.raise_for_status()
    data = res.json()

    if int(data["status"]) != 1:
        raise ValueError(f"Failed to retrieve data from API: {data}")

    return json.loads(data["result"].strip())


def _get_implementation_address(
    address: str, uri: str = "https://api.etherscan.io/api", api_key: str = None
):
    params = dict(module="contract", action="getsourcecode", address=address)
    if api_key is not None:
        params["apikey"] = api_key

    res = SESSION.get(uri, params=params)
    res.raise_for_status()
    source_data = res.json()

    if int(source_data["status"]) != 1:
        raise ValueError(f"Failed to retrieve source from Etherscan: {source_data}")

    source_data = source_data["result"][0]

    # check if the contract is a proxy
    if int(source_data["Proxy"]) == 1:
        return source_data.get("Implementation")
    else:
        return address
