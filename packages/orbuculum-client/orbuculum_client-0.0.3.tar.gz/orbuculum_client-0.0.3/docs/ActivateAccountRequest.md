# ActivateAccountRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 

## Example

```python
from orbuculum_client.models.activate_account_request import ActivateAccountRequest

# TODO update the JSON string below
json = "{}"
# create an instance of ActivateAccountRequest from a JSON string
activate_account_request_instance = ActivateAccountRequest.from_json(json)
# print the JSON string representation of the object
print(ActivateAccountRequest.to_json())

# convert the object into a dict
activate_account_request_dict = activate_account_request_instance.to_dict()
# create an instance of ActivateAccountRequest from a dict
activate_account_request_from_dict = ActivateAccountRequest.from_dict(activate_account_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


