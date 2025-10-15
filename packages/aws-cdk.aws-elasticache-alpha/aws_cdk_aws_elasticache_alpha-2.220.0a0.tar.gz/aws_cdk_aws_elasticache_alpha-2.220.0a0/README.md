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
