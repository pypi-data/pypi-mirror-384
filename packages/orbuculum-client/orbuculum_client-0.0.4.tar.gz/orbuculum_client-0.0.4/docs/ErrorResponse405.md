# ErrorResponse405

Method not allowed error response - the HTTP method used is not supported for this endpoint. The response includes the allowed methods in the 'Allow' header.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | 
**error** | **str** | Error message indicating which HTTP method is expected | 

## Example

```python
from orbuculum_client.models.error_response405 import ErrorResponse405

# TODO update the JSON string below
json = "{}"
# create an instance of ErrorResponse405 from a JSON string
error_response405_instance = ErrorResponse405.from_json(json)
# print the JSON string representation of the object
print(ErrorResponse405.to_json())

# convert the object into a dict
error_response405_dict = error_response405_instance.to_dict()
# create an instance of ErrorResponse405 from a dict
error_response405_from_dict = ErrorResponse405.from_dict(error_response405_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


