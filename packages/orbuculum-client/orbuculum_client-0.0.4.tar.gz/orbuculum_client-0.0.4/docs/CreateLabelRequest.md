# CreateLabelRequest

Request body for creating a new label

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**name** | **str** | Label name | 
**color** | **int** | Label color ID | 
**icon** | **int** | Label icon ID | 

## Example

```python
from orbuculum_client.models.create_label_request import CreateLabelRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateLabelRequest from a JSON string
create_label_request_instance = CreateLabelRequest.from_json(json)
# print the JSON string representation of the object
print(CreateLabelRequest.to_json())

# convert the object into a dict
create_label_request_dict = create_label_request_instance.to_dict()
# create an instance of CreateLabelRequest from a dict
create_label_request_from_dict = CreateLabelRequest.from_dict(create_label_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


