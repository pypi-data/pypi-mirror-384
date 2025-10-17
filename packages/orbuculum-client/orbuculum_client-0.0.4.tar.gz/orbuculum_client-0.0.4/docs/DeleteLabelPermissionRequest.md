# DeleteLabelPermissionRequest

Request body for deleting label permission

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**project_id** | **int** | Project ID | 
**role_id** | **int** | Role ID | 
**account_id** | **int** | Account ID | 
**can_manage** | **bool** | Whether to delete manage permission | 

## Example

```python
from orbuculum_client.models.delete_label_permission_request import DeleteLabelPermissionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of DeleteLabelPermissionRequest from a JSON string
delete_label_permission_request_instance = DeleteLabelPermissionRequest.from_json(json)
# print the JSON string representation of the object
print(DeleteLabelPermissionRequest.to_json())

# convert the object into a dict
delete_label_permission_request_dict = delete_label_permission_request_instance.to_dict()
# create an instance of DeleteLabelPermissionRequest from a dict
delete_label_permission_request_from_dict = DeleteLabelPermissionRequest.from_dict(delete_label_permission_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


