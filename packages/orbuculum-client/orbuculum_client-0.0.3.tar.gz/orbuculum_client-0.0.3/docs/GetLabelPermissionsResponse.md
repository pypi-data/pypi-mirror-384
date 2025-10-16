# GetLabelPermissionsResponse

Response containing label permissions

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**data** | [**List[LabelPermission]**](LabelPermission.md) | Array of label permissions | [optional] 

## Example

```python
from orbuculum_client.models.get_label_permissions_response import GetLabelPermissionsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetLabelPermissionsResponse from a JSON string
get_label_permissions_response_instance = GetLabelPermissionsResponse.from_json(json)
# print the JSON string representation of the object
print(GetLabelPermissionsResponse.to_json())

# convert the object into a dict
get_label_permissions_response_dict = get_label_permissions_response_instance.to_dict()
# create an instance of GetLabelPermissionsResponse from a dict
get_label_permissions_response_from_dict = GetLabelPermissionsResponse.from_dict(get_label_permissions_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


