import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.identifikasjon import Identifikasjon
    from ..models.vingeboring_data import VingeboringData


T = TypeVar("T", bound="Vingeboring")


@_attrs_define
class Vingeboring:
    """undersøkelse for måling av in situ udrenert skjærfasthet for uforstyrret og omrørt materiale i
    kohesjonsjordarter<engelsk>investigation for measurements of in situ undrained shear strength for undisturbed and
    remoulded material in cohesive soils</engelsk>

        Attributes:
            json_type (Union[Literal['Vingeboring'], Unset]):
            identifikasjon (Union[Unset, Identifikasjon]): Unik identifikasjon av et objekt, ivaretatt av den ansvarlige
                produsent/forvalter, som kan benyttes av eksterne applikasjoner som referanse til objektet.

                NOTE1 Denne eksterne objektidentifikasjonen må ikke forveksles med en tematisk objektidentifikasjon, slik som
                f.eks bygningsnummer.

                NOTE 2 Denne unike identifikatoren vil ikke endres i løpet av objektets levetid.
            fra_borlengde (Union[Unset, float]): lengde målt fra toppen av kurven/linja som beskriver borehullforløpet [m]
                <engelsk>distance measured from the top of  the curve describing the borehole geometry</engelsk>
            til_borlengde (Union[Unset, float]): lengde målt fra toppen av kurven/linja som beskriver borehullforløpet [m]
                <engelsk>distance measured from the top of  the curve describing the borehole geometry</engelsk>
            insitu_test_start_tidspunkt (Union[Unset, datetime.datetime]): tidspunkt for start av in situ
                prøvningen<engelsk>start time for in situ testing</engelsk>
            insitu_test_slutt_tidspunkt (Union[Unset, datetime.datetime]): tidspunkt for stopp av in situ
                prøvningen<engelsk>stop time for in situ testing</engelsk>
            vannstand_i_borehull (Union[Unset, float]): vannstand i borehull etter vingeboring i felt<engelsk>water level in
                a borehole after vane testing</engelsk>
            vinge_diameter (Union[Unset, float]): diameter for vingekors [mm] <engelsk>diameter of the vane<engelsk>
            vinge_hø_yde (Union[Unset, float]): høyde for vingekors [mm] <engelsk>height of the vane</engelsk>
            vinge_identitet (Union[Unset, str]): identifikasjon for anvendt vingeborutstyr<engelsk>identification of applied
                vane test equipment</engelsk>
            vingeboring_observasjon (Union[Unset, list['VingeboringData']]):
    """

    json_type: Union[Literal["Vingeboring"], Unset] = UNSET
    identifikasjon: Union[Unset, "Identifikasjon"] = UNSET
    fra_borlengde: Union[Unset, float] = UNSET
    til_borlengde: Union[Unset, float] = UNSET
    insitu_test_start_tidspunkt: Union[Unset, datetime.datetime] = UNSET
    insitu_test_slutt_tidspunkt: Union[Unset, datetime.datetime] = UNSET
    vannstand_i_borehull: Union[Unset, float] = UNSET
    vinge_diameter: Union[Unset, float] = UNSET
    vinge_hø_yde: Union[Unset, float] = UNSET
    vinge_identitet: Union[Unset, str] = UNSET
    vingeboring_observasjon: Union[Unset, list["VingeboringData"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        json_type = self.json_type

        identifikasjon: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.identifikasjon, Unset):
            identifikasjon = self.identifikasjon.to_dict()

        fra_borlengde = self.fra_borlengde

        til_borlengde = self.til_borlengde

        insitu_test_start_tidspunkt: Union[Unset, str] = UNSET
        if not isinstance(self.insitu_test_start_tidspunkt, Unset):
            insitu_test_start_tidspunkt = self.insitu_test_start_tidspunkt.isoformat()

        insitu_test_slutt_tidspunkt: Union[Unset, str] = UNSET
        if not isinstance(self.insitu_test_slutt_tidspunkt, Unset):
            insitu_test_slutt_tidspunkt = self.insitu_test_slutt_tidspunkt.isoformat()

        vannstand_i_borehull = self.vannstand_i_borehull

        vinge_diameter = self.vinge_diameter

        vinge_hø_yde = self.vinge_hø_yde

        vinge_identitet = self.vinge_identitet

        vingeboring_observasjon: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.vingeboring_observasjon, Unset):
            vingeboring_observasjon = []
            for vingeboring_observasjon_item_data in self.vingeboring_observasjon:
                vingeboring_observasjon_item = vingeboring_observasjon_item_data.to_dict()
                vingeboring_observasjon.append(vingeboring_observasjon_item)

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
        if insitu_test_start_tidspunkt is not UNSET:
            field_dict["insituTestStartTidspunkt"] = insitu_test_start_tidspunkt
        if insitu_test_slutt_tidspunkt is not UNSET:
            field_dict["insituTestSluttTidspunkt"] = insitu_test_slutt_tidspunkt
        if vannstand_i_borehull is not UNSET:
            field_dict["vannstandIBorehull"] = vannstand_i_borehull
        if vinge_diameter is not UNSET:
            field_dict["vingeDiameter"] = vinge_diameter
        if vinge_hø_yde is not UNSET:
            field_dict["vingeHøyde"] = vinge_hø_yde
        if vinge_identitet is not UNSET:
            field_dict["vingeIdentitet"] = vinge_identitet
        if vingeboring_observasjon is not UNSET:
            field_dict["vingeboringObservasjon"] = vingeboring_observasjon

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.identifikasjon import Identifikasjon
        from ..models.vingeboring_data import VingeboringData

        d = dict(src_dict)
        json_type = cast(Union[Literal["Vingeboring"], Unset], d.pop("jsonType", UNSET))
        if json_type != "Vingeboring" and not isinstance(json_type, Unset):
            raise ValueError(f"jsonType must match const 'Vingeboring', got '{json_type}'")

        _identifikasjon = d.pop("identifikasjon", UNSET)
        identifikasjon: Union[Unset, Identifikasjon]
        if isinstance(_identifikasjon, Unset):
            identifikasjon = UNSET
        else:
            identifikasjon = Identifikasjon.from_dict(_identifikasjon)

        fra_borlengde = d.pop("fraBorlengde", UNSET)

        til_borlengde = d.pop("tilBorlengde", UNSET)

        _insitu_test_start_tidspunkt = d.pop("insituTestStartTidspunkt", UNSET)
        insitu_test_start_tidspunkt: Union[Unset, datetime.datetime]
        if isinstance(_insitu_test_start_tidspunkt, Unset):
            insitu_test_start_tidspunkt = UNSET
        else:
            insitu_test_start_tidspunkt = isoparse(_insitu_test_start_tidspunkt)

        _insitu_test_slutt_tidspunkt = d.pop("insituTestSluttTidspunkt", UNSET)
        insitu_test_slutt_tidspunkt: Union[Unset, datetime.datetime]
        if isinstance(_insitu_test_slutt_tidspunkt, Unset):
            insitu_test_slutt_tidspunkt = UNSET
        else:
            insitu_test_slutt_tidspunkt = isoparse(_insitu_test_slutt_tidspunkt)

        vannstand_i_borehull = d.pop("vannstandIBorehull", UNSET)

        vinge_diameter = d.pop("vingeDiameter", UNSET)

        vinge_hø_yde = d.pop("vingeHøyde", UNSET)

        vinge_identitet = d.pop("vingeIdentitet", UNSET)

        vingeboring_observasjon = []
        _vingeboring_observasjon = d.pop("vingeboringObservasjon", UNSET)
        for vingeboring_observasjon_item_data in _vingeboring_observasjon or []:
            vingeboring_observasjon_item = VingeboringData.from_dict(vingeboring_observasjon_item_data)

            vingeboring_observasjon.append(vingeboring_observasjon_item)

        vingeboring = cls(
            json_type=json_type,
            identifikasjon=identifikasjon,
            fra_borlengde=fra_borlengde,
            til_borlengde=til_borlengde,
            insitu_test_start_tidspunkt=insitu_test_start_tidspunkt,
            insitu_test_slutt_tidspunkt=insitu_test_slutt_tidspunkt,
            vannstand_i_borehull=vannstand_i_borehull,
            vinge_diameter=vinge_diameter,
            vinge_hø_yde=vinge_hø_yde,
            vinge_identitet=vinge_identitet,
            vingeboring_observasjon=vingeboring_observasjon,
        )

        vingeboring.additional_properties = d
        return vingeboring

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
