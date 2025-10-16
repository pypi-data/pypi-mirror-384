# UpdateLabelRequest

Request body for updating an existing label

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**project_id** | **int** | Project ID to update | 
**name** | **str** | New label name | 
**color** | **int** | Label color ID | 
**icon** | **int** | Label icon ID | 

## Example

```python
from orbuculum_client.models.update_label_request import UpdateLabelRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateLabelRequest from a JSON string
update_label_request_instance = UpdateLabelRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateLabelRequest.to_json())

# convert the object into a dict
update_label_request_dict = update_label_request_instance.to_dict()
# create an instance of UpdateLabelRequest from a dict
update_label_request_from_dict = UpdateLabelRequest.from_dict(update_label_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


