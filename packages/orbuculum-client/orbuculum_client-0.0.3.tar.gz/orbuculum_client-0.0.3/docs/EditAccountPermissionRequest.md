# EditAccountPermissionRequest

Request body for editing account permission

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**permission_id** | **int** | Permission ID to edit | 
**can_read** | **bool** | Read permission | [optional] 
**can_write** | **bool** | Write permission | [optional] 
**can_manage** | **bool** | Management permission | [optional] 

## Example

```python
from orbuculum_client.models.edit_account_permission_request import EditAccountPermissionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of EditAccountPermissionRequest from a JSON string
edit_account_permission_request_instance = EditAccountPermissionRequest.from_json(json)
# print the JSON string representation of the object
print(EditAccountPermissionRequest.to_json())

# convert the object into a dict
edit_account_permission_request_dict = edit_account_permission_request_instance.to_dict()
# create an instance of EditAccountPermissionRequest from a dict
edit_account_permission_request_from_dict = EditAccountPermissionRequest.from_dict(edit_account_permission_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


