r'''
# ElastiCache CDK Construct Library

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

This module has constructs for [Amazon ElastiCache](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.html).

* The `ServerlessCache` construct facilitates the creation and management of serverless cache.
* The `User` and `UserGroup` constructs facilitate the creation and management of users for the cache.

## Serverless Cache

Amazon ElastiCache Serverless is a serverless option that automatically scales cache capacity based on application traffic patterns. You can create a serverless cache using the `ServerlessCache` construct:

```python
vpc = ec2.Vpc(self, "VPC")

cache = elasticache.ServerlessCache(self, "ServerlessCache",
    vpc=vpc
)
```

### Connecting to serverless cache

To control who can access the serverless cache by the security groups, use the `.connections` attribute.

The serverless cache has a default port `6379`.

This example allows an EC2 instance to connect to the serverless cache:

```python
# serverless_cache: elasticache.ServerlessCache
# instance: ec2.Instance


# allow the EC2 instance to connect to serverless cache on default port 6379
serverless_cache.connections.allow_default_port_from(instance)
```

### Cache usage limits

You can configure usage limits on both cache data storage and ECPU/second for your cache to control costs and ensure predictable performance.

**Configuration options:**

* **Maximum limits**: Ensure your cache usage never exceeds the configured maximum
* **Minimum limits**: Reserve a baseline level of resources for consistent performance
* **Both**: Define a range where your cache usage will operate

For more infomation, see [Setting scaling limits to manage costs](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Scaling.html#Pre-Scaling).

```python
# vpc: ec2.Vpc


serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
    engine=elasticache.CacheEngine.VALKEY_LATEST,
    vpc=vpc,
    cache_usage_limits=elasticache.CacheUsageLimitsProperty(
        # cache data storage limits (GB)
        data_storage_minimum_size=Size.gibibytes(2),  # minimum: 1GB
        data_storage_maximum_size=Size.gibibytes(3),  # maximum: 5000GB
        # rate limits (ECPU/second)
        request_rate_limit_minimum=1000,  # minimum: 1000
        request_rate_limit_maximum=10000
    )
)
```

### Backups and restore

You can enable automatic backups for serverless cache.
When automatic backups are enabled, ElastiCache creates a backup of the cache on a daily basis.

Also you can set the backup window for any time when it's most convenient.
If you don't specify a backup window, ElastiCache assigns one automatically.

For more information, see [Scheduling automatic backups](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/backups-automatic.html).

To enable automatic backups, set the `backupRetentionLimit` property. You can also specify the snapshot creation time by setting `backupTime` property:

```python
# vpc: ec2.Vpc


serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
    backup=elasticache.BackupSettings(
        # enable automatic backups and set the retention period to 6 days
        backup_retention_limit=6,
        # set the backup window to 9:00 AM UTC
        backup_time=events.Schedule.cron(
            hour="9",
            minute="0"
        )
    ),
    vpc=vpc
)
```

You can create a final backup by setting `backupNameBeforeDeletion` property.

```python
# vpc: ec2.Vpc


serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
    engine=elasticache.CacheEngine.VALKEY_LATEST,
    backup=elasticache.BackupSettings(
        # set a backup name before deleting a cache
        backup_name_before_deletion="my-final-backup-name"
    ),
    vpc=vpc
)
```

You can restore from backups by setting snapshot ARNs to `backupArnsToRestore` property:

```python
# vpc: ec2.Vpc


serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
    engine=elasticache.CacheEngine.VALKEY_LATEST,
    backup=elasticache.BackupSettings(
        # set the backup(s) to restore
        backup_arns_to_restore=["arn:aws:elasticache:us-east-1:123456789012:serverlesscachesnapshot:my-final-backup-name"]
    ),
    vpc=vpc
)
```

### Encryption at rest

At-rest encryption is always enabled for Serverless Cache. There are two encryption options:

* **Default**: When no `kmsKey` is specified (left as `undefined`), AWS owned KMS keys are used automatically
* **Customer Managed Key**: Create a KMS key first, then pass it to the cache via the `kmsKey` property

### Customer Managed Key for encryption at rest

ElastiCache supports symmetric Customer Managed key (CMK) for encryption at rest.

For more information, see [Using customer managed keys from AWS KMS](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/at-rest-encryption.html#using-customer-managed-keys-for-elasticache-security).

To use CMK, set your CMK to the `kmsKey` property:

```python
from aws_cdk.aws_kms import Key

# kms_key: Key
# vpc: ec2.Vpc


serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
    engine=elasticache.CacheEngine.VALKEY_LATEST,
    serverless_cache_name="my-serverless-cache",
    vpc=vpc,
    # set Customer Managed Key
    kms_key=kms_key
)
```

### Metrics and monitoring

You can monitor your serverless cache using CloudWatch Metrics via the `metric` method.

For more information about serverless cache metrics, see [Serverless metrics and events for Valkey and Redis OSS](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/serverless-metrics-events-redis.html) and [Serverless metrics and events for Memcached](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/serverless-metrics-events.memcached.html).

```python
# serverless_cache: elasticache.ServerlessCache


# The 5 minutes average of the total number of successful read-only key lookups in the cache.
cache_hits = serverless_cache.metric_cache_hit_count()

# The 5 minutes average of the total number of bytes used by the data stored in the cache.
bytes_used_for_cache = serverless_cache.metric_data_stored()

# The 5 minutes average of the total number of ElastiCacheProcessingUnits (ECPUs) consumed by the requests executed on the cache.
elasti_cache_processing_units = serverless_cache.metric_processing_units_consumed()

# Create an alarm for ECPUs.
elasti_cache_processing_units.create_alarm(self, "ElastiCacheProcessingUnitsAlarm",
    threshold=50,
    evaluation_periods=1
)
```

### Import an existing serverless cache

To import an existing ServerlessCache, use the `ServerlessCache.fromServerlessCacheAttributes` method:

```python
# security_group: ec2.SecurityGroup


imported_serverless_cache = elasticache.ServerlessCache.from_serverless_cache_attributes(self, "ImportedServerlessCache",
    serverless_cache_name="my-serverless-cache",
    security_groups=[security_group]
)
```

## User and User Group

Setup required properties and create:

```python
new_default_user = elasticache.NoPasswordUser(self, "NoPasswordUser",
    user_id="default",
    access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
)

user_group = elasticache.UserGroup(self, "UserGroup",
    users=[new_default_user]
)
```

### RBAC

In Valkey 7.2 and onward and Redis OSS 6.0 onward you can use a feature called Role-Based Access Control (RBAC). RBAC is also the only way to control access to serverless caches.

RBAC enables you to control cache access through user groups. These user groups are designed as a way to organize access to caches.

For more information, see [Role-Based Access Control (RBAC)](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Clusters.RBAC.html).

To enable RBAC for ElastiCache with Valkey or Redis OSS, you take the following steps:

* Create users.
* Create a user group and add users to the user group.
* Assign the user group to a cache.

### Create users

First, you need to create users by using `IamUser`, `PasswordUser` or `NoPasswordUser` construct.

With RBAC, you create users and assign them specific permissions by using `accessString` property.

For more information, see [Specifying Permissions Using an Access String](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Clusters.RBAC.html#Access-string).

You can create an IAM-enabled user by using `IamUser` construct:

```python
user = elasticache.IamUser(self, "User",
    # set user engine
    engine=elasticache.UserEngine.REDIS,

    # set user id
    user_id="my-user",

    # set username
    user_name="my-user",

    # set access string
    access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
)
```

> NOTE: IAM-enabled users must have matching user id and username. For more information, see [Limitations](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/auth-iam.html). The construct can set automatically the username to be the same as the user id.

If you want to create a password authenticated user, use `PasswordUser` construct:

```python
user = elasticache.PasswordUser(self, "User",
    # set user engine
    engine=elasticache.UserEngine.VALKEY,

    # set user id
    user_id="my-user-id",

    # set access string
    access_control=elasticache.AccessControl.from_access_string("on ~* +@all"),

    # set username
    user_name="my-user-name",

    # set up to two passwords
    passwords=[
        # "SecretIdForPassword" is the secret id for the password
        SecretValue.secrets_manager("SecretIdForPassword"),
        # "AnotherSecretIdForPassword" is the secret id for the password
        SecretValue.secrets_manager("AnotherSecretIdForPassword")
    ]
)
```

You can also create a no password required user by using `NoPasswordUser` construct:

```python
user = elasticache.NoPasswordUser(self, "User",
    # set user engine
    engine=elasticache.UserEngine.REDIS,

    # set user id
    user_id="my-user-id",

    # set access string
    access_control=elasticache.AccessControl.from_access_string("on ~* +@all"),

    # set username
    user_name="my-user-name"
)
```

### Default user

ElastiCache automatically creates a default user with both a user ID and username set to `default`. This default user cannot be modified or deleted. The user is created as a no password authentication user.

This user is intended for compatibility with the default behavior of previous Redis OSS versions and has an access string that permits it to call all commands and access all keys.

To use this automatically created default user in CDK, you can import it using `NoPasswordUser.fromUserAttributes` method. For more information on import methods, see the [Import an existing user and user group](#import-an-existing-user-and-user-group) section.

To add proper access control to a cache, replace the default user with a new one that is either disabled by setting the `accessString` to `off -@all` or secured with a strong password.

To change the default user, create a new default user with the username set to `default`. You can then swap it with the original default user.

For more information, see [Applying RBAC to a Cache for ElastiCache with Valkey or Redis OSS](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Clusters.RBAC.html#rbac-using).

If you want to create a new default user, `userName` must be `default` and `userId` must not be `default` by using `NoPasswordUser` or `PasswordUser`:

```python
# use the original `default` user by using import method
default_user = elasticache.NoPasswordUser.from_user_attributes(self, "DefaultUser",
    # userId and userName must be 'default'
    user_id="default"
)

# create a new default user
new_default_user = elasticache.NoPasswordUser(self, "NewDefaultUser",
    # new default user id must not be 'default'
    user_id="new-default",
    # new default username must be 'default'
    user_name="default",
    # set access string
    access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
)
```

> NOTE: You can't create a new default user using `IamUser` because an IAM-enabled user's username and user ID cannot be different.

### Add users to the user group

Next, use the `UserGroup` construct to create a user group and add users to it.
Ensure that you include either the original default user or a new default user:

```python
# new_default_user: elasticache.IUser
# user: elasticache.IUser
# another_user: elasticache.IUser


user_group = elasticache.UserGroup(self, "UserGroup",
    # add users including default user
    users=[new_default_user, user]
)

# you can also add a user by using addUser method
user_group.add_user(another_user)
```

### Assign user group

Finally, assign a user group to cache:

```python
# vpc: ec2.Vpc
# user_group: elasticache.UserGroup


serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
    engine=elasticache.CacheEngine.VALKEY_LATEST,
    serverless_cache_name="my-serverless-cache",
    vpc=vpc,
    # assign User Group
    user_group=user_group
)
```

### Grant permissions to IAM-enabled users

If you create IAM-enabled users, `"elasticache:Connect"` action must be allowed for the users and cache.

> NOTE: You don't need grant permissions to no password required users or password authentication users.

For more information, see [Authenticating with IAM](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/auth-iam.html).

To grant permissions, you can use the `grantConnect` method in `IamUser` and `ServerlessCache` constructs:

```python
# user: elasticache.IamUser
# serverless_cache: elasticache.ServerlessCache
# role: iam.Role


# grant "elasticache:Connect" action permissions to role
user.grant_connect(role)
serverless_cache.grant_connect(role)
```

### Import an existing user and user group

You can import an existing user and user group by using import methods:

```python
stack = Stack()

imported_iam_user = elasticache.IamUser.from_user_id(self, "ImportedIamUser", "my-iam-user-id")

imported_password_user = elasticache.PasswordUser.from_user_attributes(stack, "ImportedPasswordUser",
    user_id="my-password-user-id"
)

imported_no_password_user = elasticache.NoPasswordUser.from_user_attributes(stack, "ImportedNoPasswordUser",
    user_id="my-no-password-user-id"
)

imported_user_group = elasticache.UserGroup.from_user_group_attributes(self, "ImportedUserGroup",
    user_group_name="my-user-group-name"
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

from ._jsii import *

import aws_cdk as _aws_cdk_ceddda9d
import aws_cdk.aws_cloudwatch as _aws_cdk_aws_cloudwatch_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_events as _aws_cdk_aws_events_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import constructs as _constructs_77d1e7e8


class AccessControl(
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-elasticache-alpha.AccessControl",
):
    '''(experimental) Access control configuration for ElastiCache users.

    :stability: experimental
    :exampleMetadata: infused

    Example::

        user = elasticache.IamUser(self, "User",
            # set user engine
            engine=elasticache.UserEngine.REDIS,
        
            # set user id
            user_id="my-user",
        
            # set username
            user_name="my-user",
        
            # set access string
            access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
        )
    '''

    def __init__(self) -> None:
        '''
        :stability: experimental
        '''
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="fromAccessString")
    @builtins.classmethod
    def from_access_string(cls, access_string: builtins.str) -> "AccessControl":
        '''(experimental) Create access control from an access string.

        :param access_string: The access string defining user permissions.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e620f1697be9aecd3a467c280159a620b782aa506dafa85fd157be6ea7fe422e)
            check_type(argname="argument access_string", value=access_string, expected_type=type_hints["access_string"])
        return typing.cast("AccessControl", jsii.sinvoke(cls, "fromAccessString", [access_string]))

    @builtins.property
    @jsii.member(jsii_name="accessString")
    @abc.abstractmethod
    def access_string(self) -> builtins.str:
        '''(experimental) The access string that defines user's permissions.

        :stability: experimental
        '''
        ...


