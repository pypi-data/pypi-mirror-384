from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeVar
from maleo.enums.environment import Environment, EnvironmentMixin
from maleo.enums.service import (
    ServiceKey,
    SimpleServiceKeyMixin,
    ServiceName,
    SimpleServiceNameMixin,
)


ServiceKeyT = TypeVar("ServiceKeyT", bound=ServiceKey)
ServiceNameT = TypeVar("ServiceNameT", bound=ServiceName)


class MaleoClientConfig(
    SimpleServiceNameMixin[ServiceNameT],
    SimpleServiceKeyMixin[ServiceKeyT],
    EnvironmentMixin[Environment],
    Generic[ServiceKeyT, ServiceNameT],
):
    url: str = Field(..., description="Client's URL")


class MaleoTelemetryClientConfig(
    MaleoClientConfig[Literal[ServiceKey.TELEMETRY], Literal[ServiceName.TELEMETRY]]
):
    key: Annotated[
        Literal[ServiceKey.TELEMETRY],
        Field(ServiceKey.TELEMETRY, description="Client's key"),
    ] = ServiceKey.TELEMETRY
    name: Annotated[
        Literal[ServiceName.TELEMETRY],
        Field(ServiceName.TELEMETRY, description="Client's name"),
    ] = ServiceName.TELEMETRY


class MaleoTelemetryClientConfigMixin(BaseModel):
    telemetry: MaleoTelemetryClientConfig = Field(
        ..., description="MaleoTelemetry client's configuration"
    )


class MaleoMetadataClientConfig(
    MaleoClientConfig[Literal[ServiceKey.METADATA], Literal[ServiceName.METADATA]]
):
    key: Annotated[
        Literal[ServiceKey.METADATA],
        Field(ServiceKey.METADATA, description="Client's key"),
    ] = ServiceKey.METADATA
    name: Annotated[
        Literal[ServiceName.METADATA],
        Field(ServiceName.METADATA, description="Client's name"),
    ] = ServiceName.METADATA


class MaleoMetadataClientConfigMixin(BaseModel):
    metadata: MaleoMetadataClientConfig = Field(
        ..., description="MaleoMetadata client's configuration"
    )


class MaleoIdentityClientConfig(
    MaleoClientConfig[Literal[ServiceKey.IDENTITY], Literal[ServiceName.IDENTITY]]
):
    key: Annotated[
        Literal[ServiceKey.IDENTITY],
        Field(ServiceKey.IDENTITY, description="Client's key"),
    ] = ServiceKey.IDENTITY
    name: Annotated[
        Literal[ServiceName.IDENTITY],
        Field(ServiceName.IDENTITY, description="Client's name"),
    ] = ServiceName.IDENTITY


class MaleoIdentityClientConfigMixin(BaseModel):
    identity: MaleoIdentityClientConfig = Field(
        ..., description="MaleoIdentity client's configuration"
    )


class MaleoAccessClientConfig(
    MaleoClientConfig[Literal[ServiceKey.ACCESS], Literal[ServiceName.ACCESS]]
):
    key: Annotated[
        Literal[ServiceKey.ACCESS], Field(ServiceKey.ACCESS, description="Client's key")
    ] = ServiceKey.ACCESS
    name: Annotated[
        Literal[ServiceName.ACCESS],
        Field(ServiceName.ACCESS, description="Client's name"),
    ] = ServiceName.ACCESS


class MaleoAccessClientConfigMixin(BaseModel):
    access: MaleoAccessClientConfig = Field(
        ..., description="MaleoAccess client's configuration"
    )


class MaleoWorkshopClientConfig(
    MaleoClientConfig[Literal[ServiceKey.WORKSHOP], Literal[ServiceName.WORKSHOP]]
):
    key: Annotated[
        Literal[ServiceKey.WORKSHOP],
        Field(ServiceKey.WORKSHOP, description="Client's key"),
    ] = ServiceKey.WORKSHOP
    name: Annotated[
        Literal[ServiceName.WORKSHOP],
        Field(ServiceName.WORKSHOP, description="Client's name"),
    ] = ServiceName.WORKSHOP


class MaleoWorkshopClientConfigMixin(BaseModel):
    workshop: MaleoWorkshopClientConfig = Field(
        ..., description="MaleoWorkshop client's configuration"
    )


class MaleoResearchClientConfig(
    MaleoClientConfig[Literal[ServiceKey.RESEARCH], Literal[ServiceName.RESEARCH]]
):
    key: Annotated[
        Literal[ServiceKey.RESEARCH],
        Field(ServiceKey.RESEARCH, description="Client's key"),
    ] = ServiceKey.RESEARCH
    name: Annotated[
        Literal[ServiceName.RESEARCH],
        Field(ServiceName.RESEARCH, description="Client's name"),
    ] = ServiceName.RESEARCH


class MaleoResearchClientConfigMixin(BaseModel):
    research: MaleoResearchClientConfig = Field(
        ..., description="MaleoResearch client's configuration"
    )


class MaleoRegistryClientConfig(
    MaleoClientConfig[Literal[ServiceKey.REGISTRY], Literal[ServiceName.REGISTRY]]
):
    key: Annotated[
        Literal[ServiceKey.REGISTRY],
        Field(ServiceKey.REGISTRY, description="Client's key"),
    ] = ServiceKey.REGISTRY
    name: Annotated[
        Literal[ServiceName.REGISTRY],
        Field(ServiceName.REGISTRY, description="Client's name"),
    ] = ServiceName.REGISTRY


class MaleoRegistryClientConfigMixin(BaseModel):
    registry: MaleoRegistryClientConfig = Field(
        ..., description="MaleoRegistry client's configuration"
    )


