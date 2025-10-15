r'''
# Amazon OpenSearch Vector Index Construct Library

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
| ![Java Logo](https://docs.aws.amazon.com/cdk/api/latest/img/java32.png) Java                   | `io.github.cdklabs.generative_ai_cdk_constructs`|
| ![.Net](https://docs.aws.amazon.com/cdk/api/latest/img/dotnet32.png) .Net                   | `CdkLabs.GenerativeAICdkConstructs`|
| ![Go](https://docs.aws.amazon.com/cdk/api/latest/img/go32.png) Go                   | `github.com/cdklabs/generative-ai-cdk-constructs-go/generative-ai-cdk-constructs`|

This construct library provides a resource that creates a vector index on an Amazon OpenSearch Domain. It currently only supports Amazon OpenSearch Serverless.

## Table of contents

* [API](#api)
* [Vector Index](#vector-index)
* [Default values](#default-values)

## API

See the [API documentation](../../../apidocs/namespaces/opensearch_vectorindex/README.md).

## Vector Index

The `VectorIndex` resource connects to OpenSearch and creates an index suitable for use with Amazon Bedrock Knowledge Bases.

TypeScript

```python
import {
  opensearchserverless,
  opensearch_vectorindex,
} from '@cdklabs/generative-ai-cdk-constructs';

const vectorStore = new opensearchserverless.VectorCollection(
  this,
  'VectorCollection'
);

new opensearch_vectorindex.VectorIndex(this, 'VectorIndex', {
  collection: vectorStore,
  indexName: 'bedrock-knowledge-base-default-index',
  vectorField: 'bedrock-knowledge-base-default-vector',
  vectorDimensions: 1536,
  precision: 'float',
  distanceType: 'l2',
  mappings: [
    {
      mappingField: 'AMAZON_BEDROCK_TEXT_CHUNK',
      dataType: 'text',
      filterable: true,
    },
    {
      mappingField: 'AMAZON_BEDROCK_METADATA',
      dataType: 'text',
      filterable: false,
    },
  ],
  analyzer: {
    characterFilters: [opensearchserverless.CharacterFilterType.ICU_NORMALIZER],
    tokenizer: opensearchserverless.TokenizerType.KUROMOJI_TOKENIZER,
    tokenFilters: [
      opensearchserverless.TokenFilterType.KUROMOJI_BASEFORM,
      opensearchserverless.TokenFilterType.JA_STOP,
    ],
  },
});
```

Python

```python
from cdklabs.generative_ai_cdk_constructs import (
    opensearchserverless,
    opensearch_vectorindex,
)

vectorCollection = opensearchserverless.VectorCollection(self, "VectorCollection")

vectorIndex = opensearch_vectorindex.VectorIndex(self, "VectorIndex",
    vector_dimensions= 1536,
    collection=vectorCollection,
    index_name='bedrock-knowledge-base-default-index',
    vector_field='bedrock-knowledge-base-default-vector',
    precision='float',
    distance_type='l2',
    mappings= [
        opensearch_vectorindex.MetadataManagementFieldProps(
            mapping_field='AMAZON_BEDROCK_TEXT_CHUNK',
            data_type='text',
            filterable=True
        ),
        opensearch_vectorindex.MetadataManagementFieldProps(
            mapping_field='AMAZON_BEDROCK_METADATA',
            data_type='text',
            filterable=False
        )
    ],
    analyzer=opensearchserverless.AnalyzerProps(
        character_filters=[opensearchserverless.CharacterFilterType.ICU_NORMALIZER],
        tokenizer=opensearchserverless.TokenizerType.KUROMOJI_TOKENIZER,
        token_filters=[
            opensearchserverless.TokenFilterType.KUROMOJI_BASEFORM,
            opensearchserverless.TokenFilterType.JA_STOP,
        ],
    )
)
```

## Default values

Behind the scenes, the custom resource creates a k-NN vector in the OpenSearch index, allowing to perform different kinds of k-NN search. The knn_vector field is highly configurable and can serve many different k-NN workloads. It is created as follows:

Python

```py
"properties": {
            vector_field: {
                "type": "knn_vector",
                "dimension": dimensions,
                "data_type": precision,
                "method": {
                    "engine": "faiss",
                    "space_type": distance_type,
                    "name": "hnsw",
                    "parameters": {},
                },
            },
            "id": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
        },
```

Users can currently configure the `vector_field`, `dimension`, `data_type`, and `distance_type` fields through the construct interface.

For details on the different settings, you can refer to the [Knn plugin documentation](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/).
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
import constructs as _constructs_77d1e7e8
from ..opensearchserverless import (
    CharacterFilterType as _CharacterFilterType_08604228,
    TokenFilterType as _TokenFilterType_676a4ea9,
    TokenizerType as _TokenizerType_bb83330a,
    VectorCollection as _VectorCollection_91bfdaa9,
)


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.opensearch_vectorindex.Analyzer",
    jsii_struct_bases=[],
    name_mapping={
        "character_filters": "characterFilters",
        "token_filters": "tokenFilters",
        "tokenizer": "tokenizer",
    },
)
class Analyzer:
    def __init__(
        self,
        *,
        character_filters: typing.Sequence[_CharacterFilterType_08604228],
        token_filters: typing.Sequence[_TokenFilterType_676a4ea9],
        tokenizer: _TokenizerType_bb83330a,
    ) -> None:
        '''(experimental) Properties for the Analyzer.

        :param character_filters: (experimental) The analyzers to use.
        :param token_filters: (experimental) The token filters to use.
        :param tokenizer: (experimental) The tokenizer to use.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6fa36e68565a917fb0efe2571a6e2f2d28d637378517db150a0e6267d2e7842b)
            check_type(argname="argument character_filters", value=character_filters, expected_type=type_hints["character_filters"])
            check_type(argname="argument token_filters", value=token_filters, expected_type=type_hints["token_filters"])
            check_type(argname="argument tokenizer", value=tokenizer, expected_type=type_hints["tokenizer"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "character_filters": character_filters,
            "token_filters": token_filters,
            "tokenizer": tokenizer,
        }

    @builtins.property
    def character_filters(self) -> typing.List[_CharacterFilterType_08604228]:
        '''(experimental) The analyzers to use.

        :stability: experimental
        '''
        result = self._values.get("character_filters")
        assert result is not None, "Required property 'character_filters' is missing"
        return typing.cast(typing.List[_CharacterFilterType_08604228], result)

    @builtins.property
    def token_filters(self) -> typing.List[_TokenFilterType_676a4ea9]:
        '''(experimental) The token filters to use.

        :stability: experimental
        '''
        result = self._values.get("token_filters")
        assert result is not None, "Required property 'token_filters' is missing"
        return typing.cast(typing.List[_TokenFilterType_676a4ea9], result)

    @builtins.property
    def tokenizer(self) -> _TokenizerType_bb83330a:
        '''(experimental) The tokenizer to use.

        :stability: experimental
        '''
        result = self._values.get("tokenizer")
        assert result is not None, "Required property 'tokenizer' is missing"
        return typing.cast(_TokenizerType_bb83330a, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Analyzer(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.opensearch_vectorindex.MetadataManagementFieldProps",
    jsii_struct_bases=[],
    name_mapping={
        "data_type": "dataType",
        "filterable": "filterable",
        "mapping_field": "mappingField",
    },
)
class MetadataManagementFieldProps:
    def __init__(
        self,
        *,
        data_type: builtins.str,
        filterable: builtins.bool,
        mapping_field: builtins.str,
    ) -> None:
        '''(experimental) Metadata field definitions.

        :param data_type: (experimental) The data type of the field.
        :param filterable: (experimental) Whether the field is filterable.
        :param mapping_field: (experimental) The name of the field.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bc232715f2e7167be4478ee7ff835dccae7b1ffcbc414d5da6a4de31bf5a23ef)
            check_type(argname="argument data_type", value=data_type, expected_type=type_hints["data_type"])
            check_type(argname="argument filterable", value=filterable, expected_type=type_hints["filterable"])
            check_type(argname="argument mapping_field", value=mapping_field, expected_type=type_hints["mapping_field"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "data_type": data_type,
            "filterable": filterable,
            "mapping_field": mapping_field,
        }

    @builtins.property
    def data_type(self) -> builtins.str:
        '''(experimental) The data type of the field.

        :stability: experimental
        '''
        result = self._values.get("data_type")
        assert result is not None, "Required property 'data_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def filterable(self) -> builtins.bool:
        '''(experimental) Whether the field is filterable.

        :stability: experimental
        '''
        result = self._values.get("filterable")
        assert result is not None, "Required property 'filterable' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def mapping_field(self) -> builtins.str:
        '''(experimental) The name of the field.

        :stability: experimental
        '''
        result = self._values.get("mapping_field")
        assert result is not None, "Required property 'mapping_field' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MetadataManagementFieldProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class VectorIndex(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.opensearch_vectorindex.VectorIndex",
):
    '''(experimental) Deploy a vector index on the collection.

    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        collection: _VectorCollection_91bfdaa9,
        distance_type: builtins.str,
        index_name: builtins.str,
        mappings: typing.Sequence[typing.Union[MetadataManagementFieldProps, typing.Dict[builtins.str, typing.Any]]],
        precision: builtins.str,
        vector_dimensions: jsii.Number,
        vector_field: builtins.str,
        analyzer: typing.Optional[typing.Union[Analyzer, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param collection: (experimental) The OpenSearch Vector Collection.
        :param distance_type: 
        :param index_name: (experimental) The name of the index.
        :param mappings: (experimental) The metadata management fields.
        :param precision: 
        :param vector_dimensions: (experimental) The number of dimensions in the vector.
        :param vector_field: (experimental) The name of the vector field.
        :param analyzer: (experimental) The analyzer to use. Default: - No analyzer.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f5003f7f8d99d7c28d9747284aec10690f601ccd6b2cfbd8d4576c55545a72e0)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = VectorIndexProps(
            collection=collection,
            distance_type=distance_type,
            index_name=index_name,
            mappings=mappings,
            precision=precision,
            vector_dimensions=vector_dimensions,
            vector_field=vector_field,
            analyzer=analyzer,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="indexName")
    def index_name(self) -> builtins.str:
        '''(experimental) The name of the index.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "indexName"))

    @builtins.property
    @jsii.member(jsii_name="vectorDimensions")
    def vector_dimensions(self) -> jsii.Number:
        '''(experimental) The number of dimensions in the vector.

        :stability: experimental
        '''
        return typing.cast(jsii.Number, jsii.get(self, "vectorDimensions"))

    @builtins.property
    @jsii.member(jsii_name="vectorField")
    def vector_field(self) -> builtins.str:
        '''(experimental) The name of the vector field.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "vectorField"))


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.opensearch_vectorindex.VectorIndexProps",
    jsii_struct_bases=[],
    name_mapping={
        "collection": "collection",
        "distance_type": "distanceType",
        "index_name": "indexName",
        "mappings": "mappings",
        "precision": "precision",
        "vector_dimensions": "vectorDimensions",
        "vector_field": "vectorField",
        "analyzer": "analyzer",
    },
)
class VectorIndexProps:
    def __init__(
        self,
        *,
        collection: _VectorCollection_91bfdaa9,
        distance_type: builtins.str,
        index_name: builtins.str,
        mappings: typing.Sequence[typing.Union[MetadataManagementFieldProps, typing.Dict[builtins.str, typing.Any]]],
        precision: builtins.str,
        vector_dimensions: jsii.Number,
        vector_field: builtins.str,
        analyzer: typing.Optional[typing.Union[Analyzer, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) Properties for the VectorIndex.

        :param collection: (experimental) The OpenSearch Vector Collection.
        :param distance_type: 
        :param index_name: (experimental) The name of the index.
        :param mappings: (experimental) The metadata management fields.
        :param precision: 
        :param vector_dimensions: (experimental) The number of dimensions in the vector.
        :param vector_field: (experimental) The name of the vector field.
        :param analyzer: (experimental) The analyzer to use. Default: - No analyzer.

        :stability: experimental
        '''
        if isinstance(analyzer, dict):
            analyzer = Analyzer(**analyzer)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5d660fe6c930253fed67011cc25bd50dfb6c4c58bfc412a7d480a8ef1787f5dd)
            check_type(argname="argument collection", value=collection, expected_type=type_hints["collection"])
            check_type(argname="argument distance_type", value=distance_type, expected_type=type_hints["distance_type"])
            check_type(argname="argument index_name", value=index_name, expected_type=type_hints["index_name"])
            check_type(argname="argument mappings", value=mappings, expected_type=type_hints["mappings"])
            check_type(argname="argument precision", value=precision, expected_type=type_hints["precision"])
            check_type(argname="argument vector_dimensions", value=vector_dimensions, expected_type=type_hints["vector_dimensions"])
            check_type(argname="argument vector_field", value=vector_field, expected_type=type_hints["vector_field"])
            check_type(argname="argument analyzer", value=analyzer, expected_type=type_hints["analyzer"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "collection": collection,
            "distance_type": distance_type,
            "index_name": index_name,
            "mappings": mappings,
            "precision": precision,
            "vector_dimensions": vector_dimensions,
            "vector_field": vector_field,
        }
        if analyzer is not None:
            self._values["analyzer"] = analyzer

    @builtins.property
    def collection(self) -> _VectorCollection_91bfdaa9:
        '''(experimental) The OpenSearch Vector Collection.

        :stability: experimental
        '''
        result = self._values.get("collection")
        assert result is not None, "Required property 'collection' is missing"
        return typing.cast(_VectorCollection_91bfdaa9, result)

    @builtins.property
    def distance_type(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        result = self._values.get("distance_type")
        assert result is not None, "Required property 'distance_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def index_name(self) -> builtins.str:
        '''(experimental) The name of the index.

        :stability: experimental
        '''
        result = self._values.get("index_name")
        assert result is not None, "Required property 'index_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def mappings(self) -> typing.List[MetadataManagementFieldProps]:
        '''(experimental) The metadata management fields.

        :stability: experimental
        '''
        result = self._values.get("mappings")
        assert result is not None, "Required property 'mappings' is missing"
        return typing.cast(typing.List[MetadataManagementFieldProps], result)

    @builtins.property
    def precision(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        result = self._values.get("precision")
        assert result is not None, "Required property 'precision' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def vector_dimensions(self) -> jsii.Number:
        '''(experimental) The number of dimensions in the vector.

        :stability: experimental
        '''
        result = self._values.get("vector_dimensions")
        assert result is not None, "Required property 'vector_dimensions' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def vector_field(self) -> builtins.str:
        '''(experimental) The name of the vector field.

        :stability: experimental
        '''
        result = self._values.get("vector_field")
        assert result is not None, "Required property 'vector_field' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def analyzer(self) -> typing.Optional[Analyzer]:
        '''(experimental) The analyzer to use.

        :default: - No analyzer.

        :stability: experimental
        '''
        result = self._values.get("analyzer")
        return typing.cast(typing.Optional[Analyzer], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VectorIndexProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "Analyzer",
    "MetadataManagementFieldProps",
    "VectorIndex",
    "VectorIndexProps",
]

publication.publish()

def _typecheckingstub__6fa36e68565a917fb0efe2571a6e2f2d28d637378517db150a0e6267d2e7842b(
    *,
    character_filters: typing.Sequence[_CharacterFilterType_08604228],
    token_filters: typing.Sequence[_TokenFilterType_676a4ea9],
    tokenizer: _TokenizerType_bb83330a,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bc232715f2e7167be4478ee7ff835dccae7b1ffcbc414d5da6a4de31bf5a23ef(
    *,
    data_type: builtins.str,
    filterable: builtins.bool,
    mapping_field: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f5003f7f8d99d7c28d9747284aec10690f601ccd6b2cfbd8d4576c55545a72e0(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    collection: _VectorCollection_91bfdaa9,
    distance_type: builtins.str,
    index_name: builtins.str,
    mappings: typing.Sequence[typing.Union[MetadataManagementFieldProps, typing.Dict[builtins.str, typing.Any]]],
    precision: builtins.str,
    vector_dimensions: jsii.Number,
    vector_field: builtins.str,
    analyzer: typing.Optional[typing.Union[Analyzer, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5d660fe6c930253fed67011cc25bd50dfb6c4c58bfc412a7d480a8ef1787f5dd(
    *,
    collection: _VectorCollection_91bfdaa9,
    distance_type: builtins.str,
    index_name: builtins.str,
    mappings: typing.Sequence[typing.Union[MetadataManagementFieldProps, typing.Dict[builtins.str, typing.Any]]],
    precision: builtins.str,
    vector_dimensions: jsii.Number,
    vector_field: builtins.str,
    analyzer: typing.Optional[typing.Union[Analyzer, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