class _AccessControlProxy(AccessControl):
    @builtins.property
    @jsii.member(jsii_name="accessString")
    def access_string(self) -> builtins.str:
        '''(experimental) The access string that defines user's permissions.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "accessString"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, AccessControl).__jsii_proxy_class__ = lambda : _AccessControlProxy


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.BackupSettings",
    jsii_struct_bases=[],
    name_mapping={
        "backup_arns_to_restore": "backupArnsToRestore",
        "backup_name_before_deletion": "backupNameBeforeDeletion",
        "backup_retention_limit": "backupRetentionLimit",
        "backup_time": "backupTime",
    },
)
class BackupSettings:
    def __init__(
        self,
        *,
        backup_arns_to_restore: typing.Optional[typing.Sequence[builtins.str]] = None,
        backup_name_before_deletion: typing.Optional[builtins.str] = None,
        backup_retention_limit: typing.Optional[jsii.Number] = None,
        backup_time: typing.Optional[_aws_cdk_aws_events_ceddda9d.Schedule] = None,
    ) -> None:
        '''(experimental) Backup configuration for ServerlessCache.

        :param backup_arns_to_restore: (experimental) ARNs of backups from which to restore data into the new cache. Default: - Create a new cache with no existing data
        :param backup_name_before_deletion: (experimental) Name for the final backup taken before deletion. Default: - No final backup
        :param backup_retention_limit: (experimental) Number of days to retain backups (1-35). Default: - Backups are not retained
        :param backup_time: (experimental) Automated daily backup UTC time. Default: - No automated backups

        :stability: experimental
        :exampleMetadata: infused

        Example::

            # vpc: ec2.Vpc
            
            
            serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
                engine=elasticache.CacheEngine.VALKEY_LATEST,
                backup=elasticache.BackupSettings(
                    # set a backup name before deleting a cache
                    backup_name_before_deletion="my-final-backup-name"
                ),
                vpc=vpc
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ea85e979f440b15805c41c71f6c52d492e8ed626b8475463ad82343ef2dd8229)
            check_type(argname="argument backup_arns_to_restore", value=backup_arns_to_restore, expected_type=type_hints["backup_arns_to_restore"])
            check_type(argname="argument backup_name_before_deletion", value=backup_name_before_deletion, expected_type=type_hints["backup_name_before_deletion"])
            check_type(argname="argument backup_retention_limit", value=backup_retention_limit, expected_type=type_hints["backup_retention_limit"])
            check_type(argname="argument backup_time", value=backup_time, expected_type=type_hints["backup_time"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if backup_arns_to_restore is not None:
            self._values["backup_arns_to_restore"] = backup_arns_to_restore
        if backup_name_before_deletion is not None:
            self._values["backup_name_before_deletion"] = backup_name_before_deletion
        if backup_retention_limit is not None:
            self._values["backup_retention_limit"] = backup_retention_limit
        if backup_time is not None:
            self._values["backup_time"] = backup_time

    @builtins.property
    def backup_arns_to_restore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) ARNs of backups from which to restore data into the new cache.

        :default: - Create a new cache with no existing data

        :stability: experimental
        '''
        result = self._values.get("backup_arns_to_restore")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def backup_name_before_deletion(self) -> typing.Optional[builtins.str]:
        '''(experimental) Name for the final backup taken before deletion.

        :default: - No final backup

        :stability: experimental
        '''
        result = self._values.get("backup_name_before_deletion")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def backup_retention_limit(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Number of days to retain backups (1-35).

        :default: - Backups are not retained

        :stability: experimental
        '''
        result = self._values.get("backup_retention_limit")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def backup_time(self) -> typing.Optional[_aws_cdk_aws_events_ceddda9d.Schedule]:
        '''(experimental) Automated daily backup UTC time.

        :default: - No automated backups

        :stability: experimental
        '''
        result = self._values.get("backup_time")
        return typing.cast(typing.Optional[_aws_cdk_aws_events_ceddda9d.Schedule], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BackupSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="@aws-cdk/aws-elasticache-alpha.CacheEngine")
class CacheEngine(enum.Enum):
    '''(experimental) Supported cache engines together with available versions.

    :stability: experimental
    :exampleMetadata: infused

    Example::

        # vpc: ec2.Vpc
        
        
        serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
            engine=elasticache.CacheEngine.VALKEY_LATEST,
            backup=elasticache.BackupSettings(
                # set a backup name before deleting a cache
                backup_name_before_deletion="my-final-backup-name"
            ),
            vpc=vpc
        )
    '''

    VALKEY_LATEST = "VALKEY_LATEST"
    '''(experimental) Valkey engine, latest major version available, minor version is selected automatically For more information about the features related to this version check: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html.

    :stability: experimental
    '''
    VALKEY_7 = "VALKEY_7"
    '''(experimental) Valkey engine, major version 7, minor version is selected automatically For more information about the features related to this version check: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html.

    :stability: experimental
    '''
    VALKEY_8 = "VALKEY_8"
    '''(experimental) Valkey engine, major version 8, minor version is selected automatically For more information about the features related to this version check: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html.

    :stability: experimental
    '''
    REDIS_LATEST = "REDIS_LATEST"
    '''(experimental) Redis engine, latest major version available, minor version is selected automatically For more information about the features related to this version check: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html.

    :stability: experimental
    '''
    REDIS_7 = "REDIS_7"
    '''(experimental) Redis engine, major version 7, minor version is selected automatically For more information about the features related to this version check: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html.

    :stability: experimental
    '''
    MEMCACHED_LATEST = "MEMCACHED_LATEST"
    '''(experimental) Memcached engine, latest major version available, minor version is selected automatically For more information about the features related to this version check: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html.

    :stability: experimental
    '''


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.CacheUsageLimitsProperty",
    jsii_struct_bases=[],
    name_mapping={
        "data_storage_maximum_size": "dataStorageMaximumSize",
        "data_storage_minimum_size": "dataStorageMinimumSize",
        "request_rate_limit_maximum": "requestRateLimitMaximum",
        "request_rate_limit_minimum": "requestRateLimitMinimum",
    },
)
class CacheUsageLimitsProperty:
    def __init__(
        self,
        *,
        data_storage_maximum_size: typing.Optional[_aws_cdk_ceddda9d.Size] = None,
        data_storage_minimum_size: typing.Optional[_aws_cdk_ceddda9d.Size] = None,
        request_rate_limit_maximum: typing.Optional[jsii.Number] = None,
        request_rate_limit_minimum: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''(experimental) Usage limits configuration for ServerlessCache.

        :param data_storage_maximum_size: (experimental) Maximum data storage size (5000 GB). Default: - No maximum limit
        :param data_storage_minimum_size: (experimental) Minimum data storage size (1 GB). Default: - No minimum limit
        :param request_rate_limit_maximum: (experimental) Maximum request rate limit (15000000 ECPUs per second). Default: - No maximum limit
        :param request_rate_limit_minimum: (experimental) Minimum request rate limit (1000 ECPUs per second). Default: - No minimum limit

        :stability: experimental
        :exampleMetadata: infused

        Example::

            # vpc: ec2.Vpc
            
            
            serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
                engine=elasticache.CacheEngine.VALKEY_LATEST,
                vpc=vpc,
                cache_usage_limits=elasticache.CacheUsageLimitsProperty(
                    # cache data storage limits (GB)
                    data_storage_minimum_size=Size.gibibytes(2),  # minimum: 1GB
                    data_storage_maximum_size=Size.gibibytes(3),  # maximum: 5000GB
                    # rate limits (ECPU/second)
                    request_rate_limit_minimum=1000,  # minimum: 1000
                    request_rate_limit_maximum=10000
                )
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__efe6f2d96cd5b2f6811c325e3e6f8c033a8e1e3bad115c7ec1b3a89402890381)
            check_type(argname="argument data_storage_maximum_size", value=data_storage_maximum_size, expected_type=type_hints["data_storage_maximum_size"])
            check_type(argname="argument data_storage_minimum_size", value=data_storage_minimum_size, expected_type=type_hints["data_storage_minimum_size"])
            check_type(argname="argument request_rate_limit_maximum", value=request_rate_limit_maximum, expected_type=type_hints["request_rate_limit_maximum"])
            check_type(argname="argument request_rate_limit_minimum", value=request_rate_limit_minimum, expected_type=type_hints["request_rate_limit_minimum"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if data_storage_maximum_size is not None:
            self._values["data_storage_maximum_size"] = data_storage_maximum_size
        if data_storage_minimum_size is not None:
            self._values["data_storage_minimum_size"] = data_storage_minimum_size
        if request_rate_limit_maximum is not None:
            self._values["request_rate_limit_maximum"] = request_rate_limit_maximum
        if request_rate_limit_minimum is not None:
            self._values["request_rate_limit_minimum"] = request_rate_limit_minimum

    @builtins.property
    def data_storage_maximum_size(self) -> typing.Optional[_aws_cdk_ceddda9d.Size]:
        '''(experimental) Maximum data storage size (5000 GB).

        :default: - No maximum limit

        :stability: experimental
        '''
        result = self._values.get("data_storage_maximum_size")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.Size], result)

    @builtins.property
    def data_storage_minimum_size(self) -> typing.Optional[_aws_cdk_ceddda9d.Size]:
        '''(experimental) Minimum data storage size (1 GB).

        :default: - No minimum limit

        :stability: experimental
        '''
        result = self._values.get("data_storage_minimum_size")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.Size], result)

    @builtins.property
    def request_rate_limit_maximum(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Maximum request rate limit (15000000 ECPUs per second).

        :default: - No maximum limit

        :stability: experimental
        '''
        result = self._values.get("request_rate_limit_maximum")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def request_rate_limit_minimum(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Minimum request rate limit (1000 ECPUs per second).

        :default: - No minimum limit

        :stability: experimental
        '''
        result = self._values.get("request_rate_limit_minimum")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CacheUsageLimitsProperty(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.interface(jsii_type="@aws-cdk/aws-elasticache-alpha.IServerlessCache")
class IServerlessCache(
    _aws_cdk_ceddda9d.IResource,
    _aws_cdk_aws_ec2_ceddda9d.IConnectable,
    typing_extensions.Protocol,
):
    '''(experimental) Represents a Serverless ElastiCache cache.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheArn")
    def serverless_cache_arn(self) -> builtins.str:
        '''(experimental) The ARN of the serverless cache.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheName")
    def serverless_cache_name(self) -> builtins.str:
        '''(experimental) The name of the serverless cache.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="backupArnsToRestore")
    def backup_arns_to_restore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) The ARNs of backups restored in the cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional[CacheEngine]:
        '''(experimental) The cache engine used by this cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) The KMS key used for encryption.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="securityGroups")
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The security groups associated with this cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="subnets")
    def subnets(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]]:
        '''(experimental) The subnets this cache is deployed in.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="userGroup")
    def user_group(self) -> typing.Optional["IUserGroup"]:
        '''(experimental) The user group associated with this cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''(experimental) The VPC this cache is deployed in.

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant the given identity custom permissions.

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
        '''(experimental) Grant connect permissions to the cache.

        :param grantee: -

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this cache.

        :param metric_name: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricActiveConnections")
    def metric_active_connections(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for active connections.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricCacheHitCount")
    def metric_cache_hit_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for cache hit count.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricCacheHitRate")
    def metric_cache_hit_rate(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for cache hit rate.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricCacheMissCount")
    def metric_cache_miss_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for cache miss count.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricDataStored")
    def metric_data_stored(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for data stored in the cache.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricNetworkBytesIn")
    def metric_network_bytes_in(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for network bytes in.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricNetworkBytesOut")
    def metric_network_bytes_out(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for network bytes out.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricProcessingUnitsConsumed")
    def metric_processing_units_consumed(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for ECPUs consumed.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricReadRequestLatency")
    def metric_read_request_latency(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for read request latency.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="metricWriteRequestLatency")
    def metric_write_request_latency(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for write request latency.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        ...


class _IServerlessCacheProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
    jsii.proxy_for(_aws_cdk_aws_ec2_ceddda9d.IConnectable), # type: ignore[misc]
):
    '''(experimental) Represents a Serverless ElastiCache cache.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk/aws-elasticache-alpha.IServerlessCache"

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheArn")
    def serverless_cache_arn(self) -> builtins.str:
        '''(experimental) The ARN of the serverless cache.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheArn"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheName")
    def serverless_cache_name(self) -> builtins.str:
        '''(experimental) The name of the serverless cache.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheName"))

    @builtins.property
    @jsii.member(jsii_name="backupArnsToRestore")
    def backup_arns_to_restore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) The ARNs of backups restored in the cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "backupArnsToRestore"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional[CacheEngine]:
        '''(experimental) The cache engine used by this cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[CacheEngine], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) The KMS key used for encryption.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="securityGroups")
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The security groups associated with this cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]], jsii.get(self, "securityGroups"))

    @builtins.property
    @jsii.member(jsii_name="subnets")
    def subnets(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]]:
        '''(experimental) The subnets this cache is deployed in.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]], jsii.get(self, "subnets"))

    @builtins.property
    @jsii.member(jsii_name="userGroup")
    def user_group(self) -> typing.Optional["IUserGroup"]:
        '''(experimental) The user group associated with this cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional["IUserGroup"], jsii.get(self, "userGroup"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''(experimental) The VPC this cache is deployed in.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant the given identity custom permissions.

        :param grantee: -
        :param actions: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e10493c9f2558a6df1557a2b42846be6f6e2459b12e951d570214118623bf343)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
            check_type(argname="argument actions", value=actions, expected_type=typing.Tuple[type_hints["actions"], ...]) # pyright: ignore [reportGeneralTypeIssues]
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [grantee, *actions]))

    @jsii.member(jsii_name="grantConnect")
    def grant_connect(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant connect permissions to the cache.

        :param grantee: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b0289ab310f989d11350e0d7b6b9832083c842adcca6cee9b2aa5152d38320e9)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantConnect", [grantee]))

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this cache.

        :param metric_name: -
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9a792c0c5412a4811be430d976e81b32b6eadc23f7744b57dbd29f21e9457854)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metric", [metric_name, props]))

    @jsii.member(jsii_name="metricActiveConnections")
    def metric_active_connections(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for active connections.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricActiveConnections", [props]))

    @jsii.member(jsii_name="metricCacheHitCount")
    def metric_cache_hit_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for cache hit count.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricCacheHitCount", [props]))

    @jsii.member(jsii_name="metricCacheHitRate")
    def metric_cache_hit_rate(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for cache hit rate.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricCacheHitRate", [props]))

    @jsii.member(jsii_name="metricCacheMissCount")
    def metric_cache_miss_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for cache miss count.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricCacheMissCount", [props]))

    @jsii.member(jsii_name="metricDataStored")
    def metric_data_stored(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for data stored in the cache.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricDataStored", [props]))

    @jsii.member(jsii_name="metricNetworkBytesIn")
    def metric_network_bytes_in(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for network bytes in.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricNetworkBytesIn", [props]))

    @jsii.member(jsii_name="metricNetworkBytesOut")
    def metric_network_bytes_out(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for network bytes out.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricNetworkBytesOut", [props]))

    @jsii.member(jsii_name="metricProcessingUnitsConsumed")
    def metric_processing_units_consumed(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for ECPUs consumed.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricProcessingUnitsConsumed", [props]))

    @jsii.member(jsii_name="metricReadRequestLatency")
    def metric_read_request_latency(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for read request latency.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricReadRequestLatency", [props]))

    @jsii.member(jsii_name="metricWriteRequestLatency")
    def metric_write_request_latency(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for write request latency.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricWriteRequestLatency", [props]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IServerlessCache).__jsii_proxy_class__ = lambda : _IServerlessCacheProxy


@jsii.interface(jsii_type="@aws-cdk/aws-elasticache-alpha.IUser")
class IUser(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    '''(experimental) Represents an ElastiCache base user.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="userArn")
    def user_arn(self) -> builtins.str:
        '''(experimental) The user's ARN.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="userId")
    def user_id(self) -> builtins.str:
        '''(experimental) The user's ID.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional["UserEngine"]:
        '''(experimental) The engine for the user.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="userName")
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The user's name.

        :stability: experimental
        :attribute: true
        '''
        ...


