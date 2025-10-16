# UpdateCustomRecordsResponse

Response after updating custom records

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**message** | **str** | Success message | [optional] 
**result** | **int** | Number of affected rows | [optional] 

## Example

```python
from orbuculum_client.models.update_custom_records_response import UpdateCustomRecordsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateCustomRecordsResponse from a JSON string
update_custom_records_response_instance = UpdateCustomRecordsResponse.from_json(json)
# print the JSON string representation of the object
print(UpdateCustomRecordsResponse.to_json())

# convert the object into a dict
update_custom_records_response_dict = update_custom_records_response_instance.to_dict()
# create an instance of UpdateCustomRecordsResponse from a dict
update_custom_records_response_from_dict = UpdateCustomRecordsResponse.from_dict(update_custom_records_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


