r'''
# `databricks_data_quality_monitor`

Refer to the Terraform Registry for docs: [`databricks_data_quality_monitor`](https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor).
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


class DataQualityMonitor(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitor",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor databricks_data_quality_monitor}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        object_id: builtins.str,
        object_type: builtins.str,
        anomaly_detection_config: typing.Optional[typing.Union["DataQualityMonitorAnomalyDetectionConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        data_profiling_config: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor databricks_data_quality_monitor} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param object_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#object_id DataQualityMonitor#object_id}.
        :param object_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#object_type DataQualityMonitor#object_type}.
        :param anomaly_detection_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#anomaly_detection_config DataQualityMonitor#anomaly_detection_config}.
        :param data_profiling_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#data_profiling_config DataQualityMonitor#data_profiling_config}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__93a2dde71b2d3477f10d1613b50beffa0273b41466dbc185ad2c58d0231df8df)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = DataQualityMonitorConfig(
            object_id=object_id,
            object_type=object_type,
            anomaly_detection_config=anomaly_detection_config,
            data_profiling_config=data_profiling_config,
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
        '''Generates CDKTF code for importing a DataQualityMonitor resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DataQualityMonitor to import.
        :param import_from_id: The id of the existing DataQualityMonitor that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DataQualityMonitor to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e484aac5e0b48a303d3f4a764e6d2cd68723109b1cfa64758f3ac10e6ca3ac5a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putAnomalyDetectionConfig")
    def put_anomaly_detection_config(self) -> None:
        value = DataQualityMonitorAnomalyDetectionConfig()

        return typing.cast(None, jsii.invoke(self, "putAnomalyDetectionConfig", [value]))

    @jsii.member(jsii_name="putDataProfilingConfig")
    def put_data_profiling_config(
        self,
        *,
        output_schema_id: builtins.str,
        assets_dir: typing.Optional[builtins.str] = None,
        baseline_table_name: typing.Optional[builtins.str] = None,
        custom_metrics: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataQualityMonitorDataProfilingConfigCustomMetrics", typing.Dict[builtins.str, typing.Any]]]]] = None,
        inference_log: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigInferenceLog", typing.Dict[builtins.str, typing.Any]]] = None,
        notification_settings: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigNotificationSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        schedule: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigSchedule", typing.Dict[builtins.str, typing.Any]]] = None,
        skip_builtin_dashboard: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        slicing_exprs: typing.Optional[typing.Sequence[builtins.str]] = None,
        snapshot: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigSnapshot", typing.Dict[builtins.str, typing.Any]]] = None,
        time_series: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigTimeSeries", typing.Dict[builtins.str, typing.Any]]] = None,
        warehouse_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param output_schema_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#output_schema_id DataQualityMonitor#output_schema_id}.
        :param assets_dir: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#assets_dir DataQualityMonitor#assets_dir}.
        :param baseline_table_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#baseline_table_name DataQualityMonitor#baseline_table_name}.
        :param custom_metrics: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#custom_metrics DataQualityMonitor#custom_metrics}.
        :param inference_log: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#inference_log DataQualityMonitor#inference_log}.
        :param notification_settings: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#notification_settings DataQualityMonitor#notification_settings}.
        :param schedule: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#schedule DataQualityMonitor#schedule}.
        :param skip_builtin_dashboard: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#skip_builtin_dashboard DataQualityMonitor#skip_builtin_dashboard}.
        :param slicing_exprs: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#slicing_exprs DataQualityMonitor#slicing_exprs}.
        :param snapshot: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#snapshot DataQualityMonitor#snapshot}.
        :param time_series: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#time_series DataQualityMonitor#time_series}.
        :param warehouse_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#warehouse_id DataQualityMonitor#warehouse_id}.
        '''
        value = DataQualityMonitorDataProfilingConfig(
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
    @jsii.member(jsii_name="anomalyDetectionConfig")
    def anomaly_detection_config(
        self,
    ) -> "DataQualityMonitorAnomalyDetectionConfigOutputReference":
        return typing.cast("DataQualityMonitorAnomalyDetectionConfigOutputReference", jsii.get(self, "anomalyDetectionConfig"))

    @builtins.property
    @jsii.member(jsii_name="dataProfilingConfig")
    def data_profiling_config(
        self,
    ) -> "DataQualityMonitorDataProfilingConfigOutputReference":
        return typing.cast("DataQualityMonitorDataProfilingConfigOutputReference", jsii.get(self, "dataProfilingConfig"))

    @builtins.property
    @jsii.member(jsii_name="anomalyDetectionConfigInput")
    def anomaly_detection_config_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorAnomalyDetectionConfig"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorAnomalyDetectionConfig"]], jsii.get(self, "anomalyDetectionConfigInput"))

    @builtins.property
    @jsii.member(jsii_name="dataProfilingConfigInput")
    def data_profiling_config_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorDataProfilingConfig"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorDataProfilingConfig"]], jsii.get(self, "dataProfilingConfigInput"))

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
            type_hints = typing.get_type_hints(_typecheckingstub__ac8a2113562f156627ca63ae941243ab8e08f4ecf5fdc181e230f3f7e416144e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "objectId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="objectType")
    def object_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "objectType"))

    @object_type.setter
    def object_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__257e204f98cd65e946417c07854a3cc826581c1b571b3ec88b512998ff4543f2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "objectType", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorAnomalyDetectionConfig",
    jsii_struct_bases=[],
    name_mapping={},
)
class DataQualityMonitorAnomalyDetectionConfig:
    def __init__(self) -> None:
        self._values: typing.Dict[builtins.str, typing.Any] = {}

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorAnomalyDetectionConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataQualityMonitorAnomalyDetectionConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorAnomalyDetectionConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__6775775e9f0f4933f9e70555eee420e3c462f43dd9330aae9ce5c607ab44307f)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorAnomalyDetectionConfig]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorAnomalyDetectionConfig]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorAnomalyDetectionConfig]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a94b1727629fac58e164b593e75070ee47bd807d96e9e061e50c4f41aadcd0be)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "object_id": "objectId",
        "object_type": "objectType",
        "anomaly_detection_config": "anomalyDetectionConfig",
        "data_profiling_config": "dataProfilingConfig",
    },
)
class DataQualityMonitorConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        object_id: builtins.str,
        object_type: builtins.str,
        anomaly_detection_config: typing.Optional[typing.Union[DataQualityMonitorAnomalyDetectionConfig, typing.Dict[builtins.str, typing.Any]]] = None,
        data_profiling_config: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfig", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param object_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#object_id DataQualityMonitor#object_id}.
        :param object_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#object_type DataQualityMonitor#object_type}.
        :param anomaly_detection_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#anomaly_detection_config DataQualityMonitor#anomaly_detection_config}.
        :param data_profiling_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#data_profiling_config DataQualityMonitor#data_profiling_config}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(anomaly_detection_config, dict):
            anomaly_detection_config = DataQualityMonitorAnomalyDetectionConfig(**anomaly_detection_config)
        if isinstance(data_profiling_config, dict):
            data_profiling_config = DataQualityMonitorDataProfilingConfig(**data_profiling_config)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6072e659e22ef3e05826e5ab213e90bbdf88a82db6371b8b535cb74fcf6f3b9b)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument object_id", value=object_id, expected_type=type_hints["object_id"])
            check_type(argname="argument object_type", value=object_type, expected_type=type_hints["object_type"])
            check_type(argname="argument anomaly_detection_config", value=anomaly_detection_config, expected_type=type_hints["anomaly_detection_config"])
            check_type(argname="argument data_profiling_config", value=data_profiling_config, expected_type=type_hints["data_profiling_config"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "object_id": object_id,
            "object_type": object_type,
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
        if anomaly_detection_config is not None:
            self._values["anomaly_detection_config"] = anomaly_detection_config
        if data_profiling_config is not None:
            self._values["data_profiling_config"] = data_profiling_config

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
    def object_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#object_id DataQualityMonitor#object_id}.'''
        result = self._values.get("object_id")
        assert result is not None, "Required property 'object_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def object_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#object_type DataQualityMonitor#object_type}.'''
        result = self._values.get("object_type")
        assert result is not None, "Required property 'object_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def anomaly_detection_config(
        self,
    ) -> typing.Optional[DataQualityMonitorAnomalyDetectionConfig]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#anomaly_detection_config DataQualityMonitor#anomaly_detection_config}.'''
        result = self._values.get("anomaly_detection_config")
        return typing.cast(typing.Optional[DataQualityMonitorAnomalyDetectionConfig], result)

    @builtins.property
    def data_profiling_config(
        self,
    ) -> typing.Optional["DataQualityMonitorDataProfilingConfig"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#data_profiling_config DataQualityMonitor#data_profiling_config}.'''
        result = self._values.get("data_profiling_config")
        return typing.cast(typing.Optional["DataQualityMonitorDataProfilingConfig"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfig",
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
class DataQualityMonitorDataProfilingConfig:
    def __init__(
        self,
        *,
        output_schema_id: builtins.str,
        assets_dir: typing.Optional[builtins.str] = None,
        baseline_table_name: typing.Optional[builtins.str] = None,
        custom_metrics: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataQualityMonitorDataProfilingConfigCustomMetrics", typing.Dict[builtins.str, typing.Any]]]]] = None,
        inference_log: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigInferenceLog", typing.Dict[builtins.str, typing.Any]]] = None,
        notification_settings: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigNotificationSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        schedule: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigSchedule", typing.Dict[builtins.str, typing.Any]]] = None,
        skip_builtin_dashboard: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        slicing_exprs: typing.Optional[typing.Sequence[builtins.str]] = None,
        snapshot: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigSnapshot", typing.Dict[builtins.str, typing.Any]]] = None,
        time_series: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigTimeSeries", typing.Dict[builtins.str, typing.Any]]] = None,
        warehouse_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param output_schema_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#output_schema_id DataQualityMonitor#output_schema_id}.
        :param assets_dir: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#assets_dir DataQualityMonitor#assets_dir}.
        :param baseline_table_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#baseline_table_name DataQualityMonitor#baseline_table_name}.
        :param custom_metrics: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#custom_metrics DataQualityMonitor#custom_metrics}.
        :param inference_log: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#inference_log DataQualityMonitor#inference_log}.
        :param notification_settings: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#notification_settings DataQualityMonitor#notification_settings}.
        :param schedule: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#schedule DataQualityMonitor#schedule}.
        :param skip_builtin_dashboard: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#skip_builtin_dashboard DataQualityMonitor#skip_builtin_dashboard}.
        :param slicing_exprs: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#slicing_exprs DataQualityMonitor#slicing_exprs}.
        :param snapshot: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#snapshot DataQualityMonitor#snapshot}.
        :param time_series: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#time_series DataQualityMonitor#time_series}.
        :param warehouse_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#warehouse_id DataQualityMonitor#warehouse_id}.
        '''
        if isinstance(inference_log, dict):
            inference_log = DataQualityMonitorDataProfilingConfigInferenceLog(**inference_log)
        if isinstance(notification_settings, dict):
            notification_settings = DataQualityMonitorDataProfilingConfigNotificationSettings(**notification_settings)
        if isinstance(schedule, dict):
            schedule = DataQualityMonitorDataProfilingConfigSchedule(**schedule)
        if isinstance(snapshot, dict):
            snapshot = DataQualityMonitorDataProfilingConfigSnapshot(**snapshot)
        if isinstance(time_series, dict):
            time_series = DataQualityMonitorDataProfilingConfigTimeSeries(**time_series)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7c7f9557d1ebfb0bbd463a51a9edad7b45e14e46995eb7ab3a60ecd1c912e42c)
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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#output_schema_id DataQualityMonitor#output_schema_id}.'''
        result = self._values.get("output_schema_id")
        assert result is not None, "Required property 'output_schema_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def assets_dir(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#assets_dir DataQualityMonitor#assets_dir}.'''
        result = self._values.get("assets_dir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def baseline_table_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#baseline_table_name DataQualityMonitor#baseline_table_name}.'''
        result = self._values.get("baseline_table_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def custom_metrics(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataQualityMonitorDataProfilingConfigCustomMetrics"]]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#custom_metrics DataQualityMonitor#custom_metrics}.'''
        result = self._values.get("custom_metrics")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataQualityMonitorDataProfilingConfigCustomMetrics"]]], result)

    @builtins.property
    def inference_log(
        self,
    ) -> typing.Optional["DataQualityMonitorDataProfilingConfigInferenceLog"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#inference_log DataQualityMonitor#inference_log}.'''
        result = self._values.get("inference_log")
        return typing.cast(typing.Optional["DataQualityMonitorDataProfilingConfigInferenceLog"], result)

    @builtins.property
    def notification_settings(
        self,
    ) -> typing.Optional["DataQualityMonitorDataProfilingConfigNotificationSettings"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#notification_settings DataQualityMonitor#notification_settings}.'''
        result = self._values.get("notification_settings")
        return typing.cast(typing.Optional["DataQualityMonitorDataProfilingConfigNotificationSettings"], result)

    @builtins.property
    def schedule(
        self,
    ) -> typing.Optional["DataQualityMonitorDataProfilingConfigSchedule"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#schedule DataQualityMonitor#schedule}.'''
        result = self._values.get("schedule")
        return typing.cast(typing.Optional["DataQualityMonitorDataProfilingConfigSchedule"], result)

    @builtins.property
    def skip_builtin_dashboard(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#skip_builtin_dashboard DataQualityMonitor#skip_builtin_dashboard}.'''
        result = self._values.get("skip_builtin_dashboard")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def slicing_exprs(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#slicing_exprs DataQualityMonitor#slicing_exprs}.'''
        result = self._values.get("slicing_exprs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def snapshot(
        self,
    ) -> typing.Optional["DataQualityMonitorDataProfilingConfigSnapshot"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#snapshot DataQualityMonitor#snapshot}.'''
        result = self._values.get("snapshot")
        return typing.cast(typing.Optional["DataQualityMonitorDataProfilingConfigSnapshot"], result)

    @builtins.property
    def time_series(
        self,
    ) -> typing.Optional["DataQualityMonitorDataProfilingConfigTimeSeries"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#time_series DataQualityMonitor#time_series}.'''
        result = self._values.get("time_series")
        return typing.cast(typing.Optional["DataQualityMonitorDataProfilingConfigTimeSeries"], result)

    @builtins.property
    def warehouse_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#warehouse_id DataQualityMonitor#warehouse_id}.'''
        result = self._values.get("warehouse_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorDataProfilingConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigCustomMetrics",
    jsii_struct_bases=[],
    name_mapping={
        "definition": "definition",
        "input_columns": "inputColumns",
        "name": "name",
        "output_data_type": "outputDataType",
        "type": "type",
    },
)
class DataQualityMonitorDataProfilingConfigCustomMetrics:
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
        :param definition: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#definition DataQualityMonitor#definition}.
        :param input_columns: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#input_columns DataQualityMonitor#input_columns}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#name DataQualityMonitor#name}.
        :param output_data_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#output_data_type DataQualityMonitor#output_data_type}.
        :param type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#type DataQualityMonitor#type}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__395c467e09c05f489f280e481cc62098cb3718112c50e467802feb1424b57d0c)
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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#definition DataQualityMonitor#definition}.'''
        result = self._values.get("definition")
        assert result is not None, "Required property 'definition' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def input_columns(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#input_columns DataQualityMonitor#input_columns}.'''
        result = self._values.get("input_columns")
        assert result is not None, "Required property 'input_columns' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#name DataQualityMonitor#name}.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def output_data_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#output_data_type DataQualityMonitor#output_data_type}.'''
        result = self._values.get("output_data_type")
        assert result is not None, "Required property 'output_data_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#type DataQualityMonitor#type}.'''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorDataProfilingConfigCustomMetrics(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataQualityMonitorDataProfilingConfigCustomMetricsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigCustomMetricsList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__c74019bfe0e111a145be2cd6e2aaa51965ec6b2a6abba0ea7d6e9b457cf8028b)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DataQualityMonitorDataProfilingConfigCustomMetricsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__acaef86f557672f34a82995f1d8362497104feb255827deac524969a53e6c179)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DataQualityMonitorDataProfilingConfigCustomMetricsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__84a51f760bcb9bbb260d8014047ccf4f51dcfe6e3ca9354e67ac667bb6b1dd17)
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
            type_hints = typing.get_type_hints(_typecheckingstub__f4b85ee14d8c8330c949ba7683fb87b08773ba9ffe6b75a8b65fdcc58309d442)
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
            type_hints = typing.get_type_hints(_typecheckingstub__7ab1ba8825c76f2d9ac70aee668bedfd01efe0b4a2bfead74fd5a6c03bd93383)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataQualityMonitorDataProfilingConfigCustomMetrics]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataQualityMonitorDataProfilingConfigCustomMetrics]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataQualityMonitorDataProfilingConfigCustomMetrics]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__561badf0a24f30ef982077a6cecebc8276ea6405753a322bfb0538125390e6be)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataQualityMonitorDataProfilingConfigCustomMetricsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigCustomMetricsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__78a750e07d07f014d297a5cddf98d6ce4ed37bcd2473baa242bed4d0412fc2a2)
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
            type_hints = typing.get_type_hints(_typecheckingstub__b00df402169e3c85645b536e454d81ae28a0090e2e9ab4ac355e1fcbab5ff303)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "definition", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="inputColumns")
    def input_columns(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "inputColumns"))

    @input_columns.setter
    def input_columns(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f818e2d04db9773e009b187f965feddc5c9a97bce707777d8d66ea41b180aa6e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "inputColumns", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bc1f3cf73f7d2d4d6374f014257c27bdd05a25edb107d2f5d920e37d2e587ca1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="outputDataType")
    def output_data_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "outputDataType"))

    @output_data_type.setter
    def output_data_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1464017eb8c203aed87f0ba35bb11cdd1f8d540e4ab2c99f72a8e9390c492c03)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "outputDataType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9dee2a32bec4abc48a6ff064d01169bb045bc5536f57830fa9ab4e69a2b39a91)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigCustomMetrics]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigCustomMetrics]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigCustomMetrics]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__98d5fa97fa8b1afd7104ae74998ba96e73f7d55918c2d7190585c75e9ec73e31)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigInferenceLog",
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
class DataQualityMonitorDataProfilingConfigInferenceLog:
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
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#granularities DataQualityMonitor#granularities}.
        :param model_id_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#model_id_column DataQualityMonitor#model_id_column}.
        :param prediction_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#prediction_column DataQualityMonitor#prediction_column}.
        :param problem_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#problem_type DataQualityMonitor#problem_type}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#timestamp_column DataQualityMonitor#timestamp_column}.
        :param label_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#label_column DataQualityMonitor#label_column}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__27a7e3c484abb6d58ccd7dbd7e7fbb89309b889833105a7c972ad851c286e338)
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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#granularities DataQualityMonitor#granularities}.'''
        result = self._values.get("granularities")
        assert result is not None, "Required property 'granularities' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def model_id_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#model_id_column DataQualityMonitor#model_id_column}.'''
        result = self._values.get("model_id_column")
        assert result is not None, "Required property 'model_id_column' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def prediction_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#prediction_column DataQualityMonitor#prediction_column}.'''
        result = self._values.get("prediction_column")
        assert result is not None, "Required property 'prediction_column' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def problem_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#problem_type DataQualityMonitor#problem_type}.'''
        result = self._values.get("problem_type")
        assert result is not None, "Required property 'problem_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def timestamp_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#timestamp_column DataQualityMonitor#timestamp_column}.'''
        result = self._values.get("timestamp_column")
        assert result is not None, "Required property 'timestamp_column' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def label_column(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#label_column DataQualityMonitor#label_column}.'''
        result = self._values.get("label_column")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorDataProfilingConfigInferenceLog(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataQualityMonitorDataProfilingConfigInferenceLogOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigInferenceLogOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__113105ca1aa4381f2b5b10cecfea4f12aa7dd17c26b1669a842fbbd98d8cdfc1)
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
            type_hints = typing.get_type_hints(_typecheckingstub__6125b1e9d100d0a07f5c591bbf958b6f4e7f2acc59accb367869be7c489a70b4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "granularities", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="labelColumn")
    def label_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "labelColumn"))

    @label_column.setter
    def label_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d506b84571a117d9453a473ddff21b6130a746d0ff76c0012672bd01c817b2e7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "labelColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="modelIdColumn")
    def model_id_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "modelIdColumn"))

    @model_id_column.setter
    def model_id_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3d7c80574095d7de7310f5580d5ed898b6765b3745ddfe1aa126f35ef9c7c456)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "modelIdColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="predictionColumn")
    def prediction_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "predictionColumn"))

    @prediction_column.setter
    def prediction_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f12e0d974b98b87b482cb416343338c2ce3d094a7492b84245484cbce9060628)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "predictionColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="problemType")
    def problem_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "problemType"))

    @problem_type.setter
    def problem_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__066ae1909b04cf402ee70999e6474f91346f12dc99cb8fa34b6be297a2e9eef8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "problemType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timestampColumn")
    def timestamp_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timestampColumn"))

    @timestamp_column.setter
    def timestamp_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ee36254dae65a23a997c1ed668da3adfc28b4a2b1ff0d517b630f31d163b0f69)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timestampColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigInferenceLog]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigInferenceLog]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigInferenceLog]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f081a260547aee035ec209d4a3f0f46a4e68c1837e03ec35629c52202576f9f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigNotificationSettings",
    jsii_struct_bases=[],
    name_mapping={"on_failure": "onFailure"},
)
class DataQualityMonitorDataProfilingConfigNotificationSettings:
    def __init__(
        self,
        *,
        on_failure: typing.Optional[typing.Union["DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param on_failure: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#on_failure DataQualityMonitor#on_failure}.
        '''
        if isinstance(on_failure, dict):
            on_failure = DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure(**on_failure)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3959457da0bb6c5651d127d0558518b6bf2c965632574f78e513f02fe8813b0f)
            check_type(argname="argument on_failure", value=on_failure, expected_type=type_hints["on_failure"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if on_failure is not None:
            self._values["on_failure"] = on_failure

    @builtins.property
    def on_failure(
        self,
    ) -> typing.Optional["DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#on_failure DataQualityMonitor#on_failure}.'''
        result = self._values.get("on_failure")
        return typing.cast(typing.Optional["DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorDataProfilingConfigNotificationSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure",
    jsii_struct_bases=[],
    name_mapping={"email_addresses": "emailAddresses"},
)
class DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure:
    def __init__(
        self,
        *,
        email_addresses: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param email_addresses: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#email_addresses DataQualityMonitor#email_addresses}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__15190d086a7944bb5dedab47b2d9e4410442ba6c71f0c3bf0158ce5b8a36b62f)
            check_type(argname="argument email_addresses", value=email_addresses, expected_type=type_hints["email_addresses"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if email_addresses is not None:
            self._values["email_addresses"] = email_addresses

    @builtins.property
    def email_addresses(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#email_addresses DataQualityMonitor#email_addresses}.'''
        result = self._values.get("email_addresses")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__310a25cd689fec65949c31d0a837c35af55d53f5aae2779e75e6ea5e5bd9bbd6)
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
            type_hints = typing.get_type_hints(_typecheckingstub__abe1b3489c92349658fd30eeb1f591c6b8a7992fa5456ba61d379f8d5bbc1165)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailAddresses", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__44355ba46d6b06abc9f670440cb6fffc53bd25ee5c44bc56a268531fd87085e6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__fe3a743f7403b61eae945b9589715767b23fed11f6b40bf7b595b7db76da3e7d)
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
        :param email_addresses: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#email_addresses DataQualityMonitor#email_addresses}.
        '''
        value = DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure(
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
    ) -> DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference:
        return typing.cast(DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference, jsii.get(self, "onFailure"))

    @builtins.property
    @jsii.member(jsii_name="onFailureInput")
    def on_failure_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]], jsii.get(self, "onFailureInput"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettings]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettings]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettings]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d3f967ee627f31df1f80de78a044e712ff9a9117e50b88acbe34f99be05e72a6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataQualityMonitorDataProfilingConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__3de385ee0019a6cae5df0d4ada16f64a75f2516351c7006b31d21250cb9471bf)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putCustomMetrics")
    def put_custom_metrics(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataQualityMonitorDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f079346fc2d4af4df6f7ea5d01c7e6d9388f4bc76d53016b65ed8f78b41d52fe)
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
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#granularities DataQualityMonitor#granularities}.
        :param model_id_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#model_id_column DataQualityMonitor#model_id_column}.
        :param prediction_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#prediction_column DataQualityMonitor#prediction_column}.
        :param problem_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#problem_type DataQualityMonitor#problem_type}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#timestamp_column DataQualityMonitor#timestamp_column}.
        :param label_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#label_column DataQualityMonitor#label_column}.
        '''
        value = DataQualityMonitorDataProfilingConfigInferenceLog(
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
        on_failure: typing.Optional[typing.Union[DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param on_failure: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#on_failure DataQualityMonitor#on_failure}.
        '''
        value = DataQualityMonitorDataProfilingConfigNotificationSettings(
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
        :param quartz_cron_expression: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#quartz_cron_expression DataQualityMonitor#quartz_cron_expression}.
        :param timezone_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#timezone_id DataQualityMonitor#timezone_id}.
        '''
        value = DataQualityMonitorDataProfilingConfigSchedule(
            quartz_cron_expression=quartz_cron_expression, timezone_id=timezone_id
        )

        return typing.cast(None, jsii.invoke(self, "putSchedule", [value]))

    @jsii.member(jsii_name="putSnapshot")
    def put_snapshot(self) -> None:
        value = DataQualityMonitorDataProfilingConfigSnapshot()

        return typing.cast(None, jsii.invoke(self, "putSnapshot", [value]))

    @jsii.member(jsii_name="putTimeSeries")
    def put_time_series(
        self,
        *,
        granularities: typing.Sequence[builtins.str],
        timestamp_column: builtins.str,
    ) -> None:
        '''
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#granularities DataQualityMonitor#granularities}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#timestamp_column DataQualityMonitor#timestamp_column}.
        '''
        value = DataQualityMonitorDataProfilingConfigTimeSeries(
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
    def custom_metrics(self) -> DataQualityMonitorDataProfilingConfigCustomMetricsList:
        return typing.cast(DataQualityMonitorDataProfilingConfigCustomMetricsList, jsii.get(self, "customMetrics"))

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
    ) -> DataQualityMonitorDataProfilingConfigInferenceLogOutputReference:
        return typing.cast(DataQualityMonitorDataProfilingConfigInferenceLogOutputReference, jsii.get(self, "inferenceLog"))

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
    ) -> DataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference:
        return typing.cast(DataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference, jsii.get(self, "notificationSettings"))

    @builtins.property
    @jsii.member(jsii_name="profileMetricsTableName")
    def profile_metrics_table_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "profileMetricsTableName"))

    @builtins.property
    @jsii.member(jsii_name="schedule")
    def schedule(
        self,
    ) -> "DataQualityMonitorDataProfilingConfigScheduleOutputReference":
        return typing.cast("DataQualityMonitorDataProfilingConfigScheduleOutputReference", jsii.get(self, "schedule"))

    @builtins.property
    @jsii.member(jsii_name="snapshot")
    def snapshot(
        self,
    ) -> "DataQualityMonitorDataProfilingConfigSnapshotOutputReference":
        return typing.cast("DataQualityMonitorDataProfilingConfigSnapshotOutputReference", jsii.get(self, "snapshot"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="timeSeries")
    def time_series(
        self,
    ) -> "DataQualityMonitorDataProfilingConfigTimeSeriesOutputReference":
        return typing.cast("DataQualityMonitorDataProfilingConfigTimeSeriesOutputReference", jsii.get(self, "timeSeries"))

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
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataQualityMonitorDataProfilingConfigCustomMetrics]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataQualityMonitorDataProfilingConfigCustomMetrics]]], jsii.get(self, "customMetricsInput"))

    @builtins.property
    @jsii.member(jsii_name="inferenceLogInput")
    def inference_log_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigInferenceLog]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigInferenceLog]], jsii.get(self, "inferenceLogInput"))

    @builtins.property
    @jsii.member(jsii_name="notificationSettingsInput")
    def notification_settings_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettings]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettings]], jsii.get(self, "notificationSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="outputSchemaIdInput")
    def output_schema_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "outputSchemaIdInput"))

    @builtins.property
    @jsii.member(jsii_name="scheduleInput")
    def schedule_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorDataProfilingConfigSchedule"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorDataProfilingConfigSchedule"]], jsii.get(self, "scheduleInput"))

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
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorDataProfilingConfigSnapshot"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorDataProfilingConfigSnapshot"]], jsii.get(self, "snapshotInput"))

    @builtins.property
    @jsii.member(jsii_name="timeSeriesInput")
    def time_series_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorDataProfilingConfigTimeSeries"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataQualityMonitorDataProfilingConfigTimeSeries"]], jsii.get(self, "timeSeriesInput"))

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
            type_hints = typing.get_type_hints(_typecheckingstub__3891532bbb62cfc5843681b40a965799816137128d8b0f750485ade244f70ec3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "assetsDir", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="baselineTableName")
    def baseline_table_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "baselineTableName"))

    @baseline_table_name.setter
    def baseline_table_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__469ee6453e48728795d907f778b3fe8c2019806be9108b5b7f8f124438a813e2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "baselineTableName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="outputSchemaId")
    def output_schema_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "outputSchemaId"))

    @output_schema_id.setter
    def output_schema_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__20b4732645d616369b7d8512654e7348aec61f39d262956312c0404da9a7a4a0)
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
            type_hints = typing.get_type_hints(_typecheckingstub__2a9d49efd450571cb8467bce55e7613fcb53a4d3a0bd9add898edfd81a49401f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "skipBuiltinDashboard", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="slicingExprs")
    def slicing_exprs(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "slicingExprs"))

    @slicing_exprs.setter
    def slicing_exprs(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__99b9df8a06ede9bd7349656ada7446910da77fb39335e182d562b6065c6ca89f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "slicingExprs", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="warehouseId")
    def warehouse_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "warehouseId"))

    @warehouse_id.setter
    def warehouse_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__572c6975987284f1b42fa57d91a62ac4dbe91604e39d73f50417a2da1075eff7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "warehouseId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfig]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfig]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfig]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a1b42cf7f0d5991e722994ef67f14b59599c02c39201c4a9f1f6e11228ad87f0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigSchedule",
    jsii_struct_bases=[],
    name_mapping={
        "quartz_cron_expression": "quartzCronExpression",
        "timezone_id": "timezoneId",
    },
)
class DataQualityMonitorDataProfilingConfigSchedule:
    def __init__(
        self,
        *,
        quartz_cron_expression: builtins.str,
        timezone_id: builtins.str,
    ) -> None:
        '''
        :param quartz_cron_expression: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#quartz_cron_expression DataQualityMonitor#quartz_cron_expression}.
        :param timezone_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#timezone_id DataQualityMonitor#timezone_id}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1fab113c416afd173d8e2e4d67ab52cd8ca459b79b72691ec7b6ea23d998f3f7)
            check_type(argname="argument quartz_cron_expression", value=quartz_cron_expression, expected_type=type_hints["quartz_cron_expression"])
            check_type(argname="argument timezone_id", value=timezone_id, expected_type=type_hints["timezone_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "quartz_cron_expression": quartz_cron_expression,
            "timezone_id": timezone_id,
        }

    @builtins.property
    def quartz_cron_expression(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#quartz_cron_expression DataQualityMonitor#quartz_cron_expression}.'''
        result = self._values.get("quartz_cron_expression")
        assert result is not None, "Required property 'quartz_cron_expression' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def timezone_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#timezone_id DataQualityMonitor#timezone_id}.'''
        result = self._values.get("timezone_id")
        assert result is not None, "Required property 'timezone_id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorDataProfilingConfigSchedule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataQualityMonitorDataProfilingConfigScheduleOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigScheduleOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__b3838611a58ead42adb185d51f2b3088f375521c97bf5c334cbcd2b8892a4077)
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
            type_hints = typing.get_type_hints(_typecheckingstub__213cc2a3044c3ac2584f8bf0bd0a49cd617477f75f13711f8f2085c57934803c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "quartzCronExpression", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timezoneId")
    def timezone_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timezoneId"))

    @timezone_id.setter
    def timezone_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6618ad7010cbf3fcbf1ffa0375e21b4e30eeb212f3d58a90458ebc8d7248c003)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timezoneId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigSchedule]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigSchedule]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigSchedule]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b610ddb5db80d8d6abfa21f3e808b3fffd51076dcdf4b739a30fe7a9e38553cf)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigSnapshot",
    jsii_struct_bases=[],
    name_mapping={},
)
class DataQualityMonitorDataProfilingConfigSnapshot:
    def __init__(self) -> None:
        self._values: typing.Dict[builtins.str, typing.Any] = {}

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorDataProfilingConfigSnapshot(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataQualityMonitorDataProfilingConfigSnapshotOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigSnapshotOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__9eb9f5b18b03706332016d3f5dc330b3a46dcb7d1fb34080e9fe6d403bbf7ca3)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigSnapshot]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigSnapshot]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigSnapshot]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__42d7a49ec7f0ec9b5d92af99eee0b3f4ae42c6ce033f3d31990e4ac1f3183f61)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigTimeSeries",
    jsii_struct_bases=[],
    name_mapping={
        "granularities": "granularities",
        "timestamp_column": "timestampColumn",
    },
)
class DataQualityMonitorDataProfilingConfigTimeSeries:
    def __init__(
        self,
        *,
        granularities: typing.Sequence[builtins.str],
        timestamp_column: builtins.str,
    ) -> None:
        '''
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#granularities DataQualityMonitor#granularities}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#timestamp_column DataQualityMonitor#timestamp_column}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1adc0abeaf6a80ce20e9dde456fd8b9e55914208a7f514fb3e1351ac02b9a8e0)
            check_type(argname="argument granularities", value=granularities, expected_type=type_hints["granularities"])
            check_type(argname="argument timestamp_column", value=timestamp_column, expected_type=type_hints["timestamp_column"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "granularities": granularities,
            "timestamp_column": timestamp_column,
        }

    @builtins.property
    def granularities(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#granularities DataQualityMonitor#granularities}.'''
        result = self._values.get("granularities")
        assert result is not None, "Required property 'granularities' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def timestamp_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/data_quality_monitor#timestamp_column DataQualityMonitor#timestamp_column}.'''
        result = self._values.get("timestamp_column")
        assert result is not None, "Required property 'timestamp_column' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataQualityMonitorDataProfilingConfigTimeSeries(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataQualityMonitorDataProfilingConfigTimeSeriesOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataQualityMonitor.DataQualityMonitorDataProfilingConfigTimeSeriesOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__be120786185a48d645a5b7429c4309cc2c22b5e282ebf2db5a873dcc70fdf39f)
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
            type_hints = typing.get_type_hints(_typecheckingstub__5c7f7f7f7411f3034bd8310d122efe7e0e10fde61b33edaf5b3c971a68bc04e7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "granularities", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timestampColumn")
    def timestamp_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timestampColumn"))

    @timestamp_column.setter
    def timestamp_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__24445a97df6faeb4c029ba9802d4fa3d00d6ce5d5a6480e5968b2c32ea0abdd4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timestampColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigTimeSeries]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigTimeSeries]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigTimeSeries]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad8bcdc7683734692eaa8335835cc1b52417d11781c3b9185f10571f828132e1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "DataQualityMonitor",
    "DataQualityMonitorAnomalyDetectionConfig",
    "DataQualityMonitorAnomalyDetectionConfigOutputReference",
    "DataQualityMonitorConfig",
    "DataQualityMonitorDataProfilingConfig",
    "DataQualityMonitorDataProfilingConfigCustomMetrics",
    "DataQualityMonitorDataProfilingConfigCustomMetricsList",
    "DataQualityMonitorDataProfilingConfigCustomMetricsOutputReference",
    "DataQualityMonitorDataProfilingConfigInferenceLog",
    "DataQualityMonitorDataProfilingConfigInferenceLogOutputReference",
    "DataQualityMonitorDataProfilingConfigNotificationSettings",
    "DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure",
    "DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference",
    "DataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference",
    "DataQualityMonitorDataProfilingConfigOutputReference",
    "DataQualityMonitorDataProfilingConfigSchedule",
    "DataQualityMonitorDataProfilingConfigScheduleOutputReference",
    "DataQualityMonitorDataProfilingConfigSnapshot",
    "DataQualityMonitorDataProfilingConfigSnapshotOutputReference",
    "DataQualityMonitorDataProfilingConfigTimeSeries",
    "DataQualityMonitorDataProfilingConfigTimeSeriesOutputReference",
]

