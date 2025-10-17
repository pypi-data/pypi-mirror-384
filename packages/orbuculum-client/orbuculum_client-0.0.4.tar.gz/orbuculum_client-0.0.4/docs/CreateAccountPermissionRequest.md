# CreateAccountPermissionRequest

Request body for creating account permission

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**account_id** | **int** | Account ID | 
**role_id** | **int** | Role ID | 
**can_manage** | **bool** | Management permission | 
**show_balance** | **bool** | Show balance permission | 

## Example

```python
from orbuculum_client.models.create_account_permission_request import CreateAccountPermissionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateAccountPermissionRequest from a JSON string
create_account_permission_request_instance = CreateAccountPermissionRequest.from_json(json)
# print the JSON string representation of the object
print(CreateAccountPermissionRequest.to_json())

# convert the object into a dict
create_account_permission_request_dict = create_account_permission_request_instance.to_dict()
# create an instance of CreateAccountPermissionRequest from a dict
create_account_permission_request_from_dict = CreateAccountPermissionRequest.from_dict(create_account_permission_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


