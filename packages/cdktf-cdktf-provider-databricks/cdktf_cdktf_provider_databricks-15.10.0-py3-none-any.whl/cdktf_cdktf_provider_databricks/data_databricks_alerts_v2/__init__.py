r'''
# `data_databricks_alerts_v2`

Refer to the Terraform Registry for docs: [`data_databricks_alerts_v2`](https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2).
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


class DataDatabricksAlertsV2(
    _cdktf_9a9027ec.TerraformDataSource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2 databricks_alerts_v2}.'''

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
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2 databricks_alerts_v2} Data Source.

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
            type_hints = typing.get_type_hints(_typecheckingstub__7ca2e6aaba880dad183280c8634fa7ff8bafc5fa410023353064e47441de3ca3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = DataDatabricksAlertsV2Config(
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
        '''Generates CDKTF code for importing a DataDatabricksAlertsV2 resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DataDatabricksAlertsV2 to import.
        :param import_from_id: The id of the existing DataDatabricksAlertsV2 that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DataDatabricksAlertsV2 to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__47439c8fc9a43b443fc6e8ee491c9c1e623a0c383ce734766dd63e3c246b5ea0)
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
    @jsii.member(jsii_name="alerts")
    def alerts(self) -> "DataDatabricksAlertsV2AlertsList":
        return typing.cast("DataDatabricksAlertsV2AlertsList", jsii.get(self, "alerts"))


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2Alerts",
    jsii_struct_bases=[],
    name_mapping={
        "id": "id",
        "custom_description": "customDescription",
        "custom_summary": "customSummary",
        "display_name": "displayName",
        "evaluation": "evaluation",
        "parent_path": "parentPath",
        "query_text": "queryText",
        "run_as": "runAs",
        "run_as_user_name": "runAsUserName",
        "schedule": "schedule",
        "warehouse_id": "warehouseId",
    },
)
class DataDatabricksAlertsV2Alerts:
    def __init__(
        self,
        *,
        id: builtins.str,
        custom_description: typing.Optional[builtins.str] = None,
        custom_summary: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        evaluation: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsEvaluation", typing.Dict[builtins.str, typing.Any]]] = None,
        parent_path: typing.Optional[builtins.str] = None,
        query_text: typing.Optional[builtins.str] = None,
        run_as: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsRunAs", typing.Dict[builtins.str, typing.Any]]] = None,
        run_as_user_name: typing.Optional[builtins.str] = None,
        schedule: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsSchedule", typing.Dict[builtins.str, typing.Any]]] = None,
        warehouse_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#id DataDatabricksAlertsV2#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param custom_description: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#custom_description DataDatabricksAlertsV2#custom_description}.
        :param custom_summary: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#custom_summary DataDatabricksAlertsV2#custom_summary}.
        :param display_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#display_name DataDatabricksAlertsV2#display_name}.
        :param evaluation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#evaluation DataDatabricksAlertsV2#evaluation}.
        :param parent_path: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#parent_path DataDatabricksAlertsV2#parent_path}.
        :param query_text: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#query_text DataDatabricksAlertsV2#query_text}.
        :param run_as: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#run_as DataDatabricksAlertsV2#run_as}.
        :param run_as_user_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#run_as_user_name DataDatabricksAlertsV2#run_as_user_name}.
        :param schedule: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#schedule DataDatabricksAlertsV2#schedule}.
        :param warehouse_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#warehouse_id DataDatabricksAlertsV2#warehouse_id}.
        '''
        if isinstance(evaluation, dict):
            evaluation = DataDatabricksAlertsV2AlertsEvaluation(**evaluation)
        if isinstance(run_as, dict):
            run_as = DataDatabricksAlertsV2AlertsRunAs(**run_as)
        if isinstance(schedule, dict):
            schedule = DataDatabricksAlertsV2AlertsSchedule(**schedule)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c86d8eb83e6f1e1d326a76d616c17b4662a534d1c7420eb3778cd73dc9bdb303)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument custom_description", value=custom_description, expected_type=type_hints["custom_description"])
            check_type(argname="argument custom_summary", value=custom_summary, expected_type=type_hints["custom_summary"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument evaluation", value=evaluation, expected_type=type_hints["evaluation"])
            check_type(argname="argument parent_path", value=parent_path, expected_type=type_hints["parent_path"])
            check_type(argname="argument query_text", value=query_text, expected_type=type_hints["query_text"])
            check_type(argname="argument run_as", value=run_as, expected_type=type_hints["run_as"])
            check_type(argname="argument run_as_user_name", value=run_as_user_name, expected_type=type_hints["run_as_user_name"])
            check_type(argname="argument schedule", value=schedule, expected_type=type_hints["schedule"])
            check_type(argname="argument warehouse_id", value=warehouse_id, expected_type=type_hints["warehouse_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }
        if custom_description is not None:
            self._values["custom_description"] = custom_description
        if custom_summary is not None:
            self._values["custom_summary"] = custom_summary
        if display_name is not None:
            self._values["display_name"] = display_name
        if evaluation is not None:
            self._values["evaluation"] = evaluation
        if parent_path is not None:
            self._values["parent_path"] = parent_path
        if query_text is not None:
            self._values["query_text"] = query_text
        if run_as is not None:
            self._values["run_as"] = run_as
        if run_as_user_name is not None:
            self._values["run_as_user_name"] = run_as_user_name
        if schedule is not None:
            self._values["schedule"] = schedule
        if warehouse_id is not None:
            self._values["warehouse_id"] = warehouse_id

    @builtins.property
    def id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#id DataDatabricksAlertsV2#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def custom_description(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#custom_description DataDatabricksAlertsV2#custom_description}.'''
        result = self._values.get("custom_description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def custom_summary(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#custom_summary DataDatabricksAlertsV2#custom_summary}.'''
        result = self._values.get("custom_summary")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#display_name DataDatabricksAlertsV2#display_name}.'''
        result = self._values.get("display_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def evaluation(self) -> typing.Optional["DataDatabricksAlertsV2AlertsEvaluation"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#evaluation DataDatabricksAlertsV2#evaluation}.'''
        result = self._values.get("evaluation")
        return typing.cast(typing.Optional["DataDatabricksAlertsV2AlertsEvaluation"], result)

    @builtins.property
    def parent_path(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#parent_path DataDatabricksAlertsV2#parent_path}.'''
        result = self._values.get("parent_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def query_text(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#query_text DataDatabricksAlertsV2#query_text}.'''
        result = self._values.get("query_text")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def run_as(self) -> typing.Optional["DataDatabricksAlertsV2AlertsRunAs"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#run_as DataDatabricksAlertsV2#run_as}.'''
        result = self._values.get("run_as")
        return typing.cast(typing.Optional["DataDatabricksAlertsV2AlertsRunAs"], result)

    @builtins.property
    def run_as_user_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#run_as_user_name DataDatabricksAlertsV2#run_as_user_name}.'''
        result = self._values.get("run_as_user_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def schedule(self) -> typing.Optional["DataDatabricksAlertsV2AlertsSchedule"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#schedule DataDatabricksAlertsV2#schedule}.'''
        result = self._values.get("schedule")
        return typing.cast(typing.Optional["DataDatabricksAlertsV2AlertsSchedule"], result)

    @builtins.property
    def warehouse_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#warehouse_id DataDatabricksAlertsV2#warehouse_id}.'''
        result = self._values.get("warehouse_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2Alerts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEffectiveRunAs",
    jsii_struct_bases=[],
    name_mapping={
        "service_principal_name": "servicePrincipalName",
        "user_name": "userName",
    },
)
class DataDatabricksAlertsV2AlertsEffectiveRunAs:
    def __init__(
        self,
        *,
        service_principal_name: typing.Optional[builtins.str] = None,
        user_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param service_principal_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#service_principal_name DataDatabricksAlertsV2#service_principal_name}.
        :param user_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#user_name DataDatabricksAlertsV2#user_name}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e47f7968a528cb84bec9d227b05324ccfaf6b76405af875f00e290457433fb4d)
            check_type(argname="argument service_principal_name", value=service_principal_name, expected_type=type_hints["service_principal_name"])
            check_type(argname="argument user_name", value=user_name, expected_type=type_hints["user_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if service_principal_name is not None:
            self._values["service_principal_name"] = service_principal_name
        if user_name is not None:
            self._values["user_name"] = user_name

    @builtins.property
    def service_principal_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#service_principal_name DataDatabricksAlertsV2#service_principal_name}.'''
        result = self._values.get("service_principal_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def user_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#user_name DataDatabricksAlertsV2#user_name}.'''
        result = self._values.get("user_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsEffectiveRunAs(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksAlertsV2AlertsEffectiveRunAsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEffectiveRunAsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__529054c58e405b94cea579d6a7225415dbaa5d7fc84e2b3c2df99d3b23b6346d)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetServicePrincipalName")
    def reset_service_principal_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServicePrincipalName", []))

    @jsii.member(jsii_name="resetUserName")
    def reset_user_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUserName", []))

    @builtins.property
    @jsii.member(jsii_name="servicePrincipalNameInput")
    def service_principal_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "servicePrincipalNameInput"))

    @builtins.property
    @jsii.member(jsii_name="userNameInput")
    def user_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userNameInput"))

    @builtins.property
    @jsii.member(jsii_name="servicePrincipalName")
    def service_principal_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "servicePrincipalName"))

    @service_principal_name.setter
    def service_principal_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__36067428f3ed10cb90156f7a20a66f8150f13404711d4dbdff9fd44eb339636d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "servicePrincipalName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="userName")
    def user_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "userName"))

    @user_name.setter
    def user_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__12b31339c29955ae8688854a27c598f535b793b693171a59ac0b237f81eea8eb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "userName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[DataDatabricksAlertsV2AlertsEffectiveRunAs]:
        return typing.cast(typing.Optional[DataDatabricksAlertsV2AlertsEffectiveRunAs], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DataDatabricksAlertsV2AlertsEffectiveRunAs],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5e0cca8a561f5108f842ae6f051c268e6e61b6849dabd4d06626cbdae86933c0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluation",
    jsii_struct_bases=[],
    name_mapping={
        "comparison_operator": "comparisonOperator",
        "empty_result_state": "emptyResultState",
        "notification": "notification",
        "source": "source",
        "threshold": "threshold",
    },
)
class DataDatabricksAlertsV2AlertsEvaluation:
    def __init__(
        self,
        *,
        comparison_operator: typing.Optional[builtins.str] = None,
        empty_result_state: typing.Optional[builtins.str] = None,
        notification: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsEvaluationNotification", typing.Dict[builtins.str, typing.Any]]] = None,
        source: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsEvaluationSource", typing.Dict[builtins.str, typing.Any]]] = None,
        threshold: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsEvaluationThreshold", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param comparison_operator: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#comparison_operator DataDatabricksAlertsV2#comparison_operator}.
        :param empty_result_state: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#empty_result_state DataDatabricksAlertsV2#empty_result_state}.
        :param notification: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#notification DataDatabricksAlertsV2#notification}.
        :param source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#source DataDatabricksAlertsV2#source}.
        :param threshold: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#threshold DataDatabricksAlertsV2#threshold}.
        '''
        if isinstance(notification, dict):
            notification = DataDatabricksAlertsV2AlertsEvaluationNotification(**notification)
        if isinstance(source, dict):
            source = DataDatabricksAlertsV2AlertsEvaluationSource(**source)
        if isinstance(threshold, dict):
            threshold = DataDatabricksAlertsV2AlertsEvaluationThreshold(**threshold)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d1fc1495b9e85023cababc9c89d04134088d33b23e8aa1106c158a94b58e0640)
            check_type(argname="argument comparison_operator", value=comparison_operator, expected_type=type_hints["comparison_operator"])
            check_type(argname="argument empty_result_state", value=empty_result_state, expected_type=type_hints["empty_result_state"])
            check_type(argname="argument notification", value=notification, expected_type=type_hints["notification"])
            check_type(argname="argument source", value=source, expected_type=type_hints["source"])
            check_type(argname="argument threshold", value=threshold, expected_type=type_hints["threshold"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if comparison_operator is not None:
            self._values["comparison_operator"] = comparison_operator
        if empty_result_state is not None:
            self._values["empty_result_state"] = empty_result_state
        if notification is not None:
            self._values["notification"] = notification
        if source is not None:
            self._values["source"] = source
        if threshold is not None:
            self._values["threshold"] = threshold

    @builtins.property
    def comparison_operator(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#comparison_operator DataDatabricksAlertsV2#comparison_operator}.'''
        result = self._values.get("comparison_operator")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def empty_result_state(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#empty_result_state DataDatabricksAlertsV2#empty_result_state}.'''
        result = self._values.get("empty_result_state")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def notification(
        self,
    ) -> typing.Optional["DataDatabricksAlertsV2AlertsEvaluationNotification"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#notification DataDatabricksAlertsV2#notification}.'''
        result = self._values.get("notification")
        return typing.cast(typing.Optional["DataDatabricksAlertsV2AlertsEvaluationNotification"], result)

    @builtins.property
    def source(self) -> typing.Optional["DataDatabricksAlertsV2AlertsEvaluationSource"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#source DataDatabricksAlertsV2#source}.'''
        result = self._values.get("source")
        return typing.cast(typing.Optional["DataDatabricksAlertsV2AlertsEvaluationSource"], result)

    @builtins.property
    def threshold(
        self,
    ) -> typing.Optional["DataDatabricksAlertsV2AlertsEvaluationThreshold"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#threshold DataDatabricksAlertsV2#threshold}.'''
        result = self._values.get("threshold")
        return typing.cast(typing.Optional["DataDatabricksAlertsV2AlertsEvaluationThreshold"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsEvaluation(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationNotification",
    jsii_struct_bases=[],
    name_mapping={
        "notify_on_ok": "notifyOnOk",
        "retrigger_seconds": "retriggerSeconds",
        "subscriptions": "subscriptions",
    },
)
class DataDatabricksAlertsV2AlertsEvaluationNotification:
    def __init__(
        self,
        *,
        notify_on_ok: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        retrigger_seconds: typing.Optional[jsii.Number] = None,
        subscriptions: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions", typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''
        :param notify_on_ok: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#notify_on_ok DataDatabricksAlertsV2#notify_on_ok}.
        :param retrigger_seconds: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#retrigger_seconds DataDatabricksAlertsV2#retrigger_seconds}.
        :param subscriptions: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#subscriptions DataDatabricksAlertsV2#subscriptions}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__24cba6c7edc93d2a67645f0e6d7fee3fcdf3815c22dacdecc6205aecc04cea3f)
            check_type(argname="argument notify_on_ok", value=notify_on_ok, expected_type=type_hints["notify_on_ok"])
            check_type(argname="argument retrigger_seconds", value=retrigger_seconds, expected_type=type_hints["retrigger_seconds"])
            check_type(argname="argument subscriptions", value=subscriptions, expected_type=type_hints["subscriptions"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if notify_on_ok is not None:
            self._values["notify_on_ok"] = notify_on_ok
        if retrigger_seconds is not None:
            self._values["retrigger_seconds"] = retrigger_seconds
        if subscriptions is not None:
            self._values["subscriptions"] = subscriptions

    @builtins.property
    def notify_on_ok(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#notify_on_ok DataDatabricksAlertsV2#notify_on_ok}.'''
        result = self._values.get("notify_on_ok")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def retrigger_seconds(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#retrigger_seconds DataDatabricksAlertsV2#retrigger_seconds}.'''
        result = self._values.get("retrigger_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def subscriptions(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions"]]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#subscriptions DataDatabricksAlertsV2#subscriptions}.'''
        result = self._values.get("subscriptions")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions"]]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsEvaluationNotification(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksAlertsV2AlertsEvaluationNotificationOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationNotificationOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__22401e0955c944d51954b0e0c55033a7639629b280243e6aa5b586f187615d92)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putSubscriptions")
    def put_subscriptions(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b5a20e6e37adde7f2e4e2042c8dcbd68b8caca5247c792aeee93e6333131faf3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putSubscriptions", [value]))

    @jsii.member(jsii_name="resetNotifyOnOk")
    def reset_notify_on_ok(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNotifyOnOk", []))

    @jsii.member(jsii_name="resetRetriggerSeconds")
    def reset_retrigger_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRetriggerSeconds", []))

    @jsii.member(jsii_name="resetSubscriptions")
    def reset_subscriptions(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSubscriptions", []))

    @builtins.property
    @jsii.member(jsii_name="subscriptions")
    def subscriptions(
        self,
    ) -> "DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsList":
        return typing.cast("DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsList", jsii.get(self, "subscriptions"))

    @builtins.property
    @jsii.member(jsii_name="notifyOnOkInput")
    def notify_on_ok_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "notifyOnOkInput"))

    @builtins.property
    @jsii.member(jsii_name="retriggerSecondsInput")
    def retrigger_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "retriggerSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionsInput")
    def subscriptions_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions"]]], jsii.get(self, "subscriptionsInput"))

    @builtins.property
    @jsii.member(jsii_name="notifyOnOk")
    def notify_on_ok(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "notifyOnOk"))

    @notify_on_ok.setter
    def notify_on_ok(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__927861417dbc2e9b5b503a24cfd982b7340e5790e223330ff59b3ca91a931a42)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "notifyOnOk", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="retriggerSeconds")
    def retrigger_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "retriggerSeconds"))

    @retrigger_seconds.setter
    def retrigger_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__736dd48d4d2e3ed3fdd64bafc1365833bafbf42206fdad5faab4e08239e27768)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "retriggerSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotification]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotification]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotification]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__be530556c9c02ce57adb2b8bf53f2d75025da22028d64e57c10321ba5c0aeb1d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions",
    jsii_struct_bases=[],
    name_mapping={"destination_id": "destinationId", "user_email": "userEmail"},
)
class DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions:
    def __init__(
        self,
        *,
        destination_id: typing.Optional[builtins.str] = None,
        user_email: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param destination_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#destination_id DataDatabricksAlertsV2#destination_id}.
        :param user_email: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#user_email DataDatabricksAlertsV2#user_email}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3e9657043a13ac35f2e5188a6947fdae6b0d767cf9d3c89395c282d9154f8e56)
            check_type(argname="argument destination_id", value=destination_id, expected_type=type_hints["destination_id"])
            check_type(argname="argument user_email", value=user_email, expected_type=type_hints["user_email"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if destination_id is not None:
            self._values["destination_id"] = destination_id
        if user_email is not None:
            self._values["user_email"] = user_email

    @builtins.property
    def destination_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#destination_id DataDatabricksAlertsV2#destination_id}.'''
        result = self._values.get("destination_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def user_email(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#user_email DataDatabricksAlertsV2#user_email}.'''
        result = self._values.get("user_email")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__4756d8712a2542267931c591b9f9a79c49725648a800f19be559da719317363e)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ebeeac31cde3041b7adf95dd81f5a1dbef4161f5f4e67afe97dfa40ccab506ce)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5ac9428d9c04c52ef4da2f31c17cf114dce6adc6dc4543185e8c9eb9585f7895)
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
            type_hints = typing.get_type_hints(_typecheckingstub__6db8e57dfaadcf9196f9830aa8638cf2adeee54c2872bfef9f915bd84b87b7eb)
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
            type_hints = typing.get_type_hints(_typecheckingstub__138c212512ec198c91321309e619775f744984aefb9e1ed308483847c7851902)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__aca2799c3f15c6e374d4f73e4e596f40b870644b76112cb12d4b416168706c05)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__e9b3e6e21bea8d69cd943d2e19a18087ba492b93f004160d91a55a54a0f5ee09)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetDestinationId")
    def reset_destination_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDestinationId", []))

    @jsii.member(jsii_name="resetUserEmail")
    def reset_user_email(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUserEmail", []))

    @builtins.property
    @jsii.member(jsii_name="destinationIdInput")
    def destination_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "destinationIdInput"))

    @builtins.property
    @jsii.member(jsii_name="userEmailInput")
    def user_email_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userEmailInput"))

    @builtins.property
    @jsii.member(jsii_name="destinationId")
    def destination_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "destinationId"))

    @destination_id.setter
    def destination_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__075de387b50179ea4cbbcfb614ac8b57caf8e03003257178af61e2cc104a3f75)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "destinationId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="userEmail")
    def user_email(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "userEmail"))

    @user_email.setter
    def user_email(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f919ff2dc722407bf7595fe7ad11470bd498a71f40b9c91bcb81ae5b85306643)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "userEmail", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e1a04412ad02aacdec25ca3902b99337e331e61d41bf9f8ebb7500a2647781d4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksAlertsV2AlertsEvaluationOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__04abf6ef3fb63e5887a4ef558bdb6838507e1fcd2d3e35a0ca0526b0a29eb774)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putNotification")
    def put_notification(
        self,
        *,
        notify_on_ok: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        retrigger_seconds: typing.Optional[jsii.Number] = None,
        subscriptions: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''
        :param notify_on_ok: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#notify_on_ok DataDatabricksAlertsV2#notify_on_ok}.
        :param retrigger_seconds: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#retrigger_seconds DataDatabricksAlertsV2#retrigger_seconds}.
        :param subscriptions: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#subscriptions DataDatabricksAlertsV2#subscriptions}.
        '''
        value = DataDatabricksAlertsV2AlertsEvaluationNotification(
            notify_on_ok=notify_on_ok,
            retrigger_seconds=retrigger_seconds,
            subscriptions=subscriptions,
        )

        return typing.cast(None, jsii.invoke(self, "putNotification", [value]))

    @jsii.member(jsii_name="putSource")
    def put_source(
        self,
        *,
        aggregation: typing.Optional[builtins.str] = None,
        display: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param aggregation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#aggregation DataDatabricksAlertsV2#aggregation}.
        :param display: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#display DataDatabricksAlertsV2#display}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#name DataDatabricksAlertsV2#name}.
        '''
        value = DataDatabricksAlertsV2AlertsEvaluationSource(
            aggregation=aggregation, display=display, name=name
        )

        return typing.cast(None, jsii.invoke(self, "putSource", [value]))

    @jsii.member(jsii_name="putThreshold")
    def put_threshold(
        self,
        *,
        column: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsEvaluationThresholdColumn", typing.Dict[builtins.str, typing.Any]]] = None,
        value: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsEvaluationThresholdValue", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#column DataDatabricksAlertsV2#column}.
        :param value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#value DataDatabricksAlertsV2#value}.
        '''
        value_ = DataDatabricksAlertsV2AlertsEvaluationThreshold(
            column=column, value=value
        )

        return typing.cast(None, jsii.invoke(self, "putThreshold", [value_]))

    @jsii.member(jsii_name="resetComparisonOperator")
    def reset_comparison_operator(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetComparisonOperator", []))

    @jsii.member(jsii_name="resetEmptyResultState")
    def reset_empty_result_state(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEmptyResultState", []))

    @jsii.member(jsii_name="resetNotification")
    def reset_notification(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetNotification", []))

    @jsii.member(jsii_name="resetSource")
    def reset_source(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSource", []))

    @jsii.member(jsii_name="resetThreshold")
    def reset_threshold(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetThreshold", []))

    @builtins.property
    @jsii.member(jsii_name="lastEvaluatedAt")
    def last_evaluated_at(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lastEvaluatedAt"))

    @builtins.property
    @jsii.member(jsii_name="notification")
    def notification(
        self,
    ) -> DataDatabricksAlertsV2AlertsEvaluationNotificationOutputReference:
        return typing.cast(DataDatabricksAlertsV2AlertsEvaluationNotificationOutputReference, jsii.get(self, "notification"))

    @builtins.property
    @jsii.member(jsii_name="source")
    def source(self) -> "DataDatabricksAlertsV2AlertsEvaluationSourceOutputReference":
        return typing.cast("DataDatabricksAlertsV2AlertsEvaluationSourceOutputReference", jsii.get(self, "source"))

    @builtins.property
    @jsii.member(jsii_name="state")
    def state(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "state"))

    @builtins.property
    @jsii.member(jsii_name="threshold")
    def threshold(
        self,
    ) -> "DataDatabricksAlertsV2AlertsEvaluationThresholdOutputReference":
        return typing.cast("DataDatabricksAlertsV2AlertsEvaluationThresholdOutputReference", jsii.get(self, "threshold"))

    @builtins.property
    @jsii.member(jsii_name="comparisonOperatorInput")
    def comparison_operator_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "comparisonOperatorInput"))

    @builtins.property
    @jsii.member(jsii_name="emptyResultStateInput")
    def empty_result_state_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "emptyResultStateInput"))

    @builtins.property
    @jsii.member(jsii_name="notificationInput")
    def notification_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotification]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotification]], jsii.get(self, "notificationInput"))

    @builtins.property
    @jsii.member(jsii_name="sourceInput")
    def source_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsEvaluationSource"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsEvaluationSource"]], jsii.get(self, "sourceInput"))

    @builtins.property
    @jsii.member(jsii_name="thresholdInput")
    def threshold_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsEvaluationThreshold"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsEvaluationThreshold"]], jsii.get(self, "thresholdInput"))

    @builtins.property
    @jsii.member(jsii_name="comparisonOperator")
    def comparison_operator(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "comparisonOperator"))

    @comparison_operator.setter
    def comparison_operator(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f5235987cd8661b1e7d9ab8141038a39f80edd72827a32cddc0438c901f3d291)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "comparisonOperator", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="emptyResultState")
    def empty_result_state(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "emptyResultState"))

    @empty_result_state.setter
    def empty_result_state(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a3fbc6a4f58f3308163e33d9884e01fc8d23700df269334db3f39ed4b0bb464e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "emptyResultState", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluation]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluation]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluation]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__acf3101a143ad5d041815808c540b528fd7d9583d6f1389f9871f0db9e3aeeb9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationSource",
    jsii_struct_bases=[],
    name_mapping={"aggregation": "aggregation", "display": "display", "name": "name"},
)
class DataDatabricksAlertsV2AlertsEvaluationSource:
    def __init__(
        self,
        *,
        aggregation: typing.Optional[builtins.str] = None,
        display: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param aggregation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#aggregation DataDatabricksAlertsV2#aggregation}.
        :param display: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#display DataDatabricksAlertsV2#display}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#name DataDatabricksAlertsV2#name}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bcc813bb211ef8adfdafd1afaa6baa7128302b999bed0229cffeb098f6092650)
            check_type(argname="argument aggregation", value=aggregation, expected_type=type_hints["aggregation"])
            check_type(argname="argument display", value=display, expected_type=type_hints["display"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if aggregation is not None:
            self._values["aggregation"] = aggregation
        if display is not None:
            self._values["display"] = display
        if name is not None:
            self._values["name"] = name

    @builtins.property
    def aggregation(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#aggregation DataDatabricksAlertsV2#aggregation}.'''
        result = self._values.get("aggregation")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#display DataDatabricksAlertsV2#display}.'''
        result = self._values.get("display")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#name DataDatabricksAlertsV2#name}.'''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsEvaluationSource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksAlertsV2AlertsEvaluationSourceOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationSourceOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__6317a3ea38ca9cfbf6968608213e809f4a69fe5127369125b209da5e2901d03d)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetAggregation")
    def reset_aggregation(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAggregation", []))

    @jsii.member(jsii_name="resetDisplay")
    def reset_display(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDisplay", []))

    @jsii.member(jsii_name="resetName")
    def reset_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetName", []))

    @builtins.property
    @jsii.member(jsii_name="aggregationInput")
    def aggregation_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "aggregationInput"))

    @builtins.property
    @jsii.member(jsii_name="displayInput")
    def display_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "displayInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="aggregation")
    def aggregation(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "aggregation"))

    @aggregation.setter
    def aggregation(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dbe092f0f6fa7eb789052e4794703368429a5e90e2a32bb5448b3f0e65d2cf5c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "aggregation", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="display")
    def display(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "display"))

    @display.setter
    def display(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__20b18c1b2a7a7878054a2e8e250d0c766d8e94460f0d4322820fdbc72ee6881e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "display", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6cc5e6a110b0953f7d767c5fbbaa89d4c2e6cca2be4a986255b080500583e381)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationSource]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationSource]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationSource]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__704804355ff8a91544b07e0d4b4b8880e436ca998ade6275a6b21142bb1deba3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationThreshold",
    jsii_struct_bases=[],
    name_mapping={"column": "column", "value": "value"},
)
class DataDatabricksAlertsV2AlertsEvaluationThreshold:
    def __init__(
        self,
        *,
        column: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsEvaluationThresholdColumn", typing.Dict[builtins.str, typing.Any]]] = None,
        value: typing.Optional[typing.Union["DataDatabricksAlertsV2AlertsEvaluationThresholdValue", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param column: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#column DataDatabricksAlertsV2#column}.
        :param value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#value DataDatabricksAlertsV2#value}.
        '''
        if isinstance(column, dict):
            column = DataDatabricksAlertsV2AlertsEvaluationThresholdColumn(**column)
        if isinstance(value, dict):
            value = DataDatabricksAlertsV2AlertsEvaluationThresholdValue(**value)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3e992e46fa0626f9880b9081659490071c72e4e575daeaa40e3fd2ca8c8224df)
            check_type(argname="argument column", value=column, expected_type=type_hints["column"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if column is not None:
            self._values["column"] = column
        if value is not None:
            self._values["value"] = value

    @builtins.property
    def column(
        self,
    ) -> typing.Optional["DataDatabricksAlertsV2AlertsEvaluationThresholdColumn"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#column DataDatabricksAlertsV2#column}.'''
        result = self._values.get("column")
        return typing.cast(typing.Optional["DataDatabricksAlertsV2AlertsEvaluationThresholdColumn"], result)

    @builtins.property
    def value(
        self,
    ) -> typing.Optional["DataDatabricksAlertsV2AlertsEvaluationThresholdValue"]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#value DataDatabricksAlertsV2#value}.'''
        result = self._values.get("value")
        return typing.cast(typing.Optional["DataDatabricksAlertsV2AlertsEvaluationThresholdValue"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsEvaluationThreshold(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationThresholdColumn",
    jsii_struct_bases=[],
    name_mapping={"aggregation": "aggregation", "display": "display", "name": "name"},
)
class DataDatabricksAlertsV2AlertsEvaluationThresholdColumn:
    def __init__(
        self,
        *,
        aggregation: typing.Optional[builtins.str] = None,
        display: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param aggregation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#aggregation DataDatabricksAlertsV2#aggregation}.
        :param display: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#display DataDatabricksAlertsV2#display}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#name DataDatabricksAlertsV2#name}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f048da9bbe75ad73530618487893c39f89e6c0414748f52f29395fe56128f9f4)
            check_type(argname="argument aggregation", value=aggregation, expected_type=type_hints["aggregation"])
            check_type(argname="argument display", value=display, expected_type=type_hints["display"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if aggregation is not None:
            self._values["aggregation"] = aggregation
        if display is not None:
            self._values["display"] = display
        if name is not None:
            self._values["name"] = name

    @builtins.property
    def aggregation(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#aggregation DataDatabricksAlertsV2#aggregation}.'''
        result = self._values.get("aggregation")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#display DataDatabricksAlertsV2#display}.'''
        result = self._values.get("display")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#name DataDatabricksAlertsV2#name}.'''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsEvaluationThresholdColumn(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksAlertsV2AlertsEvaluationThresholdColumnOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationThresholdColumnOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__44ae4848c1adbb5e9439177d9a075e1a2ee2ef7561e08bda48eb06d09caafb8e)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetAggregation")
    def reset_aggregation(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAggregation", []))

    @jsii.member(jsii_name="resetDisplay")
    def reset_display(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDisplay", []))

    @jsii.member(jsii_name="resetName")
    def reset_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetName", []))

    @builtins.property
    @jsii.member(jsii_name="aggregationInput")
    def aggregation_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "aggregationInput"))

    @builtins.property
    @jsii.member(jsii_name="displayInput")
    def display_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "displayInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="aggregation")
    def aggregation(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "aggregation"))

    @aggregation.setter
    def aggregation(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__784183626e6818e6cf1316753b78577ae5539cb770d174df818b16c20aaaa0a4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "aggregation", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="display")
    def display(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "display"))

    @display.setter
    def display(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3d3826652f7a6d2cfbb5d1ab1e64f91ba0b7d51d9b140ff377cd42851195e16c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "display", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cc22efc96d5de73dbfd5bf5cecf9c4ee9fb809adddc555479b202c921e6c469e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdColumn]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdColumn]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdColumn]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ed33e1377e13d12ed10e44ceb4b704acd6f87f55f53b5360dec445a3a60d4ad3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksAlertsV2AlertsEvaluationThresholdOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationThresholdOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__506505f61ff077a25b5d1914b74d053107af1777dd283a680a721cfe7fce01af)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putColumn")
    def put_column(
        self,
        *,
        aggregation: typing.Optional[builtins.str] = None,
        display: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param aggregation: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#aggregation DataDatabricksAlertsV2#aggregation}.
        :param display: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#display DataDatabricksAlertsV2#display}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#name DataDatabricksAlertsV2#name}.
        '''
        value = DataDatabricksAlertsV2AlertsEvaluationThresholdColumn(
            aggregation=aggregation, display=display, name=name
        )

        return typing.cast(None, jsii.invoke(self, "putColumn", [value]))

    @jsii.member(jsii_name="putValue")
    def put_value(
        self,
        *,
        bool_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        double_value: typing.Optional[jsii.Number] = None,
        string_value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param bool_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#bool_value DataDatabricksAlertsV2#bool_value}.
        :param double_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#double_value DataDatabricksAlertsV2#double_value}.
        :param string_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#string_value DataDatabricksAlertsV2#string_value}.
        '''
        value = DataDatabricksAlertsV2AlertsEvaluationThresholdValue(
            bool_value=bool_value, double_value=double_value, string_value=string_value
        )

        return typing.cast(None, jsii.invoke(self, "putValue", [value]))

    @jsii.member(jsii_name="resetColumn")
    def reset_column(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetColumn", []))

    @jsii.member(jsii_name="resetValue")
    def reset_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetValue", []))

    @builtins.property
    @jsii.member(jsii_name="column")
    def column(
        self,
    ) -> DataDatabricksAlertsV2AlertsEvaluationThresholdColumnOutputReference:
        return typing.cast(DataDatabricksAlertsV2AlertsEvaluationThresholdColumnOutputReference, jsii.get(self, "column"))

    @builtins.property
    @jsii.member(jsii_name="value")
    def value(
        self,
    ) -> "DataDatabricksAlertsV2AlertsEvaluationThresholdValueOutputReference":
        return typing.cast("DataDatabricksAlertsV2AlertsEvaluationThresholdValueOutputReference", jsii.get(self, "value"))

    @builtins.property
    @jsii.member(jsii_name="columnInput")
    def column_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdColumn]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdColumn]], jsii.get(self, "columnInput"))

    @builtins.property
    @jsii.member(jsii_name="valueInput")
    def value_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsEvaluationThresholdValue"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsEvaluationThresholdValue"]], jsii.get(self, "valueInput"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThreshold]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThreshold]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThreshold]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4f981da2546e8eea3ef293ee948a2438f8b0814b413df82e5f73bffe86e76e4d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationThresholdValue",
    jsii_struct_bases=[],
    name_mapping={
        "bool_value": "boolValue",
        "double_value": "doubleValue",
        "string_value": "stringValue",
    },
)
class DataDatabricksAlertsV2AlertsEvaluationThresholdValue:
    def __init__(
        self,
        *,
        bool_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        double_value: typing.Optional[jsii.Number] = None,
        string_value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param bool_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#bool_value DataDatabricksAlertsV2#bool_value}.
        :param double_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#double_value DataDatabricksAlertsV2#double_value}.
        :param string_value: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#string_value DataDatabricksAlertsV2#string_value}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7dd94682873add4f2aecba9435821c78e9eb48d37a3fbfb2ae8dd1be600818a7)
            check_type(argname="argument bool_value", value=bool_value, expected_type=type_hints["bool_value"])
            check_type(argname="argument double_value", value=double_value, expected_type=type_hints["double_value"])
            check_type(argname="argument string_value", value=string_value, expected_type=type_hints["string_value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if bool_value is not None:
            self._values["bool_value"] = bool_value
        if double_value is not None:
            self._values["double_value"] = double_value
        if string_value is not None:
            self._values["string_value"] = string_value

    @builtins.property
    def bool_value(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#bool_value DataDatabricksAlertsV2#bool_value}.'''
        result = self._values.get("bool_value")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def double_value(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#double_value DataDatabricksAlertsV2#double_value}.'''
        result = self._values.get("double_value")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def string_value(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#string_value DataDatabricksAlertsV2#string_value}.'''
        result = self._values.get("string_value")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsEvaluationThresholdValue(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksAlertsV2AlertsEvaluationThresholdValueOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsEvaluationThresholdValueOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__045463279ee4c143a1221170d04cd0178900e1b6b7185c1f51d8ad68ad77a361)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetBoolValue")
    def reset_bool_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBoolValue", []))

    @jsii.member(jsii_name="resetDoubleValue")
    def reset_double_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDoubleValue", []))

    @jsii.member(jsii_name="resetStringValue")
    def reset_string_value(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetStringValue", []))

    @builtins.property
    @jsii.member(jsii_name="boolValueInput")
    def bool_value_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "boolValueInput"))

    @builtins.property
    @jsii.member(jsii_name="doubleValueInput")
    def double_value_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "doubleValueInput"))

    @builtins.property
    @jsii.member(jsii_name="stringValueInput")
    def string_value_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "stringValueInput"))

    @builtins.property
    @jsii.member(jsii_name="boolValue")
    def bool_value(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "boolValue"))

    @bool_value.setter
    def bool_value(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b39a091dfd3b16a3cf72bd87dfe6a075a5fc6c87edd20b3a456c4dcba54f0a32)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "boolValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="doubleValue")
    def double_value(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "doubleValue"))

    @double_value.setter
    def double_value(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__08a1b276f4505c402d42dbca17f718a319b892111db92ef1a088757b994cf1bf)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "doubleValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stringValue")
    def string_value(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "stringValue"))

    @string_value.setter
    def string_value(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c9a33c806bc779c766196eae93273283edcce226d05976da21da460762429615)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stringValue", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdValue]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdValue]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdValue]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6b222ef0619ddd2694e9afda51672a94c506007c806feb48dca6545441d4c3cd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksAlertsV2AlertsList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__efc3a54277d0ad2c32b61188d93cc0fb4dfa580dd07f78cad911477ca4e4779c)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(self, index: jsii.Number) -> "DataDatabricksAlertsV2AlertsOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__53be1be344c63a2fcaf7574cb2c6e0ede420b0ce45b2b63d2af4670c34575a17)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("DataDatabricksAlertsV2AlertsOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__837b94a604227ed2bb3ff427bc7c00f4d01cce9fdba8318dfa24d1fd4dccc3cf)
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
            type_hints = typing.get_type_hints(_typecheckingstub__2b94a1424f173c30f87050b6913731d06ca35bced76a8b2a88bf61bdfa50325a)
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
            type_hints = typing.get_type_hints(_typecheckingstub__a7fefaa56ed806d7ce7fe51c31467caf90c2b2e57cafaf53b3493f7c1c0fc6d9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksAlertsV2Alerts]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksAlertsV2Alerts]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksAlertsV2Alerts]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a79b4d4c6681893bc95e6d15ece74e5a6247becffde9f0eb8910101eadfe7052)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataDatabricksAlertsV2AlertsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__0da437268a3bceff1db53d12bf7eaef2ba4fd300fa984213b8d33e8e8d4ea3d6)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="putEvaluation")
    def put_evaluation(
        self,
        *,
        comparison_operator: typing.Optional[builtins.str] = None,
        empty_result_state: typing.Optional[builtins.str] = None,
        notification: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsEvaluationNotification, typing.Dict[builtins.str, typing.Any]]] = None,
        source: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsEvaluationSource, typing.Dict[builtins.str, typing.Any]]] = None,
        threshold: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsEvaluationThreshold, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param comparison_operator: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#comparison_operator DataDatabricksAlertsV2#comparison_operator}.
        :param empty_result_state: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#empty_result_state DataDatabricksAlertsV2#empty_result_state}.
        :param notification: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#notification DataDatabricksAlertsV2#notification}.
        :param source: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#source DataDatabricksAlertsV2#source}.
        :param threshold: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#threshold DataDatabricksAlertsV2#threshold}.
        '''
        value = DataDatabricksAlertsV2AlertsEvaluation(
            comparison_operator=comparison_operator,
            empty_result_state=empty_result_state,
            notification=notification,
            source=source,
            threshold=threshold,
        )

        return typing.cast(None, jsii.invoke(self, "putEvaluation", [value]))

    @jsii.member(jsii_name="putRunAs")
    def put_run_as(
        self,
        *,
        service_principal_name: typing.Optional[builtins.str] = None,
        user_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param service_principal_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#service_principal_name DataDatabricksAlertsV2#service_principal_name}.
        :param user_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#user_name DataDatabricksAlertsV2#user_name}.
        '''
        value = DataDatabricksAlertsV2AlertsRunAs(
            service_principal_name=service_principal_name, user_name=user_name
        )

        return typing.cast(None, jsii.invoke(self, "putRunAs", [value]))

    @jsii.member(jsii_name="putSchedule")
    def put_schedule(
        self,
        *,
        pause_status: typing.Optional[builtins.str] = None,
        quartz_cron_schedule: typing.Optional[builtins.str] = None,
        timezone_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param pause_status: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#pause_status DataDatabricksAlertsV2#pause_status}.
        :param quartz_cron_schedule: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#quartz_cron_schedule DataDatabricksAlertsV2#quartz_cron_schedule}.
        :param timezone_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#timezone_id DataDatabricksAlertsV2#timezone_id}.
        '''
        value = DataDatabricksAlertsV2AlertsSchedule(
            pause_status=pause_status,
            quartz_cron_schedule=quartz_cron_schedule,
            timezone_id=timezone_id,
        )

        return typing.cast(None, jsii.invoke(self, "putSchedule", [value]))

    @jsii.member(jsii_name="resetCustomDescription")
    def reset_custom_description(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCustomDescription", []))

    @jsii.member(jsii_name="resetCustomSummary")
    def reset_custom_summary(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCustomSummary", []))

    @jsii.member(jsii_name="resetDisplayName")
    def reset_display_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDisplayName", []))

    @jsii.member(jsii_name="resetEvaluation")
    def reset_evaluation(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEvaluation", []))

    @jsii.member(jsii_name="resetParentPath")
    def reset_parent_path(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetParentPath", []))

    @jsii.member(jsii_name="resetQueryText")
    def reset_query_text(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetQueryText", []))

    @jsii.member(jsii_name="resetRunAs")
    def reset_run_as(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRunAs", []))

    @jsii.member(jsii_name="resetRunAsUserName")
    def reset_run_as_user_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRunAsUserName", []))

    @jsii.member(jsii_name="resetSchedule")
    def reset_schedule(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSchedule", []))

    @jsii.member(jsii_name="resetWarehouseId")
    def reset_warehouse_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetWarehouseId", []))

    @builtins.property
    @jsii.member(jsii_name="createTime")
    def create_time(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "createTime"))

    @builtins.property
    @jsii.member(jsii_name="effectiveRunAs")
    def effective_run_as(
        self,
    ) -> DataDatabricksAlertsV2AlertsEffectiveRunAsOutputReference:
        return typing.cast(DataDatabricksAlertsV2AlertsEffectiveRunAsOutputReference, jsii.get(self, "effectiveRunAs"))

    @builtins.property
    @jsii.member(jsii_name="evaluation")
    def evaluation(self) -> DataDatabricksAlertsV2AlertsEvaluationOutputReference:
        return typing.cast(DataDatabricksAlertsV2AlertsEvaluationOutputReference, jsii.get(self, "evaluation"))

    @builtins.property
    @jsii.member(jsii_name="lifecycleState")
    def lifecycle_state(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "lifecycleState"))

    @builtins.property
    @jsii.member(jsii_name="ownerUserName")
    def owner_user_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "ownerUserName"))

    @builtins.property
    @jsii.member(jsii_name="runAs")
    def run_as(self) -> "DataDatabricksAlertsV2AlertsRunAsOutputReference":
        return typing.cast("DataDatabricksAlertsV2AlertsRunAsOutputReference", jsii.get(self, "runAs"))

    @builtins.property
    @jsii.member(jsii_name="schedule")
    def schedule(self) -> "DataDatabricksAlertsV2AlertsScheduleOutputReference":
        return typing.cast("DataDatabricksAlertsV2AlertsScheduleOutputReference", jsii.get(self, "schedule"))

    @builtins.property
    @jsii.member(jsii_name="updateTime")
    def update_time(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "updateTime"))

    @builtins.property
    @jsii.member(jsii_name="customDescriptionInput")
    def custom_description_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "customDescriptionInput"))

    @builtins.property
    @jsii.member(jsii_name="customSummaryInput")
    def custom_summary_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "customSummaryInput"))

    @builtins.property
    @jsii.member(jsii_name="displayNameInput")
    def display_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "displayNameInput"))

    @builtins.property
    @jsii.member(jsii_name="evaluationInput")
    def evaluation_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluation]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluation]], jsii.get(self, "evaluationInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="parentPathInput")
    def parent_path_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "parentPathInput"))

    @builtins.property
    @jsii.member(jsii_name="queryTextInput")
    def query_text_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "queryTextInput"))

    @builtins.property
    @jsii.member(jsii_name="runAsInput")
    def run_as_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsRunAs"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsRunAs"]], jsii.get(self, "runAsInput"))

    @builtins.property
    @jsii.member(jsii_name="runAsUserNameInput")
    def run_as_user_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "runAsUserNameInput"))

    @builtins.property
    @jsii.member(jsii_name="scheduleInput")
    def schedule_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsSchedule"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "DataDatabricksAlertsV2AlertsSchedule"]], jsii.get(self, "scheduleInput"))

    @builtins.property
    @jsii.member(jsii_name="warehouseIdInput")
    def warehouse_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "warehouseIdInput"))

    @builtins.property
    @jsii.member(jsii_name="customDescription")
    def custom_description(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "customDescription"))

    @custom_description.setter
    def custom_description(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__046249ce1c2197eb06fcdbef0626770f1940e0c54cd9a1123d2d99e507210b8c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "customDescription", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="customSummary")
    def custom_summary(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "customSummary"))

    @custom_summary.setter
    def custom_summary(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a1947b82bf9715c2358c1f10b4dd1819007f8e4c43effeca6b70003d1b7677f3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "customSummary", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="displayName")
    def display_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "displayName"))

    @display_name.setter
    def display_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5237f82be9cdec63e4ae84c233673fcd88f0a677aa46e1f1ea469d83bbbb52fe)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "displayName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8f2243c452a203a7e50f89e95ebd965f5c0b1950bfb3392da78b51d258108d37)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="parentPath")
    def parent_path(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "parentPath"))

    @parent_path.setter
    def parent_path(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b04006b00a21bca6997d00b23ac99b2e26d4ca067da0f9a6a54d18ea7218ae01)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "parentPath", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="queryText")
    def query_text(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "queryText"))

    @query_text.setter
    def query_text(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__90e963513c56de6ce8a585c063c77dbbf2ff1afecfb5a28b6519ce0a01328b59)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "queryText", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="runAsUserName")
    def run_as_user_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "runAsUserName"))

    @run_as_user_name.setter
    def run_as_user_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__877e9c59e92e9602f1d02ab9ad3d892ac748842ebb1b51c3faa2800b74cedf6b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "runAsUserName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="warehouseId")
    def warehouse_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "warehouseId"))

    @warehouse_id.setter
    def warehouse_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__77db895a72473f0b6fda5f04ece3750b75013737c10e7b700b1e38356467ced8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "warehouseId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[DataDatabricksAlertsV2Alerts]:
        return typing.cast(typing.Optional[DataDatabricksAlertsV2Alerts], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[DataDatabricksAlertsV2Alerts],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__28cdac34a0769cea2fa6075f22407f962f4c74037abb1e0f4a10453cfe57a6bb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsRunAs",
    jsii_struct_bases=[],
    name_mapping={
        "service_principal_name": "servicePrincipalName",
        "user_name": "userName",
    },
)
class DataDatabricksAlertsV2AlertsRunAs:
    def __init__(
        self,
        *,
        service_principal_name: typing.Optional[builtins.str] = None,
        user_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param service_principal_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#service_principal_name DataDatabricksAlertsV2#service_principal_name}.
        :param user_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#user_name DataDatabricksAlertsV2#user_name}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f1cdde59848731f660f8ba234d779b346301870340a0006d4004e4e4d9eccfb2)
            check_type(argname="argument service_principal_name", value=service_principal_name, expected_type=type_hints["service_principal_name"])
            check_type(argname="argument user_name", value=user_name, expected_type=type_hints["user_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if service_principal_name is not None:
            self._values["service_principal_name"] = service_principal_name
        if user_name is not None:
            self._values["user_name"] = user_name

    @builtins.property
    def service_principal_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#service_principal_name DataDatabricksAlertsV2#service_principal_name}.'''
        result = self._values.get("service_principal_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def user_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#user_name DataDatabricksAlertsV2#user_name}.'''
        result = self._values.get("user_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsRunAs(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksAlertsV2AlertsRunAsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsRunAsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__2cd4e6a95f77d7e32ff87bd768bed80108180c161686f80070e767e47fb0c4d2)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetServicePrincipalName")
    def reset_service_principal_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetServicePrincipalName", []))

    @jsii.member(jsii_name="resetUserName")
    def reset_user_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUserName", []))

    @builtins.property
    @jsii.member(jsii_name="servicePrincipalNameInput")
    def service_principal_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "servicePrincipalNameInput"))

    @builtins.property
    @jsii.member(jsii_name="userNameInput")
    def user_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "userNameInput"))

    @builtins.property
    @jsii.member(jsii_name="servicePrincipalName")
    def service_principal_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "servicePrincipalName"))

    @service_principal_name.setter
    def service_principal_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3a0c162a78fb6665c237371420001da95dcc0e177a0d7f2d357c56d1157c8c43)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "servicePrincipalName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="userName")
    def user_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "userName"))

    @user_name.setter
    def user_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b82a6ed680a71617d700fe0cfeea4a5225878827a71e52b186242c1f797bf823)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "userName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsRunAs]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsRunAs]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsRunAs]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e6e896b8c07aff92f52289d6666bf2cb64a8708bb263d35f771ae6f99d1abc48)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsSchedule",
    jsii_struct_bases=[],
    name_mapping={
        "pause_status": "pauseStatus",
        "quartz_cron_schedule": "quartzCronSchedule",
        "timezone_id": "timezoneId",
    },
)
class DataDatabricksAlertsV2AlertsSchedule:
    def __init__(
        self,
        *,
        pause_status: typing.Optional[builtins.str] = None,
        quartz_cron_schedule: typing.Optional[builtins.str] = None,
        timezone_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param pause_status: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#pause_status DataDatabricksAlertsV2#pause_status}.
        :param quartz_cron_schedule: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#quartz_cron_schedule DataDatabricksAlertsV2#quartz_cron_schedule}.
        :param timezone_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#timezone_id DataDatabricksAlertsV2#timezone_id}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d61dc0bbd6b89cc1e685bcbbcba37f2bfa8a646c0741636da94c295181bcd072)
            check_type(argname="argument pause_status", value=pause_status, expected_type=type_hints["pause_status"])
            check_type(argname="argument quartz_cron_schedule", value=quartz_cron_schedule, expected_type=type_hints["quartz_cron_schedule"])
            check_type(argname="argument timezone_id", value=timezone_id, expected_type=type_hints["timezone_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if pause_status is not None:
            self._values["pause_status"] = pause_status
        if quartz_cron_schedule is not None:
            self._values["quartz_cron_schedule"] = quartz_cron_schedule
        if timezone_id is not None:
            self._values["timezone_id"] = timezone_id

    @builtins.property
    def pause_status(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#pause_status DataDatabricksAlertsV2#pause_status}.'''
        result = self._values.get("pause_status")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def quartz_cron_schedule(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#quartz_cron_schedule DataDatabricksAlertsV2#quartz_cron_schedule}.'''
        result = self._values.get("quartz_cron_schedule")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def timezone_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/data-sources/alerts_v2#timezone_id DataDatabricksAlertsV2#timezone_id}.'''
        result = self._values.get("timezone_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataDatabricksAlertsV2AlertsSchedule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataDatabricksAlertsV2AlertsScheduleOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2AlertsScheduleOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__5f1813837835bd0003227083b9f7beacf3063886829b8091ff64f8b1e5211ae3)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetPauseStatus")
    def reset_pause_status(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPauseStatus", []))

    @jsii.member(jsii_name="resetQuartzCronSchedule")
    def reset_quartz_cron_schedule(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetQuartzCronSchedule", []))

    @jsii.member(jsii_name="resetTimezoneId")
    def reset_timezone_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimezoneId", []))

    @builtins.property
    @jsii.member(jsii_name="pauseStatusInput")
    def pause_status_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "pauseStatusInput"))

    @builtins.property
    @jsii.member(jsii_name="quartzCronScheduleInput")
    def quartz_cron_schedule_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "quartzCronScheduleInput"))

    @builtins.property
    @jsii.member(jsii_name="timezoneIdInput")
    def timezone_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "timezoneIdInput"))

    @builtins.property
    @jsii.member(jsii_name="pauseStatus")
    def pause_status(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "pauseStatus"))

    @pause_status.setter
    def pause_status(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__744de6bd3571046dd13b70c33aa49b402145803302625d35257f54978c1f8815)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "pauseStatus", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="quartzCronSchedule")
    def quartz_cron_schedule(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "quartzCronSchedule"))

    @quartz_cron_schedule.setter
    def quartz_cron_schedule(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9fe17c9a47b46e47a2483f1b8b52c487b1f42babba04a61a58549e71a5df2e6d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "quartzCronSchedule", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="timezoneId")
    def timezone_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "timezoneId"))

    @timezone_id.setter
    def timezone_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__99851a7c481ff7ecadf15dcbdb12f227c9e7f2ed962d89142fc47c03d3de2c63)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "timezoneId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsSchedule]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsSchedule]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsSchedule]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9b70020ee559d78c6c7a0b4c765f7df8ff57acbb0c2c0f8c96e79da8f9771df7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.dataDatabricksAlertsV2.DataDatabricksAlertsV2Config",
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
class DataDatabricksAlertsV2Config(_cdktf_9a9027ec.TerraformMetaArguments):
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
            type_hints = typing.get_type_hints(_typecheckingstub__261e2ad0ea21e1b8b5e930d39fb31cdca9cdb69380384f3c9236b419f86ceb7b)
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
        return "DataDatabricksAlertsV2Config(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "DataDatabricksAlertsV2",
    "DataDatabricksAlertsV2Alerts",
    "DataDatabricksAlertsV2AlertsEffectiveRunAs",
    "DataDatabricksAlertsV2AlertsEffectiveRunAsOutputReference",
    "DataDatabricksAlertsV2AlertsEvaluation",
    "DataDatabricksAlertsV2AlertsEvaluationNotification",
    "DataDatabricksAlertsV2AlertsEvaluationNotificationOutputReference",
    "DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions",
    "DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsList",
    "DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptionsOutputReference",
    "DataDatabricksAlertsV2AlertsEvaluationOutputReference",
    "DataDatabricksAlertsV2AlertsEvaluationSource",
    "DataDatabricksAlertsV2AlertsEvaluationSourceOutputReference",
    "DataDatabricksAlertsV2AlertsEvaluationThreshold",
    "DataDatabricksAlertsV2AlertsEvaluationThresholdColumn",
    "DataDatabricksAlertsV2AlertsEvaluationThresholdColumnOutputReference",
    "DataDatabricksAlertsV2AlertsEvaluationThresholdOutputReference",
    "DataDatabricksAlertsV2AlertsEvaluationThresholdValue",
    "DataDatabricksAlertsV2AlertsEvaluationThresholdValueOutputReference",
    "DataDatabricksAlertsV2AlertsList",
    "DataDatabricksAlertsV2AlertsOutputReference",
    "DataDatabricksAlertsV2AlertsRunAs",
    "DataDatabricksAlertsV2AlertsRunAsOutputReference",
    "DataDatabricksAlertsV2AlertsSchedule",
    "DataDatabricksAlertsV2AlertsScheduleOutputReference",
    "DataDatabricksAlertsV2Config",
]