class MaleoSOAPIEClientConfig(
    MaleoClientConfig[Literal[ServiceKey.SOAPIE], Literal[ServiceName.SOAPIE]]
):
    key: Annotated[
        Literal[ServiceKey.SOAPIE], Field(ServiceKey.SOAPIE, description="Client's key")
    ] = ServiceKey.SOAPIE
    name: Annotated[
        Literal[ServiceName.SOAPIE],
        Field(ServiceName.SOAPIE, description="Client's name"),
    ] = ServiceName.SOAPIE


class MaleoSOAPIEClientConfigMixin(BaseModel):
    soapie: MaleoSOAPIEClientConfig = Field(
        ..., description="MaleoSOAPIE client's configuration"
    )


class MaleoMedixClientConfig(
    MaleoClientConfig[Literal[ServiceKey.MEDIX], Literal[ServiceName.MEDIX]]
):
    key: Annotated[
        Literal[ServiceKey.MEDIX], Field(ServiceKey.MEDIX, description="Client's key")
    ] = ServiceKey.MEDIX
    name: Annotated[
        Literal[ServiceName.MEDIX],
        Field(ServiceName.MEDIX, description="Client's name"),
    ] = ServiceName.MEDIX


class MaleoMedixClientConfigMixin(BaseModel):
    medix: MaleoMedixClientConfig = Field(
        ..., description="MaleoMedix client's configuration"
    )


class MaleoDICOMClientConfig(
    MaleoClientConfig[Literal[ServiceKey.DICOM], Literal[ServiceName.DICOM]]
):
    key: Annotated[
        Literal[ServiceKey.DICOM], Field(ServiceKey.DICOM, description="Client's key")
    ] = ServiceKey.DICOM
    name: Annotated[
        Literal[ServiceName.DICOM],
        Field(ServiceName.DICOM, description="Client's name"),
    ] = ServiceName.DICOM


class MaleoDICOMClientConfigMixin(BaseModel):
    dicom: MaleoDICOMClientConfig = Field(
        ..., description="MaleoDICOM client's configuration"
    )


class MaleoScribeClientConfig(
    MaleoClientConfig[Literal[ServiceKey.SCRIBE], Literal[ServiceName.SCRIBE]]
):
    key: Annotated[
        Literal[ServiceKey.SCRIBE], Field(ServiceKey.SCRIBE, description="Client's key")
    ] = ServiceKey.SCRIBE
    name: Annotated[
        Literal[ServiceName.SCRIBE],
        Field(ServiceName.SCRIBE, description="Client's name"),
    ] = ServiceName.SCRIBE


class MaleoScribeClientConfigMixin(BaseModel):
    scribe: MaleoScribeClientConfig = Field(
        ..., description="MaleoScribe client's configuration"
    )


class MaleoCDSClientConfig(
    MaleoClientConfig[Literal[ServiceKey.CDS], Literal[ServiceName.CDS]]
):
    key: Annotated[
        Literal[ServiceKey.CDS], Field(ServiceKey.CDS, description="Client's key")
    ] = ServiceKey.CDS
    name: Annotated[
        Literal[ServiceName.CDS], Field(ServiceName.CDS, description="Client's name")
    ] = ServiceName.CDS


class MaleoCDSClientConfigMixin(BaseModel):
    cds: MaleoCDSClientConfig = Field(
        ..., description="MaleoCDS client's configuration"
    )


class MaleoImagingClientConfig(
    MaleoClientConfig[Literal[ServiceKey.IMAGING], Literal[ServiceName.IMAGING]]
):
    key: Annotated[
        Literal[ServiceKey.IMAGING],
        Field(ServiceKey.IMAGING, description="Client's key"),
    ] = ServiceKey.IMAGING
    name: Annotated[
        Literal[ServiceName.IMAGING],
        Field(ServiceName.IMAGING, description="Client's name"),
    ] = ServiceName.IMAGING


class MaleoImagingClientConfigMixin(BaseModel):
    imaging: MaleoImagingClientConfig = Field(
        ..., description="MaleoImaging client's configuration"
    )


class MaleoMCUClientConfig(
    MaleoClientConfig[Literal[ServiceKey.MCU], Literal[ServiceName.MCU]]
):
    key: Annotated[
        Literal[ServiceKey.MCU], Field(ServiceKey.MCU, description="Client's key")
    ] = ServiceKey.MCU
    name: Annotated[
        Literal[ServiceName.MCU], Field(ServiceName.MCU, description="Client's name")
    ] = ServiceName.MCU


class MaleoMCUClientConfigMixin(BaseModel):
    mcu: MaleoMCUClientConfig = Field(
        ..., description="MaleoMCU client's configuration"
    )


AnyMaleoClientConfig = (
    MaleoTelemetryClientConfig
    | MaleoMetadataClientConfig
    | MaleoIdentityClientConfig
    | MaleoAccessClientConfig
    | MaleoWorkshopClientConfig
    | MaleoResearchClientConfig
    | MaleoRegistryClientConfig
    | MaleoSOAPIEClientConfig
    | MaleoMedixClientConfig
    | MaleoDICOMClientConfig
    | MaleoScribeClientConfig
    | MaleoCDSClientConfig
    | MaleoImagingClientConfig
    | MaleoMCUClientConfig
)
AnyMaleoClientConfigT = TypeVar("AnyMaleoClientConfigT", bound=AnyMaleoClientConfig)


class MaleoClientsConfig(BaseModel):
    pass


OptMaleoClientsConfig = MaleoClientsConfig | None
MaleoClientsConfigT = TypeVar("MaleoClientsConfigT", bound=OptMaleoClientsConfig)
