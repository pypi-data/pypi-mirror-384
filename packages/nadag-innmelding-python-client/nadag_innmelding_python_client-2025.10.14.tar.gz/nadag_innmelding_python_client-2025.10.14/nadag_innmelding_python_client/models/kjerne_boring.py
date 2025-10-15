from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.proevetaking_type import ProevetakingType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.borlengde_til_berg import BorlengdeTilBerg
    from ..models.identifikasjon import Identifikasjon
    from ..models.kjerne_boring_data import KjerneBoringData


T = TypeVar("T", bound="KjerneBoring")


@_attrs_define
class KjerneBoring:
    """kjerneprøve tatt i fast berg/fjell ved kjerneboring. Ofte dype boringer og normalt ikke relevant for geoteknikk.
    Tatt med i denne produktspesifikasjon pga. at data kan finnes sammen med geoteknikkleveranser. Blir eventuelt
    overført til annen database/produktspek senere. <engelsk>core drilling</engelsk>

        Attributes:
            json_type (Union[Literal['KjerneBoring'], Unset]):
            identifikasjon (Union[Unset, Identifikasjon]): Unik identifikasjon av et objekt, ivaretatt av den ansvarlige
                produsent/forvalter, som kan benyttes av eksterne applikasjoner som referanse til objektet.

                NOTE1 Denne eksterne objektidentifikasjonen må ikke forveksles med en tematisk objektidentifikasjon, slik som
                f.eks bygningsnummer.

                NOTE 2 Denne unike identifikatoren vil ikke endres i løpet av objektets levetid.
            fra_borlengde (Union[Unset, float]): lengde målt fra toppen av kurven/linja som beskriver borehullforløpet [m]
                <engelsk>distance measured from the top of  the curve describing the borehole geometry</engelsk>
            til_borlengde (Union[Unset, float]): lengde målt fra toppen av kurven/linja som beskriver borehullforløpet [m]
                <engelsk>distance measured from the top of  the curve describing the borehole geometry</engelsk>
            prøvetype (Union[Unset, ProevetakingType]): inndeling av fysisk prøvemateriale i prøvetype, avhengig av
                prøvetakingsmetode og/eller lagringsmetode for prøvematerialet<engelsk>separation of physical samples in sample
                type classes, depending on sampling method and/or storage method for the sampled material</engelsk>
            densitet_pr_ø_vetaking (Union[Unset, float]): tyngde pr. volumenhet [kN/m3] <engelsk>gravity by unit of space
                (kN/m3)</engelsk>
            milj_ø_teknisk_unders_ø_kelse (Union[Unset, str]): beskrivelse og resultater fra miljøteknisk undersøkelse
                <engelsk>description and results from environmental investigation<engelsk>
            boret_lengde_til_berg (Union[Unset, BorlengdeTilBerg]): dybde til fjell som ikke er målt men basert på tolkning

                <engelsk>
                depth to bedrock based on interpretation
                </engelsk>
            har_data (Union[Unset, list['KjerneBoringData']]):
    """

    json_type: Union[Literal["KjerneBoring"], Unset] = UNSET
    identifikasjon: Union[Unset, "Identifikasjon"] = UNSET
    fra_borlengde: Union[Unset, float] = UNSET
    til_borlengde: Union[Unset, float] = UNSET
    prøvetype: Union[Unset, ProevetakingType] = UNSET
    densitet_pr_ø_vetaking: Union[Unset, float] = UNSET
    milj_ø_teknisk_unders_ø_kelse: Union[Unset, str] = UNSET
    boret_lengde_til_berg: Union[Unset, "BorlengdeTilBerg"] = UNSET
    har_data: Union[Unset, list["KjerneBoringData"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        json_type = self.json_type

        identifikasjon: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.identifikasjon, Unset):
            identifikasjon = self.identifikasjon.to_dict()

        fra_borlengde = self.fra_borlengde

        til_borlengde = self.til_borlengde

        prøvetype: Union[Unset, str] = UNSET
        if not isinstance(self.prøvetype, Unset):
            prøvetype = self.prøvetype.value

        densitet_pr_ø_vetaking = self.densitet_pr_ø_vetaking

        milj_ø_teknisk_unders_ø_kelse = self.milj_ø_teknisk_unders_ø_kelse

        boret_lengde_til_berg: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.boret_lengde_til_berg, Unset):
            boret_lengde_til_berg = self.boret_lengde_til_berg.to_dict()

        har_data: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.har_data, Unset):
            har_data = []
            for har_data_item_data in self.har_data:
                har_data_item = har_data_item_data.to_dict()
                har_data.append(har_data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if json_type is not UNSET:
            field_dict["jsonType"] = json_type
        if identifikasjon is not UNSET:
            field_dict["identifikasjon"] = identifikasjon
        if fra_borlengde is not UNSET:
            field_dict["fraBorlengde"] = fra_borlengde
        if til_borlengde is not UNSET:
            field_dict["tilBorlengde"] = til_borlengde
        if prøvetype is not UNSET:
            field_dict["prøvetype"] = prøvetype
        if densitet_pr_ø_vetaking is not UNSET:
            field_dict["densitetPrøvetaking"] = densitet_pr_ø_vetaking
        if milj_ø_teknisk_unders_ø_kelse is not UNSET:
            field_dict["miljøtekniskUndersøkelse"] = milj_ø_teknisk_unders_ø_kelse
        if boret_lengde_til_berg is not UNSET:
            field_dict["boretLengdeTilBerg"] = boret_lengde_til_berg
        if har_data is not UNSET:
            field_dict["harData"] = har_data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.borlengde_til_berg import BorlengdeTilBerg
        from ..models.identifikasjon import Identifikasjon
        from ..models.kjerne_boring_data import KjerneBoringData

        d = dict(src_dict)
        json_type = cast(Union[Literal["KjerneBoring"], Unset], d.pop("jsonType", UNSET))
        if json_type != "KjerneBoring" and not isinstance(json_type, Unset):
            raise ValueError(f"jsonType must match const 'KjerneBoring', got '{json_type}'")

        _identifikasjon = d.pop("identifikasjon", UNSET)
        identifikasjon: Union[Unset, Identifikasjon]
        if isinstance(_identifikasjon, Unset):
            identifikasjon = UNSET
        else:
            identifikasjon = Identifikasjon.from_dict(_identifikasjon)

        fra_borlengde = d.pop("fraBorlengde", UNSET)

        til_borlengde = d.pop("tilBorlengde", UNSET)

        _prøvetype = d.pop("prøvetype", UNSET)
        prøvetype: Union[Unset, ProevetakingType]
        if isinstance(_prøvetype, Unset):
            prøvetype = UNSET
        else:
            prøvetype = ProevetakingType(_prøvetype)

        densitet_pr_ø_vetaking = d.pop("densitetPrøvetaking", UNSET)

        milj_ø_teknisk_unders_ø_kelse = d.pop("miljøtekniskUndersøkelse", UNSET)

        _boret_lengde_til_berg = d.pop("boretLengdeTilBerg", UNSET)
        boret_lengde_til_berg: Union[Unset, BorlengdeTilBerg]
        if isinstance(_boret_lengde_til_berg, Unset):
            boret_lengde_til_berg = UNSET
        else:
            boret_lengde_til_berg = BorlengdeTilBerg.from_dict(_boret_lengde_til_berg)

        har_data = []
        _har_data = d.pop("harData", UNSET)
        for har_data_item_data in _har_data or []:
            har_data_item = KjerneBoringData.from_dict(har_data_item_data)

            har_data.append(har_data_item)

        kjerne_boring = cls(
            json_type=json_type,
            identifikasjon=identifikasjon,
            fra_borlengde=fra_borlengde,
            til_borlengde=til_borlengde,
            prøvetype=prøvetype,
            densitet_pr_ø_vetaking=densitet_pr_ø_vetaking,
            milj_ø_teknisk_unders_ø_kelse=milj_ø_teknisk_unders_ø_kelse,
            boret_lengde_til_berg=boret_lengde_til_berg,
            har_data=har_data,
        )

        kjerne_boring.additional_properties = d
        return kjerne_boring

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
