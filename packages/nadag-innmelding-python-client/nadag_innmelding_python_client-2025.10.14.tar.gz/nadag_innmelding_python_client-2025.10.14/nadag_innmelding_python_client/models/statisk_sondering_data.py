from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="StatiskSonderingData")


@_attrs_define
class StatiskSonderingData:
    """innsamlede data for utførelse og registrering ved gjennomføring av statisk sondering <engelsk>collected data for
    performance and recordings in static sounding</engelsk>

        Attributes:
            anvendtlast (Union[Unset, float]): anvendt nedpressingskraft registrert på overflaten under sonderingen [kN]
                <engelsk>applied penetration force recorded on the surface during sounding</engelsk>
            boret_lengde (Union[Unset, float]): boret dybde i forhold til terrengoverflaten eller annet angitt referansenivå
                [m] <engelsk>drilled depth related to the terrain surface or any other given reference level</engelsk>
            halve_omdreininger (Union[Unset, float]): antall halve omdreininger av stangsystemet, regnet fra forrige dybde
                <engelsk>number of half turns of the rod system, referring to the previous depth</engelsk>
            med_slag (Union[Unset, bool]): markering av slag på borstrengen under sonderingen<engelsk>marking of strokes on
                the drill rods during sounding</engelsk>
            nedpressing_tid (Union[Unset, int]): tidsangivelse ved nedpressing av stangsystemet, regnet siden forrige dybde
                [sek/m] <engelsk>time record during penetration of the rod system, referring to the previous depth</engelsk>
            nedsynkning_hastighet (Union[Unset, float]): antall slag per enhet synk [m/min] <engelsk>penetration of the rod
                system per unit time (rate of penetration)</engelsk>
            observasjon_kode (Union[Unset, str]): observasjonskoder for markering av hendelser i sonderingen. Kodene er
                (0..*) tallkoder gitt i en tekststreng med mellomrom mellom hver kode hvis mer enn 1. Kodene er beskrevet i
                kodelisten GeotekniskBoreObservasjonskode.
                <engelsk>observation codes for marking of incidents during sounding. The codes are (0..*) numeric codes given in
                a text string with spaces between each code if more than 1. The codes are described in the code list
                GeotekniskBoreObservasjonskode. </engelsk>
            observasjon_merknad (Union[Unset, str]): merknad til observasjoner i sonderingen<engelsk>remarks to observations
                made during sounding</engelsk>
            rotasjon_hastighet (Union[Unset, float]): antall omdreininger av stangsystemet per tidsenhet ved penetrasjon av
                borstrengen [omdr/min] <engelsk>number of turns of the rod system per time unit, during penetration of the drill
                string</engelsk>
            har_rotasjon (Union[Unset, bool]): <engelsk>Gets or sets the has turning, that indicates if rotation is logged
                while penetration of soil.
                @value The has turning.</engelsk>
            side_friksjon (Union[Unset, float]): <engelsk>Gets or sets the sleeve friction, the measured sleeve friction
                during penetration of the probe (friction sleeve force divided by area of the friction sleeve [kPa].</engelsk>
            slag_frekvens (Union[Unset, float]): slagfrekvens ved anvendelse av slag på borstrengen i fjellkontrollmodus,
                angitt ved antall slag per tidsenhet [slag/m]
    """

    anvendtlast: Union[Unset, float] = UNSET
    boret_lengde: Union[Unset, float] = UNSET
    halve_omdreininger: Union[Unset, float] = UNSET
    med_slag: Union[Unset, bool] = UNSET
    nedpressing_tid: Union[Unset, int] = UNSET
    nedsynkning_hastighet: Union[Unset, float] = UNSET
    observasjon_kode: Union[Unset, str] = UNSET
    observasjon_merknad: Union[Unset, str] = UNSET
    rotasjon_hastighet: Union[Unset, float] = UNSET
    har_rotasjon: Union[Unset, bool] = UNSET
    side_friksjon: Union[Unset, float] = UNSET
    slag_frekvens: Union[Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        anvendtlast = self.anvendtlast

        boret_lengde = self.boret_lengde

        halve_omdreininger = self.halve_omdreininger

        med_slag = self.med_slag

        nedpressing_tid = self.nedpressing_tid

        nedsynkning_hastighet = self.nedsynkning_hastighet

        observasjon_kode = self.observasjon_kode

        observasjon_merknad = self.observasjon_merknad

        rotasjon_hastighet = self.rotasjon_hastighet

        har_rotasjon = self.har_rotasjon

        side_friksjon = self.side_friksjon

        slag_frekvens = self.slag_frekvens

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if anvendtlast is not UNSET:
            field_dict["anvendtlast"] = anvendtlast
        if boret_lengde is not UNSET:
            field_dict["boretLengde"] = boret_lengde
        if halve_omdreininger is not UNSET:
            field_dict["halveOmdreininger"] = halve_omdreininger
        if med_slag is not UNSET:
            field_dict["medSlag"] = med_slag
        if nedpressing_tid is not UNSET:
            field_dict["nedpressingTid"] = nedpressing_tid
        if nedsynkning_hastighet is not UNSET:
            field_dict["nedsynkningHastighet"] = nedsynkning_hastighet
        if observasjon_kode is not UNSET:
            field_dict["observasjonKode"] = observasjon_kode
        if observasjon_merknad is not UNSET:
            field_dict["observasjonMerknad"] = observasjon_merknad
        if rotasjon_hastighet is not UNSET:
            field_dict["rotasjonHastighet"] = rotasjon_hastighet
        if har_rotasjon is not UNSET:
            field_dict["harRotasjon"] = har_rotasjon
        if side_friksjon is not UNSET:
            field_dict["sideFriksjon"] = side_friksjon
        if slag_frekvens is not UNSET:
            field_dict["slagFrekvens"] = slag_frekvens

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        anvendtlast = d.pop("anvendtlast", UNSET)

        boret_lengde = d.pop("boretLengde", UNSET)

        halve_omdreininger = d.pop("halveOmdreininger", UNSET)

        med_slag = d.pop("medSlag", UNSET)

        nedpressing_tid = d.pop("nedpressingTid", UNSET)

        nedsynkning_hastighet = d.pop("nedsynkningHastighet", UNSET)

        observasjon_kode = d.pop("observasjonKode", UNSET)

        observasjon_merknad = d.pop("observasjonMerknad", UNSET)

        rotasjon_hastighet = d.pop("rotasjonHastighet", UNSET)

        har_rotasjon = d.pop("harRotasjon", UNSET)

        side_friksjon = d.pop("sideFriksjon", UNSET)

        slag_frekvens = d.pop("slagFrekvens", UNSET)

        statisk_sondering_data = cls(
            anvendtlast=anvendtlast,
            boret_lengde=boret_lengde,
            halve_omdreininger=halve_omdreininger,
            med_slag=med_slag,
            nedpressing_tid=nedpressing_tid,
            nedsynkning_hastighet=nedsynkning_hastighet,
            observasjon_kode=observasjon_kode,
            observasjon_merknad=observasjon_merknad,
            rotasjon_hastighet=rotasjon_hastighet,
            har_rotasjon=har_rotasjon,
            side_friksjon=side_friksjon,
            slag_frekvens=slag_frekvens,
        )

        statisk_sondering_data.additional_properties = d
        return statisk_sondering_data

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
