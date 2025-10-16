# CreateLabelPermissionRequest

Request body for creating label permission

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**project_id** | **int** | Project ID | 
**role_id** | **int** | Role ID | 
**can_read** | **bool** | Read permission | [optional] 
**can_write** | **bool** | Write permission | [optional] 
**can_manage** | **bool** | Management permission | [optional] 

## Example

```python
from orbuculum_client.models.create_label_permission_request import CreateLabelPermissionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateLabelPermissionRequest from a JSON string
create_label_permission_request_instance = CreateLabelPermissionRequest.from_json(json)
# print the JSON string representation of the object
print(CreateLabelPermissionRequest.to_json())

# convert the object into a dict
create_label_permission_request_dict = create_label_permission_request_instance.to_dict()
# create an instance of CreateLabelPermissionRequest from a dict
create_label_permission_request_from_dict = CreateLabelPermissionRequest.from_dict(create_label_permission_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