class _IUserProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    '''(experimental) Represents an ElastiCache base user.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk/aws-elasticache-alpha.IUser"

    @builtins.property
    @jsii.member(jsii_name="userArn")
    def user_arn(self) -> builtins.str:
        '''(experimental) The user's ARN.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userArn"))

    @builtins.property
    @jsii.member(jsii_name="userId")
    def user_id(self) -> builtins.str:
        '''(experimental) The user's ID.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userId"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional["UserEngine"]:
        '''(experimental) The engine for the user.

        :stability: experimental
        '''
        return typing.cast(typing.Optional["UserEngine"], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="userName")
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The user's name.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userName"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IUser).__jsii_proxy_class__ = lambda : _IUserProxy


@jsii.interface(jsii_type="@aws-cdk/aws-elasticache-alpha.IUserGroup")
class IUserGroup(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    '''(experimental) Represents an ElastiCache UserGroup.

    :stability: experimental
    '''

    @builtins.property
    @jsii.member(jsii_name="userGroupArn")
    def user_group_arn(self) -> builtins.str:
        '''(experimental) The ARN of the user group.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="userGroupName")
    def user_group_name(self) -> builtins.str:
        '''(experimental) The name of the user group.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional["UserEngine"]:
        '''(experimental) The engine type for the user group.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="users")
    def users(self) -> typing.Optional[typing.List[IUser]]:
        '''(experimental) List of users in the user group.

        :stability: experimental
        '''
        ...

    @jsii.member(jsii_name="addUser")
    def add_user(self, user: IUser) -> None:
        '''(experimental) Add a user to this user group.

        :param user: The user to add.

        :stability: experimental
        '''
        ...


class _IUserGroupProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    '''(experimental) Represents an ElastiCache UserGroup.

    :stability: experimental
    '''

    __jsii_type__: typing.ClassVar[str] = "@aws-cdk/aws-elasticache-alpha.IUserGroup"

    @builtins.property
    @jsii.member(jsii_name="userGroupArn")
    def user_group_arn(self) -> builtins.str:
        '''(experimental) The ARN of the user group.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="userGroupName")
    def user_group_name(self) -> builtins.str:
        '''(experimental) The name of the user group.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userGroupName"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional["UserEngine"]:
        '''(experimental) The engine type for the user group.

        :stability: experimental
        '''
        return typing.cast(typing.Optional["UserEngine"], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="users")
    def users(self) -> typing.Optional[typing.List[IUser]]:
        '''(experimental) List of users in the user group.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[IUser]], jsii.get(self, "users"))

    @jsii.member(jsii_name="addUser")
    def add_user(self, user: IUser) -> None:
        '''(experimental) Add a user to this user group.

        :param user: The user to add.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9c80e32dcca4a85ef240faeaa9e93aa354e2eb9f07e6bfa3013f64da8314e02e)
            check_type(argname="argument user", value=user, expected_type=type_hints["user"])
        return typing.cast(None, jsii.invoke(self, "addUser", [user]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IUserGroup).__jsii_proxy_class__ = lambda : _IUserGroupProxy


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.ServerlessCacheAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "backup_arns_to_restore": "backupArnsToRestore",
        "engine": "engine",
        "kms_key": "kmsKey",
        "security_groups": "securityGroups",
        "serverless_cache_arn": "serverlessCacheArn",
        "serverless_cache_name": "serverlessCacheName",
        "subnets": "subnets",
        "user_group": "userGroup",
        "vpc": "vpc",
    },
)
class ServerlessCacheAttributes:
    def __init__(
        self,
        *,
        backup_arns_to_restore: typing.Optional[typing.Sequence[builtins.str]] = None,
        engine: typing.Optional[CacheEngine] = None,
        kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        serverless_cache_arn: typing.Optional[builtins.str] = None,
        serverless_cache_name: typing.Optional[builtins.str] = None,
        subnets: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISubnet]] = None,
        user_group: typing.Optional[IUserGroup] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    ) -> None:
        '''(experimental) Attributes that can be specified when importing a ServerlessCache.

        :param backup_arns_to_restore: (experimental) The ARNs of backups restored in the cache. Default: - backups are unknown
        :param engine: (experimental) The cache engine used by this cache. Default: - engine type is unknown
        :param kms_key: (experimental) The KMS key used for encryption. Default: - encryption key is unknown
        :param security_groups: (experimental) The security groups associated with this cache. Default: - security groups are unknown
        :param serverless_cache_arn: (experimental) The ARN of the serverless cache. One of ``serverlessCacheName`` or ``serverlessCacheArn`` is required. Default: - derived from serverlessCacheName
        :param serverless_cache_name: (experimental) The name of the serverless cache. One of ``serverlessCacheName`` or ``serverlessCacheArn`` is required. Default: - derived from serverlessCacheArn
        :param subnets: (experimental) The subnets this cache is deployed in. Default: - subnets are unknown
        :param user_group: (experimental) The user group associated with this cache. Default: - user group is unknown
        :param vpc: (experimental) The VPC this cache is deployed in. Default: - VPC is unknown

        :stability: experimental
        :exampleMetadata: infused

        Example::

            # security_group: ec2.SecurityGroup
            
            
            imported_serverless_cache = elasticache.ServerlessCache.from_serverless_cache_attributes(self, "ImportedServerlessCache",
                serverless_cache_name="my-serverless-cache",
                security_groups=[security_group]
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__525223783a3311afa0f7f71caa1719da598d452009b52b3759771297039ab46d)
            check_type(argname="argument backup_arns_to_restore", value=backup_arns_to_restore, expected_type=type_hints["backup_arns_to_restore"])
            check_type(argname="argument engine", value=engine, expected_type=type_hints["engine"])
            check_type(argname="argument kms_key", value=kms_key, expected_type=type_hints["kms_key"])
            check_type(argname="argument security_groups", value=security_groups, expected_type=type_hints["security_groups"])
            check_type(argname="argument serverless_cache_arn", value=serverless_cache_arn, expected_type=type_hints["serverless_cache_arn"])
            check_type(argname="argument serverless_cache_name", value=serverless_cache_name, expected_type=type_hints["serverless_cache_name"])
            check_type(argname="argument subnets", value=subnets, expected_type=type_hints["subnets"])
            check_type(argname="argument user_group", value=user_group, expected_type=type_hints["user_group"])
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if backup_arns_to_restore is not None:
            self._values["backup_arns_to_restore"] = backup_arns_to_restore
        if engine is not None:
            self._values["engine"] = engine
        if kms_key is not None:
            self._values["kms_key"] = kms_key
        if security_groups is not None:
            self._values["security_groups"] = security_groups
        if serverless_cache_arn is not None:
            self._values["serverless_cache_arn"] = serverless_cache_arn
        if serverless_cache_name is not None:
            self._values["serverless_cache_name"] = serverless_cache_name
        if subnets is not None:
            self._values["subnets"] = subnets
        if user_group is not None:
            self._values["user_group"] = user_group
        if vpc is not None:
            self._values["vpc"] = vpc

    @builtins.property
    def backup_arns_to_restore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) The ARNs of backups restored in the cache.

        :default: - backups are unknown

        :stability: experimental
        '''
        result = self._values.get("backup_arns_to_restore")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def engine(self) -> typing.Optional[CacheEngine]:
        '''(experimental) The cache engine used by this cache.

        :default: - engine type is unknown

        :stability: experimental
        '''
        result = self._values.get("engine")
        return typing.cast(typing.Optional[CacheEngine], result)

    @builtins.property
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) The KMS key used for encryption.

        :default: - encryption key is unknown

        :stability: experimental
        '''
        result = self._values.get("kms_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], result)

    @builtins.property
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The security groups associated with this cache.

        :default: - security groups are unknown

        :stability: experimental
        '''
        result = self._values.get("security_groups")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]], result)

    @builtins.property
    def serverless_cache_arn(self) -> typing.Optional[builtins.str]:
        '''(experimental) The ARN of the serverless cache.

        One of ``serverlessCacheName`` or ``serverlessCacheArn`` is required.

        :default: - derived from serverlessCacheName

        :stability: experimental
        '''
        result = self._values.get("serverless_cache_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def serverless_cache_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the serverless cache.

        One of ``serverlessCacheName`` or ``serverlessCacheArn`` is required.

        :default: - derived from serverlessCacheArn

        :stability: experimental
        '''
        result = self._values.get("serverless_cache_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def subnets(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]]:
        '''(experimental) The subnets this cache is deployed in.

        :default: - subnets are unknown

        :stability: experimental
        '''
        result = self._values.get("subnets")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]], result)

    @builtins.property
    def user_group(self) -> typing.Optional[IUserGroup]:
        '''(experimental) The user group associated with this cache.

        :default: - user group is unknown

        :stability: experimental
        '''
        result = self._values.get("user_group")
        return typing.cast(typing.Optional[IUserGroup], result)

    @builtins.property
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''(experimental) The VPC this cache is deployed in.

        :default: - VPC is unknown

        :stability: experimental
        '''
        result = self._values.get("vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ServerlessCacheAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IServerlessCache)
class ServerlessCacheBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-elasticache-alpha.ServerlessCacheBase",
):
    '''(experimental) Base class for ServerlessCache constructs.

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
            type_hints = typing.get_type_hints(_typecheckingstub__c7b51bf67205b95d0da44cd223fb2f868c44df176787b447d7896e1afb3dd6a6)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant the given identity custom permissions.

        :param grantee: The principal to grant permissions to.
        :param actions: The actions to grant.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad40da7b17882582727a25c5cae611995a4dc950a61c614016318b5b7ccb6033)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
            check_type(argname="argument actions", value=actions, expected_type=typing.Tuple[type_hints["actions"], ...]) # pyright: ignore [reportGeneralTypeIssues]
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [grantee, *actions]))

    @jsii.member(jsii_name="grantConnect")
    def grant_connect(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant connect permissions to the cache.

        :param grantee: The principal to grant permissions to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2ff19421655c341c2dcba401161d317db3e9c72bf8eb0e48622ad8857a4940bf)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantConnect", [grantee]))

    @jsii.member(jsii_name="metric")
    def metric(
        self,
        metric_name: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Return the given named metric for this cache.

        :param metric_name: The name of the metric.
        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Average over 5 minutes

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c20ab5bdc4ec344507965f099a001907bcde7ed53841efac3f9c652f4b6bfa9c)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metric", [metric_name, props]))

    @jsii.member(jsii_name="metricActiveConnections")
    def metric_active_connections(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for active connections.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Maximum over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricActiveConnections", [props]))

    @jsii.member(jsii_name="metricCacheHitCount")
    def metric_cache_hit_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for cache hit count.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Sum over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricCacheHitCount", [props]))

    @jsii.member(jsii_name="metricCacheHitRate")
    def metric_cache_hit_rate(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for cache hit rate.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Average over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricCacheHitRate", [props]))

    @jsii.member(jsii_name="metricCacheMissCount")
    def metric_cache_miss_count(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for cache miss count.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Sum over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricCacheMissCount", [props]))

    @jsii.member(jsii_name="metricDataStored")
    def metric_data_stored(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for data stored in the cache.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Maximum over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricDataStored", [props]))

    @jsii.member(jsii_name="metricNetworkBytesIn")
    def metric_network_bytes_in(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for network bytes in.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Sum over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricNetworkBytesIn", [props]))

    @jsii.member(jsii_name="metricNetworkBytesOut")
    def metric_network_bytes_out(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for network bytes out.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Sum over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricNetworkBytesOut", [props]))

    @jsii.member(jsii_name="metricProcessingUnitsConsumed")
    def metric_processing_units_consumed(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for ECPUs consumed.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Average over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricProcessingUnitsConsumed", [props]))

    @jsii.member(jsii_name="metricReadRequestLatency")
    def metric_read_request_latency(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for read request latency.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Average over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricReadRequestLatency", [props]))

    @jsii.member(jsii_name="metricWriteRequestLatency")
    def metric_write_request_latency(
        self,
        *,
        account: typing.Optional[builtins.str] = None,
        color: typing.Optional[builtins.str] = None,
        dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        id: typing.Optional[builtins.str] = None,
        label: typing.Optional[builtins.str] = None,
        period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
        region: typing.Optional[builtins.str] = None,
        stack_account: typing.Optional[builtins.str] = None,
        stack_region: typing.Optional[builtins.str] = None,
        statistic: typing.Optional[builtins.str] = None,
        unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
        visible: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_cloudwatch_ceddda9d.Metric:
        '''(experimental) Metric for write request latency.

        :param account: Account which this metric comes from. Default: - Deployment account.
        :param color: The hex color code, prefixed with '#' (e.g. '#00ff00'), to use when this metric is rendered on a graph. The ``Color`` class has a set of standard colors that can be used here. Default: - Automatic color
        :param dimensions_map: Dimensions of the metric. Default: - No dimensions.
        :param id: Unique identifier for this metric when used in dashboard widgets. The id can be used as a variable to represent this metric in math expressions. Valid characters are letters, numbers, and underscore. The first character must be a lowercase letter. Default: - No ID
        :param label: Label for this metric when added to a Graph in a Dashboard. You can use `dynamic labels <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/graph-dynamic-labels.html>`_ to show summary information about the entire displayed time series in the legend. For example, if you use:: [max: ${MAX}] MyMetric As the metric label, the maximum value in the visible range will be shown next to the time series name in the graph's legend. Default: - No label
        :param period: The period over which the specified statistic is applied. Default: Duration.minutes(5)
        :param region: Region which this metric comes from. Default: - Deployment region.
        :param stack_account: Account of the stack this metric is attached to. Default: - Deployment account.
        :param stack_region: Region of the stack this metric is attached to. Default: - Deployment region.
        :param statistic: What function to use for aggregating. Use the ``aws_cloudwatch.Stats`` helper class to construct valid input strings. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" - "tmNN.NN" | "tm(NN.NN%:NN.NN%)" - "iqm" - "wmNN.NN" | "wm(NN.NN%:NN.NN%)" - "tcNN.NN" | "tc(NN.NN%:NN.NN%)" - "tsNN.NN" | "ts(NN.NN%:NN.NN%)" Default: Average
        :param unit: Unit used to filter the metric stream. Only refer to datums emitted to the metric stream with the given unit and ignore all others. Only useful when datums are being emitted to the same metric stream under different units. The default is to use all matric datums in the stream, regardless of unit, which is recommended in nearly all cases. CloudWatch does not honor this property for graphs. Default: - All metric datums in the given metric stream
        :param visible: Whether this metric should be visible in dashboard graphs. Setting this to false is useful when you want to hide raw metrics that are used in math expressions, and show only the expression results. Default: true

        :default: Average over 5 minutes

        :stability: experimental
        '''
        props = _aws_cdk_aws_cloudwatch_ceddda9d.MetricOptions(
            account=account,
            color=color,
            dimensions_map=dimensions_map,
            id=id,
            label=label,
            period=period,
            region=region,
            stack_account=stack_account,
            stack_region=stack_region,
            statistic=statistic,
            unit=unit,
            visible=visible,
        )

        return typing.cast(_aws_cdk_aws_cloudwatch_ceddda9d.Metric, jsii.invoke(self, "metricWriteRequestLatency", [props]))

    @builtins.property
    @jsii.member(jsii_name="connections")
    @abc.abstractmethod
    def connections(self) -> _aws_cdk_aws_ec2_ceddda9d.Connections:
        '''(experimental) Access to network connections.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheArn")
    @abc.abstractmethod
    def serverless_cache_arn(self) -> builtins.str:
        '''(experimental) The ARN of the serverless cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheName")
    @abc.abstractmethod
    def serverless_cache_name(self) -> builtins.str:
        '''(experimental) The name of the serverless cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="backupArnsToRestore")
    @abc.abstractmethod
    def backup_arns_to_restore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) The ARNs of backups restored in the cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="engine")
    @abc.abstractmethod
    def engine(self) -> typing.Optional[CacheEngine]:
        '''(experimental) The cache engine used by this cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    @abc.abstractmethod
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) The KMS key used for encryption.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="securityGroups")
    @abc.abstractmethod
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The security groups associated with this cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="subnets")
    @abc.abstractmethod
    def subnets(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]]:
        '''(experimental) The subnets this cache is deployed in.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="userGroup")
    @abc.abstractmethod
    def user_group(self) -> typing.Optional[IUserGroup]:
        '''(experimental) The user group associated with this cache.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="vpc")
    @abc.abstractmethod
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''(experimental) The VPC this cache is deployed in.

        :stability: experimental
        '''
        ...


