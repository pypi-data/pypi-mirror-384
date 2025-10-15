from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ..._jsii import *


@jsii.enum(jsii_type="@cdklabs/generative-ai-cdk-constructs.kendra.Kendra.Edition")
class Edition(enum.Enum):
    '''(experimental) Represents an Amazon Kendra Index Edition.

    :stability: experimental
    '''

    DEVELOPER_EDITION = "DEVELOPER_EDITION"
    '''
    :stability: experimental
    '''
    ENTERPRISE_EDITION = "ENTERPRISE_EDITION"
    '''
    :stability: experimental
    '''
    GEN_AI_ENTERPRISE_EDITION = "GEN_AI_ENTERPRISE_EDITION"
    '''
    :stability: experimental
    '''


@jsii.enum(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.kendra.Kendra.IndexFieldTypes"
)
class IndexFieldTypes(enum.Enum):
    '''(experimental) Represents an Amazon Kendra Index Field Type.

    :stability: experimental
    '''

    STRING = "STRING"
    '''
    :stability: experimental
    '''
    STRING_LIST = "STRING_LIST"
    '''
    :stability: experimental
    '''
    LONG = "LONG"
    '''
    :stability: experimental
    '''
    DATE = "DATE"
    '''
    :stability: experimental
    '''


@jsii.enum(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.kendra.Kendra.UserContextPolicy"
)
class UserContextPolicy(enum.Enum):
    '''(experimental) The different policies available to filter search results based on user context.

    :stability: experimental
    '''

    ATTRIBUTE_FILTER = "ATTRIBUTE_FILTER"
    '''(experimental) All indexed content is searchable and displayable for all users.

    If you want to filter search results on user context, you can use
    the attribute filters of _user_id and _group_ids or you can provide
    user and group information in UserContext .

    :stability: experimental
    '''
    USER_TOKEN = "USER_TOKEN"
    '''(experimental) Enables token-based user access control to filter search results on user context.

    All documents with no access control and all documents
    accessible to the user will be searchable and displayable.

    :stability: experimental
    '''


__all__ = [
    "Edition",
    "IndexFieldTypes",
    "UserContextPolicy",
]

publication.publish()
