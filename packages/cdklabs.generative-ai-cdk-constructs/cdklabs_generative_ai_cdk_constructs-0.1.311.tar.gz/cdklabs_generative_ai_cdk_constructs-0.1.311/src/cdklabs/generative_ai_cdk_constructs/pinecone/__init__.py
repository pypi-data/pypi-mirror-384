r'''
# Pinecone Vector Store Construct Library

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

This construct library provides a class that defines an existing Pinecone database to be used for a vector store for a Knowledge Base.

## Table of contents

* [API](#api)
* [Pinecone Vector Store](#pinecone-vector-store)

## API

See the [API documentation](../../../apidocs/namespaces/pinecone/README.md).

## Pinecone Vector Store

TypeScript

```python
import { pinecone } from '@cdklabs/generative-ai-cdk-constructs';

new pinecone.PineconeVectorStore({
  connectionString: 'https://your-index-1234567.svc.gcp-starter.pinecone.io',
  credentialsSecretArn: 'arn:aws:secretsmanager:your-region:123456789876:secret:your-key-name',
  textField: 'question',
  metadataField: 'metadata'
});
```

Python

```python
from cdklabs.generative_ai_cdk_constructs import (
    pinecone
)

pineconevs = pinecone.PineconeVectorStore(
            connection_string='https://your-index-1234567.svc.gcp-starter.pinecone.io',
            credentials_secret_arn='arn:aws:secretsmanager:your-region:123456789876:secret:your-key-name',
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


class PineconeVectorStore(
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.pinecone.PineconeVectorStore",
):
    '''(experimental) Class to define a PineconeVectorStore.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        connection_string: builtins.str,
        credentials_secret_arn: builtins.str,
        metadata_field: builtins.str,
        text_field: builtins.str,
        kms_key: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection_string: (experimental) Connection string for your Pinecone index management page.
        :param credentials_secret_arn: (experimental) ARN of the secret containing the API Key to use when connecting to the Pinecone database. Learn more in the link below.
        :param metadata_field: (experimental) The name of the field in which Amazon Bedrock stores metadata about the vector store.
        :param text_field: (experimental) The name of the field in which Amazon Bedrock stores the raw text from your data.
        :param kms_key: (experimental) If you encrypted your secret, provide the KMS key here so that Bedrock can decrypt it.
        :param namespace: (experimental) Name space that will be used for writing new data to your Pinecone database.

        :stability: experimental
        '''
        props = PineconeVectorStoreProps(
            connection_string=connection_string,
            credentials_secret_arn=credentials_secret_arn,
            metadata_field=metadata_field,
            text_field=text_field,
            kms_key=kms_key,
            namespace=namespace,
        )

        jsii.create(self.__class__, self, [props])

    @builtins.property
    @jsii.member(jsii_name="connectionString")
    def connection_string(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "connectionString"))

    @builtins.property
    @jsii.member(jsii_name="credentialsSecretArn")
    def credentials_secret_arn(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "credentialsSecretArn"))

    @builtins.property
    @jsii.member(jsii_name="metadataField")
    def metadata_field(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "metadataField"))

    @builtins.property
    @jsii.member(jsii_name="textField")
    def text_field(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "textField"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional[builtins.str]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="namespace")
    def namespace(self) -> typing.Optional[builtins.str]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "namespace"))


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.pinecone.PineconeVectorStoreProps",
    jsii_struct_bases=[],
    name_mapping={
        "connection_string": "connectionString",
        "credentials_secret_arn": "credentialsSecretArn",
        "metadata_field": "metadataField",
        "text_field": "textField",
        "kms_key": "kmsKey",
        "namespace": "namespace",
    },
)
class PineconeVectorStoreProps:
    def __init__(
        self,
        *,
        connection_string: builtins.str,
        credentials_secret_arn: builtins.str,
        metadata_field: builtins.str,
        text_field: builtins.str,
        kms_key: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Properties for a PineconeVectorStore.

        :param connection_string: (experimental) Connection string for your Pinecone index management page.
        :param credentials_secret_arn: (experimental) ARN of the secret containing the API Key to use when connecting to the Pinecone database. Learn more in the link below.
        :param metadata_field: (experimental) The name of the field in which Amazon Bedrock stores metadata about the vector store.
        :param text_field: (experimental) The name of the field in which Amazon Bedrock stores the raw text from your data.
        :param kms_key: (experimental) If you encrypted your secret, provide the KMS key here so that Bedrock can decrypt it.
        :param namespace: (experimental) Name space that will be used for writing new data to your Pinecone database.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6e082eabab3ef5c3bae083d7598ea12db0801f8a772c97d28f04b4e4b73ed166)
            check_type(argname="argument connection_string", value=connection_string, expected_type=type_hints["connection_string"])
            check_type(argname="argument credentials_secret_arn", value=credentials_secret_arn, expected_type=type_hints["credentials_secret_arn"])
            check_type(argname="argument metadata_field", value=metadata_field, expected_type=type_hints["metadata_field"])
            check_type(argname="argument text_field", value=text_field, expected_type=type_hints["text_field"])
            check_type(argname="argument kms_key", value=kms_key, expected_type=type_hints["kms_key"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "connection_string": connection_string,
            "credentials_secret_arn": credentials_secret_arn,
            "metadata_field": metadata_field,
            "text_field": text_field,
        }
        if kms_key is not None:
            self._values["kms_key"] = kms_key
        if namespace is not None:
            self._values["namespace"] = namespace

    @builtins.property
    def connection_string(self) -> builtins.str:
        '''(experimental) Connection string for your Pinecone index management page.

        :stability: experimental
        '''
        result = self._values.get("connection_string")
        assert result is not None, "Required property 'connection_string' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def credentials_secret_arn(self) -> builtins.str:
        '''(experimental) ARN of the secret containing the API Key to use when connecting to the Pinecone database.

        Learn more in the link below.

        :see: https://www.pinecone.io/blog/amazon-bedrock-integration/
        :stability: experimental
        '''
        result = self._values.get("credentials_secret_arn")
        assert result is not None, "Required property 'credentials_secret_arn' is missing"
        return typing.cast(builtins.str, result)

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
        '''(experimental) The name of the field in which Amazon Bedrock stores the raw text from your data.

        :stability: experimental
        '''
        result = self._values.get("text_field")
        assert result is not None, "Required property 'text_field' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def kms_key(self) -> typing.Optional[builtins.str]:
        '''(experimental) If you encrypted your secret, provide the KMS key here so that Bedrock can decrypt it.

        :stability: experimental
        '''
        result = self._values.get("kms_key")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''(experimental) Name space that will be used for writing new data to your Pinecone database.

        :stability: experimental
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PineconeVectorStoreProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "PineconeVectorStore",
    "PineconeVectorStoreProps",
]

publication.publish()

def _typecheckingstub__6e082eabab3ef5c3bae083d7598ea12db0801f8a772c97d28f04b4e4b73ed166(
    *,
    connection_string: builtins.str,
    credentials_secret_arn: builtins.str,
    metadata_field: builtins.str,
    text_field: builtins.str,
    kms_key: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