class _ServerlessCacheBaseProxy(
    ServerlessCacheBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="connections")
    def connections(self) -> _aws_cdk_aws_ec2_ceddda9d.Connections:
        '''(experimental) Access to network connections.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.Connections, jsii.get(self, "connections"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheArn")
    def serverless_cache_arn(self) -> builtins.str:
        '''(experimental) The ARN of the serverless cache.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheArn"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheName")
    def serverless_cache_name(self) -> builtins.str:
        '''(experimental) The name of the serverless cache.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheName"))

    @builtins.property
    @jsii.member(jsii_name="backupArnsToRestore")
    def backup_arns_to_restore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) The ARNs of backups restored in the cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "backupArnsToRestore"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional[CacheEngine]:
        '''(experimental) The cache engine used by this cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[CacheEngine], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) The KMS key used for encryption.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="securityGroups")
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The security groups associated with this cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]], jsii.get(self, "securityGroups"))

    @builtins.property
    @jsii.member(jsii_name="subnets")
    def subnets(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]]:
        '''(experimental) The subnets this cache is deployed in.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]], jsii.get(self, "subnets"))

    @builtins.property
    @jsii.member(jsii_name="userGroup")
    def user_group(self) -> typing.Optional[IUserGroup]:
        '''(experimental) The user group associated with this cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[IUserGroup], jsii.get(self, "userGroup"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''(experimental) The VPC this cache is deployed in.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, ServerlessCacheBase).__jsii_proxy_class__ = lambda : _ServerlessCacheBaseProxy


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.ServerlessCacheProps",
    jsii_struct_bases=[],
    name_mapping={
        "vpc": "vpc",
        "backup": "backup",
        "cache_usage_limits": "cacheUsageLimits",
        "description": "description",
        "engine": "engine",
        "kms_key": "kmsKey",
        "security_groups": "securityGroups",
        "serverless_cache_name": "serverlessCacheName",
        "user_group": "userGroup",
        "vpc_subnets": "vpcSubnets",
    },
)
class ServerlessCacheProps:
    def __init__(
        self,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        backup: typing.Optional[typing.Union[BackupSettings, typing.Dict[builtins.str, typing.Any]]] = None,
        cache_usage_limits: typing.Optional[typing.Union[CacheUsageLimitsProperty, typing.Dict[builtins.str, typing.Any]]] = None,
        description: typing.Optional[builtins.str] = None,
        engine: typing.Optional[CacheEngine] = None,
        kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        serverless_cache_name: typing.Optional[builtins.str] = None,
        user_group: typing.Optional[IUserGroup] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''(experimental) Properties for defining a ServerlessCache.

        :param vpc: (experimental) The VPC to place the cache in.
        :param backup: (experimental) Backup configuration. Default: - No backups configured
        :param cache_usage_limits: (experimental) Usage limits for the cache. Default: - No usage limits
        :param description: (experimental) A description for the cache. Default: - No description
        :param engine: (experimental) The cache engine combined with the version Enum options: VALKEY_DEFAULT, VALKEY_7, VALKEY_8, REDIS_DEFAULT, MEMCACHED_DEFAULT The default options bring the latest versions available. Default: when not provided, the default engine would be Valkey, latest version available (VALKEY_DEFAULT)
        :param kms_key: (experimental) KMS key for encryption. Default: - Service managed encryption (AWS owned KMS key)
        :param security_groups: (experimental) Security groups for the cache. Default: - A new security group is created
        :param serverless_cache_name: (experimental) Name for the serverless cache. Default: automatically generated name by Resource
        :param user_group: (experimental) User group for access control. Default: - No user group
        :param vpc_subnets: (experimental) Which subnets to place the cache in. Default: - Private subnets with egress

        :stability: experimental
        :exampleMetadata: infused

        Example::

            # vpc: ec2.Vpc
            
            
            serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
                engine=elasticache.CacheEngine.VALKEY_LATEST,
                backup=elasticache.BackupSettings(
                    # set a backup name before deleting a cache
                    backup_name_before_deletion="my-final-backup-name"
                ),
                vpc=vpc
            )
        '''
        if isinstance(backup, dict):
            backup = BackupSettings(**backup)
        if isinstance(cache_usage_limits, dict):
            cache_usage_limits = CacheUsageLimitsProperty(**cache_usage_limits)
        if isinstance(vpc_subnets, dict):
            vpc_subnets = _aws_cdk_aws_ec2_ceddda9d.SubnetSelection(**vpc_subnets)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f75886d0cff4f1478f060fc3093d5e18de249f98bfdb7f2e6af73b6053f6836)
            check_type(argname="argument vpc", value=vpc, expected_type=type_hints["vpc"])
            check_type(argname="argument backup", value=backup, expected_type=type_hints["backup"])
            check_type(argname="argument cache_usage_limits", value=cache_usage_limits, expected_type=type_hints["cache_usage_limits"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument engine", value=engine, expected_type=type_hints["engine"])
            check_type(argname="argument kms_key", value=kms_key, expected_type=type_hints["kms_key"])
            check_type(argname="argument security_groups", value=security_groups, expected_type=type_hints["security_groups"])
            check_type(argname="argument serverless_cache_name", value=serverless_cache_name, expected_type=type_hints["serverless_cache_name"])
            check_type(argname="argument user_group", value=user_group, expected_type=type_hints["user_group"])
            check_type(argname="argument vpc_subnets", value=vpc_subnets, expected_type=type_hints["vpc_subnets"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "vpc": vpc,
        }
        if backup is not None:
            self._values["backup"] = backup
        if cache_usage_limits is not None:
            self._values["cache_usage_limits"] = cache_usage_limits
        if description is not None:
            self._values["description"] = description
        if engine is not None:
            self._values["engine"] = engine
        if kms_key is not None:
            self._values["kms_key"] = kms_key
        if security_groups is not None:
            self._values["security_groups"] = security_groups
        if serverless_cache_name is not None:
            self._values["serverless_cache_name"] = serverless_cache_name
        if user_group is not None:
            self._values["user_group"] = user_group
        if vpc_subnets is not None:
            self._values["vpc_subnets"] = vpc_subnets

    @builtins.property
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        '''(experimental) The VPC to place the cache in.

        :stability: experimental
        '''
        result = self._values.get("vpc")
        assert result is not None, "Required property 'vpc' is missing"
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, result)

    @builtins.property
    def backup(self) -> typing.Optional[BackupSettings]:
        '''(experimental) Backup configuration.

        :default: - No backups configured

        :stability: experimental
        '''
        result = self._values.get("backup")
        return typing.cast(typing.Optional[BackupSettings], result)

    @builtins.property
    def cache_usage_limits(self) -> typing.Optional[CacheUsageLimitsProperty]:
        '''(experimental) Usage limits for the cache.

        :default: - No usage limits

        :stability: experimental
        '''
        result = self._values.get("cache_usage_limits")
        return typing.cast(typing.Optional[CacheUsageLimitsProperty], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) A description for the cache.

        :default: - No description

        :stability: experimental
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def engine(self) -> typing.Optional[CacheEngine]:
        '''(experimental) The cache engine combined with the version Enum options: VALKEY_DEFAULT, VALKEY_7, VALKEY_8, REDIS_DEFAULT, MEMCACHED_DEFAULT The default options bring the latest versions available.

        :default: when not provided, the default engine would be Valkey, latest version available (VALKEY_DEFAULT)

        :stability: experimental
        '''
        result = self._values.get("engine")
        return typing.cast(typing.Optional[CacheEngine], result)

    @builtins.property
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) KMS key for encryption.

        :default: - Service managed encryption (AWS owned KMS key)

        :stability: experimental
        '''
        result = self._values.get("kms_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], result)

    @builtins.property
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) Security groups for the cache.

        :default: - A new security group is created

        :stability: experimental
        '''
        result = self._values.get("security_groups")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]], result)

    @builtins.property
    def serverless_cache_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) Name for the serverless cache.

        :default: automatically generated name by Resource

        :stability: experimental
        '''
        result = self._values.get("serverless_cache_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def user_group(self) -> typing.Optional[IUserGroup]:
        '''(experimental) User group for access control.

        :default: - No user group

        :stability: experimental
        '''
        result = self._values.get("user_group")
        return typing.cast(typing.Optional[IUserGroup], result)

    @builtins.property
    def vpc_subnets(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection]:
        '''(experimental) Which subnets to place the cache in.

        :default: - Private subnets with egress

        :stability: experimental
        '''
        result = self._values.get("vpc_subnets")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ServerlessCacheProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IUser)
class UserBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-elasticache-alpha.UserBase",
):
    '''(experimental) Base class for ElastiCache users.

    :stability: experimental
    :exampleMetadata: fixture=_generated

    Example::

        # The code below shows an example of how to instantiate this type.
        # The values are placeholders you should change.
        import aws_cdk.aws_elasticache_alpha as elasticache_alpha
        
        user_base = elasticache_alpha.UserBase.from_user_arn(self, "MyUserBase", "userArn")
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
            type_hints = typing.get_type_hints(_typecheckingstub__cd7b81bd91d16843f9e064a01afad15ad4ffd483149ced547a3469334cd684ea)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromUserArn")
    @builtins.classmethod
    def from_user_arn(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        user_arn: builtins.str,
    ) -> IUser:
        '''(experimental) Import an existing user by ARN.

        :param scope: The parent creating construct (usually ``this``).
        :param id: The construct's name.
        :param user_arn: The ARN of the existing user.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e761480c0ebfd294ebdec1335b328648571dec1230977aa4799c2820f7759c20)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument user_arn", value=user_arn, expected_type=type_hints["user_arn"])
        return typing.cast(IUser, jsii.sinvoke(cls, "fromUserArn", [scope, id, user_arn]))

    @jsii.member(jsii_name="fromUserAttributes")
    @builtins.classmethod
    def from_user_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        engine: typing.Optional["UserEngine"] = None,
        user_arn: typing.Optional[builtins.str] = None,
        user_id: typing.Optional[builtins.str] = None,
        user_name: typing.Optional[builtins.str] = None,
    ) -> IUser:
        '''(experimental) Import an existing user using attributes.

        :param scope: The parent creating construct (usually ``this``).
        :param id: The construct's name.
        :param engine: (experimental) The engine type for the user. Default: - engine type is unknown.
        :param user_arn: (experimental) The ARN of the user. One of ``userId`` or ``userArn`` is required. Default: - derived from userId.
        :param user_id: (experimental) The ID of the user. One of ``userId`` or ``userArn`` is required. Default: - derived from userArn.
        :param user_name: (experimental) The user's name. Default: - name is unknown.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b1c7010a5023bb28d22488eefa8ca48e861974805fa4eae4c35433dd9893f3b5)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = UserBaseAttributes(
            engine=engine, user_arn=user_arn, user_id=user_id, user_name=user_name
        )

        return typing.cast(IUser, jsii.sinvoke(cls, "fromUserAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="fromUserId")
    @builtins.classmethod
    def from_user_id(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        user_id: builtins.str,
    ) -> IUser:
        '''(experimental) Import an existing user by ID.

        :param scope: The parent creating construct (usually ``this``).
        :param id: The construct's name.
        :param user_id: The ID of the existing user.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__704a3972bb194bf809ebf7e171d84072283c6436009df971b1302f13e7e3506b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument user_id", value=user_id, expected_type=type_hints["user_id"])
        return typing.cast(IUser, jsii.sinvoke(cls, "fromUserId", [scope, id, user_id]))

    @builtins.property
    @jsii.member(jsii_name="userArn")
    @abc.abstractmethod
    def user_arn(self) -> builtins.str:
        '''(experimental) The user's ARN.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="userId")
    @abc.abstractmethod
    def user_id(self) -> builtins.str:
        '''(experimental) The user's ID.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="engine")
    @abc.abstractmethod
    def engine(self) -> typing.Optional["UserEngine"]:
        '''(experimental) The engine for the user.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="userName")
    @abc.abstractmethod
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The user's name.

        :stability: experimental
        :attribute: true
        '''
        ...


