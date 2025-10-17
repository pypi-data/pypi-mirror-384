r'''
# `opentelekomcloud_taurusdb_mysql_proxy_v3`

Refer to the Terraform Registry for docs: [`opentelekomcloud_taurusdb_mysql_proxy_v3`](https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3).
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


class TaurusdbMysqlProxyV3(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3",
):
    '''Represents a {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3 opentelekomcloud_taurusdb_mysql_proxy_v3}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        flavor: builtins.str,
        instance_id: builtins.str,
        node_num: jsii.Number,
        id: typing.Optional[builtins.str] = None,
        master_node_weight: typing.Optional[typing.Union["TaurusdbMysqlProxyV3MasterNodeWeight", typing.Dict[builtins.str, typing.Any]]] = None,
        proxy_mode: typing.Optional[builtins.str] = None,
        proxy_name: typing.Optional[builtins.str] = None,
        readonly_nodes_weight: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["TaurusdbMysqlProxyV3ReadonlyNodesWeight", typing.Dict[builtins.str, typing.Any]]]]] = None,
        timeouts: typing.Optional[typing.Union["TaurusdbMysqlProxyV3Timeouts", typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3 opentelekomcloud_taurusdb_mysql_proxy_v3} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param flavor: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#flavor TaurusdbMysqlProxyV3#flavor}.
        :param instance_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#instance_id TaurusdbMysqlProxyV3#instance_id}.
        :param node_num: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#node_num TaurusdbMysqlProxyV3#node_num}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#id TaurusdbMysqlProxyV3#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param master_node_weight: master_node_weight block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#master_node_weight TaurusdbMysqlProxyV3#master_node_weight}
        :param proxy_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#proxy_mode TaurusdbMysqlProxyV3#proxy_mode}.
        :param proxy_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#proxy_name TaurusdbMysqlProxyV3#proxy_name}.
        :param readonly_nodes_weight: readonly_nodes_weight block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#readonly_nodes_weight TaurusdbMysqlProxyV3#readonly_nodes_weight}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#timeouts TaurusdbMysqlProxyV3#timeouts}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__47ae0b382b22d87a11cc4c879aa52daf263110c9a5229a869ce97a0a9d2d2f2a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = TaurusdbMysqlProxyV3Config(
            flavor=flavor,
            instance_id=instance_id,
            node_num=node_num,
            id=id,
            master_node_weight=master_node_weight,
            proxy_mode=proxy_mode,
            proxy_name=proxy_name,
            readonly_nodes_weight=readonly_nodes_weight,
            timeouts=timeouts,
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
        '''Generates CDKTF code for importing a TaurusdbMysqlProxyV3 resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the TaurusdbMysqlProxyV3 to import.
        :param import_from_id: The id of the existing TaurusdbMysqlProxyV3 that should be imported. Refer to the {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the TaurusdbMysqlProxyV3 to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3b9544cdd191009a727da0f458c8e15711093d87d479a902a9d7be04af1e8e10)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putMasterNodeWeight")
    def put_master_node_weight(self, *, id: builtins.str, weight: jsii.Number) -> None:
        '''
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#id TaurusdbMysqlProxyV3#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param weight: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#weight TaurusdbMysqlProxyV3#weight}.
        '''
        value = TaurusdbMysqlProxyV3MasterNodeWeight(id=id, weight=weight)

        return typing.cast(None, jsii.invoke(self, "putMasterNodeWeight", [value]))

    @jsii.member(jsii_name="putReadonlyNodesWeight")
    def put_readonly_nodes_weight(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["TaurusdbMysqlProxyV3ReadonlyNodesWeight", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__12db498382d9aa8662c1dc16719162b9ae53c56a72eea7af56f13b03438015e7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putReadonlyNodesWeight", [value]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#create TaurusdbMysqlProxyV3#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#delete TaurusdbMysqlProxyV3#delete}.
        :param update: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#update TaurusdbMysqlProxyV3#update}.
        '''
        value = TaurusdbMysqlProxyV3Timeouts(
            create=create, delete=delete, update=update
        )

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetMasterNodeWeight")
    def reset_master_node_weight(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMasterNodeWeight", []))

    @jsii.member(jsii_name="resetProxyMode")
    def reset_proxy_mode(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetProxyMode", []))

    @jsii.member(jsii_name="resetProxyName")
    def reset_proxy_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetProxyName", []))

    @jsii.member(jsii_name="resetReadonlyNodesWeight")
    def reset_readonly_nodes_weight(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReadonlyNodesWeight", []))

    @jsii.member(jsii_name="resetTimeouts")
    def reset_timeouts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeouts", []))

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
    @jsii.member(jsii_name="address")
    def address(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "address"))

    @builtins.property
    @jsii.member(jsii_name="masterNodeWeight")
    def master_node_weight(
        self,
    ) -> "TaurusdbMysqlProxyV3MasterNodeWeightOutputReference":
        return typing.cast("TaurusdbMysqlProxyV3MasterNodeWeightOutputReference", jsii.get(self, "masterNodeWeight"))

    @builtins.property
    @jsii.member(jsii_name="nodes")
    def nodes(self) -> "TaurusdbMysqlProxyV3NodesList":
        return typing.cast("TaurusdbMysqlProxyV3NodesList", jsii.get(self, "nodes"))

    @builtins.property
    @jsii.member(jsii_name="port")
    def port(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "port"))

    @builtins.property
    @jsii.member(jsii_name="readonlyNodesWeight")
    def readonly_nodes_weight(self) -> "TaurusdbMysqlProxyV3ReadonlyNodesWeightList":
        return typing.cast("TaurusdbMysqlProxyV3ReadonlyNodesWeightList", jsii.get(self, "readonlyNodesWeight"))

    @builtins.property
    @jsii.member(jsii_name="region")
    def region(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "region"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> "TaurusdbMysqlProxyV3TimeoutsOutputReference":
        return typing.cast("TaurusdbMysqlProxyV3TimeoutsOutputReference", jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="flavorInput")
    def flavor_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "flavorInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="instanceIdInput")
    def instance_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "instanceIdInput"))

    @builtins.property
    @jsii.member(jsii_name="masterNodeWeightInput")
    def master_node_weight_input(
        self,
    ) -> typing.Optional["TaurusdbMysqlProxyV3MasterNodeWeight"]:
        return typing.cast(typing.Optional["TaurusdbMysqlProxyV3MasterNodeWeight"], jsii.get(self, "masterNodeWeightInput"))

    @builtins.property
    @jsii.member(jsii_name="nodeNumInput")
    def node_num_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "nodeNumInput"))

    @builtins.property
    @jsii.member(jsii_name="proxyModeInput")
    def proxy_mode_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "proxyModeInput"))

    @builtins.property
    @jsii.member(jsii_name="proxyNameInput")
    def proxy_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "proxyNameInput"))

    @builtins.property
    @jsii.member(jsii_name="readonlyNodesWeightInput")
    def readonly_nodes_weight_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["TaurusdbMysqlProxyV3ReadonlyNodesWeight"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["TaurusdbMysqlProxyV3ReadonlyNodesWeight"]]], jsii.get(self, "readonlyNodesWeightInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "TaurusdbMysqlProxyV3Timeouts"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "TaurusdbMysqlProxyV3Timeouts"]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="flavor")
    def flavor(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "flavor"))

    @flavor.setter
    def flavor(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__31b2ab0112fffc0f60c34490378d5498fcfa627b2935943d27f239134b3de4bb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "flavor", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5c4aa8a752854098ea8be42ebdab1b2a15386a250de592612b419cba8edcf9ec)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="instanceId")
    def instance_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "instanceId"))

    @instance_id.setter
    def instance_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__62e541adddfa5d21dd9fa2559553b9c41a389e11f1d8d2515ce0d33f4d26a056)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "instanceId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="nodeNum")
    def node_num(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "nodeNum"))

    @node_num.setter
    def node_num(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3fbc949c47991ac4cf44ea825c7ae712d596c0f7d82c522a6c59b87cf63f6d2d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "nodeNum", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="proxyMode")
    def proxy_mode(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "proxyMode"))

    @proxy_mode.setter
    def proxy_mode(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0dd2c502c45c2642b75553230f7dc9375d18cf55b9c0a487d90b7bc20cc08b4d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "proxyMode", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="proxyName")
    def proxy_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "proxyName"))

    @proxy_name.setter
    def proxy_name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__29ee28040ac24657902548913a15ef3d3218725509fc51ad0f318cbe3c0d787a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "proxyName", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3Config",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "flavor": "flavor",
        "instance_id": "instanceId",
        "node_num": "nodeNum",
        "id": "id",
        "master_node_weight": "masterNodeWeight",
        "proxy_mode": "proxyMode",
        "proxy_name": "proxyName",
        "readonly_nodes_weight": "readonlyNodesWeight",
        "timeouts": "timeouts",
    },
)
class TaurusdbMysqlProxyV3Config(_cdktf_9a9027ec.TerraformMetaArguments):
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
        flavor: builtins.str,
        instance_id: builtins.str,
        node_num: jsii.Number,
        id: typing.Optional[builtins.str] = None,
        master_node_weight: typing.Optional[typing.Union["TaurusdbMysqlProxyV3MasterNodeWeight", typing.Dict[builtins.str, typing.Any]]] = None,
        proxy_mode: typing.Optional[builtins.str] = None,
        proxy_name: typing.Optional[builtins.str] = None,
        readonly_nodes_weight: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["TaurusdbMysqlProxyV3ReadonlyNodesWeight", typing.Dict[builtins.str, typing.Any]]]]] = None,
        timeouts: typing.Optional[typing.Union["TaurusdbMysqlProxyV3Timeouts", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param flavor: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#flavor TaurusdbMysqlProxyV3#flavor}.
        :param instance_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#instance_id TaurusdbMysqlProxyV3#instance_id}.
        :param node_num: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#node_num TaurusdbMysqlProxyV3#node_num}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#id TaurusdbMysqlProxyV3#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param master_node_weight: master_node_weight block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#master_node_weight TaurusdbMysqlProxyV3#master_node_weight}
        :param proxy_mode: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#proxy_mode TaurusdbMysqlProxyV3#proxy_mode}.
        :param proxy_name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#proxy_name TaurusdbMysqlProxyV3#proxy_name}.
        :param readonly_nodes_weight: readonly_nodes_weight block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#readonly_nodes_weight TaurusdbMysqlProxyV3#readonly_nodes_weight}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#timeouts TaurusdbMysqlProxyV3#timeouts}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(master_node_weight, dict):
            master_node_weight = TaurusdbMysqlProxyV3MasterNodeWeight(**master_node_weight)
        if isinstance(timeouts, dict):
            timeouts = TaurusdbMysqlProxyV3Timeouts(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9afe07297896f0c30de494d369b2b8c86d3923f88ea82b11d5732dbd33aa6963)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument flavor", value=flavor, expected_type=type_hints["flavor"])
            check_type(argname="argument instance_id", value=instance_id, expected_type=type_hints["instance_id"])
            check_type(argname="argument node_num", value=node_num, expected_type=type_hints["node_num"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument master_node_weight", value=master_node_weight, expected_type=type_hints["master_node_weight"])
            check_type(argname="argument proxy_mode", value=proxy_mode, expected_type=type_hints["proxy_mode"])
            check_type(argname="argument proxy_name", value=proxy_name, expected_type=type_hints["proxy_name"])
            check_type(argname="argument readonly_nodes_weight", value=readonly_nodes_weight, expected_type=type_hints["readonly_nodes_weight"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "flavor": flavor,
            "instance_id": instance_id,
            "node_num": node_num,
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
        if id is not None:
            self._values["id"] = id
        if master_node_weight is not None:
            self._values["master_node_weight"] = master_node_weight
        if proxy_mode is not None:
            self._values["proxy_mode"] = proxy_mode
        if proxy_name is not None:
            self._values["proxy_name"] = proxy_name
        if readonly_nodes_weight is not None:
            self._values["readonly_nodes_weight"] = readonly_nodes_weight
        if timeouts is not None:
            self._values["timeouts"] = timeouts

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
    def flavor(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#flavor TaurusdbMysqlProxyV3#flavor}.'''
        result = self._values.get("flavor")
        assert result is not None, "Required property 'flavor' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def instance_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#instance_id TaurusdbMysqlProxyV3#instance_id}.'''
        result = self._values.get("instance_id")
        assert result is not None, "Required property 'instance_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def node_num(self) -> jsii.Number:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#node_num TaurusdbMysqlProxyV3#node_num}.'''
        result = self._values.get("node_num")
        assert result is not None, "Required property 'node_num' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#id TaurusdbMysqlProxyV3#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def master_node_weight(
        self,
    ) -> typing.Optional["TaurusdbMysqlProxyV3MasterNodeWeight"]:
        '''master_node_weight block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#master_node_weight TaurusdbMysqlProxyV3#master_node_weight}
        '''
        result = self._values.get("master_node_weight")
        return typing.cast(typing.Optional["TaurusdbMysqlProxyV3MasterNodeWeight"], result)

    @builtins.property
    def proxy_mode(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#proxy_mode TaurusdbMysqlProxyV3#proxy_mode}.'''
        result = self._values.get("proxy_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def proxy_name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#proxy_name TaurusdbMysqlProxyV3#proxy_name}.'''
        result = self._values.get("proxy_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def readonly_nodes_weight(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["TaurusdbMysqlProxyV3ReadonlyNodesWeight"]]]:
        '''readonly_nodes_weight block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#readonly_nodes_weight TaurusdbMysqlProxyV3#readonly_nodes_weight}
        '''
        result = self._values.get("readonly_nodes_weight")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["TaurusdbMysqlProxyV3ReadonlyNodesWeight"]]], result)

    @builtins.property
    def timeouts(self) -> typing.Optional["TaurusdbMysqlProxyV3Timeouts"]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#timeouts TaurusdbMysqlProxyV3#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional["TaurusdbMysqlProxyV3Timeouts"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TaurusdbMysqlProxyV3Config(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3MasterNodeWeight",
    jsii_struct_bases=[],
    name_mapping={"id": "id", "weight": "weight"},
)
class TaurusdbMysqlProxyV3MasterNodeWeight:
    def __init__(self, *, id: builtins.str, weight: jsii.Number) -> None:
        '''
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#id TaurusdbMysqlProxyV3#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param weight: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#weight TaurusdbMysqlProxyV3#weight}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c4bed4310a859db974c8fc67f3bc3c9301e12e6db6f0cf73cfe2ba07e0bbf7fc)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument weight", value=weight, expected_type=type_hints["weight"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
            "weight": weight,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#id TaurusdbMysqlProxyV3#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def weight(self) -> jsii.Number:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#weight TaurusdbMysqlProxyV3#weight}.'''
        result = self._values.get("weight")
        assert result is not None, "Required property 'weight' is missing"
        return typing.cast(jsii.Number, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TaurusdbMysqlProxyV3MasterNodeWeight(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class TaurusdbMysqlProxyV3MasterNodeWeightOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3MasterNodeWeightOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__7eccf53f317464979cc313f1a69759770d0cba85ac531075095b6e9cb54c4037)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="weightInput")
    def weight_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "weightInput"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1a23e1cd814472566866058fb4ff77bd3b400ac57d65d29b608aa741dada1528)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="weight")
    def weight(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "weight"))

    @weight.setter
    def weight(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__46b09aa3c65a5eeabb93a93a4570ffa9b7c6c2034e55cb69dabe4375c5b8516e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "weight", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[TaurusdbMysqlProxyV3MasterNodeWeight]:
        return typing.cast(typing.Optional[TaurusdbMysqlProxyV3MasterNodeWeight], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[TaurusdbMysqlProxyV3MasterNodeWeight],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__009b3f663bc94b246d4cdf8257652af2334eb79393826773a1e8a2caeed21130)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3Nodes",
    jsii_struct_bases=[],
    name_mapping={},
)
class TaurusdbMysqlProxyV3Nodes:
    def __init__(self) -> None:
        self._values: typing.Dict[builtins.str, typing.Any] = {}

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TaurusdbMysqlProxyV3Nodes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class TaurusdbMysqlProxyV3NodesList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3NodesList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__0369c6783e7e0003985b93a19db408c2a51afc767347c61a64e4d21fb75e2325)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(self, index: jsii.Number) -> "TaurusdbMysqlProxyV3NodesOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d6174b9da847efb7a44b03f6262609ce4f9d2d0c14ac13364247513852c9d6d8)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("TaurusdbMysqlProxyV3NodesOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__60b49565aa8b29a7cce7b5dc41ec60d8e365c9aabf4bf4f06103826160436626)
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
            type_hints = typing.get_type_hints(_typecheckingstub__303f28fcf8c981676cfd4bf227822b4fadb90ab240a09381c38cb92d4cfadeff)
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
            type_hints = typing.get_type_hints(_typecheckingstub__011f1487f968e01cdc9c7df48e4d5908d26337d4e79e29aff630baf83fbb92b0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]


