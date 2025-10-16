# ErrorResponse401

Unauthorized error response - invalid or expired authentication token. May optionally include additional 'message' field with detailed error information for debugging purposes.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | 
**error** | **str** | Error message describing authentication failure | 

## Example

```python
from orbuculum_client.models.error_response401 import ErrorResponse401

# TODO update the JSON string below
json = "{}"
# create an instance of ErrorResponse401 from a JSON string
error_response401_instance = ErrorResponse401.from_json(json)
# print the JSON string representation of the object
print(ErrorResponse401.to_json())

# convert the object into a dict
error_response401_dict = error_response401_instance.to_dict()
# create an instance of ErrorResponse401 from a dict
error_response401_from_dict = ErrorResponse401.from_dict(error_response401_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