class _UserBaseProxy(
    UserBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="userArn")
    def user_arn(self) -> builtins.str:
        '''(experimental) The user's ARN.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userArn"))

    @builtins.property
    @jsii.member(jsii_name="userId")
    def user_id(self) -> builtins.str:
        '''(experimental) The user's ID.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userId"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional["UserEngine"]:
        '''(experimental) The engine for the user.

        :stability: experimental
        '''
        return typing.cast(typing.Optional["UserEngine"], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="userName")
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The user's name.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userName"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, UserBase).__jsii_proxy_class__ = lambda : _UserBaseProxy


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.UserBaseAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "engine": "engine",
        "user_arn": "userArn",
        "user_id": "userId",
        "user_name": "userName",
    },
)
class UserBaseAttributes:
    def __init__(
        self,
        *,
        engine: typing.Optional["UserEngine"] = None,
        user_arn: typing.Optional[builtins.str] = None,
        user_id: typing.Optional[builtins.str] = None,
        user_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Attributes for importing an existing ElastiCache user.

        :param engine: (experimental) The engine type for the user. Default: - engine type is unknown.
        :param user_arn: (experimental) The ARN of the user. One of ``userId`` or ``userArn`` is required. Default: - derived from userId.
        :param user_id: (experimental) The ID of the user. One of ``userId`` or ``userArn`` is required. Default: - derived from userArn.
        :param user_name: (experimental) The user's name. Default: - name is unknown.

        :stability: experimental
        :exampleMetadata: infused

        Example::

            # use the original `default` user by using import method
            default_user = elasticache.NoPasswordUser.from_user_attributes(self, "DefaultUser",
                # userId and userName must be 'default'
                user_id="default"
            )
            
            # create a new default user
            new_default_user = elasticache.NoPasswordUser(self, "NewDefaultUser",
                # new default user id must not be 'default'
                user_id="new-default",
                # new default username must be 'default'
                user_name="default",
                # set access string
                access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cdf1d20dc614181bdd9ec4f71003b1c6acdd827489b62d62be7fa2a11c2c8131)
            check_type(argname="argument engine", value=engine, expected_type=type_hints["engine"])
            check_type(argname="argument user_arn", value=user_arn, expected_type=type_hints["user_arn"])
            check_type(argname="argument user_id", value=user_id, expected_type=type_hints["user_id"])
            check_type(argname="argument user_name", value=user_name, expected_type=type_hints["user_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if engine is not None:
            self._values["engine"] = engine
        if user_arn is not None:
            self._values["user_arn"] = user_arn
        if user_id is not None:
            self._values["user_id"] = user_id
        if user_name is not None:
            self._values["user_name"] = user_name

    @builtins.property
    def engine(self) -> typing.Optional["UserEngine"]:
        '''(experimental) The engine type for the user.

        :default: - engine type is unknown.

        :stability: experimental
        '''
        result = self._values.get("engine")
        return typing.cast(typing.Optional["UserEngine"], result)

    @builtins.property
    def user_arn(self) -> typing.Optional[builtins.str]:
        '''(experimental) The ARN of the user.

        One of ``userId`` or ``userArn`` is required.

        :default: - derived from userId.

        :stability: experimental
        '''
        result = self._values.get("user_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def user_id(self) -> typing.Optional[builtins.str]:
        '''(experimental) The ID of the user.

        One of ``userId`` or ``userArn`` is required.

        :default: - derived from userArn.

        :stability: experimental
        '''
        result = self._values.get("user_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The user's name.

        :default: - name is unknown.

        :stability: experimental
        '''
        result = self._values.get("user_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "UserBaseAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.UserBaseProps",
    jsii_struct_bases=[],
    name_mapping={
        "access_control": "accessControl",
        "user_id": "userId",
        "engine": "engine",
    },
)
class UserBaseProps:
    def __init__(
        self,
        *,
        access_control: AccessControl,
        user_id: builtins.str,
        engine: typing.Optional["UserEngine"] = None,
    ) -> None:
        '''(experimental) Properties for defining an ElastiCache base user.

        :param access_control: (experimental) Access control configuration for the user.
        :param user_id: (experimental) The ID of the user.
        :param engine: (experimental) The engine type for the user. Enum options: UserEngine.VALKEY, UserEngine.REDIS. Default: UserEngine.VALKEY.

        :stability: experimental
        :exampleMetadata: fixture=_generated

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_elasticache_alpha as elasticache_alpha
            
            # access_control: elasticache_alpha.AccessControl
            
            user_base_props = elasticache_alpha.UserBaseProps(
                access_control=access_control,
                user_id="userId",
            
                # the properties below are optional
                engine=elasticache_alpha.UserEngine.VALKEY
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f02aff3e7c2886ad06074fe94984dabf4561cfd6ed96513f581a7a9744e69253)
            check_type(argname="argument access_control", value=access_control, expected_type=type_hints["access_control"])
            check_type(argname="argument user_id", value=user_id, expected_type=type_hints["user_id"])
            check_type(argname="argument engine", value=engine, expected_type=type_hints["engine"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "access_control": access_control,
            "user_id": user_id,
        }
        if engine is not None:
            self._values["engine"] = engine

    @builtins.property
    def access_control(self) -> AccessControl:
        '''(experimental) Access control configuration for the user.

        :stability: experimental
        '''
        result = self._values.get("access_control")
        assert result is not None, "Required property 'access_control' is missing"
        return typing.cast(AccessControl, result)

    @builtins.property
    def user_id(self) -> builtins.str:
        '''(experimental) The ID of the user.

        :stability: experimental
        '''
        result = self._values.get("user_id")
        assert result is not None, "Required property 'user_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def engine(self) -> typing.Optional["UserEngine"]:
        '''(experimental) The engine type for the user.

        Enum options: UserEngine.VALKEY, UserEngine.REDIS.

        :default: UserEngine.VALKEY.

        :stability: experimental
        '''
        result = self._values.get("engine")
        return typing.cast(typing.Optional["UserEngine"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "UserBaseProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="@aws-cdk/aws-elasticache-alpha.UserEngine")
class UserEngine(enum.Enum):
    '''(experimental) Engine type for ElastiCache users and user groups.

    :stability: experimental
    :exampleMetadata: infused

    Example::

        user = elasticache.IamUser(self, "User",
            # set user engine
            engine=elasticache.UserEngine.REDIS,
        
            # set user id
            user_id="my-user",
        
            # set username
            user_name="my-user",
        
            # set access string
            access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
        )
    '''

    VALKEY = "VALKEY"
    '''(experimental) Valkey engine.

    :stability: experimental
    '''
    REDIS = "REDIS"
    '''(experimental) Redis engine.

    :stability: experimental
    '''


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.UserGroupAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "engine": "engine",
        "user_group_arn": "userGroupArn",
        "user_group_name": "userGroupName",
        "users": "users",
    },
)
class UserGroupAttributes:
    def __init__(
        self,
        *,
        engine: typing.Optional[UserEngine] = None,
        user_group_arn: typing.Optional[builtins.str] = None,
        user_group_name: typing.Optional[builtins.str] = None,
        users: typing.Optional[typing.Sequence[IUser]] = None,
    ) -> None:
        '''(experimental) Attributes that can be specified when importing a UserGroup.

        :param engine: (experimental) The engine type for the user group. Default: - engine type is unknown
        :param user_group_arn: (experimental) The ARN of the user group. One of ``userGroupName`` or ``userGroupArn`` is required. Default: - derived from userGroupName
        :param user_group_name: (experimental) The name of the user group. One of ``userGroupName`` or ``userGroupArn`` is required. Default: - derived from userGroupArn
        :param users: (experimental) List of users in the user group. Default: - users are unknown

        :stability: experimental
        :exampleMetadata: infused

        Example::

            stack = Stack()
            
            imported_iam_user = elasticache.IamUser.from_user_id(self, "ImportedIamUser", "my-iam-user-id")
            
            imported_password_user = elasticache.PasswordUser.from_user_attributes(stack, "ImportedPasswordUser",
                user_id="my-password-user-id"
            )
            
            imported_no_password_user = elasticache.NoPasswordUser.from_user_attributes(stack, "ImportedNoPasswordUser",
                user_id="my-no-password-user-id"
            )
            
            imported_user_group = elasticache.UserGroup.from_user_group_attributes(self, "ImportedUserGroup",
                user_group_name="my-user-group-name"
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__db74853827d2f9386370091f5ca49d6c2aed58fa0432e0620e2035a7533112c1)
            check_type(argname="argument engine", value=engine, expected_type=type_hints["engine"])
            check_type(argname="argument user_group_arn", value=user_group_arn, expected_type=type_hints["user_group_arn"])
            check_type(argname="argument user_group_name", value=user_group_name, expected_type=type_hints["user_group_name"])
            check_type(argname="argument users", value=users, expected_type=type_hints["users"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if engine is not None:
            self._values["engine"] = engine
        if user_group_arn is not None:
            self._values["user_group_arn"] = user_group_arn
        if user_group_name is not None:
            self._values["user_group_name"] = user_group_name
        if users is not None:
            self._values["users"] = users

    @builtins.property
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine type for the user group.

        :default: - engine type is unknown

        :stability: experimental
        '''
        result = self._values.get("engine")
        return typing.cast(typing.Optional[UserEngine], result)

    @builtins.property
    def user_group_arn(self) -> typing.Optional[builtins.str]:
        '''(experimental) The ARN of the user group.

        One of ``userGroupName`` or ``userGroupArn`` is required.

        :default: - derived from userGroupName

        :stability: experimental
        '''
        result = self._values.get("user_group_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def user_group_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the user group.

        One of ``userGroupName`` or ``userGroupArn`` is required.

        :default: - derived from userGroupArn

        :stability: experimental
        '''
        result = self._values.get("user_group_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def users(self) -> typing.Optional[typing.List[IUser]]:
        '''(experimental) List of users in the user group.

        :default: - users are unknown

        :stability: experimental
        '''
        result = self._values.get("users")
        return typing.cast(typing.Optional[typing.List[IUser]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "UserGroupAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(IUserGroup)
class UserGroupBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-elasticache-alpha.UserGroupBase",
):
    '''(experimental) Base class for UserGroup constructs.

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
            type_hints = typing.get_type_hints(_typecheckingstub__129a538a4481ec262096321ff41577cd9504c059761c56ebf0d64ab1d4e8bea9)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="addUser")
    def add_user(self, _user: IUser) -> None:
        '''(experimental) Add a user to this user group.

        :param _user: The user to add.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__589f4a71a023f13cb4428634c1d5766cf35a5fe45f9a39d37a95d648e1b9230a)
            check_type(argname="argument _user", value=_user, expected_type=type_hints["_user"])
        return typing.cast(None, jsii.invoke(self, "addUser", [_user]))

    @builtins.property
    @jsii.member(jsii_name="userGroupArn")
    @abc.abstractmethod
    def user_group_arn(self) -> builtins.str:
        '''(experimental) The ARN of the user group.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="userGroupName")
    @abc.abstractmethod
    def user_group_name(self) -> builtins.str:
        '''(experimental) The name of the user group.

        :stability: experimental
        :attribute: true
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="engine")
    @abc.abstractmethod
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine type for the user group.

        :stability: experimental
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="users")
    @abc.abstractmethod
    def users(self) -> typing.Optional[typing.List[IUser]]:
        '''(experimental) List of users in the user group.

        :stability: experimental
        '''
        ...


class _UserGroupBaseProxy(
    UserGroupBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="userGroupArn")
    def user_group_arn(self) -> builtins.str:
        '''(experimental) The ARN of the user group.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="userGroupName")
    def user_group_name(self) -> builtins.str:
        '''(experimental) The name of the user group.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userGroupName"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine type for the user group.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[UserEngine], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="users")
    def users(self) -> typing.Optional[typing.List[IUser]]:
        '''(experimental) List of users in the user group.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[IUser]], jsii.get(self, "users"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, UserGroupBase).__jsii_proxy_class__ = lambda : _UserGroupBaseProxy


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.UserGroupProps",
    jsii_struct_bases=[],
    name_mapping={
        "engine": "engine",
        "user_group_name": "userGroupName",
        "users": "users",
    },
)
class UserGroupProps:
    def __init__(
        self,
        *,
        engine: typing.Optional[UserEngine] = None,
        user_group_name: typing.Optional[builtins.str] = None,
        users: typing.Optional[typing.Sequence[IUser]] = None,
    ) -> None:
        '''(experimental) Properties for defining an ElastiCache UserGroup.

        :param engine: (experimental) The engine type for the user group Enum options: UserEngine.VALKEY, UserEngine.REDIS. Default: UserEngine.VALKEY
        :param user_group_name: (experimental) Enforces a particular physical user group name. Default: 
        :param users: (experimental) List of users inside the user group. Default: - no users

        :stability: experimental
        :exampleMetadata: infused

        Example::

            new_default_user = elasticache.NoPasswordUser(self, "NoPasswordUser",
                user_id="default",
                access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
            )
            
            user_group = elasticache.UserGroup(self, "UserGroup",
                users=[new_default_user]
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__47db8eef599a3412e1208c1788f490f7eef502c1862c5a129999646ffa5df171)
            check_type(argname="argument engine", value=engine, expected_type=type_hints["engine"])
            check_type(argname="argument user_group_name", value=user_group_name, expected_type=type_hints["user_group_name"])
            check_type(argname="argument users", value=users, expected_type=type_hints["users"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if engine is not None:
            self._values["engine"] = engine
        if user_group_name is not None:
            self._values["user_group_name"] = user_group_name
        if users is not None:
            self._values["users"] = users

    @builtins.property
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine type for the user group Enum options: UserEngine.VALKEY, UserEngine.REDIS.

        :default: UserEngine.VALKEY

        :stability: experimental
        '''
        result = self._values.get("engine")
        return typing.cast(typing.Optional[UserEngine], result)

    @builtins.property
    def user_group_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) Enforces a particular physical user group name.

        :default:

        :stability: experimental
        '''
        result = self._values.get("user_group_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def users(self) -> typing.Optional[typing.List[IUser]]:
        '''(experimental) List of users inside the user group.

        :default: - no users

        :stability: experimental
        '''
        result = self._values.get("users")
        return typing.cast(typing.Optional[typing.List[IUser]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "UserGroupProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class IamUser(
    UserBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-elasticache-alpha.IamUser",
):
    '''(experimental) Define an ElastiCache user with IAM authentication.

    :stability: experimental
    :resource: AWS::ElastiCache::User
    :exampleMetadata: infused

    Example::

        user = elasticache.IamUser(self, "User",
            # set user engine
            engine=elasticache.UserEngine.REDIS,
        
            # set user id
            user_id="my-user",
        
            # set username
            user_name="my-user",
        
            # set access string
            access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
        )
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        user_name: typing.Optional[builtins.str] = None,
        access_control: AccessControl,
        user_id: builtins.str,
        engine: typing.Optional[UserEngine] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param user_name: (experimental) The name of the user. Default: - Same as userId.
        :param access_control: (experimental) Access control configuration for the user.
        :param user_id: (experimental) The ID of the user.
        :param engine: (experimental) The engine type for the user. Enum options: UserEngine.VALKEY, UserEngine.REDIS. Default: UserEngine.VALKEY.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__009b9161fccb666529247da64089de9839548b5c2a964eb4e8043df674d87095)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = IamUserProps(
            user_name=user_name,
            access_control=access_control,
            user_id=user_id,
            engine=engine,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="isIamUser")
    @builtins.classmethod
    def is_iam_user(cls, x: typing.Any) -> builtins.bool:
        '''(experimental) Return whether the given object is an ``IamUser``.

        :param x: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__56ae57372703251157d6443ab7d50a7fb49b8fb55b46cd8347c43f74293ca79d)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isIamUser", [x]))

    @jsii.member(jsii_name="grant")
    def grant(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
        *actions: builtins.str,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant the given identity custom permissions.

        :param grantee: The IAM identity to grant permissions to.
        :param actions: The actions to grant.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__531923e678be4fb8e2101687229c243b4b35916ffa1ac12568143d638d36f840)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
            check_type(argname="argument actions", value=actions, expected_type=typing.Tuple[type_hints["actions"], ...]) # pyright: ignore [reportGeneralTypeIssues]
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grant", [grantee, *actions]))

    @jsii.member(jsii_name="grantConnect")
    def grant_connect(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''(experimental) Grant connect permissions to the given IAM identity.

        :param grantee: The IAM identity to grant permissions to.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__68f423048bb8be45471234dabf5ec309183d8ff58b20ee2f283635f6f50a44fc)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantConnect", [grantee]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="accessString")
    def access_string(self) -> builtins.str:
        '''(experimental) The access string that defines the user's permissions.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "accessString"))

    @builtins.property
    @jsii.member(jsii_name="userArn")
    def user_arn(self) -> builtins.str:
        '''(experimental) The user's ARN.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userArn"))

    @builtins.property
    @jsii.member(jsii_name="userId")
    def user_id(self) -> builtins.str:
        '''(experimental) The user's ID.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userId"))

    @builtins.property
    @jsii.member(jsii_name="userStatus")
    def user_status(self) -> builtins.str:
        '''(experimental) The user's status.

        Can be 'active', 'modifying', 'deleting'.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userStatus"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine for the user.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[UserEngine], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="userName")
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The user's name.

        For IAM authentication userName must be equal to userId.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userName"))


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.IamUserProps",
    jsii_struct_bases=[UserBaseProps],
    name_mapping={
        "access_control": "accessControl",
        "user_id": "userId",
        "engine": "engine",
        "user_name": "userName",
    },
)
class IamUserProps(UserBaseProps):
    def __init__(
        self,
        *,
        access_control: AccessControl,
        user_id: builtins.str,
        engine: typing.Optional[UserEngine] = None,
        user_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Properties for defining an ElastiCache user with IAM authentication.

        :param access_control: (experimental) Access control configuration for the user.
        :param user_id: (experimental) The ID of the user.
        :param engine: (experimental) The engine type for the user. Enum options: UserEngine.VALKEY, UserEngine.REDIS. Default: UserEngine.VALKEY.
        :param user_name: (experimental) The name of the user. Default: - Same as userId.

        :stability: experimental
        :exampleMetadata: infused

        Example::

            user = elasticache.IamUser(self, "User",
                # set user engine
                engine=elasticache.UserEngine.REDIS,
            
                # set user id
                user_id="my-user",
            
                # set username
                user_name="my-user",
            
                # set access string
                access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__71d61e28530130d34f11937e2bce8b514fb2f950b88f5a02e6f48f3be2c7f15a)
            check_type(argname="argument access_control", value=access_control, expected_type=type_hints["access_control"])
            check_type(argname="argument user_id", value=user_id, expected_type=type_hints["user_id"])
            check_type(argname="argument engine", value=engine, expected_type=type_hints["engine"])
            check_type(argname="argument user_name", value=user_name, expected_type=type_hints["user_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "access_control": access_control,
            "user_id": user_id,
        }
        if engine is not None:
            self._values["engine"] = engine
        if user_name is not None:
            self._values["user_name"] = user_name

    @builtins.property
    def access_control(self) -> AccessControl:
        '''(experimental) Access control configuration for the user.

        :stability: experimental
        '''
        result = self._values.get("access_control")
        assert result is not None, "Required property 'access_control' is missing"
        return typing.cast(AccessControl, result)

    @builtins.property
    def user_id(self) -> builtins.str:
        '''(experimental) The ID of the user.

        :stability: experimental
        '''
        result = self._values.get("user_id")
        assert result is not None, "Required property 'user_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine type for the user.

        Enum options: UserEngine.VALKEY, UserEngine.REDIS.

        :default: UserEngine.VALKEY.

        :stability: experimental
        '''
        result = self._values.get("engine")
        return typing.cast(typing.Optional[UserEngine], result)

    @builtins.property
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the user.

        :default: - Same as userId.

        :stability: experimental
        '''
        result = self._values.get("user_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IamUserProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class NoPasswordUser(
    UserBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-elasticache-alpha.NoPasswordUser",
):
    '''(experimental) Define an ElastiCache user with no password authentication.

    :stability: experimental
    :resource: AWS::ElastiCache::User
    :exampleMetadata: infused

    Example::

        # use the original `default` user by using import method
        default_user = elasticache.NoPasswordUser.from_user_attributes(self, "DefaultUser",
            # userId and userName must be 'default'
            user_id="default"
        )
        
        # create a new default user
        new_default_user = elasticache.NoPasswordUser(self, "NewDefaultUser",
            # new default user id must not be 'default'
            user_id="new-default",
            # new default username must be 'default'
            user_name="default",
            # set access string
            access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
        )
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        user_name: typing.Optional[builtins.str] = None,
        access_control: AccessControl,
        user_id: builtins.str,
        engine: typing.Optional[UserEngine] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param user_name: (experimental) The name of the user. Default: - Same as userId.
        :param access_control: (experimental) Access control configuration for the user.
        :param user_id: (experimental) The ID of the user.
        :param engine: (experimental) The engine type for the user. Enum options: UserEngine.VALKEY, UserEngine.REDIS. Default: UserEngine.VALKEY.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__220efdd6a1ee333465f59b25a57b6b5c8fa267e557e225d08a230326886d4212)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = NoPasswordUserProps(
            user_name=user_name,
            access_control=access_control,
            user_id=user_id,
            engine=engine,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="isNoPasswordUser")
    @builtins.classmethod
    def is_no_password_user(cls, x: typing.Any) -> builtins.bool:
        '''(experimental) Return whether the given object is a ``NoPasswordUser``.

        :param x: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__504a0278e91c4ca35ec41ada718d541ca6ac49f8ac4304d02e0fd7bb57df426e)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isNoPasswordUser", [x]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="accessString")
    def access_string(self) -> builtins.str:
        '''(experimental) The access string that defines the user's permissions.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "accessString"))

    @builtins.property
    @jsii.member(jsii_name="userArn")
    def user_arn(self) -> builtins.str:
        '''(experimental) The user's ARN.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userArn"))

    @builtins.property
    @jsii.member(jsii_name="userId")
    def user_id(self) -> builtins.str:
        '''(experimental) The user's ID.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userId"))

    @builtins.property
    @jsii.member(jsii_name="userStatus")
    def user_status(self) -> builtins.str:
        '''(experimental) The user's status.

        Can be 'active', 'modifying', 'deleting'.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userStatus"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine for the user.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[UserEngine], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="userName")
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The user's name.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userName"))


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.NoPasswordUserProps",
    jsii_struct_bases=[UserBaseProps],
    name_mapping={
        "access_control": "accessControl",
        "user_id": "userId",
        "engine": "engine",
        "user_name": "userName",
    },
)
class NoPasswordUserProps(UserBaseProps):
    def __init__(
        self,
        *,
        access_control: AccessControl,
        user_id: builtins.str,
        engine: typing.Optional[UserEngine] = None,
        user_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Properties for defining an ElastiCache user with no password authentication.

        :param access_control: (experimental) Access control configuration for the user.
        :param user_id: (experimental) The ID of the user.
        :param engine: (experimental) The engine type for the user. Enum options: UserEngine.VALKEY, UserEngine.REDIS. Default: UserEngine.VALKEY.
        :param user_name: (experimental) The name of the user. Default: - Same as userId.

        :stability: experimental
        :exampleMetadata: infused

        Example::

            # use the original `default` user by using import method
            default_user = elasticache.NoPasswordUser.from_user_attributes(self, "DefaultUser",
                # userId and userName must be 'default'
                user_id="default"
            )
            
            # create a new default user
            new_default_user = elasticache.NoPasswordUser(self, "NewDefaultUser",
                # new default user id must not be 'default'
                user_id="new-default",
                # new default username must be 'default'
                user_name="default",
                # set access string
                access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1945122f32e59fe859a4e110d6cb24139e14754f7652d849daa8838a0e30bd81)
            check_type(argname="argument access_control", value=access_control, expected_type=type_hints["access_control"])
            check_type(argname="argument user_id", value=user_id, expected_type=type_hints["user_id"])
            check_type(argname="argument engine", value=engine, expected_type=type_hints["engine"])
            check_type(argname="argument user_name", value=user_name, expected_type=type_hints["user_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "access_control": access_control,
            "user_id": user_id,
        }
        if engine is not None:
            self._values["engine"] = engine
        if user_name is not None:
            self._values["user_name"] = user_name

    @builtins.property
    def access_control(self) -> AccessControl:
        '''(experimental) Access control configuration for the user.

        :stability: experimental
        '''
        result = self._values.get("access_control")
        assert result is not None, "Required property 'access_control' is missing"
        return typing.cast(AccessControl, result)

    @builtins.property
    def user_id(self) -> builtins.str:
        '''(experimental) The ID of the user.

        :stability: experimental
        '''
        result = self._values.get("user_id")
        assert result is not None, "Required property 'user_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine type for the user.

        Enum options: UserEngine.VALKEY, UserEngine.REDIS.

        :default: UserEngine.VALKEY.

        :stability: experimental
        '''
        result = self._values.get("engine")
        return typing.cast(typing.Optional[UserEngine], result)

    @builtins.property
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the user.

        :default: - Same as userId.

        :stability: experimental
        '''
        result = self._values.get("user_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NoPasswordUserProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class PasswordUser(
    UserBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-elasticache-alpha.PasswordUser",
):
    '''(experimental) Define an ElastiCache user with password authentication.

    :stability: experimental
    :resource: AWS::ElastiCache::User
    :exampleMetadata: infused

    Example::

        user = elasticache.PasswordUser(self, "User",
            # set user engine
            engine=elasticache.UserEngine.VALKEY,
        
            # set user id
            user_id="my-user-id",
        
            # set access string
            access_control=elasticache.AccessControl.from_access_string("on ~* +@all"),
        
            # set username
            user_name="my-user-name",
        
            # set up to two passwords
            passwords=[
                # "SecretIdForPassword" is the secret id for the password
                SecretValue.secrets_manager("SecretIdForPassword"),
                # "AnotherSecretIdForPassword" is the secret id for the password
                SecretValue.secrets_manager("AnotherSecretIdForPassword")
            ]
        )
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        passwords: typing.Sequence[_aws_cdk_ceddda9d.SecretValue],
        user_name: typing.Optional[builtins.str] = None,
        access_control: AccessControl,
        user_id: builtins.str,
        engine: typing.Optional[UserEngine] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param passwords: (experimental) The passwords for the user. Password authentication requires using 1-2 passwords.
        :param user_name: (experimental) The name of the user. Default: - Same as userId.
        :param access_control: (experimental) Access control configuration for the user.
        :param user_id: (experimental) The ID of the user.
        :param engine: (experimental) The engine type for the user. Enum options: UserEngine.VALKEY, UserEngine.REDIS. Default: UserEngine.VALKEY.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1e27f6a80117c6a240801779b06ee60ad2ff950cec5f4ff2c781cedcb4fe1b2c)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = PasswordUserProps(
            passwords=passwords,
            user_name=user_name,
            access_control=access_control,
            user_id=user_id,
            engine=engine,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="isPasswordUser")
    @builtins.classmethod
    def is_password_user(cls, x: typing.Any) -> builtins.bool:
        '''(experimental) Return whether the given object is a ``PasswordUser``.

        :param x: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e497a332be1ff515e12ea3e1ea5d80ec514cc2e9af73e4ac2b319b092a332121)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isPasswordUser", [x]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="accessString")
    def access_string(self) -> builtins.str:
        '''(experimental) The access string that defines the user's permissions.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "accessString"))

    @builtins.property
    @jsii.member(jsii_name="userArn")
    def user_arn(self) -> builtins.str:
        '''(experimental) The user's ARN.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userArn"))

    @builtins.property
    @jsii.member(jsii_name="userId")
    def user_id(self) -> builtins.str:
        '''(experimental) The user's ID.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userId"))

    @builtins.property
    @jsii.member(jsii_name="userStatus")
    def user_status(self) -> builtins.str:
        '''(experimental) The user's status.

        Can be 'active', 'modifying', 'deleting'.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userStatus"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine for the user.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[UserEngine], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="userName")
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The user's name.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userName"))


@jsii.data_type(
    jsii_type="@aws-cdk/aws-elasticache-alpha.PasswordUserProps",
    jsii_struct_bases=[UserBaseProps],
    name_mapping={
        "access_control": "accessControl",
        "user_id": "userId",
        "engine": "engine",
        "passwords": "passwords",
        "user_name": "userName",
    },
)
class PasswordUserProps(UserBaseProps):
    def __init__(
        self,
        *,
        access_control: AccessControl,
        user_id: builtins.str,
        engine: typing.Optional[UserEngine] = None,
        passwords: typing.Sequence[_aws_cdk_ceddda9d.SecretValue],
        user_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Properties for defining an ElastiCache user with password authentication.

        :param access_control: (experimental) Access control configuration for the user.
        :param user_id: (experimental) The ID of the user.
        :param engine: (experimental) The engine type for the user. Enum options: UserEngine.VALKEY, UserEngine.REDIS. Default: UserEngine.VALKEY.
        :param passwords: (experimental) The passwords for the user. Password authentication requires using 1-2 passwords.
        :param user_name: (experimental) The name of the user. Default: - Same as userId.

        :stability: experimental
        :exampleMetadata: infused

        Example::

            user = elasticache.PasswordUser(self, "User",
                # set user engine
                engine=elasticache.UserEngine.VALKEY,
            
                # set user id
                user_id="my-user-id",
            
                # set access string
                access_control=elasticache.AccessControl.from_access_string("on ~* +@all"),
            
                # set username
                user_name="my-user-name",
            
                # set up to two passwords
                passwords=[
                    # "SecretIdForPassword" is the secret id for the password
                    SecretValue.secrets_manager("SecretIdForPassword"),
                    # "AnotherSecretIdForPassword" is the secret id for the password
                    SecretValue.secrets_manager("AnotherSecretIdForPassword")
                ]
            )
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__86efaa461d323dc3423a5acef5393ef236f32cc15f45d769ae260baed5afcdff)
            check_type(argname="argument access_control", value=access_control, expected_type=type_hints["access_control"])
            check_type(argname="argument user_id", value=user_id, expected_type=type_hints["user_id"])
            check_type(argname="argument engine", value=engine, expected_type=type_hints["engine"])
            check_type(argname="argument passwords", value=passwords, expected_type=type_hints["passwords"])
            check_type(argname="argument user_name", value=user_name, expected_type=type_hints["user_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "access_control": access_control,
            "user_id": user_id,
            "passwords": passwords,
        }
        if engine is not None:
            self._values["engine"] = engine
        if user_name is not None:
            self._values["user_name"] = user_name

    @builtins.property
    def access_control(self) -> AccessControl:
        '''(experimental) Access control configuration for the user.

        :stability: experimental
        '''
        result = self._values.get("access_control")
        assert result is not None, "Required property 'access_control' is missing"
        return typing.cast(AccessControl, result)

    @builtins.property
    def user_id(self) -> builtins.str:
        '''(experimental) The ID of the user.

        :stability: experimental
        '''
        result = self._values.get("user_id")
        assert result is not None, "Required property 'user_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine type for the user.

        Enum options: UserEngine.VALKEY, UserEngine.REDIS.

        :default: UserEngine.VALKEY.

        :stability: experimental
        '''
        result = self._values.get("engine")
        return typing.cast(typing.Optional[UserEngine], result)

    @builtins.property
    def passwords(self) -> typing.List[_aws_cdk_ceddda9d.SecretValue]:
        '''(experimental) The passwords for the user.

        Password authentication requires using 1-2 passwords.

        :stability: experimental
        '''
        result = self._values.get("passwords")
        assert result is not None, "Required property 'passwords' is missing"
        return typing.cast(typing.List[_aws_cdk_ceddda9d.SecretValue], result)

    @builtins.property
    def user_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the user.

        :default: - Same as userId.

        :stability: experimental
        '''
        result = self._values.get("user_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PasswordUserProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ServerlessCache(
    ServerlessCacheBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-elasticache-alpha.ServerlessCache",
):
    '''(experimental) A serverless ElastiCache cache.

    :stability: experimental
    :resource: AWS::ElastiCache::ServerlessCache
    :exampleMetadata: infused

    Example::

        # vpc: ec2.Vpc
        
        
        serverless_cache = elasticache.ServerlessCache(self, "ServerlessCache",
            engine=elasticache.CacheEngine.VALKEY_LATEST,
            backup=elasticache.BackupSettings(
                # set a backup name before deleting a cache
                backup_name_before_deletion="my-final-backup-name"
            ),
            vpc=vpc
        )
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
        backup: typing.Optional[typing.Union[BackupSettings, typing.Dict[builtins.str, typing.Any]]] = None,
        cache_usage_limits: typing.Optional[typing.Union[CacheUsageLimitsProperty, typing.Dict[builtins.str, typing.Any]]] = None,
        description: typing.Optional[builtins.str] = None,
        engine: typing.Optional[CacheEngine] = None,
        kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        serverless_cache_name: typing.Optional[builtins.str] = None,
        user_group: typing.Optional[IUserGroup] = None,
        vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param vpc: (experimental) The VPC to place the cache in.
        :param backup: (experimental) Backup configuration. Default: - No backups configured
        :param cache_usage_limits: (experimental) Usage limits for the cache. Default: - No usage limits
        :param description: (experimental) A description for the cache. Default: - No description
        :param engine: (experimental) The cache engine combined with the version Enum options: VALKEY_DEFAULT, VALKEY_7, VALKEY_8, REDIS_DEFAULT, MEMCACHED_DEFAULT The default options bring the latest versions available. Default: when not provided, the default engine would be Valkey, latest version available (VALKEY_DEFAULT)
        :param kms_key: (experimental) KMS key for encryption. Default: - Service managed encryption (AWS owned KMS key)
        :param security_groups: (experimental) Security groups for the cache. Default: - A new security group is created
        :param serverless_cache_name: (experimental) Name for the serverless cache. Default: automatically generated name by Resource
        :param user_group: (experimental) User group for access control. Default: - No user group
        :param vpc_subnets: (experimental) Which subnets to place the cache in. Default: - Private subnets with egress

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8da89d4a89db427adb5af73feb884b509a358374f44df4c6e4e9cefdfeb388b7)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ServerlessCacheProps(
            vpc=vpc,
            backup=backup,
            cache_usage_limits=cache_usage_limits,
            description=description,
            engine=engine,
            kms_key=kms_key,
            security_groups=security_groups,
            serverless_cache_name=serverless_cache_name,
            user_group=user_group,
            vpc_subnets=vpc_subnets,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromServerlessCacheArn")
    @builtins.classmethod
    def from_serverless_cache_arn(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        serverless_cache_arn: builtins.str,
    ) -> IServerlessCache:
        '''(experimental) Import an existing serverless cache by ARN.

        :param scope: The parent creating construct (usually ``this``).
        :param id: The construct's name.
        :param serverless_cache_arn: The ARN of the existing serverless cache.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c99f6acaff34f5944552932163c59b887083fb8aed98020eacc0f564f72ba22d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument serverless_cache_arn", value=serverless_cache_arn, expected_type=type_hints["serverless_cache_arn"])
        return typing.cast(IServerlessCache, jsii.sinvoke(cls, "fromServerlessCacheArn", [scope, id, serverless_cache_arn]))

    @jsii.member(jsii_name="fromServerlessCacheAttributes")
    @builtins.classmethod
    def from_serverless_cache_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        backup_arns_to_restore: typing.Optional[typing.Sequence[builtins.str]] = None,
        engine: typing.Optional[CacheEngine] = None,
        kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
        security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
        serverless_cache_arn: typing.Optional[builtins.str] = None,
        serverless_cache_name: typing.Optional[builtins.str] = None,
        subnets: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISubnet]] = None,
        user_group: typing.Optional[IUserGroup] = None,
        vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    ) -> IServerlessCache:
        '''(experimental) Import an existing serverless cache using attributes.

        :param scope: The parent creating construct (usually ``this``).
        :param id: The construct's name.
        :param backup_arns_to_restore: (experimental) The ARNs of backups restored in the cache. Default: - backups are unknown
        :param engine: (experimental) The cache engine used by this cache. Default: - engine type is unknown
        :param kms_key: (experimental) The KMS key used for encryption. Default: - encryption key is unknown
        :param security_groups: (experimental) The security groups associated with this cache. Default: - security groups are unknown
        :param serverless_cache_arn: (experimental) The ARN of the serverless cache. One of ``serverlessCacheName`` or ``serverlessCacheArn`` is required. Default: - derived from serverlessCacheName
        :param serverless_cache_name: (experimental) The name of the serverless cache. One of ``serverlessCacheName`` or ``serverlessCacheArn`` is required. Default: - derived from serverlessCacheArn
        :param subnets: (experimental) The subnets this cache is deployed in. Default: - subnets are unknown
        :param user_group: (experimental) The user group associated with this cache. Default: - user group is unknown
        :param vpc: (experimental) The VPC this cache is deployed in. Default: - VPC is unknown

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3bb6bd61b0b428cb63e0c58200191068ecf8b4db4325e8fb0a507de9e307fc73)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = ServerlessCacheAttributes(
            backup_arns_to_restore=backup_arns_to_restore,
            engine=engine,
            kms_key=kms_key,
            security_groups=security_groups,
            serverless_cache_arn=serverless_cache_arn,
            serverless_cache_name=serverless_cache_name,
            subnets=subnets,
            user_group=user_group,
            vpc=vpc,
        )

        return typing.cast(IServerlessCache, jsii.sinvoke(cls, "fromServerlessCacheAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="fromServerlessCacheName")
    @builtins.classmethod
    def from_serverless_cache_name(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        serverless_cache_name: builtins.str,
    ) -> IServerlessCache:
        '''(experimental) Import an existing serverless cache by name.

        :param scope: The parent creating construct (usually ``this``).
        :param id: The construct's name.
        :param serverless_cache_name: The name of the existing serverless cache.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5b140560c718e68d17b3c02c3f4bee0785d6f5c53f4f666665b6b1e2e1cfc452)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument serverless_cache_name", value=serverless_cache_name, expected_type=type_hints["serverless_cache_name"])
        return typing.cast(IServerlessCache, jsii.sinvoke(cls, "fromServerlessCacheName", [scope, id, serverless_cache_name]))

    @jsii.member(jsii_name="isServerlessCache")
    @builtins.classmethod
    def is_serverless_cache(cls, x: typing.Any) -> builtins.bool:
        '''(experimental) Return whether the given object is a ``ServerlessCache``.

        :param x: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1c8f70299e49bf30ff971c7a7af719b8a69a14371b7f98c85365685c0c00f369)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isServerlessCache", [x]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="connections")
    def connections(self) -> _aws_cdk_aws_ec2_ceddda9d.Connections:
        '''(experimental) Access to network connections.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.Connections, jsii.get(self, "connections"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheArn")
    def serverless_cache_arn(self) -> builtins.str:
        '''(experimental) The ARN of the serverless cache.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheArn"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheEndpointAddress")
    def serverless_cache_endpoint_address(self) -> builtins.str:
        '''(experimental) The endpoint address of the serverless cache.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheEndpointAddress"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheEndpointPort")
    def serverless_cache_endpoint_port(self) -> builtins.str:
        '''(experimental) The endpoint port of the serverless cache.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheEndpointPort"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheName")
    def serverless_cache_name(self) -> builtins.str:
        '''(experimental) The name of the serverless cache.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheName"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheReaderEndpointAddress")
    def serverless_cache_reader_endpoint_address(self) -> builtins.str:
        '''(experimental) The reader endpoint address of the serverless cache.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheReaderEndpointAddress"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheReaderEndpointPort")
    def serverless_cache_reader_endpoint_port(self) -> builtins.str:
        '''(experimental) The reader endpoint port of the serverless cache.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheReaderEndpointPort"))

    @builtins.property
    @jsii.member(jsii_name="serverlessCacheStatus")
    def serverless_cache_status(self) -> builtins.str:
        '''(experimental) The current status of the serverless cache Can be 'CREATING', 'AVAILABLE', 'DELETING', 'CREATE-FAILED', 'MODIFYING'.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "serverlessCacheStatus"))

    @builtins.property
    @jsii.member(jsii_name="backupArnsToRestore")
    def backup_arns_to_restore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) The ARNs of backups restored in the cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "backupArnsToRestore"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional[CacheEngine]:
        '''(experimental) The cache engine used by this cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[CacheEngine], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        '''(experimental) The KMS key used for encryption.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="securityGroups")
    def security_groups(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]]:
        '''(experimental) The security groups associated with this cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]], jsii.get(self, "securityGroups"))

    @builtins.property
    @jsii.member(jsii_name="subnets")
    def subnets(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]]:
        '''(experimental) The subnets this cache is deployed in.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_ec2_ceddda9d.ISubnet]], jsii.get(self, "subnets"))

    @builtins.property
    @jsii.member(jsii_name="userGroup")
    def user_group(self) -> typing.Optional[IUserGroup]:
        '''(experimental) The user group associated with this cache.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[IUserGroup], jsii.get(self, "userGroup"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''(experimental) The VPC this cache is deployed in.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))


class UserGroup(
    UserGroupBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-elasticache-alpha.UserGroup",
):
    '''(experimental) An ElastiCache UserGroup.

    :stability: experimental
    :resource: AWS::ElastiCache::UserGroup
    :exampleMetadata: infused

    Example::

        new_default_user = elasticache.NoPasswordUser(self, "NoPasswordUser",
            user_id="default",
            access_control=elasticache.AccessControl.from_access_string("on ~* +@all")
        )
        
        user_group = elasticache.UserGroup(self, "UserGroup",
            users=[new_default_user]
        )
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        engine: typing.Optional[UserEngine] = None,
        user_group_name: typing.Optional[builtins.str] = None,
        users: typing.Optional[typing.Sequence[IUser]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param engine: (experimental) The engine type for the user group Enum options: UserEngine.VALKEY, UserEngine.REDIS. Default: UserEngine.VALKEY
        :param user_group_name: (experimental) Enforces a particular physical user group name. Default: 
        :param users: (experimental) List of users inside the user group. Default: - no users

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9f869e1edde0796f11475dd05c29721098eccbc302914cc05e0a4c088a5266ae)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = UserGroupProps(
            engine=engine, user_group_name=user_group_name, users=users
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromUserGroupArn")
    @builtins.classmethod
    def from_user_group_arn(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        user_group_arn: builtins.str,
    ) -> IUserGroup:
        '''(experimental) Import an existing user group by ARN.

        :param scope: The parent creating construct (usually ``this``).
        :param id: The construct's name.
        :param user_group_arn: The ARN of the existing user group.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a598bc13db0b0d1d6eeb6564127a8eef0bf03017cbdaedda17ee1283ff98a5be)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument user_group_arn", value=user_group_arn, expected_type=type_hints["user_group_arn"])
        return typing.cast(IUserGroup, jsii.sinvoke(cls, "fromUserGroupArn", [scope, id, user_group_arn]))

    @jsii.member(jsii_name="fromUserGroupAttributes")
    @builtins.classmethod
    def from_user_group_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        engine: typing.Optional[UserEngine] = None,
        user_group_arn: typing.Optional[builtins.str] = None,
        user_group_name: typing.Optional[builtins.str] = None,
        users: typing.Optional[typing.Sequence[IUser]] = None,
    ) -> IUserGroup:
        '''(experimental) Import an existing user group using attributes.

        :param scope: The parent creating construct (usually ``this``).
        :param id: The construct's name.
        :param engine: (experimental) The engine type for the user group. Default: - engine type is unknown
        :param user_group_arn: (experimental) The ARN of the user group. One of ``userGroupName`` or ``userGroupArn`` is required. Default: - derived from userGroupName
        :param user_group_name: (experimental) The name of the user group. One of ``userGroupName`` or ``userGroupArn`` is required. Default: - derived from userGroupArn
        :param users: (experimental) List of users in the user group. Default: - users are unknown

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__384b9299faa0c8136cd96b4dc0ce50de8719ed545a767c5a596cf1eef5086095)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = UserGroupAttributes(
            engine=engine,
            user_group_arn=user_group_arn,
            user_group_name=user_group_name,
            users=users,
        )

        return typing.cast(IUserGroup, jsii.sinvoke(cls, "fromUserGroupAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="fromUserGroupName")
    @builtins.classmethod
    def from_user_group_name(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        user_group_name: builtins.str,
    ) -> IUserGroup:
        '''(experimental) Import an existing user group by name.

        :param scope: The parent creating construct (usually ``this``).
        :param id: The construct's name.
        :param user_group_name: The name of the existing user group.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f35cf585e21df1ff872f721dd715750a91217dfe11c2b54b8d7ee36815596b77)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument user_group_name", value=user_group_name, expected_type=type_hints["user_group_name"])
        return typing.cast(IUserGroup, jsii.sinvoke(cls, "fromUserGroupName", [scope, id, user_group_name]))

    @jsii.member(jsii_name="isUserGroup")
    @builtins.classmethod
    def is_user_group(cls, x: typing.Any) -> builtins.bool:
        '''(experimental) Return whether the given object is a ``UserGroup``.

        :param x: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__77a47106b8ab52cc4a788213f6b3e992c521806a492218507e9ab60aa1a2c23f)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isUserGroup", [x]))

    @jsii.member(jsii_name="addUser")
    def add_user(self, user: IUser) -> None:
        '''(experimental) Add a user to this user group.

        :param user: The user to add to the group.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__88c92cd5ecefa34613ada785b685b5b6c86ee832d320e4f17883932e2850c269)
            check_type(argname="argument user", value=user, expected_type=type_hints["user"])
        return typing.cast(None, jsii.invoke(self, "addUser", [user]))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_INJECTION_ID")
    def PROPERTY_INJECTION_ID(cls) -> builtins.str:
        '''(experimental) Uniquely identifies this class.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_INJECTION_ID"))

    @builtins.property
    @jsii.member(jsii_name="userGroupArn")
    def user_group_arn(self) -> builtins.str:
        '''(experimental) The ARN of the user group.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="userGroupName")
    def user_group_name(self) -> builtins.str:
        '''(experimental) The name of the user group.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "userGroupName"))

    @builtins.property
    @jsii.member(jsii_name="userGroupStatus")
    def user_group_status(self) -> builtins.str:
        '''(experimental) The status of the user group Can be 'creating', 'active', 'modifying', 'deleting'.

        :stability: experimental
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "userGroupStatus"))

    @builtins.property
    @jsii.member(jsii_name="engine")
    def engine(self) -> typing.Optional[UserEngine]:
        '''(experimental) The engine type for the user group.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[UserEngine], jsii.get(self, "engine"))

    @builtins.property
    @jsii.member(jsii_name="users")
    def users(self) -> typing.Optional[typing.List[IUser]]:
        '''(experimental) Array of users in the user group.

        Do not push directly to this array.
        Use addUser() instead to ensure proper validation and dependency management.

        :stability: experimental
        '''
        return typing.cast(typing.Optional[typing.List[IUser]], jsii.get(self, "users"))


