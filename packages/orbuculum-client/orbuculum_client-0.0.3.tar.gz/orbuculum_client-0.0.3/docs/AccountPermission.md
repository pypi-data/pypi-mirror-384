# AccountPermission

Account permission object

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**account_id** | **int** | Account ID | [optional] 
**account_name** | **str** | Account name | [optional] 
**can_read** | **bool** | Read permission | [optional] 
**can_write** | **bool** | Write permission | [optional] 
**can_manage** | **bool** | Management permission | [optional] 

## Example

```python
from orbuculum_client.models.account_permission import AccountPermission

# TODO update the JSON string below
json = "{}"
# create an instance of AccountPermission from a JSON string
account_permission_instance = AccountPermission.from_json(json)
# print the JSON string representation of the object
print(AccountPermission.to_json())

# convert the object into a dict
account_permission_dict = account_permission_instance.to_dict()
# create an instance of AccountPermission from a dict
account_permission_from_dict = AccountPermission.from_dict(account_permission_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


