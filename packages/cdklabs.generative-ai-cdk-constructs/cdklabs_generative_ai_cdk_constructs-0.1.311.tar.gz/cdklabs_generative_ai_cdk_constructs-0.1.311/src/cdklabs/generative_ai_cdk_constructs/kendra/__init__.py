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

from .._jsii import *

import aws_cdk as _aws_cdk_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import constructs as _constructs_77d1e7e8
from .kendra import Edition as _Edition_3dadb043


@jsii.interface(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.kendra.IKendraGenAiIndex"
)
class IKendraGenAiIndex(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    '''(experimental) Represents a Kendra Index, either created with CDK or imported.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="indexArn")
    def index_arn(self) -> builtins.str:
        '''(experimental) The Amazon Resource Name (ARN) of the index.

        :stability: experimental

        Example::

            'arn:aws:kendra:us-east-1:123456789012:index/af04c7ea-22bc-46b7-a65e-6c21e604fc11'
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="indexId")
    def index_id(self) -> builtins.str:
        '''(experimental) The identifier of the index.

        :stability: experimental

        Example::

            'af04c7ea-22bc-46b7-a65e-6c21e604fc11'.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) An IAM role that gives Amazon Kendra permissions to access your Amazon CloudWatch logs and metrics.

        This is also the
        role used when you use the BatchPutDocument operation to index
        documents from an Amazon S3 bucket.

        :stability: experimental
        '''
        ...