__all__ = [
    "AccessControl",
    "BackupSettings",
    "CacheEngine",
    "CacheUsageLimitsProperty",
    "IServerlessCache",
    "IUser",
    "IUserGroup",
    "IamUser",
    "IamUserProps",
    "NoPasswordUser",
    "NoPasswordUserProps",
    "PasswordUser",
    "PasswordUserProps",
    "ServerlessCache",
    "ServerlessCacheAttributes",
    "ServerlessCacheBase",
    "ServerlessCacheProps",
    "UserBase",
    "UserBaseAttributes",
    "UserBaseProps",
    "UserEngine",
    "UserGroup",
    "UserGroupAttributes",
    "UserGroupBase",
    "UserGroupProps",
]

publication.publish()

def _typecheckingstub__e620f1697be9aecd3a467c280159a620b782aa506dafa85fd157be6ea7fe422e(
    access_string: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ea85e979f440b15805c41c71f6c52d492e8ed626b8475463ad82343ef2dd8229(
    *,
    backup_arns_to_restore: typing.Optional[typing.Sequence[builtins.str]] = None,
    backup_name_before_deletion: typing.Optional[builtins.str] = None,
    backup_retention_limit: typing.Optional[jsii.Number] = None,
    backup_time: typing.Optional[_aws_cdk_aws_events_ceddda9d.Schedule] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__efe6f2d96cd5b2f6811c325e3e6f8c033a8e1e3bad115c7ec1b3a89402890381(
    *,
    data_storage_maximum_size: typing.Optional[_aws_cdk_ceddda9d.Size] = None,
    data_storage_minimum_size: typing.Optional[_aws_cdk_ceddda9d.Size] = None,
    request_rate_limit_maximum: typing.Optional[jsii.Number] = None,
    request_rate_limit_minimum: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e10493c9f2558a6df1557a2b42846be6f6e2459b12e951d570214118623bf343(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    *actions: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b0289ab310f989d11350e0d7b6b9832083c842adcca6cee9b2aa5152d38320e9(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9a792c0c5412a4811be430d976e81b32b6eadc23f7744b57dbd29f21e9457854(
    metric_name: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9c80e32dcca4a85ef240faeaa9e93aa354e2eb9f07e6bfa3013f64da8314e02e(
    user: IUser,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__525223783a3311afa0f7f71caa1719da598d452009b52b3759771297039ab46d(
    *,
    backup_arns_to_restore: typing.Optional[typing.Sequence[builtins.str]] = None,
    engine: typing.Optional[CacheEngine] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    serverless_cache_arn: typing.Optional[builtins.str] = None,
    serverless_cache_name: typing.Optional[builtins.str] = None,
    subnets: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISubnet]] = None,
    user_group: typing.Optional[IUserGroup] = None,
    vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c7b51bf67205b95d0da44cd223fb2f868c44df176787b447d7896e1afb3dd6a6(
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

def _typecheckingstub__ad40da7b17882582727a25c5cae611995a4dc950a61c614016318b5b7ccb6033(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    *actions: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2ff19421655c341c2dcba401161d317db3e9c72bf8eb0e48622ad8857a4940bf(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c20ab5bdc4ec344507965f099a001907bcde7ed53841efac3f9c652f4b6bfa9c(
    metric_name: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    color: typing.Optional[builtins.str] = None,
    dimensions_map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    id: typing.Optional[builtins.str] = None,
    label: typing.Optional[builtins.str] = None,
    period: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
    region: typing.Optional[builtins.str] = None,
    stack_account: typing.Optional[builtins.str] = None,
    stack_region: typing.Optional[builtins.str] = None,
    statistic: typing.Optional[builtins.str] = None,
    unit: typing.Optional[_aws_cdk_aws_cloudwatch_ceddda9d.Unit] = None,
    visible: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f75886d0cff4f1478f060fc3093d5e18de249f98bfdb7f2e6af73b6053f6836(
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    backup: typing.Optional[typing.Union[BackupSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    cache_usage_limits: typing.Optional[typing.Union[CacheUsageLimitsProperty, typing.Dict[builtins.str, typing.Any]]] = None,
    description: typing.Optional[builtins.str] = None,
    engine: typing.Optional[CacheEngine] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    serverless_cache_name: typing.Optional[builtins.str] = None,
    user_group: typing.Optional[IUserGroup] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cd7b81bd91d16843f9e064a01afad15ad4ffd483149ced547a3469334cd684ea(
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

def _typecheckingstub__e761480c0ebfd294ebdec1335b328648571dec1230977aa4799c2820f7759c20(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    user_arn: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b1c7010a5023bb28d22488eefa8ca48e861974805fa4eae4c35433dd9893f3b5(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    engine: typing.Optional[UserEngine] = None,
    user_arn: typing.Optional[builtins.str] = None,
    user_id: typing.Optional[builtins.str] = None,
    user_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__704a3972bb194bf809ebf7e171d84072283c6436009df971b1302f13e7e3506b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    user_id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cdf1d20dc614181bdd9ec4f71003b1c6acdd827489b62d62be7fa2a11c2c8131(
    *,
    engine: typing.Optional[UserEngine] = None,
    user_arn: typing.Optional[builtins.str] = None,
    user_id: typing.Optional[builtins.str] = None,
    user_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f02aff3e7c2886ad06074fe94984dabf4561cfd6ed96513f581a7a9744e69253(
    *,
    access_control: AccessControl,
    user_id: builtins.str,
    engine: typing.Optional[UserEngine] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__db74853827d2f9386370091f5ca49d6c2aed58fa0432e0620e2035a7533112c1(
    *,
    engine: typing.Optional[UserEngine] = None,
    user_group_arn: typing.Optional[builtins.str] = None,
    user_group_name: typing.Optional[builtins.str] = None,
    users: typing.Optional[typing.Sequence[IUser]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__129a538a4481ec262096321ff41577cd9504c059761c56ebf0d64ab1d4e8bea9(
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

def _typecheckingstub__589f4a71a023f13cb4428634c1d5766cf35a5fe45f9a39d37a95d648e1b9230a(
    _user: IUser,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__47db8eef599a3412e1208c1788f490f7eef502c1862c5a129999646ffa5df171(
    *,
    engine: typing.Optional[UserEngine] = None,
    user_group_name: typing.Optional[builtins.str] = None,
    users: typing.Optional[typing.Sequence[IUser]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__009b9161fccb666529247da64089de9839548b5c2a964eb4e8043df674d87095(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    user_name: typing.Optional[builtins.str] = None,
    access_control: AccessControl,
    user_id: builtins.str,
    engine: typing.Optional[UserEngine] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__56ae57372703251157d6443ab7d50a7fb49b8fb55b46cd8347c43f74293ca79d(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__531923e678be4fb8e2101687229c243b4b35916ffa1ac12568143d638d36f840(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    *actions: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__68f423048bb8be45471234dabf5ec309183d8ff58b20ee2f283635f6f50a44fc(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__71d61e28530130d34f11937e2bce8b514fb2f950b88f5a02e6f48f3be2c7f15a(
    *,
    access_control: AccessControl,
    user_id: builtins.str,
    engine: typing.Optional[UserEngine] = None,
    user_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__220efdd6a1ee333465f59b25a57b6b5c8fa267e557e225d08a230326886d4212(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    user_name: typing.Optional[builtins.str] = None,
    access_control: AccessControl,
    user_id: builtins.str,
    engine: typing.Optional[UserEngine] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__504a0278e91c4ca35ec41ada718d541ca6ac49f8ac4304d02e0fd7bb57df426e(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1945122f32e59fe859a4e110d6cb24139e14754f7652d849daa8838a0e30bd81(
    *,
    access_control: AccessControl,
    user_id: builtins.str,
    engine: typing.Optional[UserEngine] = None,
    user_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e27f6a80117c6a240801779b06ee60ad2ff950cec5f4ff2c781cedcb4fe1b2c(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    passwords: typing.Sequence[_aws_cdk_ceddda9d.SecretValue],
    user_name: typing.Optional[builtins.str] = None,
    access_control: AccessControl,
    user_id: builtins.str,
    engine: typing.Optional[UserEngine] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e497a332be1ff515e12ea3e1ea5d80ec514cc2e9af73e4ac2b319b092a332121(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__86efaa461d323dc3423a5acef5393ef236f32cc15f45d769ae260baed5afcdff(
    *,
    access_control: AccessControl,
    user_id: builtins.str,
    engine: typing.Optional[UserEngine] = None,
    passwords: typing.Sequence[_aws_cdk_ceddda9d.SecretValue],
    user_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8da89d4a89db427adb5af73feb884b509a358374f44df4c6e4e9cefdfeb388b7(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    vpc: _aws_cdk_aws_ec2_ceddda9d.IVpc,
    backup: typing.Optional[typing.Union[BackupSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    cache_usage_limits: typing.Optional[typing.Union[CacheUsageLimitsProperty, typing.Dict[builtins.str, typing.Any]]] = None,
    description: typing.Optional[builtins.str] = None,
    engine: typing.Optional[CacheEngine] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    serverless_cache_name: typing.Optional[builtins.str] = None,
    user_group: typing.Optional[IUserGroup] = None,
    vpc_subnets: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.SubnetSelection, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c99f6acaff34f5944552932163c59b887083fb8aed98020eacc0f564f72ba22d(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    serverless_cache_arn: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3bb6bd61b0b428cb63e0c58200191068ecf8b4db4325e8fb0a507de9e307fc73(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    backup_arns_to_restore: typing.Optional[typing.Sequence[builtins.str]] = None,
    engine: typing.Optional[CacheEngine] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    serverless_cache_arn: typing.Optional[builtins.str] = None,
    serverless_cache_name: typing.Optional[builtins.str] = None,
    subnets: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISubnet]] = None,
    user_group: typing.Optional[IUserGroup] = None,
    vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5b140560c718e68d17b3c02c3f4bee0785d6f5c53f4f666665b6b1e2e1cfc452(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    serverless_cache_name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1c8f70299e49bf30ff971c7a7af719b8a69a14371b7f98c85365685c0c00f369(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9f869e1edde0796f11475dd05c29721098eccbc302914cc05e0a4c088a5266ae(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    engine: typing.Optional[UserEngine] = None,
    user_group_name: typing.Optional[builtins.str] = None,
    users: typing.Optional[typing.Sequence[IUser]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a598bc13db0b0d1d6eeb6564127a8eef0bf03017cbdaedda17ee1283ff98a5be(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    user_group_arn: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__384b9299faa0c8136cd96b4dc0ce50de8719ed545a767c5a596cf1eef5086095(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    engine: typing.Optional[UserEngine] = None,
    user_group_arn: typing.Optional[builtins.str] = None,
    user_group_name: typing.Optional[builtins.str] = None,
    users: typing.Optional[typing.Sequence[IUser]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f35cf585e21df1ff872f721dd715750a91217dfe11c2b54b8d7ee36815596b77(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    user_group_name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__77a47106b8ab52cc4a788213f6b3e992c521806a492218507e9ab60aa1a2c23f(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__88c92cd5ecefa34613ada785b685b5b6c86ee832d320e4f17883932e2850c269(
    user: IUser,
) -> None:
    """Type checking stubs"""
    pass
