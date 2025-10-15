r'''
# MongoDB Atlas Vector Store Construct Library

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

## MongoDBAtlasVectorStore

The `MongoDBAtlasVectorStore` construct allows you to define a MongoDB Atlas instance as a vector store for your Amazon Bedrock Knowledge Base.

### Usage

#### TypeScript

```python
import * as cdk from 'aws-cdk-lib';
import { MongoDBAtlasVectorStore } from '@cdklabs/generative-ai-cdk-constructs';

const vectorStore = new MongoDBAtlasVectorStore(stack, 'MyVectorStore', {
  collectionName: 'embeddings',
  credentialsSecretArn: 'arn:aws:secretsmanager:region:account:secret:secret-name',
  databaseName: 'vectordb',
  endpoint: 'https://your-mongodb-atlas-endpoint.mongodb.net',
  endpointServiceName: 'mongodb-atlas',
  fieldMapping: {
    vectorField: 'embedding',
    textField: 'text',
    metadataField: 'metadata'
  },
  vectorIndexName: 'vector_index'
});
```

#### Python

```python
from cdklabs.generative_ai_cdk_constructs import MongoDBAtlasVectorStore

vector_store = MongoDBAtlasVectorStore(self, 'MyVectorStore',
  collection_name='embeddings',
  credentials_secret_arn='arn:aws:secretsmanager:region:account:secret:secret-name',
  database_name='vectordb',
  endpoint='https://your-mongodb-atlas-endpoint.mongodb.net',
  endpoint_service_name='mongodb-atlas',
  field_mapping=mongodb_atlas.MongoDbAtlasFieldMapping(
        vector_field='embedding',
        text_field='text',
        metadata_field='metadata'
    ),
  vector_index_name='vector_index'
)
```

### Properties

The `MongoDBAtlasVectorStore` construct accepts the following properties:

| Property | Type | Description |
|----------|------|-------------|
| `collectionName` | string | The name of the collection in MongoDB Atlas |
| `credentialsSecretArn` | string | The ARN of the AWS Secrets Manager secret containing MongoDB Atlas credentials |
| `databaseName` | string | The name of the database in MongoDB Atlas |
| `endpoint` | string | The endpoint URL for MongoDB Atlas |
| `endpointServiceName` | string | The name of the endpoint service |
| `fieldMapping` | MongoDbAtlasFieldMapping | The mapping of fields in the MongoDB collection |
| `vectorIndexName` | string | The name of the vector index in MongoDB Atlas |

### Field Mapping

The `fieldMapping` property defines how fields in your MongoDB collection map to vector store concepts:

| Property | Type | Description |
|----------|------|-------------|
| `vectorField` | string | The field name for storing vector embeddings |
| `textField` | string | The field name for storing the original text |
| `metadataField` | string | The field name for storing additional metadata |
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


class MongoDBAtlasVectorStore(
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.mongodbAtlas.MongoDBAtlasVectorStore",
):
    '''(experimental) Construct for MongoDB Atlas vector store.

    :stability: experimental
    '''

    def __init__(
        self,
        *,
        collection_name: builtins.str,
        credentials_secret_arn: builtins.str,
        database_name: builtins.str,
        endpoint: builtins.str,
        field_mapping: typing.Union["MongoDbAtlasFieldMapping", typing.Dict[builtins.str, typing.Any]],
        vector_index_name: builtins.str,
        endpoint_service_name: typing.Optional[builtins.str] = None,
        text_index_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Creates a new instance of the MongoDBAtlas class.

        :param collection_name: (experimental) The name of the collection.
        :param credentials_secret_arn: (experimental) The ARN of the secret containing MongoDB Atlas credentials.
        :param database_name: (experimental) The name of the database.
        :param endpoint: (experimental) The endpoint URL for MongoDB Atlas.
        :param field_mapping: (experimental) The field mapping for MongoDB Atlas.
        :param vector_index_name: (experimental) The name of the vector index.
        :param endpoint_service_name: (experimental) The name of the endpoint service.
        :param text_index_name: (experimental) The name of the text index.

        :stability: experimental
        '''
        props = MongoDBAtlasVectorStoreProps(
            collection_name=collection_name,
            credentials_secret_arn=credentials_secret_arn,
            database_name=database_name,
            endpoint=endpoint,
            field_mapping=field_mapping,
            vector_index_name=vector_index_name,
            endpoint_service_name=endpoint_service_name,
            text_index_name=text_index_name,
        )

        jsii.create(self.__class__, self, [props])

    @builtins.property
    @jsii.member(jsii_name="collectionName")
    def collection_name(self) -> builtins.str:
        '''(experimental) The name of the collection.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "collectionName"))

    @builtins.property
    @jsii.member(jsii_name="credentialsSecretArn")
    def credentials_secret_arn(self) -> builtins.str:
        '''(experimental) The ARN of the secret containing MongoDB Atlas credentials.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "credentialsSecretArn"))

    @builtins.property
    @jsii.member(jsii_name="databaseName")
    def database_name(self) -> builtins.str:
        '''(experimental) The name of the database.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "databaseName"))

    @builtins.property
    @jsii.member(jsii_name="endpoint")
    def endpoint(self) -> builtins.str:
        '''(experimental) The endpoint URL for MongoDB Atlas.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "endpoint"))

    @builtins.property
    @jsii.member(jsii_name="fieldMapping")
    def field_mapping(self) -> "MongoDbAtlasFieldMapping":
        '''(experimental) The field mapping for MongoDB Atlas.

        :stability: experimental
        '''
        return typing.cast("MongoDbAtlasFieldMapping", jsii.get(self, "fieldMapping"))

    @builtins.property
    @jsii.member(jsii_name="vectorIndexName")
    def vector_index_name(self) -> builtins.str:
        '''(experimental) The name of the vector index.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "vectorIndexName"))

    @builtins.property
    @jsii.member(jsii_name="endpointServiceName")
    def endpoint_service_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the endpoint service.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "endpointServiceName"))

    @builtins.property
    @jsii.member(jsii_name="textIndexName")
    def text_index_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the text index.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "textIndexName"))


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.mongodbAtlas.MongoDBAtlasVectorStoreProps",
    jsii_struct_bases=[],
    name_mapping={
        "collection_name": "collectionName",
        "credentials_secret_arn": "credentialsSecretArn",
        "database_name": "databaseName",
        "endpoint": "endpoint",
        "field_mapping": "fieldMapping",
        "vector_index_name": "vectorIndexName",
        "endpoint_service_name": "endpointServiceName",
        "text_index_name": "textIndexName",
    },
)
class MongoDBAtlasVectorStoreProps:
    def __init__(
        self,
        *,
        collection_name: builtins.str,
        credentials_secret_arn: builtins.str,
        database_name: builtins.str,
        endpoint: builtins.str,
        field_mapping: typing.Union["MongoDbAtlasFieldMapping", typing.Dict[builtins.str, typing.Any]],
        vector_index_name: builtins.str,
        endpoint_service_name: typing.Optional[builtins.str] = None,
        text_index_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Interface for MongoDB Atlas vector store configuration.

        :param collection_name: (experimental) The name of the collection.
        :param credentials_secret_arn: (experimental) The ARN of the secret containing MongoDB Atlas credentials.
        :param database_name: (experimental) The name of the database.
        :param endpoint: (experimental) The endpoint URL for MongoDB Atlas.
        :param field_mapping: (experimental) The field mapping for MongoDB Atlas.
        :param vector_index_name: (experimental) The name of the vector index.
        :param endpoint_service_name: (experimental) The name of the endpoint service.
        :param text_index_name: (experimental) The name of the text index.

        :stability: experimental
        '''
        if isinstance(field_mapping, dict):
            field_mapping = MongoDbAtlasFieldMapping(**field_mapping)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__28a3588f4e105edba1d4a736110b4e04967e17d3a3a5d516fd3c29f2ec528451)
            check_type(argname="argument collection_name", value=collection_name, expected_type=type_hints["collection_name"])
            check_type(argname="argument credentials_secret_arn", value=credentials_secret_arn, expected_type=type_hints["credentials_secret_arn"])
            check_type(argname="argument database_name", value=database_name, expected_type=type_hints["database_name"])
            check_type(argname="argument endpoint", value=endpoint, expected_type=type_hints["endpoint"])
            check_type(argname="argument field_mapping", value=field_mapping, expected_type=type_hints["field_mapping"])
            check_type(argname="argument vector_index_name", value=vector_index_name, expected_type=type_hints["vector_index_name"])
            check_type(argname="argument endpoint_service_name", value=endpoint_service_name, expected_type=type_hints["endpoint_service_name"])
            check_type(argname="argument text_index_name", value=text_index_name, expected_type=type_hints["text_index_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "collection_name": collection_name,
            "credentials_secret_arn": credentials_secret_arn,
            "database_name": database_name,
            "endpoint": endpoint,
            "field_mapping": field_mapping,
            "vector_index_name": vector_index_name,
        }
        if endpoint_service_name is not None:
            self._values["endpoint_service_name"] = endpoint_service_name
        if text_index_name is not None:
            self._values["text_index_name"] = text_index_name

    @builtins.property
    def collection_name(self) -> builtins.str:
        '''(experimental) The name of the collection.

        :stability: experimental
        '''
        result = self._values.get("collection_name")
        assert result is not None, "Required property 'collection_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def credentials_secret_arn(self) -> builtins.str:
        '''(experimental) The ARN of the secret containing MongoDB Atlas credentials.

        :stability: experimental
        '''
        result = self._values.get("credentials_secret_arn")
        assert result is not None, "Required property 'credentials_secret_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def database_name(self) -> builtins.str:
        '''(experimental) The name of the database.

        :stability: experimental
        '''
        result = self._values.get("database_name")
        assert result is not None, "Required property 'database_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def endpoint(self) -> builtins.str:
        '''(experimental) The endpoint URL for MongoDB Atlas.

        :stability: experimental
        '''
        result = self._values.get("endpoint")
        assert result is not None, "Required property 'endpoint' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def field_mapping(self) -> "MongoDbAtlasFieldMapping":
        '''(experimental) The field mapping for MongoDB Atlas.

        :stability: experimental
        '''
        result = self._values.get("field_mapping")
        assert result is not None, "Required property 'field_mapping' is missing"
        return typing.cast("MongoDbAtlasFieldMapping", result)

    @builtins.property
    def vector_index_name(self) -> builtins.str:
        '''(experimental) The name of the vector index.

        :stability: experimental
        '''
        result = self._values.get("vector_index_name")
        assert result is not None, "Required property 'vector_index_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def endpoint_service_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the endpoint service.

        :stability: experimental
        '''
        result = self._values.get("endpoint_service_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def text_index_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the text index.

        :stability: experimental
        '''
        result = self._values.get("text_index_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MongoDBAtlasVectorStoreProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.mongodbAtlas.MongoDbAtlasFieldMapping",
    jsii_struct_bases=[],
    name_mapping={
        "metadata_field": "metadataField",
        "text_field": "textField",
        "vector_field": "vectorField",
    },
)
class MongoDbAtlasFieldMapping:
    def __init__(
        self,
        *,
        metadata_field: builtins.str,
        text_field: builtins.str,
        vector_field: builtins.str,
    ) -> None:
        '''(experimental) Interface for MongoDB Atlas field mapping.

        :param metadata_field: (experimental) The field name for the metadata field.
        :param text_field: (experimental) The field name for the text field.
        :param vector_field: (experimental) The field name for the vector field.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d1dd057c4ced144f0b90a37c5a3a5be83f5eed75fed1ccee2e9cb791e40357d5)
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
        '''(experimental) The field name for the metadata field.

        :stability: experimental
        '''
        result = self._values.get("metadata_field")
        assert result is not None, "Required property 'metadata_field' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def text_field(self) -> builtins.str:
        '''(experimental) The field name for the text field.

        :stability: experimental
        '''
        result = self._values.get("text_field")
        assert result is not None, "Required property 'text_field' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def vector_field(self) -> builtins.str:
        '''(experimental) The field name for the vector field.

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
        return "MongoDbAtlasFieldMapping(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "MongoDBAtlasVectorStore",
    "MongoDBAtlasVectorStoreProps",
    "MongoDbAtlasFieldMapping",
]

publication.publish()

def _typecheckingstub__28a3588f4e105edba1d4a736110b4e04967e17d3a3a5d516fd3c29f2ec528451(
    *,
    collection_name: builtins.str,
    credentials_secret_arn: builtins.str,
    database_name: builtins.str,
    endpoint: builtins.str,
    field_mapping: typing.Union[MongoDbAtlasFieldMapping, typing.Dict[builtins.str, typing.Any]],
    vector_index_name: builtins.str,
    endpoint_service_name: typing.Optional[builtins.str] = None,
    text_index_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d1dd057c4ced144f0b90a37c5a3a5be83f5eed75fed1ccee2e9cb791e40357d5(
    *,
    metadata_field: builtins.str,
    text_field: builtins.str,
    vector_field: builtins.str,
) -> None:
    """Type checking stubs"""
    pass
