# IP Fabric 

IPFabric is a Python module for connecting to and communicating against an IP Fabric instance.

***For full documentation please see [IP Fabric Documentation Portal](https://docs.ipfabric.io/main/integrations/python/).***

## IP Fabric

[IP Fabric](https://ipfabric.io) is a vendor-neutral network assurance platform that automates the 
holistic discovery, verification, visualization, and documentation of 
large-scale enterprise networks, reducing the associated costs and required 
resources whilst improving security and efficiency.

It supports your engineering and operations teams, underpinning migration and 
transformation projects. IP Fabric will revolutionize how you approach network 
visibility and assurance, security assurance, automation, multi-cloud 
networking, and trouble resolution.

**Integrations or scripts should not be installed directly on the IP Fabric VM unless directly communicated from the
IP Fabric Support or Solution Architect teams.  Any action on the Command-Line Interface (CLI) using the root, osadmin,
or autoboss account may cause irreversible, detrimental changes to the product and can render the system unusable.**

## Bugs

A bug has been identified when ~2,000 requests are being made to the API.  The underlining issue seems to be with the
implementation of `http2`. The workaround is to set `http2=False` in the `IPFClient` class.  Example error:

`httpx.RemoteProtocolError: <ConnectionTerminated error_code:ErrorCodes.NO_ERROR, last_stream_id:1999, additional_data:None>`

## Notices

**Please note IP Fabric's new [API Versioning Policy](https://docs.ipfabric.io/latest/IP_Fabric_API/#api-versioning).**

IP Fabric team is migrating from `httpx` to [`niquests`](https://github.com/jawah/niquests) in IP Fabric SDK `v7.5.0`.
This is outside of a major release however the IP Fabric version `7.5.0` will include our new database and will require
through testing to ensure compatibility.

This should not impact any existing automations unless you are using `httpx` Client in your code. This is a private
attribute of the IP Fabric `IPFClient` class. The HTTP method functions did not appear to require any changes so using
`IPFClient().get()`, `IPFClient().post()`, etc. will continue to work as expected we expect.

Reasons: 

- Our team has opened an issue with `httpx` to address the bug above and have not received any support after 10 months.
- Last release of `httpx` was in December 2024 compared to `niquests` which has more frequent releases.
- Lacks many features compared to `niquests`.
- Will enable our team to explore HTTP2 multiplexing API requests.
- `niquests` is a maintained fork of `requests` so should be familiar to most Python users.

![Niquests Features](niquests.png)

## Upcoming Deprecation Notices

### v7.5.0

#### HTTPX Client

In `ipfabric>=v7.5.0` the HTTP Client will be changed from `httpx` to `niquests`.
Please see the notice above for more information.

#### Restore Intents
With the introduction of the IP Fabric **Configuration Import/Export** Feature in version `7.2` 
`ipfabric.tools.restore_intents.RestoreIntents()` will be removed.  Please utilize the new 
`IPFClient().settings.appliance_configuration` methods.

### v8.0.0

#### Python 3.9 Removed

Python 3.9 (End of Life 2025-10) will be removed in `v8.0.0`.  Please ensure you are using Python 3.10+.

#### Moved Models

The following Models have moved and old locations removed in `v8.0.0`:

* `ipfabric.settings.vendor_api_models.*` -> `ipfabric.models.vendor_api`
* `ipfabric.settings.discovery.Networks` -> `ipfabric.models.discovery.Networks`
* `ipfabric.settings.seeds.SeedList` -> `ipfabric.models.discovery.SeedList`
* `ipfabric.settings.authentication.[Credential, CredentialList, Privilege, PrivilegeList]` -> `ipfabric.models.authentication`

#### Login IP Columns Removed

**In `ipfabric>=v7.3.0` column `loginIp` was replaced with `loginIpv4` and `loginIpv6` and in `v8.0.0` it is changed to a text field return IPv4 or IPv6.**

The current `loginIp` column are removed from these tables:

* Inventory > Devices: `tables/inventory/devices`
* Discovery Snapshot > Connectivity Report: `tables/reports/discovery-tasks`
* Management > Discovery History: `tables/inventory/discovery-history`
* Management > Changes: 
  * `tables/management/changes/devices`
  * `tables/management/changes/managed-devs`
* Management > Saved Config Consistency: `tables/management/configuration/saved`
* Technology > Management > Telnet access: `tables/security/enabled-telnet`

## Versioning

**Please note IP Fabric's new [API Versioning Policy](https://docs.ipfabric.io/latest/IP_Fabric_API/#api-versioning).**

Semantic Versioning: `Major.Minor.Patch`

Starting with IP Fabric version 5.0.x the `ipfabric` SDK is recommended to match your IP Fabric major and minor version.  
We will try to keep some backwards compatability (SDK version `6.9.x` should work with IP Fabric API `6.8`) however new 
features may break some functionality.  By ensuring that your `ipfabric` SDK's match your IP Fabric major and minor  
version will ensure compatibility and will continue to work.

The Patch version of the SDK is used for bug fixes and new features that are compatible with the major and minor version.

## Defaulted to Streaming Data

See [Notices](NOTICES.md) for full information.

* GET URL is limited to 4096 characters.
  * Complex queries and filters could go over this limit; however in testing it was very difficult to reach this.
* CSV Export
  * Only supported with a streaming GET request and return a bytes string of data in the Python SDK.
  * It will also convert times to human-readable format.
  * **`reports` (returning Intent Check data) is not supported with CSV export, however is required when filtering based on Intents (colors).**

```python
from ipfabric import IPFClient
ipf = IPFClient(streaming=True)

dev = ipf.inventory.devices.all()
print(type(dev))  # list 

dev_csv = ipf.fetch_all('tables/inventory/devices', export='csv')
print(type(dev_csv))  # bytes 

# Timezone can be changed for CSV export; see `ipfabric.tools.shared.TIMEZONES`
dev_csv_tz = ipf.inventory.devices.all(export='csv', csv_tz='UTC')

# If specifying to return reports and CSV request will drop reports input and use GET
dev_csv_reports = ipf.fetch_all('tables/inventory/devices', reports=True, export='csv')
"""CSV export does not return reports, parameter has been excluded."""
print(type(dev_csv_reports))  # bytes

# If URL exceeds 4096 characters the following exception will be raised:
# raise InvalidURL(f"URL exceeds max character limit of 4096: length={len(url)}.")
```

## Installation

```
pip install ipfabric
```

To use `export='df'` on some methods please install `pandas` with `ipfabric`

```
pip install ipfabric[pd]
```

## Introduction

Please take a look at [API Programmability - Part 1: The Basics](https://ipfabric.io/blog/api-programmability-part-1/)
for instructions on creating an API token.

Most of the methods and features can be located in [Examples](examples) to show how to use this package. 
Another great introduction to this package can be found at [API Programmability - Part 2: Python](https://ipfabric.io/blog/api-programmability-python/)

## Authentication

### Username/Password

Supply in client:
```python
from ipfabric import IPFClient
ipf = IPFClient('https://demo3.ipfabric.io/', auth=('user', 'pass'))
```

### Token

```python
from ipfabric import IPFClient
ipf = IPFClient('https://demo3.ipfabric.io/', auth='token')
```

### Environment 

The easiest way to use this package is with a `.env` file.  You can copy the sample and edit it with your environment variables. 

```commandline
cp sample.env .env
```

This contains the following variables which can also be set as environment variables instead of a .env file.
```
IPF_URL="https://demo3.ipfabric.io"
IPF_TOKEN=TOKEN
IPF_VERIFY=true
```

Or if using Username/Password:
```
IPF_URL="https://demo3.ipfabric.io"
IPF_USERNAME=USER
IPF_PASSWORD=PASS
```

## Development

### Poetry Installation

IPFabric uses [Poetry](https://pypi.org/project/poetry/) to make setting up a virtual environment with all dependencies
installed quick and easy.

Install poetry globally:
```
pip install poetry
```

To install a virtual environment run the following command in the root of this directory.

```
poetry install
```

To run examples, install extras:
```
poetry install ipfabric -E examples
```

### Test and Build

```
poetry run pytest
poetry build
```

Prior to pushing changes run:
```
poetry run black ipfabric
poetry update
```
