# CreateCustomRecordRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID where the custom table exists | 
**table_name** | **str** | Custom table name (prefix &#39;c_&#39; will be added automatically if not present). Example: &#39;clients&#39; becomes &#39;c_clients&#39; | 
**record_data** | **Dict[str, object]** | Key-value pairs where keys are column names in your custom table and values are the data to insert. Column names must match your table schema. | 

## Example

```python
from orbuculum_client.models.create_custom_record_request import CreateCustomRecordRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateCustomRecordRequest from a JSON string
create_custom_record_request_instance = CreateCustomRecordRequest.from_json(json)
# print the JSON string representation of the object
print(CreateCustomRecordRequest.to_json())

# convert the object into a dict
create_custom_record_request_dict = create_custom_record_request_instance.to_dict()
# create an instance of CreateCustomRecordRequest from a dict
create_custom_record_request_from_dict = CreateCustomRecordRequest.from_dict(create_custom_record_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


