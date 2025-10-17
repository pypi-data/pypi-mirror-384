r'''
# `data_databricks_feature_engineering_features`

Refer to the Terraform Registry for docs: [`data_databricks_feature_engineering_features`](https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features).
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


class DataDatabricksFeatureEngineeringFeatures(
    _cdktf_9a9027ec.TerraformDataSource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeatures",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features databricks_feature_engineering_features}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features databricks_feature_engineering_features} Data Source.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2131055a7c36ca9dd5d07c418b7ad65afb4b1c7354e7a641ef69e7b910ead1bd)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = DataDatabricksFeatureEngineeringFeaturesConfig(
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
        '''Generates CDKTF code for importing a DataDatabricksFeatureEngineeringFeatures resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DataDatabricksFeatureEngineeringFeatures to import.
        :param import_from_id: The id of the existing DataDatabricksFeatureEngineeringFeatures that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DataDatabricksFeatureEngineeringFeatures to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eb488d6215f2208ed5b43fb48c271f5d8e894034856069f3e69bedc01e931ee9)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

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
    @jsii.member(jsii_name="features")
    def features(self) -> "DataDatabricksFeatureEngineeringFeaturesFeaturesList":
        return typing.cast("DataDatabricksFeatureEngineeringFeaturesFeaturesList", jsii.get(self, "features"))


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
    },
)
class DataDatabricksFeatureEngineeringFeaturesConfig(
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
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c2deeaf867f0acddef6db27728ff7bf2a62304d1850fb031c14312135d45f7cc)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
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

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksFeatureEngineeringFeaturesConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeatures",
    jsii_struct_bases=[],
    name_mapping={
        "full_name": "fullName",
        "function": "function",
        "inputs": "inputs",
        "source": "source",
        "time_window": "timeWindow",
        "description": "description",
    },
)
class DataDatabricksFeatureEngineeringFeaturesFeatures:
    def __init__(
        self,
        *,
        full_name: builtins.str,
        function: typing.Union["DataDatabricksFeatureEngineeringFeaturesFeaturesFunction", typing.Dict[builtins.str, typing.Any]],
        inputs: typing.Sequence[builtins.str],
        source: typing.Union["DataDatabricksFeatureEngineeringFeaturesFeaturesSource", typing.Dict[builtins.str, typing.Any]],
        time_window: typing.Union["DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow", typing.Dict[builtins.str, typing.Any]],
        description: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#full_name DataDatabricksFeatureEngineeringFeatures#full_name}.
        :param function: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#function DataDatabricksFeatureEngineeringFeatures#function}.
        :param inputs: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#inputs DataDatabricksFeatureEngineeringFeatures#inputs}.
        :param source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#source DataDatabricksFeatureEngineeringFeatures#source}.
        :param time_window: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#time_window DataDatabricksFeatureEngineeringFeatures#time_window}.
        :param description: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#description DataDatabricksFeatureEngineeringFeatures#description}.
        '''
        if isinstance(function, dict):
            function = DataDatabricksFeatureEngineeringFeaturesFeaturesFunction(**function)
        if isinstance(source, dict):
            source = DataDatabricksFeatureEngineeringFeaturesFeaturesSource(**source)
        if isinstance(time_window, dict):
            time_window = DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow(**time_window)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b6f32fce82528c8e35f7c83b48d2b4b154b05496dc551583f9a850d0ee658096)
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
        if description is not None:
            self._values["description"] = description

    @builtins.property
    def full_name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#full_name DataDatabricksFeatureEngineeringFeatures#full_name}.'''
        result = self._values.get("full_name")
        assert result is not None, "Required property 'full_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def function(self) -> "DataDatabricksFeatureEngineeringFeaturesFeaturesFunction":
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#function DataDatabricksFeatureEngineeringFeatures#function}.'''
        result = self._values.get("function")
        assert result is not None, "Required property 'function' is missing"
        return typing.cast("DataDatabricksFeatureEngineeringFeaturesFeaturesFunction", result)

    @builtins.property
    def inputs(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#inputs DataDatabricksFeatureEngineeringFeatures#inputs}.'''
        result = self._values.get("inputs")
        assert result is not None, "Required property 'inputs' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def source(self) -> "DataDatabricksFeatureEngineeringFeaturesFeaturesSource":
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#source DataDatabricksFeatureEngineeringFeatures#source}.'''
        result = self._values.get("source")
        assert result is not None, "Required property 'source' is missing"
        return typing.cast("DataDatabricksFeatureEngineeringFeaturesFeaturesSource", result)

    @builtins.property
    def time_window(
        self,
    ) -> "DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow":
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#time_window DataDatabricksFeatureEngineeringFeatures#time_window}.'''
        result = self._values.get("time_window")
        assert result is not None, "Required property 'time_window' is missing"
        return typing.cast("DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow", result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#description DataDatabricksFeatureEngineeringFeatures#description}.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksFeatureEngineeringFeaturesFeatures(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesFunction",
    jsii_struct_bases=[],
    name_mapping={
        "function_type": "functionType",
        "extra_parameters": "extraParameters",
    },
)
class DataDatabricksFeatureEngineeringFeaturesFeaturesFunction:
    def __init__(
        self,
        *,
        function_type: builtins.str,
        extra_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters", typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''
        :param function_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#function_type DataDatabricksFeatureEngineeringFeatures#function_type}.
        :param extra_parameters: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#extra_parameters DataDatabricksFeatureEngineeringFeatures#extra_parameters}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c38772e28f9407030cc0bd3b54b5d488bd43323b73f9e86322aff3076bd7ffc4)
            check_type(argname="argument function_type", value=function_type, expected_type=type_hints["function_type"])
            check_type(argname="argument extra_parameters", value=extra_parameters, expected_type=type_hints["extra_parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "function_type": function_type,
        }
        if extra_parameters is not None:
            self._values["extra_parameters"] = extra_parameters

    @builtins.property
    def function_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#function_type DataDatabricksFeatureEngineeringFeatures#function_type}.'''
        result = self._values.get("function_type")
        assert result is not None, "Required property 'function_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def extra_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters"]]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#extra_parameters DataDatabricksFeatureEngineeringFeatures#extra_parameters}.'''
        result = self._values.get("extra_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters"]]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksFeatureEngineeringFeaturesFeaturesFunction(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters",
    jsii_struct_bases=[],
    name_mapping={"key": "key", "value": "value"},
)
class DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters:
    def __init__(self, *, key: builtins.str, value: builtins.str) -> None:
        '''
        :param key: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#key DataDatabricksFeatureEngineeringFeatures#key}.
        :param value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#value DataDatabricksFeatureEngineeringFeatures#value}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9481da63ceba4272ce7813904a303dd9c5239ed74c370bca246fd1ee4ce0bf47)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "key": key,
            "value": value,
        }

    @builtins.property
    def key(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#key DataDatabricksFeatureEngineeringFeatures#key}.'''
        result = self._values.get("key")
        assert result is not None, "Required property 'key' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#value DataDatabricksFeatureEngineeringFeatures#value}.'''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__eed8da7cfa6b86f566b7ee727af8bb33ebb3da86ed835339ba1314657d5d9423)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8dfe801c2b650e2aeb41cb2daf5edf751063e2a32993008102ea5ee38938bcc0)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8025a5b3366c2de208699665562bfbabcb8e1363acfdc06321eb0f87156eaf34)
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
            type_hints = typing.get_type_hints(_typecheckingstub__1f6a07f81f09b3b01a6ceb14f199bed9b8084309a7f1a043cc0f092e2b0dce27)
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
            type_hints = typing.get_type_hints(_typecheckingstub__c79e94cab79641cdafe3ea0730f67c891e3674f8eac958a40583402bdcea1d80)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__38c214d304ce279ebf417056f4524eb7a61d8aab8b653f4af553e154f950a7e1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__a3e865e582b1d7be0d6d33a75810af863efc42c8cd77e396521c307cf41a5e8a)
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
            type_hints = typing.get_type_hints(_typecheckingstub__debf77cb46273a9702606ec4a19f6b5744e01387c631af8b91cb1c714eb7d672)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "key", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="value")
    def value(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "value"))

    @value.setter
    def value(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ff9a4f88ae90b4be32d3617d662dd74565f0ae9b53e3130349fc3af6d77ae3d6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "value", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__262f29980deddd5c09a4737fd8de2cb7f7439e10405332a64b2abe21d401167a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__327cc1f9943e6235e6ba2e294868663ba1d07b8f80bb517b39378cc6449f2f42)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putExtraParameters")
    def put_extra_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters, typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a0e996571682115856162199c737d9c3b9f8f101b31a07a239001ede4be5c483)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putExtraParameters", [value]))

    @jsii.member(jsii_name="resetExtraParameters")
    def reset_extra_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExtraParameters", []))

    @builtins.property
    @jsii.member(jsii_name="extraParameters")
    def extra_parameters(
        self,
    ) -> DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersList:
        return typing.cast(DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersList, jsii.get(self, "extraParameters"))

    @builtins.property
    @jsii.member(jsii_name="extraParametersInput")
    def extra_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]]], jsii.get(self, "extraParametersInput"))

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
            type_hints = typing.get_type_hints(_typecheckingstub__d814ea208d27b32ee6cd9e8b206bd6bc8da5c420329360196dff5b0e789e6fc0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "functionType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesFunction]:
        return typing.cast(typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesFunction], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesFunction],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c647fdc24fd1855b2e2fcea3480520302ebd142011be1c05a3c4290c1e848a89)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksFeatureEngineeringFeaturesFeaturesList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__87bb161a2bed5d2b76eac9ed0f6efa5a6e602f172a3b123051785eea096938fe)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DataDatabricksFeatureEngineeringFeaturesFeaturesOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1f7ecd176f24962f18043b41cbe67397dbb3c559e23207086408c8841ab0f67d)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DataDatabricksFeatureEngineeringFeaturesFeaturesOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0baeaeaee012a35c65741f0c26c8e20cf78ea82aaf6df8641e2daf2b53046d87)
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
            type_hints = typing.get_type_hints(_typecheckingstub__bd3fa84103eced98a7094828903d8e669cfeed119dab54640ff39dd17e79c81d)
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
            type_hints = typing.get_type_hints(_typecheckingstub__c44f161134c2f722d283d5e8caf1702839e4dfd61063aa002d26360b6def804e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeatures]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeatures]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeatures]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa7316bcdae42522be0d35c71458f5d988d82906d144a954e4d660cad8d54a4e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksFeatureEngineeringFeaturesFeaturesOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__77c156acfb8759da4febbf59bed7e66aed9cab3ca644a3d37e044ea692935e32)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="putFunction")
    def put_function(
        self,
        *,
        function_type: builtins.str,
        extra_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''
        :param function_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#function_type DataDatabricksFeatureEngineeringFeatures#function_type}.
        :param extra_parameters: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#extra_parameters DataDatabricksFeatureEngineeringFeatures#extra_parameters}.
        '''
        value = DataDatabricksFeatureEngineeringFeaturesFeaturesFunction(
            function_type=function_type, extra_parameters=extra_parameters
        )

        return typing.cast(None, jsii.invoke(self, "putFunction", [value]))

    @jsii.member(jsii_name="putSource")
    def put_source(
        self,
        *,
        delta_table_source: typing.Optional[typing.Union["DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param delta_table_source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#delta_table_source DataDatabricksFeatureEngineeringFeatures#delta_table_source}.
        '''
        value = DataDatabricksFeatureEngineeringFeaturesFeaturesSource(
            delta_table_source=delta_table_source
        )

        return typing.cast(None, jsii.invoke(self, "putSource", [value]))

    @jsii.member(jsii_name="putTimeWindow")
    def put_time_window(
        self,
        *,
        duration: builtins.str,
        offset: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param duration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#duration DataDatabricksFeatureEngineeringFeatures#duration}.
        :param offset: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#offset DataDatabricksFeatureEngineeringFeatures#offset}.
        '''
        value = DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow(
            duration=duration, offset=offset
        )

        return typing.cast(None, jsii.invoke(self, "putTimeWindow", [value]))

    @jsii.member(jsii_name="resetDescription")
    def reset_description(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDescription", []))

    @builtins.property
    @jsii.member(jsii_name="function")
    def function(
        self,
    ) -> DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionOutputReference:
        return typing.cast(DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionOutputReference, jsii.get(self, "function"))

    @builtins.property
    @jsii.member(jsii_name="source")
    def source(
        self,
    ) -> "DataDatabricksFeatureEngineeringFeaturesFeaturesSourceOutputReference":
        return typing.cast("DataDatabricksFeatureEngineeringFeaturesFeaturesSourceOutputReference", jsii.get(self, "source"))

    @builtins.property
    @jsii.member(jsii_name="timeWindow")
    def time_window(
        self,
    ) -> "DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindowOutputReference":
        return typing.cast("DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindowOutputReference", jsii.get(self, "timeWindow"))

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
    ) -> typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesFunction]:
        return typing.cast(typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesFunction], jsii.get(self, "functionInput"))

    @builtins.property
    @jsii.member(jsii_name="inputsInput")
    def inputs_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "inputsInput"))

    @builtins.property
    @jsii.member(jsii_name="sourceInput")
    def source_input(
        self,
    ) -> typing.Optional["DataDatabricksFeatureEngineeringFeaturesFeaturesSource"]:
        return typing.cast(typing.Optional["DataDatabricksFeatureEngineeringFeaturesFeaturesSource"], jsii.get(self, "sourceInput"))

    @builtins.property
    @jsii.member(jsii_name="timeWindowInput")
    def time_window_input(
        self,
    ) -> typing.Optional["DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow"]:
        return typing.cast(typing.Optional["DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow"], jsii.get(self, "timeWindowInput"))

    @builtins.property
    @jsii.member(jsii_name="description")
    def description(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "description"))

    @description.setter
    def description(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bb6afadbd9a0a2592581a6c1889292ad8c28b3f12bcdd580f84746ec9e76a5d9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "description", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="fullName")
    def full_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "fullName"))

    @full_name.setter
    def full_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c69538b4b1f66e0af193f6fa191a04a09f3d8dc20dcd97d50dda21bca5130b6d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "fullName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="inputs")
    def inputs(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "inputs"))

    @inputs.setter
    def inputs(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0b975bf94de3c3228631b78f62763e65b0a4c85f75a25b6df17acbcf4c6b2cf2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "inputs", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeatures]:
        return typing.cast(typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeatures], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeatures],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f3883c7da5a1338aadb16c0cf0f6951275efbbc069bd4cf5b0d1a527279e8a5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesSource",
    jsii_struct_bases=[],
    name_mapping={"delta_table_source": "deltaTableSource"},
)
class DataDatabricksFeatureEngineeringFeaturesFeaturesSource:
    def __init__(
        self,
        *,
        delta_table_source: typing.Optional[typing.Union["DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param delta_table_source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#delta_table_source DataDatabricksFeatureEngineeringFeatures#delta_table_source}.
        '''
        if isinstance(delta_table_source, dict):
            delta_table_source = DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource(**delta_table_source)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b1c31f53129eddde83dac597afa1b53d3f6335e2f448119b98a2991a6cc7f489)
            check_type(argname="argument delta_table_source", value=delta_table_source, expected_type=type_hints["delta_table_source"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if delta_table_source is not None:
            self._values["delta_table_source"] = delta_table_source

    @builtins.property
    def delta_table_source(
        self,
    ) -> typing.Optional["DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#delta_table_source DataDatabricksFeatureEngineeringFeatures#delta_table_source}.'''
        result = self._values.get("delta_table_source")
        return typing.cast(typing.Optional["DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksFeatureEngineeringFeaturesFeaturesSource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource",
    jsii_struct_bases=[],
    name_mapping={
        "entity_columns": "entityColumns",
        "full_name": "fullName",
        "timeseries_column": "timeseriesColumn",
    },
)
class DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource:
    def __init__(
        self,
        *,
        entity_columns: typing.Sequence[builtins.str],
        full_name: builtins.str,
        timeseries_column: builtins.str,
    ) -> None:
        '''
        :param entity_columns: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#entity_columns DataDatabricksFeatureEngineeringFeatures#entity_columns}.
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#full_name DataDatabricksFeatureEngineeringFeatures#full_name}.
        :param timeseries_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#timeseries_column DataDatabricksFeatureEngineeringFeatures#timeseries_column}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fdd635d496a22f18844f660fad5a8dd8dbe7390b32b44b6160de689db283c456)
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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#entity_columns DataDatabricksFeatureEngineeringFeatures#entity_columns}.'''
        result = self._values.get("entity_columns")
        assert result is not None, "Required property 'entity_columns' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def full_name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#full_name DataDatabricksFeatureEngineeringFeatures#full_name}.'''
        result = self._values.get("full_name")
        assert result is not None, "Required property 'full_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def timeseries_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#timeseries_column DataDatabricksFeatureEngineeringFeatures#timeseries_column}.'''
        result = self._values.get("timeseries_column")
        assert result is not None, "Required property 'timeseries_column' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSourceOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSourceOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__4a3eb244d7bfc373d25bbf28544b7b380355061dd018ca00d692df9d91225a44)
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
            type_hints = typing.get_type_hints(_typecheckingstub__b6abd8ef6c4270e32379aae27ce83265dd84b968485d002cad9c1bc1027af188)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "entityColumns", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="fullName")
    def full_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "fullName"))

    @full_name.setter
    def full_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9ddce497fb3665ed9b38574c4b3ac94d41b1f9ddf25f0fbf879840ab0818942e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "fullName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timeseriesColumn")
    def timeseries_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timeseriesColumn"))

    @timeseries_column.setter
    def timeseries_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__686d1b3c43126c935f811f3decfb7135e390c85cb67186a57586323debe3a7b8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timeseriesColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__806005c80a28c1c86db84e7982f9367df489bead3e8aad282547e6d494f3f09d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksFeatureEngineeringFeaturesFeaturesSourceOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesSourceOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__faab88c6c94ff25cb2cdc4fb92227340fb861b8dc22e6f5bf159cef0c59e76fe)
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
        :param entity_columns: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#entity_columns DataDatabricksFeatureEngineeringFeatures#entity_columns}.
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#full_name DataDatabricksFeatureEngineeringFeatures#full_name}.
        :param timeseries_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#timeseries_column DataDatabricksFeatureEngineeringFeatures#timeseries_column}.
        '''
        value = DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource(
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
    ) -> DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSourceOutputReference:
        return typing.cast(DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSourceOutputReference, jsii.get(self, "deltaTableSource"))

    @builtins.property
    @jsii.member(jsii_name="deltaTableSourceInput")
    def delta_table_source_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource]], jsii.get(self, "deltaTableSourceInput"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesSource]:
        return typing.cast(typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesSource], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesSource],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c46fd1c15c31744790c5e0c556a2540e196b7236fd3217982be144e5722e6f94)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow",
    jsii_struct_bases=[],
    name_mapping={"duration": "duration", "offset": "offset"},
)
class DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow:
    def __init__(
        self,
        *,
        duration: builtins.str,
        offset: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param duration: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#duration DataDatabricksFeatureEngineeringFeatures#duration}.
        :param offset: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#offset DataDatabricksFeatureEngineeringFeatures#offset}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f50510a5d4b81df76526fc93ffdd8e67184df932a3902f770baa40a49ee66703)
            check_type(argname="argument duration", value=duration, expected_type=type_hints["duration"])
            check_type(argname="argument offset", value=offset, expected_type=type_hints["offset"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "duration": duration,
        }
        if offset is not None:
            self._values["offset"] = offset

    @builtins.property
    def duration(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#duration DataDatabricksFeatureEngineeringFeatures#duration}.'''
        result = self._values.get("duration")
        assert result is not None, "Required property 'duration' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def offset(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/feature_engineering_features#offset DataDatabricksFeatureEngineeringFeatures#offset}.'''
        result = self._values.get("offset")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindowOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksFeatureEngineeringFeatures.DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindowOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__e16a3241e497e5187185b7ab368a8d3e4bbdd47c536a0f7b88bd1a32b717fc87)
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
            type_hints = typing.get_type_hints(_typecheckingstub__ad98634a0f15285d52dec0b972ed9518fc0b2e82e7ea256507edae66d5f2eb45)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "duration", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="offset")
    def offset(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "offset"))

    @offset.setter
    def offset(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3a78467499890f4749f1f86a8279c216bebd03127240b8912c1d7df12b71c4c8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "offset", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow]:
        return typing.cast(typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d26cd571cbad955118e91fd7dda89709e83bb0f3952d6d04328b5c675cb647e7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "DataDatabricksFeatureEngineeringFeatures",
    "DataDatabricksFeatureEngineeringFeaturesConfig",
    "DataDatabricksFeatureEngineeringFeaturesFeatures",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesFunction",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersList",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParametersOutputReference",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionOutputReference",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesList",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesOutputReference",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesSource",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSourceOutputReference",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesSourceOutputReference",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow",
    "DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindowOutputReference",
]

