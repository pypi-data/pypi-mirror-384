r'''
# `databricks_registered_model`

Refer to the Terraform Registry for docs: [`databricks_registered_model`](https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model).
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


class RegisteredModel(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.registeredModel.RegisteredModel",
):
    '''Represents a {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model databricks_registered_model}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        aliases: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["RegisteredModelAliases", typing.Dict[builtins.str, typing.Any]]]]] = None,
        browse_only: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        catalog_name: typing.Optional[builtins.str] = None,
        comment: typing.Optional[builtins.str] = None,
        created_at: typing.Optional[jsii.Number] = None,
        created_by: typing.Optional[builtins.str] = None,
        full_name: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        metastore_id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        owner: typing.Optional[builtins.str] = None,
        schema_name: typing.Optional[builtins.str] = None,
        storage_location: typing.Optional[builtins.str] = None,
        updated_at: typing.Optional[jsii.Number] = None,
        updated_by: typing.Optional[builtins.str] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model databricks_registered_model} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param aliases: aliases block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#aliases RegisteredModel#aliases}
        :param browse_only: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#browse_only RegisteredModel#browse_only}.
        :param catalog_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#catalog_name RegisteredModel#catalog_name}.
        :param comment: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#comment RegisteredModel#comment}.
        :param created_at: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#created_at RegisteredModel#created_at}.
        :param created_by: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#created_by RegisteredModel#created_by}.
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#full_name RegisteredModel#full_name}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#id RegisteredModel#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param metastore_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#metastore_id RegisteredModel#metastore_id}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#name RegisteredModel#name}.
        :param owner: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#owner RegisteredModel#owner}.
        :param schema_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#schema_name RegisteredModel#schema_name}.
        :param storage_location: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#storage_location RegisteredModel#storage_location}.
        :param updated_at: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#updated_at RegisteredModel#updated_at}.
        :param updated_by: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#updated_by RegisteredModel#updated_by}.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3fbc768fd235f2ab8cca102508658e0e1a2ee139b7bbd634cdbcc594fe0f6da8)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = RegisteredModelConfig(
            aliases=aliases,
            browse_only=browse_only,
            catalog_name=catalog_name,
            comment=comment,
            created_at=created_at,
            created_by=created_by,
            full_name=full_name,
            id=id,
            metastore_id=metastore_id,
            name=name,
            owner=owner,
            schema_name=schema_name,
            storage_location=storage_location,
            updated_at=updated_at,
            updated_by=updated_by,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id_, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a RegisteredModel resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the RegisteredModel to import.
        :param import_from_id: The id of the existing RegisteredModel that should be imported. Refer to the {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the RegisteredModel to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__78b0d8598c95c96deb859161723769cae5a293f4c970bb2564486f4204deaea8)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putAliases")
    def put_aliases(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["RegisteredModelAliases", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__261074f9a5ec48f99ab7c59d3ce78e95b91555ac1a3df87d374b883a093d0cf0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putAliases", [value]))

    @jsii.member(jsii_name="resetAliases")
    def reset_aliases(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAliases", []))

    @jsii.member(jsii_name="resetBrowseOnly")
    def reset_browse_only(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBrowseOnly", []))

    @jsii.member(jsii_name="resetCatalogName")
    def reset_catalog_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCatalogName", []))

    @jsii.member(jsii_name="resetComment")
    def reset_comment(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetComment", []))

    @jsii.member(jsii_name="resetCreatedAt")
    def reset_created_at(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreatedAt", []))

    @jsii.member(jsii_name="resetCreatedBy")
    def reset_created_by(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreatedBy", []))

    @jsii.member(jsii_name="resetFullName")
    def reset_full_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetFullName", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetMetastoreId")
    def reset_metastore_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMetastoreId", []))

    @jsii.member(jsii_name="resetName")
    def reset_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetName", []))

    @jsii.member(jsii_name="resetOwner")
    def reset_owner(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOwner", []))

    @jsii.member(jsii_name="resetSchemaName")
    def reset_schema_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSchemaName", []))

    @jsii.member(jsii_name="resetStorageLocation")
    def reset_storage_location(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetStorageLocation", []))

    @jsii.member(jsii_name="resetUpdatedAt")
    def reset_updated_at(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdatedAt", []))

    @jsii.member(jsii_name="resetUpdatedBy")
    def reset_updated_by(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdatedBy", []))

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
    @jsii.member(jsii_name="aliases")
    def aliases(self) -> "RegisteredModelAliasesList":
        return typing.cast("RegisteredModelAliasesList", jsii.get(self, "aliases"))

    @builtins.property
    @jsii.member(jsii_name="aliasesInput")
    def aliases_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["RegisteredModelAliases"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["RegisteredModelAliases"]]], jsii.get(self, "aliasesInput"))

    @builtins.property
    @jsii.member(jsii_name="browseOnlyInput")
    def browse_only_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "browseOnlyInput"))

    @builtins.property
    @jsii.member(jsii_name="catalogNameInput")
    def catalog_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "catalogNameInput"))

    @builtins.property
    @jsii.member(jsii_name="commentInput")
    def comment_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "commentInput"))

    @builtins.property
    @jsii.member(jsii_name="createdAtInput")
    def created_at_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "createdAtInput"))

    @builtins.property
    @jsii.member(jsii_name="createdByInput")
    def created_by_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createdByInput"))

    @builtins.property
    @jsii.member(jsii_name="fullNameInput")
    def full_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "fullNameInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="metastoreIdInput")
    def metastore_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "metastoreIdInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="ownerInput")
    def owner_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "ownerInput"))

    @builtins.property
    @jsii.member(jsii_name="schemaNameInput")
    def schema_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "schemaNameInput"))

    @builtins.property
    @jsii.member(jsii_name="storageLocationInput")
    def storage_location_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "storageLocationInput"))

    @builtins.property
    @jsii.member(jsii_name="updatedAtInput")
    def updated_at_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "updatedAtInput"))

    @builtins.property
    @jsii.member(jsii_name="updatedByInput")
    def updated_by_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "updatedByInput"))

    @builtins.property
    @jsii.member(jsii_name="browseOnly")
    def browse_only(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "browseOnly"))

    @browse_only.setter
    def browse_only(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dde75a27abbee48ef0ea91761c5221f50c61689926a580b76d19368d321978b4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "browseOnly", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="catalogName")
    def catalog_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "catalogName"))

    @catalog_name.setter
    def catalog_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a3d3c9685669f3582ac9a423452f07855840477639454dcb671394695c3c7d43)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "catalogName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="comment")
    def comment(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "comment"))

    @comment.setter
    def comment(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__de78346f938d9719e0daffb5f5120266a87afba674cd1af986761c93ac2eb37b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "comment", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "createdAt"))

    @created_at.setter
    def created_at(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3c0cbd4107f6effe0294948dfdc7808234fba629768c0e49304dec30b23a62b4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "createdAt", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="createdBy")
    def created_by(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "createdBy"))

    @created_by.setter
    def created_by(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__643f814a74e70e51c4557d3081ea4edec02745c8f29e277e7464de598b7e42d3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "createdBy", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="fullName")
    def full_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "fullName"))

    @full_name.setter
    def full_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ffcc46880c801c07615e46546ac3cc91b40810988b2028ce09678af0060b114f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "fullName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8ed4f9c1d0f890965807d9253eed886b7a9f920f0cc180ab290138fa897341d2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="metastoreId")
    def metastore_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "metastoreId"))

    @metastore_id.setter
    def metastore_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0fde42627b0b9f88ef29d172806703c276dda862c58ae8f4d35f1892a5c080d3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "metastoreId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a65a70df625cb5c0207ca0b3bce190845366676d769662f439b65ede0c484b43)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="owner")
    def owner(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "owner"))

    @owner.setter
    def owner(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad1dd67c963ebcffd837b531f954c467b8e6339eac778f33b451746ada9112e1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "owner", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="schemaName")
    def schema_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "schemaName"))

    @schema_name.setter
    def schema_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fbb7fdceeefaf34049a350500c28bd13533c9a0bc5807086396139201e36a925)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "schemaName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="storageLocation")
    def storage_location(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "storageLocation"))

    @storage_location.setter
    def storage_location(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a21ad7296e45cfa9c3cdc87642d33d7518b6e90011ed253231f6332a2b73d745)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "storageLocation", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="updatedAt")
    def updated_at(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "updatedAt"))

    @updated_at.setter
    def updated_at(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6554d84e7a59c721c337855957a0244189eec6f10d60fff0f81883867730209a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "updatedAt", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="updatedBy")
    def updated_by(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "updatedBy"))

    @updated_by.setter
    def updated_by(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__017b0e55a31896fef93938f97f529bd724a12cc1b4b117fd7cf77d94f03272fe)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "updatedBy", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.registeredModel.RegisteredModelAliases",
    jsii_struct_bases=[],
    name_mapping={
        "alias_name": "aliasName",
        "catalog_name": "catalogName",
        "id": "id",
        "model_name": "modelName",
        "schema_name": "schemaName",
        "version_num": "versionNum",
    },
)
class RegisteredModelAliases:
    def __init__(
        self,
        *,
        alias_name: typing.Optional[builtins.str] = None,
        catalog_name: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        model_name: typing.Optional[builtins.str] = None,
        schema_name: typing.Optional[builtins.str] = None,
        version_num: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param alias_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#alias_name RegisteredModel#alias_name}.
        :param catalog_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#catalog_name RegisteredModel#catalog_name}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#id RegisteredModel#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param model_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#model_name RegisteredModel#model_name}.
        :param schema_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#schema_name RegisteredModel#schema_name}.
        :param version_num: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#version_num RegisteredModel#version_num}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5999acd3cd60deec99265088d1b7f52b50db19acc2be590b810da392fbed3ca7)
            check_type(argname="argument alias_name", value=alias_name, expected_type=type_hints["alias_name"])
            check_type(argname="argument catalog_name", value=catalog_name, expected_type=type_hints["catalog_name"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument model_name", value=model_name, expected_type=type_hints["model_name"])
            check_type(argname="argument schema_name", value=schema_name, expected_type=type_hints["schema_name"])
            check_type(argname="argument version_num", value=version_num, expected_type=type_hints["version_num"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if alias_name is not None:
            self._values["alias_name"] = alias_name
        if catalog_name is not None:
            self._values["catalog_name"] = catalog_name
        if id is not None:
            self._values["id"] = id
        if model_name is not None:
            self._values["model_name"] = model_name
        if schema_name is not None:
            self._values["schema_name"] = schema_name
        if version_num is not None:
            self._values["version_num"] = version_num

    @builtins.property
    def alias_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#alias_name RegisteredModel#alias_name}.'''
        result = self._values.get("alias_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def catalog_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#catalog_name RegisteredModel#catalog_name}.'''
        result = self._values.get("catalog_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#id RegisteredModel#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def model_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#model_name RegisteredModel#model_name}.'''
        result = self._values.get("model_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def schema_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#schema_name RegisteredModel#schema_name}.'''
        result = self._values.get("schema_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def version_num(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#version_num RegisteredModel#version_num}.'''
        result = self._values.get("version_num")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RegisteredModelAliases(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class RegisteredModelAliasesList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.registeredModel.RegisteredModelAliasesList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__fb4e94e8c11797c17bd9f6eeca0bc01d322aa22833f48bbc2ed3bd3ee650cc47)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(self, index: jsii.Number) -> "RegisteredModelAliasesOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dedda119482ff939e410fe93a9765a6ed41dbdb29c0e851efe87c93c2a315cac)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("RegisteredModelAliasesOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7ea07118e69b95ff49dd4b91e177da521c5fa9a00a63995a7cedae585f3de86d)
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
            type_hints = typing.get_type_hints(_typecheckingstub__3a29c7ea55033fe0c4a392f92ac5a3185f6569462d7da59b207145ec036ab5d0)
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
            type_hints = typing.get_type_hints(_typecheckingstub__b845869821cfe9d67d1305eebdb2453de78799499e1d472c5fb892387c68b08e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[RegisteredModelAliases]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[RegisteredModelAliases]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[RegisteredModelAliases]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__653db548cf515d28b9872a04d8b5a28132d25693f7e23ff945b9e48a03026e37)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class RegisteredModelAliasesOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-databricks.registeredModel.RegisteredModelAliasesOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__642d331538321b32efddf8d2f7f97a7c7b78aa31acda8c2f3a9b48d6559afb50)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetAliasName")
    def reset_alias_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAliasName", []))

    @jsii.member(jsii_name="resetCatalogName")
    def reset_catalog_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCatalogName", []))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetModelName")
    def reset_model_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetModelName", []))

    @jsii.member(jsii_name="resetSchemaName")
    def reset_schema_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSchemaName", []))

    @jsii.member(jsii_name="resetVersionNum")
    def reset_version_num(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetVersionNum", []))

    @builtins.property
    @jsii.member(jsii_name="aliasNameInput")
    def alias_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "aliasNameInput"))

    @builtins.property
    @jsii.member(jsii_name="catalogNameInput")
    def catalog_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "catalogNameInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="modelNameInput")
    def model_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "modelNameInput"))

    @builtins.property
    @jsii.member(jsii_name="schemaNameInput")
    def schema_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "schemaNameInput"))

    @builtins.property
    @jsii.member(jsii_name="versionNumInput")
    def version_num_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "versionNumInput"))

    @builtins.property
    @jsii.member(jsii_name="aliasName")
    def alias_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "aliasName"))

    @alias_name.setter
    def alias_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__522c8b3d93adb49ba4167adfaa10c4f7df08cc683e11e1582d3fce7bde4e1445)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "aliasName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="catalogName")
    def catalog_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "catalogName"))

    @catalog_name.setter
    def catalog_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f5a03aafe1722930ab1b324afd7e7d2d91ae1e38a4e5716f5b46a2ed04861e96)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "catalogName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13147a92ca4bbeebe3fe01b7dea7a5a84a842552bae4febc6123a9de3ae81203)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="modelName")
    def model_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "modelName"))

    @model_name.setter
    def model_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__945f89c19e01065730fcf7876982c001395a90906ee716c45ba22e3c8a082420)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "modelName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="schemaName")
    def schema_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "schemaName"))

    @schema_name.setter
    def schema_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4b6543efbede2f67727341d276f0a5ad182aa9f1981d20bbd03e50769297ca6a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "schemaName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="versionNum")
    def version_num(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "versionNum"))

    @version_num.setter
    def version_num(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__495f422a0004c2ca907322b9680a4dec89cd99c57604b1242661184003a2e98a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "versionNum", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, RegisteredModelAliases]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, RegisteredModelAliases]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, RegisteredModelAliases]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__53c9cdeb4bcaf8230d3af84ad29b8f4821c06882ee5b322d07f21bed8abbe888)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-databricks.registeredModel.RegisteredModelConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "aliases": "aliases",
        "browse_only": "browseOnly",
        "catalog_name": "catalogName",
        "comment": "comment",
        "created_at": "createdAt",
        "created_by": "createdBy",
        "full_name": "fullName",
        "id": "id",
        "metastore_id": "metastoreId",
        "name": "name",
        "owner": "owner",
        "schema_name": "schemaName",
        "storage_location": "storageLocation",
        "updated_at": "updatedAt",
        "updated_by": "updatedBy",
    },
)
class RegisteredModelConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        aliases: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[RegisteredModelAliases, typing.Dict[builtins.str, typing.Any]]]]] = None,
        browse_only: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        catalog_name: typing.Optional[builtins.str] = None,
        comment: typing.Optional[builtins.str] = None,
        created_at: typing.Optional[jsii.Number] = None,
        created_by: typing.Optional[builtins.str] = None,
        full_name: typing.Optional[builtins.str] = None,
        id: typing.Optional[builtins.str] = None,
        metastore_id: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        owner: typing.Optional[builtins.str] = None,
        schema_name: typing.Optional[builtins.str] = None,
        storage_location: typing.Optional[builtins.str] = None,
        updated_at: typing.Optional[jsii.Number] = None,
        updated_by: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param aliases: aliases block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#aliases RegisteredModel#aliases}
        :param browse_only: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#browse_only RegisteredModel#browse_only}.
        :param catalog_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#catalog_name RegisteredModel#catalog_name}.
        :param comment: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#comment RegisteredModel#comment}.
        :param created_at: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#created_at RegisteredModel#created_at}.
        :param created_by: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#created_by RegisteredModel#created_by}.
        :param full_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#full_name RegisteredModel#full_name}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#id RegisteredModel#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param metastore_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#metastore_id RegisteredModel#metastore_id}.
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#name RegisteredModel#name}.
        :param owner: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#owner RegisteredModel#owner}.
        :param schema_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#schema_name RegisteredModel#schema_name}.
        :param storage_location: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#storage_location RegisteredModel#storage_location}.
        :param updated_at: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#updated_at RegisteredModel#updated_at}.
        :param updated_by: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#updated_by RegisteredModel#updated_by}.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__920d6cbbade02c95f76fb476f5ec11ff1e8364a8fc6a9a980cb4ba33172990a2)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument aliases", value=aliases, expected_type=type_hints["aliases"])
            check_type(argname="argument browse_only", value=browse_only, expected_type=type_hints["browse_only"])
            check_type(argname="argument catalog_name", value=catalog_name, expected_type=type_hints["catalog_name"])
            check_type(argname="argument comment", value=comment, expected_type=type_hints["comment"])
            check_type(argname="argument created_at", value=created_at, expected_type=type_hints["created_at"])
            check_type(argname="argument created_by", value=created_by, expected_type=type_hints["created_by"])
            check_type(argname="argument full_name", value=full_name, expected_type=type_hints["full_name"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument metastore_id", value=metastore_id, expected_type=type_hints["metastore_id"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument owner", value=owner, expected_type=type_hints["owner"])
            check_type(argname="argument schema_name", value=schema_name, expected_type=type_hints["schema_name"])
            check_type(argname="argument storage_location", value=storage_location, expected_type=type_hints["storage_location"])
            check_type(argname="argument updated_at", value=updated_at, expected_type=type_hints["updated_at"])
            check_type(argname="argument updated_by", value=updated_by, expected_type=type_hints["updated_by"])
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
        if aliases is not None:
            self._values["aliases"] = aliases
        if browse_only is not None:
            self._values["browse_only"] = browse_only
        if catalog_name is not None:
            self._values["catalog_name"] = catalog_name
        if comment is not None:
            self._values["comment"] = comment
        if created_at is not None:
            self._values["created_at"] = created_at
        if created_by is not None:
            self._values["created_by"] = created_by
        if full_name is not None:
            self._values["full_name"] = full_name
        if id is not None:
            self._values["id"] = id
        if metastore_id is not None:
            self._values["metastore_id"] = metastore_id
        if name is not None:
            self._values["name"] = name
        if owner is not None:
            self._values["owner"] = owner
        if schema_name is not None:
            self._values["schema_name"] = schema_name
        if storage_location is not None:
            self._values["storage_location"] = storage_location
        if updated_at is not None:
            self._values["updated_at"] = updated_at
        if updated_by is not None:
            self._values["updated_by"] = updated_by

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
    def aliases(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[RegisteredModelAliases]]]:
        '''aliases block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#aliases RegisteredModel#aliases}
        '''
        result = self._values.get("aliases")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[RegisteredModelAliases]]], result)

    @builtins.property
    def browse_only(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#browse_only RegisteredModel#browse_only}.'''
        result = self._values.get("browse_only")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def catalog_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#catalog_name RegisteredModel#catalog_name}.'''
        result = self._values.get("catalog_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def comment(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#comment RegisteredModel#comment}.'''
        result = self._values.get("comment")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def created_at(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#created_at RegisteredModel#created_at}.'''
        result = self._values.get("created_at")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def created_by(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#created_by RegisteredModel#created_by}.'''
        result = self._values.get("created_by")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def full_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#full_name RegisteredModel#full_name}.'''
        result = self._values.get("full_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#id RegisteredModel#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def metastore_id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#metastore_id RegisteredModel#metastore_id}.'''
        result = self._values.get("metastore_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#name RegisteredModel#name}.'''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def owner(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#owner RegisteredModel#owner}.'''
        result = self._values.get("owner")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def schema_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#schema_name RegisteredModel#schema_name}.'''
        result = self._values.get("schema_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def storage_location(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#storage_location RegisteredModel#storage_location}.'''
        result = self._values.get("storage_location")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def updated_at(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#updated_at RegisteredModel#updated_at}.'''
        result = self._values.get("updated_at")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def updated_by(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/databricks/databricks/1.93.0/docs/resources/registered_model#updated_by RegisteredModel#updated_by}.'''
        result = self._values.get("updated_by")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RegisteredModelConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "RegisteredModel",
    "RegisteredModelAliases",
    "RegisteredModelAliasesList",
    "RegisteredModelAliasesOutputReference",
    "RegisteredModelConfig",
]

publication.publish()

def _typecheckingstub__3fbc768fd235f2ab8cca102508658e0e1a2ee139b7bbd634cdbcc594fe0f6da8(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    aliases: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[RegisteredModelAliases, typing.Dict[builtins.str, typing.Any]]]]] = None,
    browse_only: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    catalog_name: typing.Optional[builtins.str] = None,
    comment: typing.Optional[builtins.str] = None,
    created_at: typing.Optional[jsii.Number] = None,
    created_by: typing.Optional[builtins.str] = None,
    full_name: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    metastore_id: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
    owner: typing.Optional[builtins.str] = None,
    schema_name: typing.Optional[builtins.str] = None,
    storage_location: typing.Optional[builtins.str] = None,
    updated_at: typing.Optional[jsii.Number] = None,
    updated_by: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__78b0d8598c95c96deb859161723769cae5a293f4c970bb2564486f4204deaea8(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__261074f9a5ec48f99ab7c59d3ce78e95b91555ac1a3df87d374b883a093d0cf0(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[RegisteredModelAliases, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dde75a27abbee48ef0ea91761c5221f50c61689926a580b76d19368d321978b4(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a3d3c9685669f3582ac9a423452f07855840477639454dcb671394695c3c7d43(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__de78346f938d9719e0daffb5f5120266a87afba674cd1af986761c93ac2eb37b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3c0cbd4107f6effe0294948dfdc7808234fba629768c0e49304dec30b23a62b4(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__643f814a74e70e51c4557d3081ea4edec02745c8f29e277e7464de598b7e42d3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ffcc46880c801c07615e46546ac3cc91b40810988b2028ce09678af0060b114f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8ed4f9c1d0f890965807d9253eed886b7a9f920f0cc180ab290138fa897341d2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0fde42627b0b9f88ef29d172806703c276dda862c58ae8f4d35f1892a5c080d3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a65a70df625cb5c0207ca0b3bce190845366676d769662f439b65ede0c484b43(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad1dd67c963ebcffd837b531f954c467b8e6339eac778f33b451746ada9112e1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fbb7fdceeefaf34049a350500c28bd13533c9a0bc5807086396139201e36a925(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a21ad7296e45cfa9c3cdc87642d33d7518b6e90011ed253231f6332a2b73d745(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6554d84e7a59c721c337855957a0244189eec6f10d60fff0f81883867730209a(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__017b0e55a31896fef93938f97f529bd724a12cc1b4b117fd7cf77d94f03272fe(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5999acd3cd60deec99265088d1b7f52b50db19acc2be590b810da392fbed3ca7(
    *,
    alias_name: typing.Optional[builtins.str] = None,
    catalog_name: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    model_name: typing.Optional[builtins.str] = None,
    schema_name: typing.Optional[builtins.str] = None,
    version_num: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fb4e94e8c11797c17bd9f6eeca0bc01d322aa22833f48bbc2ed3bd3ee650cc47(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dedda119482ff939e410fe93a9765a6ed41dbdb29c0e851efe87c93c2a315cac(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7ea07118e69b95ff49dd4b91e177da521c5fa9a00a63995a7cedae585f3de86d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a29c7ea55033fe0c4a392f92ac5a3185f6569462d7da59b207145ec036ab5d0(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b845869821cfe9d67d1305eebdb2453de78799499e1d472c5fb892387c68b08e(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__653db548cf515d28b9872a04d8b5a28132d25693f7e23ff945b9e48a03026e37(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[RegisteredModelAliases]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__642d331538321b32efddf8d2f7f97a7c7b78aa31acda8c2f3a9b48d6559afb50(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__522c8b3d93adb49ba4167adfaa10c4f7df08cc683e11e1582d3fce7bde4e1445(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f5a03aafe1722930ab1b324afd7e7d2d91ae1e38a4e5716f5b46a2ed04861e96(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13147a92ca4bbeebe3fe01b7dea7a5a84a842552bae4febc6123a9de3ae81203(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__945f89c19e01065730fcf7876982c001395a90906ee716c45ba22e3c8a082420(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4b6543efbede2f67727341d276f0a5ad182aa9f1981d20bbd03e50769297ca6a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__495f422a0004c2ca907322b9680a4dec89cd99c57604b1242661184003a2e98a(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__53c9cdeb4bcaf8230d3af84ad29b8f4821c06882ee5b322d07f21bed8abbe888(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, RegisteredModelAliases]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__920d6cbbade02c95f76fb476f5ec11ff1e8364a8fc6a9a980cb4ba33172990a2(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    aliases: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[RegisteredModelAliases, typing.Dict[builtins.str, typing.Any]]]]] = None,
    browse_only: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    catalog_name: typing.Optional[builtins.str] = None,
    comment: typing.Optional[builtins.str] = None,
    created_at: typing.Optional[jsii.Number] = None,
    created_by: typing.Optional[builtins.str] = None,
    full_name: typing.Optional[builtins.str] = None,
    id: typing.Optional[builtins.str] = None,
    metastore_id: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
    owner: typing.Optional[builtins.str] = None,
    schema_name: typing.Optional[builtins.str] = None,
    storage_location: typing.Optional[builtins.str] = None,
    updated_at: typing.Optional[jsii.Number] = None,
    updated_by: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