class TaurusdbMysqlProxyV3NodesOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3NodesOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__5865e118ad2d054ef85acba178c3fa53beed6e4c1bcc911f51efb2f4a77236a7)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @builtins.property
    @jsii.member(jsii_name="azCode")
    def az_code(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "azCode"))

    @builtins.property
    @jsii.member(jsii_name="frozenFlag")
    def frozen_flag(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "frozenFlag"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="role")
    def role(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "role"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[TaurusdbMysqlProxyV3Nodes]:
        return typing.cast(typing.Optional[TaurusdbMysqlProxyV3Nodes], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(self, value: typing.Optional[TaurusdbMysqlProxyV3Nodes]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1c9774faabe56f82a36078ed1b15ba43feb742c835dca24cc5bf0efbfe94c093)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3ReadonlyNodesWeight",
    jsii_struct_bases=[],
    name_mapping={"id": "id", "weight": "weight"},
)
class TaurusdbMysqlProxyV3ReadonlyNodesWeight:
    def __init__(self, *, id: builtins.str, weight: jsii.Number) -> None:
        '''
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#id TaurusdbMysqlProxyV3#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param weight: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#weight TaurusdbMysqlProxyV3#weight}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0887ddbee84be5604ac05f0b2eb566162fa8a5910821572fadace298d868b386)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument weight", value=weight, expected_type=type_hints["weight"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
            "weight": weight,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#id TaurusdbMysqlProxyV3#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def weight(self) -> jsii.Number:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#weight TaurusdbMysqlProxyV3#weight}.'''
        result = self._values.get("weight")
        assert result is not None, "Required property 'weight' is missing"
        return typing.cast(jsii.Number, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TaurusdbMysqlProxyV3ReadonlyNodesWeight(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class TaurusdbMysqlProxyV3ReadonlyNodesWeightList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3ReadonlyNodesWeightList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__86ef3f183adafdcd8a76636d2038468d72014fbafdc6cbd1765398155fc0ce13)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "TaurusdbMysqlProxyV3ReadonlyNodesWeightOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4eaf0610972fa10f236226b63f7a5cc3ac39dc1b34b972348e7f779c5a36f76a)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("TaurusdbMysqlProxyV3ReadonlyNodesWeightOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__015f981c9c37baf95ef9683c5d41e9dc58728b4353cec4da47baa7ba4d748434)
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
            type_hints = typing.get_type_hints(_typecheckingstub__e3749dfedec071f0bb469a1a1fa4270a985c30cfbe96e1d48f6c6e7c46ff76af)
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
            type_hints = typing.get_type_hints(_typecheckingstub__4a59911e0524981779ad02442dc577c90681e1b06c27ecab77434a99305d8df4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[TaurusdbMysqlProxyV3ReadonlyNodesWeight]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[TaurusdbMysqlProxyV3ReadonlyNodesWeight]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[TaurusdbMysqlProxyV3ReadonlyNodesWeight]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b33ae3a303f8e3b6d5227975b1cb7c87df2436119b3bd3a1a4451f16d5a6973a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class TaurusdbMysqlProxyV3ReadonlyNodesWeightOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3ReadonlyNodesWeightOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__5538e01e4a70a6956fb89adb0061780e8df3dff2ed70a504992892f0ac7f5f39)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="weightInput")
    def weight_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "weightInput"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3335f399697b1c97502b51ded69abaa0e1b165a2e1c6696655122e1f00fee881)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="weight")
    def weight(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "weight"))

    @weight.setter
    def weight(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__946a0aaacc424c63061175b63bf89d980b429e7bcf84ffb2bcfb9a86f683ee77)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "weight", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, TaurusdbMysqlProxyV3ReadonlyNodesWeight]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, TaurusdbMysqlProxyV3ReadonlyNodesWeight]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, TaurusdbMysqlProxyV3ReadonlyNodesWeight]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__360759fddd64583baaac2ff6fd11e6660c9a7f9823f9b79fa932607cdf78d391)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3Timeouts",
    jsii_struct_bases=[],
    name_mapping={"create": "create", "delete": "delete", "update": "update"},
)
class TaurusdbMysqlProxyV3Timeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#create TaurusdbMysqlProxyV3#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#delete TaurusdbMysqlProxyV3#delete}.
        :param update: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#update TaurusdbMysqlProxyV3#update}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__de6540b4b18b5aa20497957d5367bbf3390c7d9ca6c9885359ae32b3e8b42e67)
            check_type(argname="argument create", value=create, expected_type=type_hints["create"])
            check_type(argname="argument delete", value=delete, expected_type=type_hints["delete"])
            check_type(argname="argument update", value=update, expected_type=type_hints["update"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create is not None:
            self._values["create"] = create
        if delete is not None:
            self._values["delete"] = delete
        if update is not None:
            self._values["update"] = update

    @builtins.property
    def create(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#create TaurusdbMysqlProxyV3#create}.'''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#delete TaurusdbMysqlProxyV3#delete}.'''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def update(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/taurusdb_mysql_proxy_v3#update TaurusdbMysqlProxyV3#update}.'''
        result = self._values.get("update")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TaurusdbMysqlProxyV3Timeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class TaurusdbMysqlProxyV3TimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.taurusdbMysqlProxyV3.TaurusdbMysqlProxyV3TimeoutsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__e2683820b356c8204f2999fa4fc99c12a32f6bd1176f3da068bef58ceea5583c)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCreate")
    def reset_create(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreate", []))

    @jsii.member(jsii_name="resetDelete")
    def reset_delete(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDelete", []))

    @jsii.member(jsii_name="resetUpdate")
    def reset_update(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdate", []))

    @builtins.property
    @jsii.member(jsii_name="createInput")
    def create_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createInput"))

    @builtins.property
    @jsii.member(jsii_name="deleteInput")
    def delete_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "deleteInput"))

    @builtins.property
    @jsii.member(jsii_name="updateInput")
    def update_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "updateInput"))

    @builtins.property
    @jsii.member(jsii_name="create")
    def create(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "create"))

    @create.setter
    def create(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9dac51f52484f638244088bcb16210ad60bb53901f0aec7e435d0681a61189f1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0507c7ccb233884841923ad97a7da534b11968036255e0d020481a3c9d9a08c1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="update")
    def update(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "update"))

    @update.setter
    def update(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa70756a19b21772c582f77db2e4428971d5d9cf6579fe822f82d349ae28b14a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "update", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, TaurusdbMysqlProxyV3Timeouts]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, TaurusdbMysqlProxyV3Timeouts]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, TaurusdbMysqlProxyV3Timeouts]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2a6de045850d17e5efb5867bd68393537549eff316c5eac25c367c8554ee6b2d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "TaurusdbMysqlProxyV3",
    "TaurusdbMysqlProxyV3Config",
    "TaurusdbMysqlProxyV3MasterNodeWeight",
    "TaurusdbMysqlProxyV3MasterNodeWeightOutputReference",
    "TaurusdbMysqlProxyV3Nodes",
    "TaurusdbMysqlProxyV3NodesList",
    "TaurusdbMysqlProxyV3NodesOutputReference",
    "TaurusdbMysqlProxyV3ReadonlyNodesWeight",
    "TaurusdbMysqlProxyV3ReadonlyNodesWeightList",
    "TaurusdbMysqlProxyV3ReadonlyNodesWeightOutputReference",
    "TaurusdbMysqlProxyV3Timeouts",
    "TaurusdbMysqlProxyV3TimeoutsOutputReference",
]

