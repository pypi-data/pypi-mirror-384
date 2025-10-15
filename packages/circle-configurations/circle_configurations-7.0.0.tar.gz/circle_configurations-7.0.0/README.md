# circle-configurations
General Configuration APIs for Developer Services products.

- API version: 1.0
- Package version: 7.0.0

## Requirements.

Python 3.7+

## Installation
### pip install

```sh
pip install circle-configurations
```

Then import the package:
```python
from circle.web3 import configurations
```


## Usage


1. Generate an API key, if you haven't already, in the [Web3 Services Console](https://console.circle.com/). This API key will be used for authentication and authorization when making requests to Circle's APIs. API key can be set by environment variable or function parameter

```sh
export CIRCLE_WEB3_API_KEY="Your API KEY"
```

2. Initiate API client

```python
from circle.web3 import utils

client = utils.init_configurations_client(api_key="Your API KEY")
```

3. Interact with the client:

```python
from circle.web3 import configurations

api_instance = configurations.DeveloperAccountApi(client)
try:
    api_response = api_instance.get_public_key()
    print(api_response.data.public_key)
except configurations.ApiException as e:
    print("Exception when calling DeveloperAccountApi->get_public_key: %s\n" % e)
```

## Configuration

The client accept following configuration parameters:

Option | Required | Description
------------ | ------------- | -------------
api_key | [] | Api Key that is used to authenticate against Circle APIs.
host | [] | Optional base URL to override the default: https://api.circle.com.
user_agent | [] | Optional custom user agent request header. We will prepend it to default user agent header if provided.

## Need help or have questions?

Here are some helpful links, if you encounter any issues or have questions about this SDK:

 - 📖 [Getting started](https://developers.circle.com/interactive-quickstarts): Check out our official Developer-Controlled Wallets QuickStart.
 - 🎮 [Join our Discord Community](https://discord.com/invite/buildoncircle): Engage, learn, and collaborate.
 - 🛎 [Visit our Help-Desk Page](https://support.usdc.circle.com/hc/en-us/p/contactus?_gl=1*1va6vat*_ga*MTAyNTA0NTQ2NC4xNjk5NTYyMjgx*_ga_GJDVPCQNRV*MTcwMDQ5Mzg3Ny4xNC4xLjE3MDA0OTM4ODQuNTMuMC4w): Dive into curated FAQs and guides.
 - 📧 [Direct Email](mailto:customer-support@circle.com): We're always a message away.
 - 📖 [Read docs](https://developers.circle.com/w3s/docs?_gl=1*15ozb5b*_ga*MTAyNTA0NTQ2NC4xNjk5NTYyMjgx*_ga_GJDVPCQNRV*MTcwMDQ5Mzg3Ny4xNC4xLjE3MDA0OTM4ODQuNTMuMC4w): Check out our developer documentation.
Happy coding!
