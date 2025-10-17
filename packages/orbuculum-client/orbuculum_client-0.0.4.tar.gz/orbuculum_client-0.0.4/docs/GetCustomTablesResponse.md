# GetCustomTablesResponse

Response containing list of custom tables with their structures

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**message** | **str** | Success message | [optional] 
**data** | [**List[CustomTableInfo]**](CustomTableInfo.md) | Array of custom table information | [optional] 

## Example

```python
from orbuculum_client.models.get_custom_tables_response import GetCustomTablesResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetCustomTablesResponse from a JSON string
get_custom_tables_response_instance = GetCustomTablesResponse.from_json(json)
# print the JSON string representation of the object
print(GetCustomTablesResponse.to_json())

# convert the object into a dict
get_custom_tables_response_dict = get_custom_tables_response_instance.to_dict()
# create an instance of GetCustomTablesResponse from a dict
get_custom_tables_response_from_dict = GetCustomTablesResponse.from_dict(get_custom_tables_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


