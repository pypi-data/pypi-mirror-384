# ErrorResponse500

Internal server error response - unexpected error occurred during request processing. This is a catch-all error that indicates something went wrong on the server side.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | 
**error** | **str** | Error message describing what went wrong | 

## Example

```python
from orbuculum_client.models.error_response500 import ErrorResponse500

# TODO update the JSON string below
json = "{}"
# create an instance of ErrorResponse500 from a JSON string
error_response500_instance = ErrorResponse500.from_json(json)
# print the JSON string representation of the object
print(ErrorResponse500.to_json())

# convert the object into a dict
error_response500_dict = error_response500_instance.to_dict()
# create an instance of ErrorResponse500 from a dict
error_response500_from_dict = ErrorResponse500.from_dict(error_response500_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