publication.publish()

def _typecheckingstub__2131055a7c36ca9dd5d07c418b7ad65afb4b1c7354e7a641ef69e7b910ead1bd(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
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

def _typecheckingstub__eb488d6215f2208ed5b43fb48c271f5d8e894034856069f3e69bedc01e931ee9(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c2deeaf867f0acddef6db27728ff7bf2a62304d1850fb031c14312135d45f7cc(
    *,
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

def _typecheckingstub__b6f32fce82528c8e35f7c83b48d2b4b154b05496dc551583f9a850d0ee658096(
    *,
    full_name: builtins.str,
    function: typing.Union[DataDatabricksFeatureEngineeringFeaturesFeaturesFunction, typing.Dict[builtins.str, typing.Any]],
    inputs: typing.Sequence[builtins.str],
    source: typing.Union[DataDatabricksFeatureEngineeringFeaturesFeaturesSource, typing.Dict[builtins.str, typing.Any]],
    time_window: typing.Union[DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow, typing.Dict[builtins.str, typing.Any]],
    description: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c38772e28f9407030cc0bd3b54b5d488bd43323b73f9e86322aff3076bd7ffc4(
    *,
    function_type: builtins.str,
    extra_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9481da63ceba4272ce7813904a303dd9c5239ed74c370bca246fd1ee4ce0bf47(
    *,
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eed8da7cfa6b86f566b7ee727af8bb33ebb3da86ed835339ba1314657d5d9423(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8dfe801c2b650e2aeb41cb2daf5edf751063e2a32993008102ea5ee38938bcc0(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8025a5b3366c2de208699665562bfbabcb8e1363acfdc06321eb0f87156eaf34(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1f6a07f81f09b3b01a6ceb14f199bed9b8084309a7f1a043cc0f092e2b0dce27(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c79e94cab79641cdafe3ea0730f67c891e3674f8eac958a40583402bdcea1d80(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__38c214d304ce279ebf417056f4524eb7a61d8aab8b653f4af553e154f950a7e1(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a3e865e582b1d7be0d6d33a75810af863efc42c8cd77e396521c307cf41a5e8a(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__debf77cb46273a9702606ec4a19f6b5744e01387c631af8b91cb1c714eb7d672(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ff9a4f88ae90b4be32d3617d662dd74565f0ae9b53e3130349fc3af6d77ae3d6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__262f29980deddd5c09a4737fd8de2cb7f7439e10405332a64b2abe21d401167a(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__327cc1f9943e6235e6ba2e294868663ba1d07b8f80bb517b39378cc6449f2f42(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a0e996571682115856162199c737d9c3b9f8f101b31a07a239001ede4be5c483(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksFeatureEngineeringFeaturesFeaturesFunctionExtraParameters, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d814ea208d27b32ee6cd9e8b206bd6bc8da5c420329360196dff5b0e789e6fc0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c647fdc24fd1855b2e2fcea3480520302ebd142011be1c05a3c4290c1e848a89(
    value: typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesFunction],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__87bb161a2bed5d2b76eac9ed0f6efa5a6e602f172a3b123051785eea096938fe(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1f7ecd176f24962f18043b41cbe67397dbb3c559e23207086408c8841ab0f67d(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0baeaeaee012a35c65741f0c26c8e20cf78ea82aaf6df8641e2daf2b53046d87(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bd3fa84103eced98a7094828903d8e669cfeed119dab54640ff39dd17e79c81d(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c44f161134c2f722d283d5e8caf1702839e4dfd61063aa002d26360b6def804e(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa7316bcdae42522be0d35c71458f5d988d82906d144a954e4d660cad8d54a4e(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksFeatureEngineeringFeaturesFeatures]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__77c156acfb8759da4febbf59bed7e66aed9cab3ca644a3d37e044ea692935e32(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bb6afadbd9a0a2592581a6c1889292ad8c28b3f12bcdd580f84746ec9e76a5d9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c69538b4b1f66e0af193f6fa191a04a09f3d8dc20dcd97d50dda21bca5130b6d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0b975bf94de3c3228631b78f62763e65b0a4c85f75a25b6df17acbcf4c6b2cf2(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f3883c7da5a1338aadb16c0cf0f6951275efbbc069bd4cf5b0d1a527279e8a5(
    value: typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeatures],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b1c31f53129eddde83dac597afa1b53d3f6335e2f448119b98a2991a6cc7f489(
    *,
    delta_table_source: typing.Optional[typing.Union[DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fdd635d496a22f18844f660fad5a8dd8dbe7390b32b44b6160de689db283c456(
    *,
    entity_columns: typing.Sequence[builtins.str],
    full_name: builtins.str,
    timeseries_column: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4a3eb244d7bfc373d25bbf28544b7b380355061dd018ca00d692df9d91225a44(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b6abd8ef6c4270e32379aae27ce83265dd84b968485d002cad9c1bc1027af188(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9ddce497fb3665ed9b38574c4b3ac94d41b1f9ddf25f0fbf879840ab0818942e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__686d1b3c43126c935f811f3decfb7135e390c85cb67186a57586323debe3a7b8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__806005c80a28c1c86db84e7982f9367df489bead3e8aad282547e6d494f3f09d(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksFeatureEngineeringFeaturesFeaturesSourceDeltaTableSource]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__faab88c6c94ff25cb2cdc4fb92227340fb861b8dc22e6f5bf159cef0c59e76fe(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c46fd1c15c31744790c5e0c556a2540e196b7236fd3217982be144e5722e6f94(
    value: typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesSource],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f50510a5d4b81df76526fc93ffdd8e67184df932a3902f770baa40a49ee66703(
    *,
    duration: builtins.str,
    offset: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e16a3241e497e5187185b7ab368a8d3e4bbdd47c536a0f7b88bd1a32b717fc87(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad98634a0f15285d52dec0b972ed9518fc0b2e82e7ea256507edae66d5f2eb45(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a78467499890f4749f1f86a8279c216bebd03127240b8912c1d7df12b71c4c8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d26cd571cbad955118e91fd7dda89709e83bb0f3952d6d04328b5c675cb647e7(
    value: typing.Optional[DataDatabricksFeatureEngineeringFeaturesFeaturesTimeWindow],
) -> None:
    """Type checking stubs"""
    pass
