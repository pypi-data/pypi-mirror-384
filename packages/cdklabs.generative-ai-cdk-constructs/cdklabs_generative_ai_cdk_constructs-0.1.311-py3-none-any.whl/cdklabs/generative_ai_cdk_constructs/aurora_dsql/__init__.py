r'''
# Amazon Aurora DSQL

<!--BEGIN STABILITY BANNER-->---


![Stability: Experimental](https://img.shields.io/badge/stability-Experimental-important.svg?style=for-the-badge)

> All classes are under active development and subject to non-backward compatible changes or removal in any
> future version. These are not subject to the [Semantic Versioning](https://semver.org/) model.
> This means that while you may use them, you may need to update your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

| **Language**                                                                                   | **Package**                             |
| :--------------------------------------------------------------------------------------------- | --------------------------------------- |
| ![Typescript Logo](https://docs.aws.amazon.com/cdk/api/latest/img/typescript32.png) TypeScript | `@cdklabs/generative-ai-cdk-constructs` |
| ![Python Logo](https://docs.aws.amazon.com/cdk/api/latest/img/python32.png) Python             | `cdklabs.generative_ai_cdk_constructs`  |
| ![.Net](https://docs.aws.amazon.com/cdk/api/latest/img/dotnet32.png) .Net                   | `CdkLabs.GenerativeAICdkConstructs`|
| ![Go](https://docs.aws.amazon.com/cdk/api/latest/img/go32.png) Go                   | `github.com/cdklabs/generative-ai-cdk-constructs-go/generative-ai-cdk-constructs`|

Amazon Aurora DSQL is the fastest serverless distributed SQL database with active-active high availability to help ensure your applications are always available. It ensures all reads and writes to any Regional endpoint are strongly consistent and durable. Moreover, its serverless design makes database management effortless, offering virtually unlimited scalability and zero infrastructure management.

This construct library provides L2 constructs to manage Aurora DSQL resources.

## Table of contents

* [Aurora DSQL cluster](#opensearch-managed-cluster-vector-store)

  * [Cluster properties](#cluster-properties)
  * [Single region cluster](#single-region-cluster)
  * [Multi region cluster](#multi-region-cluster)

## Aurora DSQL Cluster

Aurora DSQL provides several configuration options to help you establish the right database infrastructure for your needs. To set up your Aurora DSQL cluster infrastructure, review the following sections.

### Cluster properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| removalPolicy | RemovalPolicy | No | This option prevents accidental cluster deletion. When set to RETAIN, you can't delete the cluster. By default, RemovalPolicy.DESTROY is applied. |
| kmsKey | IKey | No | A custom KMS key to use for encrypting data. Default: Your data is encrypted by default with a key that AWS owns and manages for you. |
| multiRegionProperties | MultiRegionProperties | No | Structure for multi-Region cluster configurations. Default: single region configuration. |
| tags | Record<string, string> | No | Tags to apply to the cluster. Default: no tags applied. |

### Single region cluster

```python
new auroraDsql.Cluster(stack, 'TestCluster', {});
```

You can use tags on a cluster, for instance:

```python
new auroraDsql.Cluster(this, 'TestCluster', {
    tags: {
        Name: 'TestCluster',
    }
});
```

### Multi region cluster

Multi-Region peered clusters provide the same resilience and connectivity as single-Region clusters. But they improve availability by offering two Regional endpoints, one in each peered cluster Region. Both endpoints of a peered cluster present a single logical database. They are available for concurrent read and write operations, and provide strong data consistency. You can build applications that run in multiple Regions at the same time for performance and resilience—and know that readers always see the same data.

```python
// create a cluster in a different region
const peeredCluster1 = new auroraDsql.Cluster(stack1, 'TestPeeredCluster1', {});

// or load existing cluster through the fromAttributes method

new Cluster(stack3, 'TestCluster', {
    multiRegionProperties: {
        witnessRegion: 'us-east-1',
        clusters: [peeredCluster1],
    },
});
```
'''
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


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.auroraDsql.ClusterAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "cluster_arn": "clusterArn",
        "vpc_endpoint_service_name": "vpcEndpointServiceName",
        "creation_time": "creationTime",
        "encryption_key": "encryptionKey",
        "status": "status",
    },
)
class ClusterAttributes:
    def __init__(
        self,
        *,
        cluster_arn: builtins.str,
        vpc_endpoint_service_name: builtins.str,
        creation_time: typing.Optional[builtins.str] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        status: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Attributes for specifying an imported Aurora DSQL cluster.

        :param cluster_arn: (experimental) The ARN of the cluster.
        :param vpc_endpoint_service_name: (experimental) VpcEndpointServiceName of the cluster.
        :param creation_time: (experimental) The timestamp when the cluster was created, in ISO 8601 format. Default: undefined - No creation time is provided
        :param encryption_key: (experimental) KMS encryption key associated with this cluster. Default: - no encryption key
        :param status: (experimental) The status of the cluster. Default: undefined - No status is provided

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__24de4270819b601d6eb8496aab768698004b05e95e4cc0090c43af71f652d1d5)
            check_type(argname="argument cluster_arn", value=cluster_arn, expected_type=type_hints["cluster_arn"])
            check_type(argname="argument vpc_endpoint_service_name", value=vpc_endpoint_service_name, expected_type=type_hints["vpc_endpoint_service_name"])
            check_type(argname="argument creation_time", value=creation_time, expected_type=type_hints["creation_time"])
            check_type(argname="argument encryption_key", value=encryption_key, expected_type=type_hints["encryption_key"])
            check_type(argname="argument status", value=status, expected_type=type_hints["status"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cluster_arn": cluster_arn,
            "vpc_endpoint_service_name": vpc_endpoint_service_name,
        }
        if creation_time is not None:
            self._values["creation_time"] = creation_time
        if encryption_key is not None:
            self._values["encryption_key"] = encryption_key
        if status is not None:
            self._values["status"] = status

    @builtins.property
    def cluster_arn(self) -> builtins.str:
        '''(experimental) The ARN of the cluster.

        :stability: experimental
        :attribute: true
        '''
        result = self._values.get("cluster_arn")
        assert result is not None, "Required property 'cluster_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def vpc_endpoint_service_name(self) -> builtins.str:
        '''(experimental) VpcEndpointServiceName of the cluster.

        :stability: experimental
        :attribute: true
        '''
        result = self._values.get("vpc_endpoint_service_name")
        assert result is not None, "Required property 'vpc_endpoint_service_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def creation_time(self) -> typing.Optional[builtins.str]:
        '''(experimental) The timestamp when the cluster was created, in ISO 8601 format.

        :default: undefined - No creation time is provided

        :stability: experimental
        '''
        result = self._values.get("creation_time")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) KMS encryption key associated with this cluster.

        :default: - no encryption key

        :stability: experimental
        '''
        result = self._values.get("encryption_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], result)

    @builtins.property
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the cluster.

        :default: undefined - No status is provided

        :stability: experimental
        '''
        result = self._values.get("status")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ClusterAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.auroraDsql.ClusterCustomProps",
    jsii_struct_bases=[],
    name_mapping={
        "kms_key": "kmsKey",
        "multi_region_properties": "multiRegionProperties",
        "removal_policy": "removalPolicy",
        "tags": "tags",
    },
)
class ClusterCustomProps:
    def __init__(
        self,
        *,
        kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        multi_region_properties: typing.Optional[typing.Union["MultiRegionProperties", typing.Dict[builtins.str, typing.Any]]] = None,
        removal_policy: typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''(experimental) Properties for creating a Aurora DSQL cluster resource.

        :param kms_key: (experimental) KMS key to use for the cluster. Default: - A new KMS key is created.
        :param multi_region_properties: (experimental) Defines the structure for multi-Region cluster configurations, containing the witness Region and peered cluster settings. If not provided, the cluster will be created in the same region as the stack (single region cluster). Default: - No multi-Region cluster configurations.
        :param removal_policy: (experimental) The removal policy for the cluster. Only RemovalPolicy.DESTROY and RemovalPolicy.RETAIN are allowed. Default: - RemovalPolicy.DESTROY
        :param tags: (experimental) Tags to apply to the cluster. Default: - No tags.

        :stability: experimental
        '''
        if isinstance(multi_region_properties, dict):
            multi_region_properties = MultiRegionProperties(**multi_region_properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__044307b7ec599c6c058a5fe1f2510e92038af72cc31f91944edc61a7e2f182b9)
            check_type(argname="argument kms_key", value=kms_key, expected_type=type_hints["kms_key"])
            check_type(argname="argument multi_region_properties", value=multi_region_properties, expected_type=type_hints["multi_region_properties"])
            check_type(argname="argument removal_policy", value=removal_policy, expected_type=type_hints["removal_policy"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if kms_key is not None:
            self._values["kms_key"] = kms_key
        if multi_region_properties is not None:
            self._values["multi_region_properties"] = multi_region_properties
        if removal_policy is not None:
            self._values["removal_policy"] = removal_policy
        if tags is not None:
            self._values["tags"] = tags

    @builtins.property
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) KMS key to use for the cluster.

        :default: - A new KMS key is created.

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("kms_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], result)

    @builtins.property
    def multi_region_properties(self) -> typing.Optional["MultiRegionProperties"]:
        '''(experimental) Defines the structure for multi-Region cluster configurations, containing the witness Region and peered cluster settings.

        If not provided, the cluster will be created in the same region as the stack (single region cluster).

        :default: - No multi-Region cluster configurations.

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("multi_region_properties")
        return typing.cast(typing.Optional["MultiRegionProperties"], result)

    @builtins.property
    def removal_policy(self) -> typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy]:
        '''(experimental) The removal policy for the cluster.

        Only RemovalPolicy.DESTROY and RemovalPolicy.RETAIN are allowed.

        :default: - RemovalPolicy.DESTROY

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("removal_policy")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Tags to apply to the cluster.

        :default: - No tags.

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ClusterCustomProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.interface(jsii_type="@cdklabs/generative-ai-cdk-constructs.auroraDsql.ICluster")
class ICluster(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    '''(experimental) Interface for Aurora DSQL cluster resources.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="clusterArn")
    def cluster_arn(self) -> builtins.str:
        '''(experimental) The ARN of the cluster.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="clusterId")
    def cluster_id(self) -> builtins.str:
        '''(experimental) The id of the cluster.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="vpcEndpointServiceName")
    def vpc_endpoint_service_name(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="creationTime")
    def creation_time(self) -> typing.Optional[builtins.str]:
        '''(experimental) The timestamp when the cluster was created, in ISO 8601 format.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="encryptionKey")
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) Optional KMS encryption key associated with this bucket.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the cluster.

        :stability: experimental
        :attribute: true
        '''
        ...

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants IAM actions to the IAM Principal.

        :param grantee: -
        :param actions: -

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grantConnect")
    def grant_connect(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) grants connection authorization for a custom database role to the IAM Principal.

        :param grantee: -

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grantConnectAdmin")
    def grant_connect_admin(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants connection authorization for the admin role to the IAM Principal.

        :param grantee: -

        :stability: experimental
        '''
        ...


class _IClusterProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    '''(experimental) Interface for Aurora DSQL cluster resources.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@cdklabs/generative-ai-cdk-constructs.auroraDsql.ICluster"

    @builtins.property
    @jsii.member(jsii_name="clusterArn")
    def cluster_arn(self) -> builtins.str:
        '''(experimental) The ARN of the cluster.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "clusterArn"))

    @builtins.property
    @jsii.member(jsii_name="clusterId")
    def cluster_id(self) -> builtins.str:
        '''(experimental) The id of the cluster.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "clusterId"))

    @builtins.property
    @jsii.member(jsii_name="vpcEndpointServiceName")
    def vpc_endpoint_service_name(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "vpcEndpointServiceName"))

    @builtins.property
    @jsii.member(jsii_name="creationTime")
    def creation_time(self) -> typing.Optional[builtins.str]:
        '''(experimental) The timestamp when the cluster was created, in ISO 8601 format.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "creationTime"))

    @builtins.property
    @jsii.member(jsii_name="encryptionKey")
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) Optional KMS encryption key associated with this bucket.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "encryptionKey"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the cluster.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants IAM actions to the IAM Principal.

        :param grantee: -
        :param actions: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__564af2d559575895a6b482051aa11872224da0fdff9f21ae227245ffadffc40d)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
            check_type(argname="argument actions", value=actions, expected_type=typing.Tuple[type_hints["actions"], ...]) # pyright: ignore [reportGeneralTypeIssues]
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [grantee, *actions]))

    @jsii.member(jsii_name="grantConnect")
    def grant_connect(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) grants connection authorization for a custom database role to the IAM Principal.

        :param grantee: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a28d61223e2b2b1778aebe083ee9f3b53ec21fcd100ba23217cd6d411d4de93d)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantConnect", [grantee]))

    @jsii.member(jsii_name="grantConnectAdmin")
    def grant_connect_admin(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants connection authorization for the admin role to the IAM Principal.

        :param grantee: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__59bd621b17996ee9852eeeb147c4e4b6c3cc193533de7260d4930c1ac606bde4)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantConnectAdmin", [grantee]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, ICluster).__jsii_proxy_class__ = lambda : _IClusterProxy


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.auroraDsql.MultiRegionProperties",
    jsii_struct_bases=[],
    name_mapping={"witness_region": "witnessRegion", "clusters": "clusters"},
)
class MultiRegionProperties:
    def __init__(
        self,
        *,
        witness_region: builtins.str,
        clusters: typing.Optional[typing.Sequence[ICluster]] = None,
    ) -> None:
        '''(experimental) Interface for multi-region cluster properties.

        :param witness_region: (experimental) The Region that serves as the witness Region for a multi-Region cluster. The witness Region helps maintain cluster consistency and quorum. The witness Region receives data written to any Read-Write Region but does not have an endpoint.
        :param clusters: (experimental) The set of peered clusters that form the multi-Region cluster configuration. Each peered cluster represents a database instance in a different Region. Default: - No peered clusters (single region cluster)

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ae8cb3b502f6da64338306fa8f6429c13cd4e966812c1df51c1be142780e49a3)
            check_type(argname="argument witness_region", value=witness_region, expected_type=type_hints["witness_region"])
            check_type(argname="argument clusters", value=clusters, expected_type=type_hints["clusters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "witness_region": witness_region,
        }
        if clusters is not None:
            self._values["clusters"] = clusters

    @builtins.property
    def witness_region(self) -> builtins.str:
        '''(experimental) The Region that serves as the witness Region for a multi-Region cluster.

        The witness Region helps maintain cluster consistency and quorum.
        The witness Region receives data written to any Read-Write Region
        but does not have an endpoint.

        :stability: experimental
        :required: - Yes
        '''
        result = self._values.get("witness_region")
        assert result is not None, "Required property 'witness_region' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def clusters(self) -> typing.Optional[typing.List[ICluster]]:
        '''(experimental) The set of peered clusters that form the multi-Region cluster configuration.

        Each peered cluster represents a database instance in a different Region.

        :default: - No peered clusters (single region cluster)

        :stability: experimental
        :required: - No
        '''
        result = self._values.get("clusters")
        return typing.cast(typing.Optional[typing.List[ICluster]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MultiRegionProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(ICluster)
class ClusterBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.auroraDsql.ClusterBase",
):
    '''(experimental) Abstract base class for a Aurora DSQL cluster.

    Contains methods and attributes valid for Aurora DSQL clusters either created with CDK or imported.

    :stability: experimental
    '''

    def __init__(self, scope: _constructs_77d1e7e8.Construct, id: builtins.str) -> None:
        '''
        :param scope: -
        :param id: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__04004de5b535054b20703f86e0cd818f8e9b112aa08ad0e857f17895e2d2b5d9)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        jsii.create(self.__class__, self, [scope, id])

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants IAM actions to the IAM Principal.

        :param grantee: - The IAM principal to grant permissions to.
        :param actions: - The actions to grant.

        :return: An IAM Grant object representing the granted permissions

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__daeb0b5f0ac211d52a8e8dd08b34b54ebd24e45104ac91264e236d2cd83b9f3a)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
            check_type(argname="argument actions", value=actions, expected_type=typing.Tuple[type_hints["actions"], ...]) # pyright: ignore [reportGeneralTypeIssues]
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [grantee, *actions]))

    @jsii.member(jsii_name="grantConnect")
    def grant_connect(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants connection authorization to the IAM Principal.

        :param grantee: - The IAM principal to grant permissions to.

        :default:

        - Default grant configuration:
        - actions: ['dsql:DbConnect'] on this.clusterArn

        :return: An IAM Grant object representing the granted permissions

        :see: https://docs.aws.amazon.com/aurora-dsql/latest/userguide/authentication-authorization.html#authentication-authorization-iam-policy
        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f899988ef461e96385d19d91109c1fbf7edf3c4eb9d63fe2a24e20f7ba62c5d3)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantConnect", [grantee]))

    @jsii.member(jsii_name="grantConnectAdmin")
    def grant_connect_admin(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grants connection authorization to the IAM Principal.

        :param grantee: - The IAM principal to grant permissions to.

        :default:

        - Default grant configuration:
        - actions: ['dsql:DbConnectAdmin'] on this.clusterArn

        :return: An IAM Grant object representing the granted permissions

        :see: https://docs.aws.amazon.com/aurora-dsql/latest/userguide/authentication-authorization.html#authentication-authorization-iam-policy
        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e87ac96beb2af5e5d86d863ea006cdfc6873e1178561e7bbd5e82e5fbc02964c)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantConnectAdmin", [grantee]))

    @builtins.property
    @jsii.member(jsii_name="clusterArn")
    @abc.abstractmethod
    def cluster_arn(self) -> builtins.str:
        '''(experimental) The ARN of the cluster.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="clusterId")
    @abc.abstractmethod
    def cluster_id(self) -> builtins.str:
        '''(experimental) The id of the cluster.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="vpcEndpointServiceName")
    @abc.abstractmethod
    def vpc_endpoint_service_name(self) -> builtins.str:
        '''(experimental) The VpcEndpointServiceName of the cluster.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="creationTime")
    @abc.abstractmethod
    def creation_time(self) -> typing.Optional[builtins.str]:
        '''(experimental) The timestamp when the cluster was created, in ISO 8601 format.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="encryptionKey")
    @abc.abstractmethod
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) Optional KMS encryption key associated with this cluster.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="status")
    @abc.abstractmethod
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the cluster.

        :stability: experimental
        '''
        ...


