r'''
# `data_databricks_rfa_access_request_destinations`

Refer to the Terraform Registry for docs: [`data_databricks_rfa_access_request_destinations`](https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations).
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


class DataDatabricksRfaAccessRequestDestinations(
    _cdktf_9a9027ec.TerraformDataSource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksRfaAccessRequestDestinations.DataDatabricksRfaAccessRequestDestinations",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations databricks_rfa_access_request_destinations}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        destinations: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataDatabricksRfaAccessRequestDestinationsDestinations", typing.Dict[builtins.str, typing.Any]]]],
        securable: typing.Union["DataDatabricksRfaAccessRequestDestinationsSecurable", typing.Dict[builtins.str, typing.Any]],
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations databricks_rfa_access_request_destinations} Data Source.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param destinations: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#destinations DataDatabricksRfaAccessRequestDestinations#destinations}.
        :param securable: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#securable DataDatabricksRfaAccessRequestDestinations#securable}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d634f3395ea7057e0e9e7b239a15588cc507ef5a9cc738307351627289ac1b3e)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = DataDatabricksRfaAccessRequestDestinationsConfig(
            destinations=destinations,
            securable=securable,
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
        '''Generates CDKTF code for importing a DataDatabricksRfaAccessRequestDestinations resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DataDatabricksRfaAccessRequestDestinations to import.
        :param import_from_id: The id of the existing DataDatabricksRfaAccessRequestDestinations that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DataDatabricksRfaAccessRequestDestinations to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ed951b7e4f54751a99d3a4058ac9f2cf5d27e6b7370a05b92710f0821c11b312)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putDestinations")
    def put_destinations(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataDatabricksRfaAccessRequestDestinationsDestinations", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e661e580ed2e515e053d252c15d216d0649d5dea0af7fb0889c2164440194ab8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putDestinations", [value]))

    @jsii.member(jsii_name="putSecurable")
    def put_securable(
        self,
        *,
        full_name: typing.Optional[builtins.str] = None,
        provider_share: typing.Optional[builtins.str] = None,
        type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#full_name DataDatabricksRfaAccessRequestDestinations#full_name}.
        :param provider_share: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#provider_share DataDatabricksRfaAccessRequestDestinations#provider_share}.
        :param type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#type DataDatabricksRfaAccessRequestDestinations#type}.
        '''
        value = DataDatabricksRfaAccessRequestDestinationsSecurable(
            full_name=full_name, provider_share=provider_share, type=type
        )

        return typing.cast(None, jsii.invoke(self, "putSecurable", [value]))

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
    @jsii.member(jsii_name="areAnyDestinationsHidden")
    def are_any_destinations_hidden(self) -> _cdktf_9a9027ec.IResolvable:
        return typing.cast(_cdktf_9a9027ec.IResolvable, jsii.get(self, "areAnyDestinationsHidden"))

    @builtins.property
    @jsii.member(jsii_name="destinations")
    def destinations(
        self,
    ) -> "DataDatabricksRfaAccessRequestDestinationsDestinationsList":
        return typing.cast("DataDatabricksRfaAccessRequestDestinationsDestinationsList", jsii.get(self, "destinations"))

    @builtins.property
    @jsii.member(jsii_name="securable")
    def securable(
        self,
    ) -> "DataDatabricksRfaAccessRequestDestinationsSecurableOutputReference":
        return typing.cast("DataDatabricksRfaAccessRequestDestinationsSecurableOutputReference", jsii.get(self, "securable"))

    @builtins.property
    @jsii.member(jsii_name="destinationsInput")
    def destinations_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksRfaAccessRequestDestinationsDestinations"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksRfaAccessRequestDestinationsDestinations"]]], jsii.get(self, "destinationsInput"))

    @builtins.property
    @jsii.member(jsii_name="securableInput")
    def securable_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksRfaAccessRequestDestinationsSecurable"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksRfaAccessRequestDestinationsSecurable"]], jsii.get(self, "securableInput"))


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksRfaAccessRequestDestinations.DataDatabricksRfaAccessRequestDestinationsConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "destinations": "destinations",
        "securable": "securable",
    },
)
class DataDatabricksRfaAccessRequestDestinationsConfig(
    _cdktf_9a9027ec.TerraformMetaArguments,
):
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
        destinations: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataDatabricksRfaAccessRequestDestinationsDestinations", typing.Dict[builtins.str, typing.Any]]]],
        securable: typing.Union["DataDatabricksRfaAccessRequestDestinationsSecurable", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param destinations: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#destinations DataDatabricksRfaAccessRequestDestinations#destinations}.
        :param securable: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#securable DataDatabricksRfaAccessRequestDestinations#securable}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(securable, dict):
            securable = DataDatabricksRfaAccessRequestDestinationsSecurable(**securable)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5df673a8cfe74c3ed5913a847e30e023f29089e37f91ac5993da7aa438163f01)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument destinations", value=destinations, expected_type=type_hints["destinations"])
            check_type(argname="argument securable", value=securable, expected_type=type_hints["securable"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "destinations": destinations,
            "securable": securable,
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
    def destinations(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksRfaAccessRequestDestinationsDestinations"]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#destinations DataDatabricksRfaAccessRequestDestinations#destinations}.'''
        result = self._values.get("destinations")
        assert result is not None, "Required property 'destinations' is missing"
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksRfaAccessRequestDestinationsDestinations"]], result)

    @builtins.property
    def securable(self) -> "DataDatabricksRfaAccessRequestDestinationsSecurable":
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#securable DataDatabricksRfaAccessRequestDestinations#securable}.'''
        result = self._values.get("securable")
        assert result is not None, "Required property 'securable' is missing"
        return typing.cast("DataDatabricksRfaAccessRequestDestinationsSecurable", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksRfaAccessRequestDestinationsConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksRfaAccessRequestDestinations.DataDatabricksRfaAccessRequestDestinationsDestinations",
    jsii_struct_bases=[],
    name_mapping={
        "destination_id": "destinationId",
        "destination_type": "destinationType",
        "special_destination": "specialDestination",
    },
)
class DataDatabricksRfaAccessRequestDestinationsDestinations:
    def __init__(
        self,
        *,
        destination_id: typing.Optional[builtins.str] = None,
        destination_type: typing.Optional[builtins.str] = None,
        special_destination: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param destination_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#destination_id DataDatabricksRfaAccessRequestDestinations#destination_id}.
        :param destination_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#destination_type DataDatabricksRfaAccessRequestDestinations#destination_type}.
        :param special_destination: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#special_destination DataDatabricksRfaAccessRequestDestinations#special_destination}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__18f547fa22cb2fbdee3196f0d8cd3ea3c0a72662eff3cbdc3c986e85aceae6bd)
            check_type(argname="argument destination_id", value=destination_id, expected_type=type_hints["destination_id"])
            check_type(argname="argument destination_type", value=destination_type, expected_type=type_hints["destination_type"])
            check_type(argname="argument special_destination", value=special_destination, expected_type=type_hints["special_destination"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if destination_id is not None:
            self._values["destination_id"] = destination_id
        if destination_type is not None:
            self._values["destination_type"] = destination_type
        if special_destination is not None:
            self._values["special_destination"] = special_destination

    @builtins.property
    def destination_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#destination_id DataDatabricksRfaAccessRequestDestinations#destination_id}.'''
        result = self._values.get("destination_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def destination_type(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#destination_type DataDatabricksRfaAccessRequestDestinations#destination_type}.'''
        result = self._values.get("destination_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def special_destination(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#special_destination DataDatabricksRfaAccessRequestDestinations#special_destination}.'''
        result = self._values.get("special_destination")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksRfaAccessRequestDestinationsDestinations(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksRfaAccessRequestDestinationsDestinationsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksRfaAccessRequestDestinations.DataDatabricksRfaAccessRequestDestinationsDestinationsList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__d0190a5edeee488d7ddb6a5e7535c2da76948722923e0ecd6c0cdc0b1fe1e715)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DataDatabricksRfaAccessRequestDestinationsDestinationsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__175cc0dae56813058e3b372ca60b43b365966c0c68bebf3c72b56847d7a61a95)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DataDatabricksRfaAccessRequestDestinationsDestinationsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e6c40afc9e5d24f8ba5f7ce2ff275dc5c10ec17c23b7b1a67ca9b3134a201741)
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
            type_hints = typing.get_type_hints(_typecheckingstub__d0822828ebf54c801d903a35abb71ee1fad00f8ce60348866d8b1858e9a75175)
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
            type_hints = typing.get_type_hints(_typecheckingstub__2a8b662a51775717a345d8db6fc091bf263caab1e6d5a59687fe069ce69a2e9f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksRfaAccessRequestDestinationsDestinations]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksRfaAccessRequestDestinationsDestinations]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksRfaAccessRequestDestinationsDestinations]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__302977e4d96161a0af53f28478e8c5ecf4a866fd580870e29e9adf9caa6e9929)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksRfaAccessRequestDestinationsDestinationsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksRfaAccessRequestDestinations.DataDatabricksRfaAccessRequestDestinationsDestinationsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__31f0ac13da502ebc63f1884eb452d193824c8dc368f585769d9a016abada94f2)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetDestinationId")
    def reset_destination_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDestinationId", []))

    @jsii.member(jsii_name="resetDestinationType")
    def reset_destination_type(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDestinationType", []))

    @jsii.member(jsii_name="resetSpecialDestination")
    def reset_special_destination(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSpecialDestination", []))

    @builtins.property
    @jsii.member(jsii_name="destinationIdInput")
    def destination_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "destinationIdInput"))

    @builtins.property
    @jsii.member(jsii_name="destinationTypeInput")
    def destination_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "destinationTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="specialDestinationInput")
    def special_destination_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "specialDestinationInput"))

    @builtins.property
    @jsii.member(jsii_name="destinationId")
    def destination_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "destinationId"))

    @destination_id.setter
    def destination_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f0dbdada7d96b3145f9ab903f3a09b817c1bc7f19bd8394efb6c4be1b3e970c9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "destinationId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="destinationType")
    def destination_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "destinationType"))

    @destination_type.setter
    def destination_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f953681d6e64b9e3d0e3476f61c8e7b32968754111be89d54b4138f8a981874d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "destinationType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="specialDestination")
    def special_destination(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "specialDestination"))

    @special_destination.setter
    def special_destination(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ff945fe24136facd91c1d33bfd3f00edacbbecd56294c90d1843a557bd09912f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "specialDestination", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksRfaAccessRequestDestinationsDestinations]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksRfaAccessRequestDestinationsDestinations]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksRfaAccessRequestDestinationsDestinations]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__974faf4360545e437f141af62cbbd7435c233361d6f269f0f49d87e281f48379)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksRfaAccessRequestDestinations.DataDatabricksRfaAccessRequestDestinationsSecurable",
    jsii_struct_bases=[],
    name_mapping={
        "full_name": "fullName",
        "provider_share": "providerShare",
        "type": "type",
    },
)
class DataDatabricksRfaAccessRequestDestinationsSecurable:
    def __init__(
        self,
        *,
        full_name: typing.Optional[builtins.str] = None,
        provider_share: typing.Optional[builtins.str] = None,
        type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#full_name DataDatabricksRfaAccessRequestDestinations#full_name}.
        :param provider_share: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#provider_share DataDatabricksRfaAccessRequestDestinations#provider_share}.
        :param type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#type DataDatabricksRfaAccessRequestDestinations#type}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__00497a2549195e2352556af55740675931600f7a2fd48e86d2b7319076a9bf8b)
            check_type(argname="argument full_name", value=full_name, expected_type=type_hints["full_name"])
            check_type(argname="argument provider_share", value=provider_share, expected_type=type_hints["provider_share"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if full_name is not None:
            self._values["full_name"] = full_name
        if provider_share is not None:
            self._values["provider_share"] = provider_share
        if type is not None:
            self._values["type"] = type

    @builtins.property
    def full_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#full_name DataDatabricksRfaAccessRequestDestinations#full_name}.'''
        result = self._values.get("full_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def provider_share(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#provider_share DataDatabricksRfaAccessRequestDestinations#provider_share}.'''
        result = self._values.get("provider_share")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def type(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/rfa_access_request_destinations#type DataDatabricksRfaAccessRequestDestinations#type}.'''
        result = self._values.get("type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksRfaAccessRequestDestinationsSecurable(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksRfaAccessRequestDestinationsSecurableOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksRfaAccessRequestDestinations.DataDatabricksRfaAccessRequestDestinationsSecurableOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__aa83cf948e6f84bf1f479a89ba27f5aaccb8610b601055274a98d08cc8fdc713)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetFullName")
    def reset_full_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetFullName", []))

    @jsii.member(jsii_name="resetProviderShare")
    def reset_provider_share(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetProviderShare", []))

    @jsii.member(jsii_name="resetType")
    def reset_type(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetType", []))

    @builtins.property
    @jsii.member(jsii_name="fullNameInput")
    def full_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "fullNameInput"))

    @builtins.property
    @jsii.member(jsii_name="providerShareInput")
    def provider_share_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "providerShareInput"))

    @builtins.property
    @jsii.member(jsii_name="typeInput")
    def type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "typeInput"))

    @builtins.property
    @jsii.member(jsii_name="fullName")
    def full_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "fullName"))

    @full_name.setter
    def full_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e165a477963543bd2e9c48b5752dd8c0a35bb4f32a3c1f3f4310ad65330accf1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "fullName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="providerShare")
    def provider_share(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "providerShare"))

    @provider_share.setter
    def provider_share(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__82bebaf2ad286bfcd9916861314564fc163b4ac24021e7b19ebc1f7f55d50d51)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "providerShare", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__56ed5124115b0b8310046c789e0776c32b2ef3b734a206c11fa928f094c938fc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksRfaAccessRequestDestinationsSecurable]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksRfaAccessRequestDestinationsSecurable]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksRfaAccessRequestDestinationsSecurable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26457abfecf1c58f1f156102f101b691939b2467a6d8fc1e1a2aef22ff99a2e8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "DataDatabricksRfaAccessRequestDestinations",
    "DataDatabricksRfaAccessRequestDestinationsConfig",
    "DataDatabricksRfaAccessRequestDestinationsDestinations",
    "DataDatabricksRfaAccessRequestDestinationsDestinationsList",
    "DataDatabricksRfaAccessRequestDestinationsDestinationsOutputReference",
    "DataDatabricksRfaAccessRequestDestinationsSecurable",
    "DataDatabricksRfaAccessRequestDestinationsSecurableOutputReference",
]

