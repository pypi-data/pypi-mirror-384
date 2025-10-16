# GetAccountPermissionsResponse

Response containing account permissions

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**data** | [**List[AccountPermission]**](AccountPermission.md) | Array of account permissions | [optional] 

## Example

```python
from orbuculum_client.models.get_account_permissions_response import GetAccountPermissionsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetAccountPermissionsResponse from a JSON string
get_account_permissions_response_instance = GetAccountPermissionsResponse.from_json(json)
# print the JSON string representation of the object
print(GetAccountPermissionsResponse.to_json())

# convert the object into a dict
get_account_permissions_response_dict = get_account_permissions_response_instance.to_dict()
# create an instance of GetAccountPermissionsResponse from a dict
get_account_permissions_response_from_dict = GetAccountPermissionsResponse.from_dict(get_account_permissions_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