publication.publish()

def _typecheckingstub__93a2dde71b2d3477f10d1613b50beffa0273b41466dbc185ad2c58d0231df8df(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    object_id: builtins.str,
    object_type: builtins.str,
    anomaly_detection_config: typing.Optional[typing.Union[DataQualityMonitorAnomalyDetectionConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    data_profiling_config: typing.Optional[typing.Union[DataQualityMonitorDataProfilingConfig, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__e484aac5e0b48a303d3f4a764e6d2cd68723109b1cfa64758f3ac10e6ca3ac5a(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ac8a2113562f156627ca63ae941243ab8e08f4ecf5fdc181e230f3f7e416144e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__257e204f98cd65e946417c07854a3cc826581c1b571b3ec88b512998ff4543f2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6775775e9f0f4933f9e70555eee420e3c462f43dd9330aae9ce5c607ab44307f(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a94b1727629fac58e164b593e75070ee47bd807d96e9e061e50c4f41aadcd0be(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorAnomalyDetectionConfig]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6072e659e22ef3e05826e5ab213e90bbdf88a82db6371b8b535cb74fcf6f3b9b(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    object_id: builtins.str,
    object_type: builtins.str,
    anomaly_detection_config: typing.Optional[typing.Union[DataQualityMonitorAnomalyDetectionConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    data_profiling_config: typing.Optional[typing.Union[DataQualityMonitorDataProfilingConfig, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7c7f9557d1ebfb0bbd463a51a9edad7b45e14e46995eb7ab3a60ecd1c912e42c(
    *,
    output_schema_id: builtins.str,
    assets_dir: typing.Optional[builtins.str] = None,
    baseline_table_name: typing.Optional[builtins.str] = None,
    custom_metrics: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataQualityMonitorDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]]] = None,
    inference_log: typing.Optional[typing.Union[DataQualityMonitorDataProfilingConfigInferenceLog, typing.Dict[builtins.str, typing.Any]]] = None,
    notification_settings: typing.Optional[typing.Union[DataQualityMonitorDataProfilingConfigNotificationSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    schedule: typing.Optional[typing.Union[DataQualityMonitorDataProfilingConfigSchedule, typing.Dict[builtins.str, typing.Any]]] = None,
    skip_builtin_dashboard: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    slicing_exprs: typing.Optional[typing.Sequence[builtins.str]] = None,
    snapshot: typing.Optional[typing.Union[DataQualityMonitorDataProfilingConfigSnapshot, typing.Dict[builtins.str, typing.Any]]] = None,
    time_series: typing.Optional[typing.Union[DataQualityMonitorDataProfilingConfigTimeSeries, typing.Dict[builtins.str, typing.Any]]] = None,
    warehouse_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__395c467e09c05f489f280e481cc62098cb3718112c50e467802feb1424b57d0c(
    *,
    definition: builtins.str,
    input_columns: typing.Sequence[builtins.str],
    name: builtins.str,
    output_data_type: builtins.str,
    type: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c74019bfe0e111a145be2cd6e2aaa51965ec6b2a6abba0ea7d6e9b457cf8028b(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__acaef86f557672f34a82995f1d8362497104feb255827deac524969a53e6c179(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__84a51f760bcb9bbb260d8014047ccf4f51dcfe6e3ca9354e67ac667bb6b1dd17(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f4b85ee14d8c8330c949ba7683fb87b08773ba9ffe6b75a8b65fdcc58309d442(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7ab1ba8825c76f2d9ac70aee668bedfd01efe0b4a2bfead74fd5a6c03bd93383(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__561badf0a24f30ef982077a6cecebc8276ea6405753a322bfb0538125390e6be(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataQualityMonitorDataProfilingConfigCustomMetrics]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__78a750e07d07f014d297a5cddf98d6ce4ed37bcd2473baa242bed4d0412fc2a2(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b00df402169e3c85645b536e454d81ae28a0090e2e9ab4ac355e1fcbab5ff303(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f818e2d04db9773e009b187f965feddc5c9a97bce707777d8d66ea41b180aa6e(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bc1f3cf73f7d2d4d6374f014257c27bdd05a25edb107d2f5d920e37d2e587ca1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1464017eb8c203aed87f0ba35bb11cdd1f8d540e4ab2c99f72a8e9390c492c03(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9dee2a32bec4abc48a6ff064d01169bb045bc5536f57830fa9ab4e69a2b39a91(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__98d5fa97fa8b1afd7104ae74998ba96e73f7d55918c2d7190585c75e9ec73e31(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigCustomMetrics]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__27a7e3c484abb6d58ccd7dbd7e7fbb89309b889833105a7c972ad851c286e338(
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

def _typecheckingstub__113105ca1aa4381f2b5b10cecfea4f12aa7dd17c26b1669a842fbbd98d8cdfc1(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6125b1e9d100d0a07f5c591bbf958b6f4e7f2acc59accb367869be7c489a70b4(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d506b84571a117d9453a473ddff21b6130a746d0ff76c0012672bd01c817b2e7(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3d7c80574095d7de7310f5580d5ed898b6765b3745ddfe1aa126f35ef9c7c456(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f12e0d974b98b87b482cb416343338c2ce3d094a7492b84245484cbce9060628(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__066ae1909b04cf402ee70999e6474f91346f12dc99cb8fa34b6be297a2e9eef8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ee36254dae65a23a997c1ed668da3adfc28b4a2b1ff0d517b630f31d163b0f69(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f081a260547aee035ec209d4a3f0f46a4e68c1837e03ec35629c52202576f9f(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigInferenceLog]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3959457da0bb6c5651d127d0558518b6bf2c965632574f78e513f02fe8813b0f(
    *,
    on_failure: typing.Optional[typing.Union[DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__15190d086a7944bb5dedab47b2d9e4410442ba6c71f0c3bf0158ce5b8a36b62f(
    *,
    email_addresses: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__310a25cd689fec65949c31d0a837c35af55d53f5aae2779e75e6ea5e5bd9bbd6(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__abe1b3489c92349658fd30eeb1f591c6b8a7992fa5456ba61d379f8d5bbc1165(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__44355ba46d6b06abc9f670440cb6fffc53bd25ee5c44bc56a268531fd87085e6(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fe3a743f7403b61eae945b9589715767b23fed11f6b40bf7b595b7db76da3e7d(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d3f967ee627f31df1f80de78a044e712ff9a9117e50b88acbe34f99be05e72a6(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigNotificationSettings]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3de385ee0019a6cae5df0d4ada16f64a75f2516351c7006b31d21250cb9471bf(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f079346fc2d4af4df6f7ea5d01c7e6d9388f4bc76d53016b65ed8f78b41d52fe(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataQualityMonitorDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3891532bbb62cfc5843681b40a965799816137128d8b0f750485ade244f70ec3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__469ee6453e48728795d907f778b3fe8c2019806be9108b5b7f8f124438a813e2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__20b4732645d616369b7d8512654e7348aec61f39d262956312c0404da9a7a4a0(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a9d49efd450571cb8467bce55e7613fcb53a4d3a0bd9add898edfd81a49401f(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__99b9df8a06ede9bd7349656ada7446910da77fb39335e182d562b6065c6ca89f(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__572c6975987284f1b42fa57d91a62ac4dbe91604e39d73f50417a2da1075eff7(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a1b42cf7f0d5991e722994ef67f14b59599c02c39201c4a9f1f6e11228ad87f0(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfig]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1fab113c416afd173d8e2e4d67ab52cd8ca459b79b72691ec7b6ea23d998f3f7(
    *,
    quartz_cron_expression: builtins.str,
    timezone_id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b3838611a58ead42adb185d51f2b3088f375521c97bf5c334cbcd2b8892a4077(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__213cc2a3044c3ac2584f8bf0bd0a49cd617477f75f13711f8f2085c57934803c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6618ad7010cbf3fcbf1ffa0375e21b4e30eeb212f3d58a90458ebc8d7248c003(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b610ddb5db80d8d6abfa21f3e808b3fffd51076dcdf4b739a30fe7a9e38553cf(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigSchedule]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9eb9f5b18b03706332016d3f5dc330b3a46dcb7d1fb34080e9fe6d403bbf7ca3(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__42d7a49ec7f0ec9b5d92af99eee0b3f4ae42c6ce033f3d31990e4ac1f3183f61(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigSnapshot]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1adc0abeaf6a80ce20e9dde456fd8b9e55914208a7f514fb3e1351ac02b9a8e0(
    *,
    granularities: typing.Sequence[builtins.str],
    timestamp_column: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be120786185a48d645a5b7429c4309cc2c22b5e282ebf2db5a873dcc70fdf39f(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5c7f7f7f7411f3034bd8310d122efe7e0e10fde61b33edaf5b3c971a68bc04e7(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__24445a97df6faeb4c029ba9802d4fa3d00d6ce5d5a6480e5968b2c32ea0abdd4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad8bcdc7683734692eaa8335835cc1b52417d11781c3b9185f10571f828132e1(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataQualityMonitorDataProfilingConfigTimeSeries]],
) -> None:
    """Type checking stubs"""
    pass
