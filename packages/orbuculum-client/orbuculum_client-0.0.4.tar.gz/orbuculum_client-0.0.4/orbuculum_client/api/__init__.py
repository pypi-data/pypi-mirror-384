# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from orbuculum_client.api.account_api import AccountApi
    from orbuculum_client.api.account_permissions_api import AccountPermissionsApi
    from orbuculum_client.api.authentication_api import AuthenticationApi
    from orbuculum_client.api.custom_api import CustomApi
    from orbuculum_client.api.entity_permissions_api import EntityPermissionsApi
    from orbuculum_client.api.label_api import LabelApi
    from orbuculum_client.api.label_permissions_api import LabelPermissionsApi
    from orbuculum_client.api.limitation_api import LimitationApi
    from orbuculum_client.api.transaction_api import TransactionApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from orbuculum_client.api.account_api import AccountApi
from orbuculum_client.api.account_permissions_api import AccountPermissionsApi
from orbuculum_client.api.authentication_api import AuthenticationApi
from orbuculum_client.api.custom_api import CustomApi
from orbuculum_client.api.entity_permissions_api import EntityPermissionsApi
from orbuculum_client.api.label_api import LabelApi
from orbuculum_client.api.label_permissions_api import LabelPermissionsApi
from orbuculum_client.api.limitation_api import LimitationApi
from orbuculum_client.api.transaction_api import TransactionApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
