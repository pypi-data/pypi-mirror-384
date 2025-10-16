# ErrorResponse404

Not found error response - requested resource does not exist. May optionally include additional 'message' field with detailed error information for debugging purposes.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | 
**error** | **str** | Error message indicating resource not found | 

## Example

```python
from orbuculum_client.models.error_response404 import ErrorResponse404

# TODO update the JSON string below
json = "{}"
# create an instance of ErrorResponse404 from a JSON string
error_response404_instance = ErrorResponse404.from_json(json)
# print the JSON string representation of the object
print(ErrorResponse404.to_json())

# convert the object into a dict
error_response404_dict = error_response404_instance.to_dict()
# create an instance of ErrorResponse404 from a dict
error_response404_from_dict = ErrorResponse404.from_dict(error_response404_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


