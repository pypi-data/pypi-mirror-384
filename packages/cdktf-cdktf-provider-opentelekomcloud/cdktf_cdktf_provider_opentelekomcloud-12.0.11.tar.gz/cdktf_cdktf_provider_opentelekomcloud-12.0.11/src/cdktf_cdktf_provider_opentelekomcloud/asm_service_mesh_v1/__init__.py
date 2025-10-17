r'''
# `opentelekomcloud_asm_service_mesh_v1`

Refer to the Terraform Registry for docs: [`opentelekomcloud_asm_service_mesh_v1`](https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1).
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


class AsmServiceMeshV1(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1",
):
    '''Represents a {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1 opentelekomcloud_asm_service_mesh_v1}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id_: builtins.str,
        *,
        clusters: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["AsmServiceMeshV1Clusters", typing.Dict[builtins.str, typing.Any]]]],
        name: builtins.str,
        type: builtins.str,
        version: builtins.str,
        id: typing.Optional[builtins.str] = None,
        ipv6_enable: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        proxy_config: typing.Optional[typing.Union["AsmServiceMeshV1ProxyConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        telemetry_config_tracing: typing.Optional[typing.Union["AsmServiceMeshV1TelemetryConfigTracing", typing.Dict[builtins.str, typing.Any]]] = None,
        timeouts: typing.Optional[typing.Union["AsmServiceMeshV1Timeouts", typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1 opentelekomcloud_asm_service_mesh_v1} Resource.

        :param scope: The scope in which to define this construct.
        :param id_: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param clusters: clusters block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#clusters AsmServiceMeshV1#clusters}
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#name AsmServiceMeshV1#name}.
        :param type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#type AsmServiceMeshV1#type}.
        :param version: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#version AsmServiceMeshV1#version}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#id AsmServiceMeshV1#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param ipv6_enable: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#ipv6_enable AsmServiceMeshV1#ipv6_enable}.
        :param proxy_config: proxy_config block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#proxy_config AsmServiceMeshV1#proxy_config}
        :param telemetry_config_tracing: telemetry_config_tracing block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#telemetry_config_tracing AsmServiceMeshV1#telemetry_config_tracing}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#timeouts AsmServiceMeshV1#timeouts}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c58ddf9929244d7fb704b993ec6a6547166281f4f4c496f38b91ca3d30cde986)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id_", value=id_, expected_type=type_hints["id_"])
        config = AsmServiceMeshV1Config(
            clusters=clusters,
            name=name,
            type=type,
            version=version,
            id=id,
            ipv6_enable=ipv6_enable,
            proxy_config=proxy_config,
            telemetry_config_tracing=telemetry_config_tracing,
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
        '''Generates CDKTF code for importing a AsmServiceMeshV1 resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the AsmServiceMeshV1 to import.
        :param import_from_id: The id of the existing AsmServiceMeshV1 that should be imported. Refer to the {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the AsmServiceMeshV1 to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__79bd83bb6056ece168f7b9695d7f951e485e345026cace95ff779bdebe7c74d3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putClusters")
    def put_clusters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["AsmServiceMeshV1Clusters", typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ff1501ca883f5f54b3f798a3197b98e9dc4a6e8046e87c18c7f87c1e769a80e2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putClusters", [value]))

    @jsii.member(jsii_name="putProxyConfig")
    def put_proxy_config(
        self,
        *,
        exclude_inbound_ports: typing.Optional[builtins.str] = None,
        exclude_ip_ranges: typing.Optional[builtins.str] = None,
        exclude_outbound_ports: typing.Optional[builtins.str] = None,
        include_inbound_ports: typing.Optional[builtins.str] = None,
        include_ip_ranges: typing.Optional[builtins.str] = None,
        include_outbound_ports: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param exclude_inbound_ports: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#exclude_inbound_ports AsmServiceMeshV1#exclude_inbound_ports}.
        :param exclude_ip_ranges: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#exclude_ip_ranges AsmServiceMeshV1#exclude_ip_ranges}.
        :param exclude_outbound_ports: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#exclude_outbound_ports AsmServiceMeshV1#exclude_outbound_ports}.
        :param include_inbound_ports: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#include_inbound_ports AsmServiceMeshV1#include_inbound_ports}.
        :param include_ip_ranges: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#include_ip_ranges AsmServiceMeshV1#include_ip_ranges}.
        :param include_outbound_ports: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#include_outbound_ports AsmServiceMeshV1#include_outbound_ports}.
        '''
        value = AsmServiceMeshV1ProxyConfig(
            exclude_inbound_ports=exclude_inbound_ports,
            exclude_ip_ranges=exclude_ip_ranges,
            exclude_outbound_ports=exclude_outbound_ports,
            include_inbound_ports=include_inbound_ports,
            include_ip_ranges=include_ip_ranges,
            include_outbound_ports=include_outbound_ports,
        )

        return typing.cast(None, jsii.invoke(self, "putProxyConfig", [value]))

    @jsii.member(jsii_name="putTelemetryConfigTracing")
    def put_telemetry_config_tracing(
        self,
        *,
        default_providers: typing.Optional[typing.Sequence[builtins.str]] = None,
        extension_providers: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["AsmServiceMeshV1TelemetryConfigTracingExtensionProviders", typing.Dict[builtins.str, typing.Any]]]]] = None,
        random_sampling_percentage: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param default_providers: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#default_providers AsmServiceMeshV1#default_providers}.
        :param extension_providers: extension_providers block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#extension_providers AsmServiceMeshV1#extension_providers}
        :param random_sampling_percentage: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#random_sampling_percentage AsmServiceMeshV1#random_sampling_percentage}.
        '''
        value = AsmServiceMeshV1TelemetryConfigTracing(
            default_providers=default_providers,
            extension_providers=extension_providers,
            random_sampling_percentage=random_sampling_percentage,
        )

        return typing.cast(None, jsii.invoke(self, "putTelemetryConfigTracing", [value]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#create AsmServiceMeshV1#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#delete AsmServiceMeshV1#delete}.
        '''
        value = AsmServiceMeshV1Timeouts(create=create, delete=delete)

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetId")
    def reset_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetId", []))

    @jsii.member(jsii_name="resetIpv6Enable")
    def reset_ipv6_enable(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIpv6Enable", []))

    @jsii.member(jsii_name="resetProxyConfig")
    def reset_proxy_config(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetProxyConfig", []))

    @jsii.member(jsii_name="resetTelemetryConfigTracing")
    def reset_telemetry_config_tracing(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTelemetryConfigTracing", []))

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
    @jsii.member(jsii_name="clusterIds")
    def cluster_ids(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "clusterIds"))

    @builtins.property
    @jsii.member(jsii_name="clusters")
    def clusters(self) -> "AsmServiceMeshV1ClustersList":
        return typing.cast("AsmServiceMeshV1ClustersList", jsii.get(self, "clusters"))

    @builtins.property
    @jsii.member(jsii_name="creationTimestamp")
    def creation_timestamp(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "creationTimestamp"))

    @builtins.property
    @jsii.member(jsii_name="proxyConfig")
    def proxy_config(self) -> "AsmServiceMeshV1ProxyConfigOutputReference":
        return typing.cast("AsmServiceMeshV1ProxyConfigOutputReference", jsii.get(self, "proxyConfig"))

    @builtins.property
    @jsii.member(jsii_name="status")
    def status(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "status"))

    @builtins.property
    @jsii.member(jsii_name="telemetryConfigTracing")
    def telemetry_config_tracing(
        self,
    ) -> "AsmServiceMeshV1TelemetryConfigTracingOutputReference":
        return typing.cast("AsmServiceMeshV1TelemetryConfigTracingOutputReference", jsii.get(self, "telemetryConfigTracing"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> "AsmServiceMeshV1TimeoutsOutputReference":
        return typing.cast("AsmServiceMeshV1TimeoutsOutputReference", jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="clustersInput")
    def clusters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["AsmServiceMeshV1Clusters"]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["AsmServiceMeshV1Clusters"]]], jsii.get(self, "clustersInput"))

    @builtins.property
    @jsii.member(jsii_name="idInput")
    def id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "idInput"))

    @builtins.property
    @jsii.member(jsii_name="ipv6EnableInput")
    def ipv6_enable_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "ipv6EnableInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="proxyConfigInput")
    def proxy_config_input(self) -> typing.Optional["AsmServiceMeshV1ProxyConfig"]:
        return typing.cast(typing.Optional["AsmServiceMeshV1ProxyConfig"], jsii.get(self, "proxyConfigInput"))

    @builtins.property
    @jsii.member(jsii_name="telemetryConfigTracingInput")
    def telemetry_config_tracing_input(
        self,
    ) -> typing.Optional["AsmServiceMeshV1TelemetryConfigTracing"]:
        return typing.cast(typing.Optional["AsmServiceMeshV1TelemetryConfigTracing"], jsii.get(self, "telemetryConfigTracingInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "AsmServiceMeshV1Timeouts"]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, "AsmServiceMeshV1Timeouts"]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="typeInput")
    def type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "typeInput"))

    @builtins.property
    @jsii.member(jsii_name="versionInput")
    def version_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "versionInput"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6ca4f0ad254c42ff7dd5d76edeb818f118a47e52764e6dbe4265e2efda06f248)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ipv6Enable")
    def ipv6_enable(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "ipv6Enable"))

    @ipv6_enable.setter
    def ipv6_enable(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d9a1bfebf0352eb6b9069863eda5095e19e1c2c6a95d6b1960797184a14103ff)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ipv6Enable", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__146e4cb60ac5527a2dff5eb6b866b8581aa7f9f6f94de8be0b41bbac56b431ef)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d5bde1080a4ae541525460ffcab554b68ccfc44813af706a4f243cf3e970f0a1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="version")
    def version(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "version"))

    @version.setter
    def version(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b9ac320cf46d259cb98c15b9bac8e7aa24f014ddeaacee6c25b34773342693cd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "version", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1Clusters",
    jsii_struct_bases=[],
    name_mapping={
        "cluster_id": "clusterId",
        "installation_nodes": "installationNodes",
        "injection_namespaces": "injectionNamespaces",
    },
)
class AsmServiceMeshV1Clusters:
    def __init__(
        self,
        *,
        cluster_id: builtins.str,
        installation_nodes: typing.Sequence[builtins.str],
        injection_namespaces: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param cluster_id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#cluster_id AsmServiceMeshV1#cluster_id}.
        :param installation_nodes: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#installation_nodes AsmServiceMeshV1#installation_nodes}.
        :param injection_namespaces: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#injection_namespaces AsmServiceMeshV1#injection_namespaces}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8975e641ddf1ae1a29b77aa6b1d7a6a69c12c86a94f32f75a2b72ddeee931e26)
            check_type(argname="argument cluster_id", value=cluster_id, expected_type=type_hints["cluster_id"])
            check_type(argname="argument installation_nodes", value=installation_nodes, expected_type=type_hints["installation_nodes"])
            check_type(argname="argument injection_namespaces", value=injection_namespaces, expected_type=type_hints["injection_namespaces"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cluster_id": cluster_id,
            "installation_nodes": installation_nodes,
        }
        if injection_namespaces is not None:
            self._values["injection_namespaces"] = injection_namespaces

    @builtins.property
    def cluster_id(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#cluster_id AsmServiceMeshV1#cluster_id}.'''
        result = self._values.get("cluster_id")
        assert result is not None, "Required property 'cluster_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def installation_nodes(self) -> typing.List[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#installation_nodes AsmServiceMeshV1#installation_nodes}.'''
        result = self._values.get("installation_nodes")
        assert result is not None, "Required property 'installation_nodes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def injection_namespaces(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#injection_namespaces AsmServiceMeshV1#injection_namespaces}.'''
        result = self._values.get("injection_namespaces")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AsmServiceMeshV1Clusters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class AsmServiceMeshV1ClustersList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1ClustersList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__92ddce252053460aaab691a9b89013ae6235661fafadad37f55ef160c1ce10b3)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(self, index: jsii.Number) -> "AsmServiceMeshV1ClustersOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f80ff232a64c118c76dd479be9b95b8ea84efa9d7c17e59cc89868233539d853)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("AsmServiceMeshV1ClustersOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6dc787099603dbf4bc5b9abb6a8ee0070ce3665696c2043591bd67394eadcedb)
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
            type_hints = typing.get_type_hints(_typecheckingstub__9d227ea132e53bdcc61ac3f3152c3a1e84d3d60e7ef86074cdee8ab54ef6a19a)
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
            type_hints = typing.get_type_hints(_typecheckingstub__9684f879e6f5b13664226fe5a8ffb1dc7c4beb868c9883d0f2882fac096f8f5a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1Clusters]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1Clusters]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1Clusters]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2e9a7a874000a093df157261553f21cb36afde6f6346ec3f2048555886bd6a78)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class AsmServiceMeshV1ClustersOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1ClustersOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__94231ed6fafa0c9c10366501bd22fff7bfe47e06bb88037b441431120ff1de5f)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetInjectionNamespaces")
    def reset_injection_namespaces(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetInjectionNamespaces", []))

    @builtins.property
    @jsii.member(jsii_name="clusterIdInput")
    def cluster_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clusterIdInput"))

    @builtins.property
    @jsii.member(jsii_name="injectionNamespacesInput")
    def injection_namespaces_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "injectionNamespacesInput"))

    @builtins.property
    @jsii.member(jsii_name="installationNodesInput")
    def installation_nodes_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "installationNodesInput"))

    @builtins.property
    @jsii.member(jsii_name="clusterId")
    def cluster_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "clusterId"))

    @cluster_id.setter
    def cluster_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ec888d0b23ad1390616577285f480f8a0aa1f8ed459a3518852218b9b6b74801)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "clusterId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="injectionNamespaces")
    def injection_namespaces(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "injectionNamespaces"))

    @injection_namespaces.setter
    def injection_namespaces(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__57274a32fb8c87440ee168c539486b74e27a9d5c5f1b31d5af1dfad6dd7daf7d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "injectionNamespaces", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="installationNodes")
    def installation_nodes(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "installationNodes"))

    @installation_nodes.setter
    def installation_nodes(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cf096c3adda329c861bf603304e0ce4252e1abbb2b0f01a3b947c9fb740034de)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "installationNodes", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1Clusters]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1Clusters]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1Clusters]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0c29eea85f6a5dffe3f5e64d1483bb32ddf0c4fbaa42b8b6e3dfcfaa679cd276)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1Config",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "clusters": "clusters",
        "name": "name",
        "type": "type",
        "version": "version",
        "id": "id",
        "ipv6_enable": "ipv6Enable",
        "proxy_config": "proxyConfig",
        "telemetry_config_tracing": "telemetryConfigTracing",
        "timeouts": "timeouts",
    },
)
class AsmServiceMeshV1Config(_cdktf_9a9027ec.TerraformMetaArguments):
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
        clusters: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[AsmServiceMeshV1Clusters, typing.Dict[builtins.str, typing.Any]]]],
        name: builtins.str,
        type: builtins.str,
        version: builtins.str,
        id: typing.Optional[builtins.str] = None,
        ipv6_enable: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        proxy_config: typing.Optional[typing.Union["AsmServiceMeshV1ProxyConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        telemetry_config_tracing: typing.Optional[typing.Union["AsmServiceMeshV1TelemetryConfigTracing", typing.Dict[builtins.str, typing.Any]]] = None,
        timeouts: typing.Optional[typing.Union["AsmServiceMeshV1Timeouts", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param clusters: clusters block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#clusters AsmServiceMeshV1#clusters}
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#name AsmServiceMeshV1#name}.
        :param type: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#type AsmServiceMeshV1#type}.
        :param version: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#version AsmServiceMeshV1#version}.
        :param id: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#id AsmServiceMeshV1#id}. Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2. If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        :param ipv6_enable: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#ipv6_enable AsmServiceMeshV1#ipv6_enable}.
        :param proxy_config: proxy_config block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#proxy_config AsmServiceMeshV1#proxy_config}
        :param telemetry_config_tracing: telemetry_config_tracing block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#telemetry_config_tracing AsmServiceMeshV1#telemetry_config_tracing}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#timeouts AsmServiceMeshV1#timeouts}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(proxy_config, dict):
            proxy_config = AsmServiceMeshV1ProxyConfig(**proxy_config)
        if isinstance(telemetry_config_tracing, dict):
            telemetry_config_tracing = AsmServiceMeshV1TelemetryConfigTracing(**telemetry_config_tracing)
        if isinstance(timeouts, dict):
            timeouts = AsmServiceMeshV1Timeouts(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c65309e1289cac320034f746760e7b1056589049ad31e42d15253f3fecd75bd7)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument clusters", value=clusters, expected_type=type_hints["clusters"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument ipv6_enable", value=ipv6_enable, expected_type=type_hints["ipv6_enable"])
            check_type(argname="argument proxy_config", value=proxy_config, expected_type=type_hints["proxy_config"])
            check_type(argname="argument telemetry_config_tracing", value=telemetry_config_tracing, expected_type=type_hints["telemetry_config_tracing"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "clusters": clusters,
            "name": name,
            "type": type,
            "version": version,
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
        if ipv6_enable is not None:
            self._values["ipv6_enable"] = ipv6_enable
        if proxy_config is not None:
            self._values["proxy_config"] = proxy_config
        if telemetry_config_tracing is not None:
            self._values["telemetry_config_tracing"] = telemetry_config_tracing
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
    def clusters(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1Clusters]]:
        '''clusters block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#clusters AsmServiceMeshV1#clusters}
        '''
        result = self._values.get("clusters")
        assert result is not None, "Required property 'clusters' is missing"
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1Clusters]], result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#name AsmServiceMeshV1#name}.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#type AsmServiceMeshV1#type}.'''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def version(self) -> builtins.str:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#version AsmServiceMeshV1#version}.'''
        result = self._values.get("version")
        assert result is not None, "Required property 'version' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#id AsmServiceMeshV1#id}.

        Please be aware that the id field is automatically added to all resources in Terraform providers using a Terraform provider SDK version below 2.
        If you experience problems setting this value it might not be settable. Please take a look at the provider documentation to ensure it should be settable.
        '''
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ipv6_enable(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#ipv6_enable AsmServiceMeshV1#ipv6_enable}.'''
        result = self._values.get("ipv6_enable")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def proxy_config(self) -> typing.Optional["AsmServiceMeshV1ProxyConfig"]:
        '''proxy_config block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#proxy_config AsmServiceMeshV1#proxy_config}
        '''
        result = self._values.get("proxy_config")
        return typing.cast(typing.Optional["AsmServiceMeshV1ProxyConfig"], result)

    @builtins.property
    def telemetry_config_tracing(
        self,
    ) -> typing.Optional["AsmServiceMeshV1TelemetryConfigTracing"]:
        '''telemetry_config_tracing block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#telemetry_config_tracing AsmServiceMeshV1#telemetry_config_tracing}
        '''
        result = self._values.get("telemetry_config_tracing")
        return typing.cast(typing.Optional["AsmServiceMeshV1TelemetryConfigTracing"], result)

    @builtins.property
    def timeouts(self) -> typing.Optional["AsmServiceMeshV1Timeouts"]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#timeouts AsmServiceMeshV1#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional["AsmServiceMeshV1Timeouts"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AsmServiceMeshV1Config(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1ProxyConfig",
    jsii_struct_bases=[],
    name_mapping={
        "exclude_inbound_ports": "excludeInboundPorts",
        "exclude_ip_ranges": "excludeIpRanges",
        "exclude_outbound_ports": "excludeOutboundPorts",
        "include_inbound_ports": "includeInboundPorts",
        "include_ip_ranges": "includeIpRanges",
        "include_outbound_ports": "includeOutboundPorts",
    },
)
class AsmServiceMeshV1ProxyConfig:
    def __init__(
        self,
        *,
        exclude_inbound_ports: typing.Optional[builtins.str] = None,
        exclude_ip_ranges: typing.Optional[builtins.str] = None,
        exclude_outbound_ports: typing.Optional[builtins.str] = None,
        include_inbound_ports: typing.Optional[builtins.str] = None,
        include_ip_ranges: typing.Optional[builtins.str] = None,
        include_outbound_ports: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param exclude_inbound_ports: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#exclude_inbound_ports AsmServiceMeshV1#exclude_inbound_ports}.
        :param exclude_ip_ranges: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#exclude_ip_ranges AsmServiceMeshV1#exclude_ip_ranges}.
        :param exclude_outbound_ports: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#exclude_outbound_ports AsmServiceMeshV1#exclude_outbound_ports}.
        :param include_inbound_ports: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#include_inbound_ports AsmServiceMeshV1#include_inbound_ports}.
        :param include_ip_ranges: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#include_ip_ranges AsmServiceMeshV1#include_ip_ranges}.
        :param include_outbound_ports: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#include_outbound_ports AsmServiceMeshV1#include_outbound_ports}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3ba3f28b4f9e932e50e65159f54696f7e3269996784aace1b1aa46f41ca3a0ca)
            check_type(argname="argument exclude_inbound_ports", value=exclude_inbound_ports, expected_type=type_hints["exclude_inbound_ports"])
            check_type(argname="argument exclude_ip_ranges", value=exclude_ip_ranges, expected_type=type_hints["exclude_ip_ranges"])
            check_type(argname="argument exclude_outbound_ports", value=exclude_outbound_ports, expected_type=type_hints["exclude_outbound_ports"])
            check_type(argname="argument include_inbound_ports", value=include_inbound_ports, expected_type=type_hints["include_inbound_ports"])
            check_type(argname="argument include_ip_ranges", value=include_ip_ranges, expected_type=type_hints["include_ip_ranges"])
            check_type(argname="argument include_outbound_ports", value=include_outbound_ports, expected_type=type_hints["include_outbound_ports"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if exclude_inbound_ports is not None:
            self._values["exclude_inbound_ports"] = exclude_inbound_ports
        if exclude_ip_ranges is not None:
            self._values["exclude_ip_ranges"] = exclude_ip_ranges
        if exclude_outbound_ports is not None:
            self._values["exclude_outbound_ports"] = exclude_outbound_ports
        if include_inbound_ports is not None:
            self._values["include_inbound_ports"] = include_inbound_ports
        if include_ip_ranges is not None:
            self._values["include_ip_ranges"] = include_ip_ranges
        if include_outbound_ports is not None:
            self._values["include_outbound_ports"] = include_outbound_ports

    @builtins.property
    def exclude_inbound_ports(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#exclude_inbound_ports AsmServiceMeshV1#exclude_inbound_ports}.'''
        result = self._values.get("exclude_inbound_ports")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def exclude_ip_ranges(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#exclude_ip_ranges AsmServiceMeshV1#exclude_ip_ranges}.'''
        result = self._values.get("exclude_ip_ranges")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def exclude_outbound_ports(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#exclude_outbound_ports AsmServiceMeshV1#exclude_outbound_ports}.'''
        result = self._values.get("exclude_outbound_ports")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def include_inbound_ports(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#include_inbound_ports AsmServiceMeshV1#include_inbound_ports}.'''
        result = self._values.get("include_inbound_ports")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def include_ip_ranges(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#include_ip_ranges AsmServiceMeshV1#include_ip_ranges}.'''
        result = self._values.get("include_ip_ranges")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def include_outbound_ports(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#include_outbound_ports AsmServiceMeshV1#include_outbound_ports}.'''
        result = self._values.get("include_outbound_ports")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AsmServiceMeshV1ProxyConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class AsmServiceMeshV1ProxyConfigOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1ProxyConfigOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__48d4aa4c973f1c042307c21437f4274959928e3f368ccbdfa8beb3805e29f4c9)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetExcludeInboundPorts")
    def reset_exclude_inbound_ports(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExcludeInboundPorts", []))

    @jsii.member(jsii_name="resetExcludeIpRanges")
    def reset_exclude_ip_ranges(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExcludeIpRanges", []))

    @jsii.member(jsii_name="resetExcludeOutboundPorts")
    def reset_exclude_outbound_ports(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExcludeOutboundPorts", []))

    @jsii.member(jsii_name="resetIncludeInboundPorts")
    def reset_include_inbound_ports(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeInboundPorts", []))

    @jsii.member(jsii_name="resetIncludeIpRanges")
    def reset_include_ip_ranges(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeIpRanges", []))

    @jsii.member(jsii_name="resetIncludeOutboundPorts")
    def reset_include_outbound_ports(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIncludeOutboundPorts", []))

    @builtins.property
    @jsii.member(jsii_name="excludeInboundPortsInput")
    def exclude_inbound_ports_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "excludeInboundPortsInput"))

    @builtins.property
    @jsii.member(jsii_name="excludeIpRangesInput")
    def exclude_ip_ranges_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "excludeIpRangesInput"))

    @builtins.property
    @jsii.member(jsii_name="excludeOutboundPortsInput")
    def exclude_outbound_ports_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "excludeOutboundPortsInput"))

    @builtins.property
    @jsii.member(jsii_name="includeInboundPortsInput")
    def include_inbound_ports_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "includeInboundPortsInput"))

    @builtins.property
    @jsii.member(jsii_name="includeIpRangesInput")
    def include_ip_ranges_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "includeIpRangesInput"))

    @builtins.property
    @jsii.member(jsii_name="includeOutboundPortsInput")
    def include_outbound_ports_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "includeOutboundPortsInput"))

    @builtins.property
    @jsii.member(jsii_name="excludeInboundPorts")
    def exclude_inbound_ports(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "excludeInboundPorts"))

    @exclude_inbound_ports.setter
    def exclude_inbound_ports(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__04cb12ae207ad04b37e0279946cf4cb85c85747af293d787b6d572b7e2e0ebd2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "excludeInboundPorts", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="excludeIpRanges")
    def exclude_ip_ranges(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "excludeIpRanges"))

    @exclude_ip_ranges.setter
    def exclude_ip_ranges(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6a3e925bc8f45945142f8c9bf67993c038b1e05d4280cb4860e8a47559652dd4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "excludeIpRanges", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="excludeOutboundPorts")
    def exclude_outbound_ports(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "excludeOutboundPorts"))

    @exclude_outbound_ports.setter
    def exclude_outbound_ports(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__89b0f1a21efc8130e02db54f1064cfc382b785036e6be22d9dd450effbdcb36b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "excludeOutboundPorts", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeInboundPorts")
    def include_inbound_ports(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "includeInboundPorts"))

    @include_inbound_ports.setter
    def include_inbound_ports(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8367a5c724fb8784fdaf0bb36067dfef3ed1ee8b5001dbbab098538806ce8611)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeInboundPorts", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeIpRanges")
    def include_ip_ranges(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "includeIpRanges"))

    @include_ip_ranges.setter
    def include_ip_ranges(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__22b01b0a5035d0c60c6d47eded0df8ff21989bd883e4b1adfa0596dcc5f8a962)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeIpRanges", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="includeOutboundPorts")
    def include_outbound_ports(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "includeOutboundPorts"))

    @include_outbound_ports.setter
    def include_outbound_ports(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e5e1312a26bce727ab4bf494c306d517d337b35042f059af84d62038f3412512)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "includeOutboundPorts", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[AsmServiceMeshV1ProxyConfig]:
        return typing.cast(typing.Optional[AsmServiceMeshV1ProxyConfig], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[AsmServiceMeshV1ProxyConfig],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0d2d90513ad43da861fdcce5db9dd48202be86f8bdc1b0530ab579a9c5cd59ca)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1TelemetryConfigTracing",
    jsii_struct_bases=[],
    name_mapping={
        "default_providers": "defaultProviders",
        "extension_providers": "extensionProviders",
        "random_sampling_percentage": "randomSamplingPercentage",
    },
)
class AsmServiceMeshV1TelemetryConfigTracing:
    def __init__(
        self,
        *,
        default_providers: typing.Optional[typing.Sequence[builtins.str]] = None,
        extension_providers: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union["AsmServiceMeshV1TelemetryConfigTracingExtensionProviders", typing.Dict[builtins.str, typing.Any]]]]] = None,
        random_sampling_percentage: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param default_providers: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#default_providers AsmServiceMeshV1#default_providers}.
        :param extension_providers: extension_providers block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#extension_providers AsmServiceMeshV1#extension_providers}
        :param random_sampling_percentage: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#random_sampling_percentage AsmServiceMeshV1#random_sampling_percentage}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__48ab8a84680c7278835ad0f35247f8eab5aa7792c3d16f84bc9ee099c24eb4f3)
            check_type(argname="argument default_providers", value=default_providers, expected_type=type_hints["default_providers"])
            check_type(argname="argument extension_providers", value=extension_providers, expected_type=type_hints["extension_providers"])
            check_type(argname="argument random_sampling_percentage", value=random_sampling_percentage, expected_type=type_hints["random_sampling_percentage"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if default_providers is not None:
            self._values["default_providers"] = default_providers
        if extension_providers is not None:
            self._values["extension_providers"] = extension_providers
        if random_sampling_percentage is not None:
            self._values["random_sampling_percentage"] = random_sampling_percentage

    @builtins.property
    def default_providers(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#default_providers AsmServiceMeshV1#default_providers}.'''
        result = self._values.get("default_providers")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def extension_providers(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["AsmServiceMeshV1TelemetryConfigTracingExtensionProviders"]]]:
        '''extension_providers block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#extension_providers AsmServiceMeshV1#extension_providers}
        '''
        result = self._values.get("extension_providers")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List["AsmServiceMeshV1TelemetryConfigTracingExtensionProviders"]]], result)

    @builtins.property
    def random_sampling_percentage(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#random_sampling_percentage AsmServiceMeshV1#random_sampling_percentage}.'''
        result = self._values.get("random_sampling_percentage")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AsmServiceMeshV1TelemetryConfigTracing(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1TelemetryConfigTracingExtensionProviders",
    jsii_struct_bases=[],
    name_mapping={
        "name": "name",
        "zipkin_service_addr": "zipkinServiceAddr",
        "zipkin_service_port": "zipkinServicePort",
    },
)
class AsmServiceMeshV1TelemetryConfigTracingExtensionProviders:
    def __init__(
        self,
        *,
        name: typing.Optional[builtins.str] = None,
        zipkin_service_addr: typing.Optional[builtins.str] = None,
        zipkin_service_port: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param name: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#name AsmServiceMeshV1#name}.
        :param zipkin_service_addr: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#zipkin_service_addr AsmServiceMeshV1#zipkin_service_addr}.
        :param zipkin_service_port: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#zipkin_service_port AsmServiceMeshV1#zipkin_service_port}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c5c722c858a907652032a95a585db00690aa70ea04aa04714faea190c6da5e38)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument zipkin_service_addr", value=zipkin_service_addr, expected_type=type_hints["zipkin_service_addr"])
            check_type(argname="argument zipkin_service_port", value=zipkin_service_port, expected_type=type_hints["zipkin_service_port"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if name is not None:
            self._values["name"] = name
        if zipkin_service_addr is not None:
            self._values["zipkin_service_addr"] = zipkin_service_addr
        if zipkin_service_port is not None:
            self._values["zipkin_service_port"] = zipkin_service_port

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#name AsmServiceMeshV1#name}.'''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def zipkin_service_addr(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#zipkin_service_addr AsmServiceMeshV1#zipkin_service_addr}.'''
        result = self._values.get("zipkin_service_addr")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def zipkin_service_port(self) -> typing.Optional[jsii.Number]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#zipkin_service_port AsmServiceMeshV1#zipkin_service_port}.'''
        result = self._values.get("zipkin_service_port")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AsmServiceMeshV1TelemetryConfigTracingExtensionProviders(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersList",
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
            type_hints = typing.get_type_hints(_typecheckingstub__a8216109878a67d638d621409dc64f4f91bbbfe75e9880f9ea0e6688972cd501)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> "AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersOutputReference":
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5748984c47f1410f923d2796a3e6b65fb14cddccff1ddf8d092df00b75d02f57)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast("AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersOutputReference", jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b83256aa24daf5fdf32cb1e6768c56c66b0532f06432bb5d09dad4b5d8f5357e)
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
            type_hints = typing.get_type_hints(_typecheckingstub__1e8ba4b3adb9a862ef98d752f3ed84fef3e06c906b5c7f3271b84fc924f13a29)
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
            type_hints = typing.get_type_hints(_typecheckingstub__aaefe565c84963461af34db85971955bb878a033749e757994548898eaf1c660)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c9633f1c958ab69606a3709a970998672711aa7b58a78f17ecd395d70e06f9f9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__a45dd98a40e08bb2cb05215713a76b611379c792ec329084b6f15fcbd92a5220)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetName")
    def reset_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetName", []))

    @jsii.member(jsii_name="resetZipkinServiceAddr")
    def reset_zipkin_service_addr(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetZipkinServiceAddr", []))

    @jsii.member(jsii_name="resetZipkinServicePort")
    def reset_zipkin_service_port(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetZipkinServicePort", []))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="zipkinServiceAddrInput")
    def zipkin_service_addr_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "zipkinServiceAddrInput"))

    @builtins.property
    @jsii.member(jsii_name="zipkinServicePortInput")
    def zipkin_service_port_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "zipkinServicePortInput"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5ecccc10c331537d18ec5960f4697ef1d629b89b1aa3f59f9c1a18fb30a3c001)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="zipkinServiceAddr")
    def zipkin_service_addr(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "zipkinServiceAddr"))

    @zipkin_service_addr.setter
    def zipkin_service_addr(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9888c25dbec40ae8f111f504ab7de54fcf1668fa5a22830fc200d899bea73dbd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "zipkinServiceAddr", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="zipkinServicePort")
    def zipkin_service_port(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "zipkinServicePort"))

    @zipkin_service_port.setter
    def zipkin_service_port(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c2454c9c7764cb61ddc8ef48bbbfee775ff5551e8d67df27e1e4588b4c164e99)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "zipkinServicePort", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e40971971f5cae66e12e48e572da64c805687731476f9e2efca45a3645fea7d0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class AsmServiceMeshV1TelemetryConfigTracingOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1TelemetryConfigTracingOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__d1c526913e33c07f49b4e4989608ba22db57c6a05d8a558b59a9dbb2550ff1b6)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="putExtensionProviders")
    def put_extension_providers(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[AsmServiceMeshV1TelemetryConfigTracingExtensionProviders, typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__59518f7ac4c8a5f5b876a1d1aa00d4621882e1c84f51e5c4128124c15cd85626)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putExtensionProviders", [value]))

    @jsii.member(jsii_name="resetDefaultProviders")
    def reset_default_providers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDefaultProviders", []))

    @jsii.member(jsii_name="resetExtensionProviders")
    def reset_extension_providers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetExtensionProviders", []))

    @jsii.member(jsii_name="resetRandomSamplingPercentage")
    def reset_random_sampling_percentage(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRandomSamplingPercentage", []))

    @builtins.property
    @jsii.member(jsii_name="extensionProviders")
    def extension_providers(
        self,
    ) -> AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersList:
        return typing.cast(AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersList, jsii.get(self, "extensionProviders"))

    @builtins.property
    @jsii.member(jsii_name="defaultProvidersInput")
    def default_providers_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "defaultProvidersInput"))

    @builtins.property
    @jsii.member(jsii_name="extensionProvidersInput")
    def extension_providers_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]]], jsii.get(self, "extensionProvidersInput"))

    @builtins.property
    @jsii.member(jsii_name="randomSamplingPercentageInput")
    def random_sampling_percentage_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "randomSamplingPercentageInput"))

    @builtins.property
    @jsii.member(jsii_name="defaultProviders")
    def default_providers(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "defaultProviders"))

    @default_providers.setter
    def default_providers(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cbb74a1f3e953dd240a3d3553868358df7875f8dd42b8641b40f9b920600983a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "defaultProviders", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="randomSamplingPercentage")
    def random_sampling_percentage(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "randomSamplingPercentage"))

    @random_sampling_percentage.setter
    def random_sampling_percentage(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d346650165dd76bedcbe9b5823a776f126a812957a52e474fe05df6be59baef0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "randomSamplingPercentage", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[AsmServiceMeshV1TelemetryConfigTracing]:
        return typing.cast(typing.Optional[AsmServiceMeshV1TelemetryConfigTracing], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[AsmServiceMeshV1TelemetryConfigTracing],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b1e1b260e764a8bd08181c0f9ee5227619b4851c53e4144bf9c7455e244ba55b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1Timeouts",
    jsii_struct_bases=[],
    name_mapping={"create": "create", "delete": "delete"},
)
class AsmServiceMeshV1Timeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#create AsmServiceMeshV1#create}.
        :param delete: Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#delete AsmServiceMeshV1#delete}.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__567967ea81a8f489e2b765bf9f87b315790c072563663cfad167b8fe3ed98017)
            check_type(argname="argument create", value=create, expected_type=type_hints["create"])
            check_type(argname="argument delete", value=delete, expected_type=type_hints["delete"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create is not None:
            self._values["create"] = create
        if delete is not None:
            self._values["delete"] = delete

    @builtins.property
    def create(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#create AsmServiceMeshV1#create}.'''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''Docs at Terraform Registry: {@link https://registry.terraform.io/providers/opentelekomcloud/opentelekomcloud/1.36.50/docs/resources/asm_service_mesh_v1#delete AsmServiceMeshV1#delete}.'''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AsmServiceMeshV1Timeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class AsmServiceMeshV1TimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@cdktf/provider-opentelekomcloud.asmServiceMeshV1.AsmServiceMeshV1TimeoutsOutputReference",
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
            type_hints = typing.get_type_hints(_typecheckingstub__b9978f21570b0cdf71be2f5224a18d7c9ba28c615a98b6926c6be84b55991ecf)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCreate")
    def reset_create(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreate", []))

    @jsii.member(jsii_name="resetDelete")
    def reset_delete(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDelete", []))

    @builtins.property
    @jsii.member(jsii_name="createInput")
    def create_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createInput"))

    @builtins.property
    @jsii.member(jsii_name="deleteInput")
    def delete_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "deleteInput"))

    @builtins.property
    @jsii.member(jsii_name="create")
    def create(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "create"))

    @create.setter
    def create(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__473c23585f80d0d86f9844ecb2278a7305c1d22f6c30814eda87e2b95762b441)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eac156e7d74bfa560a6ef7ea0ebdc58adaf970c3f36227120ab0f01ce23def69)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1Timeouts]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1Timeouts]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1Timeouts]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e7c47636cbdb99ef524dc8bfceb7a81d40683db213895ce9a7d180e3975e9e4e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "AsmServiceMeshV1",
    "AsmServiceMeshV1Clusters",
    "AsmServiceMeshV1ClustersList",
    "AsmServiceMeshV1ClustersOutputReference",
    "AsmServiceMeshV1Config",
    "AsmServiceMeshV1ProxyConfig",
    "AsmServiceMeshV1ProxyConfigOutputReference",
    "AsmServiceMeshV1TelemetryConfigTracing",
    "AsmServiceMeshV1TelemetryConfigTracingExtensionProviders",
    "AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersList",
    "AsmServiceMeshV1TelemetryConfigTracingExtensionProvidersOutputReference",
    "AsmServiceMeshV1TelemetryConfigTracingOutputReference",
    "AsmServiceMeshV1Timeouts",
    "AsmServiceMeshV1TimeoutsOutputReference",
]

