# LabelCreatedResponse

Response after creating a label

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**id** | **int** | Created label ID | [optional] 
**message** | **str** | Success message | [optional] 

## Example

```python
from orbuculum_client.models.label_created_response import LabelCreatedResponse

# TODO update the JSON string below
json = "{}"
# create an instance of LabelCreatedResponse from a JSON string
label_created_response_instance = LabelCreatedResponse.from_json(json)
# print the JSON string representation of the object
print(LabelCreatedResponse.to_json())

# convert the object into a dict
label_created_response_dict = label_created_response_instance.to_dict()
# create an instance of LabelCreatedResponse from a dict
label_created_response_from_dict = LabelCreatedResponse.from_dict(label_created_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