class _IKendraGenAiIndexProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    '''(experimental) Represents a Kendra Index, either created with CDK or imported.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@cdklabs/generative-ai-cdk-constructs.kendra.IKendraGenAiIndex"

    @builtins.property
    @jsii.member(jsii_name="indexArn")
    def index_arn(self) -> builtins.str:
        '''(experimental) The Amazon Resource Name (ARN) of the index.

        :stability: experimental

        Example::

            'arn:aws:kendra:us-east-1:123456789012:index/af04c7ea-22bc-46b7-a65e-6c21e604fc11'
        '''
        return typing.cast(builtins.str, jsii.get(self, "indexArn"))

    @builtins.property
    @jsii.member(jsii_name="indexId")
    def index_id(self) -> builtins.str:
        '''(experimental) The identifier of the index.

        :stability: experimental

        Example::

            'af04c7ea-22bc-46b7-a65e-6c21e604fc11'.
        '''
        return typing.cast(builtins.str, jsii.get(self, "indexId"))

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) An IAM role that gives Amazon Kendra permissions to access your Amazon CloudWatch logs and metrics.

        This is also the
        role used when you use the BatchPutDocument operation to index
        documents from an Amazon S3 bucket.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "role"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IKendraGenAiIndex).__jsii_proxy_class__ = lambda : _IKendraGenAiIndexProxy


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.kendra.KendraGenAiIndexAttributes",
    jsii_struct_bases=[],
    name_mapping={"index_id": "indexId", "role": "role"},
)
class KendraGenAiIndexAttributes:
    def __init__(
        self,
        *,
        index_id: builtins.str,
        role: _aws_cdk_aws_iam_ceddda9d.IRole,
    ) -> None:
        '''(experimental) Properties needed for importing an existing Kendra Index.

        :param index_id: (experimental) The Id of the index.
        :param role: (experimental) An IAM role that gives your Amazon Kendra index permissions.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__383a16778b57db636cd3f820c0af0595a1c1a0f0a9c94f43627feba671e73c6f)
            check_type(argname="argument index_id", value=index_id, expected_type=type_hints["index_id"])
            check_type(argname="argument role", value=role, expected_type=type_hints["role"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "index_id": index_id,
            "role": role,
        }

    @builtins.property
    def index_id(self) -> builtins.str:
        '''(experimental) The Id of the index.

        :stability: experimental

        Example::

            'af04c7ea-22bc-46b7-a65e-6c21e604fc11'
        '''
        result = self._values.get("index_id")
        assert result is not None, "Required property 'index_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) An IAM role that gives your Amazon Kendra index permissions.

        :stability: experimental
        '''
        result = self._values.get("role")
        assert result is not None, "Required property 'role' is missing"
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "KendraGenAiIndexAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IKendraGenAiIndex)
class KendraGenAiIndexBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.kendra.KendraGenAiIndexBase",
):
    '''(experimental) Abstract base class for a Kendra GenAI index.

    Contains methods and attributes valid for Kendra GenAI Indexes either created with CDK or imported.

    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        environment_from_arn: typing.Optional[builtins.str] = None,
        physical_name: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param account: The AWS account ID this resource belongs to. Default: - the resource is in the same account as the stack it belongs to
        :param environment_from_arn: ARN to deduce region and account from. The ARN is parsed and the account and region are taken from the ARN. This should be used for imported resources. Cannot be supplied together with either ``account`` or ``region``. Default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        :param physical_name: The value passed in by users to the physical name prop of the resource. - ``undefined`` implies that a physical name will be allocated by CloudFormation during deployment. - a concrete value implies a specific physical name - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation. Default: - The physical name will be allocated by CloudFormation at deployment time
        :param region: The AWS region this resource belongs to. Default: - the resource is in the same region as the stack it belongs to
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__57684f89879355f156f1e2afad3d19f2472d77a8339fe1528d4f715cc8ba2f49)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="indexArn")
    @abc.abstractmethod
    def index_arn(self) -> builtins.str:
        '''(experimental) The Amazon Resource Name (ARN) of the index.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="indexId")
    @abc.abstractmethod
    def index_id(self) -> builtins.str:
        '''(experimental) The identifier of the index.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="role")
    @abc.abstractmethod
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) An IAM role that gives Amazon Kendra permissions to access your Amazon CloudWatch logs and metrics.

        This is also the
        role used when you use the BatchPutDocument operation to index
        documents from an Amazon S3 bucket.

        :stability: experimental
        '''
        ...


class _KendraGenAiIndexBaseProxy(
    KendraGenAiIndexBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="indexArn")
    def index_arn(self) -> builtins.str:
        '''(experimental) The Amazon Resource Name (ARN) of the index.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "indexArn"))

    @builtins.property
    @jsii.member(jsii_name="indexId")
    def index_id(self) -> builtins.str:
        '''(experimental) The identifier of the index.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "indexId"))

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) An IAM role that gives Amazon Kendra permissions to access your Amazon CloudWatch logs and metrics.

        This is also the
        role used when you use the BatchPutDocument operation to index
        documents from an Amazon S3 bucket.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "role"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, KendraGenAiIndexBase).__jsii_proxy_class__ = lambda : _KendraGenAiIndexBaseProxy


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.kendra.KendraGenAiIndexProps",
    jsii_struct_bases=[],
    name_mapping={
        "document_capacity_units": "documentCapacityUnits",
        "kms_key": "kmsKey",
        "name": "name",
        "query_capacity_units": "queryCapacityUnits",
    },
)
class KendraGenAiIndexProps:
    def __init__(
        self,
        *,
        document_capacity_units: typing.Optional[jsii.Number] = None,
        kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        name: typing.Optional[builtins.str] = None,
        query_capacity_units: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''(experimental) Properties for creating a GenAI Index.

        :param document_capacity_units: (experimental) The document capacity units. Every unit increases the baseline capacity by 20,000 documents. E.g. ``documentCapacityUnits: 1`` means Baseline + 20,000 documents = 40,000 documents Default: 0 - baseline capacity of 20,000 documents
        :param kms_key: (experimental) The identifier of the AWS KMS customer managed key (CMK) to use to encrypt data indexed by Amazon Kendra. Amazon Kendra doesn't support asymmetric CMKs. Default: - AWS managed encryption key is used.
        :param name: (experimental) The name of the index. Default: - A name is generated by CDK.
        :param query_capacity_units: (experimental) The query capacity units. Every unit increases the baseline capacity by 0.1 QPS. E.g. ``queryCapacityUnits: 7`` means Baseline + 0.1 QPS * 7 = 0.8 QPS Default: 0 - baseline capacity of 0.1 QPS

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__68d05ab6881701c1aa7370932d51436f37ae1c88ae7bab591424729acc1a0c58)
            check_type(argname="argument document_capacity_units", value=document_capacity_units, expected_type=type_hints["document_capacity_units"])
            check_type(argname="argument kms_key", value=kms_key, expected_type=type_hints["kms_key"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument query_capacity_units", value=query_capacity_units, expected_type=type_hints["query_capacity_units"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if document_capacity_units is not None:
            self._values["document_capacity_units"] = document_capacity_units
        if kms_key is not None:
            self._values["kms_key"] = kms_key
        if name is not None:
            self._values["name"] = name
        if query_capacity_units is not None:
            self._values["query_capacity_units"] = query_capacity_units

    @builtins.property
    def document_capacity_units(self) -> typing.Optional[jsii.Number]:
        '''(experimental) The document capacity units.

        Every unit increases the baseline capacity by 20,000 documents.
        E.g. ``documentCapacityUnits: 1`` means Baseline + 20,000 documents = 40,000 documents

        :default: 0 - baseline capacity of 20,000 documents

        :stability: experimental
        '''
        result = self._values.get("document_capacity_units")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) The identifier of the AWS KMS customer managed key (CMK) to use to encrypt data indexed by Amazon Kendra.

        Amazon Kendra doesn't support
        asymmetric CMKs.

        :default: - AWS managed encryption key is used.

        :stability: experimental
        '''
        result = self._values.get("kms_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the index.

        :default: - A name is generated by CDK.

        :stability: experimental
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def query_capacity_units(self) -> typing.Optional[jsii.Number]:
        '''(experimental) The query capacity units.

        Every unit increases the baseline capacity by 0.1 QPS.
        E.g. ``queryCapacityUnits: 7`` means Baseline + 0.1 QPS * 7 = 0.8 QPS

        :default: 0 - baseline capacity of 0.1 QPS

        :stability: experimental
        '''
        result = self._values.get("query_capacity_units")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "KendraGenAiIndexProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class KendraGenAiIndex(
    KendraGenAiIndexBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.kendra.KendraGenAiIndex",
):
    '''(experimental) Class to create a Kendra GenAI Index with CDK.

    :stability: experimental
    :cloudformationResource: AWS::Kendra::Index
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        document_capacity_units: typing.Optional[jsii.Number] = None,
        kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        name: typing.Optional[builtins.str] = None,
        query_capacity_units: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param document_capacity_units: (experimental) The document capacity units. Every unit increases the baseline capacity by 20,000 documents. E.g. ``documentCapacityUnits: 1`` means Baseline + 20,000 documents = 40,000 documents Default: 0 - baseline capacity of 20,000 documents
        :param kms_key: (experimental) The identifier of the AWS KMS customer managed key (CMK) to use to encrypt data indexed by Amazon Kendra. Amazon Kendra doesn't support asymmetric CMKs. Default: - AWS managed encryption key is used.
        :param name: (experimental) The name of the index. Default: - A name is generated by CDK.
        :param query_capacity_units: (experimental) The query capacity units. Every unit increases the baseline capacity by 0.1 QPS. E.g. ``queryCapacityUnits: 7`` means Baseline + 0.1 QPS * 7 = 0.8 QPS Default: 0 - baseline capacity of 0.1 QPS

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__df915b1817a197a8529c9942e2c9ff75dd575b13b41c6abedc5e5b0824e9cc21)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = KendraGenAiIndexProps(
            document_capacity_units=document_capacity_units,
            kms_key=kms_key,
            name=name,
            query_capacity_units=query_capacity_units,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromAttrs")
    @builtins.classmethod
    def from_attrs(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        index_id: builtins.str,
        role: _aws_cdk_aws_iam_ceddda9d.IRole,
    ) -> IKendraGenAiIndex:
        '''(experimental) Import a guardrail given its attributes.

        :param scope: -
        :param id: -
        :param index_id: (experimental) The Id of the index.
        :param role: (experimental) An IAM role that gives your Amazon Kendra index permissions.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0b89851ca17063c3ab454d24c41e23c713de320c3e26c08ceee2d0d29b0837f2)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = KendraGenAiIndexAttributes(index_id=index_id, role=role)

        return typing.cast(IKendraGenAiIndex, jsii.sinvoke(cls, "fromAttrs", [scope, id, attrs]))

    @builtins.property
    @jsii.member(jsii_name="documentCapacityUnits")
    def document_capacity_units(self) -> jsii.Number:
        '''(experimental) The document capacity units used for the Gen AI index.

        :stability: experimental
        '''
        return typing.cast(jsii.Number, jsii.get(self, "documentCapacityUnits"))

    @builtins.property
    @jsii.member(jsii_name="edition")
    def edition(self) -> _Edition_3dadb043:
        '''(experimental) The edition of the Gen AI index.

        :stability: experimental
        '''
        return typing.cast(_Edition_3dadb043, jsii.get(self, "edition"))

    @builtins.property
    @jsii.member(jsii_name="indexArn")
    def index_arn(self) -> builtins.str:
        '''(experimental) The Amazon Resource Name (ARN) of the index.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "indexArn"))

    @builtins.property
    @jsii.member(jsii_name="indexId")
    def index_id(self) -> builtins.str:
        '''(experimental) The identifier of the index.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "indexId"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''(experimental) The name of the Gen AI index.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="queryCapacityUnits")
    def query_capacity_units(self) -> jsii.Number:
        '''(experimental) The query capacity units used for the Gen AI index.

        :stability: experimental
        '''
        return typing.cast(jsii.Number, jsii.get(self, "queryCapacityUnits"))

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        '''(experimental) An IAM role that gives Amazon Kendra permissions to access your Amazon CloudWatch logs and metrics.

        This is also the
        role used when you use the BatchPutDocument operation to index
        documents from an Amazon S3 bucket.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "role"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) The AWS KMS key (CMK) used to encrypt data.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "kmsKey"))


__all__ = [
    "IKendraGenAiIndex",
    "KendraGenAiIndex",
    "KendraGenAiIndexAttributes",
    "KendraGenAiIndexBase",
    "KendraGenAiIndexProps",
    "kendra",
]

publication.publish()

# Loading modules to ensure their types are registered with the jsii runtime library
from . import kendra

def _typecheckingstub__383a16778b57db636cd3f820c0af0595a1c1a0f0a9c94f43627feba671e73c6f(
    *,
    index_id: builtins.str,
    role: _aws_cdk_aws_iam_ceddda9d.IRole,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__57684f89879355f156f1e2afad3d19f2472d77a8339fe1528d4f715cc8ba2f49(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    environment_from_arn: typing.Optional[builtins.str] = None,
    physical_name: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__68d05ab6881701c1aa7370932d51436f37ae1c88ae7bab591424729acc1a0c58(
    *,
    document_capacity_units: typing.Optional[jsii.Number] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    name: typing.Optional[builtins.str] = None,
    query_capacity_units: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__df915b1817a197a8529c9942e2c9ff75dd575b13b41c6abedc5e5b0824e9cc21(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    document_capacity_units: typing.Optional[jsii.Number] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    name: typing.Optional[builtins.str] = None,
    query_capacity_units: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0b89851ca17063c3ab454d24c41e23c713de320c3e26c08ceee2d0d29b0837f2(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    index_id: builtins.str,
    role: _aws_cdk_aws_iam_ceddda9d.IRole,
) -> None:
    """Type checking stubs"""
    pass

for cls in [IKendraGenAiIndex]:
    typing.cast(typing.Any, cls).__protocol_attrs__ = typing.cast(typing.Any, cls).__protocol_attrs__ - set(['__jsii_proxy_class__', '__jsii_type__'])
