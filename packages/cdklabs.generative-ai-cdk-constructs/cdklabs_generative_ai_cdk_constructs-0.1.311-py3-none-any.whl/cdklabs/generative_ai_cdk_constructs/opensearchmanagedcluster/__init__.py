r'''
# OpenSearch Managed Cluster Vector Store Construct Library

<!--BEGIN STABILITY BANNER-->---


![Stability: Experimental](https://img.shields.io/badge/stability-Experimental-important.svg?style=for-the-badge)

> All classes are under active development and subject to non-backward compatible changes or removal in any
> future version. These are not subject to the [Semantic Versioning](https://semver.org/) model.
> This means that while you may use them, you may need to update your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

| **Language**     | **Package**        |
|:-------------|-----------------|
|![Typescript Logo](https://docs.aws.amazon.com/cdk/api/latest/img/typescript32.png) TypeScript|`@cdklabs/generative-ai-cdk-constructs`|
|![Python Logo](https://docs.aws.amazon.com/cdk/api/latest/img/python32.png) Python|`cdklabs.generative_ai_cdk_constructs`|
| ![Java Logo](https://docs.aws.amazon.com/cdk/api/latest/img/java32.png) Java                   | `io.github.cdklabs.generative_ai_cdk_constructs`|
| ![.Net](https://docs.aws.amazon.com/cdk/api/latest/img/dotnet32.png) .Net                   | `CdkLabs.GenerativeAICdkConstructs`|
| ![Go](https://docs.aws.amazon.com/cdk/api/latest/img/go32.png) Go                   | `github.com/cdklabs/generative-ai-cdk-constructs-go/generative-ai-cdk-constructs`|

This construct library provides a class that defines an existing OpenSearch managed cluster to be used as a vector store for a Knowledge Base.

## Table of contents

* [API](#api)
* [OpenSearch Managed Cluster Vector Store](#opensearch-managed-cluster-vector-store)

## API

See the [API documentation](../../../apidocs/namespaces/opensearchmanagedcluster/README.md).

## OpenSearch Managed Cluster Vector Store

TypeScript

```python
import { opensearchmanagedcluster } from '@cdklabs/generative-ai-cdk-constructs';

new opensearchmanagedcluster.OpenSearchManagedClusterVectorStore({
  domainArn: 'arn:aws:es:region:account:domain/your-domain',
  domainEndpoint: 'https://your-domain.region.es.amazonaws.com',
  vectorIndexName: 'your-vector-index',
  fieldMapping: {
    metadataField: 'metadata',
    textField: 'text',
    vectorField: 'vector'
  }
});
```

Python

```python
from cdklabs.generative_ai_cdk_constructs import (
    opensearchmanagedcluster
)

opensearchvs = opensearchmanagedcluster.OpenSearchManagedClusterVectorStore(
    domain_arn='arn:aws:es:region:account:domain/your-domain',
    domain_endpoint='https://your-domain.region.es.amazonaws.com',
    vector_index_name='your-vector-index',
    field_mapping={
        'metadataField': 'metadata',
        'textField': 'text',
        'vectorField': 'vector'
    }
)
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


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.opensearchmanagedcluster.OpenSearchFieldMapping",
    jsii_struct_bases=[],
    name_mapping={
        "metadata_field": "metadataField",
        "text_field": "textField",
        "vector_field": "vectorField",
    },
)
class OpenSearchFieldMapping:
    def __init__(
        self,
        *,
        metadata_field: builtins.str,
        text_field: builtins.str,
        vector_field: builtins.str,
    ) -> None:
        '''(experimental) Field mapping configuration for OpenSearch vector store.

        :param metadata_field: (experimental) The name of the field in which Amazon Bedrock stores metadata about the vector store.
        :param text_field: (experimental) The name of the field in which Amazon Bedrock stores the raw text in chunks from your data.
        :param vector_field: (experimental) The name of the field in which Amazon Bedrock stores the vector embeddings.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5fc910f8cf2c00a339e12e98125bef54c13acd2eafc5b3595477c6c1eae6c90f)
            check_type(argname="argument metadata_field", value=metadata_field, expected_type=type_hints["metadata_field"])
            check_type(argname="argument text_field", value=text_field, expected_type=type_hints["text_field"])
            check_type(argname="argument vector_field", value=vector_field, expected_type=type_hints["vector_field"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "metadata_field": metadata_field,
            "text_field": text_field,
            "vector_field": vector_field,
        }

    @builtins.property
    def metadata_field(self) -> builtins.str:
        '''(experimental) The name of the field in which Amazon Bedrock stores metadata about the vector store.

        :stability: experimental
        '''
        result = self._values.get("metadata_field")
        assert result is not None, "Required property 'metadata_field' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def text_field(self) -> builtins.str:
        '''(experimental) The name of the field in which Amazon Bedrock stores the raw text in chunks from your data.

        :stability: experimental
        '''
        result = self._values.get("text_field")
        assert result is not None, "Required property 'text_field' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def vector_field(self) -> builtins.str:
        '''(experimental) The name of the field in which Amazon Bedrock stores the vector embeddings.

        :stability: experimental
        '''
        result = self._values.get("vector_field")
        assert result is not None, "Required property 'vector_field' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "OpenSearchFieldMapping(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class OpenSearchManagedClusterVectorStore(
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.opensearchmanagedcluster.OpenSearchManagedClusterVectorStore",
):
    '''(experimental) Class to define an OpenSearchManagedClusterVectorStore.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        domain_arn: builtins.str,
        domain_endpoint: builtins.str,
        field_mapping: typing.Union[OpenSearchFieldMapping, typing.Dict[builtins.str, typing.Any]],
        vector_index_name: builtins.str,
    ) -> None:
        '''
        :param domain_arn: (experimental) The ARN of your OpenSearch Customer Managed Domain.
        :param domain_endpoint: (experimental) The url of your OpenSearch Managed cluster domain.
        :param field_mapping: (experimental) Configuration for field mappings in the vector store. Bedrock uses these fields to store your data. If you haven't configured these fields in your vector database, your Knowledge Base will fail to be created.
        :param vector_index_name: (experimental) The vector index name of your OpenSearch Customer Managed Domain.

        :stability: experimental
        '''
        props = OpenSearchManagedClusterVectorStoreProps(
            domain_arn=domain_arn,
            domain_endpoint=domain_endpoint,
            field_mapping=field_mapping,
            vector_index_name=vector_index_name,
        )

        jsii.create(self.__class__, self, [props])

    @builtins.property
    @jsii.member(jsii_name="domainArn")
    def domain_arn(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "domainArn"))

    @builtins.property
    @jsii.member(jsii_name="domainEndpoint")
    def domain_endpoint(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "domainEndpoint"))

    @builtins.property
    @jsii.member(jsii_name="fieldMapping")
    def field_mapping(self) -> OpenSearchFieldMapping:
        '''
        :stability: experimental
        '''
        return typing.cast(OpenSearchFieldMapping, jsii.get(self, "fieldMapping"))

    @builtins.property
    @jsii.member(jsii_name="vectorIndexName")
    def vector_index_name(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "vectorIndexName"))


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.opensearchmanagedcluster.OpenSearchManagedClusterVectorStoreProps",
    jsii_struct_bases=[],
    name_mapping={
        "domain_arn": "domainArn",
        "domain_endpoint": "domainEndpoint",
        "field_mapping": "fieldMapping",
        "vector_index_name": "vectorIndexName",
    },
)
class OpenSearchManagedClusterVectorStoreProps:
    def __init__(
        self,
        *,
        domain_arn: builtins.str,
        domain_endpoint: builtins.str,
        field_mapping: typing.Union[OpenSearchFieldMapping, typing.Dict[builtins.str, typing.Any]],
        vector_index_name: builtins.str,
    ) -> None:
        '''(experimental) Properties for an OpenSearchManagedClusterVectorStore.

        :param domain_arn: (experimental) The ARN of your OpenSearch Customer Managed Domain.
        :param domain_endpoint: (experimental) The url of your OpenSearch Managed cluster domain.
        :param field_mapping: (experimental) Configuration for field mappings in the vector store. Bedrock uses these fields to store your data. If you haven't configured these fields in your vector database, your Knowledge Base will fail to be created.
        :param vector_index_name: (experimental) The vector index name of your OpenSearch Customer Managed Domain.

        :stability: experimental
        '''
        if isinstance(field_mapping, dict):
            field_mapping = OpenSearchFieldMapping(**field_mapping)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4ee13120d497dda1cfc6b69e74ab2badf116b41a49adba30de15d2b90e880c95)
            check_type(argname="argument domain_arn", value=domain_arn, expected_type=type_hints["domain_arn"])
            check_type(argname="argument domain_endpoint", value=domain_endpoint, expected_type=type_hints["domain_endpoint"])
            check_type(argname="argument field_mapping", value=field_mapping, expected_type=type_hints["field_mapping"])
            check_type(argname="argument vector_index_name", value=vector_index_name, expected_type=type_hints["vector_index_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "domain_arn": domain_arn,
            "domain_endpoint": domain_endpoint,
            "field_mapping": field_mapping,
            "vector_index_name": vector_index_name,
        }

    @builtins.property
    def domain_arn(self) -> builtins.str:
        '''(experimental) The ARN of your OpenSearch Customer Managed Domain.

        :stability: experimental
        '''
        result = self._values.get("domain_arn")
        assert result is not None, "Required property 'domain_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def domain_endpoint(self) -> builtins.str:
        '''(experimental) The url of your OpenSearch Managed cluster domain.

        :stability: experimental
        '''
        result = self._values.get("domain_endpoint")
        assert result is not None, "Required property 'domain_endpoint' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def field_mapping(self) -> OpenSearchFieldMapping:
        '''(experimental) Configuration for field mappings in the vector store.

        Bedrock uses these fields to store your data.
        If you haven't configured these fields in your vector database, your Knowledge Base
        will fail to be created.

        :stability: experimental
        '''
        result = self._values.get("field_mapping")
        assert result is not None, "Required property 'field_mapping' is missing"
        return typing.cast(OpenSearchFieldMapping, result)

    @builtins.property
    def vector_index_name(self) -> builtins.str:
        '''(experimental) The vector index name of your OpenSearch Customer Managed Domain.

        :stability: experimental
        '''
        result = self._values.get("vector_index_name")
        assert result is not None, "Required property 'vector_index_name' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "OpenSearchManagedClusterVectorStoreProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "OpenSearchFieldMapping",
    "OpenSearchManagedClusterVectorStore",
    "OpenSearchManagedClusterVectorStoreProps",
]

publication.publish()

def _typecheckingstub__5fc910f8cf2c00a339e12e98125bef54c13acd2eafc5b3595477c6c1eae6c90f(
    *,
    metadata_field: builtins.str,
    text_field: builtins.str,
    vector_field: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4ee13120d497dda1cfc6b69e74ab2badf116b41a49adba30de15d2b90e880c95(
    *,
    domain_arn: builtins.str,
    domain_endpoint: builtins.str,
    field_mapping: typing.Union[OpenSearchFieldMapping, typing.Dict[builtins.str, typing.Any]],
    vector_index_name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass
