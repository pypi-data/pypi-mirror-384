import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="DissipasjonData")


@_attrs_define
class DissipasjonData:
    """data fra måling av dissipasjon (drenasje) i felt, aktuelt ved utførelse av dissipasjonstest i CPTU<engelsk>data fra
    måling av dissipasjon (drenasje) i felt, aktuelt ved utførelse av dissipasjonstest i CPTU</engelsk>

        Attributes:
            boret_dybde (Union[Unset, float]): nivå for utførelse av dissipasjonstest<engelsk>depth below the terrain
                surface or any other given reference level</engelsk>
            dissipasjons_poretrykk_u1 (Union[Unset, float]): reduksjon av poretrykk i filterposisjon 1 (spiss) som funksjon
                av tid i dissipasjonstest<engelsk>reduction of pore pressure at filter location 1 (tip) as a function of time in
                a dissipation test</engelsk>
            dissipasjons_poretrykk_u2 (Union[Unset, float]): reduksjon av poretrykk i filterposisjon 2 (bak spiss) som
                funksjon av tid i dissipasjonstest<engelsk>reduction of pore pressure at filter location 2 (behind the tip) as a
                function of time in a dissipation test</engelsk>
            dissipasjons_poretrykk_u3 (Union[Unset, float]): reduksjon av poretrykk i filterposisjon 3 (bak friksjonshylse)
                som funksjon av tid i dissipasjonstest<engelsk>reduction of pore pressure at filter location 3 (behind the
                friction sleeve) as a function of time in a dissipation test</engelsk>
            dissipasjons_tidspunkt (Union[Unset, datetime.datetime]): angitt tidspunkt i dissipasjonstest<engelsk>given time
                in a dissipation test</engelsk>
            friksjon (Union[Unset, float]): målt sidefriksjon ved nedpressing av trykksonde (friksjonskraft dividert med
                areal av friksjonshylse)<engelsk>measured sleeve friction during penetration of the probe (friction sleeve force
                divided by area of the friction sleeve)</engelsk>
            observasjon_kode (Union[Unset, str]): observasjonskoder for markering av hendelser i dissipasjonstesten. Kodene
                er (0..*) tallkoder gitt i en tekststreng med mellomrom mellom hver kode hvis mer enn 1. Kodene er beskrevet i
                kodelisten GeotekniskBoreObservasjonskode.
                <engelsk>observation codes for marking of incidents during dissipation. The codes are (0..*) numeric codes given
                in a text string with spaces between each code if more than 1. The codes are described in the code list
                GeotekniskBoreObservasjonskode.</engelsk>
            observasjon_merknad (Union[Unset, str]): merknad til observasjoner i dissipasjonstesten <engelsk>remarks to
                observations made during dissipation</engelsk>
            poretrykk1 (Union[Unset, float]): poretrykk som utvikles i filterposisjon 1 (spiss) ved nedpressing av
                trykksonde <engelsk>pore pressure generated at filter position 1 (tip) during penetration of the probe</engelsk>
            poretrykk2 (Union[Unset, float]): poretrykk som utvikles i filterposisjon 2 (bak spiss) ved nedpressing av
                trykksonde <engelsk>pore pressure generated at filter position 2 (behind the tip) during penetration of the
                probe</engelsk>
            poretrykk3 (Union[Unset, float]): poretrykk som utvikles i filterposisjon 3 (bak friksjonshylse) ved nedpressing
                av trykksonde <engelsk>pore pressure generated at filter position 3 (behind the sleeve) during penetration of
                the probe</engelsk>
            spissmotstand (Union[Unset, float]): målt spissmotstand ved nedpressing av trykksonde (spisskraft dividert med
                tverrsnittsareal av trykksonde)<engelsk>measured cone resistance during penetration of the probe (point load
                divided by cross-sectional area of probe)</engelsk>
    """

    boret_dybde: Union[Unset, float] = UNSET
    dissipasjons_poretrykk_u1: Union[Unset, float] = UNSET
    dissipasjons_poretrykk_u2: Union[Unset, float] = UNSET
    dissipasjons_poretrykk_u3: Union[Unset, float] = UNSET
    dissipasjons_tidspunkt: Union[Unset, datetime.datetime] = UNSET
    friksjon: Union[Unset, float] = UNSET
    observasjon_kode: Union[Unset, str] = UNSET
    observasjon_merknad: Union[Unset, str] = UNSET
    poretrykk1: Union[Unset, float] = UNSET
    poretrykk2: Union[Unset, float] = UNSET
    poretrykk3: Union[Unset, float] = UNSET
    spissmotstand: Union[Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        boret_dybde = self.boret_dybde

        dissipasjons_poretrykk_u1 = self.dissipasjons_poretrykk_u1

        dissipasjons_poretrykk_u2 = self.dissipasjons_poretrykk_u2

        dissipasjons_poretrykk_u3 = self.dissipasjons_poretrykk_u3

        dissipasjons_tidspunkt: Union[Unset, str] = UNSET
        if not isinstance(self.dissipasjons_tidspunkt, Unset):
            dissipasjons_tidspunkt = self.dissipasjons_tidspunkt.isoformat()

        friksjon = self.friksjon

        observasjon_kode = self.observasjon_kode

        observasjon_merknad = self.observasjon_merknad

        poretrykk1 = self.poretrykk1

        poretrykk2 = self.poretrykk2

        poretrykk3 = self.poretrykk3

        spissmotstand = self.spissmotstand

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if boret_dybde is not UNSET:
            field_dict["boretDybde"] = boret_dybde
        if dissipasjons_poretrykk_u1 is not UNSET:
            field_dict["dissipasjonsPoretrykkU1"] = dissipasjons_poretrykk_u1
        if dissipasjons_poretrykk_u2 is not UNSET:
            field_dict["dissipasjonsPoretrykkU2"] = dissipasjons_poretrykk_u2
        if dissipasjons_poretrykk_u3 is not UNSET:
            field_dict["dissipasjonsPoretrykkU3"] = dissipasjons_poretrykk_u3
        if dissipasjons_tidspunkt is not UNSET:
            field_dict["dissipasjonsTidspunkt"] = dissipasjons_tidspunkt
        if friksjon is not UNSET:
            field_dict["friksjon"] = friksjon
        if observasjon_kode is not UNSET:
            field_dict["observasjonKode"] = observasjon_kode
        if observasjon_merknad is not UNSET:
            field_dict["observasjonMerknad"] = observasjon_merknad
        if poretrykk1 is not UNSET:
            field_dict["poretrykk1"] = poretrykk1
        if poretrykk2 is not UNSET:
            field_dict["poretrykk2"] = poretrykk2
        if poretrykk3 is not UNSET:
            field_dict["poretrykk3"] = poretrykk3
        if spissmotstand is not UNSET:
            field_dict["spissmotstand"] = spissmotstand

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        boret_dybde = d.pop("boretDybde", UNSET)

        dissipasjons_poretrykk_u1 = d.pop("dissipasjonsPoretrykkU1", UNSET)

        dissipasjons_poretrykk_u2 = d.pop("dissipasjonsPoretrykkU2", UNSET)

        dissipasjons_poretrykk_u3 = d.pop("dissipasjonsPoretrykkU3", UNSET)

        _dissipasjons_tidspunkt = d.pop("dissipasjonsTidspunkt", UNSET)
        dissipasjons_tidspunkt: Union[Unset, datetime.datetime]
        if isinstance(_dissipasjons_tidspunkt, Unset):
            dissipasjons_tidspunkt = UNSET
        else:
            dissipasjons_tidspunkt = isoparse(_dissipasjons_tidspunkt)

        friksjon = d.pop("friksjon", UNSET)

        observasjon_kode = d.pop("observasjonKode", UNSET)

        observasjon_merknad = d.pop("observasjonMerknad", UNSET)

        poretrykk1 = d.pop("poretrykk1", UNSET)

        poretrykk2 = d.pop("poretrykk2", UNSET)

        poretrykk3 = d.pop("poretrykk3", UNSET)

        spissmotstand = d.pop("spissmotstand", UNSET)

        dissipasjon_data = cls(
            boret_dybde=boret_dybde,
            dissipasjons_poretrykk_u1=dissipasjons_poretrykk_u1,
            dissipasjons_poretrykk_u2=dissipasjons_poretrykk_u2,
            dissipasjons_poretrykk_u3=dissipasjons_poretrykk_u3,
            dissipasjons_tidspunkt=dissipasjons_tidspunkt,
            friksjon=friksjon,
            observasjon_kode=observasjon_kode,
            observasjon_merknad=observasjon_merknad,
            poretrykk1=poretrykk1,
            poretrykk2=poretrykk2,
            poretrykk3=poretrykk3,
            spissmotstand=spissmotstand,
        )

        dissipasjon_data.additional_properties = d
        return dissipasjon_data

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
