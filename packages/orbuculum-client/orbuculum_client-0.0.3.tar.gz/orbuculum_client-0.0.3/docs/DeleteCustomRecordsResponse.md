# DeleteCustomRecordsResponse

Response after deleting custom records

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**message** | **str** | Success message | [optional] 
**data** | **object** | Result of delete operation | [optional] 

## Example

```python
from orbuculum_client.models.delete_custom_records_response import DeleteCustomRecordsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of DeleteCustomRecordsResponse from a JSON string
delete_custom_records_response_instance = DeleteCustomRecordsResponse.from_json(json)
# print the JSON string representation of the object
print(DeleteCustomRecordsResponse.to_json())

# convert the object into a dict
delete_custom_records_response_dict = delete_custom_records_response_instance.to_dict()
# create an instance of DeleteCustomRecordsResponse from a dict
delete_custom_records_response_from_dict = DeleteCustomRecordsResponse.from_dict(delete_custom_records_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