publication.publish()

def _typecheckingstub__d634f3395ea7057e0e9e7b239a15588cc507ef5a9cc738307351627289ac1b3e(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    destinations: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksRfaAccessRequestDestinationsDestinations, typing.Dict[builtins.str, typing.Any]]]],
    securable: typing.Union[DataDatabricksRfaAccessRequestDestinationsSecurable, typing.Dict[builtins.str, typing.Any]],
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

def _typecheckingstub__ed951b7e4f54751a99d3a4058ac9f2cf5d27e6b7370a05b92710f0821c11b312(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e661e580ed2e515e053d252c15d216d0649d5dea0af7fb0889c2164440194ab8(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksRfaAccessRequestDestinationsDestinations, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5df673a8cfe74c3ed5913a847e30e023f29089e37f91ac5993da7aa438163f01(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    destinations: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksRfaAccessRequestDestinationsDestinations, typing.Dict[builtins.str, typing.Any]]]],
    securable: typing.Union[DataDatabricksRfaAccessRequestDestinationsSecurable, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__18f547fa22cb2fbdee3196f0d8cd3ea3c0a72662eff3cbdc3c986e85aceae6bd(
    *,
    destination_id: typing.Optional[builtins.str] = None,
    destination_type: typing.Optional[builtins.str] = None,
    special_destination: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d0190a5edeee488d7ddb6a5e7535c2da76948722923e0ecd6c0cdc0b1fe1e715(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__175cc0dae56813058e3b372ca60b43b365966c0c68bebf3c72b56847d7a61a95(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e6c40afc9e5d24f8ba5f7ce2ff275dc5c10ec17c23b7b1a67ca9b3134a201741(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d0822828ebf54c801d903a35abb71ee1fad00f8ce60348866d8b1858e9a75175(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a8b662a51775717a345d8db6fc091bf263caab1e6d5a59687fe069ce69a2e9f(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__302977e4d96161a0af53f28478e8c5ecf4a866fd580870e29e9adf9caa6e9929(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksRfaAccessRequestDestinationsDestinations]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__31f0ac13da502ebc63f1884eb452d193824c8dc368f585769d9a016abada94f2(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f0dbdada7d96b3145f9ab903f3a09b817c1bc7f19bd8394efb6c4be1b3e970c9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f953681d6e64b9e3d0e3476f61c8e7b32968754111be89d54b4138f8a981874d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ff945fe24136facd91c1d33bfd3f00edacbbecd56294c90d1843a557bd09912f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__974faf4360545e437f141af62cbbd7435c233361d6f269f0f49d87e281f48379(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksRfaAccessRequestDestinationsDestinations]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__00497a2549195e2352556af55740675931600f7a2fd48e86d2b7319076a9bf8b(
    *,
    full_name: typing.Optional[builtins.str] = None,
    provider_share: typing.Optional[builtins.str] = None,
    type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aa83cf948e6f84bf1f479a89ba27f5aaccb8610b601055274a98d08cc8fdc713(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e165a477963543bd2e9c48b5752dd8c0a35bb4f32a3c1f3f4310ad65330accf1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__82bebaf2ad286bfcd9916861314564fc163b4ac24021e7b19ebc1f7f55d50d51(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__56ed5124115b0b8310046c789e0776c32b2ef3b734a206c11fa928f094c938fc(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26457abfecf1c58f1f156102f101b691939b2467a6d8fc1e1a2aef22ff99a2e8(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksRfaAccessRequestDestinationsSecurable]],
) -> None:
    """Type checking stubs"""
    pass