publication.publish()

def _typecheckingstub__7ca2e6aaba880dad183280c8634fa7ff8bafc5fa410023353064e47441de3ca3(
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

def _typecheckingstub__47439c8fc9a43b443fc6e8ee491c9c1e623a0c383ce734766dd63e3c246b5ea0(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c86d8eb83e6f1e1d326a76d616c17b4662a534d1c7420eb3778cd73dc9bdb303(
    *,
    id: builtins.str,
    custom_description: typing.Optional[builtins.str] = None,
    custom_summary: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    evaluation: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsEvaluation, typing.Dict[builtins.str, typing.Any]]] = None,
    parent_path: typing.Optional[builtins.str] = None,
    query_text: typing.Optional[builtins.str] = None,
    run_as: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsRunAs, typing.Dict[builtins.str, typing.Any]]] = None,
    run_as_user_name: typing.Optional[builtins.str] = None,
    schedule: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsSchedule, typing.Dict[builtins.str, typing.Any]]] = None,
    warehouse_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e47f7968a528cb84bec9d227b05324ccfaf6b76405af875f00e290457433fb4d(
    *,
    service_principal_name: typing.Optional[builtins.str] = None,
    user_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__529054c58e405b94cea579d6a7225415dbaa5d7fc84e2b3c2df99d3b23b6346d(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__36067428f3ed10cb90156f7a20a66f8150f13404711d4dbdff9fd44eb339636d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__12b31339c29955ae8688854a27c598f535b793b693171a59ac0b237f81eea8eb(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5e0cca8a561f5108f842ae6f051c268e6e61b6849dabd4d06626cbdae86933c0(
    value: typing.Optional[DataDatabricksAlertsV2AlertsEffectiveRunAs],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d1fc1495b9e85023cababc9c89d04134088d33b23e8aa1106c158a94b58e0640(
    *,
    comparison_operator: typing.Optional[builtins.str] = None,
    empty_result_state: typing.Optional[builtins.str] = None,
    notification: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsEvaluationNotification, typing.Dict[builtins.str, typing.Any]]] = None,
    source: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsEvaluationSource, typing.Dict[builtins.str, typing.Any]]] = None,
    threshold: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsEvaluationThreshold, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__24cba6c7edc93d2a67645f0e6d7fee3fcdf3815c22dacdecc6205aecc04cea3f(
    *,
    notify_on_ok: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    retrigger_seconds: typing.Optional[jsii.Number] = None,
    subscriptions: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__22401e0955c944d51954b0e0c55033a7639629b280243e6aa5b586f187615d92(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b5a20e6e37adde7f2e4e2042c8dcbd68b8caca5247c792aeee93e6333131faf3(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__927861417dbc2e9b5b503a24cfd982b7340e5790e223330ff59b3ca91a931a42(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__736dd48d4d2e3ed3fdd64bafc1365833bafbf42206fdad5faab4e08239e27768(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be530556c9c02ce57adb2b8bf53f2d75025da22028d64e57c10321ba5c0aeb1d(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotification]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3e9657043a13ac35f2e5188a6947fdae6b0d767cf9d3c89395c282d9154f8e56(
    *,
    destination_id: typing.Optional[builtins.str] = None,
    user_email: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4756d8712a2542267931c591b9f9a79c49725648a800f19be559da719317363e(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ebeeac31cde3041b7adf95dd81f5a1dbef4161f5f4e67afe97dfa40ccab506ce(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5ac9428d9c04c52ef4da2f31c17cf114dce6adc6dc4543185e8c9eb9585f7895(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6db8e57dfaadcf9196f9830aa8638cf2adeee54c2872bfef9f915bd84b87b7eb(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__138c212512ec198c91321309e619775f744984aefb9e1ed308483847c7851902(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aca2799c3f15c6e374d4f73e4e596f40b870644b76112cb12d4b416168706c05(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e9b3e6e21bea8d69cd943d2e19a18087ba492b93f004160d91a55a54a0f5ee09(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__075de387b50179ea4cbbcfb614ac8b57caf8e03003257178af61e2cc104a3f75(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f919ff2dc722407bf7595fe7ad11470bd498a71f40b9c91bcb81ae5b85306643(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e1a04412ad02aacdec25ca3902b99337e331e61d41bf9f8ebb7500a2647781d4(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationNotificationSubscriptions]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04abf6ef3fb63e5887a4ef558bdb6838507e1fcd2d3e35a0ca0526b0a29eb774(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f5235987cd8661b1e7d9ab8141038a39f80edd72827a32cddc0438c901f3d291(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a3fbc6a4f58f3308163e33d9884e01fc8d23700df269334db3f39ed4b0bb464e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__acf3101a143ad5d041815808c540b528fd7d9583d6f1389f9871f0db9e3aeeb9(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluation]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bcc813bb211ef8adfdafd1afaa6baa7128302b999bed0229cffeb098f6092650(
    *,
    aggregation: typing.Optional[builtins.str] = None,
    display: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6317a3ea38ca9cfbf6968608213e809f4a69fe5127369125b209da5e2901d03d(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dbe092f0f6fa7eb789052e4794703368429a5e90e2a32bb5448b3f0e65d2cf5c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__20b18c1b2a7a7878054a2e8e250d0c766d8e94460f0d4322820fdbc72ee6881e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6cc5e6a110b0953f7d767c5fbbaa89d4c2e6cca2be4a986255b080500583e381(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__704804355ff8a91544b07e0d4b4b8880e436ca998ade6275a6b21142bb1deba3(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationSource]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3e992e46fa0626f9880b9081659490071c72e4e575daeaa40e3fd2ca8c8224df(
    *,
    column: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsEvaluationThresholdColumn, typing.Dict[builtins.str, typing.Any]]] = None,
    value: typing.Optional[typing.Union[DataDatabricksAlertsV2AlertsEvaluationThresholdValue, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f048da9bbe75ad73530618487893c39f89e6c0414748f52f29395fe56128f9f4(
    *,
    aggregation: typing.Optional[builtins.str] = None,
    display: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__44ae4848c1adbb5e9439177d9a075e1a2ee2ef7561e08bda48eb06d09caafb8e(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__784183626e6818e6cf1316753b78577ae5539cb770d174df818b16c20aaaa0a4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3d3826652f7a6d2cfbb5d1ab1e64f91ba0b7d51d9b140ff377cd42851195e16c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cc22efc96d5de73dbfd5bf5cecf9c4ee9fb809adddc555479b202c921e6c469e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ed33e1377e13d12ed10e44ceb4b704acd6f87f55f53b5360dec445a3a60d4ad3(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdColumn]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__506505f61ff077a25b5d1914b74d053107af1777dd283a680a721cfe7fce01af(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4f981da2546e8eea3ef293ee948a2438f8b0814b413df82e5f73bffe86e76e4d(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThreshold]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7dd94682873add4f2aecba9435821c78e9eb48d37a3fbfb2ae8dd1be600818a7(
    *,
    bool_value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    double_value: typing.Optional[jsii.Number] = None,
    string_value: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__045463279ee4c143a1221170d04cd0178900e1b6b7185c1f51d8ad68ad77a361(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b39a091dfd3b16a3cf72bd87dfe6a075a5fc6c87edd20b3a456c4dcba54f0a32(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__08a1b276f4505c402d42dbca17f718a319b892111db92ef1a088757b994cf1bf(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c9a33c806bc779c766196eae93273283edcce226d05976da21da460762429615(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6b222ef0619ddd2694e9afda51672a94c506007c806feb48dca6545441d4c3cd(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsEvaluationThresholdValue]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__efc3a54277d0ad2c32b61188d93cc0fb4dfa580dd07f78cad911477ca4e4779c(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__53be1be344c63a2fcaf7574cb2c6e0ede420b0ce45b2b63d2af4670c34575a17(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__837b94a604227ed2bb3ff427bc7c00f4d01cce9fdba8318dfa24d1fd4dccc3cf(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2b94a1424f173c30f87050b6913731d06ca35bced76a8b2a88bf61bdfa50325a(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a7fefaa56ed806d7ce7fe51c31467caf90c2b2e57cafaf53b3493f7c1c0fc6d9(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a79b4d4c6681893bc95e6d15ece74e5a6247becffde9f0eb8910101eadfe7052(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[DataDatabricksAlertsV2Alerts]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0da437268a3bceff1db53d12bf7eaef2ba4fd300fa984213b8d33e8e8d4ea3d6(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__046249ce1c2197eb06fcdbef0626770f1940e0c54cd9a1123d2d99e507210b8c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a1947b82bf9715c2358c1f10b4dd1819007f8e4c43effeca6b70003d1b7677f3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5237f82be9cdec63e4ae84c233673fcd88f0a677aa46e1f1ea469d83bbbb52fe(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8f2243c452a203a7e50f89e95ebd965f5c0b1950bfb3392da78b51d258108d37(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b04006b00a21bca6997d00b23ac99b2e26d4ca067da0f9a6a54d18ea7218ae01(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__90e963513c56de6ce8a585c063c77dbbf2ff1afecfb5a28b6519ce0a01328b59(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__877e9c59e92e9602f1d02ab9ad3d892ac748842ebb1b51c3faa2800b74cedf6b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__77db895a72473f0b6fda5f04ece3750b75013737c10e7b700b1e38356467ced8(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__28cdac34a0769cea2fa6075f22407f962f4c74037abb1e0f4a10453cfe57a6bb(
    value: typing.Optional[DataDatabricksAlertsV2Alerts],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f1cdde59848731f660f8ba234d779b346301870340a0006d4004e4e4d9eccfb2(
    *,
    service_principal_name: typing.Optional[builtins.str] = None,
    user_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2cd4e6a95f77d7e32ff87bd768bed80108180c161686f80070e767e47fb0c4d2(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a0c162a78fb6665c237371420001da95dcc0e177a0d7f2d357c56d1157c8c43(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b82a6ed680a71617d700fe0cfeea4a5225878827a71e52b186242c1f797bf823(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e6e896b8c07aff92f52289d6666bf2cb64a8708bb263d35f771ae6f99d1abc48(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsRunAs]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d61dc0bbd6b89cc1e685bcbbcba37f2bfa8a646c0741636da94c295181bcd072(
    *,
    pause_status: typing.Optional[builtins.str] = None,
    quartz_cron_schedule: typing.Optional[builtins.str] = None,
    timezone_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5f1813837835bd0003227083b9f7beacf3063886829b8091ff64f8b1e5211ae3(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__744de6bd3571046dd13b70c33aa49b402145803302625d35257f54978c1f8815(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9fe17c9a47b46e47a2483f1b8b52c487b1f42babba04a61a58549e71a5df2e6d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__99851a7c481ff7ecadf15dcbdb12f227c9e7f2ed962d89142fc47c03d3de2c63(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9b70020ee559d78c6c7a0b4c765f7df8ff57acbb0c2c0f8c96e79da8f9771df7(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, DataDatabricksAlertsV2AlertsSchedule]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__261e2ad0ea21e1b8b5e930d39fb31cdca9cdb69380384f3c9236b419f86ceb7b(
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
