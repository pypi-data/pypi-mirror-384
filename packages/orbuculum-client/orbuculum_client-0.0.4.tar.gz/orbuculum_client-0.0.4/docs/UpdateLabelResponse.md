# UpdateLabelResponse

Response after updating a label

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**message** | **str** | Success message | [optional] 
**data** | [**UpdateLabelResponseData**](UpdateLabelResponseData.md) |  | [optional] 

## Example

```python
from orbuculum_client.models.update_label_response import UpdateLabelResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateLabelResponse from a JSON string
update_label_response_instance = UpdateLabelResponse.from_json(json)
# print the JSON string representation of the object
print(UpdateLabelResponse.to_json())

# convert the object into a dict
update_label_response_dict = update_label_response_instance.to_dict()
# create an instance of UpdateLabelResponse from a dict
update_label_response_from_dict = UpdateLabelResponse.from_dict(update_label_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


