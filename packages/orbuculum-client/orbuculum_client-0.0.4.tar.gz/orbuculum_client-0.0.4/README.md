# Orbuculum Python Client

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python client library for the [Orbuculum API](https://s1.orbuculum.app/swagger) - accounting and finance automation platform.

## 📦 Package Information

- **PyPI Package**: `orbuculum-client`
- **Import Name**: `orbuculum_client`
- **Client Version**: 0.0.1
- **Supported API Version**: 0.4.0
- **Python**: 3.9+

This package is automatically generated from the OpenAPI specification using [OpenAPI Generator](https://openapi-generator.tech) 7.15.0.

---

## 🚀 Quick Start

### Installation

```bash
pip install orbuculum-client
```

Or install from source:
```bash
pip install git+https://github.com/orbuculum-app/orbuculum-python-client.git
```

### Basic Usage

```python
import orbuculum_client
from orbuculum_client.rest import ApiException
import os

# Configure API client
configuration = orbuculum_client.Configuration(
    host = "https://s1.orbuculum.app",
    access_token = os.environ["BEARER_TOKEN"]  # JWT token
)

# Use the API
with orbuculum_client.ApiClient(configuration) as api_client:
    # Create API instance
    api_instance = orbuculum_client.AccountApi(api_client)
    
    try:
        # Get account details
        response = api_instance.get_account(id=1)
        print(response)
    except ApiException as e:
        print(f"Error: {e}")
```

---

## 📚 Documentation

### For Users

- **[Installation & Usage](#installation)** - Get started quickly
- **[API Endpoints](#documentation-for-api-endpoints)** - Available API methods
- **[Models](#documentation-for-models)** - Data structures
- **[Authentication](#documentation-for-authorization)** - How to authenticate

### For Developers

- **[DOCKER.md](DOCKER.md)** - Docker-based development workflow ⚠️ **Required for all operations**
- **[API_UPDATES.md](API_UPDATES.md)** - How to update client from API changes
- **[PUBLISHING.md](PUBLISHING.md)** - Complete publishing guide to PyPI
- **[QUICK_PUBLISH_GUIDE.md](QUICK_PUBLISH_GUIDE.md)** - Quick reference for publishing
- **[VERSIONING.md](VERSIONING.md)** - Version management and SemVer policy

---

## ⚠️ Important: Docker-Only Development

**All development, build, and publishing operations MUST be performed inside Docker containers.**

```bash
# Update from API
docker-compose run --rm updater

# Build package
docker-compose run --rm builder

# Run tests
docker-compose run --rm dev pytest

# Publish to PyPI
docker-compose run --rm publisher pypi

# Publish to TestPyPI
docker-compose run --rm publisher testpypi
```

See [DOCKER.md](DOCKER.md) for complete details.

---

## 🔧 Development Workflow

### 1. Update API Client

When the API specification changes:

```bash
docker-compose run --rm updater
```

See [API_UPDATES.md](API_UPDATES.md) for details.

### 2. Run Tests

```bash
docker-compose run --rm dev pytest
```

### 3. Build Package

```bash
docker-compose run --rm builder
```

### 4. Publish

```bash
# Test on TestPyPI first
docker-compose run --rm publisher testpypi

# Then publish to PyPI
docker-compose run --rm publisher pypi
```

See [PUBLISHING.md](PUBLISHING.md) for complete publishing workflow.

---

## 📋 Requirements

- **Python**: 3.9 or higher
- **Docker**: For all development operations (required)
- **Dependencies**:
  - `urllib3>=2.1.0,<3.0.0`
  - `python-dateutil>=2.8.2`
  - `pydantic>=2`
  - `typing-extensions>=4.7.1`
  - `lazy-imports>=1,<2`

---

## Getting Started

Please follow the [installation procedure](#installation--usage) and then run the following:

```python

import orbuculum_client
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
    api_instance = orbuculum_client.AccountApi(api_client)
    id = 1 # int | Account ID to activate
    activate_account_request = orbuculum_client.ActivateAccountRequest() # ActivateAccountRequest | 

    try:
        # Activate an existing account
        api_response = api_instance.activate_account(id, activate_account_request)
        print("The response of AccountApi->activate_account:\n")
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling AccountApi->activate_account: %s\n" % e)

```

## Documentation for API Endpoints

All URIs are relative to *https://s1.orbuculum.app*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*AccountApi* | [**activate_account**](docs/AccountApi.md#activate_account) | **POST** /api/account/activate | Activate an existing account
*AccountApi* | [**create_account**](docs/AccountApi.md#create_account) | **POST** /api/account/create | Create a new account
*AccountApi* | [**delete_account**](docs/AccountApi.md#delete_account) | **DELETE** /api/account/delete | Delete an existing account
*AccountApi* | [**get_account**](docs/AccountApi.md#get_account) | **GET** /api/account/get | Get account details
*AccountApi* | [**update_account**](docs/AccountApi.md#update_account) | **POST** /api/account/update | Update an existing account
*AccountPermissionsApi* | [**create_account_permission**](docs/AccountPermissionsApi.md#create_account_permission) | **POST** /api/permission/account-create | Create account permission
*AccountPermissionsApi* | [**delete_account_permission**](docs/AccountPermissionsApi.md#delete_account_permission) | **DELETE** /api/permission/account-delete | Delete account permission
*AccountPermissionsApi* | [**edit_account_permission**](docs/AccountPermissionsApi.md#edit_account_permission) | **POST** /api/permission/account-edit | Permission to edit account
*AccountPermissionsApi* | [**get_account_permissions**](docs/AccountPermissionsApi.md#get_account_permissions) | **GET** /api/permission/account | Get account permissions
*AuthenticationApi* | [**login**](docs/AuthenticationApi.md#login) | **POST** /api/auth/login | Login and get JWT token
*CustomApi* | [**create_custom_record**](docs/CustomApi.md#create_custom_record) | **POST** /api/custom/create | Create a record in custom table
*CustomApi* | [**delete_custom_records**](docs/CustomApi.md#delete_custom_records) | **POST** /api/custom/delete | Delete records from custom table
*CustomApi* | [**get_custom_tables**](docs/CustomApi.md#get_custom_tables) | **GET** /api/custom/tables | Get list of custom tables
*CustomApi* | [**read_custom_records**](docs/CustomApi.md#read_custom_records) | **GET** /api/custom/read | Read records from custom table
*CustomApi* | [**update_custom_records**](docs/CustomApi.md#update_custom_records) | **POST** /api/custom/update | Update records in custom table
*EntityPermissionsApi* | [**create_entity_permission**](docs/EntityPermissionsApi.md#create_entity_permission) | **POST** /api/permission/entity-create | Create entity permission
*EntityPermissionsApi* | [**delete_entity_permission**](docs/EntityPermissionsApi.md#delete_entity_permission) | **DELETE** /api/permission/entity-delete | Delete entity permission
*EntityPermissionsApi* | [**get_entity_permissions**](docs/EntityPermissionsApi.md#get_entity_permissions) | **GET** /api/permission/entity | Get entity permissions
*LabelApi* | [**create_label**](docs/LabelApi.md#create_label) | **POST** /api/label/create | Create label
*LabelApi* | [**delete_label**](docs/LabelApi.md#delete_label) | **DELETE** /api/label/delete | Delete an existing label
*LabelApi* | [**get_label**](docs/LabelApi.md#get_label) | **GET** /api/label/get | Get label
*LabelApi* | [**update_label**](docs/LabelApi.md#update_label) | **POST** /api/label/update | Update label
*LabelPermissionsApi* | [**create_label_permission**](docs/LabelPermissionsApi.md#create_label_permission) | **POST** /api/permission/label-create | Create label permission
*LabelPermissionsApi* | [**delete_label_permission**](docs/LabelPermissionsApi.md#delete_label_permission) | **DELETE** /api/permission/label-delete | Delete label permission
*LabelPermissionsApi* | [**get_label_permissions**](docs/LabelPermissionsApi.md#get_label_permissions) | **GET** /api/permission/label | Get label permissions
*LimitationApi* | [**get_limitation**](docs/LimitationApi.md#get_limitation) | **GET** /api/limitation/get | Get transaction limitations for an account
*LimitationApi* | [**manage_account_limitation**](docs/LimitationApi.md#manage_account_limitation) | **POST** /api/limitation/account-manage | Manage account transaction limitations
*LimitationApi* | [**manage_entity_limitation**](docs/LimitationApi.md#manage_entity_limitation) | **POST** /api/limitation/entity-manage | Manage entity transaction limitations
*TransactionApi* | [**add_transaction_commission**](docs/TransactionApi.md#add_transaction_commission) | **POST** /api/transaction/add-commission | Add commission to a transaction
*TransactionApi* | [**create_transaction**](docs/TransactionApi.md#create_transaction) | **POST** /api/transaction/create | Create a new transaction
*TransactionApi* | [**delete_transaction**](docs/TransactionApi.md#delete_transaction) | **DELETE** /api/transaction/delete | Delete an existing transaction
*TransactionApi* | [**get_transaction**](docs/TransactionApi.md#get_transaction) | **GET** /api/transaction/get | Get transaction details
*TransactionApi* | [**update_transaction**](docs/TransactionApi.md#update_transaction) | **POST** /api/transaction/update | Update an existing transaction


## Documentation For Models

 - [Account](docs/Account.md)
 - [AccountCreatedResponse](docs/AccountCreatedResponse.md)
 - [AccountPermission](docs/AccountPermission.md)
 - [ActivateAccountRequest](docs/ActivateAccountRequest.md)
 - [AddCommissionRequest](docs/AddCommissionRequest.md)
 - [ColumnInfo](docs/ColumnInfo.md)
 - [CommissionCreatedResponse](docs/CommissionCreatedResponse.md)
 - [CommissionData](docs/CommissionData.md)
 - [CreateAccountPermissionRequest](docs/CreateAccountPermissionRequest.md)
 - [CreateAccountRequest](docs/CreateAccountRequest.md)
 - [CreateCustomRecordRequest](docs/CreateCustomRecordRequest.md)
 - [CreateCustomRecordResponse](docs/CreateCustomRecordResponse.md)
 - [CreateEntityPermissionRequest](docs/CreateEntityPermissionRequest.md)
 - [CreateLabelPermissionRequest](docs/CreateLabelPermissionRequest.md)
 - [CreateLabelRequest](docs/CreateLabelRequest.md)
 - [CreateTransactionRequest](docs/CreateTransactionRequest.md)
 - [CustomTableInfo](docs/CustomTableInfo.md)
 - [CustomValue](docs/CustomValue.md)
 - [DeleteCustomRecordsRequest](docs/DeleteCustomRecordsRequest.md)
 - [DeleteCustomRecordsResponse](docs/DeleteCustomRecordsResponse.md)
 - [DeleteEntityPermissionRequest](docs/DeleteEntityPermissionRequest.md)
 - [DeleteLabelPermissionRequest](docs/DeleteLabelPermissionRequest.md)
 - [DeleteTransactionRequest](docs/DeleteTransactionRequest.md)
 - [EditAccountPermissionRequest](docs/EditAccountPermissionRequest.md)
 - [EntityPermission](docs/EntityPermission.md)
 - [ErrorResponse](docs/ErrorResponse.md)
 - [ErrorResponse400](docs/ErrorResponse400.md)
 - [ErrorResponse401](docs/ErrorResponse401.md)
 - [ErrorResponse403](docs/ErrorResponse403.md)
 - [ErrorResponse404](docs/ErrorResponse404.md)
 - [ErrorResponse405](docs/ErrorResponse405.md)
 - [ErrorResponse500](docs/ErrorResponse500.md)
 - [GetAccountPermissionsResponse](docs/GetAccountPermissionsResponse.md)
 - [GetAccountResponse](docs/GetAccountResponse.md)
 - [GetCustomTablesResponse](docs/GetCustomTablesResponse.md)
 - [GetEntityPermissionsResponse](docs/GetEntityPermissionsResponse.md)
 - [GetLabelPermissionsResponse](docs/GetLabelPermissionsResponse.md)
 - [GetLabelsResponse](docs/GetLabelsResponse.md)
 - [GetLimitationsResponse](docs/GetLimitationsResponse.md)
 - [Label](docs/Label.md)
 - [LabelCreatedResponse](docs/LabelCreatedResponse.md)
 - [LabelCreatedResponseData](docs/LabelCreatedResponseData.md)
 - [LabelPermission](docs/LabelPermission.md)
 - [Limitation](docs/Limitation.md)
 - [LimitationManagedResponse](docs/LimitationManagedResponse.md)
 - [LoginRequest](docs/LoginRequest.md)
 - [LoginResponse](docs/LoginResponse.md)
 - [ManageAccountLimitationRequest](docs/ManageAccountLimitationRequest.md)
 - [ManageEntityLimitationRequest](docs/ManageEntityLimitationRequest.md)
 - [PaginationMeta](docs/PaginationMeta.md)
 - [PermissionCreatedResponse](docs/PermissionCreatedResponse.md)
 - [ReadCustomRecordsResponse](docs/ReadCustomRecordsResponse.md)
 - [SuccessResponse](docs/SuccessResponse.md)
 - [Transaction](docs/Transaction.md)
 - [TransactionCreatedData](docs/TransactionCreatedData.md)
 - [TransactionCreatedResponse](docs/TransactionCreatedResponse.md)
 - [TransactionListResponse](docs/TransactionListResponse.md)
 - [UpdateAccountRequest](docs/UpdateAccountRequest.md)
 - [UpdateCustomRecordsRequest](docs/UpdateCustomRecordsRequest.md)
 - [UpdateCustomRecordsResponse](docs/UpdateCustomRecordsResponse.md)
 - [UpdateLabelRequest](docs/UpdateLabelRequest.md)
 - [UpdateLabelResponse](docs/UpdateLabelResponse.md)
 - [UpdateLabelResponseData](docs/UpdateLabelResponseData.md)
 - [UpdateTransactionRequest](docs/UpdateTransactionRequest.md)


<a id="documentation-for-authorization"></a>
## Documentation For Authorization


Authentication schemes defined for the API:
<a id="bearerAuth"></a>
### bearerAuth

- **Type**: Bearer authentication (JWT)


## Author

Orbuculum Team <i@orbuculum.app>

---

## 🔄 Version Management

This client follows [Semantic Versioning](https://semver.org/). The client version is **independent** from the API version.

### Current Versions

```python
import orbuculum_client

print(orbuculum_client.__version__)        # Client version: 0.0.1
print(orbuculum_client.__api_version__)    # API version: 0.4.0
print(orbuculum_client.__api_supported__)  # Supported API: 0.4.0
```

### Version Update Guidelines

- **PATCH** (0.0.1 → 0.0.2): Bug fixes, documentation updates
- **MINOR** (0.0.2 → 0.1.0): New features, backward-compatible
- **MAJOR** (0.1.0 → 1.0.0): Breaking changes

See [VERSIONING.md](VERSIONING.md) for complete version management policy.

---

## 🤝 Contributing

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/orbuculum-app/orbuculum-python-client.git
   cd orbuculum-python-client
   ```

2. **Use Docker for all operations** (required)
   ```bash
   # Development shell
   docker-compose run --rm dev
   
   # Run tests
   docker-compose run --rm dev pytest
   ```

3. **Update from API changes**
   ```bash
   docker-compose run --rm updater
   ```

See [DOCKER.md](DOCKER.md) for complete development workflow.

### Project Structure

```
orbuculum-python-client/
├── orbuculum_client/          # Main package (import as orbuculum_client)
│   ├── api/                   # API endpoint classes
│   ├── models/                # Data models
│   └── __init__.py           # Package initialization
├── docs/                      # API documentation (auto-generated)
├── test/                      # Tests
│   ├── generated/            # Auto-generated tests
│   └── custom/               # Custom tests
├── scripts/                   # Build and update scripts
├── docker/                    # Docker configuration
├── dev-notes/                 # Personal development notes (gitignored)
├── pyproject.toml            # Package configuration
├── README.md                 # This file
├── DOCKER.md                 # Docker workflow (required reading)
├── API_UPDATES.md            # API update process
├── PUBLISHING.md             # Publishing guide
├── VERSIONING.md             # Version policy
└── docker-compose.yml        # Docker services
```

---

## 📖 Additional Resources

- **API Documentation**: https://s1.orbuculum.app/swagger
- **OpenAPI Specification**: https://s1.orbuculum.app/swagger/json
- **GitHub Repository**: https://github.com/orbuculum-app/orbuculum-python-client
- **Issue Tracker**: https://github.com/orbuculum-app/orbuculum-python-client/issues

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **Documentation Issues**: Open an issue on GitHub
- **API Questions**: Check the [API documentation](https://s1.orbuculum.app/swagger)
- **Bug Reports**: Use the [issue tracker](https://github.com/orbuculum-app/orbuculum-python-client/issues)

---

