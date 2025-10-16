# Old Deprecation & Other Important Notices

## v7.3.0

**In `ipfabric>=v7.3.x` new columns `loginIpv4` and `loginIpv6` have been introduced to replace `loginIp`.**

The current `loginIp` column has been marked as `Deprecated` in the 7.3 release but it will not be removed after further
discussions with our Development Team.  You may see this warning in your logs but it can safely be ignored.

* Inventory > Devices: `tables/inventory/devices`
* Discovery Snapshot > Connectivity Report: `tables/reports/discovery-tasks`
* Management > Discovery History: `tables/inventory/discovery-history`
* Management > Changes: 
  * `tables/management/changes/devices`
  * `tables/management/changes/managed-devs`
* Management > Saved Config Consistency: `tables/management/configuration/saved`
* Technology > Management > Telnet access: `tables/security/enabled-telnet`

SDK Device Model will be updated to reflect this change and will include the following properties:

* `login_ipv4` - Python `ipaddress.IPv4Address` object.
* `login_ipv6` - Python `ipaddress.IPv6Address` object.
* `login_ip` - No change until the next major release.

## v7.2.0

**In `ipfabric>=v7.2.x` Python 3.8 will be removed as a supported version as it is now 
[End of Life](https://devguide.python.org/versions/) as of 2024-10-07.**

Some changes to Vendor API models have been implemented in order for being able to model all settings.

## v7.0.0

In `ipfabric>=v7.0.0` the following will be changed/deprecated:

- All classes including `IPFClient()` will switch to keyword only arguments to support Pydantic BaseModel.
  - `IPFClient('https//url')` -> `IPFClient(base_url='https//url')`
- `IPFClient().intent.intent_by_name()` will be removed and is replaced by `IPFClient().intent.intents_by_name()`
- The following endpoints were moved and the old methods will be removed:
  - `Technology.LoadBalancing.virtual_servers_f5_partitions` -> `Technology.LoadBalancing.partitions`
  - `Technology.Sdwan.sites` -> `Technology.Sdwan.versa_sites`
  - `Technology.Sdwan.links` -> `Technology.Sdwan.versa_links`

## v6.9.0

In `ipfabric>=v6.9.0` the following will be changed/deprecated:

- `IPFDiagram` will be removed as it is now located in `IPFClient().diagram`, the following will be changed:
  - `IPFDiagram().diagram_model()` -> `IPFClient().diagram.model()` 
  - `IPFDiagram().diagram_json()` -> `IPFClient().diagram.json()` 
  - `IPFDiagram().diagram_svg()` -> `IPFClient().diagram.svg()` 
  -`IPFDiagram().diagram_png()` -> `IPFClient().diagram.png()` 
- Methods found in `ipfabric.models.Snapshot` class will no longer accept the `IPFClient` argument being passed.
  - Example: `ipf.snapshot.lock(ipf)` -> `ipf.snapshot.lock()`

## v6.8.0: Deprecations

In `ipfabric>=v6.8.0` the following has been changed/deprecated:

- The use of `token='<TOKEN>'` or `username='<USER>', password='<PASS>'` in `IPFClient()` will be removed:
  - Token: `IPFClient(auth='TOKEN')`
  - User/Pass: `IPFClient(auth=('USER', 'PASS'))`
  - `.env` file will only accept `IPF_TOKEN` or (`IPF_USERNAME` and `IPF_PASSWORD`) and not `auth`
- Methods found in `ipfabric.models.Device` class will no longer accept the `IPFClient` argument being passed.
  - Example: `ipf.devices.all[0].interfaces(ipf)` -> `ipf.devices.all[0].interfaces()`
- `IPFClient()._get_columns()` will be removed in place of `IPFClient().get_columns()`

## v6.5.0: Streaming Defaulted to True

**STREAMING HAS BEEN DEFAULTED TO TRUE IN `v6.5.0`**

In IP Fabric version `6.3.0` the option to return table data using a streaming
GET request instead of a paginated POST request has been added. 

**FOR CUSTOMERS USING RBAC. Please ensure you are running IP Fabric `>=6.3.1` due to 
a bug where custom RBAC Policies do not allow you to create a Policy to the GET
endpoints and only admins can query data.THIS AFFECTS CSV EXPORT AND STREAMING JSON EXPORT.**

* GET URL is limited to 4096 characters, complex queries and filters could go over this limit; however in testing it was very difficult to reach this.
* Since request has been changed from `httpx.post` to `httpx.stream` no changes in timeout was required in testing.
* Performance Testing on 1.7M rows:
  * POST requires 1,719 requests (1k rows per request) ~ 82 minutes
  * Streaming GET requires 1 request ~ 6.2 minutes
* No degradation in navigating the GUI including viewing table data or creating diagrams.
* Supports `csv` and `json` exports:
  * CSV 
    * Only supported with a streaming GET request and return a bytes string of data in the Python SDK.
    * It will also convert times to human-readable format.
    * **`reports` (returning Intent Check data) is not supported with CSV export, however is required when filtering based on Intents (colors).**
  * JSON provides same support as POST.

```python
from ipfabric import IPFClient
ipf = IPFClient(streaming=True)

dev = ipf.inventory.devices.all()
dev_2 = ipf.fetch_all('tables/inventory/devices')
print(dev == dev_2)  # True
print(type(dev))  # list 

dev_csv = ipf.inventory.devices.all(export='csv')
dev_csv_2 = ipf.fetch_all('tables/inventory/devices', export='csv')
print(dev_csv == dev_csv_2 ) # True
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

## v6.3.1: Python 3.7 Deprecation

In `ipfabric>=v6.3.1` Python 3.7 support will be removed.  This was originally 
planned for `v7.0.0` however to add new functionality of Pandas Dataframe we 
are required to move this forward.

**Python 3.7 is now End of Life as of June 27th 2023**
