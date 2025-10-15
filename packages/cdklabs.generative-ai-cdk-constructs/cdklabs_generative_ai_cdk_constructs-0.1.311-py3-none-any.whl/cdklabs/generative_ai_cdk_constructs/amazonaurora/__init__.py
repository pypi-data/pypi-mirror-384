r'''
# Amazon Aurora Vector Store Construct Library

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

This construct library provides a class that defines a `AmazonAuroraVectorStore` construct for an Amazon Aurora to be used for a vector store for a Knowledge Base. Additionally, you can utilize `fromExistingAuroraVectorStore()` method to use your existing Aurora database as a vector DB. `AmazonAuroraVectorStore` is an L3 resource that creates a VPC with 3 subnets (public, private with NAT Gateway, private without NAT Gateway) and Amazon Aurora Serverless V2 Cluster. The cluster has 1 writer/reader instance with latest supported PostgreSQL version (currently it is 15.5) and having the following cofiguration: min capacity 0.5, max capacity 4. Lambda custom resource executes required pgvector and Amazon Bedrock Knowledge Base SQL queries (see more [here](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.VectorDB.html)) against Aurora cluster during deployment. The secret containing databases credentials is being deployed and securely stored in AWS Secrets Manager. You must specify the same embeddings model that you are going to use in KnowledgeBase construct. Due to the nature of provisioning RDS cluster it takes a long time (over 20-25 minutes) to both deploying and destroying construct so please take this in consideration.

## Table of contents

* [API](#api)
* [Amazon Aurora Vector Store](#amazon-aurora-vector-store)
* [fromExistingAuroraVectorStore()](#fromExistingAuroraVectorStore())

## API

See the [API documentation](../../../apidocs/namespaces/amazonaurora/README.md).

## Amazon Aurora Vector Store

TypeScript

```python
import { amazonaurora, foundation_models } from '@cdklabs/generative-ai-cdk-constructs';

new amazonaurora.AmazonAuroraVectorStore(stack, 'AuroraVectorStore', {
  embeddingsModel: foundation_models.BedrockFoundationModel.COHERE_EMBED_ENGLISH_V3,
});
```

Python

```python

from cdklabs.generative_ai_cdk_constructs import (
    amazonaurora,
    foundation_models
)

aurora = amazonaurora.AmazonAuroraVectorStore(self, 'AuroraVectorStore',
            embeddings_model=foundation_models.BedrockFoundationModel.COHERE_EMBED_ENGLISH_V3,
        )
```

## fromExistingAuroraVectorStore()

You can import your existing Aurora DB to be used as a vector DB for a knowledge base. **Note** - you need to provide `clusterIdentifier`, `databaseName`, `vpc`, `secret` and `auroraSecurityGroupName` used in deployment of your existing RDS Amazon Aurora DB, as well as `embeddingsModel` that you want to be used by a Knowledge Base for chunking. Additionally, your stack's **env** needs to contain `region` and `account` variables.

TypeScript

```python
import { amazonaurora, foundation_models, bedrock } from '@cdklabs/generative-ai-cdk-constructs';
import * as cdk from 'aws-cdk-lib';

const auroraDb = amazonaurora.AmazonAuroraVectorStore.fromExistingAuroraVectorStore(stack, 'ExistingAuroraVectorStore', {
  clusterIdentifier: 'aurora-serverless-vector-cluster',
  databaseName: 'bedrock_vector_db',
  schemaName: 'bedrock_integration',
  tableName: 'bedrock_kb',
  vectorField: 'embedding',
  textField: 'chunks',
  metadataField: 'metadata',
  primaryKeyField: 'id',
  embeddingsModelVectorDimension: bedrock.BedrockFoundationModel.COHERE_EMBED_ENGLISH_V3.vectorDimensions!,
  vpc: cdk.aws_ec2.Vpc.fromLookup(stack, 'VPC', {
    vpcId: 'vpc-0c1a234567ee8bc90',
  }),
  auroraSecurityGroup: cdk.aws_ec2.SecurityGroup.fromSecurityGroupId(
    stack,
    'AuroraSecurityGroup',
    'sg-012456789'
  ),
  secret: cdk.aws_rds.DatabaseSecret.fromSecretCompleteArn(
    stack,
    'Secret',
    cdk.Stack.of(stack).formatArn({
      service: 'secretsmanager',
      resource: 'secret',
      resourceName: 'rds-db-credentials/cluster-1234567890',
      region: cdk.Stack.of(stack).region,
      account: cdk.Stack.of(stack).account,
      arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
    }),
  ),
});

const kb = new bedrock.VectorKnowledgeBase(this, "KnowledgeBase", {
  embeddingsModel: foundation_models.BedrockFoundationModel.COHERE_EMBED_ENGLISH_V3,
  vectorStore: auroraDb,
  instruction:
    "Use this knowledge base to answer questions about books. " +
    "It contains the full text of novels.",
});

const docBucket = new cdk.aws_s3.Bucket(this, "DocBucket");

new bedrock.S3DataSource(this, "DataSource", {
  bucket: docBucket,
  knowledgeBase: kb,
  dataSourceName: "books",
  chunkingStrategy: bedrock.ChunkingStrategy.fixedSize({
    maxTokens: 500,
    overlapPercentage: 20,
  }),
});
```

Python

```python
from aws_cdk import (
    aws_s3 as s3,
    aws_rds as rds,
    aws_ec2 as ec2,
    Stack,
    ArnFormat
)
from cdklabs.generative_ai_cdk_constructs import (
    bedrock,
    amazonaurora,
    foundation_models
)

aurora_db = amazonaurora.AmazonAuroraVectorStore.from_existing_aurora_vector_store(
    self, 'ExistingAuroraVectorStore',
    cluster_identifier='aurora-serverless-vector-cluster',
    database_name='bedrock_vector_db',
    schema_name='bedrock_integration',
    table_name='bedrock_kb',
    vector_field='embedding',
    text_field='chunks',
    metadata_field='metadata',
    primary_key_field='id',
    embeddings_model_vector_dimension=bedrock.BedrockFoundationModel.COHERE_EMBED_ENGLISH_V3.vectorDimensions!,
    vpc=ec2.Vpc.from_lookup(self, 'VPC', vpc_id='vpc-0c1a234567ee8bc90'),
    aurora_security_group=ec2.SecurityGroup.from_security_group_id(
        self,
        'AuroraSecurityGroup',
        'sg-01245678'
    ),
    secret=rds.DatabaseSecret.from_secret_complete_arn(
        self,
        'Secret',
        Stack.of(self).format_arn(
            service= 'secretsmanager',
            resource= 'secret',
            resource_name= 'rds-db-credentials/cluster-1234567890',
            region= Stack.of(self).region,
            account= Stack.of(self).account,
            arn_format= ArnFormat.COLON_RESOURCE_NAME
        )
    )
)

kb = bedrock.VectorKnowledgeBase(self, 'KnowledgeBase',
            embeddings_model= foundation_models.BedrockFoundationModel.TITAN_EMBED_TEXT_V2_1024,
            vector_store=aurora_db,
            instruction=  'Use this knowledge base to answer questions about books. ' +
    'It contains the full text of novels.'
)

docBucket = s3.Bucket(self, 'DockBucket')

bedrock.S3DataSource(self, 'DataSource',
    bucket= docBucket,
    knowledge_base=kb,
    data_source_name='books',
    chunking_strategy= bedrock.ChunkingStrategy.FIXED_SIZE,
    max_tokens=500,
    overlap_percentage=20
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

import aws_cdk as _aws_cdk_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_rds as _aws_cdk_aws_rds_ceddda9d
import aws_cdk.aws_secretsmanager as _aws_cdk_aws_secretsmanager_ceddda9d
import constructs as _constructs_77d1e7e8


class AmazonAuroraVectorStore(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.amazonaurora.AmazonAuroraVectorStore",
):
    '''
    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        cluster_id: typing.Optional[builtins.str] = None,
        database_name: typing.Optional[builtins.str] = None,
        postgre_sql_version: typing.Optional[_aws_cdk_aws_rds_ceddda9d.AuroraPostgresEngineVersion] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        embeddings_model_vector_dimension: jsii.Number,
        metadata_field: typing.Optional[builtins.str] = None,
        primary_key_field: typing.Optional[builtins.str] = None,
        schema_name: typing.Optional[builtins.str] = None,
        table_name: typing.Optional[builtins.str] = None,
        text_field: typing.Optional[builtins.str] = None,
        vector_field: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param cluster_id: (experimental) Cluster identifier.
        :param database_name: (experimental) The name of the database for the Aurora Vector Store.
        :param postgre_sql_version: (experimental) The version of PostgreSQL to use for the Aurora Vector Store. By default, the latest supported version will be used.
        :param vpc: (experimental) User's VPC in which they want to deploy Aurora Database.
        :param embeddings_model_vector_dimension: (experimental) The embeddings model dimension used for the Aurora Vector Store. The vector dimensions of the model must match the dimensions used in the KnowledgeBase construct.
        :param metadata_field: (experimental) The field name for the metadata column in the Aurora Vector Store.
        :param primary_key_field: (experimental) The primary key field for the Aurora Vector Store table.
        :param schema_name: (experimental) The schema name for the Aurora Vector Store.
        :param table_name: (experimental) The name of the table for the Aurora Vector Store.
        :param text_field: (experimental) The field name for the text column in the Aurora Vector Store.
        :param vector_field: (experimental) The field name for the vector column in the Aurora Vector Store.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__742bfb7e146b244ee6d699c1caaf86c6f1822a15bdb42de183e3d4f29f4f8e24)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AmazonAuroraVectorStoreProps(
            cluster_id=cluster_id,
            database_name=database_name,
            postgre_sql_version=postgre_sql_version,
            vpc=vpc,
            embeddings_model_vector_dimension=embeddings_model_vector_dimension,
            metadata_field=metadata_field,
            primary_key_field=primary_key_field,
            schema_name=schema_name,
            table_name=table_name,
            text_field=text_field,
            vector_field=vector_field,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromExistingAuroraVectorStore")
    @builtins.classmethod
    def from_existing_aurora_vector_store(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
        cluster_identifier: builtins.str,
        database_name: builtins.str,
        secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        embeddings_model_vector_dimension: jsii.Number,
        metadata_field: typing.Optional[builtins.str] = None,
        primary_key_field: typing.Optional[builtins.str] = None,
        schema_name: typing.Optional[builtins.str] = None,
        table_name: typing.Optional[builtins.str] = None,
        text_field: typing.Optional[builtins.str] = None,
        vector_field: typing.Optional[builtins.str] = None,
    ) -> "ExistingAmazonAuroraVectorStore":
        '''(experimental) Creates an instance of AmazonAuroraVectorStore using existing Aurora Vector Store properties.

        You need to provide your existing Aurora Vector Store properties
        such as ``databaseName``, ``clusterIdentifier``, ``vpc`` where database is deployed,
        ``secret`` containing username and password for authentication to database,
        and ``auroraSecurityGroup`` with the ecurity group that was used for the database.

        :param scope: - The scope in which to define the construct.
        :param id: - The ID of the construct.
        :param aurora_security_group: (experimental) The Security group associated with the RDS Aurora instance. This security group allows access to the Aurora Vector Store from Lambda's custom resource running pgVector SQL commands.
        :param cluster_identifier: (experimental) The unique cluster identifier of your Aurora RDS cluster.
        :param database_name: (experimental) The name of the database for the Aurora Vector Store.
        :param secret: (experimental) The secret containing the database credentials. The secret must contain ``host``, ``port``, ``username``, ``password`` and ``dbname`` values.
        :param vpc: (experimental) The VPC in which the existing Aurora Vector Store is located.
        :param embeddings_model_vector_dimension: (experimental) The embeddings model dimension used for the Aurora Vector Store. The vector dimensions of the model must match the dimensions used in the KnowledgeBase construct.
        :param metadata_field: (experimental) The field name for the metadata column in the Aurora Vector Store.
        :param primary_key_field: (experimental) The primary key field for the Aurora Vector Store table.
        :param schema_name: (experimental) The schema name for the Aurora Vector Store.
        :param table_name: (experimental) The name of the table for the Aurora Vector Store.
        :param text_field: (experimental) The field name for the text column in the Aurora Vector Store.
        :param vector_field: (experimental) The field name for the vector column in the Aurora Vector Store.

        :return: An instance of AmazonAuroraVectorStore.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__684c8e9c9331fe4162c5fcb9208179405aa3a01d2039a3b9ed61ae8717229b1d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ExistingAmazonAuroraVectorStoreProps(
            aurora_security_group=aurora_security_group,
            cluster_identifier=cluster_identifier,
            database_name=database_name,
            secret=secret,
            vpc=vpc,
            embeddings_model_vector_dimension=embeddings_model_vector_dimension,
            metadata_field=metadata_field,
            primary_key_field=primary_key_field,
            schema_name=schema_name,
            table_name=table_name,
            text_field=text_field,
            vector_field=vector_field,
        )

        return typing.cast("ExistingAmazonAuroraVectorStore", jsii.sinvoke(cls, "fromExistingAuroraVectorStore", [scope, id, props]))

    @jsii.member(jsii_name="addIngressRuleToAuroraSecurityGroup")
    def _add_ingress_rule_to_aurora_security_group(
        self,
        lambda_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
        aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    ) -> None:
        '''
        :param lambda_security_group: -
        :param aurora_security_group: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cc2cb74d2717f8a9267940982149b22a48909ab295eaee1cfbe006c645401b91)
            check_type(argname="argument lambda_security_group", value=lambda_security_group, expected_type=type_hints["lambda_security_group"])
            check_type(argname="argument aurora_security_group", value=aurora_security_group, expected_type=type_hints["aurora_security_group"])
        return typing.cast(None, jsii.invoke(self, "addIngressRuleToAuroraSecurityGroup", [lambda_security_group, aurora_security_group]))

    @jsii.member(jsii_name="createAuroraPgCRPolicy")
    def _create_aurora_pg_cr_policy(
        self,
        cluster_identifier: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.ManagedPolicy:
        '''
        :param cluster_identifier: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__941b28cb1b2ce8505829999aa8c268507353ecfd5d99e81bf8de1c61e92f9abe)
            check_type(argname="argument cluster_identifier", value=cluster_identifier, expected_type=type_hints["cluster_identifier"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.ManagedPolicy, jsii.invoke(self, "createAuroraPgCRPolicy", [cluster_identifier]))

    @jsii.member(jsii_name="createLambdaSecurityGroup")
    def _create_lambda_security_group(
        self,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    ) -> _aws_cdk_aws_ec2_ceddda9d.SecurityGroup:
        '''
        :param vpc: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__81514e055a1f329a7c85955ab93d851b60a0a191bf155d1c171dfb591cf735d5)
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.SecurityGroup, jsii.invoke(self, "createLambdaSecurityGroup", [vpc]))

    @jsii.member(jsii_name="generateResourceArn")
    def _generate_resource_arn(self, cluster_identifier: builtins.str) -> builtins.str:
        '''
        :param cluster_identifier: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f959b075d03b9890bed2500d557cb2023d94825521b2839de462db00e399df84)
            check_type(argname="argument cluster_identifier", value=cluster_identifier, expected_type=type_hints["cluster_identifier"])
        return typing.cast(builtins.str, jsii.invoke(self, "generateResourceArn", [cluster_identifier]))

    @jsii.member(jsii_name="setupCustomResource")
    def _setup_custom_resource(
        self,
        database_cluster_resources: typing.Union["DatabaseClusterResources", typing.Dict[builtins.str, typing.Any]],
        lambda_security_group: _aws_cdk_aws_ec2_ceddda9d.SecurityGroup,
        aurora_pg_cr_policy: _aws_cdk_aws_iam_ceddda9d.ManagedPolicy,
    ) -> _aws_cdk_ceddda9d.CustomResource:
        '''
        :param database_cluster_resources: -
        :param lambda_security_group: -
        :param aurora_pg_cr_policy: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6311e0a104e6f31ecd1afdb00615bfd69c7f7f6d7465d09ca0185b9e17fd3266)
            check_type(argname="argument database_cluster_resources", value=database_cluster_resources, expected_type=type_hints["database_cluster_resources"])
            check_type(argname="argument lambda_security_group", value=lambda_security_group, expected_type=type_hints["lambda_security_group"])
            check_type(argname="argument aurora_pg_cr_policy", value=aurora_pg_cr_policy, expected_type=type_hints["aurora_pg_cr_policy"])
        return typing.cast(_aws_cdk_ceddda9d.CustomResource, jsii.invoke(self, "setupCustomResource", [database_cluster_resources, lambda_security_group, aurora_pg_cr_policy]))

    @jsii.member(jsii_name="setupDatabaseClusterResources")
    def _setup_database_cluster_resources(
        self,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
        cluster_identifier: builtins.str,
        aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    ) -> "DatabaseClusterResources":
        '''
        :param vpc: -
        :param secret: -
        :param cluster_identifier: -
        :param aurora_security_group: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c97d3722603742a7d5d91d2da3e7a42783edca93c8a1f0c35bbc65730313f35b)
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
            check_type(argname="argument secret", value=secret, expected_type=type_hints["secret"])
            check_type(argname="argument cluster_identifier", value=cluster_identifier, expected_type=type_hints["cluster_identifier"])
            check_type(argname="argument aurora_security_group", value=aurora_security_group, expected_type=type_hints["aurora_security_group"])
        return typing.cast("DatabaseClusterResources", jsii.invoke(self, "setupDatabaseClusterResources", [vpc, secret, cluster_identifier, aurora_security_group]))

    @builtins.property
    @jsii.member(jsii_name="credentialsSecretArn")
    def credentials_secret_arn(self) -> builtins.str:
        '''(experimental) The Secret ARN of your Amazon Aurora DB cluster.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "credentialsSecretArn"))

    @builtins.property
    @jsii.member(jsii_name="databaseName")
    def database_name(self) -> builtins.str:
        '''(experimental) The name of the database for the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "databaseName"))

    @builtins.property
    @jsii.member(jsii_name="embeddingsModelVectorDimension")
    def embeddings_model_vector_dimension(self) -> jsii.Number:
        '''(experimental) The embeddings model dimension used for the Aurora Vector Store.

        The vector dimensions of the model must match the dimensions
        used in the KnowledgeBase construct.

        :stability: experimental
        '''
        return typing.cast(jsii.Number, jsii.get(self, "embeddingsModelVectorDimension"))

    @builtins.property
    @jsii.member(jsii_name="metadataField")
    def metadata_field(self) -> builtins.str:
        '''(experimental) The field name for the metadata column in the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "metadataField"))

    @builtins.property
    @jsii.member(jsii_name="primaryKeyField")
    def primary_key_field(self) -> builtins.str:
        '''(experimental) The primary key field for the Aurora Vector Store table.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "primaryKeyField"))

    @builtins.property
    @jsii.member(jsii_name="resourceArn")
    def resource_arn(self) -> builtins.str:
        '''(experimental) The ARN of your Amazon Aurora DB cluster.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "resourceArn"))

    @builtins.property
    @jsii.member(jsii_name="schemaName")
    def schema_name(self) -> builtins.str:
        '''(experimental) The schema name for the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "schemaName"))

    @builtins.property
    @jsii.member(jsii_name="tableName")
    def table_name(self) -> builtins.str:
        '''(experimental) The name of the table for the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "tableName"))

    @builtins.property
    @jsii.member(jsii_name="textField")
    def text_field(self) -> builtins.str:
        '''(experimental) The field name for the text column in the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "textField"))

    @builtins.property
    @jsii.member(jsii_name="vectorField")
    def vector_field(self) -> builtins.str:
        '''(experimental) The field name for the vector column in the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "vectorField"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC of your Amazon Aurora DB cluster.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.amazonaurora.BaseAuroraVectorStoreProps",
    jsii_struct_bases=[],
    name_mapping={
        "embeddings_model_vector_dimension": "embeddingsModelVectorDimension",
        "metadata_field": "metadataField",
        "primary_key_field": "primaryKeyField",
        "schema_name": "schemaName",
        "table_name": "tableName",
        "text_field": "textField",
        "vector_field": "vectorField",
    },
)
class BaseAuroraVectorStoreProps:
    def __init__(
        self,
        *,
        embeddings_model_vector_dimension: jsii.Number,
        metadata_field: typing.Optional[builtins.str] = None,
        primary_key_field: typing.Optional[builtins.str] = None,
        schema_name: typing.Optional[builtins.str] = None,
        table_name: typing.Optional[builtins.str] = None,
        text_field: typing.Optional[builtins.str] = None,
        vector_field: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Base properties for an Aurora Vector Store.

        :param embeddings_model_vector_dimension: (experimental) The embeddings model dimension used for the Aurora Vector Store. The vector dimensions of the model must match the dimensions used in the KnowledgeBase construct.
        :param metadata_field: (experimental) The field name for the metadata column in the Aurora Vector Store.
        :param primary_key_field: (experimental) The primary key field for the Aurora Vector Store table.
        :param schema_name: (experimental) The schema name for the Aurora Vector Store.
        :param table_name: (experimental) The name of the table for the Aurora Vector Store.
        :param text_field: (experimental) The field name for the text column in the Aurora Vector Store.
        :param vector_field: (experimental) The field name for the vector column in the Aurora Vector Store.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8c590d53e38be1c52846d1063c597e22b13d544913eee79389f549dbb453f2bf)
            check_type(argname="argument embeddings_model_vector_dimension", value=embeddings_model_vector_dimension, expected_type=type_hints["embeddings_model_vector_dimension"])
            check_type(argname="argument metadata_field", value=metadata_field, expected_type=type_hints["metadata_field"])
            check_type(argname="argument primary_key_field", value=primary_key_field, expected_type=type_hints["primary_key_field"])
            check_type(argname="argument schema_name", value=schema_name, expected_type=type_hints["schema_name"])
            check_type(argname="argument table_name", value=table_name, expected_type=type_hints["table_name"])
            check_type(argname="argument text_field", value=text_field, expected_type=type_hints["text_field"])
            check_type(argname="argument vector_field", value=vector_field, expected_type=type_hints["vector_field"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "embeddings_model_vector_dimension": embeddings_model_vector_dimension,
        }
        if metadata_field is not None:
            self._values["metadata_field"] = metadata_field
        if primary_key_field is not None:
            self._values["primary_key_field"] = primary_key_field
        if schema_name is not None:
            self._values["schema_name"] = schema_name
        if table_name is not None:
            self._values["table_name"] = table_name
        if text_field is not None:
            self._values["text_field"] = text_field
        if vector_field is not None:
            self._values["vector_field"] = vector_field

    @builtins.property
    def embeddings_model_vector_dimension(self) -> jsii.Number:
        '''(experimental) The embeddings model dimension used for the Aurora Vector Store.

        The vector dimensions of the model must match the dimensions
        used in the KnowledgeBase construct.

        :stability: experimental
        '''
        result = self._values.get("embeddings_model_vector_dimension")
        assert result is not None, "Required property 'embeddings_model_vector_dimension' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def metadata_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The field name for the metadata column in the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("metadata_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def primary_key_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The primary key field for the Aurora Vector Store table.

        :stability: experimental
        '''
        result = self._values.get("primary_key_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def schema_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The schema name for the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("schema_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def table_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the table for the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("table_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def text_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The field name for the text column in the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("text_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vector_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The field name for the vector column in the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("vector_field")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BaseAuroraVectorStoreProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.amazonaurora.DatabaseClusterResources",
    jsii_struct_bases=[],
    name_mapping={
        "aurora_security_group": "auroraSecurityGroup",
        "cluster_identifier": "clusterIdentifier",
        "resource_arn": "resourceArn",
        "secret": "secret",
        "vpc": "vpc",
        "aurora_cluster": "auroraCluster",
    },
)
class DatabaseClusterResources:
    def __init__(
        self,
        *,
        aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
        cluster_identifier: builtins.str,
        resource_arn: builtins.str,
        secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        aurora_cluster: typing.Optional[_aws_cdk_aws_rds_ceddda9d.DatabaseCluster] = None,
    ) -> None:
        '''(experimental) Interface representing the resources required for a database cluster.

        :param aurora_security_group: (experimental) The security group associated with the Aurora cluster.
        :param cluster_identifier: (experimental) The unique cluster identifier of the Aurora RDS cluster.
        :param resource_arn: (experimental) The ARN of your existing Amazon Aurora DB cluster.
        :param secret: (experimental) The secret containing the database credentials. The secret must contain ``username`` and ``password`` values.
        :param vpc: (experimental) The VPC in which the database cluster is located.
        :param aurora_cluster: (experimental) The Amazon Aurora RDS cluster.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__190d2665ff987b4762992f96a160574058e05079350349a93202fcb7ba8c960c)
            check_type(argname="argument aurora_security_group", value=aurora_security_group, expected_type=type_hints["aurora_security_group"])
            check_type(argname="argument cluster_identifier", value=cluster_identifier, expected_type=type_hints["cluster_identifier"])
            check_type(argname="argument resource_arn", value=resource_arn, expected_type=type_hints["resource_arn"])
            check_type(argname="argument secret", value=secret, expected_type=type_hints["secret"])
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
            check_type(argname="argument aurora_cluster", value=aurora_cluster, expected_type=type_hints["aurora_cluster"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "aurora_security_group": aurora_security_group,
            "cluster_identifier": cluster_identifier,
            "resource_arn": resource_arn,
            "secret": secret,
            "vpc": vpc,
        }
        if aurora_cluster is not None:
            self._values["aurora_cluster"] = aurora_cluster

    @builtins.property
    def aurora_security_group(self) -> _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup:
        '''(experimental) The security group associated with the Aurora cluster.

        :stability: experimental
        '''
        result = self._values.get("aurora_security_group")
        assert result is not None, "Required property 'aurora_security_group' is missing"
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup, result)

    @builtins.property
    def cluster_identifier(self) -> builtins.str:
        '''(experimental) The unique cluster identifier of the Aurora RDS cluster.

        :stability: experimental
        '''
        result = self._values.get("cluster_identifier")
        assert result is not None, "Required property 'cluster_identifier' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_arn(self) -> builtins.str:
        '''(experimental) The ARN of your existing Amazon Aurora DB cluster.

        :stability: experimental
        '''
        result = self._values.get("resource_arn")
        assert result is not None, "Required property 'resource_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def secret(self) -> _aws_cdk_aws_secretsmanager_ceddda9d.ISecret:
        '''(experimental) The secret containing the database credentials.

        The secret must contain ``username`` and ``password`` values.

        :stability: experimental
        '''
        result = self._values.get("secret")
        assert result is not None, "Required property 'secret' is missing"
        return typing.cast(_aws_cdk_aws_secretsmanager_ceddda9d.ISecret, result)

    @builtins.property
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC in which the database cluster is located.

        :stability: experimental
        '''
        result = self._values.get("vpc")
        assert result is not None, "Required property 'vpc' is missing"
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, result)

    @builtins.property
    def aurora_cluster(
        self,
    ) -> typing.Optional[_aws_cdk_aws_rds_ceddda9d.DatabaseCluster]:
        '''(experimental) The Amazon Aurora RDS cluster.

        :stability: experimental
        '''
        result = self._values.get("aurora_cluster")
        return typing.cast(typing.Optional[_aws_cdk_aws_rds_ceddda9d.DatabaseCluster], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DatabaseClusterResources(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ExistingAmazonAuroraVectorStore(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdklabs/generative-ai-cdk-constructs.amazonaurora.ExistingAmazonAuroraVectorStore",
):
    '''
    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
        cluster_identifier: builtins.str,
        database_name: builtins.str,
        secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        embeddings_model_vector_dimension: jsii.Number,
        metadata_field: typing.Optional[builtins.str] = None,
        primary_key_field: typing.Optional[builtins.str] = None,
        schema_name: typing.Optional[builtins.str] = None,
        table_name: typing.Optional[builtins.str] = None,
        text_field: typing.Optional[builtins.str] = None,
        vector_field: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param aurora_security_group: (experimental) The Security group associated with the RDS Aurora instance. This security group allows access to the Aurora Vector Store from Lambda's custom resource running pgVector SQL commands.
        :param cluster_identifier: (experimental) The unique cluster identifier of your Aurora RDS cluster.
        :param database_name: (experimental) The name of the database for the Aurora Vector Store.
        :param secret: (experimental) The secret containing the database credentials. The secret must contain ``host``, ``port``, ``username``, ``password`` and ``dbname`` values.
        :param vpc: (experimental) The VPC in which the existing Aurora Vector Store is located.
        :param embeddings_model_vector_dimension: (experimental) The embeddings model dimension used for the Aurora Vector Store. The vector dimensions of the model must match the dimensions used in the KnowledgeBase construct.
        :param metadata_field: (experimental) The field name for the metadata column in the Aurora Vector Store.
        :param primary_key_field: (experimental) The primary key field for the Aurora Vector Store table.
        :param schema_name: (experimental) The schema name for the Aurora Vector Store.
        :param table_name: (experimental) The name of the table for the Aurora Vector Store.
        :param text_field: (experimental) The field name for the text column in the Aurora Vector Store.
        :param vector_field: (experimental) The field name for the vector column in the Aurora Vector Store.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3a6ad5fd56ef45d9d088efe46462a9e2c17eb77657b23d1eb5ca910b80f3e89d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ExistingAmazonAuroraVectorStoreProps(
            aurora_security_group=aurora_security_group,
            cluster_identifier=cluster_identifier,
            database_name=database_name,
            secret=secret,
            vpc=vpc,
            embeddings_model_vector_dimension=embeddings_model_vector_dimension,
            metadata_field=metadata_field,
            primary_key_field=primary_key_field,
            schema_name=schema_name,
            table_name=table_name,
            text_field=text_field,
            vector_field=vector_field,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="addIngressRuleToAuroraSecurityGroup")
    def _add_ingress_rule_to_aurora_security_group(
        self,
        lambda_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
        aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    ) -> None:
        '''
        :param lambda_security_group: -
        :param aurora_security_group: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9733000e2b4ac63c0d9de1a42f4bdb4f8293565c07ba3df614e4428d9de2c91f)
            check_type(argname="argument lambda_security_group", value=lambda_security_group, expected_type=type_hints["lambda_security_group"])
            check_type(argname="argument aurora_security_group", value=aurora_security_group, expected_type=type_hints["aurora_security_group"])
        return typing.cast(None, jsii.invoke(self, "addIngressRuleToAuroraSecurityGroup", [lambda_security_group, aurora_security_group]))

    @jsii.member(jsii_name="createAuroraPgCRPolicy")
    def _create_aurora_pg_cr_policy(
        self,
        cluster_identifier: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.ManagedPolicy:
        '''
        :param cluster_identifier: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__22897b3199ef65f202d7ebae59e485787628c0fb79cf70fd00b438f70ca23577)
            check_type(argname="argument cluster_identifier", value=cluster_identifier, expected_type=type_hints["cluster_identifier"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.ManagedPolicy, jsii.invoke(self, "createAuroraPgCRPolicy", [cluster_identifier]))

    @jsii.member(jsii_name="createLambdaSecurityGroup")
    def _create_lambda_security_group(
        self,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    ) -> _aws_cdk_aws_ec2_ceddda9d.SecurityGroup:
        '''
        :param vpc: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8a2e9f5492e0ce5c908783fc73180578f5115dcd57a19dafee6c721c9a043db9)
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.SecurityGroup, jsii.invoke(self, "createLambdaSecurityGroup", [vpc]))

    @jsii.member(jsii_name="generateResourceArn")
    def _generate_resource_arn(self, cluster_identifier: builtins.str) -> builtins.str:
        '''
        :param cluster_identifier: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f501fd1fe366e35135b325e46bc95a6d48ef5a708ef1465e43f8bf4186ad9a92)
            check_type(argname="argument cluster_identifier", value=cluster_identifier, expected_type=type_hints["cluster_identifier"])
        return typing.cast(builtins.str, jsii.invoke(self, "generateResourceArn", [cluster_identifier]))

    @jsii.member(jsii_name="setupCustomResource")
    def _setup_custom_resource(
        self,
        database_cluster_resources: typing.Union[DatabaseClusterResources, typing.Dict[builtins.str, typing.Any]],
        lambda_security_group: _aws_cdk_aws_ec2_ceddda9d.SecurityGroup,
        aurora_pg_cr_policy: _aws_cdk_aws_iam_ceddda9d.ManagedPolicy,
    ) -> _aws_cdk_ceddda9d.CustomResource:
        '''
        :param database_cluster_resources: -
        :param lambda_security_group: -
        :param aurora_pg_cr_policy: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__926fb08fb8538f889d4d7128a374b09f3bd2fd8d30a61b65ee5964e7250f97e6)
            check_type(argname="argument database_cluster_resources", value=database_cluster_resources, expected_type=type_hints["database_cluster_resources"])
            check_type(argname="argument lambda_security_group", value=lambda_security_group, expected_type=type_hints["lambda_security_group"])
            check_type(argname="argument aurora_pg_cr_policy", value=aurora_pg_cr_policy, expected_type=type_hints["aurora_pg_cr_policy"])
        return typing.cast(_aws_cdk_ceddda9d.CustomResource, jsii.invoke(self, "setupCustomResource", [database_cluster_resources, lambda_security_group, aurora_pg_cr_policy]))

    @jsii.member(jsii_name="setupDatabaseClusterResources")
    def _setup_database_cluster_resources(
        self,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
        cluster_identifier: builtins.str,
        aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    ) -> DatabaseClusterResources:
        '''
        :param vpc: -
        :param secret: -
        :param cluster_identifier: -
        :param aurora_security_group: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b0c4703a70d70feef7e48462143c004e3446ea37ab923439b9f3028f0bf513de)
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
            check_type(argname="argument secret", value=secret, expected_type=type_hints["secret"])
            check_type(argname="argument cluster_identifier", value=cluster_identifier, expected_type=type_hints["cluster_identifier"])
            check_type(argname="argument aurora_security_group", value=aurora_security_group, expected_type=type_hints["aurora_security_group"])
        return typing.cast(DatabaseClusterResources, jsii.invoke(self, "setupDatabaseClusterResources", [vpc, secret, cluster_identifier, aurora_security_group]))

    @builtins.property
    @jsii.member(jsii_name="credentialsSecretArn")
    def credentials_secret_arn(self) -> builtins.str:
        '''(experimental) The Secret ARN of your Amazon Aurora DB cluster.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "credentialsSecretArn"))

    @builtins.property
    @jsii.member(jsii_name="databaseName")
    def database_name(self) -> builtins.str:
        '''(experimental) The name of the database for the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "databaseName"))

    @builtins.property
    @jsii.member(jsii_name="embeddingsModelVectorDimension")
    def embeddings_model_vector_dimension(self) -> jsii.Number:
        '''(experimental) The embeddings model dimension used for the Aurora Vector Store.

        The vector dimensions of the model must match the dimensions
        used in the KnowledgeBase construct.

        :stability: experimental
        '''
        return typing.cast(jsii.Number, jsii.get(self, "embeddingsModelVectorDimension"))

    @builtins.property
    @jsii.member(jsii_name="metadataField")
    def metadata_field(self) -> builtins.str:
        '''(experimental) The field name for the metadata column in the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "metadataField"))

    @builtins.property
    @jsii.member(jsii_name="primaryKeyField")
    def primary_key_field(self) -> builtins.str:
        '''(experimental) The primary key field for the Aurora Vector Store table.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "primaryKeyField"))

    @builtins.property
    @jsii.member(jsii_name="resourceArn")
    def resource_arn(self) -> builtins.str:
        '''(experimental) The ARN of your Amazon Aurora DB cluster.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "resourceArn"))

    @builtins.property
    @jsii.member(jsii_name="schemaName")
    def schema_name(self) -> builtins.str:
        '''(experimental) The schema name for the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "schemaName"))

    @builtins.property
    @jsii.member(jsii_name="tableName")
    def table_name(self) -> builtins.str:
        '''(experimental) The name of the table for the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "tableName"))

    @builtins.property
    @jsii.member(jsii_name="textField")
    def text_field(self) -> builtins.str:
        '''(experimental) The field name for the text column in the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "textField"))

    @builtins.property
    @jsii.member(jsii_name="vectorField")
    def vector_field(self) -> builtins.str:
        '''(experimental) The field name for the vector column in the Aurora Vector Store.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "vectorField"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC of your Amazon Aurora DB cluster.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.amazonaurora.ExistingAmazonAuroraVectorStoreProps",
    jsii_struct_bases=[BaseAuroraVectorStoreProps],
    name_mapping={
        "embeddings_model_vector_dimension": "embeddingsModelVectorDimension",
        "metadata_field": "metadataField",
        "primary_key_field": "primaryKeyField",
        "schema_name": "schemaName",
        "table_name": "tableName",
        "text_field": "textField",
        "vector_field": "vectorField",
        "aurora_security_group": "auroraSecurityGroup",
        "cluster_identifier": "clusterIdentifier",
        "database_name": "databaseName",
        "secret": "secret",
        "vpc": "vpc",
    },
)
class ExistingAmazonAuroraVectorStoreProps(BaseAuroraVectorStoreProps):
    def __init__(
        self,
        *,
        embeddings_model_vector_dimension: jsii.Number,
        metadata_field: typing.Optional[builtins.str] = None,
        primary_key_field: typing.Optional[builtins.str] = None,
        schema_name: typing.Optional[builtins.str] = None,
        table_name: typing.Optional[builtins.str] = None,
        text_field: typing.Optional[builtins.str] = None,
        vector_field: typing.Optional[builtins.str] = None,
        aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
        cluster_identifier: builtins.str,
        database_name: builtins.str,
        secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    ) -> None:
        '''(experimental) Properties for an existing Aurora Vector Store.

        You database must have TCP/IP port that the
        database will use for application connections
        set up for ``5432``.

        :param embeddings_model_vector_dimension: (experimental) The embeddings model dimension used for the Aurora Vector Store. The vector dimensions of the model must match the dimensions used in the KnowledgeBase construct.
        :param metadata_field: (experimental) The field name for the metadata column in the Aurora Vector Store.
        :param primary_key_field: (experimental) The primary key field for the Aurora Vector Store table.
        :param schema_name: (experimental) The schema name for the Aurora Vector Store.
        :param table_name: (experimental) The name of the table for the Aurora Vector Store.
        :param text_field: (experimental) The field name for the text column in the Aurora Vector Store.
        :param vector_field: (experimental) The field name for the vector column in the Aurora Vector Store.
        :param aurora_security_group: (experimental) The Security group associated with the RDS Aurora instance. This security group allows access to the Aurora Vector Store from Lambda's custom resource running pgVector SQL commands.
        :param cluster_identifier: (experimental) The unique cluster identifier of your Aurora RDS cluster.
        :param database_name: (experimental) The name of the database for the Aurora Vector Store.
        :param secret: (experimental) The secret containing the database credentials. The secret must contain ``host``, ``port``, ``username``, ``password`` and ``dbname`` values.
        :param vpc: (experimental) The VPC in which the existing Aurora Vector Store is located.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5e60fb0053aea54295685afce45c654cba8070098d25edcb4af68cfddea59c3c)
            check_type(argname="argument embeddings_model_vector_dimension", value=embeddings_model_vector_dimension, expected_type=type_hints["embeddings_model_vector_dimension"])
            check_type(argname="argument metadata_field", value=metadata_field, expected_type=type_hints["metadata_field"])
            check_type(argname="argument primary_key_field", value=primary_key_field, expected_type=type_hints["primary_key_field"])
            check_type(argname="argument schema_name", value=schema_name, expected_type=type_hints["schema_name"])
            check_type(argname="argument table_name", value=table_name, expected_type=type_hints["table_name"])
            check_type(argname="argument text_field", value=text_field, expected_type=type_hints["text_field"])
            check_type(argname="argument vector_field", value=vector_field, expected_type=type_hints["vector_field"])
            check_type(argname="argument aurora_security_group", value=aurora_security_group, expected_type=type_hints["aurora_security_group"])
            check_type(argname="argument cluster_identifier", value=cluster_identifier, expected_type=type_hints["cluster_identifier"])
            check_type(argname="argument database_name", value=database_name, expected_type=type_hints["database_name"])
            check_type(argname="argument secret", value=secret, expected_type=type_hints["secret"])
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "embeddings_model_vector_dimension": embeddings_model_vector_dimension,
            "aurora_security_group": aurora_security_group,
            "cluster_identifier": cluster_identifier,
            "database_name": database_name,
            "secret": secret,
            "vpc": vpc,
        }
        if metadata_field is not None:
            self._values["metadata_field"] = metadata_field
        if primary_key_field is not None:
            self._values["primary_key_field"] = primary_key_field
        if schema_name is not None:
            self._values["schema_name"] = schema_name
        if table_name is not None:
            self._values["table_name"] = table_name
        if text_field is not None:
            self._values["text_field"] = text_field
        if vector_field is not None:
            self._values["vector_field"] = vector_field

    @builtins.property
    def embeddings_model_vector_dimension(self) -> jsii.Number:
        '''(experimental) The embeddings model dimension used for the Aurora Vector Store.

        The vector dimensions of the model must match the dimensions
        used in the KnowledgeBase construct.

        :stability: experimental
        '''
        result = self._values.get("embeddings_model_vector_dimension")
        assert result is not None, "Required property 'embeddings_model_vector_dimension' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def metadata_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The field name for the metadata column in the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("metadata_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def primary_key_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The primary key field for the Aurora Vector Store table.

        :stability: experimental
        '''
        result = self._values.get("primary_key_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def schema_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The schema name for the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("schema_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def table_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the table for the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("table_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def text_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The field name for the text column in the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("text_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vector_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The field name for the vector column in the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("vector_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def aurora_security_group(self) -> _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup:
        '''(experimental) The Security group associated with the RDS Aurora instance.

        This security group allows access to the Aurora Vector Store from Lambda's
        custom resource running pgVector SQL commands.

        :stability: experimental
        '''
        result = self._values.get("aurora_security_group")
        assert result is not None, "Required property 'aurora_security_group' is missing"
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup, result)

    @builtins.property
    def cluster_identifier(self) -> builtins.str:
        '''(experimental) The unique cluster identifier of your Aurora RDS cluster.

        :stability: experimental
        '''
        result = self._values.get("cluster_identifier")
        assert result is not None, "Required property 'cluster_identifier' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def database_name(self) -> builtins.str:
        '''(experimental) The name of the database for the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("database_name")
        assert result is not None, "Required property 'database_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def secret(self) -> _aws_cdk_aws_secretsmanager_ceddda9d.ISecret:
        '''(experimental) The secret containing the database credentials.

        The secret must contain ``host``, ``port``, ``username``,
        ``password`` and ``dbname`` values.

        :stability: experimental
        '''
        result = self._values.get("secret")
        assert result is not None, "Required property 'secret' is missing"
        return typing.cast(_aws_cdk_aws_secretsmanager_ceddda9d.ISecret, result)

    @builtins.property
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC in which the existing Aurora Vector Store is located.

        :stability: experimental
        '''
        result = self._values.get("vpc")
        assert result is not None, "Required property 'vpc' is missing"
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ExistingAmazonAuroraVectorStoreProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdklabs/generative-ai-cdk-constructs.amazonaurora.AmazonAuroraVectorStoreProps",
    jsii_struct_bases=[BaseAuroraVectorStoreProps],
    name_mapping={
        "embeddings_model_vector_dimension": "embeddingsModelVectorDimension",
        "metadata_field": "metadataField",
        "primary_key_field": "primaryKeyField",
        "schema_name": "schemaName",
        "table_name": "tableName",
        "text_field": "textField",
        "vector_field": "vectorField",
        "cluster_id": "clusterId",
        "database_name": "databaseName",
        "postgre_sql_version": "postgreSQLVersion",
        "vpc": "vpc",
    },
)
class AmazonAuroraVectorStoreProps(BaseAuroraVectorStoreProps):
    def __init__(
        self,
        *,
        embeddings_model_vector_dimension: jsii.Number,
        metadata_field: typing.Optional[builtins.str] = None,
        primary_key_field: typing.Optional[builtins.str] = None,
        schema_name: typing.Optional[builtins.str] = None,
        table_name: typing.Optional[builtins.str] = None,
        text_field: typing.Optional[builtins.str] = None,
        vector_field: typing.Optional[builtins.str] = None,
        cluster_id: typing.Optional[builtins.str] = None,
        database_name: typing.Optional[builtins.str] = None,
        postgre_sql_version: typing.Optional[_aws_cdk_aws_rds_ceddda9d.AuroraPostgresEngineVersion] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    ) -> None:
        '''(experimental) Properties for configuring an Amazon Aurora Vector Store.

        :param embeddings_model_vector_dimension: (experimental) The embeddings model dimension used for the Aurora Vector Store. The vector dimensions of the model must match the dimensions used in the KnowledgeBase construct.
        :param metadata_field: (experimental) The field name for the metadata column in the Aurora Vector Store.
        :param primary_key_field: (experimental) The primary key field for the Aurora Vector Store table.
        :param schema_name: (experimental) The schema name for the Aurora Vector Store.
        :param table_name: (experimental) The name of the table for the Aurora Vector Store.
        :param text_field: (experimental) The field name for the text column in the Aurora Vector Store.
        :param vector_field: (experimental) The field name for the vector column in the Aurora Vector Store.
        :param cluster_id: (experimental) Cluster identifier.
        :param database_name: (experimental) The name of the database for the Aurora Vector Store.
        :param postgre_sql_version: (experimental) The version of PostgreSQL to use for the Aurora Vector Store. By default, the latest supported version will be used.
        :param vpc: (experimental) User's VPC in which they want to deploy Aurora Database.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__479db2f7e67505b8a3b5fb3b16af4aa17abcf77b50dc07738fe9abab2f5fc209)
            check_type(argname="argument embeddings_model_vector_dimension", value=embeddings_model_vector_dimension, expected_type=type_hints["embeddings_model_vector_dimension"])
            check_type(argname="argument metadata_field", value=metadata_field, expected_type=type_hints["metadata_field"])
            check_type(argname="argument primary_key_field", value=primary_key_field, expected_type=type_hints["primary_key_field"])
            check_type(argname="argument schema_name", value=schema_name, expected_type=type_hints["schema_name"])
            check_type(argname="argument table_name", value=table_name, expected_type=type_hints["table_name"])
            check_type(argname="argument text_field", value=text_field, expected_type=type_hints["text_field"])
            check_type(argname="argument vector_field", value=vector_field, expected_type=type_hints["vector_field"])
            check_type(argname="argument cluster_id", value=cluster_id, expected_type=type_hints["cluster_id"])
            check_type(argname="argument database_name", value=database_name, expected_type=type_hints["database_name"])
            check_type(argname="argument postgre_sql_version", value=postgre_sql_version, expected_type=type_hints["postgre_sql_version"])
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "embeddings_model_vector_dimension": embeddings_model_vector_dimension,
        }
        if metadata_field is not None:
            self._values["metadata_field"] = metadata_field
        if primary_key_field is not None:
            self._values["primary_key_field"] = primary_key_field
        if schema_name is not None:
            self._values["schema_name"] = schema_name
        if table_name is not None:
            self._values["table_name"] = table_name
        if text_field is not None:
            self._values["text_field"] = text_field
        if vector_field is not None:
            self._values["vector_field"] = vector_field
        if cluster_id is not None:
            self._values["cluster_id"] = cluster_id
        if database_name is not None:
            self._values["database_name"] = database_name
        if postgre_sql_version is not None:
            self._values["postgre_sql_version"] = postgre_sql_version
        if vpc is not None:
            self._values["vpc"] = vpc

    @builtins.property
    def embeddings_model_vector_dimension(self) -> jsii.Number:
        '''(experimental) The embeddings model dimension used for the Aurora Vector Store.

        The vector dimensions of the model must match the dimensions
        used in the KnowledgeBase construct.

        :stability: experimental
        '''
        result = self._values.get("embeddings_model_vector_dimension")
        assert result is not None, "Required property 'embeddings_model_vector_dimension' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def metadata_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The field name for the metadata column in the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("metadata_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def primary_key_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The primary key field for the Aurora Vector Store table.

        :stability: experimental
        '''
        result = self._values.get("primary_key_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def schema_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The schema name for the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("schema_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def table_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the table for the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("table_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def text_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The field name for the text column in the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("text_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vector_field(self) -> typing.Optional[builtins.str]:
        '''(experimental) The field name for the vector column in the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("vector_field")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def cluster_id(self) -> typing.Optional[builtins.str]:
        '''(experimental) Cluster identifier.

        :stability: experimental
        '''
        result = self._values.get("cluster_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def database_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the database for the Aurora Vector Store.

        :stability: experimental
        '''
        result = self._values.get("database_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def postgre_sql_version(
        self,
    ) -> typing.Optional[_aws_cdk_aws_rds_ceddda9d.AuroraPostgresEngineVersion]:
        '''(experimental) The version of PostgreSQL to use for the Aurora Vector Store.

        By default, the latest supported version will be used.

        :stability: experimental
        '''
        result = self._values.get("postgre_sql_version")
        return typing.cast(typing.Optional[_aws_cdk_aws_rds_ceddda9d.AuroraPostgresEngineVersion], result)

    @builtins.property
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''(experimental) User's VPC in which they want to deploy Aurora Database.

        :stability: experimental
        '''
        result = self._values.get("vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AmazonAuroraVectorStoreProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "AmazonAuroraVectorStore",
    "AmazonAuroraVectorStoreProps",
    "BaseAuroraVectorStoreProps",
    "DatabaseClusterResources",
    "ExistingAmazonAuroraVectorStore",
    "ExistingAmazonAuroraVectorStoreProps",
]

publication.publish()

def _typecheckingstub__742bfb7e146b244ee6d699c1caaf86c6f1822a15bdb42de183e3d4f29f4f8e24(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    cluster_id: typing.Optional[builtins.str] = None,
    database_name: typing.Optional[builtins.str] = None,
    postgre_sql_version: typing.Optional[_aws_cdk_aws_rds_ceddda9d.AuroraPostgresEngineVersion] = None,
    vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    embeddings_model_vector_dimension: jsii.Number,
    metadata_field: typing.Optional[builtins.str] = None,
    primary_key_field: typing.Optional[builtins.str] = None,
    schema_name: typing.Optional[builtins.str] = None,
    table_name: typing.Optional[builtins.str] = None,
    text_field: typing.Optional[builtins.str] = None,
    vector_field: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__684c8e9c9331fe4162c5fcb9208179405aa3a01d2039a3b9ed61ae8717229b1d(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    cluster_identifier: builtins.str,
    database_name: builtins.str,
    secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    embeddings_model_vector_dimension: jsii.Number,
    metadata_field: typing.Optional[builtins.str] = None,
    primary_key_field: typing.Optional[builtins.str] = None,
    schema_name: typing.Optional[builtins.str] = None,
    table_name: typing.Optional[builtins.str] = None,
    text_field: typing.Optional[builtins.str] = None,
    vector_field: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cc2cb74d2717f8a9267940982149b22a48909ab295eaee1cfbe006c645401b91(
    lambda_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__941b28cb1b2ce8505829999aa8c268507353ecfd5d99e81bf8de1c61e92f9abe(
    cluster_identifier: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__81514e055a1f329a7c85955ab93d851b60a0a191bf155d1c171dfb591cf735d5(
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f959b075d03b9890bed2500d557cb2023d94825521b2839de462db00e399df84(
    cluster_identifier: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6311e0a104e6f31ecd1afdb00615bfd69c7f7f6d7465d09ca0185b9e17fd3266(
    database_cluster_resources: typing.Union[DatabaseClusterResources, typing.Dict[builtins.str, typing.Any]],
    lambda_security_group: _aws_cdk_aws_ec2_ceddda9d.SecurityGroup,
    aurora_pg_cr_policy: _aws_cdk_aws_iam_ceddda9d.ManagedPolicy,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c97d3722603742a7d5d91d2da3e7a42783edca93c8a1f0c35bbc65730313f35b(
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
    cluster_identifier: builtins.str,
    aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8c590d53e38be1c52846d1063c597e22b13d544913eee79389f549dbb453f2bf(
    *,
    embeddings_model_vector_dimension: jsii.Number,
    metadata_field: typing.Optional[builtins.str] = None,
    primary_key_field: typing.Optional[builtins.str] = None,
    schema_name: typing.Optional[builtins.str] = None,
    table_name: typing.Optional[builtins.str] = None,
    text_field: typing.Optional[builtins.str] = None,
    vector_field: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__190d2665ff987b4762992f96a160574058e05079350349a93202fcb7ba8c960c(
    *,
    aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    cluster_identifier: builtins.str,
    resource_arn: builtins.str,
    secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    aurora_cluster: typing.Optional[_aws_cdk_aws_rds_ceddda9d.DatabaseCluster] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a6ad5fd56ef45d9d088efe46462a9e2c17eb77657b23d1eb5ca910b80f3e89d(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    cluster_identifier: builtins.str,
    database_name: builtins.str,
    secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    embeddings_model_vector_dimension: jsii.Number,
    metadata_field: typing.Optional[builtins.str] = None,
    primary_key_field: typing.Optional[builtins.str] = None,
    schema_name: typing.Optional[builtins.str] = None,
    table_name: typing.Optional[builtins.str] = None,
    text_field: typing.Optional[builtins.str] = None,
    vector_field: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9733000e2b4ac63c0d9de1a42f4bdb4f8293565c07ba3df614e4428d9de2c91f(
    lambda_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__22897b3199ef65f202d7ebae59e485787628c0fb79cf70fd00b438f70ca23577(
    cluster_identifier: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8a2e9f5492e0ce5c908783fc73180578f5115dcd57a19dafee6c721c9a043db9(
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f501fd1fe366e35135b325e46bc95a6d48ef5a708ef1465e43f8bf4186ad9a92(
    cluster_identifier: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__926fb08fb8538f889d4d7128a374b09f3bd2fd8d30a61b65ee5964e7250f97e6(
    database_cluster_resources: typing.Union[DatabaseClusterResources, typing.Dict[builtins.str, typing.Any]],
    lambda_security_group: _aws_cdk_aws_ec2_ceddda9d.SecurityGroup,
    aurora_pg_cr_policy: _aws_cdk_aws_iam_ceddda9d.ManagedPolicy,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b0c4703a70d70feef7e48462143c004e3446ea37ab923439b9f3028f0bf513de(
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
    cluster_identifier: builtins.str,
    aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5e60fb0053aea54295685afce45c654cba8070098d25edcb4af68cfddea59c3c(
    *,
    embeddings_model_vector_dimension: jsii.Number,
    metadata_field: typing.Optional[builtins.str] = None,
    primary_key_field: typing.Optional[builtins.str] = None,
    schema_name: typing.Optional[builtins.str] = None,
    table_name: typing.Optional[builtins.str] = None,
    text_field: typing.Optional[builtins.str] = None,
    vector_field: typing.Optional[builtins.str] = None,
    aurora_security_group: _aws_cdk_aws_ec2_ceddda9d.ISecurityGroup,
    cluster_identifier: builtins.str,
    database_name: builtins.str,
    secret: _aws_cdk_aws_secretsmanager_ceddda9d.ISecret,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__479db2f7e67505b8a3b5fb3b16af4aa17abcf77b50dc07738fe9abab2f5fc209(
    *,
    embeddings_model_vector_dimension: jsii.Number,
    metadata_field: typing.Optional[builtins.str] = None,
    primary_key_field: typing.Optional[builtins.str] = None,
    schema_name: typing.Optional[builtins.str] = None,
    table_name: typing.Optional[builtins.str] = None,
    text_field: typing.Optional[builtins.str] = None,
    vector_field: typing.Optional[builtins.str] = None,
    cluster_id: typing.Optional[builtins.str] = None,
    database_name: typing.Optional[builtins.str] = None,
    postgre_sql_version: typing.Optional[_aws_cdk_aws_rds_ceddda9d.AuroraPostgresEngineVersion] = None,
    vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
) -> None:
    """Type checking stubs"""
    pass