publication.publish()

def _typecheckingstub__c58ddf9929244d7fb704b993ec6a6547166281f4f4c496f38b91ca3d30cde986(
    scope: _constructs_77d1e7e8.Construct,
    id_: builtins.str,
    *,
    clusters: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[AsmServiceMeshV1Clusters, typing.Dict[builtins.str, typing.Any]]]],
    name: builtins.str,
    type: builtins.str,
    version: builtins.str,
    id: typing.Optional[builtins.str] = None,
    ipv6_enable: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    proxy_config: typing.Optional[typing.Union[AsmServiceMeshV1ProxyConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    telemetry_config_tracing: typing.Optional[typing.Union[AsmServiceMeshV1TelemetryConfigTracing, typing.Dict[builtins.str, typing.Any]]] = None,
    timeouts: typing.Optional[typing.Union[AsmServiceMeshV1Timeouts, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__79bd83bb6056ece168f7b9695d7f951e485e345026cace95ff779bdebe7c74d3(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ff1501ca883f5f54b3f798a3197b98e9dc4a6e8046e87c18c7f87c1e769a80e2(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[AsmServiceMeshV1Clusters, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6ca4f0ad254c42ff7dd5d76edeb818f118a47e52764e6dbe4265e2efda06f248(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d9a1bfebf0352eb6b9069863eda5095e19e1c2c6a95d6b1960797184a14103ff(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__146e4cb60ac5527a2dff5eb6b866b8581aa7f9f6f94de8be0b41bbac56b431ef(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d5bde1080a4ae541525460ffcab554b68ccfc44813af706a4f243cf3e970f0a1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b9ac320cf46d259cb98c15b9bac8e7aa24f014ddeaacee6c25b34773342693cd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8975e641ddf1ae1a29b77aa6b1d7a6a69c12c86a94f32f75a2b72ddeee931e26(
    *,
    cluster_id: builtins.str,
    installation_nodes: typing.Sequence[builtins.str],
    injection_namespaces: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__92ddce252053460aaab691a9b89013ae6235661fafadad37f55ef160c1ce10b3(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f80ff232a64c118c76dd479be9b95b8ea84efa9d7c17e59cc89868233539d853(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6dc787099603dbf4bc5b9abb6a8ee0070ce3665696c2043591bd67394eadcedb(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9d227ea132e53bdcc61ac3f3152c3a1e84d3d60e7ef86074cdee8ab54ef6a19a(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9684f879e6f5b13664226fe5a8ffb1dc7c4beb868c9883d0f2882fac096f8f5a(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2e9a7a874000a093df157261553f21cb36afde6f6346ec3f2048555886bd6a78(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1Clusters]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__94231ed6fafa0c9c10366501bd22fff7bfe47e06bb88037b441431120ff1de5f(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ec888d0b23ad1390616577285f480f8a0aa1f8ed459a3518852218b9b6b74801(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__57274a32fb8c87440ee168c539486b74e27a9d5c5f1b31d5af1dfad6dd7daf7d(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cf096c3adda329c861bf603304e0ce4252e1abbb2b0f01a3b947c9fb740034de(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0c29eea85f6a5dffe3f5e64d1483bb32ddf0c4fbaa42b8b6e3dfcfaa679cd276(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1Clusters]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c65309e1289cac320034f746760e7b1056589049ad31e42d15253f3fecd75bd7(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    clusters: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[AsmServiceMeshV1Clusters, typing.Dict[builtins.str, typing.Any]]]],
    name: builtins.str,
    type: builtins.str,
    version: builtins.str,
    id: typing.Optional[builtins.str] = None,
    ipv6_enable: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    proxy_config: typing.Optional[typing.Union[AsmServiceMeshV1ProxyConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    telemetry_config_tracing: typing.Optional[typing.Union[AsmServiceMeshV1TelemetryConfigTracing, typing.Dict[builtins.str, typing.Any]]] = None,
    timeouts: typing.Optional[typing.Union[AsmServiceMeshV1Timeouts, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3ba3f28b4f9e932e50e65159f54696f7e3269996784aace1b1aa46f41ca3a0ca(
    *,
    exclude_inbound_ports: typing.Optional[builtins.str] = None,
    exclude_ip_ranges: typing.Optional[builtins.str] = None,
    exclude_outbound_ports: typing.Optional[builtins.str] = None,
    include_inbound_ports: typing.Optional[builtins.str] = None,
    include_ip_ranges: typing.Optional[builtins.str] = None,
    include_outbound_ports: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48d4aa4c973f1c042307c21437f4274959928e3f368ccbdfa8beb3805e29f4c9(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__04cb12ae207ad04b37e0279946cf4cb85c85747af293d787b6d572b7e2e0ebd2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6a3e925bc8f45945142f8c9bf67993c038b1e05d4280cb4860e8a47559652dd4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__89b0f1a21efc8130e02db54f1064cfc382b785036e6be22d9dd450effbdcb36b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8367a5c724fb8784fdaf0bb36067dfef3ed1ee8b5001dbbab098538806ce8611(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__22b01b0a5035d0c60c6d47eded0df8ff21989bd883e4b1adfa0596dcc5f8a962(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e5e1312a26bce727ab4bf494c306d517d337b35042f059af84d62038f3412512(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0d2d90513ad43da861fdcce5db9dd48202be86f8bdc1b0530ab579a9c5cd59ca(
    value: typing.Optional[AsmServiceMeshV1ProxyConfig],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48ab8a84680c7278835ad0f35247f8eab5aa7792c3d16f84bc9ee099c24eb4f3(
    *,
    default_providers: typing.Optional[typing.Sequence[builtins.str]] = None,
    extension_providers: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[AsmServiceMeshV1TelemetryConfigTracingExtensionProviders, typing.Dict[builtins.str, typing.Any]]]]] = None,
    random_sampling_percentage: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c5c722c858a907652032a95a585db00690aa70ea04aa04714faea190c6da5e38(
    *,
    name: typing.Optional[builtins.str] = None,
    zipkin_service_addr: typing.Optional[builtins.str] = None,
    zipkin_service_port: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a8216109878a67d638d621409dc64f4f91bbbfe75e9880f9ea0e6688972cd501(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5748984c47f1410f923d2796a3e6b65fb14cddccff1ddf8d092df00b75d02f57(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b83256aa24daf5fdf32cb1e6768c56c66b0532f06432bb5d09dad4b5d8f5357e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e8ba4b3adb9a862ef98d752f3ed84fef3e06c906b5c7f3271b84fc924f13a29(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aaefe565c84963461af34db85971955bb878a033749e757994548898eaf1c660(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c9633f1c958ab69606a3709a970998672711aa7b58a78f17ecd395d70e06f9f9(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a45dd98a40e08bb2cb05215713a76b611379c792ec329084b6f15fcbd92a5220(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5ecccc10c331537d18ec5960f4697ef1d629b89b1aa3f59f9c1a18fb30a3c001(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9888c25dbec40ae8f111f504ab7de54fcf1668fa5a22830fc200d899bea73dbd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c2454c9c7764cb61ddc8ef48bbbfee775ff5551e8d67df27e1e4588b4c164e99(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e40971971f5cae66e12e48e572da64c805687731476f9e2efca45a3645fea7d0(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1TelemetryConfigTracingExtensionProviders]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d1c526913e33c07f49b4e4989608ba22db57c6a05d8a558b59a9dbb2550ff1b6(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__59518f7ac4c8a5f5b876a1d1aa00d4621882e1c84f51e5c4128124c15cd85626(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[AsmServiceMeshV1TelemetryConfigTracingExtensionProviders, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cbb74a1f3e953dd240a3d3553868358df7875f8dd42b8641b40f9b920600983a(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d346650165dd76bedcbe9b5823a776f126a812957a52e474fe05df6be59baef0(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b1e1b260e764a8bd08181c0f9ee5227619b4851c53e4144bf9c7455e244ba55b(
    value: typing.Optional[AsmServiceMeshV1TelemetryConfigTracing],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__567967ea81a8f489e2b765bf9f87b315790c072563663cfad167b8fe3ed98017(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b9978f21570b0cdf71be2f5224a18d7c9ba28c615a98b6926c6be84b55991ecf(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__473c23585f80d0d86f9844ecb2278a7305c1d22f6c30814eda87e2b95762b441(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eac156e7d74bfa560a6ef7ea0ebdc58adaf970c3f36227120ab0f01ce23def69(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e7c47636cbdb99ef524dc8bfceb7a81d40683db213895ce9a7d180e3975e9e4e(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, AsmServiceMeshV1Timeouts]],
) -> None:
    """Type checking stubs"""
    pass
