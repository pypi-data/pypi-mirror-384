from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DilatometerTestData")


@_attrs_define
class DilatometerTestData:
    """en enkel innretning, formet som et flatt blad designet for å trykkes ned i bakken. Merknad: ble utviklet for å
    bestemme modulus for en jordart.
    <engelsk>a simple device, shaped in the form of a flat blade designed to be pushed into the ground Note: It was
    developed to evaluate the soil modulus.</engelsk>

        Attributes:
            boret_dybde (Union[Unset, float]): dybde fra 0 nivå, hvor z verdien til undersøkelsens posisjon er satt til 0.
                Angir hvor dypt det er boret.
                <engelsk>depth from zero level, the z value of investigation start point is 0. drilling depth [m]
                </engelsk>
            observasjon_merknad (Union[Unset, str]): tekst som beskriver observasjonen <engelsk>description of the
                observation</engelsk>
            observasjon_kode (Union[Unset, str]): kode som angir observasjonen. Kodene er (0..*) tallkoder gitt i en
                tekststreng med mellomrom mellom hver kode hvis mer enn 1. Kodene er beskrevet i kodelisten
                GeotekniskBoreObservasjonskode.<engelsk>observation code according to valid codes. The codes are (0..*) numeric
                codes given in a text string with spaces between each code if more than 1. The codes are described in the code
                list GeotekniskBoreObservasjonskode. </engelsk>
            kontakt_trykk_p0 (Union[Unset, float]): gasstrykk når membran ikke lenger har kontakt <engelsk>membrane lift-off
                pressure</engelsk>
            ekspansjon_trykk_p1 (Union[Unset, float]): gasstrykk når senter av membran har flyttet seg 1,1 mm <engelsk>gass
                pressure when membrane has moved 1,1 mm</engelsk>
            horisontal_kraft (Union[Unset, float]): horisontal last<engelsk>horizontal load</engelsk>
            poretrykk (Union[Unset, float]): trykket i porevannet angitt som kraft pr. flateenhet, med atmosfæretrykket som
                nullpunkt

                <engelsk>registered pore pressure [kPa]</engelsk>
    """

    boret_dybde: Union[Unset, float] = UNSET
    observasjon_merknad: Union[Unset, str] = UNSET
    observasjon_kode: Union[Unset, str] = UNSET
    kontakt_trykk_p0: Union[Unset, float] = UNSET
    ekspansjon_trykk_p1: Union[Unset, float] = UNSET
    horisontal_kraft: Union[Unset, float] = UNSET
    poretrykk: Union[Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        boret_dybde = self.boret_dybde

        observasjon_merknad = self.observasjon_merknad

        observasjon_kode = self.observasjon_kode

        kontakt_trykk_p0 = self.kontakt_trykk_p0

        ekspansjon_trykk_p1 = self.ekspansjon_trykk_p1

        horisontal_kraft = self.horisontal_kraft

        poretrykk = self.poretrykk

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if boret_dybde is not UNSET:
            field_dict["boretDybde"] = boret_dybde
        if observasjon_merknad is not UNSET:
            field_dict["observasjonMerknad"] = observasjon_merknad
        if observasjon_kode is not UNSET:
            field_dict["observasjonKode"] = observasjon_kode
        if kontakt_trykk_p0 is not UNSET:
            field_dict["kontaktTrykkP0"] = kontakt_trykk_p0
        if ekspansjon_trykk_p1 is not UNSET:
            field_dict["ekspansjonTrykkP1"] = ekspansjon_trykk_p1
        if horisontal_kraft is not UNSET:
            field_dict["horisontalKraft"] = horisontal_kraft
        if poretrykk is not UNSET:
            field_dict["poretrykk"] = poretrykk

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        boret_dybde = d.pop("boretDybde", UNSET)

        observasjon_merknad = d.pop("observasjonMerknad", UNSET)

        observasjon_kode = d.pop("observasjonKode", UNSET)

        kontakt_trykk_p0 = d.pop("kontaktTrykkP0", UNSET)

        ekspansjon_trykk_p1 = d.pop("ekspansjonTrykkP1", UNSET)

        horisontal_kraft = d.pop("horisontalKraft", UNSET)

        poretrykk = d.pop("poretrykk", UNSET)

        dilatometer_test_data = cls(
            boret_dybde=boret_dybde,
            observasjon_merknad=observasjon_merknad,
            observasjon_kode=observasjon_kode,
            kontakt_trykk_p0=kontakt_trykk_p0,
            ekspansjon_trykk_p1=ekspansjon_trykk_p1,
            horisontal_kraft=horisontal_kraft,
            poretrykk=poretrykk,
        )

        dilatometer_test_data.additional_properties = d
        return dilatometer_test_data

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
