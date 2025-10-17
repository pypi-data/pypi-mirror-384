r'''
# `databricks_database_instance`

Refer to the Terraform Registry for docs: [`databricks_database_instance`](https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance).
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

import cdktf as _cdktf_9a9027ec
import constructs as _constructs_77d1e7e8


class DatabaseInstance(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstance",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance databricks_database_instance}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        name: builtins.str,
        capacity: typing.Optional[builtins.str] = None,
        custom_tags: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DatabaseInstanceCustomTags", typing.Dict[builtins.str, typing.Any]]]]] = None,
        enable_pg_native_login: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        enable_readable_secondaries: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        node_count: typing.Optional[jsii.Number] = None,
        parent_instance_ref: typing.Optional[typing.Union["DatabaseInstanceParentInstanceRef", typing.Dict[builtins.str, typing.Any]]] = None,
        purge_on_delete: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        retention_window_in_days: typing.Optional[jsii.Number] = None,
        stopped: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        usage_policy_id: typing.Optional[builtins.str] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance databricks_database_instance} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#name DatabaseInstance#name}.
        :param capacity: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#capacity DatabaseInstance#capacity}.
        :param custom_tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#custom_tags DatabaseInstance#custom_tags}.
        :param enable_pg_native_login: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#enable_pg_native_login DatabaseInstance#enable_pg_native_login}.
        :param enable_readable_secondaries: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#enable_readable_secondaries DatabaseInstance#enable_readable_secondaries}.
        :param node_count: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#node_count DatabaseInstance#node_count}.
        :param parent_instance_ref: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#parent_instance_ref DatabaseInstance#parent_instance_ref}.
        :param purge_on_delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#purge_on_delete DatabaseInstance#purge_on_delete}.
        :param retention_window_in_days: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#retention_window_in_days DatabaseInstance#retention_window_in_days}.
        :param stopped: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#stopped DatabaseInstance#stopped}.
        :param usage_policy_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#usage_policy_id DatabaseInstance#usage_policy_id}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__39f8ed0afe093cf72f4138d0a18915400567bcfb27ae1893c3ce48849a3b23cf)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = DatabaseInstanceConfig(
            name=name,
            capacity=capacity,
            custom_tags=custom_tags,
            enable_pg_native_login=enable_pg_native_login,
            enable_readable_secondaries=enable_readable_secondaries,
            node_count=node_count,
            parent_instance_ref=parent_instance_ref,
            purge_on_delete=purge_on_delete,
            retention_window_in_days=retention_window_in_days,
            stopped=stopped,
            usage_policy_id=usage_policy_id,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a DatabaseInstance resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DatabaseInstance to import.
        :param import_from_id: The id of the existing DatabaseInstance that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DatabaseInstance to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2ffd3b682212a973b7a4797509a116336f9dd85373cf8f906ca4c95557c51950)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putCustomTags")
    def put_custom_tags(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DatabaseInstanceCustomTags", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__28fbfdfea46a58c183ed59ca8169dde09ab12ccb8648f6ece0804f79f0cf0b8d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putCustomTags", [value]))

    @jsii.member(jsii_name="putParentInstanceRef")
    def put_parent_instance_ref(
        self,
        *,
        branch_time: typing.Optional[builtins.str] = None,
        lsn: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param branch_time: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#branch_time DatabaseInstance#branch_time}.
        :param lsn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#lsn DatabaseInstance#lsn}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#name DatabaseInstance#name}.
        '''
        value = DatabaseInstanceParentInstanceRef(
            branch_time=branch_time, lsn=lsn, name=name
        )

        return typing.cast(None, jsii.invoke(self, "putParentInstanceRef", [value]))

    @jsii.member(jsii_name="resetCapacity")
    def reset_capacity(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCapacity", []))

    @jsii.member(jsii_name="resetCustomTags")
    def reset_custom_tags(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCustomTags", []))

    @jsii.member(jsii_name="resetEnablePgNativeLogin")
    def reset_enable_pg_native_login(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEnablePgNativeLogin", []))

    @jsii.member(jsii_name="resetEnableReadableSecondaries")
    def reset_enable_readable_secondaries(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEnableReadableSecondaries", []))

    @jsii.member(jsii_name="resetNodeCount")
    def reset_node_count(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNodeCount", []))

    @jsii.member(jsii_name="resetParentInstanceRef")
    def reset_parent_instance_ref(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetParentInstanceRef", []))

    @jsii.member(jsii_name="resetPurgeOnDelete")
    def reset_purge_on_delete(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPurgeOnDelete", []))

    @jsii.member(jsii_name="resetRetentionWindowInDays")
    def reset_retention_window_in_days(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRetentionWindowInDays", []))

    @jsii.member(jsii_name="resetStopped")
    def reset_stopped(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetStopped", []))

    @jsii.member(jsii_name="resetUsagePolicyId")
    def reset_usage_policy_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUsagePolicyId", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="childInstanceRefs")
    def child_instance_refs(self) -> "DatabaseInstanceChildInstanceRefsList":
        return typing.cast("DatabaseInstanceChildInstanceRefsList", jsii.get(self, "childInstanceRefs"))

    @builtins.property
    @jsii.member(jsii_name="creationTime")
    def creation_time(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "creationTime"))

    @builtins.property
    @jsii.member(jsii_name="creator")
    def creator(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "creator"))

    @builtins.property
    @jsii.member(jsii_name="customTags")
    def custom_tags(self) -> "DatabaseInstanceCustomTagsList":
        return typing.cast("DatabaseInstanceCustomTagsList", jsii.get(self, "customTags"))

    @builtins.property
    @jsii.member(jsii_name="effectiveCapacity")
    def effective_capacity(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "effectiveCapacity"))

    @builtins.property
    @jsii.member(jsii_name="effectiveCustomTags")
    def effective_custom_tags(self) -> "DatabaseInstanceEffectiveCustomTagsList":
        return typing.cast("DatabaseInstanceEffectiveCustomTagsList", jsii.get(self, "effectiveCustomTags"))

    @builtins.property
    @jsii.member(jsii_name="effectiveEnablePgNativeLogin")
    def effective_enable_pg_native_login(self) -> _cdktf_9a9027ec.IResolvable:
        return typing.cast(_cdktf_9a9027ec.IResolvable, jsii.get(self, "effectiveEnablePgNativeLogin"))

    @builtins.property
    @jsii.member(jsii_name="effectiveEnableReadableSecondaries")
    def effective_enable_readable_secondaries(self) -> _cdktf_9a9027ec.IResolvable:
        return typing.cast(_cdktf_9a9027ec.IResolvable, jsii.get(self, "effectiveEnableReadableSecondaries"))

    @builtins.property
    @jsii.member(jsii_name="effectiveNodeCount")
    def effective_node_count(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "effectiveNodeCount"))

    @builtins.property
    @jsii.member(jsii_name="effectiveRetentionWindowInDays")
    def effective_retention_window_in_days(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "effectiveRetentionWindowInDays"))

    @builtins.property
    @jsii.member(jsii_name="effectiveStopped")
    def effective_stopped(self) -> _cdktf_9a9027ec.IResolvable:
        return typing.cast(_cdktf_9a9027ec.IResolvable, jsii.get(self, "effectiveStopped"))

    @builtins.property
    @jsii.member(jsii_name="effectiveUsagePolicyId")
    def effective_usage_policy_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "effectiveUsagePolicyId"))

    @builtins.property
    @jsii.member(jsii_name="parentInstanceRef")
    def parent_instance_ref(self) -> "DatabaseInstanceParentInstanceRefOutputReference":
        return typing.cast("DatabaseInstanceParentInstanceRefOutputReference", jsii.get(self, "parentInstanceRef"))

    @builtins.property
    @jsii.member(jsii_name="pgVersion")
    def pg_version(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "pgVersion"))

    @builtins.property
    @jsii.member(jsii_name="readOnlyDns")
    def read_only_dns(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "readOnlyDns"))

    @builtins.property
    @jsii.member(jsii_name="readWriteDns")
    def read_write_dns(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "readWriteDns"))

    @builtins.property
    @jsii.member(jsii_name="state")
    def state(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "state"))

    @builtins.property
    @jsii.member(jsii_name="uid")
    def uid(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "uid"))

    @builtins.property
    @jsii.member(jsii_name="capacityInput")
    def capacity_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "capacityInput"))

    @builtins.property
    @jsii.member(jsii_name="customTagsInput")
    def custom_tags_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DatabaseInstanceCustomTags"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DatabaseInstanceCustomTags"]]], jsii.get(self, "customTagsInput"))

    @builtins.property
    @jsii.member(jsii_name="enablePgNativeLoginInput")
    def enable_pg_native_login_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "enablePgNativeLoginInput"))

    @builtins.property
    @jsii.member(jsii_name="enableReadableSecondariesInput")
    def enable_readable_secondaries_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "enableReadableSecondariesInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="nodeCountInput")
    def node_count_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "nodeCountInput"))

    @builtins.property
    @jsii.member(jsii_name="parentInstanceRefInput")
    def parent_instance_ref_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DatabaseInstanceParentInstanceRef"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DatabaseInstanceParentInstanceRef"]], jsii.get(self, "parentInstanceRefInput"))

    @builtins.property
    @jsii.member(jsii_name="purgeOnDeleteInput")
    def purge_on_delete_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "purgeOnDeleteInput"))

    @builtins.property
    @jsii.member(jsii_name="retentionWindowInDaysInput")
    def retention_window_in_days_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "retentionWindowInDaysInput"))

    @builtins.property
    @jsii.member(jsii_name="stoppedInput")
    def stopped_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "stoppedInput"))

    @builtins.property
    @jsii.member(jsii_name="usagePolicyIdInput")
    def usage_policy_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "usagePolicyIdInput"))

    @builtins.property
    @jsii.member(jsii_name="capacity")
    def capacity(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "capacity"))

    @capacity.setter
    def capacity(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fd15df291d7d47090118837041b521d1510e56c80e8559c134b3dd25466eec1c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "capacity", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="enablePgNativeLogin")
    def enable_pg_native_login(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "enablePgNativeLogin"))

    @enable_pg_native_login.setter
    def enable_pg_native_login(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3cb6e59fee7b184f79507e783e9f9b739338e6b7781e063f571240e1cab7613a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "enablePgNativeLogin", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="enableReadableSecondaries")
    def enable_readable_secondaries(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "enableReadableSecondaries"))

    @enable_readable_secondaries.setter
    def enable_readable_secondaries(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d5c10073505ead9d82bffcf9ed1838833c2602b384472d5fa2e45972998ec61a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "enableReadableSecondaries", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bc2098c0ec477fa2b3fe25aee8ad56046056073c141997e5dcb33bb5a3456c9b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="nodeCount")
    def node_count(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "nodeCount"))

    @node_count.setter
    def node_count(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cc0f157bd2b4860f0fe0430c3345f7f49e9b1e6d6d996cdba142a74fe5781af8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "nodeCount", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="purgeOnDelete")
    def purge_on_delete(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "purgeOnDelete"))

    @purge_on_delete.setter
    def purge_on_delete(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9b2206c2eaabddc33fa15b3c3ef371ee1c1bd42ae4d31c27e7ebb33822e76054)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "purgeOnDelete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="retentionWindowInDays")
    def retention_window_in_days(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "retentionWindowInDays"))

    @retention_window_in_days.setter
    def retention_window_in_days(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da6ba46d24a1715a60aa9b30de1d712d14970befe5930517ea21b3a0d08e8990)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "retentionWindowInDays", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stopped")
    def stopped(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "stopped"))

    @stopped.setter
    def stopped(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9bfe9c3a30b6b573a5594f5c00fc04e8dc827f40dc2081639a5e915a09a9c529)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stopped", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="usagePolicyId")
    def usage_policy_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "usagePolicyId"))

    @usage_policy_id.setter
    def usage_policy_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f60a31a8402c06968353c62250ee300c45fb2a293a1271c8a1634e0680b390f1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "usagePolicyId", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceChildInstanceRefs",
    jsii_struct_bases=[],
    name_mapping={"branch_time": "branchTime", "lsn": "lsn", "name": "name"},
)
class DatabaseInstanceChildInstanceRefs:
    def __init__(
        self,
        *,
        branch_time: typing.Optional[builtins.str] = None,
        lsn: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param branch_time: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#branch_time DatabaseInstance#branch_time}.
        :param lsn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#lsn DatabaseInstance#lsn}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#name DatabaseInstance#name}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fae60ba8be61b16989b10dcb410bf644c71056dab9b58b1fd0d42e38d6eccae7)
            check_type(argname="argument branch_time", value=branch_time, expected_type=type_hints["branch_time"])
            check_type(argname="argument lsn", value=lsn, expected_type=type_hints["lsn"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if branch_time is not None:
            self._values["branch_time"] = branch_time
        if lsn is not None:
            self._values["lsn"] = lsn
        if name is not None:
            self._values["name"] = name

    @builtins.property
    def branch_time(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#branch_time DatabaseInstance#branch_time}.'''
        result = self._values.get("branch_time")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def lsn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#lsn DatabaseInstance#lsn}.'''
        result = self._values.get("lsn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#name DatabaseInstance#name}.'''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DatabaseInstanceChildInstanceRefs(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DatabaseInstanceChildInstanceRefsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceChildInstanceRefsList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b19f27bdd66ce0681da8b64ea163ab9856a16a10a56733e23c1ef07771cda9be)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DatabaseInstanceChildInstanceRefsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ebdaf35ef23a291adab4aefc97da2dcf7e34b51d5426eecad1200310be8012cf)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DatabaseInstanceChildInstanceRefsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__60e2c4b595d6b7b5405b92334e029f4af109c7369c66bf0a607351ce98109e9a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9017074020736d940a9da4989f94da518df1e5d5e9d7a99742cc5e53aaddb9bf)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__57a75860f84df5e9475da63f37e4217235bb51dbec4ac3d5fb914a6cd53ca5cb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceChildInstanceRefs]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceChildInstanceRefs]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceChildInstanceRefs]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c6371d550055e8b6acfbe231c316ff7b8c905dc570c63b82117c754339901724)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DatabaseInstanceChildInstanceRefsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceChildInstanceRefsOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__24e1aa511d5bc6eb73eaf7ab7784ea0a128b5f22e6a14f5101605a8081c3f17c)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetBranchTime")
    def reset_branch_time(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBranchTime", []))

    @jsii.member(jsii_name="resetLsn")
    def reset_lsn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLsn", []))

    @jsii.member(jsii_name="resetName")
    def reset_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetName", []))

    @builtins.property
    @jsii.member(jsii_name="effectiveLsn")
    def effective_lsn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "effectiveLsn"))

    @builtins.property
    @jsii.member(jsii_name="uid")
    def uid(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "uid"))

    @builtins.property
    @jsii.member(jsii_name="branchTimeInput")
    def branch_time_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "branchTimeInput"))

    @builtins.property
    @jsii.member(jsii_name="lsnInput")
    def lsn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lsnInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="branchTime")
    def branch_time(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "branchTime"))

    @branch_time.setter
    def branch_time(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6cc9b750bb2a9224e60d6bd5efd9dfd6299517b694aa6b9ba4c469473672ed24)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "branchTime", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="lsn")
    def lsn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lsn"))

    @lsn.setter
    def lsn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c6c41e5bcafe6ae63b75f1fcd089bf8b704c615e0e4ba2684cbbad61271b7678)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "lsn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5ec88ce26d14522272eb08efe49285569133df191804146985ae7d8f21725445)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DatabaseInstanceChildInstanceRefs]:
        return typing.cast(typing.Optional[DatabaseInstanceChildInstanceRefs], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DatabaseInstanceChildInstanceRefs],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a82b80cda1d19b848372e476d95a6ca0cda30da5e8d383419e63b9b77562e38d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "name": "name",
        "capacity": "capacity",
        "custom_tags": "customTags",
        "enable_pg_native_login": "enablePgNativeLogin",
        "enable_readable_secondaries": "enableReadableSecondaries",
        "node_count": "nodeCount",
        "parent_instance_ref": "parentInstanceRef",
        "purge_on_delete": "purgeOnDelete",
        "retention_window_in_days": "retentionWindowInDays",
        "stopped": "stopped",
        "usage_policy_id": "usagePolicyId",
    },
)
class DatabaseInstanceConfig(_cdktf_9a9027ec.TerraformMetaArguments):
    def __init__(
        self,
        *,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
        name: builtins.str,
        capacity: typing.Optional[builtins.str] = None,
        custom_tags: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DatabaseInstanceCustomTags", typing.Dict[builtins.str, typing.Any]]]]] = None,
        enable_pg_native_login: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        enable_readable_secondaries: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        node_count: typing.Optional[jsii.Number] = None,
        parent_instance_ref: typing.Optional[typing.Union["DatabaseInstanceParentInstanceRef", typing.Dict[builtins.str, typing.Any]]] = None,
        purge_on_delete: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        retention_window_in_days: typing.Optional[jsii.Number] = None,
        stopped: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        usage_policy_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#name DatabaseInstance#name}.
        :param capacity: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#capacity DatabaseInstance#capacity}.
        :param custom_tags: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#custom_tags DatabaseInstance#custom_tags}.
        :param enable_pg_native_login: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#enable_pg_native_login DatabaseInstance#enable_pg_native_login}.
        :param enable_readable_secondaries: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#enable_readable_secondaries DatabaseInstance#enable_readable_secondaries}.
        :param node_count: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#node_count DatabaseInstance#node_count}.
        :param parent_instance_ref: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#parent_instance_ref DatabaseInstance#parent_instance_ref}.
        :param purge_on_delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#purge_on_delete DatabaseInstance#purge_on_delete}.
        :param retention_window_in_days: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#retention_window_in_days DatabaseInstance#retention_window_in_days}.
        :param stopped: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#stopped DatabaseInstance#stopped}.
        :param usage_policy_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#usage_policy_id DatabaseInstance#usage_policy_id}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(parent_instance_ref, dict):
            parent_instance_ref = DatabaseInstanceParentInstanceRef(**parent_instance_ref)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__385217781715ae036d13b692f78f07152a4de27da49acbbabaa2c4480d57ad2e)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument capacity", value=capacity, expected_type=type_hints["capacity"])
            check_type(argname="argument custom_tags", value=custom_tags, expected_type=type_hints["custom_tags"])
            check_type(argname="argument enable_pg_native_login", value=enable_pg_native_login, expected_type=type_hints["enable_pg_native_login"])
            check_type(argname="argument enable_readable_secondaries", value=enable_readable_secondaries, expected_type=type_hints["enable_readable_secondaries"])
            check_type(argname="argument node_count", value=node_count, expected_type=type_hints["node_count"])
            check_type(argname="argument parent_instance_ref", value=parent_instance_ref, expected_type=type_hints["parent_instance_ref"])
            check_type(argname="argument purge_on_delete", value=purge_on_delete, expected_type=type_hints["purge_on_delete"])
            check_type(argname="argument retention_window_in_days", value=retention_window_in_days, expected_type=type_hints["retention_window_in_days"])
            check_type(argname="argument stopped", value=stopped, expected_type=type_hints["stopped"])
            check_type(argname="argument usage_policy_id", value=usage_policy_id, expected_type=type_hints["usage_policy_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
        }
        if connection is not None:
            self._values["connection"] = connection
        if count is not None:
            self._values["count"] = count
        if depends_on is not None:
            self._values["depends_on"] = depends_on
        if for_each is not None:
            self._values["for_each"] = for_each
        if lifecycle is not None:
            self._values["lifecycle"] = lifecycle
        if provider is not None:
            self._values["provider"] = provider
        if provisioners is not None:
            self._values["provisioners"] = provisioners
        if capacity is not None:
            self._values["capacity"] = capacity
        if custom_tags is not None:
            self._values["custom_tags"] = custom_tags
        if enable_pg_native_login is not None:
            self._values["enable_pg_native_login"] = enable_pg_native_login
        if enable_readable_secondaries is not None:
            self._values["enable_readable_secondaries"] = enable_readable_secondaries
        if node_count is not None:
            self._values["node_count"] = node_count
        if parent_instance_ref is not None:
            self._values["parent_instance_ref"] = parent_instance_ref
        if purge_on_delete is not None:
            self._values["purge_on_delete"] = purge_on_delete
        if retention_window_in_days is not None:
            self._values["retention_window_in_days"] = retention_window_in_days
        if stopped is not None:
            self._values["stopped"] = stopped
        if usage_policy_id is not None:
            self._values["usage_policy_id"] = usage_policy_id

    @builtins.property
    def connection(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("connection")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]], result)

    @builtins.property
    def count(
        self,
    ) -> typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("count")
        return typing.cast(typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]], result)

    @builtins.property
    def depends_on(
        self,
    ) -> typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("depends_on")
        return typing.cast(typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]], result)

    @builtins.property
    def for_each(self) -> typing.Optional[_cdktf_9a9027ec.ITerraformIterator]:
        '''
        :stability: experimental
        '''
        result = self._values.get("for_each")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.ITerraformIterator], result)

    @builtins.property
    def lifecycle(self) -> typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle]:
        '''
        :stability: experimental
        '''
        result = self._values.get("lifecycle")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle], result)

    @builtins.property
    def provider(self) -> typing.Optional[_cdktf_9a9027ec.TerraformProvider]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provider")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformProvider], result)

    @builtins.property
    def provisioners(
        self,
    ) -> typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provisioners")
        return typing.cast(typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]], result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#name DatabaseInstance#name}.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def capacity(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#capacity DatabaseInstance#capacity}.'''
        result = self._values.get("capacity")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def custom_tags(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DatabaseInstanceCustomTags"]]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#custom_tags DatabaseInstance#custom_tags}.'''
        result = self._values.get("custom_tags")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DatabaseInstanceCustomTags"]]], result)

    @builtins.property
    def enable_pg_native_login(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#enable_pg_native_login DatabaseInstance#enable_pg_native_login}.'''
        result = self._values.get("enable_pg_native_login")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def enable_readable_secondaries(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#enable_readable_secondaries DatabaseInstance#enable_readable_secondaries}.'''
        result = self._values.get("enable_readable_secondaries")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def node_count(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#node_count DatabaseInstance#node_count}.'''
        result = self._values.get("node_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def parent_instance_ref(
        self,
    ) -> typing.Optional["DatabaseInstanceParentInstanceRef"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#parent_instance_ref DatabaseInstance#parent_instance_ref}.'''
        result = self._values.get("parent_instance_ref")
        return typing.cast(typing.Optional["DatabaseInstanceParentInstanceRef"], result)

    @builtins.property
    def purge_on_delete(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#purge_on_delete DatabaseInstance#purge_on_delete}.'''
        result = self._values.get("purge_on_delete")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def retention_window_in_days(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#retention_window_in_days DatabaseInstance#retention_window_in_days}.'''
        result = self._values.get("retention_window_in_days")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def stopped(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#stopped DatabaseInstance#stopped}.'''
        result = self._values.get("stopped")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def usage_policy_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#usage_policy_id DatabaseInstance#usage_policy_id}.'''
        result = self._values.get("usage_policy_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DatabaseInstanceConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceCustomTags",
    jsii_struct_bases=[],
    name_mapping={"key": "key", "value": "value"},
)
class DatabaseInstanceCustomTags:
    def __init__(
        self,
        *,
        key: typing.Optional[builtins.str] = None,
        value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param key: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#key DatabaseInstance#key}.
        :param value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#value DatabaseInstance#value}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1bc0409a7e6a9240cf690a2fe85dc77de51b70cf8bb7f50e3e2280e0f2e9269b)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if key is not None:
            self._values["key"] = key
        if value is not None:
            self._values["value"] = value

    @builtins.property
    def key(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#key DatabaseInstance#key}.'''
        result = self._values.get("key")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def value(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#value DatabaseInstance#value}.'''
        result = self._values.get("value")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DatabaseInstanceCustomTags(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DatabaseInstanceCustomTagsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceCustomTagsList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__97f0eee52f4a31abc8c09c971628370767dcdd51a4018b851f9e47be972e2c83)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(self, index: jsii.Number) -> "DatabaseInstanceCustomTagsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__794e9567ec230ee6f046dddc39164f704e917e80eaa2ed756ca9d069e35458d9)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DatabaseInstanceCustomTagsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bf9d788c9973adcfda6f2718d86a3ea6ffbb0107c6f60928f33ff660cf164786)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d23eaa2effe789078081b238ff1490deadb40d92d6c31cb5172c90ed81faca2e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a76b664a10967eb5035da99cf5d1ae214784863c3479023e098a508a4077e73b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceCustomTags]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceCustomTags]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceCustomTags]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__948a577fcc8b949dfa54e92c59251dfb05e8895fb553cd6ade460da974ad26c6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DatabaseInstanceCustomTagsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceCustomTagsOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0c83515d723b092af0fb97c9268bdb1893a7af75475963377ab3d56fefc2f457)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetKey")
    def reset_key(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetKey", []))

    @jsii.member(jsii_name="resetValue")
    def reset_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetValue", []))

    @builtins.property
    @jsii.member(jsii_name="keyInput")
    def key_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "keyInput"))

    @builtins.property
    @jsii.member(jsii_name="valueInput")
    def value_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "valueInput"))

    @builtins.property
    @jsii.member(jsii_name="key")
    def key(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "key"))

    @key.setter
    def key(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__88c99fd942feb01bf7429756851104e9480c39df7ef3e9960b8514203b0762d2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "key", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="value")
    def value(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "value"))

    @value.setter
    def value(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3c089856369dc255b014c8b3350b4df4288a9ef817c44e2a3988116d71b51c4d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "value", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DatabaseInstanceCustomTags]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DatabaseInstanceCustomTags]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DatabaseInstanceCustomTags]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__56a8859c91be9bdb3e4fd4b3a06eedb5b9715f6db1b556d59708da3066d369ea)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceEffectiveCustomTags",
    jsii_struct_bases=[],
    name_mapping={"key": "key", "value": "value"},
)
class DatabaseInstanceEffectiveCustomTags:
    def __init__(
        self,
        *,
        key: typing.Optional[builtins.str] = None,
        value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param key: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#key DatabaseInstance#key}.
        :param value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#value DatabaseInstance#value}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e5e1bac5b9fc84091f6584e0921f54e9f7a6729cdb599d7b80feeff4e4493438)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if key is not None:
            self._values["key"] = key
        if value is not None:
            self._values["value"] = value

    @builtins.property
    def key(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#key DatabaseInstance#key}.'''
        result = self._values.get("key")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def value(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#value DatabaseInstance#value}.'''
        result = self._values.get("value")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DatabaseInstanceEffectiveCustomTags(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DatabaseInstanceEffectiveCustomTagsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceEffectiveCustomTagsList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__85cf8b0adb820939010f6f612183b538163ba4f87b506333da1a8d0cde78675a)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DatabaseInstanceEffectiveCustomTagsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2fe46d907f77089f004e7c388d608b7e2cab7433cf922a496a777a370b4ac732)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DatabaseInstanceEffectiveCustomTagsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6e37000a4583748d15954b4a1aac52286efc595c4fc188f2a018be3964f7aae1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1225c8e2c804adb6f3b3fd6688f455f2e5f78c40dec6fa709debbcb54023baf4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2c9762d4f557a0d01cb73e65fdd851f2e180e13f2dea62c4fb9167b79e8943bb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceEffectiveCustomTags]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceEffectiveCustomTags]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceEffectiveCustomTags]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__61d7640fb6e199f09b2a6013ad1aae842acc4fbf7b6e22d3265fd990a020aad6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DatabaseInstanceEffectiveCustomTagsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceEffectiveCustomTagsOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a41419e1ce6d7322487fda8eb7f702b6d7ef732d7477a4589df9165bc5b94645)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetKey")
    def reset_key(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetKey", []))

    @jsii.member(jsii_name="resetValue")
    def reset_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetValue", []))

    @builtins.property
    @jsii.member(jsii_name="keyInput")
    def key_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "keyInput"))

    @builtins.property
    @jsii.member(jsii_name="valueInput")
    def value_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "valueInput"))

    @builtins.property
    @jsii.member(jsii_name="key")
    def key(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "key"))

    @key.setter
    def key(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5526dd7cd9126a71bb069fdfcb2c27c288dbb58925060e15990d476f4a77e64d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "key", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="value")
    def value(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "value"))

    @value.setter
    def value(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0041667467af2000ffdc10cbf537af2b10276e2705d8b3acd55b4db5530a7ca8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "value", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DatabaseInstanceEffectiveCustomTags]:
        return typing.cast(typing.Optional[DatabaseInstanceEffectiveCustomTags], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DatabaseInstanceEffectiveCustomTags],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__af037ff7b5c593249f2466714f9c8522a8d7d2e883f9bf87b02b69d955bb0bce)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceParentInstanceRef",
    jsii_struct_bases=[],
    name_mapping={"branch_time": "branchTime", "lsn": "lsn", "name": "name"},
)
class DatabaseInstanceParentInstanceRef:
    def __init__(
        self,
        *,
        branch_time: typing.Optional[builtins.str] = None,
        lsn: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param branch_time: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#branch_time DatabaseInstance#branch_time}.
        :param lsn: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#lsn DatabaseInstance#lsn}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#name DatabaseInstance#name}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9bfa4aae268e29cfc8d94bc43218443c8e4202880a84e084d1321d5e423cdd4f)
            check_type(argname="argument branch_time", value=branch_time, expected_type=type_hints["branch_time"])
            check_type(argname="argument lsn", value=lsn, expected_type=type_hints["lsn"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if branch_time is not None:
            self._values["branch_time"] = branch_time
        if lsn is not None:
            self._values["lsn"] = lsn
        if name is not None:
            self._values["name"] = name

    @builtins.property
    def branch_time(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#branch_time DatabaseInstance#branch_time}.'''
        result = self._values.get("branch_time")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def lsn(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#lsn DatabaseInstance#lsn}.'''
        result = self._values.get("lsn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/database_instance#name DatabaseInstance#name}.'''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DatabaseInstanceParentInstanceRef(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DatabaseInstanceParentInstanceRefOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.databaseInstance.DatabaseInstanceParentInstanceRefOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d6c1d40b1e7a65f6864c10750a5378183d7e046daf36186f3a49cf95894f2cf8)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetBranchTime")
    def reset_branch_time(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBranchTime", []))

    @jsii.member(jsii_name="resetLsn")
    def reset_lsn(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLsn", []))

    @jsii.member(jsii_name="resetName")
    def reset_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetName", []))

    @builtins.property
    @jsii.member(jsii_name="effectiveLsn")
    def effective_lsn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "effectiveLsn"))

    @builtins.property
    @jsii.member(jsii_name="uid")
    def uid(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "uid"))

    @builtins.property
    @jsii.member(jsii_name="branchTimeInput")
    def branch_time_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "branchTimeInput"))

    @builtins.property
    @jsii.member(jsii_name="lsnInput")
    def lsn_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "lsnInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="branchTime")
    def branch_time(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "branchTime"))

    @branch_time.setter
    def branch_time(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dcc040c01a1d4cc43f0553c77c366dfa984a659be23b4ac7354a8250b2c67a03)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "branchTime", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="lsn")
    def lsn(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lsn"))

    @lsn.setter
    def lsn(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3e49e5a30df5211ea6437d2d3ddd1c308373719b7eeafbfc86b8652f067fe5e9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "lsn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0d8c1d6235cb1305d031b43925aaf062798eee385ef4ea081795360fa19cc7d6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DatabaseInstanceParentInstanceRef]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DatabaseInstanceParentInstanceRef]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DatabaseInstanceParentInstanceRef]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__87e4cab3f3b3f7966a3be7a53d688519df84feb993fe0e2087bbdf40a52c1399)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "DatabaseInstance",
    "DatabaseInstanceChildInstanceRefs",
    "DatabaseInstanceChildInstanceRefsList",
    "DatabaseInstanceChildInstanceRefsOutputReference",
    "DatabaseInstanceConfig",
    "DatabaseInstanceCustomTags",
    "DatabaseInstanceCustomTagsList",
    "DatabaseInstanceCustomTagsOutputReference",
    "DatabaseInstanceEffectiveCustomTags",
    "DatabaseInstanceEffectiveCustomTagsList",
    "DatabaseInstanceEffectiveCustomTagsOutputReference",
    "DatabaseInstanceParentInstanceRef",
    "DatabaseInstanceParentInstanceRefOutputReference",
]

publication.publish()

def _typecheckingstub__39f8ed0afe093cf72f4138d0a18915400567bcfb27ae1893c3ce48849a3b23cf(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    name: builtins.str,
    capacity: typing.Optional[builtins.str] = None,
    custom_tags: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DatabaseInstanceCustomTags, typing.Dict[builtins.str, typing.Any]]]]] = None,
    enable_pg_native_login: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    enable_readable_secondaries: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    node_count: typing.Optional[jsii.Number] = None,
    parent_instance_ref: typing.Optional[typing.Union[DatabaseInstanceParentInstanceRef, typing.Dict[builtins.str, typing.Any]]] = None,
    purge_on_delete: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    retention_window_in_days: typing.Optional[jsii.Number] = None,
    stopped: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    usage_policy_id: typing.Optional[builtins.str] = None,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2ffd3b682212a973b7a4797509a116336f9dd85373cf8f906ca4c95557c51950(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__28fbfdfea46a58c183ed59ca8169dde09ab12ccb8648f6ece0804f79f0cf0b8d(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DatabaseInstanceCustomTags, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fd15df291d7d47090118837041b521d1510e56c80e8559c134b3dd25466eec1c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3cb6e59fee7b184f79507e783e9f9b739338e6b7781e063f571240e1cab7613a(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d5c10073505ead9d82bffcf9ed1838833c2602b384472d5fa2e45972998ec61a(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bc2098c0ec477fa2b3fe25aee8ad56046056073c141997e5dcb33bb5a3456c9b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cc0f157bd2b4860f0fe0430c3345f7f49e9b1e6d6d996cdba142a74fe5781af8(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9b2206c2eaabddc33fa15b3c3ef371ee1c1bd42ae4d31c27e7ebb33822e76054(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__da6ba46d24a1715a60aa9b30de1d712d14970befe5930517ea21b3a0d08e8990(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9bfe9c3a30b6b573a5594f5c00fc04e8dc827f40dc2081639a5e915a09a9c529(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f60a31a8402c06968353c62250ee300c45fb2a293a1271c8a1634e0680b390f1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fae60ba8be61b16989b10dcb410bf644c71056dab9b58b1fd0d42e38d6eccae7(
    *,
    branch_time: typing.Optional[builtins.str] = None,
    lsn: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b19f27bdd66ce0681da8b64ea163ab9856a16a10a56733e23c1ef07771cda9be(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ebdaf35ef23a291adab4aefc97da2dcf7e34b51d5426eecad1200310be8012cf(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__60e2c4b595d6b7b5405b92334e029f4af109c7369c66bf0a607351ce98109e9a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9017074020736d940a9da4989f94da518df1e5d5e9d7a99742cc5e53aaddb9bf(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__57a75860f84df5e9475da63f37e4217235bb51dbec4ac3d5fb914a6cd53ca5cb(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c6371d550055e8b6acfbe231c316ff7b8c905dc570c63b82117c754339901724(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceChildInstanceRefs]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__24e1aa511d5bc6eb73eaf7ab7784ea0a128b5f22e6a14f5101605a8081c3f17c(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6cc9b750bb2a9224e60d6bd5efd9dfd6299517b694aa6b9ba4c469473672ed24(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c6c41e5bcafe6ae63b75f1fcd089bf8b704c615e0e4ba2684cbbad61271b7678(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5ec88ce26d14522272eb08efe49285569133df191804146985ae7d8f21725445(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a82b80cda1d19b848372e476d95a6ca0cda30da5e8d383419e63b9b77562e38d(
    value: typing.Optional[DatabaseInstanceChildInstanceRefs],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__385217781715ae036d13b692f78f07152a4de27da49acbbabaa2c4480d57ad2e(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    name: builtins.str,
    capacity: typing.Optional[builtins.str] = None,
    custom_tags: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DatabaseInstanceCustomTags, typing.Dict[builtins.str, typing.Any]]]]] = None,
    enable_pg_native_login: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    enable_readable_secondaries: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    node_count: typing.Optional[jsii.Number] = None,
    parent_instance_ref: typing.Optional[typing.Union[DatabaseInstanceParentInstanceRef, typing.Dict[builtins.str, typing.Any]]] = None,
    purge_on_delete: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    retention_window_in_days: typing.Optional[jsii.Number] = None,
    stopped: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    usage_policy_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1bc0409a7e6a9240cf690a2fe85dc77de51b70cf8bb7f50e3e2280e0f2e9269b(
    *,
    key: typing.Optional[builtins.str] = None,
    value: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__97f0eee52f4a31abc8c09c971628370767dcdd51a4018b851f9e47be972e2c83(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__794e9567ec230ee6f046dddc39164f704e917e80eaa2ed756ca9d069e35458d9(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bf9d788c9973adcfda6f2718d86a3ea6ffbb0107c6f60928f33ff660cf164786(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d23eaa2effe789078081b238ff1490deadb40d92d6c31cb5172c90ed81faca2e(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a76b664a10967eb5035da99cf5d1ae214784863c3479023e098a508a4077e73b(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__948a577fcc8b949dfa54e92c59251dfb05e8895fb553cd6ade460da974ad26c6(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceCustomTags]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0c83515d723b092af0fb97c9268bdb1893a7af75475963377ab3d56fefc2f457(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__88c99fd942feb01bf7429756851104e9480c39df7ef3e9960b8514203b0762d2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3c089856369dc255b014c8b3350b4df4288a9ef817c44e2a3988116d71b51c4d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__56a8859c91be9bdb3e4fd4b3a06eedb5b9715f6db1b556d59708da3066d369ea(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DatabaseInstanceCustomTags]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e5e1bac5b9fc84091f6584e0921f54e9f7a6729cdb599d7b80feeff4e4493438(
    *,
    key: typing.Optional[builtins.str] = None,
    value: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__85cf8b0adb820939010f6f612183b538163ba4f87b506333da1a8d0cde78675a(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2fe46d907f77089f004e7c388d608b7e2cab7433cf922a496a777a370b4ac732(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6e37000a4583748d15954b4a1aac52286efc595c4fc188f2a018be3964f7aae1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1225c8e2c804adb6f3b3fd6688f455f2e5f78c40dec6fa709debbcb54023baf4(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2c9762d4f557a0d01cb73e65fdd851f2e180e13f2dea62c4fb9167b79e8943bb(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__61d7640fb6e199f09b2a6013ad1aae842acc4fbf7b6e22d3265fd990a020aad6(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DatabaseInstanceEffectiveCustomTags]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a41419e1ce6d7322487fda8eb7f702b6d7ef732d7477a4589df9165bc5b94645(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5526dd7cd9126a71bb069fdfcb2c27c288dbb58925060e15990d476f4a77e64d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0041667467af2000ffdc10cbf537af2b10276e2705d8b3acd55b4db5530a7ca8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__af037ff7b5c593249f2466714f9c8522a8d7d2e883f9bf87b02b69d955bb0bce(
    value: typing.Optional[DatabaseInstanceEffectiveCustomTags],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9bfa4aae268e29cfc8d94bc43218443c8e4202880a84e084d1321d5e423cdd4f(
    *,
    branch_time: typing.Optional[builtins.str] = None,
    lsn: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d6c1d40b1e7a65f6864c10750a5378183d7e046daf36186f3a49cf95894f2cf8(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dcc040c01a1d4cc43f0553c77c366dfa984a659be23b4ac7354a8250b2c67a03(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3e49e5a30df5211ea6437d2d3ddd1c308373719b7eeafbfc86b8652f067fe5e9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0d8c1d6235cb1305d031b43925aaf062798eee385ef4ea081795360fa19cc7d6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__87e4cab3f3b3f7966a3be7a53d688519df84feb993fe0e2087bbdf40a52c1399(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DatabaseInstanceParentInstanceRef]],
) -> None:
    """Type checking stubs"""
    pass