publication.publish()

def _typecheckingstub__47ae0b382b22d87a11cc4c879aa52daf263110c9a5229a869ce97a0a9d2d2f2a(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    flavor: builtins.str,
    instance_id: builtins.str,
    node_num: jsii.Number,
    id: typing.Optional[builtins.str] = None,
    master_node_weight: typing.Optional[typing.Union[TaurusdbMysqlProxyV3MasterNodeWeight, typing.Dict[builtins.str, typing.Any]]] = None,
    proxy_mode: typing.Optional[builtins.str] = None,
    proxy_name: typing.Optional[builtins.str] = None,
    readonly_nodes_weight: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[TaurusdbMysqlProxyV3ReadonlyNodesWeight, typing.Dict[builtins.str, typing.Any]]]]] = None,
    timeouts: typing.Optional[typing.Union[TaurusdbMysqlProxyV3Timeouts, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__3b9544cdd191009a727da0f458c8e15711093d87d479a902a9d7be04af1e8e10(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__12db498382d9aa8662c1dc16719162b9ae53c56a72eea7af56f13b03438015e7(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[TaurusdbMysqlProxyV3ReadonlyNodesWeight, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__31b2ab0112fffc0f60c34490378d5498fcfa627b2935943d27f239134b3de4bb(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5c4aa8a752854098ea8be42ebdab1b2a15386a250de592612b419cba8edcf9ec(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__62e541adddfa5d21dd9fa2559553b9c41a389e11f1d8d2515ce0d33f4d26a056(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3fbc949c47991ac4cf44ea825c7ae712d596c0f7d82c522a6c59b87cf63f6d2d(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0dd2c502c45c2642b75553230f7dc9375d18cf55b9c0a487d90b7bc20cc08b4d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__29ee28040ac24657902548913a15ef3d3218725509fc51ad0f318cbe3c0d787a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9afe07297896f0c30de494d369b2b8c86d3923f88ea82b11d5732dbd33aa6963(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    flavor: builtins.str,
    instance_id: builtins.str,
    node_num: jsii.Number,
    id: typing.Optional[builtins.str] = None,
    master_node_weight: typing.Optional[typing.Union[TaurusdbMysqlProxyV3MasterNodeWeight, typing.Dict[builtins.str, typing.Any]]] = None,
    proxy_mode: typing.Optional[builtins.str] = None,
    proxy_name: typing.Optional[builtins.str] = None,
    readonly_nodes_weight: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[TaurusdbMysqlProxyV3ReadonlyNodesWeight, typing.Dict[builtins.str, typing.Any]]]]] = None,
    timeouts: typing.Optional[typing.Union[TaurusdbMysqlProxyV3Timeouts, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c4bed4310a859db974c8fc67f3bc3c9301e12e6db6f0cf73cfe2ba07e0bbf7fc(
    *,
    id: builtins.str,
    weight: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7eccf53f317464979cc313f1a69759770d0cba85ac531075095b6e9cb54c4037(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1a23e1cd814472566866058fb4ff77bd3b400ac57d65d29b608aa741dada1528(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__46b09aa3c65a5eeabb93a93a4570ffa9b7c6c2034e55cb69dabe4375c5b8516e(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__009b3f663bc94b246d4cdf8257652af2334eb79393826773a1e8a2caeed21130(
    value: typing.Optional[TaurusdbMysqlProxyV3MasterNodeWeight],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0369c6783e7e0003985b93a19db408c2a51afc767347c61a64e4d21fb75e2325(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d6174b9da847efb7a44b03f6262609ce4f9d2d0c14ac13364247513852c9d6d8(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__60b49565aa8b29a7cce7b5dc41ec60d8e365c9aabf4bf4f06103826160436626(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__303f28fcf8c981676cfd4bf227822b4fadb90ab240a09381c38cb92d4cfadeff(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__011f1487f968e01cdc9c7df48e4d5908d26337d4e79e29aff630baf83fbb92b0(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5865e118ad2d054ef85acba178c3fa53beed6e4c1bcc911f51efb2f4a77236a7(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1c9774faabe56f82a36078ed1b15ba43feb742c835dca24cc5bf0efbfe94c093(
    value: typing.Optional[TaurusdbMysqlProxyV3Nodes],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0887ddbee84be5604ac05f0b2eb566162fa8a5910821572fadace298d868b386(
    *,
    id: builtins.str,
    weight: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__86ef3f183adafdcd8a76636d2038468d72014fbafdc6cbd1765398155fc0ce13(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4eaf0610972fa10f236226b63f7a5cc3ac39dc1b34b972348e7f779c5a36f76a(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__015f981c9c37baf95ef9683c5d41e9dc58728b4353cec4da47baa7ba4d748434(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e3749dfedec071f0bb469a1a1fa4270a985c30cfbe96e1d48f6c6e7c46ff76af(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4a59911e0524981779ad02442dc577c90681e1b06c27ecab77434a99305d8df4(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b33ae3a303f8e3b6d5227975b1cb7c87df2436119b3bd3a1a4451f16d5a6973a(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[TaurusdbMysqlProxyV3ReadonlyNodesWeight]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5538e01e4a70a6956fb89adb0061780e8df3dff2ed70a504992892f0ac7f5f39(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3335f399697b1c97502b51ded69abaa0e1b165a2e1c6696655122e1f00fee881(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__946a0aaacc424c63061175b63bf89d980b429e7bcf84ffb2bcfb9a86f683ee77(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__360759fddd64583baaac2ff6fd11e6660c9a7f9823f9b79fa932607cdf78d391(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, TaurusdbMysqlProxyV3ReadonlyNodesWeight]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__de6540b4b18b5aa20497957d5367bbf3390c7d9ca6c9885359ae32b3e8b42e67(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
    update: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e2683820b356c8204f2999fa4fc99c12a32f6bd1176f3da068bef58ceea5583c(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9dac51f52484f638244088bcb16210ad60bb53901f0aec7e435d0681a61189f1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0507c7ccb233884841923ad97a7da534b11968036255e0d020481a3c9d9a08c1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa70756a19b21772c582f77db2e4428971d5d9cf6579fe822f82d349ae28b14a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a6de045850d17e5efb5867bd68393537549eff316c5eac25c367c8554ee6b2d(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, TaurusdbMysqlProxyV3Timeouts]],
) -> None:
    """Type checking stubs"""
    pass
