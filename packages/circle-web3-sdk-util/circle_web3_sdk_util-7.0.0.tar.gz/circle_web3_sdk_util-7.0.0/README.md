# Circle Web3 APIs Python SDK

The Circle Web3 Python SDK provides convenient access to the Circle Web3 APIs for
applications written in Python. For the API reference, see the [Circle Web3 API Docs](https://developers.circle.com/w3s/reference/getping). 
Also see this project's [PyPI Package Page [TODO]]().

## Requirements

Python 3.10+.

Java 11 and Node 10+ (optional for contributing and development).

## Installation

The recommended way of installation is using the Python Package Index (PyPI):
```sh
pip install circle-developer-controlled-wallets
pip install circle-smart-contract-platform
pip install circle-user-controlled-wallets
```

## Development
Clone this repo and install development dependencies using

```sh
# For codegen tools and git hook checks
npm ci
```

Initialize the submodules:
```bash
git submodule init
```

Build the OpenAPI specifications:
```bash
cd w3s-openapi-internal
make bundle
cd ..
```

Run the codegen command to generate the source code for this SDK from 
the `w3s-openapi-internal` OpenAPI specifications
```sh
npm run build
```

## Usage

Initialize circle web3 API clients. To secure your entity secret and circle API key. Set the API key and entity secret as environment variables. Learn more about entity secret management [here](https://developers.circle.com/w3s/docs/entity-secret-management)

```shell
export CIRCLE_ENTITY_SECRET="Your entity secret"
export CIRCLE_WEB3_API_KEY="Your API KEY"
```

```python
from circle.web3 import utils

dcw_client = utils.init_developer_controlled_wallets_client(api_key="Your API KEY", entity_secret="Your entity secret")
scp_client = utils.init_smart_contract_platform_client(api_key="Your API KEY", entity_secret="Your entity secret")
ucw_client = utils.init_user_controlled_wallets_client(api_key="Your API KEY")
```

Using client to make a transaction.

```python
from circle.web3 import user_controlled_wallets

# Create a API instance
ucw_client = utils.init_user_controlled_wallets_client(api_key="<your-api-key>")

api_instance = user_controlled_wallets.PINAuthenticationApi(ucw_client)
try:
    api_request = user_controlled_wallets.UserTokenRequest.from_dict({"userId": "test-user"})
    api_response = api_instance.get_user_token(api_request)
    print(api_response.data.user_token)
except user_controlled_wallets.ApiException as e:
    print("Exception when calling PINAuthenticationApi->get_user_token: %s\n" % e)
```

## Contributions

Please follow the [Conventional Commits][convencomms] format for all commits when creating a contributing pull request for this repo.

[convencomms]: https://www.conventionalcommits.org/en/v1.0.0/