class _ClusterBaseProxy(
    ClusterBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="clusterArn")
    def cluster_arn(self) -> builtins.str:
        '''(experimental) The ARN of the cluster.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "clusterArn"))

    @builtins.property
    @jsii.member(jsii_name="clusterId")
    def cluster_id(self) -> builtins.str:
        '''(experimental) The id of the cluster.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "clusterId"))

    @builtins.property
    @jsii.member(jsii_name="vpcEndpointServiceName")
    def vpc_endpoint_service_name(self) -> builtins.str:
        '''(experimental) The VpcEndpointServiceName of the cluster.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "vpcEndpointServiceName"))

    @builtins.property
    @jsii.member(jsii_name="creationTime")
    def creation_time(self) -> typing.Optional[builtins.str]:
        '''(experimental) The timestamp when the cluster was created, in ISO 8601 format.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "creationTime"))

    @builtins.property
    @jsii.member(jsii_name="encryptionKey")
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) Optional KMS encryption key associated with this cluster.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "encryptionKey"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the cluster.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, ClusterBase).__jsii_proxy_class__ = lambda : _ClusterBaseProxy


class Cluster(
    ClusterBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.auroraDsql.Cluster",
):
    '''(experimental) Aurora DSQL cluster resource for AWS Aurora DSQL.

    You can use this resource to create, modify, and manage clusters.

    :see: https://docs.aws.amazon.com/aurora-dsql/latest/userguide/what-is-aurora-dsql.html
    :stability: experimental
    :resource: AWS::DSQL::Cluster
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        multi_region_properties: typing.Optional[typing.Union[MultiRegionProperties, typing.Dict[builtins.str, typing.Any]]] = None,
        removal_policy: typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param kms_key: (experimental) KMS key to use for the cluster. Default: - A new KMS key is created.
        :param multi_region_properties: (experimental) Defines the structure for multi-Region cluster configurations, containing the witness Region and peered cluster settings. If not provided, the cluster will be created in the same region as the stack (single region cluster). Default: - No multi-Region cluster configurations.
        :param removal_policy: (experimental) The removal policy for the cluster. Only RemovalPolicy.DESTROY and RemovalPolicy.RETAIN are allowed. Default: - RemovalPolicy.DESTROY
        :param tags: (experimental) Tags to apply to the cluster. Default: - No tags.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ffd565af5a823a426f3b1a44f2c8ded165af35089e6177fdd84bd223fb82894e)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ClusterCustomProps(
            kms_key=kms_key,
            multi_region_properties=multi_region_properties,
            removal_policy=removal_policy,
            tags=tags,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromClusterAttributes")
    @builtins.classmethod
    def from_cluster_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        cluster_arn: builtins.str,
        vpc_endpoint_service_name: builtins.str,
        creation_time: typing.Optional[builtins.str] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        status: typing.Optional[builtins.str] = None,
    ) -> ICluster:
        '''(experimental) Creates an Aurora DSQL cluster reference from an existing cluster's attributes.

        :param scope: - The construct scope.
        :param id: - Identifier of the construct.
        :param cluster_arn: (experimental) The ARN of the cluster.
        :param vpc_endpoint_service_name: (experimental) VpcEndpointServiceName of the cluster.
        :param creation_time: (experimental) The timestamp when the cluster was created, in ISO 8601 format. Default: undefined - No creation time is provided
        :param encryption_key: (experimental) KMS encryption key associated with this cluster. Default: - no encryption key
        :param status: (experimental) The status of the cluster. Default: undefined - No status is provided

        :return: An ICluster reference to the existing cluster

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__86096eaea20c9427f89e08ce820c4b826141086b38098ed74e3ff10333e2065f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = ClusterAttributes(
            cluster_arn=cluster_arn,
            vpc_endpoint_service_name=vpc_endpoint_service_name,
            creation_time=creation_time,
            encryption_key=encryption_key,
            status=status,
        )

        return typing.cast(ICluster, jsii.sinvoke(cls, "fromClusterAttributes", [scope, id, attrs]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="clusterArn")
    def cluster_arn(self) -> builtins.str:
        '''(experimental) The ARN of the cluster.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "clusterArn"))

    @builtins.property
    @jsii.member(jsii_name="clusterId")
    def cluster_id(self) -> builtins.str:
        '''(experimental) The id of the cluster.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "clusterId"))

    @builtins.property
    @jsii.member(jsii_name="vpcEndpointServiceName")
    def vpc_endpoint_service_name(self) -> builtins.str:
        '''(experimental) VpcEndpointServiceName of the cluster.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "vpcEndpointServiceName"))

    @builtins.property
    @jsii.member(jsii_name="creationTime")
    def creation_time(self) -> typing.Optional[builtins.str]:
        '''(experimental) The timestamp when the cluster was created, in ISO 8601 format.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "creationTime"))

    @builtins.property
    @jsii.member(jsii_name="encryptionKey")
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) KMS encryption key associated with this cluster.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "encryptionKey"))

    @builtins.property
    @jsii.member(jsii_name="multiRegionProperties")
    def multi_region_properties(self) -> typing.Optional[MultiRegionProperties]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[MultiRegionProperties], jsii.get(self, "multiRegionProperties"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> typing.Optional[builtins.str]:
        '''(experimental) The status of the cluster.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Tags applied to this cluster resource A map of key-value pairs for resource tagging.

        :default: - No tags applied

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "tags"))


__all__ = [
    "Cluster",
    "ClusterAttributes",
    "ClusterBase",
    "ClusterCustomProps",
    "ICluster",
    "MultiRegionProperties",
]

publication.publish()

def _typecheckingstub__24de4270819b601d6eb8496aab768698004b05e95e4cc0090c43af71f652d1d5(
    *,
    cluster_arn: builtins.str,
    vpc_endpoint_service_name: builtins.str,
    creation_time: typing.Optional[builtins.str] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    status: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__044307b7ec599c6c058a5fe1f2510e92038af72cc31f91944edc61a7e2f182b9(
    *,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    multi_region_properties: typing.Optional[typing.Union[MultiRegionProperties, typing.Dict[builtins.str, typing.Any]]] = None,
    removal_policy: typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__564af2d559575895a6b482051aa11872224da0fdff9f21ae227245ffadffc40d(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    *actions: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a28d61223e2b2b1778aebe083ee9f3b53ec21fcd100ba23217cd6d411d4de93d(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__59bd621b17996ee9852eeeb147c4e4b6c3cc193533de7260d4930c1ac606bde4(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ae8cb3b502f6da64338306fa8f6429c13cd4e966812c1df51c1be142780e49a3(
    *,
    witness_region: builtins.str,
    clusters: typing.Optional[typing.Sequence[ICluster]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04004de5b535054b20703f86e0cd818f8e9b112aa08ad0e857f17895e2d2b5d9(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__daeb0b5f0ac211d52a8e8dd08b34b54ebd24e45104ac91264e236d2cd83b9f3a(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    *actions: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f899988ef461e96385d19d91109c1fbf7edf3c4eb9d63fe2a24e20f7ba62c5d3(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e87ac96beb2af5e5d86d863ea006cdfc6873e1178561e7bbd5e82e5fbc02964c(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ffd565af5a823a426f3b1a44f2c8ded165af35089e6177fdd84bd223fb82894e(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    multi_region_properties: typing.Optional[typing.Union[MultiRegionProperties, typing.Dict[builtins.str, typing.Any]]] = None,
    removal_policy: typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__86096eaea20c9427f89e08ce820c4b826141086b38098ed74e3ff10333e2065f(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    cluster_arn: builtins.str,
    vpc_endpoint_service_name: builtins.str,
    creation_time: typing.Optional[builtins.str] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    status: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

for cls in [ICluster]:
    typing.cast(typing.Any, cls).__protocol_attrs__ = typing.cast(typing.Any, cls).__protocol_attrs__ - set(['__jsii_proxy_class__', '__jsii_type__'])
