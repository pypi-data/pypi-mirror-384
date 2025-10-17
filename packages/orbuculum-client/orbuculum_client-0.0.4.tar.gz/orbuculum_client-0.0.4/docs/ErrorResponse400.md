# ErrorResponse400

Bad request error response - validation failed or required parameter missing. May optionally include additional 'message' field with detailed error information for debugging purposes.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | 
**error** | **str** | Error message describing validation failure | 

## Example

```python
from orbuculum_client.models.error_response400 import ErrorResponse400

# TODO update the JSON string below
json = "{}"
# create an instance of ErrorResponse400 from a JSON string
error_response400_instance = ErrorResponse400.from_json(json)
# print the JSON string representation of the object
print(ErrorResponse400.to_json())

# convert the object into a dict
error_response400_dict = error_response400_instance.to_dict()
# create an instance of ErrorResponse400 from a dict
error_response400_from_dict = ErrorResponse400.from_dict(error_response400_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


