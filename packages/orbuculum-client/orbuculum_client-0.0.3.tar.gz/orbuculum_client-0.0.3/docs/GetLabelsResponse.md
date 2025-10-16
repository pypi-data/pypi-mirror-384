# GetLabelsResponse

Response containing label data

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**data** | [**List[Label]**](Label.md) | Array of labels | [optional] 

## Example

```python
from orbuculum_client.models.get_labels_response import GetLabelsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetLabelsResponse from a JSON string
get_labels_response_instance = GetLabelsResponse.from_json(json)
# print the JSON string representation of the object
print(GetLabelsResponse.to_json())

# convert the object into a dict
get_labels_response_dict = get_labels_response_instance.to_dict()
# create an instance of GetLabelsResponse from a dict
get_labels_response_from_dict = GetLabelsResponse.from_dict(get_labels_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


