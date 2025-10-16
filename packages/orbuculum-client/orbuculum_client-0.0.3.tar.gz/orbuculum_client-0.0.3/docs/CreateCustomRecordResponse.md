# CreateCustomRecordResponse

Response after creating a custom record

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**message** | **str** | Success message | [optional] 
**result** | **int** | Number of affected rows | [optional] 

## Example

```python
from orbuculum_client.models.create_custom_record_response import CreateCustomRecordResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CreateCustomRecordResponse from a JSON string
create_custom_record_response_instance = CreateCustomRecordResponse.from_json(json)
# print the JSON string representation of the object
print(CreateCustomRecordResponse.to_json())

# convert the object into a dict
create_custom_record_response_dict = create_custom_record_response_instance.to_dict()
# create an instance of CreateCustomRecordResponse from a dict
create_custom_record_response_from_dict = CreateCustomRecordResponse.from_dict(create_custom_record_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


