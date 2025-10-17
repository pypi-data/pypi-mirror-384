r'''
# `databricks_feature_engineering_feature`

Refer to the Terraform Registry for docs: [`databricks_feature_engineering_feature`](https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature).
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


class FeatureEngineeringFeature(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeature",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature databricks_feature_engineering_feature}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        full_name: builtins.str,
        function: typing.Union["FeatureEngineeringFeatureFunction", typing.Dict[builtins.str, typing.Any]],
        inputs: typing.Sequence[builtins.str],
        source: typing.Union["FeatureEngineeringFeatureSource", typing.Dict[builtins.str, typing.Any]],
        time_window: typing.Union["FeatureEngineeringFeatureTimeWindow", typing.Dict[builtins.str, typing.Any]],
        description: typing.Optional[builtins.str] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature databricks_feature_engineering_feature} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#full_name FeatureEngineeringFeature#full_name}.
        :param function: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#function FeatureEngineeringFeature#function}.
        :param inputs: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#inputs FeatureEngineeringFeature#inputs}.
        :param source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#source FeatureEngineeringFeature#source}.
        :param time_window: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#time_window FeatureEngineeringFeature#time_window}.
        :param description: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#description FeatureEngineeringFeature#description}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__606357cc75ccfd75eebb3bf0fa6e4437cf6f3ecabb465b78c5bc4ab049327141)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = FeatureEngineeringFeatureConfig(
            full_name=full_name,
            function=function,
            inputs=inputs,
            source=source,
            time_window=time_window,
            description=description,
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
        '''Generates CDKTF code for importing a FeatureEngineeringFeature resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the FeatureEngineeringFeature to import.
        :param import_from_id: The id of the existing FeatureEngineeringFeature that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the FeatureEngineeringFeature to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6b7c6a800663ced08ee15eddde6368656478da564ef38aea0d0f4e132323db7a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putFunction")
    def put_function(
        self,
        *,
        function_type: builtins.str,
        extra_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["FeatureEngineeringFeatureFunctionExtraParameters", typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''
        :param function_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#function_type FeatureEngineeringFeature#function_type}.
        :param extra_parameters: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#extra_parameters FeatureEngineeringFeature#extra_parameters}.
        '''
        value = FeatureEngineeringFeatureFunction(
            function_type=function_type, extra_parameters=extra_parameters
        )

        return typing.cast(None, jsii.invoke(self, "putFunction", [value]))

    @jsii.member(jsii_name="putSource")
    def put_source(
        self,
        *,
        delta_table_source: typing.Optional[typing.Union["FeatureEngineeringFeatureSourceDeltaTableSource", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param delta_table_source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#delta_table_source FeatureEngineeringFeature#delta_table_source}.
        '''
        value = FeatureEngineeringFeatureSource(delta_table_source=delta_table_source)

        return typing.cast(None, jsii.invoke(self, "putSource", [value]))

    @jsii.member(jsii_name="putTimeWindow")
    def put_time_window(
        self,
        *,
        duration: builtins.str,
        offset: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param duration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#duration FeatureEngineeringFeature#duration}.
        :param offset: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#offset FeatureEngineeringFeature#offset}.
        '''
        value = FeatureEngineeringFeatureTimeWindow(duration=duration, offset=offset)

        return typing.cast(None, jsii.invoke(self, "putTimeWindow", [value]))

    @jsii.member(jsii_name="resetDescription")
    def reset_description(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDescription", []))

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
    @jsii.member(jsii_name="function")
    def function(self) -> "FeatureEngineeringFeatureFunctionOutputReference":
        return typing.cast("FeatureEngineeringFeatureFunctionOutputReference", jsii.get(self, "function"))

    @builtins.property
    @jsii.member(jsii_name="source")
    def source(self) -> "FeatureEngineeringFeatureSourceOutputReference":
        return typing.cast("FeatureEngineeringFeatureSourceOutputReference", jsii.get(self, "source"))

    @builtins.property
    @jsii.member(jsii_name="timeWindow")
    def time_window(self) -> "FeatureEngineeringFeatureTimeWindowOutputReference":
        return typing.cast("FeatureEngineeringFeatureTimeWindowOutputReference", jsii.get(self, "timeWindow"))

    @builtins.property
    @jsii.member(jsii_name="descriptionInput")
    def description_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "descriptionInput"))

    @builtins.property
    @jsii.member(jsii_name="fullNameInput")
    def full_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "fullNameInput"))

    @builtins.property
    @jsii.member(jsii_name="functionInput")
    def function_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "FeatureEngineeringFeatureFunction"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "FeatureEngineeringFeatureFunction"]], jsii.get(self, "functionInput"))

    @builtins.property
    @jsii.member(jsii_name="inputsInput")
    def inputs_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "inputsInput"))

    @builtins.property
    @jsii.member(jsii_name="sourceInput")
    def source_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "FeatureEngineeringFeatureSource"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "FeatureEngineeringFeatureSource"]], jsii.get(self, "sourceInput"))

    @builtins.property
    @jsii.member(jsii_name="timeWindowInput")
    def time_window_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "FeatureEngineeringFeatureTimeWindow"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "FeatureEngineeringFeatureTimeWindow"]], jsii.get(self, "timeWindowInput"))

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "description"))

    @description.setter
    def description(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0a931852939a02022ff927a0b7ba4e1c36352599f3b399fb8f651fc02fb80e60)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "description", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="fullName")
    def full_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "fullName"))

    @full_name.setter
    def full_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ac3d27f83cf7dc70ca72ae8ed73f6b956b8a333e3236192a42bb544730f794c6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "fullName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="inputs")
    def inputs(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "inputs"))

    @inputs.setter
    def inputs(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3a8e4d1f01667c3edcc568fc748fe7828bbce4dbd20b6b5a22a9d5a517a66ec5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "inputs", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "full_name": "fullName",
        "function": "function",
        "inputs": "inputs",
        "source": "source",
        "time_window": "timeWindow",
        "description": "description",
    },
)
class FeatureEngineeringFeatureConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        full_name: builtins.str,
        function: typing.Union["FeatureEngineeringFeatureFunction", typing.Dict[builtins.str, typing.Any]],
        inputs: typing.Sequence[builtins.str],
        source: typing.Union["FeatureEngineeringFeatureSource", typing.Dict[builtins.str, typing.Any]],
        time_window: typing.Union["FeatureEngineeringFeatureTimeWindow", typing.Dict[builtins.str, typing.Any]],
        description: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#full_name FeatureEngineeringFeature#full_name}.
        :param function: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#function FeatureEngineeringFeature#function}.
        :param inputs: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#inputs FeatureEngineeringFeature#inputs}.
        :param source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#source FeatureEngineeringFeature#source}.
        :param time_window: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#time_window FeatureEngineeringFeature#time_window}.
        :param description: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#description FeatureEngineeringFeature#description}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(function, dict):
            function = FeatureEngineeringFeatureFunction(**function)
        if isinstance(source, dict):
            source = FeatureEngineeringFeatureSource(**source)
        if isinstance(time_window, dict):
            time_window = FeatureEngineeringFeatureTimeWindow(**time_window)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d56641dfeb32d319d9b95af5665dc6f6ad219f22dc0dbffaca0366d6ca31c103)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument full_name", value=full_name, expected_type=type_hints["full_name"])
            check_type(argname="argument function", value=function, expected_type=type_hints["function"])
            check_type(argname="argument inputs", value=inputs, expected_type=type_hints["inputs"])
            check_type(argname="argument source", value=source, expected_type=type_hints["source"])
            check_type(argname="argument time_window", value=time_window, expected_type=type_hints["time_window"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "full_name": full_name,
            "function": function,
            "inputs": inputs,
            "source": source,
            "time_window": time_window,
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
        if description is not None:
            self._values["description"] = description

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
    def full_name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#full_name FeatureEngineeringFeature#full_name}.'''
        result = self._values.get("full_name")
        assert result is not None, "Required property 'full_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def function(self) -> "FeatureEngineeringFeatureFunction":
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#function FeatureEngineeringFeature#function}.'''
        result = self._values.get("function")
        assert result is not None, "Required property 'function' is missing"
        return typing.cast("FeatureEngineeringFeatureFunction", result)

    @builtins.property
    def inputs(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#inputs FeatureEngineeringFeature#inputs}.'''
        result = self._values.get("inputs")
        assert result is not None, "Required property 'inputs' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def source(self) -> "FeatureEngineeringFeatureSource":
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#source FeatureEngineeringFeature#source}.'''
        result = self._values.get("source")
        assert result is not None, "Required property 'source' is missing"
        return typing.cast("FeatureEngineeringFeatureSource", result)

    @builtins.property
    def time_window(self) -> "FeatureEngineeringFeatureTimeWindow":
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#time_window FeatureEngineeringFeature#time_window}.'''
        result = self._values.get("time_window")
        assert result is not None, "Required property 'time_window' is missing"
        return typing.cast("FeatureEngineeringFeatureTimeWindow", result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#description FeatureEngineeringFeature#description}.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "FeatureEngineeringFeatureConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureFunction",
    jsii_struct_bases=[],
    name_mapping={
        "function_type": "functionType",
        "extra_parameters": "extraParameters",
    },
)
class FeatureEngineeringFeatureFunction:
    def __init__(
        self,
        *,
        function_type: builtins.str,
        extra_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["FeatureEngineeringFeatureFunctionExtraParameters", typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''
        :param function_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#function_type FeatureEngineeringFeature#function_type}.
        :param extra_parameters: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#extra_parameters FeatureEngineeringFeature#extra_parameters}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__45decf0b0e67eba248fffe99d1eb25d0c3d4dd0265f13f821948d5e9342602a0)
            check_type(argname="argument function_type", value=function_type, expected_type=type_hints["function_type"])
            check_type(argname="argument extra_parameters", value=extra_parameters, expected_type=type_hints["extra_parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "function_type": function_type,
        }
        if extra_parameters is not None:
            self._values["extra_parameters"] = extra_parameters

    @builtins.property
    def function_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#function_type FeatureEngineeringFeature#function_type}.'''
        result = self._values.get("function_type")
        assert result is not None, "Required property 'function_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def extra_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["FeatureEngineeringFeatureFunctionExtraParameters"]]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#extra_parameters FeatureEngineeringFeature#extra_parameters}.'''
        result = self._values.get("extra_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["FeatureEngineeringFeatureFunctionExtraParameters"]]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "FeatureEngineeringFeatureFunction(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureFunctionExtraParameters",
    jsii_struct_bases=[],
    name_mapping={"key": "key", "value": "value"},
)
class FeatureEngineeringFeatureFunctionExtraParameters:
    def __init__(self, *, key: builtins.str, value: builtins.str) -> None:
        '''
        :param key: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#key FeatureEngineeringFeature#key}.
        :param value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#value FeatureEngineeringFeature#value}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__49a1663612670861532c2507f1951a031322fecfcea9ea2be3304de8a64c8646)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "key": key,
            "value": value,
        }

    @builtins.property
    def key(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#key FeatureEngineeringFeature#key}.'''
        result = self._values.get("key")
        assert result is not None, "Required property 'key' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#value FeatureEngineeringFeature#value}.'''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "FeatureEngineeringFeatureFunctionExtraParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class FeatureEngineeringFeatureFunctionExtraParametersList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureFunctionExtraParametersList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__0246479c215c375141e38f376f974a9e0155fbd59adcf1ab59f83c9e5f69f25b)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "FeatureEngineeringFeatureFunctionExtraParametersOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2a287a4a896d700224a7cb97ecc976991b1eda84e77e151bfa963928c3855fa0)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("FeatureEngineeringFeatureFunctionExtraParametersOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40e4d60b0b67da994db9a7f337c65a6b57625aa079d315d76e3411718f6861bd)
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
            type_hints = typing.get_type_hints(_typecheckingstub__58f6bf39e1ab61dd1615f728fa720e82641f108241f07f26b23b9efa25d86d83)
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
            type_hints = typing.get_type_hints(_typecheckingstub__3eba3104a0018154ffab14dbb12a4cf2d0f4becb6a33ebeb5bc1e0ae2d90d936)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[FeatureEngineeringFeatureFunctionExtraParameters]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[FeatureEngineeringFeatureFunctionExtraParameters]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[FeatureEngineeringFeatureFunctionExtraParameters]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b348321ff3c2220652be3bd66207c65677e12f4b98bf043cc0ddd2259cb7403f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class FeatureEngineeringFeatureFunctionExtraParametersOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureFunctionExtraParametersOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__37d65395a8a3c361a2237e86b68096e0906d9b99a7a439bce18bebf53576744e)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

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
            type_hints = typing.get_type_hints(_typecheckingstub__8ae8236aebc4db4a0844256eef124534535751b51160b6e2ab4aa5e005a0ddd9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "key", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="value")
    def value(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "value"))

    @value.setter
    def value(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dee426c1cea32945e63642c9a4dc46242d9b2ab77320e3129b0c576ed93721dc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "value", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureFunctionExtraParameters]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureFunctionExtraParameters]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureFunctionExtraParameters]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d8f0b9fcd930f3412d401160455672a9c49e39ff1186943f6abbb46b5d20064a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class FeatureEngineeringFeatureFunctionOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureFunctionOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__70b1f4c2a6c49c9bca4267d9654dbf101fc465ced027c881999370a68aa1b8d7)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putExtraParameters")
    def put_extra_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[FeatureEngineeringFeatureFunctionExtraParameters, typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__909ff15d14093ac2945e256fc86c909b4bb57557bb876572c431b87db65c4f4c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putExtraParameters", [value]))

    @jsii.member(jsii_name="resetExtraParameters")
    def reset_extra_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExtraParameters", []))

    @builtins.property
    @jsii.member(jsii_name="extraParameters")
    def extra_parameters(self) -> FeatureEngineeringFeatureFunctionExtraParametersList:
        return typing.cast(FeatureEngineeringFeatureFunctionExtraParametersList, jsii.get(self, "extraParameters"))

    @builtins.property
    @jsii.member(jsii_name="extraParametersInput")
    def extra_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[FeatureEngineeringFeatureFunctionExtraParameters]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[FeatureEngineeringFeatureFunctionExtraParameters]]], jsii.get(self, "extraParametersInput"))

    @builtins.property
    @jsii.member(jsii_name="functionTypeInput")
    def function_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "functionTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="functionType")
    def function_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "functionType"))

    @function_type.setter
    def function_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da6407ca20474d8709842b50b5b75f173c4e817f1d492d7a234ee3cf9e4964ed)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "functionType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureFunction]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureFunction]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureFunction]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2771d693a70c8bf9e0e095d529762fa7691c2890467a57e3ef1a1ea8f9766599)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureSource",
    jsii_struct_bases=[],
    name_mapping={"delta_table_source": "deltaTableSource"},
)
class FeatureEngineeringFeatureSource:
    def __init__(
        self,
        *,
        delta_table_source: typing.Optional[typing.Union["FeatureEngineeringFeatureSourceDeltaTableSource", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param delta_table_source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#delta_table_source FeatureEngineeringFeature#delta_table_source}.
        '''
        if isinstance(delta_table_source, dict):
            delta_table_source = FeatureEngineeringFeatureSourceDeltaTableSource(**delta_table_source)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e0f871de001b309d51cac5465fbec8ceec22a4d057845933e22eb5ed4d41ee5b)
            check_type(argname="argument delta_table_source", value=delta_table_source, expected_type=type_hints["delta_table_source"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if delta_table_source is not None:
            self._values["delta_table_source"] = delta_table_source

    @builtins.property
    def delta_table_source(
        self,
    ) -> typing.Optional["FeatureEngineeringFeatureSourceDeltaTableSource"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#delta_table_source FeatureEngineeringFeature#delta_table_source}.'''
        result = self._values.get("delta_table_source")
        return typing.cast(typing.Optional["FeatureEngineeringFeatureSourceDeltaTableSource"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "FeatureEngineeringFeatureSource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureSourceDeltaTableSource",
    jsii_struct_bases=[],
    name_mapping={
        "entity_columns": "entityColumns",
        "full_name": "fullName",
        "timeseries_column": "timeseriesColumn",
    },
)
class FeatureEngineeringFeatureSourceDeltaTableSource:
    def __init__(
        self,
        *,
        entity_columns: typing.Sequence[builtins.str],
        full_name: builtins.str,
        timeseries_column: builtins.str,
    ) -> None:
        '''
        :param entity_columns: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#entity_columns FeatureEngineeringFeature#entity_columns}.
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#full_name FeatureEngineeringFeature#full_name}.
        :param timeseries_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#timeseries_column FeatureEngineeringFeature#timeseries_column}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0f80107797a636d301dcbf5f5c504eaa4f3b61d9be496d93c5e53dfb243740fe)
            check_type(argname="argument entity_columns", value=entity_columns, expected_type=type_hints["entity_columns"])
            check_type(argname="argument full_name", value=full_name, expected_type=type_hints["full_name"])
            check_type(argname="argument timeseries_column", value=timeseries_column, expected_type=type_hints["timeseries_column"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "entity_columns": entity_columns,
            "full_name": full_name,
            "timeseries_column": timeseries_column,
        }

    @builtins.property
    def entity_columns(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#entity_columns FeatureEngineeringFeature#entity_columns}.'''
        result = self._values.get("entity_columns")
        assert result is not None, "Required property 'entity_columns' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def full_name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#full_name FeatureEngineeringFeature#full_name}.'''
        result = self._values.get("full_name")
        assert result is not None, "Required property 'full_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def timeseries_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#timeseries_column FeatureEngineeringFeature#timeseries_column}.'''
        result = self._values.get("timeseries_column")
        assert result is not None, "Required property 'timeseries_column' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "FeatureEngineeringFeatureSourceDeltaTableSource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class FeatureEngineeringFeatureSourceDeltaTableSourceOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureSourceDeltaTableSourceOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__3972d15d356acf49651890e208ca53e9f789dab8869f76a061ccdce41aaa23ca)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="entityColumnsInput")
    def entity_columns_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "entityColumnsInput"))

    @builtins.property
    @jsii.member(jsii_name="fullNameInput")
    def full_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "fullNameInput"))

    @builtins.property
    @jsii.member(jsii_name="timeseriesColumnInput")
    def timeseries_column_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "timeseriesColumnInput"))

    @builtins.property
    @jsii.member(jsii_name="entityColumns")
    def entity_columns(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "entityColumns"))

    @entity_columns.setter
    def entity_columns(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__aaf9157dfd329364c2be718eaa7e97c13556282739c582c129bb0519d7c83b8d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "entityColumns", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="fullName")
    def full_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "fullName"))

    @full_name.setter
    def full_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3cafe0f0d4beef0d2dfdef975a5a6219d3b68245e353a00a20d6fc9c965cf64b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "fullName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timeseriesColumn")
    def timeseries_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timeseriesColumn"))

    @timeseries_column.setter
    def timeseries_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4b3f3b4981cadf791aa35800d929ba4c53e0939f8d8d8624e66d79eead3ca525)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timeseriesColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSourceDeltaTableSource]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSourceDeltaTableSource]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSourceDeltaTableSource]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4d4de1beef3146f947adb7d84e1bc1f7ba7804570e7c9d7548b4282f22ad2c20)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class FeatureEngineeringFeatureSourceOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureSourceOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__2121890cacfed1cf073bb0903bd186d29785fc944461783267ef357caa94f054)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putDeltaTableSource")
    def put_delta_table_source(
        self,
        *,
        entity_columns: typing.Sequence[builtins.str],
        full_name: builtins.str,
        timeseries_column: builtins.str,
    ) -> None:
        '''
        :param entity_columns: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#entity_columns FeatureEngineeringFeature#entity_columns}.
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#full_name FeatureEngineeringFeature#full_name}.
        :param timeseries_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#timeseries_column FeatureEngineeringFeature#timeseries_column}.
        '''
        value = FeatureEngineeringFeatureSourceDeltaTableSource(
            entity_columns=entity_columns,
            full_name=full_name,
            timeseries_column=timeseries_column,
        )

        return typing.cast(None, jsii.invoke(self, "putDeltaTableSource", [value]))

    @jsii.member(jsii_name="resetDeltaTableSource")
    def reset_delta_table_source(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDeltaTableSource", []))

    @builtins.property
    @jsii.member(jsii_name="deltaTableSource")
    def delta_table_source(
        self,
    ) -> FeatureEngineeringFeatureSourceDeltaTableSourceOutputReference:
        return typing.cast(FeatureEngineeringFeatureSourceDeltaTableSourceOutputReference, jsii.get(self, "deltaTableSource"))

    @builtins.property
    @jsii.member(jsii_name="deltaTableSourceInput")
    def delta_table_source_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSourceDeltaTableSource]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSourceDeltaTableSource]], jsii.get(self, "deltaTableSourceInput"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSource]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSource]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSource]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2e666b55181e593280c3c5921ba985971ba919851fea8f0f085abe63fc61fe94)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureTimeWindow",
    jsii_struct_bases=[],
    name_mapping={"duration": "duration", "offset": "offset"},
)
class FeatureEngineeringFeatureTimeWindow:
    def __init__(
        self,
        *,
        duration: builtins.str,
        offset: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param duration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#duration FeatureEngineeringFeature#duration}.
        :param offset: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#offset FeatureEngineeringFeature#offset}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__524bf6d77d072776a5198d66b6c0d3cbaa3eb2d004e68688f34156eca9456e87)
            check_type(argname="argument duration", value=duration, expected_type=type_hints["duration"])
            check_type(argname="argument offset", value=offset, expected_type=type_hints["offset"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "duration": duration,
        }
        if offset is not None:
            self._values["offset"] = offset

    @builtins.property
    def duration(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#duration FeatureEngineeringFeature#duration}.'''
        result = self._values.get("duration")
        assert result is not None, "Required property 'duration' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def offset(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/feature_engineering_feature#offset FeatureEngineeringFeature#offset}.'''
        result = self._values.get("offset")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "FeatureEngineeringFeatureTimeWindow(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class FeatureEngineeringFeatureTimeWindowOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.featureEngineeringFeature.FeatureEngineeringFeatureTimeWindowOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__8bd85c2b1c86bb55ee9a611ed926f6d3286a883735e3ac295606d592d3d765b5)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetOffset")
    def reset_offset(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOffset", []))

    @builtins.property
    @jsii.member(jsii_name="durationInput")
    def duration_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "durationInput"))

    @builtins.property
    @jsii.member(jsii_name="offsetInput")
    def offset_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "offsetInput"))

    @builtins.property
    @jsii.member(jsii_name="duration")
    def duration(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "duration"))

    @duration.setter
    def duration(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9db2df6d22379cd6065c5aa77025e0b640b3318a73346060c1b7826bec87d1c1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "duration", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="offset")
    def offset(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "offset"))

    @offset.setter
    def offset(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__db5cc1582479b0e52ae6d3c9d3d8087e941246458e06a81279bd52f6898fe2ad)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "offset", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureTimeWindow]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureTimeWindow]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureTimeWindow]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e6ba62ed702de3af3386efd4e028f16775d4a6d1f288ea07644cfde0f91bb589)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "FeatureEngineeringFeature",
    "FeatureEngineeringFeatureConfig",
    "FeatureEngineeringFeatureFunction",
    "FeatureEngineeringFeatureFunctionExtraParameters",
    "FeatureEngineeringFeatureFunctionExtraParametersList",
    "FeatureEngineeringFeatureFunctionExtraParametersOutputReference",
    "FeatureEngineeringFeatureFunctionOutputReference",
    "FeatureEngineeringFeatureSource",
    "FeatureEngineeringFeatureSourceDeltaTableSource",
    "FeatureEngineeringFeatureSourceDeltaTableSourceOutputReference",
    "FeatureEngineeringFeatureSourceOutputReference",
    "FeatureEngineeringFeatureTimeWindow",
    "FeatureEngineeringFeatureTimeWindowOutputReference",
]

