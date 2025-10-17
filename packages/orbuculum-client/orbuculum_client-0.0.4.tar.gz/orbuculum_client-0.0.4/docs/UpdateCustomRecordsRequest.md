# UpdateCustomRecordsRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID where the custom table exists | 
**table_name** | **str** | Custom table name (prefix &#39;c_&#39; will be added automatically if not present) | 
**query_column** | **str** | Column name to identify which record(s) to update (usually &#39;id&#39;) | 
**query_value** | **object** | Value to match in query_column to find the record(s) to update | 
**record_data** | **Dict[str, object]** | Key-value pairs of columns to update. Keys are column names, values are new data. | 

## Example

```python
from orbuculum_client.models.update_custom_records_request import UpdateCustomRecordsRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateCustomRecordsRequest from a JSON string
update_custom_records_request_instance = UpdateCustomRecordsRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateCustomRecordsRequest.to_json())

# convert the object into a dict
update_custom_records_request_dict = update_custom_records_request_instance.to_dict()
# create an instance of UpdateCustomRecordsRequest from a dict
update_custom_records_request_from_dict = UpdateCustomRecordsRequest.from_dict(update_custom_records_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


