# LabelPermission

Label permission object

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**project_id** | **int** | Project ID | [optional] 
**label_name** | **str** | Label name | [optional] 
**can_read** | **bool** | Read permission | [optional] 
**can_write** | **bool** | Write permission | [optional] 
**can_manage** | **bool** | Management permission | [optional] 

## Example

```python
from orbuculum_client.models.label_permission import LabelPermission

# TODO update the JSON string below
json = "{}"
# create an instance of LabelPermission from a JSON string
label_permission_instance = LabelPermission.from_json(json)
# print the JSON string representation of the object
print(LabelPermission.to_json())

# convert the object into a dict
label_permission_dict = label_permission_instance.to_dict()
# create an instance of LabelPermission from a dict
label_permission_from_dict = LabelPermission.from_dict(label_permission_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


