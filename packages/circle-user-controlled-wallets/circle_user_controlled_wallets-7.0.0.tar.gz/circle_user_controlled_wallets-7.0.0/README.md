# circle-user-controlled-wallets
User-Controlled Wallets API documentation.

- API version: 1.0
- Package version: 7.0.0

## Requirements.

Python 3.7+

## Installation
### pip install

```sh
pip install circle-user-controlled-wallets
```

Then import the package:
```python
from circle.web3 import user_controlled_wallets
```


## Usage

1. Generate an API key, if you haven't already, in the [Web3 Services Console](https://console.circle.com/). This API key will be used for authentication and authorization when making requests to Circle's APIs. API key can be set by environment variable or function parameter

```sh
export CIRCLE_WEB3_API_KEY="Your API KEY"
```

2. Follow our [User-Controlled QuickStart](https://developers.circle.com/interactive-quickstarts/user-controlled-wallets). This step ensures that you fully grasp the concept of Circle's User-Controlled Wallets.

3. Initiate API client

```python
from circle.web3 import utils

client = utils.init_user_controlled_wallets_client(api_key="Your API KEY")
```

4. Interact with the client:

```python
import uuid
from circle.web3 import user_controlled_wallets

# generate a user id
user_id = str(uuid.uuid4())

# create user
api_instance = user_controlled_wallets.UsersApi(client)
try:
    request = user_controlled_wallets.CreateUserRequest(user_id=user_id)
    api_instance.create_user(request)
except user_controlled_wallets.ApiException as e:
    print("Exception when calling UsersApi->create_user: %s\n" % e)

# get user
try:
    response = api_instance.get_user(id=user_id)
    print(response.data)
except user_controlled_wallets.ApiException as e:
    print("Exception when calling UsersApi->get_user: %s\n" % e)

# get user token
try:
    auth_api_instance = user_controlled_wallets.PINAuthenticationApi(client)
    request = user_controlled_wallets.UserTokenRequest.from_dict({"userId": user_id})
    response = auth_api_instance.get_user_token(request)
    print(response)
except user_controlled_wallets.ApiException as e:
    print("Exception when calling PINAuthenticationApi->get_user_token: %s\n" % e)
```

We recommend reading through the official [documentation](https://developers.circle.com/w3s/docs) and [QuickStart guides](https://developers.circle.com/interactive-quickstarts) mentioned above to ensure a smooth setup and usage experience.


## Configuration

The client accept following configuration parameters:

Option | Required | Description
------------ | ------------- | -------------
api_key | Yes | Api Key that is used to authenticate against Circle APIs. Must be provided by ether env variable or function parameter.
host | No | Optional base URL to override the default: https://api.circle.com/v1/w3s.
user_agent | No | Optional custom user agent request header. We will prepend it to default user agent header if provided.


## Need help or have questions?

Here are some helpful links, if you encounter any issues or have questions about this SDK:

- 📖 [Getting started](https://developers.circle.com/interactive-quickstarts/user-controlled-wallets): Check out our official User-Controlled Wallets QuickStart.
- 🎮 [Join our Discord Community](https://discord.com/invite/buildoncircle): Engage, learn, and collaborate.
- 🛎 [Visit our Help-Desk Page](https://support.usdc.circle.com/hc/en-us/p/contactus?_gl=1*1va6vat*_ga*MTAyNTA0NTQ2NC4xNjk5NTYyMjgx*_ga_GJDVPCQNRV*MTcwMDQ5Mzg3Ny4xNC4xLjE3MDA0OTM4ODQuNTMuMC4w): Dive into curated FAQs and guides.
- 📧 [Direct Email](mailto:customer-support@circle.com): We're always a message away.
- 📖 [Read docs](https://developers.circle.com/w3s/docs?_gl=1*15ozb5b*_ga*MTAyNTA0NTQ2NC4xNjk5NTYyMjgx*_ga_GJDVPCQNRV*MTcwMDQ5Mzg3Ny4xNC4xLjE3MDA0OTM4ODQuNTMuMC4w): Check out our developer documentation.
Happy coding!
