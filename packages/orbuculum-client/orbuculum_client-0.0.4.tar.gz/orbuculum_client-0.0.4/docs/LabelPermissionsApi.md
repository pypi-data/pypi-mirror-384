# orbuculum_client.LabelPermissionsApi

All URIs are relative to *https://s1.orbuculum.app*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_label_permission**](LabelPermissionsApi.md#create_label_permission) | **POST** /api/permission/label-create | Create label permission
[**delete_label_permission**](LabelPermissionsApi.md#delete_label_permission) | **DELETE** /api/permission/label-delete | Delete label permission
[**get_label_permissions**](LabelPermissionsApi.md#get_label_permissions) | **GET** /api/permission/label | Get label permissions


# **create_label_permission**
> PermissionCreatedResponse create_label_permission(create_label_permission_request)

Create label permission

Creates new permission settings for a label, defining access levels for users or roles

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.create_label_permission_request import CreateLabelPermissionRequest
from orbuculum_client.models.permission_created_response import PermissionCreatedResponse
from orbuculum_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://s1.orbuculum.app
# See configuration.py for a list of all supported configuration parameters.
configuration = orbuculum_client.Configuration(
    host = "https://s1.orbuculum.app"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = orbuculum_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with orbuculum_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = orbuculum_client.LabelPermissionsApi(api_client)
    create_label_permission_request = orbuculum_client.CreateLabelPermissionRequest() # CreateLabelPermissionRequest | 

    try:
        # Create label permission
        api_response = api_instance.create_label_permission(create_label_permission_request)
        print("The response of LabelPermissionsApi->create_label_permission:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LabelPermissionsApi->create_label_permission: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_label_permission_request** | [**CreateLabelPermissionRequest**](CreateLabelPermissionRequest.md)|  | 

### Return type

[**PermissionCreatedResponse**](PermissionCreatedResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Label permission created successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_label_permission**
> SuccessResponse delete_label_permission(delete_label_permission_request)

Delete label permission

Removes permission settings for a label, revoking access for specified users or roles

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.delete_label_permission_request import DeleteLabelPermissionRequest
from orbuculum_client.models.success_response import SuccessResponse
from orbuculum_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://s1.orbuculum.app
# See configuration.py for a list of all supported configuration parameters.
configuration = orbuculum_client.Configuration(
    host = "https://s1.orbuculum.app"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = orbuculum_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with orbuculum_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = orbuculum_client.LabelPermissionsApi(api_client)
    delete_label_permission_request = orbuculum_client.DeleteLabelPermissionRequest() # DeleteLabelPermissionRequest | 

    try:
        # Delete label permission
        api_response = api_instance.delete_label_permission(delete_label_permission_request)
        print("The response of LabelPermissionsApi->delete_label_permission:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LabelPermissionsApi->delete_label_permission: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **delete_label_permission_request** | [**DeleteLabelPermissionRequest**](DeleteLabelPermissionRequest.md)|  | 

### Return type

[**SuccessResponse**](SuccessResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Label permission deleted successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**404** | Resource not found |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_label_permissions**
> GetLabelPermissionsResponse get_label_permissions(workspace_id, project_id=project_id, role_id=role_id, account_id=account_id)

Get label permissions

Retrieves permissions for labels including access levels and management rights

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.get_label_permissions_response import GetLabelPermissionsResponse
from orbuculum_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://s1.orbuculum.app
# See configuration.py for a list of all supported configuration parameters.
configuration = orbuculum_client.Configuration(
    host = "https://s1.orbuculum.app"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = orbuculum_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with orbuculum_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = orbuculum_client.LabelPermissionsApi(api_client)
    workspace_id = 1 # int | Workspace ID
    project_id = 1 # int | Specific project ID to get permissions for (optional)
    role_id = 1 # int | Role ID to filter permissions (optional)
    account_id = 1 # int | Account ID to filter permissions (optional)

    try:
        # Get label permissions
        api_response = api_instance.get_label_permissions(workspace_id, project_id=project_id, role_id=role_id, account_id=account_id)
        print("The response of LabelPermissionsApi->get_label_permissions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LabelPermissionsApi->get_label_permissions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **int**| Workspace ID | 
 **project_id** | **int**| Specific project ID to get permissions for | [optional] 
 **role_id** | **int**| Role ID to filter permissions | [optional] 
 **account_id** | **int**| Account ID to filter permissions | [optional] 

### Return type

[**GetLabelPermissionsResponse**](GetLabelPermissionsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Label permissions retrieved successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