publication.publish()

def _typecheckingstub__606357cc75ccfd75eebb3bf0fa6e4437cf6f3ecabb465b78c5bc4ab049327141(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    full_name: builtins.str,
    function: typing.Union[FeatureEngineeringFeatureFunction, typing.Dict[builtins.str, typing.Any]],
    inputs: typing.Sequence[builtins.str],
    source: typing.Union[FeatureEngineeringFeatureSource, typing.Dict[builtins.str, typing.Any]],
    time_window: typing.Union[FeatureEngineeringFeatureTimeWindow, typing.Dict[builtins.str, typing.Any]],
    description: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__6b7c6a800663ced08ee15eddde6368656478da564ef38aea0d0f4e132323db7a(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0a931852939a02022ff927a0b7ba4e1c36352599f3b399fb8f651fc02fb80e60(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ac3d27f83cf7dc70ca72ae8ed73f6b956b8a333e3236192a42bb544730f794c6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a8e4d1f01667c3edcc568fc748fe7828bbce4dbd20b6b5a22a9d5a517a66ec5(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d56641dfeb32d319d9b95af5665dc6f6ad219f22dc0dbffaca0366d6ca31c103(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    full_name: builtins.str,
    function: typing.Union[FeatureEngineeringFeatureFunction, typing.Dict[builtins.str, typing.Any]],
    inputs: typing.Sequence[builtins.str],
    source: typing.Union[FeatureEngineeringFeatureSource, typing.Dict[builtins.str, typing.Any]],
    time_window: typing.Union[FeatureEngineeringFeatureTimeWindow, typing.Dict[builtins.str, typing.Any]],
    description: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__45decf0b0e67eba248fffe99d1eb25d0c3d4dd0265f13f821948d5e9342602a0(
    *,
    function_type: builtins.str,
    extra_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[FeatureEngineeringFeatureFunctionExtraParameters, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__49a1663612670861532c2507f1951a031322fecfcea9ea2be3304de8a64c8646(
    *,
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0246479c215c375141e38f376f974a9e0155fbd59adcf1ab59f83c9e5f69f25b(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a287a4a896d700224a7cb97ecc976991b1eda84e77e151bfa963928c3855fa0(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40e4d60b0b67da994db9a7f337c65a6b57625aa079d315d76e3411718f6861bd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__58f6bf39e1ab61dd1615f728fa720e82641f108241f07f26b23b9efa25d86d83(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3eba3104a0018154ffab14dbb12a4cf2d0f4becb6a33ebeb5bc1e0ae2d90d936(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b348321ff3c2220652be3bd66207c65677e12f4b98bf043cc0ddd2259cb7403f(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[FeatureEngineeringFeatureFunctionExtraParameters]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__37d65395a8a3c361a2237e86b68096e0906d9b99a7a439bce18bebf53576744e(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8ae8236aebc4db4a0844256eef124534535751b51160b6e2ab4aa5e005a0ddd9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dee426c1cea32945e63642c9a4dc46242d9b2ab77320e3129b0c576ed93721dc(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d8f0b9fcd930f3412d401160455672a9c49e39ff1186943f6abbb46b5d20064a(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureFunctionExtraParameters]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__70b1f4c2a6c49c9bca4267d9654dbf101fc465ced027c881999370a68aa1b8d7(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__909ff15d14093ac2945e256fc86c909b4bb57557bb876572c431b87db65c4f4c(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[FeatureEngineeringFeatureFunctionExtraParameters, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__da6407ca20474d8709842b50b5b75f173c4e817f1d492d7a234ee3cf9e4964ed(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2771d693a70c8bf9e0e095d529762fa7691c2890467a57e3ef1a1ea8f9766599(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureFunction]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e0f871de001b309d51cac5465fbec8ceec22a4d057845933e22eb5ed4d41ee5b(
    *,
    delta_table_source: typing.Optional[typing.Union[FeatureEngineeringFeatureSourceDeltaTableSource, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0f80107797a636d301dcbf5f5c504eaa4f3b61d9be496d93c5e53dfb243740fe(
    *,
    entity_columns: typing.Sequence[builtins.str],
    full_name: builtins.str,
    timeseries_column: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3972d15d356acf49651890e208ca53e9f789dab8869f76a061ccdce41aaa23ca(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aaf9157dfd329364c2be718eaa7e97c13556282739c582c129bb0519d7c83b8d(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3cafe0f0d4beef0d2dfdef975a5a6219d3b68245e353a00a20d6fc9c965cf64b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4b3f3b4981cadf791aa35800d929ba4c53e0939f8d8d8624e66d79eead3ca525(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4d4de1beef3146f947adb7d84e1bc1f7ba7804570e7c9d7548b4282f22ad2c20(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSourceDeltaTableSource]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2121890cacfed1cf073bb0903bd186d29785fc944461783267ef357caa94f054(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2e666b55181e593280c3c5921ba985971ba919851fea8f0f085abe63fc61fe94(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureSource]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__524bf6d77d072776a5198d66b6c0d3cbaa3eb2d004e68688f34156eca9456e87(
    *,
    duration: builtins.str,
    offset: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8bd85c2b1c86bb55ee9a611ed926f6d3286a883735e3ac295606d592d3d765b5(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9db2df6d22379cd6065c5aa77025e0b640b3318a73346060c1b7826bec87d1c1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__db5cc1582479b0e52ae6d3c9d3d8087e941246458e06a81279bd52f6898fe2ad(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e6ba62ed702de3af3386efd4e028f16775d4a6d1f288ea07644cfde0f91bb589(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, FeatureEngineeringFeatureTimeWindow]],
) -> None:
    """Type checking stubs"""
    pass
