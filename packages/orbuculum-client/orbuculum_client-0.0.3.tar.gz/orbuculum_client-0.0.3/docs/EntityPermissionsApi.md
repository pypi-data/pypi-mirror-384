# orbuculum_client.EntityPermissionsApi

All URIs are relative to *https://s1.orbuculum.app*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_entity_permission**](EntityPermissionsApi.md#create_entity_permission) | **POST** /api/permission/entity-create | Create entity permission
[**delete_entity_permission**](EntityPermissionsApi.md#delete_entity_permission) | **DELETE** /api/permission/entity-delete | Delete entity permission
[**get_entity_permissions**](EntityPermissionsApi.md#get_entity_permissions) | **GET** /api/permission/entity | Get entity permissions


# **create_entity_permission**
> PermissionCreatedResponse create_entity_permission(create_entity_permission_request)

Create entity permission

Creates new permission settings for an entity, defining access levels for users or roles

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.create_entity_permission_request import CreateEntityPermissionRequest
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
    api_instance = orbuculum_client.EntityPermissionsApi(api_client)
    create_entity_permission_request = orbuculum_client.CreateEntityPermissionRequest() # CreateEntityPermissionRequest | 

    try:
        # Create entity permission
        api_response = api_instance.create_entity_permission(create_entity_permission_request)
        print("The response of EntityPermissionsApi->create_entity_permission:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EntityPermissionsApi->create_entity_permission: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_entity_permission_request** | [**CreateEntityPermissionRequest**](CreateEntityPermissionRequest.md)|  | 

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
**201** | Entity permission created successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_entity_permission**
> SuccessResponse delete_entity_permission(delete_entity_permission_request)

Delete entity permission

Removes permission settings for an entity, revoking access for specified users or roles

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.delete_entity_permission_request import DeleteEntityPermissionRequest
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
    api_instance = orbuculum_client.EntityPermissionsApi(api_client)
    delete_entity_permission_request = orbuculum_client.DeleteEntityPermissionRequest() # DeleteEntityPermissionRequest | 

    try:
        # Delete entity permission
        api_response = api_instance.delete_entity_permission(delete_entity_permission_request)
        print("The response of EntityPermissionsApi->delete_entity_permission:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EntityPermissionsApi->delete_entity_permission: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **delete_entity_permission_request** | [**DeleteEntityPermissionRequest**](DeleteEntityPermissionRequest.md)|  | 

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
**200** | Entity permission deleted successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**404** | Resource not found |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_entity_permissions**
> GetEntityPermissionsResponse get_entity_permissions(workspace_id, entity_id=entity_id, role_id=role_id)

Get entity permissions

Retrieves permissions for entities including read, write, and delete access levels

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.get_entity_permissions_response import GetEntityPermissionsResponse
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
    api_instance = orbuculum_client.EntityPermissionsApi(api_client)
    workspace_id = 1 # int | Workspace ID
    entity_id = 1 # int | Specific entity ID to get permissions for (optional)
    role_id = 1 # int | Role ID to filter permissions (optional)

    try:
        # Get entity permissions
        api_response = api_instance.get_entity_permissions(workspace_id, entity_id=entity_id, role_id=role_id)
        print("The response of EntityPermissionsApi->get_entity_permissions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EntityPermissionsApi->get_entity_permissions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **int**| Workspace ID | 
 **entity_id** | **int**| Specific entity ID to get permissions for | [optional] 
 **role_id** | **int**| Role ID to filter permissions | [optional] 

### Return type

[**GetEntityPermissionsResponse**](GetEntityPermissionsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Entity permissions retrieved successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

