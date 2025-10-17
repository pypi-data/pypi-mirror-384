r'''
# `data_databricks_data_quality_monitor`

Refer to the Terraform Registry for docs: [`data_databricks_data_quality_monitor`](https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor).
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


class DataDatabricksDataQualityMonitor(
    _cdktf_9a9027ec.TerraformDataSource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitor",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor databricks_data_quality_monitor}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        object_id: builtins.str,
        object_type: builtins.str,
        anomaly_detection_config: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorAnomalyDetectionConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        data_profiling_config: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor databricks_data_quality_monitor} Data Source.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param object_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#object_id DataDatabricksDataQualityMonitor#object_id}.
        :param object_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#object_type DataDatabricksDataQualityMonitor#object_type}.
        :param anomaly_detection_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#anomaly_detection_config DataDatabricksDataQualityMonitor#anomaly_detection_config}.
        :param data_profiling_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#data_profiling_config DataDatabricksDataQualityMonitor#data_profiling_config}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d660afd9e795802eb1075266c69a0d325bfce5d627d480025d38d59832b0c97e)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = DataDatabricksDataQualityMonitorConfig(
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
        '''Generates CDKTF code for importing a DataDatabricksDataQualityMonitor resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DataDatabricksDataQualityMonitor to import.
        :param import_from_id: The id of the existing DataDatabricksDataQualityMonitor that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DataDatabricksDataQualityMonitor to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7a562b136030dd00cb22405b5a395ffda75d419bb037e9b456e89deaba2341fd)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putAnomalyDetectionConfig")
    def put_anomaly_detection_config(self) -> None:
        value = DataDatabricksDataQualityMonitorAnomalyDetectionConfig()

        return typing.cast(None, jsii.invoke(self, "putAnomalyDetectionConfig", [value]))

    @jsii.member(jsii_name="putDataProfilingConfig")
    def put_data_profiling_config(
        self,
        *,
        output_schema_id: builtins.str,
        assets_dir: typing.Optional[builtins.str] = None,
        baseline_table_name: typing.Optional[builtins.str] = None,
        custom_metrics: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics", typing.Dict[builtins.str, typing.Any]]]]] = None,
        inference_log: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog", typing.Dict[builtins.str, typing.Any]]] = None,
        notification_settings: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        schedule: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigSchedule", typing.Dict[builtins.str, typing.Any]]] = None,
        skip_builtin_dashboard: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        slicing_exprs: typing.Optional[typing.Sequence[builtins.str]] = None,
        snapshot: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot", typing.Dict[builtins.str, typing.Any]]] = None,
        time_series: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries", typing.Dict[builtins.str, typing.Any]]] = None,
        warehouse_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param output_schema_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#output_schema_id DataDatabricksDataQualityMonitor#output_schema_id}.
        :param assets_dir: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#assets_dir DataDatabricksDataQualityMonitor#assets_dir}.
        :param baseline_table_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#baseline_table_name DataDatabricksDataQualityMonitor#baseline_table_name}.
        :param custom_metrics: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#custom_metrics DataDatabricksDataQualityMonitor#custom_metrics}.
        :param inference_log: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#inference_log DataDatabricksDataQualityMonitor#inference_log}.
        :param notification_settings: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#notification_settings DataDatabricksDataQualityMonitor#notification_settings}.
        :param schedule: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#schedule DataDatabricksDataQualityMonitor#schedule}.
        :param skip_builtin_dashboard: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#skip_builtin_dashboard DataDatabricksDataQualityMonitor#skip_builtin_dashboard}.
        :param slicing_exprs: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#slicing_exprs DataDatabricksDataQualityMonitor#slicing_exprs}.
        :param snapshot: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#snapshot DataDatabricksDataQualityMonitor#snapshot}.
        :param time_series: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#time_series DataDatabricksDataQualityMonitor#time_series}.
        :param warehouse_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#warehouse_id DataDatabricksDataQualityMonitor#warehouse_id}.
        '''
        value = DataDatabricksDataQualityMonitorDataProfilingConfig(
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
    ) -> "DataDatabricksDataQualityMonitorAnomalyDetectionConfigOutputReference":
        return typing.cast("DataDatabricksDataQualityMonitorAnomalyDetectionConfigOutputReference", jsii.get(self, "anomalyDetectionConfig"))

    @builtins.property
    @jsii.member(jsii_name="dataProfilingConfig")
    def data_profiling_config(
        self,
    ) -> "DataDatabricksDataQualityMonitorDataProfilingConfigOutputReference":
        return typing.cast("DataDatabricksDataQualityMonitorDataProfilingConfigOutputReference", jsii.get(self, "dataProfilingConfig"))

    @builtins.property
    @jsii.member(jsii_name="anomalyDetectionConfigInput")
    def anomaly_detection_config_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorAnomalyDetectionConfig"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorAnomalyDetectionConfig"]], jsii.get(self, "anomalyDetectionConfigInput"))

    @builtins.property
    @jsii.member(jsii_name="dataProfilingConfigInput")
    def data_profiling_config_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorDataProfilingConfig"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorDataProfilingConfig"]], jsii.get(self, "dataProfilingConfigInput"))

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
            type_hints = typing.get_type_hints(_typecheckingstub__d9407771456486dcf281794f92b7a01aeebe37ab75e8fde6dfb2873d20591e12)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "objectId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="objectType")
    def object_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "objectType"))

    @object_type.setter
    def object_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a77d0e436db20e64fde17f66e92b8c9aae3201a1381fbcc2533ec9edbfca430b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "objectType", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorAnomalyDetectionConfig",
    jsii_struct_bases=[],
    name_mapping={},
)
class DataDatabricksDataQualityMonitorAnomalyDetectionConfig:
    def __init__(self) -> None:
        self._values: typing.Dict[builtins.str, typing.Any] = {}

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorAnomalyDetectionConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorAnomalyDetectionConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorAnomalyDetectionConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__1f503603f1e773a6df065bb18e26da609ae4ce664b0882938fe3b546a01ef4c0)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorAnomalyDetectionConfig]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorAnomalyDetectionConfig]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorAnomalyDetectionConfig]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7efba2f64e35664ddd8b3fa195aa80dcde34359ebce59127c3354b401a9816b0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorConfig",
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
class DataDatabricksDataQualityMonitorConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        anomaly_detection_config: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorAnomalyDetectionConfig, typing.Dict[builtins.str, typing.Any]]] = None,
        data_profiling_config: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfig", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param object_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#object_id DataDatabricksDataQualityMonitor#object_id}.
        :param object_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#object_type DataDatabricksDataQualityMonitor#object_type}.
        :param anomaly_detection_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#anomaly_detection_config DataDatabricksDataQualityMonitor#anomaly_detection_config}.
        :param data_profiling_config: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#data_profiling_config DataDatabricksDataQualityMonitor#data_profiling_config}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(anomaly_detection_config, dict):
            anomaly_detection_config = DataDatabricksDataQualityMonitorAnomalyDetectionConfig(**anomaly_detection_config)
        if isinstance(data_profiling_config, dict):
            data_profiling_config = DataDatabricksDataQualityMonitorDataProfilingConfig(**data_profiling_config)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__77a6dae5b69911914797f92c48256d227523c27b022f04e4acea69a2006fac9c)
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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#object_id DataDatabricksDataQualityMonitor#object_id}.'''
        result = self._values.get("object_id")
        assert result is not None, "Required property 'object_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def object_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#object_type DataDatabricksDataQualityMonitor#object_type}.'''
        result = self._values.get("object_type")
        assert result is not None, "Required property 'object_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def anomaly_detection_config(
        self,
    ) -> typing.Optional[DataDatabricksDataQualityMonitorAnomalyDetectionConfig]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#anomaly_detection_config DataDatabricksDataQualityMonitor#anomaly_detection_config}.'''
        result = self._values.get("anomaly_detection_config")
        return typing.cast(typing.Optional[DataDatabricksDataQualityMonitorAnomalyDetectionConfig], result)

    @builtins.property
    def data_profiling_config(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfig"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#data_profiling_config DataDatabricksDataQualityMonitor#data_profiling_config}.'''
        result = self._values.get("data_profiling_config")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfig"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfig",
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
class DataDatabricksDataQualityMonitorDataProfilingConfig:
    def __init__(
        self,
        *,
        output_schema_id: builtins.str,
        assets_dir: typing.Optional[builtins.str] = None,
        baseline_table_name: typing.Optional[builtins.str] = None,
        custom_metrics: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics", typing.Dict[builtins.str, typing.Any]]]]] = None,
        inference_log: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog", typing.Dict[builtins.str, typing.Any]]] = None,
        notification_settings: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        schedule: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigSchedule", typing.Dict[builtins.str, typing.Any]]] = None,
        skip_builtin_dashboard: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        slicing_exprs: typing.Optional[typing.Sequence[builtins.str]] = None,
        snapshot: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot", typing.Dict[builtins.str, typing.Any]]] = None,
        time_series: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries", typing.Dict[builtins.str, typing.Any]]] = None,
        warehouse_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param output_schema_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#output_schema_id DataDatabricksDataQualityMonitor#output_schema_id}.
        :param assets_dir: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#assets_dir DataDatabricksDataQualityMonitor#assets_dir}.
        :param baseline_table_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#baseline_table_name DataDatabricksDataQualityMonitor#baseline_table_name}.
        :param custom_metrics: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#custom_metrics DataDatabricksDataQualityMonitor#custom_metrics}.
        :param inference_log: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#inference_log DataDatabricksDataQualityMonitor#inference_log}.
        :param notification_settings: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#notification_settings DataDatabricksDataQualityMonitor#notification_settings}.
        :param schedule: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#schedule DataDatabricksDataQualityMonitor#schedule}.
        :param skip_builtin_dashboard: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#skip_builtin_dashboard DataDatabricksDataQualityMonitor#skip_builtin_dashboard}.
        :param slicing_exprs: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#slicing_exprs DataDatabricksDataQualityMonitor#slicing_exprs}.
        :param snapshot: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#snapshot DataDatabricksDataQualityMonitor#snapshot}.
        :param time_series: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#time_series DataDatabricksDataQualityMonitor#time_series}.
        :param warehouse_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#warehouse_id DataDatabricksDataQualityMonitor#warehouse_id}.
        '''
        if isinstance(inference_log, dict):
            inference_log = DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog(**inference_log)
        if isinstance(notification_settings, dict):
            notification_settings = DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings(**notification_settings)
        if isinstance(schedule, dict):
            schedule = DataDatabricksDataQualityMonitorDataProfilingConfigSchedule(**schedule)
        if isinstance(snapshot, dict):
            snapshot = DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot(**snapshot)
        if isinstance(time_series, dict):
            time_series = DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries(**time_series)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8a107bc7e631d81fbeffb889c41009ab493b523df919bf208a3bb422d62dc11e)
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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#output_schema_id DataDatabricksDataQualityMonitor#output_schema_id}.'''
        result = self._values.get("output_schema_id")
        assert result is not None, "Required property 'output_schema_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def assets_dir(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#assets_dir DataDatabricksDataQualityMonitor#assets_dir}.'''
        result = self._values.get("assets_dir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def baseline_table_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#baseline_table_name DataDatabricksDataQualityMonitor#baseline_table_name}.'''
        result = self._values.get("baseline_table_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def custom_metrics(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics"]]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#custom_metrics DataDatabricksDataQualityMonitor#custom_metrics}.'''
        result = self._values.get("custom_metrics")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics"]]], result)

    @builtins.property
    def inference_log(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#inference_log DataDatabricksDataQualityMonitor#inference_log}.'''
        result = self._values.get("inference_log")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog"], result)

    @builtins.property
    def notification_settings(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#notification_settings DataDatabricksDataQualityMonitor#notification_settings}.'''
        result = self._values.get("notification_settings")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings"], result)

    @builtins.property
    def schedule(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigSchedule"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#schedule DataDatabricksDataQualityMonitor#schedule}.'''
        result = self._values.get("schedule")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigSchedule"], result)

    @builtins.property
    def skip_builtin_dashboard(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#skip_builtin_dashboard DataDatabricksDataQualityMonitor#skip_builtin_dashboard}.'''
        result = self._values.get("skip_builtin_dashboard")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def slicing_exprs(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#slicing_exprs DataDatabricksDataQualityMonitor#slicing_exprs}.'''
        result = self._values.get("slicing_exprs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def snapshot(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#snapshot DataDatabricksDataQualityMonitor#snapshot}.'''
        result = self._values.get("snapshot")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot"], result)

    @builtins.property
    def time_series(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#time_series DataDatabricksDataQualityMonitor#time_series}.'''
        result = self._values.get("time_series")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries"], result)

    @builtins.property
    def warehouse_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#warehouse_id DataDatabricksDataQualityMonitor#warehouse_id}.'''
        result = self._values.get("warehouse_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorDataProfilingConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics",
    jsii_struct_bases=[],
    name_mapping={
        "definition": "definition",
        "input_columns": "inputColumns",
        "name": "name",
        "output_data_type": "outputDataType",
        "type": "type",
    },
)
class DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics:
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
        :param definition: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#definition DataDatabricksDataQualityMonitor#definition}.
        :param input_columns: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#input_columns DataDatabricksDataQualityMonitor#input_columns}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#name DataDatabricksDataQualityMonitor#name}.
        :param output_data_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#output_data_type DataDatabricksDataQualityMonitor#output_data_type}.
        :param type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#type DataDatabricksDataQualityMonitor#type}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c10f0e606d1e2f1181c480f929f6725ec7dce0490e93c290119d0923231de674)
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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#definition DataDatabricksDataQualityMonitor#definition}.'''
        result = self._values.get("definition")
        assert result is not None, "Required property 'definition' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def input_columns(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#input_columns DataDatabricksDataQualityMonitor#input_columns}.'''
        result = self._values.get("input_columns")
        assert result is not None, "Required property 'input_columns' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#name DataDatabricksDataQualityMonitor#name}.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def output_data_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#output_data_type DataDatabricksDataQualityMonitor#output_data_type}.'''
        result = self._values.get("output_data_type")
        assert result is not None, "Required property 'output_data_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#type DataDatabricksDataQualityMonitor#type}.'''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__ea499615fb146d2b60eb23b4c367695aa41a21025fe3f661e287230ecaf4104a)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ece50e3e46cd98f1bf10e039e5c9ca681d5c7a162dffc606b196ac10d1e5d3ef)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bef5aa624f87eea9799ef452de9dd5a3cd7290ed8fc9d949ef455b375d5d0ae5)
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
            type_hints = typing.get_type_hints(_typecheckingstub__25544199e3f557ede250cd37fae7417cf1ecc4e551872838e66259e1806326d2)
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
            type_hints = typing.get_type_hints(_typecheckingstub__e6cd70e94500aaffcbad4d8c31edc9624216a2e9ccd5b492c4ef33b10f5311ad)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7440b58e5ab2f43800fe6dc16a2ec29c6ae37ea53fd3fb7caa1019cacf5a3103)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__db0663bcd76a07c1735b147540dc9b95b3b45b08b2b300289d826ec3c1b4c9ef)
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
            type_hints = typing.get_type_hints(_typecheckingstub__26f1f64d0dee5e4b6dcae270d0072976fe7444d16002563ad39325578735e0f1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "definition", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="inputColumns")
    def input_columns(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "inputColumns"))

    @input_columns.setter
    def input_columns(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e4f73ccc5127745eecbf271cd038ceccea1108664a7ee86d21de3ca7a1c8a818)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "inputColumns", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6fe84198c75f8b4c6d64d66d983c333a9b276112075cc267521adb10fb046025)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="outputDataType")
    def output_data_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "outputDataType"))

    @output_data_type.setter
    def output_data_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__54d254464ad14c369dccc4efa46939847975bd03279daf56ee327f7b79aa21fd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "outputDataType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a9ef55a3ad829d3e37591972dc495fa9def5c0309030b3894b685ce9922ec575)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__48e7508f5333c474d544365c65d8c1d3da964f66be06045fd89b0b8789d129b9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog",
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
class DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog:
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
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#granularities DataDatabricksDataQualityMonitor#granularities}.
        :param model_id_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#model_id_column DataDatabricksDataQualityMonitor#model_id_column}.
        :param prediction_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#prediction_column DataDatabricksDataQualityMonitor#prediction_column}.
        :param problem_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#problem_type DataDatabricksDataQualityMonitor#problem_type}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#timestamp_column DataDatabricksDataQualityMonitor#timestamp_column}.
        :param label_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#label_column DataDatabricksDataQualityMonitor#label_column}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2320109509455d6545195887f721a511b154fc0c2f02e4ca80876aa194f76f2a)
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
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#granularities DataDatabricksDataQualityMonitor#granularities}.'''
        result = self._values.get("granularities")
        assert result is not None, "Required property 'granularities' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def model_id_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#model_id_column DataDatabricksDataQualityMonitor#model_id_column}.'''
        result = self._values.get("model_id_column")
        assert result is not None, "Required property 'model_id_column' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def prediction_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#prediction_column DataDatabricksDataQualityMonitor#prediction_column}.'''
        result = self._values.get("prediction_column")
        assert result is not None, "Required property 'prediction_column' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def problem_type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#problem_type DataDatabricksDataQualityMonitor#problem_type}.'''
        result = self._values.get("problem_type")
        assert result is not None, "Required property 'problem_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def timestamp_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#timestamp_column DataDatabricksDataQualityMonitor#timestamp_column}.'''
        result = self._values.get("timestamp_column")
        assert result is not None, "Required property 'timestamp_column' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def label_column(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#label_column DataDatabricksDataQualityMonitor#label_column}.'''
        result = self._values.get("label_column")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLogOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLogOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__1cede4c1e0915b79450f7ea0c2c717501ca63c179473a49d52bfb30f12dcfeb9)
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
            type_hints = typing.get_type_hints(_typecheckingstub__1d4c588d122eb327e369c2cef03ceda4650d1f300b0f406291a007ca979c9d70)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "granularities", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="labelColumn")
    def label_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "labelColumn"))

    @label_column.setter
    def label_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f3be275587494941d42de591af114e8df132d31f6051298b5f60b9b99af49f0a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "labelColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="modelIdColumn")
    def model_id_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "modelIdColumn"))

    @model_id_column.setter
    def model_id_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a9dcec379a13f2415fed5c1e93ba673a98a43a89649c693b6a2fb3ec7652730d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "modelIdColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="predictionColumn")
    def prediction_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "predictionColumn"))

    @prediction_column.setter
    def prediction_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0e5a0402ec937ef62e6b7f5dde9c81028de42e5aa9ce39e6a994a38d70daee03)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "predictionColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="problemType")
    def problem_type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "problemType"))

    @problem_type.setter
    def problem_type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2df6ae86e5c072d8232917a6b0c8c23694c27816e3b5ca28e080ddaa9e447aae)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "problemType", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timestampColumn")
    def timestamp_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timestampColumn"))

    @timestamp_column.setter
    def timestamp_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2e7182edb2fb1517dc92a3ff517af678b81e8f34b6c3eb044ff5dbca0ab9556a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timestampColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a2a3b06b340aed88edd933bd18fb22c66197f0636432b4055c043511743ad2bc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings",
    jsii_struct_bases=[],
    name_mapping={"on_failure": "onFailure"},
)
class DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings:
    def __init__(
        self,
        *,
        on_failure: typing.Optional[typing.Union["DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param on_failure: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#on_failure DataDatabricksDataQualityMonitor#on_failure}.
        '''
        if isinstance(on_failure, dict):
            on_failure = DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure(**on_failure)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f4ff2216c7ead7c5c5781b5aa5b000a8f0c0c73dc88ff239cd964e1a17fa7eb0)
            check_type(argname="argument on_failure", value=on_failure, expected_type=type_hints["on_failure"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if on_failure is not None:
            self._values["on_failure"] = on_failure

    @builtins.property
    def on_failure(
        self,
    ) -> typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#on_failure DataDatabricksDataQualityMonitor#on_failure}.'''
        result = self._values.get("on_failure")
        return typing.cast(typing.Optional["DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure",
    jsii_struct_bases=[],
    name_mapping={"email_addresses": "emailAddresses"},
)
class DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure:
    def __init__(
        self,
        *,
        email_addresses: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param email_addresses: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#email_addresses DataDatabricksDataQualityMonitor#email_addresses}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6ea8ad61db92bad83c14aff0a5817b32d3d702eedafa049136a71e6e3516459c)
            check_type(argname="argument email_addresses", value=email_addresses, expected_type=type_hints["email_addresses"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if email_addresses is not None:
            self._values["email_addresses"] = email_addresses

    @builtins.property
    def email_addresses(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#email_addresses DataDatabricksDataQualityMonitor#email_addresses}.'''
        result = self._values.get("email_addresses")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__6446361f6d31648c96899cd30720027806b07ad67901ee3f925bd31c20e162af)
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
            type_hints = typing.get_type_hints(_typecheckingstub__c2ddf3eeb12e35318ded2b760923cb2fdd302aede44cfb808cf294f5009c431c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emailAddresses", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__04adf5d484fc0cb88d3dc0a497ffd7b22173415dee1844018c0fc605c61dc5d3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__7daf3211b294dd5ef4279f1b0ccff87d435c6a1f6f84fdc41c8a8b5462b3dfd8)
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
        :param email_addresses: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#email_addresses DataDatabricksDataQualityMonitor#email_addresses}.
        '''
        value = DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure(
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
    ) -> DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference:
        return typing.cast(DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference, jsii.get(self, "onFailure"))

    @builtins.property
    @jsii.member(jsii_name="onFailureInput")
    def on_failure_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]], jsii.get(self, "onFailureInput"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__20e2da752fdb5839cef64075bc8c2fa193fa43c9a481eb729351a533ada079d6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksDataQualityMonitorDataProfilingConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__fe3c74d0556a4be5645f9cfbefa11833a2bd7307cfdceba66c4282184904d1eb)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putCustomMetrics")
    def put_custom_metrics(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c34379526e5a75b97b70383d1dd3af38f622dce8af55049e4915aeccf343c776)
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
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#granularities DataDatabricksDataQualityMonitor#granularities}.
        :param model_id_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#model_id_column DataDatabricksDataQualityMonitor#model_id_column}.
        :param prediction_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#prediction_column DataDatabricksDataQualityMonitor#prediction_column}.
        :param problem_type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#problem_type DataDatabricksDataQualityMonitor#problem_type}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#timestamp_column DataDatabricksDataQualityMonitor#timestamp_column}.
        :param label_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#label_column DataDatabricksDataQualityMonitor#label_column}.
        '''
        value = DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog(
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
        on_failure: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param on_failure: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#on_failure DataDatabricksDataQualityMonitor#on_failure}.
        '''
        value = DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings(
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
        :param quartz_cron_expression: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#quartz_cron_expression DataDatabricksDataQualityMonitor#quartz_cron_expression}.
        :param timezone_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#timezone_id DataDatabricksDataQualityMonitor#timezone_id}.
        '''
        value = DataDatabricksDataQualityMonitorDataProfilingConfigSchedule(
            quartz_cron_expression=quartz_cron_expression, timezone_id=timezone_id
        )

        return typing.cast(None, jsii.invoke(self, "putSchedule", [value]))

    @jsii.member(jsii_name="putSnapshot")
    def put_snapshot(self) -> None:
        value = DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot()

        return typing.cast(None, jsii.invoke(self, "putSnapshot", [value]))

    @jsii.member(jsii_name="putTimeSeries")
    def put_time_series(
        self,
        *,
        granularities: typing.Sequence[builtins.str],
        timestamp_column: builtins.str,
    ) -> None:
        '''
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#granularities DataDatabricksDataQualityMonitor#granularities}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#timestamp_column DataDatabricksDataQualityMonitor#timestamp_column}.
        '''
        value = DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries(
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
    ) -> DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsList:
        return typing.cast(DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsList, jsii.get(self, "customMetrics"))

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
    ) -> DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLogOutputReference:
        return typing.cast(DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLogOutputReference, jsii.get(self, "inferenceLog"))

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
    ) -> DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference:
        return typing.cast(DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference, jsii.get(self, "notificationSettings"))

    @builtins.property
    @jsii.member(jsii_name="profileMetricsTableName")
    def profile_metrics_table_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "profileMetricsTableName"))

    @builtins.property
    @jsii.member(jsii_name="schedule")
    def schedule(
        self,
    ) -> "DataDatabricksDataQualityMonitorDataProfilingConfigScheduleOutputReference":
        return typing.cast("DataDatabricksDataQualityMonitorDataProfilingConfigScheduleOutputReference", jsii.get(self, "schedule"))

    @builtins.property
    @jsii.member(jsii_name="snapshot")
    def snapshot(
        self,
    ) -> "DataDatabricksDataQualityMonitorDataProfilingConfigSnapshotOutputReference":
        return typing.cast("DataDatabricksDataQualityMonitorDataProfilingConfigSnapshotOutputReference", jsii.get(self, "snapshot"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="timeSeries")
    def time_series(
        self,
    ) -> "DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeriesOutputReference":
        return typing.cast("DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeriesOutputReference", jsii.get(self, "timeSeries"))

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
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]]], jsii.get(self, "customMetricsInput"))

    @builtins.property
    @jsii.member(jsii_name="inferenceLogInput")
    def inference_log_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog]], jsii.get(self, "inferenceLogInput"))

    @builtins.property
    @jsii.member(jsii_name="notificationSettingsInput")
    def notification_settings_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings]], jsii.get(self, "notificationSettingsInput"))

    @builtins.property
    @jsii.member(jsii_name="outputSchemaIdInput")
    def output_schema_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "outputSchemaIdInput"))

    @builtins.property
    @jsii.member(jsii_name="scheduleInput")
    def schedule_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorDataProfilingConfigSchedule"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorDataProfilingConfigSchedule"]], jsii.get(self, "scheduleInput"))

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
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot"]], jsii.get(self, "snapshotInput"))

    @builtins.property
    @jsii.member(jsii_name="timeSeriesInput")
    def time_series_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries"]], jsii.get(self, "timeSeriesInput"))

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
            type_hints = typing.get_type_hints(_typecheckingstub__7798ae8c164cefd9e5e46903eb247cb0ce5a4f649a0bccd339c39fe64bae6ca3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "assetsDir", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="baselineTableName")
    def baseline_table_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "baselineTableName"))

    @baseline_table_name.setter
    def baseline_table_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__82e6601ab1125642fe0895b59372db6a5ff683e2565fa9d55aa5317afa59ded3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "baselineTableName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="outputSchemaId")
    def output_schema_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "outputSchemaId"))

    @output_schema_id.setter
    def output_schema_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dba3052b7310f005547a2ed741a341da6a81e8d4fae5bf8d5803470aa839920c)
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
            type_hints = typing.get_type_hints(_typecheckingstub__04f2bb882f62e9ff0820fbab2fd42812bc7127eef87f2cae4c45d00f3bb0ae48)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "skipBuiltinDashboard", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="slicingExprs")
    def slicing_exprs(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "slicingExprs"))

    @slicing_exprs.setter
    def slicing_exprs(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2936e07ec1e348c7e72fbf5a5f1f5630b09bcad30ba549d29dce251bb1e2a066)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "slicingExprs", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="warehouseId")
    def warehouse_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "warehouseId"))

    @warehouse_id.setter
    def warehouse_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da8c7b4441b50e9c073e454863d7035a9a11d2a290c41e88a8c31f537f3be1ba)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "warehouseId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfig]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfig]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfig]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5339d14b67952b77152887f90f38b004c67b3d32c6deeba5f985989f2a16d4ad)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigSchedule",
    jsii_struct_bases=[],
    name_mapping={
        "quartz_cron_expression": "quartzCronExpression",
        "timezone_id": "timezoneId",
    },
)
class DataDatabricksDataQualityMonitorDataProfilingConfigSchedule:
    def __init__(
        self,
        *,
        quartz_cron_expression: builtins.str,
        timezone_id: builtins.str,
    ) -> None:
        '''
        :param quartz_cron_expression: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#quartz_cron_expression DataDatabricksDataQualityMonitor#quartz_cron_expression}.
        :param timezone_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#timezone_id DataDatabricksDataQualityMonitor#timezone_id}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7b5d15c8043f9d78f60da58b5e82895ff602365ced8d2a163e0e11c841cd788c)
            check_type(argname="argument quartz_cron_expression", value=quartz_cron_expression, expected_type=type_hints["quartz_cron_expression"])
            check_type(argname="argument timezone_id", value=timezone_id, expected_type=type_hints["timezone_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "quartz_cron_expression": quartz_cron_expression,
            "timezone_id": timezone_id,
        }

    @builtins.property
    def quartz_cron_expression(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#quartz_cron_expression DataDatabricksDataQualityMonitor#quartz_cron_expression}.'''
        result = self._values.get("quartz_cron_expression")
        assert result is not None, "Required property 'quartz_cron_expression' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def timezone_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#timezone_id DataDatabricksDataQualityMonitor#timezone_id}.'''
        result = self._values.get("timezone_id")
        assert result is not None, "Required property 'timezone_id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorDataProfilingConfigSchedule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorDataProfilingConfigScheduleOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigScheduleOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__0a9a5e935cb6fe62c1620b73cc0f8ce9e1193941e0c76ed775be72df3727e722)
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
            type_hints = typing.get_type_hints(_typecheckingstub__3ed332fd3afa6f8cb0934cee7ee12fd0d054493914ac5128efd73b355f53c67c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "quartzCronExpression", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timezoneId")
    def timezone_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timezoneId"))

    @timezone_id.setter
    def timezone_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__df10cf3140854e76250ea17473281f4f87e99d4472c2b0834ea506b28cc9bbd2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timezoneId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigSchedule]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigSchedule]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigSchedule]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e9acefac3b42927c8ebcda0fbd55d5d25f7f2bc9f7eecaf5998160cca2c9fe01)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot",
    jsii_struct_bases=[],
    name_mapping={},
)
class DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot:
    def __init__(self) -> None:
        self._values: typing.Dict[builtins.str, typing.Any] = {}

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorDataProfilingConfigSnapshotOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigSnapshotOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__a78581a98875348d8d59e19282132c4cc3556a8c3290e9e835f4ddcddf9f8978)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8360bf291a98cbe27552539de30dbb68eecc373e80ceefaaca82f10147a3b4d7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries",
    jsii_struct_bases=[],
    name_mapping={
        "granularities": "granularities",
        "timestamp_column": "timestampColumn",
    },
)
class DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries:
    def __init__(
        self,
        *,
        granularities: typing.Sequence[builtins.str],
        timestamp_column: builtins.str,
    ) -> None:
        '''
        :param granularities: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#granularities DataDatabricksDataQualityMonitor#granularities}.
        :param timestamp_column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#timestamp_column DataDatabricksDataQualityMonitor#timestamp_column}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__044f739cc9a03a2a2c851626e90d1e0c43e06d7b232c2e87d76a28c6e3844c46)
            check_type(argname="argument granularities", value=granularities, expected_type=type_hints["granularities"])
            check_type(argname="argument timestamp_column", value=timestamp_column, expected_type=type_hints["timestamp_column"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "granularities": granularities,
            "timestamp_column": timestamp_column,
        }

    @builtins.property
    def granularities(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#granularities DataDatabricksDataQualityMonitor#granularities}.'''
        result = self._values.get("granularities")
        assert result is not None, "Required property 'granularities' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def timestamp_column(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/data_quality_monitor#timestamp_column DataDatabricksDataQualityMonitor#timestamp_column}.'''
        result = self._values.get("timestamp_column")
        assert result is not None, "Required property 'timestamp_column' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeriesOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksDataQualityMonitor.DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeriesOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__d2d7eec86bd83161f3f6a384178487ab33bc71178a93ed224338098a8ec55e51)
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
            type_hints = typing.get_type_hints(_typecheckingstub__d71ac255e3b24227f568c4d5e54afe91c7806de0c27dced5063c89922d8fe2d7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "granularities", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timestampColumn")
    def timestamp_column(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timestampColumn"))

    @timestamp_column.setter
    def timestamp_column(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__840c7ab957df94c2e50843345b1dc583ce309b08afb1633a2027b16484c2a105)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timestampColumn", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__885b9f91ab4e90dfabd55bbeb758e954aba0284082c987cffc9371d96621170a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "DataDatabricksDataQualityMonitor",
    "DataDatabricksDataQualityMonitorAnomalyDetectionConfig",
    "DataDatabricksDataQualityMonitorAnomalyDetectionConfigOutputReference",
    "DataDatabricksDataQualityMonitorConfig",
    "DataDatabricksDataQualityMonitorDataProfilingConfig",
    "DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics",
    "DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsList",
    "DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetricsOutputReference",
    "DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog",
    "DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLogOutputReference",
    "DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings",
    "DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure",
    "DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailureOutputReference",
    "DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOutputReference",
    "DataDatabricksDataQualityMonitorDataProfilingConfigOutputReference",
    "DataDatabricksDataQualityMonitorDataProfilingConfigSchedule",
    "DataDatabricksDataQualityMonitorDataProfilingConfigScheduleOutputReference",
    "DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot",
    "DataDatabricksDataQualityMonitorDataProfilingConfigSnapshotOutputReference",
    "DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries",
    "DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeriesOutputReference",
]

publication.publish()

def _typecheckingstub__d660afd9e795802eb1075266c69a0d325bfce5d627d480025d38d59832b0c97e(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    object_id: builtins.str,
    object_type: builtins.str,
    anomaly_detection_config: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorAnomalyDetectionConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    data_profiling_config: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfig, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__7a562b136030dd00cb22405b5a395ffda75d419bb037e9b456e89deaba2341fd(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d9407771456486dcf281794f92b7a01aeebe37ab75e8fde6dfb2873d20591e12(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a77d0e436db20e64fde17f66e92b8c9aae3201a1381fbcc2533ec9edbfca430b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1f503603f1e773a6df065bb18e26da609ae4ce664b0882938fe3b546a01ef4c0(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7efba2f64e35664ddd8b3fa195aa80dcde34359ebce59127c3354b401a9816b0(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorAnomalyDetectionConfig]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__77a6dae5b69911914797f92c48256d227523c27b022f04e4acea69a2006fac9c(
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
    anomaly_detection_config: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorAnomalyDetectionConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    data_profiling_config: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfig, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8a107bc7e631d81fbeffb889c41009ab493b523df919bf208a3bb422d62dc11e(
    *,
    output_schema_id: builtins.str,
    assets_dir: typing.Optional[builtins.str] = None,
    baseline_table_name: typing.Optional[builtins.str] = None,
    custom_metrics: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]]] = None,
    inference_log: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog, typing.Dict[builtins.str, typing.Any]]] = None,
    notification_settings: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    schedule: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigSchedule, typing.Dict[builtins.str, typing.Any]]] = None,
    skip_builtin_dashboard: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    slicing_exprs: typing.Optional[typing.Sequence[builtins.str]] = None,
    snapshot: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot, typing.Dict[builtins.str, typing.Any]]] = None,
    time_series: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries, typing.Dict[builtins.str, typing.Any]]] = None,
    warehouse_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c10f0e606d1e2f1181c480f929f6725ec7dce0490e93c290119d0923231de674(
    *,
    definition: builtins.str,
    input_columns: typing.Sequence[builtins.str],
    name: builtins.str,
    output_data_type: builtins.str,
    type: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ea499615fb146d2b60eb23b4c367695aa41a21025fe3f661e287230ecaf4104a(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ece50e3e46cd98f1bf10e039e5c9ca681d5c7a162dffc606b196ac10d1e5d3ef(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bef5aa624f87eea9799ef452de9dd5a3cd7290ed8fc9d949ef455b375d5d0ae5(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__25544199e3f557ede250cd37fae7417cf1ecc4e551872838e66259e1806326d2(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e6cd70e94500aaffcbad4d8c31edc9624216a2e9ccd5b492c4ef33b10f5311ad(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7440b58e5ab2f43800fe6dc16a2ec29c6ae37ea53fd3fb7caa1019cacf5a3103(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__db0663bcd76a07c1735b147540dc9b95b3b45b08b2b300289d826ec3c1b4c9ef(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26f1f64d0dee5e4b6dcae270d0072976fe7444d16002563ad39325578735e0f1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e4f73ccc5127745eecbf271cd038ceccea1108664a7ee86d21de3ca7a1c8a818(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6fe84198c75f8b4c6d64d66d983c333a9b276112075cc267521adb10fb046025(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__54d254464ad14c369dccc4efa46939847975bd03279daf56ee327f7b79aa21fd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a9ef55a3ad829d3e37591972dc495fa9def5c0309030b3894b685ce9922ec575(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48e7508f5333c474d544365c65d8c1d3da964f66be06045fd89b0b8789d129b9(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2320109509455d6545195887f721a511b154fc0c2f02e4ca80876aa194f76f2a(
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

def _typecheckingstub__1cede4c1e0915b79450f7ea0c2c717501ca63c179473a49d52bfb30f12dcfeb9(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1d4c588d122eb327e369c2cef03ceda4650d1f300b0f406291a007ca979c9d70(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f3be275587494941d42de591af114e8df132d31f6051298b5f60b9b99af49f0a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a9dcec379a13f2415fed5c1e93ba673a98a43a89649c693b6a2fb3ec7652730d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0e5a0402ec937ef62e6b7f5dde9c81028de42e5aa9ce39e6a994a38d70daee03(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2df6ae86e5c072d8232917a6b0c8c23694c27816e3b5ca28e080ddaa9e447aae(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2e7182edb2fb1517dc92a3ff517af678b81e8f34b6c3eb044ff5dbca0ab9556a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a2a3b06b340aed88edd933bd18fb22c66197f0636432b4055c043511743ad2bc(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigInferenceLog]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f4ff2216c7ead7c5c5781b5aa5b000a8f0c0c73dc88ff239cd964e1a17fa7eb0(
    *,
    on_failure: typing.Optional[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6ea8ad61db92bad83c14aff0a5817b32d3d702eedafa049136a71e6e3516459c(
    *,
    email_addresses: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6446361f6d31648c96899cd30720027806b07ad67901ee3f925bd31c20e162af(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c2ddf3eeb12e35318ded2b760923cb2fdd302aede44cfb808cf294f5009c431c(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04adf5d484fc0cb88d3dc0a497ffd7b22173415dee1844018c0fc605c61dc5d3(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettingsOnFailure]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7daf3211b294dd5ef4279f1b0ccff87d435c6a1f6f84fdc41c8a8b5462b3dfd8(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__20e2da752fdb5839cef64075bc8c2fa193fa43c9a481eb729351a533ada079d6(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigNotificationSettings]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fe3c74d0556a4be5645f9cfbefa11833a2bd7307cfdceba66c4282184904d1eb(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c34379526e5a75b97b70383d1dd3af38f622dce8af55049e4915aeccf343c776(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksDataQualityMonitorDataProfilingConfigCustomMetrics, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7798ae8c164cefd9e5e46903eb247cb0ce5a4f649a0bccd339c39fe64bae6ca3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__82e6601ab1125642fe0895b59372db6a5ff683e2565fa9d55aa5317afa59ded3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dba3052b7310f005547a2ed741a341da6a81e8d4fae5bf8d5803470aa839920c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04f2bb882f62e9ff0820fbab2fd42812bc7127eef87f2cae4c45d00f3bb0ae48(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2936e07ec1e348c7e72fbf5a5f1f5630b09bcad30ba549d29dce251bb1e2a066(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__da8c7b4441b50e9c073e454863d7035a9a11d2a290c41e88a8c31f537f3be1ba(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5339d14b67952b77152887f90f38b004c67b3d32c6deeba5f985989f2a16d4ad(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfig]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7b5d15c8043f9d78f60da58b5e82895ff602365ced8d2a163e0e11c841cd788c(
    *,
    quartz_cron_expression: builtins.str,
    timezone_id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0a9a5e935cb6fe62c1620b73cc0f8ce9e1193941e0c76ed775be72df3727e722(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3ed332fd3afa6f8cb0934cee7ee12fd0d054493914ac5128efd73b355f53c67c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__df10cf3140854e76250ea17473281f4f87e99d4472c2b0834ea506b28cc9bbd2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e9acefac3b42927c8ebcda0fbd55d5d25f7f2bc9f7eecaf5998160cca2c9fe01(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigSchedule]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a78581a98875348d8d59e19282132c4cc3556a8c3290e9e835f4ddcddf9f8978(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8360bf291a98cbe27552539de30dbb68eecc373e80ceefaaca82f10147a3b4d7(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigSnapshot]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__044f739cc9a03a2a2c851626e90d1e0c43e06d7b232c2e87d76a28c6e3844c46(
    *,
    granularities: typing.Sequence[builtins.str],
    timestamp_column: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d2d7eec86bd83161f3f6a384178487ab33bc71178a93ed224338098a8ec55e51(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d71ac255e3b24227f568c4d5e54afe91c7806de0c27dced5063c89922d8fe2d7(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__840c7ab957df94c2e50843345b1dc583ce309b08afb1633a2027b16484c2a105(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__885b9f91ab4e90dfabd55bbeb758e954aba0284082c987cffc9371d96621170a(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksDataQualityMonitorDataProfilingConfigTimeSeries]],
) -> None:
    """Type checking stubs"""
    pass
