r'''
# `data_databricks_data_quality_monitors`

Refer to the Terraform Registry for docs: [`data_databricks_data_quality_monitors`](https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors).
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


class DataDatabricksDataQualityMonitors(
    _cdktf_9a9027ec.TerraformDataSource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitors",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors databricks_data_quality_monitors}.'''

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
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors databricks_data_quality_monitors} Data Source.

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
            type_hints = typing.get_type_hints(_typecheckingstub__154dade6af038db7bb1eda30385d3b11e9d6af12838cc0eeaa8f965caf881523)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = DataDatabricksDataQualityMonitorsConfig(
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
        '''Generates CDKTF code for importing a DataDatabricksDataQualityMonitors resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DataDatabricksDataQualityMonitors to import.
        :param import_from_id: The id of the existing DataDatabricksDataQualityMonitors that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DataDatabricksDataQualityMonitors to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5c03e8623a1aeeaa33e39f66f14d9e628dbc1350488e23537251e55c3c699c54)
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
    @jsii.member(jsii_name="monitors")
    def monitors(self) -> "DataDatabricksDataQualityMonitorsMonitorsList":
        return typing.cast("DataDatabricksDataQualityMonitorsMonitorsList", jsii.get(self, "monitors"))


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsConfig",
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
class DataDatabricksDataQualityMonitorsConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
            type_hints = typing.get_type_hints(_typecheckingstub__3a0c39bef64cd26e5ec92a6d3bb76f6d5071db47b6e4e68341dac1548ef3a444)
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
        return "DataDatabricksDataQualityMonitorsConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitors",
    jsii_struct_bases=[],
    name_mapping={
        "object_id": "objectId",
        "object_type": "objectType",
        "anomaly_detection_config": "anomalyDetectionConfig",
        "data_profiling_config": "dataProfilingConfig",
    },
)
class DataDatabricksDataQualityMonitorsMonitors:
    def __init__(
        self,
        *,
        object_id: builtins.str,
        object_type: builtins.str,
        anomaly_detection_config: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        data_profiling_config: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param object_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#object_id DataDatabricksDataQualityMonitors#object_id}.
        :param object_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#object_type DataDatabricksDataQualityMonitors#object_type}.
        :param anomaly_detection_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#anomaly_detection_config DataDatabricksDataQualityMonitors#anomaly_detection_config}.
        :param data_profiling_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#data_profiling_config DataDatabricksDataQualityMonitors#data_profiling_config}.
        '''
        if isinstance(anomaly_detection_config, dict):
            anomaly_detection_config = DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig(**anomaly_detection_config)
        if isinstance(data_profiling_config, dict):
            data_profiling_config = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig(**data_profiling_config)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__27c5673a47dc6e51ec5e77da087d1bba77110369856032e834af2ee81e236c3c)
            check_type(argname="argument object_id", value=object_id, expected_type=type_hints["object_id"])
            check_type(argname="argument object_type", value=object_type, expected_type=type_hints["object_type"])
            check_type(argname="argument anomaly_detection_config", value=anomaly_detection_config, expected_type=type_hints["anomaly_detection_config"])
            check_type(argname="argument data_profiling_config", value=data_profiling_config, expected_type=type_hints["data_profiling_config"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "object_id": object_id,
            "object_type": object_type,
        }
        if anomaly_detection_config is not None:
            self._values["anomaly_detection_config"] = anomaly_detection_config
        if data_profiling_config is not None:
            self._values["data_profiling_config"] = data_profiling_config

    @builtins.property
    def object_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#object_id DataDatabricksDataQualityMonitors#object_id}.'''
        result = self._values.get("object_id")
        assert result is not None, "Required property 'object_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def object_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#object_type DataDatabricksDataQualityMonitors#object_type}.'''
        result = self._values.get("object_type")
        assert result is not None, "Required property 'object_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def anomaly_detection_config(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#anomaly_detection_config DataDatabricksDataQualityMonitors#anomaly_detection_config}.'''
        result = self._values.get("anomaly_detection_config")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig"], result)

    @builtins.property
    def data_profiling_config(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#data_profiling_config DataDatabricksDataQualityMonitors#data_profiling_config}.'''
        result = self._values.get("data_profiling_config")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitors(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig",
    jsii_struct_bases=[],
    name_mapping={},
)
class DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig:
    def __init__(self) -> None:
        self._values: typing.Dict[builtins.str, typing.Any] = {}

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__15995d3f58ec3dc46f49bfb36da09202db2935098683ea6fd4c09533fa2f9397)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40679cb4785eee535f14c5054827404848270f05dc6e3e0fed0c745b41abe0ad)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig",
    jsii_struct_bases=[],
    name_mapping={
        "output_schema_id": "outputSchemaId",
        "assets_dir": "assetsDir",
        "baseline_table_name": "baselineTableName",
        "custom_metrics": "customMetrics",
        "inference_log": "inferenceLog",
        "notification_settings": "notificationSettings",
        "schedule": "schedule",
        "skip_builtin_dashboard": "skipBuiltinDashboard",
        "slicing_exprs": "slicingExprs",
        "snapshot": "snapshot",
        "time_series": "timeSeries",
        "warehouse_id": "warehouseId",
    },
)
class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig:
    def __init__(
        self,
        *,
        output_schema_id: builtins.str,
        assets_dir: typing.Optional[builtins.str] = None,
        baseline_table_name: typing.Optional[builtins.str] = None,
        custom_metrics: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics", typing.Dict[builtins.str, typing.Any]]]]] = None,
        inference_log: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog", typing.Dict[builtins.str, typing.Any]]] = None,
        notification_settings: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        schedule: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule", typing.Dict[builtins.str, typing.Any]]] = None,
        skip_builtin_dashboard: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        slicing_exprs: typing.Optional[typing.Sequence[builtins.str]] = None,
        snapshot: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot", typing.Dict[builtins.str, typing.Any]]] = None,
        time_series: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries", typing.Dict[builtins.str, typing.Any]]] = None,
        warehouse_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param output_schema_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#output_schema_id DataDatabricksDataQualityMonitors#output_schema_id}.
        :param assets_dir: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#assets_dir DataDatabricksDataQualityMonitors#assets_dir}.
        :param baseline_table_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#baseline_table_name DataDatabricksDataQualityMonitors#baseline_table_name}.
        :param custom_metrics: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#custom_metrics DataDatabricksDataQualityMonitors#custom_metrics}.
        :param inference_log: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#inference_log DataDatabricksDataQualityMonitors#inference_log}.
        :param notification_settings: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#notification_settings DataDatabricksDataQualityMonitors#notification_settings}.
        :param schedule: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#schedule DataDatabricksDataQualityMonitors#schedule}.
        :param skip_builtin_dashboard: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#skip_builtin_dashboard DataDatabricksDataQualityMonitors#skip_builtin_dashboard}.
        :param slicing_exprs: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#slicing_exprs DataDatabricksDataQualityMonitors#slicing_exprs}.
        :param snapshot: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#snapshot DataDatabricksDataQualityMonitors#snapshot}.
        :param time_series: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#time_series DataDatabricksDataQualityMonitors#time_series}.
        :param warehouse_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#warehouse_id DataDatabricksDataQualityMonitors#warehouse_id}.
        '''
        if isinstance(inference_log, dict):
            inference_log = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog(**inference_log)
        if isinstance(notification_settings, dict):
            notification_settings = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings(**notification_settings)
        if isinstance(schedule, dict):
            schedule = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule(**schedule)
        if isinstance(snapshot, dict):
            snapshot = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot(**snapshot)
        if isinstance(time_series, dict):
            time_series = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries(**time_series)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4f9e550992efbe9cf34eb7030b663ae7d5a9826f1a0a4f722aa669a91f40254c)
            check_type(argname="argument output_schema_id", value=output_schema_id, expected_type=type_hints["output_schema_id"])
            check_type(argname="argument assets_dir", value=assets_dir, expected_type=type_hints["assets_dir"])
            check_type(argname="argument baseline_table_name", value=baseline_table_name, expected_type=type_hints["baseline_table_name"])
            check_type(argname="argument custom_metrics", value=custom_metrics, expected_type=type_hints["custom_metrics"])
            check_type(argname="argument inference_log", value=inference_log, expected_type=type_hints["inference_log"])
            check_type(argname="argument notification_settings", value=notification_settings, expected_type=type_hints["notification_settings"])
            check_type(argname="argument schedule", value=schedule, expected_type=type_hints["schedule"])
            check_type(argname="argument skip_builtin_dashboard", value=skip_builtin_dashboard, expected_type=type_hints["skip_builtin_dashboard"])
            check_type(argname="argument slicing_exprs", value=slicing_exprs, expected_type=type_hints["slicing_exprs"])
            check_type(argname="argument snapshot", value=snapshot, expected_type=type_hints["snapshot"])
            check_type(argname="argument time_series", value=time_series, expected_type=type_hints["time_series"])
            check_type(argname="argument warehouse_id", value=warehouse_id, expected_type=type_hints["warehouse_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "output_schema_id": output_schema_id,
        }
        if assets_dir is not None:
            self._values["assets_dir"] = assets_dir
        if baseline_table_name is not None:
            self._values["baseline_table_name"] = baseline_table_name
        if custom_metrics is not None:
            self._values["custom_metrics"] = custom_metrics
        if inference_log is not None:
            self._values["inference_log"] = inference_log
        if notification_settings is not None:
            self._values["notification_settings"] = notification_settings
        if schedule is not None:
            self._values["schedule"] = schedule
        if skip_builtin_dashboard is not None:
            self._values["skip_builtin_dashboard"] = skip_builtin_dashboard
        if slicing_exprs is not None:
            self._values["slicing_exprs"] = slicing_exprs
        if snapshot is not None:
            self._values["snapshot"] = snapshot
        if time_series is not None:
            self._values["time_series"] = time_series
        if warehouse_id is not None:
            self._values["warehouse_id"] = warehouse_id

    @builtins.property
    def output_schema_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#output_schema_id DataDatabricksDataQualityMonitors#output_schema_id}.'''
        result = self._values.get("output_schema_id")
        assert result is not None, "Required property 'output_schema_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def assets_dir(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#assets_dir DataDatabricksDataQualityMonitors#assets_dir}.'''
        result = self._values.get("assets_dir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def baseline_table_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#baseline_table_name DataDatabricksDataQualityMonitors#baseline_table_name}.'''
        result = self._values.get("baseline_table_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def custom_metrics(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics"]]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#custom_metrics DataDatabricksDataQualityMonitors#custom_metrics}.'''
        result = self._values.get("custom_metrics")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics"]]], result)

    @builtins.property
    def inference_log(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#inference_log DataDatabricksDataQualityMonitors#inference_log}.'''
        result = self._values.get("inference_log")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog"], result)

    @builtins.property
    def notification_settings(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#notification_settings DataDatabricksDataQualityMonitors#notification_settings}.'''
        result = self._values.get("notification_settings")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings"], result)

    @builtins.property
    def schedule(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#schedule DataDatabricksDataQualityMonitors#schedule}.'''
        result = self._values.get("schedule")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule"], result)

    @builtins.property
    def skip_builtin_dashboard(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#skip_builtin_dashboard DataDatabricksDataQualityMonitors#skip_builtin_dashboard}.'''
        result = self._values.get("skip_builtin_dashboard")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def slicing_exprs(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#slicing_exprs DataDatabricksDataQualityMonitors#slicing_exprs}.'''
        result = self._values.get("slicing_exprs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def snapshot(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#snapshot DataDatabricksDataQualityMonitors#snapshot}.'''
        result = self._values.get("snapshot")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot"], result)

    @builtins.property
    def time_series(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#time_series DataDatabricksDataQualityMonitors#time_series}.'''
        result = self._values.get("time_series")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries"], result)

    @builtins.property
    def warehouse_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#warehouse_id DataDatabricksDataQualityMonitors#warehouse_id}.'''
        result = self._values.get("warehouse_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics",
    jsii_struct_bases=[],
    name_mapping={
        "definition": "definition",
        "input_columns": "inputColumns",
        "name": "name",
        "output_data_type": "outputDataType",
        "type": "type",
    },
)
class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics:
    def __init__(
        self,
        *,
        definition: builtins.str,
        input_columns: typing.Sequence[builtins.str],
        name: builtins.str,
        output_data_type: builtins.str,
        type: builtins.str,
    ) -> None:
        '''
        :param definition: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#definition DataDatabricksDataQualityMonitors#definition}.
        :param input_columns: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#input_columns DataDatabricksDataQualityMonitors#input_columns}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#name DataDatabricksDataQualityMonitors#name}.
        :param output_data_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#output_data_type DataDatabricksDataQualityMonitors#output_data_type}.
        :param type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#type DataDatabricksDataQualityMonitors#type}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b5b82761193b3f7fc04c110b089e6d48012a981cd8c52a5e0722ffafdb0ba107)
            check_type(argname="argument definition", value=definition, expected_type=type_hints["definition"])
            check_type(argname="argument input_columns", value=input_columns, expected_type=type_hints["input_columns"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument output_data_type", value=output_data_type, expected_type=type_hints["output_data_type"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "definition": definition,
            "input_columns": input_columns,
            "name": name,
            "output_data_type": output_data_type,
            "type": type,
        }

    @builtins.property
    def definition(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#definition DataDatabricksDataQualityMonitors#definition}.'''
        result = self._values.get("definition")
        assert result is not None, "Required property 'definition' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def input_columns(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#input_columns DataDatabricksDataQualityMonitors#input_columns}.'''
        result = self._values.get("input_columns")
        assert result is not None, "Required property 'input_columns' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#name DataDatabricksDataQualityMonitors#name}.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def output_data_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#output_data_type DataDatabricksDataQualityMonitors#output_data_type}.'''
        result = self._values.get("output_data_type")
        assert result is not None, "Required property 'output_data_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#type DataDatabricksDataQualityMonitors#type}.'''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__4e2567f848d619db2d489a8456777d44f70e166c16f7b34845b888fa9e5d7245)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9275dae5cbcd292df3e8164e13f24f0cad939de29898107ec8f799d96dcdfba5)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e8b81a0d0c89996309f7669090431befb8e1bbfb2b61c7e645148a10614003df)
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
            type_hints = typing.get_type_hints(_typecheckingstub__5fea723a8ababa81cce463577ba42448c960603a27f45ca973a41b92743b4ced)
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
            type_hints = typing.get_type_hints(_typecheckingstub__f8ee0f72cbdb4ac3c259df1a67c9af29c259416034c57bd65541f9f7f3b6e2b3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f6057b25dbcdf802ee8a22669f203ecf22fc6c057c85ffdd5e4c60fcccd84f2f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__25aef9f6a9414c1be65ed1e351cebf76bfe3813d18109d5920f2cc7b8a3502ae)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @builtins.property
    @jsii.member(jsii_name="definitionInput")
    def definition_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "definitionInput"))

    @builtins.property
    @jsii.member(jsii_name="inputColumnsInput")
    def input_columns_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "inputColumnsInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="outputDataTypeInput")
    def output_data_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "outputDataTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="typeInput")
    def type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "typeInput"))

    @builtins.property
    @jsii.member(jsii_name="definition")
    def definition(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "definition"))

    @definition.setter
    def definition(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4eca1efd5a944255bdbf82b3ed1725efa3d52800b34396ea2c4099295846f900)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "definition", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="inputColumns")
    def input_columns(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "inputColumns"))

    @input_columns.setter
    def input_columns(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__82cee604570b665cd219a5a5238dde3d8a7f9cbe27e1d7c8fe1cbdd30947c11c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "inputColumns", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7cbd53c766e2139ddb1b2da4aa17e2d84631b6d8330e31ee1cd6817ca1491e87)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="outputDataType")
    def output_data_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "outputDataType"))

    @output_data_type.setter
    def output_data_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ada885030f9cdfa4d35ec7713b210b7d51d463f9e73df93e94f071a2b51290bb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "outputDataType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__868d931cd8653b1c9cb9857ec340499388f8cd79c93864530b9627c7f832925d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13d0cdb079f2e8c7e7288da658ff02465030ae6f30e18c1d8140aa0f0ea9dbc9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog",
    jsii_struct_bases=[],
    name_mapping={
        "granularities": "granularities",
        "model_id_column": "modelIdColumn",
        "prediction_column": "predictionColumn",
        "problem_type": "problemType",
        "timestamp_column": "timestampColumn",
        "label_column": "labelColumn",
    },
)
class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog:
    def __init__(
        self,
        *,
        granularities: typing.Sequence[builtins.str],
        model_id_column: builtins.str,
        prediction_column: builtins.str,
        problem_type: builtins.str,
        timestamp_column: builtins.str,
        label_column: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#granularities DataDatabricksDataQualityMonitors#granularities}.
        :param model_id_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#model_id_column DataDatabricksDataQualityMonitors#model_id_column}.
        :param prediction_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#prediction_column DataDatabricksDataQualityMonitors#prediction_column}.
        :param problem_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#problem_type DataDatabricksDataQualityMonitors#problem_type}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#timestamp_column DataDatabricksDataQualityMonitors#timestamp_column}.
        :param label_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#label_column DataDatabricksDataQualityMonitors#label_column}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a8e5dced866f6a2d8b51f1cefbea8880af7c8ab47164174c8c2ef322462b9f95)
            check_type(argname="argument granularities", value=granularities, expected_type=type_hints["granularities"])
            check_type(argname="argument model_id_column", value=model_id_column, expected_type=type_hints["model_id_column"])
            check_type(argname="argument prediction_column", value=prediction_column, expected_type=type_hints["prediction_column"])
            check_type(argname="argument problem_type", value=problem_type, expected_type=type_hints["problem_type"])
            check_type(argname="argument timestamp_column", value=timestamp_column, expected_type=type_hints["timestamp_column"])
            check_type(argname="argument label_column", value=label_column, expected_type=type_hints["label_column"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "granularities": granularities,
            "model_id_column": model_id_column,
            "prediction_column": prediction_column,
            "problem_type": problem_type,
            "timestamp_column": timestamp_column,
        }
        if label_column is not None:
            self._values["label_column"] = label_column

    @builtins.property
    def granularities(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#granularities DataDatabricksDataQualityMonitors#granularities}.'''
        result = self._values.get("granularities")
        assert result is not None, "Required property 'granularities' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def model_id_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#model_id_column DataDatabricksDataQualityMonitors#model_id_column}.'''
        result = self._values.get("model_id_column")
        assert result is not None, "Required property 'model_id_column' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def prediction_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#prediction_column DataDatabricksDataQualityMonitors#prediction_column}.'''
        result = self._values.get("prediction_column")
        assert result is not None, "Required property 'prediction_column' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def problem_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#problem_type DataDatabricksDataQualityMonitors#problem_type}.'''
        result = self._values.get("problem_type")
        assert result is not None, "Required property 'problem_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def timestamp_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#timestamp_column DataDatabricksDataQualityMonitors#timestamp_column}.'''
        result = self._values.get("timestamp_column")
        assert result is not None, "Required property 'timestamp_column' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def label_column(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#label_column DataDatabricksDataQualityMonitors#label_column}.'''
        result = self._values.get("label_column")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLogOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLogOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__91562d2d9dbc64d20722be846eedb695653b95a45948da367c48086448b2c573)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetLabelColumn")
    def reset_label_column(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLabelColumn", []))

    @builtins.property
    @jsii.member(jsii_name="granularitiesInput")
    def granularities_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "granularitiesInput"))

    @builtins.property
    @jsii.member(jsii_name="labelColumnInput")
    def label_column_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "labelColumnInput"))

    @builtins.property
    @jsii.member(jsii_name="modelIdColumnInput")
    def model_id_column_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "modelIdColumnInput"))

    @builtins.property
    @jsii.member(jsii_name="predictionColumnInput")
    def prediction_column_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "predictionColumnInput"))

    @builtins.property
    @jsii.member(jsii_name="problemTypeInput")
    def problem_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "problemTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="timestampColumnInput")
    def timestamp_column_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "timestampColumnInput"))

    @builtins.property
    @jsii.member(jsii_name="granularities")
    def granularities(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "granularities"))

    @granularities.setter
    def granularities(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3240f11e735430b3293de9b24c55a4c4bd3c2b949a4882dcd91918e3a678b818)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "granularities", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="labelColumn")
    def label_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "labelColumn"))

    @label_column.setter
    def label_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__017ee2201a95bf41e75bb116f3a58f5bb58142c9999924770660fad48e9bdaa2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "labelColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="modelIdColumn")
    def model_id_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "modelIdColumn"))

    @model_id_column.setter
    def model_id_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7c1df33144565bd064aeced99207b8c3f5afeca0180e6d0634bdf49346daf38b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "modelIdColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="predictionColumn")
    def prediction_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "predictionColumn"))

    @prediction_column.setter
    def prediction_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40aa5e31ee24c56f2c7d62bdc41cf627724d1a8b810901178d9af62777a3b5ad)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "predictionColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="problemType")
    def problem_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "problemType"))

    @problem_type.setter
    def problem_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__839c43673bb890f95f59987b531e2b0d0ee67177e0dbb9154f9f4a5008d779ee)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "problemType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timestampColumn")
    def timestamp_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timestampColumn"))

    @timestamp_column.setter
    def timestamp_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a4ecd7b975f076faa7658c4eb2799eeb6b43a55f601c4c9af7e75bf0df9c719a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timestampColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__22cbba345d2f0f14ee894b493900b608cc899fe792de1d79b87b7f8b33811f80)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings",
    jsii_struct_bases=[],
    name_mapping={"on_failure": "onFailure"},
)
class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings:
    def __init__(
        self,
        *,
        on_failure: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param on_failure: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#on_failure DataDatabricksDataQualityMonitors#on_failure}.
        '''
        if isinstance(on_failure, dict):
            on_failure = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure(**on_failure)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eac39fee1d1f03820a50785c9c9d9509636f6ec21544336871d11f6d1c21c13a)
            check_type(argname="argument on_failure", value=on_failure, expected_type=type_hints["on_failure"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if on_failure is not None:
            self._values["on_failure"] = on_failure

    @builtins.property
    def on_failure(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#on_failure DataDatabricksDataQualityMonitors#on_failure}.'''
        result = self._values.get("on_failure")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure",
    jsii_struct_bases=[],
    name_mapping={"email_addresses": "emailAddresses"},
)
class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure:
    def __init__(
        self,
        *,
        email_addresses: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param email_addresses: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#email_addresses DataDatabricksDataQualityMonitors#email_addresses}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f28c2f3b0c0325b14f71d371d571f1217202482e965f2cc88a4db3a8102feee0)
            check_type(argname="argument email_addresses", value=email_addresses, expected_type=type_hints["email_addresses"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if email_addresses is not None:
            self._values["email_addresses"] = email_addresses

    @builtins.property
    def email_addresses(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#email_addresses DataDatabricksDataQualityMonitors#email_addresses}.'''
        result = self._values.get("email_addresses")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailureOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailureOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__679db1bbff201c7928e8c867526509a54dbd3de66e8783dc12f840b994d963f2)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetEmailAddresses")
    def reset_email_addresses(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmailAddresses", []))

    @builtins.property
    @jsii.member(jsii_name="emailAddressesInput")
    def email_addresses_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "emailAddressesInput"))

    @builtins.property
    @jsii.member(jsii_name="emailAddresses")
    def email_addresses(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "emailAddresses"))

    @email_addresses.setter
    def email_addresses(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b445b78ef8f7c1fb4949763a4ce79c07b720f94b9c52dc8c795fb26dbcd64674)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailAddresses", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a9418c905597f4935996e654325835c8e893a4ab74ecbafcca4b2d93dae96071)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__bb8f8add8476361efbb9f2c5bcf02d9f442ab2bf4235499dce73f02737bdd795)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putOnFailure")
    def put_on_failure(
        self,
        *,
        email_addresses: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param email_addresses: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#email_addresses DataDatabricksDataQualityMonitors#email_addresses}.
        '''
        value = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure(
            email_addresses=email_addresses
        )

        return typing.cast(None, jsii.invoke(self, "putOnFailure", [value]))

    @jsii.member(jsii_name="resetOnFailure")
    def reset_on_failure(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOnFailure", []))

    @builtins.property
    @jsii.member(jsii_name="onFailure")
    def on_failure(
        self,
    ) -> DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailureOutputReference:
        return typing.cast(DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailureOutputReference, jsii.get(self, "onFailure"))

    @builtins.property
    @jsii.member(jsii_name="onFailureInput")
    def on_failure_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure]], jsii.get(self, "onFailureInput"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1cee549e0dba77c616813fcec52135e109a96fee3c9db383230d5665943c2644)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__ce8ac9d8bcb3be79c734e127a70ea0a074fd9e86f38d3728f6d85e6af3754532)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putCustomMetrics")
    def put_custom_metrics(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__00b3f10f8d349902f33eb68ca83cca98842c34d15ccc8bce16492cc12c6fadb5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putCustomMetrics", [value]))

    @jsii.member(jsii_name="putInferenceLog")
    def put_inference_log(
        self,
        *,
        granularities: typing.Sequence[builtins.str],
        model_id_column: builtins.str,
        prediction_column: builtins.str,
        problem_type: builtins.str,
        timestamp_column: builtins.str,
        label_column: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#granularities DataDatabricksDataQualityMonitors#granularities}.
        :param model_id_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#model_id_column DataDatabricksDataQualityMonitors#model_id_column}.
        :param prediction_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#prediction_column DataDatabricksDataQualityMonitors#prediction_column}.
        :param problem_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#problem_type DataDatabricksDataQualityMonitors#problem_type}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#timestamp_column DataDatabricksDataQualityMonitors#timestamp_column}.
        :param label_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#label_column DataDatabricksDataQualityMonitors#label_column}.
        '''
        value = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog(
            granularities=granularities,
            model_id_column=model_id_column,
            prediction_column=prediction_column,
            problem_type=problem_type,
            timestamp_column=timestamp_column,
            label_column=label_column,
        )

        return typing.cast(None, jsii.invoke(self, "putInferenceLog", [value]))

    @jsii.member(jsii_name="putNotificationSettings")
    def put_notification_settings(
        self,
        *,
        on_failure: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param on_failure: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#on_failure DataDatabricksDataQualityMonitors#on_failure}.
        '''
        value = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings(
            on_failure=on_failure
        )

        return typing.cast(None, jsii.invoke(self, "putNotificationSettings", [value]))

    @jsii.member(jsii_name="putSchedule")
    def put_schedule(
        self,
        *,
        quartz_cron_expression: builtins.str,
        timezone_id: builtins.str,
    ) -> None:
        '''
        :param quartz_cron_expression: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#quartz_cron_expression DataDatabricksDataQualityMonitors#quartz_cron_expression}.
        :param timezone_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#timezone_id DataDatabricksDataQualityMonitors#timezone_id}.
        '''
        value = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule(
            quartz_cron_expression=quartz_cron_expression, timezone_id=timezone_id
        )

        return typing.cast(None, jsii.invoke(self, "putSchedule", [value]))

    @jsii.member(jsii_name="putSnapshot")
    def put_snapshot(self) -> None:
        value = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot()

        return typing.cast(None, jsii.invoke(self, "putSnapshot", [value]))

    @jsii.member(jsii_name="putTimeSeries")
    def put_time_series(
        self,
        *,
        granularities: typing.Sequence[builtins.str],
        timestamp_column: builtins.str,
    ) -> None:
        '''
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#granularities DataDatabricksDataQualityMonitors#granularities}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#timestamp_column DataDatabricksDataQualityMonitors#timestamp_column}.
        '''
        value = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries(
            granularities=granularities, timestamp_column=timestamp_column
        )

        return typing.cast(None, jsii.invoke(self, "putTimeSeries", [value]))

    @jsii.member(jsii_name="resetAssetsDir")
    def reset_assets_dir(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAssetsDir", []))

    @jsii.member(jsii_name="resetBaselineTableName")
    def reset_baseline_table_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBaselineTableName", []))

    @jsii.member(jsii_name="resetCustomMetrics")
    def reset_custom_metrics(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCustomMetrics", []))

    @jsii.member(jsii_name="resetInferenceLog")
    def reset_inference_log(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetInferenceLog", []))

    @jsii.member(jsii_name="resetNotificationSettings")
    def reset_notification_settings(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNotificationSettings", []))

    @jsii.member(jsii_name="resetSchedule")
    def reset_schedule(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSchedule", []))

    @jsii.member(jsii_name="resetSkipBuiltinDashboard")
    def reset_skip_builtin_dashboard(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSkipBuiltinDashboard", []))

    @jsii.member(jsii_name="resetSlicingExprs")
    def reset_slicing_exprs(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSlicingExprs", []))

    @jsii.member(jsii_name="resetSnapshot")
    def reset_snapshot(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSnapshot", []))

    @jsii.member(jsii_name="resetTimeSeries")
    def reset_time_series(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeSeries", []))

    @jsii.member(jsii_name="resetWarehouseId")
    def reset_warehouse_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetWarehouseId", []))

    @builtins.property
    @jsii.member(jsii_name="customMetrics")
    def custom_metrics(
        self,
    ) -> DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsList:
        return typing.cast(DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsList, jsii.get(self, "customMetrics"))

    @builtins.property
    @jsii.member(jsii_name="dashboardId")
    def dashboard_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "dashboardId"))

    @builtins.property
    @jsii.member(jsii_name="driftMetricsTableName")
    def drift_metrics_table_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "driftMetricsTableName"))

    @builtins.property
    @jsii.member(jsii_name="effectiveWarehouseId")
    def effective_warehouse_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "effectiveWarehouseId"))

    @builtins.property
    @jsii.member(jsii_name="inferenceLog")
    def inference_log(
        self,
    ) -> DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLogOutputReference:
        return typing.cast(DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLogOutputReference, jsii.get(self, "inferenceLog"))

    @builtins.property
    @jsii.member(jsii_name="latestMonitorFailureMessage")
    def latest_monitor_failure_message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "latestMonitorFailureMessage"))

    @builtins.property
    @jsii.member(jsii_name="monitoredTableName")
    def monitored_table_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "monitoredTableName"))

    @builtins.property
    @jsii.member(jsii_name="monitorVersion")
    def monitor_version(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "monitorVersion"))

    @builtins.property
    @jsii.member(jsii_name="notificationSettings")
    def notification_settings(
        self,
    ) -> DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOutputReference:
        return typing.cast(DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOutputReference, jsii.get(self, "notificationSettings"))

    @builtins.property
    @jsii.member(jsii_name="profileMetricsTableName")
    def profile_metrics_table_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "profileMetricsTableName"))

    @builtins.property
    @jsii.member(jsii_name="schedule")
    def schedule(
        self,
    ) -> "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigScheduleOutputReference":
        return typing.cast("DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigScheduleOutputReference", jsii.get(self, "schedule"))

    @builtins.property
    @jsii.member(jsii_name="snapshot")
    def snapshot(
        self,
    ) -> "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshotOutputReference":
        return typing.cast("DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshotOutputReference", jsii.get(self, "snapshot"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="timeSeries")
    def time_series(
        self,
    ) -> "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeriesOutputReference":
        return typing.cast("DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeriesOutputReference", jsii.get(self, "timeSeries"))

    @builtins.property
    @jsii.member(jsii_name="assetsDirInput")
    def assets_dir_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "assetsDirInput"))

    @builtins.property
    @jsii.member(jsii_name="baselineTableNameInput")
    def baseline_table_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "baselineTableNameInput"))

    @builtins.property
    @jsii.member(jsii_name="customMetricsInput")
    def custom_metrics_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]]], jsii.get(self, "customMetricsInput"))

    @builtins.property
    @jsii.member(jsii_name="inferenceLogInput")
    def inference_log_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog]], jsii.get(self, "inferenceLogInput"))

    @builtins.property
    @jsii.member(jsii_name="notificationSettingsInput")
    def notification_settings_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings]], jsii.get(self, "notificationSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="outputSchemaIdInput")
    def output_schema_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "outputSchemaIdInput"))

    @builtins.property
    @jsii.member(jsii_name="scheduleInput")
    def schedule_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule"]], jsii.get(self, "scheduleInput"))

    @builtins.property
    @jsii.member(jsii_name="skipBuiltinDashboardInput")
    def skip_builtin_dashboard_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "skipBuiltinDashboardInput"))

    @builtins.property
    @jsii.member(jsii_name="slicingExprsInput")
    def slicing_exprs_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "slicingExprsInput"))

    @builtins.property
    @jsii.member(jsii_name="snapshotInput")
    def snapshot_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot"]], jsii.get(self, "snapshotInput"))

    @builtins.property
    @jsii.member(jsii_name="timeSeriesInput")
    def time_series_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries"]], jsii.get(self, "timeSeriesInput"))

    @builtins.property
    @jsii.member(jsii_name="warehouseIdInput")
    def warehouse_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "warehouseIdInput"))

    @builtins.property
    @jsii.member(jsii_name="assetsDir")
    def assets_dir(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "assetsDir"))

    @assets_dir.setter
    def assets_dir(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__07b76bdfb752874d1a4fb1c0f40e01f4e5d87d6958c81f195a3d9e69e6987171)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "assetsDir", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="baselineTableName")
    def baseline_table_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "baselineTableName"))

    @baseline_table_name.setter
    def baseline_table_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c2d0dc8cd01c65271f660c66915ffb18a7ffbaff57aba51ce4c782125ff5919c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "baselineTableName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="outputSchemaId")
    def output_schema_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "outputSchemaId"))

    @output_schema_id.setter
    def output_schema_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e180ade620f95e094b6bf9eb6f56190da0b7fb899c9ec0ff087afd660923c22f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "outputSchemaId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="skipBuiltinDashboard")
    def skip_builtin_dashboard(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "skipBuiltinDashboard"))

    @skip_builtin_dashboard.setter
    def skip_builtin_dashboard(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e93288867392c658cc446d72b622307ad65ff24b00b49e4359bce38157c09a5e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "skipBuiltinDashboard", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="slicingExprs")
    def slicing_exprs(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "slicingExprs"))

    @slicing_exprs.setter
    def slicing_exprs(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__967830e36134df2ede49fed2fdebc7f4454f6f0968e54f68ade37d87804bcb5a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "slicingExprs", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="warehouseId")
    def warehouse_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "warehouseId"))

    @warehouse_id.setter
    def warehouse_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b2a285ef1b8cd588073908fd9ab5e76da3935c80ec62d71cd51f71b6c5173d3f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "warehouseId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__848ce25163914ba67839f78e04e09205ee13f9fbdd5879ad7e978ae465cd2130)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule",
    jsii_struct_bases=[],
    name_mapping={
        "quartz_cron_expression": "quartzCronExpression",
        "timezone_id": "timezoneId",
    },
)
class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule:
    def __init__(
        self,
        *,
        quartz_cron_expression: builtins.str,
        timezone_id: builtins.str,
    ) -> None:
        '''
        :param quartz_cron_expression: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#quartz_cron_expression DataDatabricksDataQualityMonitors#quartz_cron_expression}.
        :param timezone_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#timezone_id DataDatabricksDataQualityMonitors#timezone_id}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e64d9e273c978bd1e0704364b2fdb4f5e090da1f0918f916158ab82523e0f90d)
            check_type(argname="argument quartz_cron_expression", value=quartz_cron_expression, expected_type=type_hints["quartz_cron_expression"])
            check_type(argname="argument timezone_id", value=timezone_id, expected_type=type_hints["timezone_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "quartz_cron_expression": quartz_cron_expression,
            "timezone_id": timezone_id,
        }

    @builtins.property
    def quartz_cron_expression(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#quartz_cron_expression DataDatabricksDataQualityMonitors#quartz_cron_expression}.'''
        result = self._values.get("quartz_cron_expression")
        assert result is not None, "Required property 'quartz_cron_expression' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def timezone_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#timezone_id DataDatabricksDataQualityMonitors#timezone_id}.'''
        result = self._values.get("timezone_id")
        assert result is not None, "Required property 'timezone_id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigScheduleOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigScheduleOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__1440bfbc5107bb9b02b5d561c31d6f2297fb7d4e2290c4e537de6a40778c588a)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="pauseStatus")
    def pause_status(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "pauseStatus"))

    @builtins.property
    @jsii.member(jsii_name="quartzCronExpressionInput")
    def quartz_cron_expression_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "quartzCronExpressionInput"))

    @builtins.property
    @jsii.member(jsii_name="timezoneIdInput")
    def timezone_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "timezoneIdInput"))

    @builtins.property
    @jsii.member(jsii_name="quartzCronExpression")
    def quartz_cron_expression(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "quartzCronExpression"))

    @quartz_cron_expression.setter
    def quartz_cron_expression(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2edfa4b44a3a993e4ea632fec2d350dd9ec8b224d7800da2fbc1800faa058e7b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "quartzCronExpression", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timezoneId")
    def timezone_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timezoneId"))

    @timezone_id.setter
    def timezone_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d0341016a65554ef4a019d27e333a7e661d869941ac4719bdf1f7d6799925dcd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timezoneId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e6e0d1b713a0e5fe7ccecab621f84a72fd3c1d9feb4885d7e86b0371d1d4ce5d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot",
    jsii_struct_bases=[],
    name_mapping={},
)
class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot:
    def __init__(self) -> None:
        self._values: typing.Dict[builtins.str, typing.Any] = {}

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshotOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshotOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__f450939d09796158edf0d9619e95d541b1a3fdb5bf8c2ee97d4dd761513870e7)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f1edfabd1b2f47749e964a17a19fce214a90fe7742c47964820fe5a1f33fd5c4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries",
    jsii_struct_bases=[],
    name_mapping={
        "granularities": "granularities",
        "timestamp_column": "timestampColumn",
    },
)
class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries:
    def __init__(
        self,
        *,
        granularities: typing.Sequence[builtins.str],
        timestamp_column: builtins.str,
    ) -> None:
        '''
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#granularities DataDatabricksDataQualityMonitors#granularities}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#timestamp_column DataDatabricksDataQualityMonitors#timestamp_column}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a8735596eb0f40f97e80ff4f6a56b445a62c96b4304efb44f3b60b5d9767e7ac)
            check_type(argname="argument granularities", value=granularities, expected_type=type_hints["granularities"])
            check_type(argname="argument timestamp_column", value=timestamp_column, expected_type=type_hints["timestamp_column"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "granularities": granularities,
            "timestamp_column": timestamp_column,
        }

    @builtins.property
    def granularities(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#granularities DataDatabricksDataQualityMonitors#granularities}.'''
        result = self._values.get("granularities")
        assert result is not None, "Required property 'granularities' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def timestamp_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#timestamp_column DataDatabricksDataQualityMonitors#timestamp_column}.'''
        result = self._values.get("timestamp_column")
        assert result is not None, "Required property 'timestamp_column' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeriesOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeriesOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__91224f1e293def4eb84ed4485458270beaa6c8fb77888075645945f7e84125b1)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="granularitiesInput")
    def granularities_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "granularitiesInput"))

    @builtins.property
    @jsii.member(jsii_name="timestampColumnInput")
    def timestamp_column_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "timestampColumnInput"))

    @builtins.property
    @jsii.member(jsii_name="granularities")
    def granularities(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "granularities"))

    @granularities.setter
    def granularities(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ae74da4c7dc55b0133d3032003637267811070ed3f47c8772f21fbe9c33f453e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "granularities", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timestampColumn")
    def timestamp_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timestampColumn"))

    @timestamp_column.setter
    def timestamp_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6087e9b259065a95a1043e27555110a31e80f9c9c06407a7c683e08f668a5ab0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timestampColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__640cd08dc46424f7e528222a5e07a1bc8cf7baa58a6e1d1ae6fc70e2198e33de)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksDataQualityMonitorsMonitorsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__064a1f170484d2b4f1627d379b7091817c99b284109b750b539a4f97f9f43d7a)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DataDatabricksDataQualityMonitorsMonitorsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9abe5b0e3c844553b70f0d0c8b24431cf40f22360a81dd163de4bfaf92074b46)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DataDatabricksDataQualityMonitorsMonitorsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__383b544e2f6dcd812262701e1dd90dd9b0ed471d5060b01c0db73f06d1698e03)
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
            type_hints = typing.get_type_hints(_typecheckingstub__a99d7d57769fc9d6763215bed015c26e69421d6d322e61798978408a79d1b446)
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
            type_hints = typing.get_type_hints(_typecheckingstub__26bbf3a211a7920e18106009d201e2f9cd34a5b357b0fcc1c23d53e2aa94c7ed)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitors]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitors]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitors]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0eed8c15efc79cc10774b1428ed9241716c47659685689ac9eb8671f192c8e19)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksDataQualityMonitorsMonitorsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitors.DataDatabricksDataQualityMonitorsMonitorsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__bb50bc23aa68463011f0b2467b74e08638a3d3f62d48067c8dfb0e3fa2048455)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="putAnomalyDetectionConfig")
    def put_anomaly_detection_config(self) -> None:
        value = DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig()

        return typing.cast(None, jsii.invoke(self, "putAnomalyDetectionConfig", [value]))

    @jsii.member(jsii_name="putDataProfilingConfig")
    def put_data_profiling_config(
        self,
        *,
        output_schema_id: builtins.str,
        assets_dir: typing.Optional[builtins.str] = None,
        baseline_table_name: typing.Optional[builtins.str] = None,
        custom_metrics: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]]] = None,
        inference_log: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog, typing.Dict[builtins.str, typing.Any]]] = None,
        notification_settings: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings, typing.Dict[builtins.str, typing.Any]]] = None,
        schedule: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule, typing.Dict[builtins.str, typing.Any]]] = None,
        skip_builtin_dashboard: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        slicing_exprs: typing.Optional[typing.Sequence[builtins.str]] = None,
        snapshot: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot, typing.Dict[builtins.str, typing.Any]]] = None,
        time_series: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries, typing.Dict[builtins.str, typing.Any]]] = None,
        warehouse_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param output_schema_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#output_schema_id DataDatabricksDataQualityMonitors#output_schema_id}.
        :param assets_dir: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#assets_dir DataDatabricksDataQualityMonitors#assets_dir}.
        :param baseline_table_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#baseline_table_name DataDatabricksDataQualityMonitors#baseline_table_name}.
        :param custom_metrics: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#custom_metrics DataDatabricksDataQualityMonitors#custom_metrics}.
        :param inference_log: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#inference_log DataDatabricksDataQualityMonitors#inference_log}.
        :param notification_settings: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#notification_settings DataDatabricksDataQualityMonitors#notification_settings}.
        :param schedule: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#schedule DataDatabricksDataQualityMonitors#schedule}.
        :param skip_builtin_dashboard: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#skip_builtin_dashboard DataDatabricksDataQualityMonitors#skip_builtin_dashboard}.
        :param slicing_exprs: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#slicing_exprs DataDatabricksDataQualityMonitors#slicing_exprs}.
        :param snapshot: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#snapshot DataDatabricksDataQualityMonitors#snapshot}.
        :param time_series: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#time_series DataDatabricksDataQualityMonitors#time_series}.
        :param warehouse_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitors#warehouse_id DataDatabricksDataQualityMonitors#warehouse_id}.
        '''
        value = DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig(
            output_schema_id=output_schema_id,
            assets_dir=assets_dir,
            baseline_table_name=baseline_table_name,
            custom_metrics=custom_metrics,
            inference_log=inference_log,
            notification_settings=notification_settings,
            schedule=schedule,
            skip_builtin_dashboard=skip_builtin_dashboard,
            slicing_exprs=slicing_exprs,
            snapshot=snapshot,
            time_series=time_series,
            warehouse_id=warehouse_id,
        )

        return typing.cast(None, jsii.invoke(self, "putDataProfilingConfig", [value]))

    @jsii.member(jsii_name="resetAnomalyDetectionConfig")
    def reset_anomaly_detection_config(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAnomalyDetectionConfig", []))

    @jsii.member(jsii_name="resetDataProfilingConfig")
    def reset_data_profiling_config(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDataProfilingConfig", []))

    @builtins.property
    @jsii.member(jsii_name="anomalyDetectionConfig")
    def anomaly_detection_config(
        self,
    ) -> DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfigOutputReference:
        return typing.cast(DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfigOutputReference, jsii.get(self, "anomalyDetectionConfig"))

    @builtins.property
    @jsii.member(jsii_name="dataProfilingConfig")
    def data_profiling_config(
        self,
    ) -> DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigOutputReference:
        return typing.cast(DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigOutputReference, jsii.get(self, "dataProfilingConfig"))

    @builtins.property
    @jsii.member(jsii_name="anomalyDetectionConfigInput")
    def anomaly_detection_config_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig]], jsii.get(self, "anomalyDetectionConfigInput"))

    @builtins.property
    @jsii.member(jsii_name="dataProfilingConfigInput")
    def data_profiling_config_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig]], jsii.get(self, "dataProfilingConfigInput"))

    @builtins.property
    @jsii.member(jsii_name="objectIdInput")
    def object_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "objectIdInput"))

    @builtins.property
    @jsii.member(jsii_name="objectTypeInput")
    def object_type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "objectTypeInput"))

    @builtins.property
    @jsii.member(jsii_name="objectId")
    def object_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "objectId"))

    @object_id.setter
    def object_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d63d5df1047a67d91cc693e8f83c009a27898d76639b1f4481c085b118aa0196)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "objectId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="objectType")
    def object_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "objectType"))

    @object_type.setter
    def object_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__367b90498353848cb1f20d63277aa19301089bf4f2c7d82e243207190b27710b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "objectType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[DataDatabricksDataQualityMonitorsMonitors]:
        return typing.cast(typing.Optional[DataDatabricksDataQualityMonitorsMonitors], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DataDatabricksDataQualityMonitorsMonitors],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__55d68a0438746aa0d84eee8167f0d5f2014958f0d71740aa76928c363f593862)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "DataDatabricksDataQualityMonitors",
    "DataDatabricksDataQualityMonitorsConfig",
    "DataDatabricksDataQualityMonitorsMonitors",
    "DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig",
    "DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfigOutputReference",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsList",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetricsOutputReference",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLogOutputReference",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailureOutputReference",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOutputReference",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigOutputReference",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigScheduleOutputReference",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshotOutputReference",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries",
    "DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeriesOutputReference",
    "DataDatabricksDataQualityMonitorsMonitorsList",
    "DataDatabricksDataQualityMonitorsMonitorsOutputReference",
]

publication.publish()

def _typecheckingstub__154dade6af038db7bb1eda30385d3b11e9d6af12838cc0eeaa8f965caf881523(
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

def _typecheckingstub__5c03e8623a1aeeaa33e39f66f14d9e628dbc1350488e23537251e55c3c699c54(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a0c39bef64cd26e5ec92a6d3bb76f6d5071db47b6e4e68341dac1548ef3a444(
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

def _typecheckingstub__27c5673a47dc6e51ec5e77da087d1bba77110369856032e834af2ee81e236c3c(
    *,
    object_id: builtins.str,
    object_type: builtins.str,
    anomaly_detection_config: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    data_profiling_config: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__15995d3f58ec3dc46f49bfb36da09202db2935098683ea6fd4c09533fa2f9397(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40679cb4785eee535f14c5054827404848270f05dc6e3e0fed0c745b41abe0ad(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsAnomalyDetectionConfig]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4f9e550992efbe9cf34eb7030b663ae7d5a9826f1a0a4f722aa669a91f40254c(
    *,
    output_schema_id: builtins.str,
    assets_dir: typing.Optional[builtins.str] = None,
    baseline_table_name: typing.Optional[builtins.str] = None,
    custom_metrics: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]]] = None,
    inference_log: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog, typing.Dict[builtins.str, typing.Any]]] = None,
    notification_settings: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    schedule: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule, typing.Dict[builtins.str, typing.Any]]] = None,
    skip_builtin_dashboard: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    slicing_exprs: typing.Optional[typing.Sequence[builtins.str]] = None,
    snapshot: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot, typing.Dict[builtins.str, typing.Any]]] = None,
    time_series: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries, typing.Dict[builtins.str, typing.Any]]] = None,
    warehouse_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b5b82761193b3f7fc04c110b089e6d48012a981cd8c52a5e0722ffafdb0ba107(
    *,
    definition: builtins.str,
    input_columns: typing.Sequence[builtins.str],
    name: builtins.str,
    output_data_type: builtins.str,
    type: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4e2567f848d619db2d489a8456777d44f70e166c16f7b34845b888fa9e5d7245(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9275dae5cbcd292df3e8164e13f24f0cad939de29898107ec8f799d96dcdfba5(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e8b81a0d0c89996309f7669090431befb8e1bbfb2b61c7e645148a10614003df(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5fea723a8ababa81cce463577ba42448c960603a27f45ca973a41b92743b4ced(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f8ee0f72cbdb4ac3c259df1a67c9af29c259416034c57bd65541f9f7f3b6e2b3(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f6057b25dbcdf802ee8a22669f203ecf22fc6c057c85ffdd5e4c60fcccd84f2f(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__25aef9f6a9414c1be65ed1e351cebf76bfe3813d18109d5920f2cc7b8a3502ae(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4eca1efd5a944255bdbf82b3ed1725efa3d52800b34396ea2c4099295846f900(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__82cee604570b665cd219a5a5238dde3d8a7f9cbe27e1d7c8fe1cbdd30947c11c(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7cbd53c766e2139ddb1b2da4aa17e2d84631b6d8330e31ee1cd6817ca1491e87(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ada885030f9cdfa4d35ec7713b210b7d51d463f9e73df93e94f071a2b51290bb(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__868d931cd8653b1c9cb9857ec340499388f8cd79c93864530b9627c7f832925d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13d0cdb079f2e8c7e7288da658ff02465030ae6f30e18c1d8140aa0f0ea9dbc9(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a8e5dced866f6a2d8b51f1cefbea8880af7c8ab47164174c8c2ef322462b9f95(
    *,
    granularities: typing.Sequence[builtins.str],
    model_id_column: builtins.str,
    prediction_column: builtins.str,
    problem_type: builtins.str,
    timestamp_column: builtins.str,
    label_column: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__91562d2d9dbc64d20722be846eedb695653b95a45948da367c48086448b2c573(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3240f11e735430b3293de9b24c55a4c4bd3c2b949a4882dcd91918e3a678b818(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__017ee2201a95bf41e75bb116f3a58f5bb58142c9999924770660fad48e9bdaa2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7c1df33144565bd064aeced99207b8c3f5afeca0180e6d0634bdf49346daf38b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40aa5e31ee24c56f2c7d62bdc41cf627724d1a8b810901178d9af62777a3b5ad(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__839c43673bb890f95f59987b531e2b0d0ee67177e0dbb9154f9f4a5008d779ee(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a4ecd7b975f076faa7658c4eb2799eeb6b43a55f601c4c9af7e75bf0df9c719a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__22cbba345d2f0f14ee894b493900b608cc899fe792de1d79b87b7f8b33811f80(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigInferenceLog]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eac39fee1d1f03820a50785c9c9d9509636f6ec21544336871d11f6d1c21c13a(
    *,
    on_failure: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f28c2f3b0c0325b14f71d371d571f1217202482e965f2cc88a4db3a8102feee0(
    *,
    email_addresses: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__679db1bbff201c7928e8c867526509a54dbd3de66e8783dc12f840b994d963f2(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b445b78ef8f7c1fb4949763a4ce79c07b720f94b9c52dc8c795fb26dbcd64674(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a9418c905597f4935996e654325835c8e893a4ab74ecbafcca4b2d93dae96071(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettingsOnFailure]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bb8f8add8476361efbb9f2c5bcf02d9f442ab2bf4235499dce73f02737bdd795(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1cee549e0dba77c616813fcec52135e109a96fee3c9db383230d5665943c2644(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigNotificationSettings]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ce8ac9d8bcb3be79c734e127a70ea0a074fd9e86f38d3728f6d85e6af3754532(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__00b3f10f8d349902f33eb68ca83cca98842c34d15ccc8bce16492cc12c6fadb5(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__07b76bdfb752874d1a4fb1c0f40e01f4e5d87d6958c81f195a3d9e69e6987171(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c2d0dc8cd01c65271f660c66915ffb18a7ffbaff57aba51ce4c782125ff5919c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e180ade620f95e094b6bf9eb6f56190da0b7fb899c9ec0ff087afd660923c22f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e93288867392c658cc446d72b622307ad65ff24b00b49e4359bce38157c09a5e(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__967830e36134df2ede49fed2fdebc7f4454f6f0968e54f68ade37d87804bcb5a(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b2a285ef1b8cd588073908fd9ab5e76da3935c80ec62d71cd51f71b6c5173d3f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__848ce25163914ba67839f78e04e09205ee13f9fbdd5879ad7e978ae465cd2130(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfig]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e64d9e273c978bd1e0704364b2fdb4f5e090da1f0918f916158ab82523e0f90d(
    *,
    quartz_cron_expression: builtins.str,
    timezone_id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1440bfbc5107bb9b02b5d561c31d6f2297fb7d4e2290c4e537de6a40778c588a(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2edfa4b44a3a993e4ea632fec2d350dd9ec8b224d7800da2fbc1800faa058e7b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d0341016a65554ef4a019d27e333a7e661d869941ac4719bdf1f7d6799925dcd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e6e0d1b713a0e5fe7ccecab621f84a72fd3c1d9feb4885d7e86b0371d1d4ce5d(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSchedule]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f450939d09796158edf0d9619e95d541b1a3fdb5bf8c2ee97d4dd761513870e7(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f1edfabd1b2f47749e964a17a19fce214a90fe7742c47964820fe5a1f33fd5c4(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigSnapshot]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a8735596eb0f40f97e80ff4f6a56b445a62c96b4304efb44f3b60b5d9767e7ac(
    *,
    granularities: typing.Sequence[builtins.str],
    timestamp_column: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__91224f1e293def4eb84ed4485458270beaa6c8fb77888075645945f7e84125b1(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ae74da4c7dc55b0133d3032003637267811070ed3f47c8772f21fbe9c33f453e(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6087e9b259065a95a1043e27555110a31e80f9c9c06407a7c683e08f668a5ab0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__640cd08dc46424f7e528222a5e07a1bc8cf7baa58a6e1d1ae6fc70e2198e33de(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorsMonitorsDataProfilingConfigTimeSeries]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__064a1f170484d2b4f1627d379b7091817c99b284109b750b539a4f97f9f43d7a(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9abe5b0e3c844553b70f0d0c8b24431cf40f22360a81dd163de4bfaf92074b46(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__383b544e2f6dcd812262701e1dd90dd9b0ed471d5060b01c0db73f06d1698e03(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a99d7d57769fc9d6763215bed015c26e69421d6d322e61798978408a79d1b446(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26bbf3a211a7920e18106009d201e2f9cd34a5b357b0fcc1c23d53e2aa94c7ed(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0eed8c15efc79cc10774b1428ed9241716c47659685689ac9eb8671f192c8e19(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorsMonitors]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bb50bc23aa68463011f0b2467b74e08638a3d3f62d48067c8dfb0e3fa2048455(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d63d5df1047a67d91cc693e8f83c009a27898d76639b1f4481c085b118aa0196(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__367b90498353848cb1f20d63277aa19301089bf4f2c7d82e243207190b27710b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__55d68a0438746aa0d84eee8167f0d5f2014958f0d71740aa76928c363f593862(
    value: typing.Optional[DataDatabricksDataQualityMonitorsMonitors],
) -> None:
    """Type checking stubs"""
    pass
