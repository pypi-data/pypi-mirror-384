from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TrykksonderingData")


@_attrs_define
class TrykksonderingData:
    """data fra utførelse av trykksondering (med poretrykksmåling) CPT(U)<engelsk>data fra performance of cone penetration
    test (with pore pressure measurements) CPT(U)</engelsk>

        Attributes:
            anvendt_last (Union[Unset, float]): anvendt last på overflaten for nedpressing av trykksonde med stenger [kN]
                <engelsk>applied thrust load on the surface for penetration of the test rods and probe</engelsk>
            boret_dybde (Union[Unset, float]): boret dybde i forhold til terrengoverflaten eller annet angitt referansenivå
                [m] <engelsk>depth below the terrain surface or any other given reference level</engelsk>
            boret_lengde (Union[Unset, float]): lengde langs borehullets forløp, tilsvarer dyp ved vertikal boring [m]
                <engelsk>length along the physical borehole, the same as depth in a vertical borehole</engelsk>
            friksjon (Union[Unset, float]): målt sidefriksjon ved nedpressing av trykksonde (friksjonskraft dividert med
                areal av friksjonshylse) [kPa] <engelsk>measured sleeve friction during penetration of the probe (friction
                sleeve force divided by area of the friction sleeve)</engelsk>
            helning (Union[Unset, float]): vinkelavvik mellom nedpressingsretning for trykksonde og vertikalaksen [°]
                <engelsk>deviation between the penetration axis and the vertical axis</engelsk>
            initielt_poretrykk (Union[Unset, float]): initielt poretrykk ved start av dissipasjonstest i CPTU [kPa]
                <engelsk>initial pore pressure at the start of the dissipation test in CPTU</engelsk>
            resistivitet (Union[Unset, float]): elektrisk motstand når den går gjennom et materiale, måles ved gjennomføring
                av RCPTU-forsøk. Måles i [Ωm] (ohm-meter). <engelsk>electrical resistivity, measured in a RCPTU-test (?m)
                </engelsk>
            korrigert_friksjon (Union[Unset, float]): korrigert sidefriksjon ved nedpressing av trykksonde (friksjonskraft
                dividert med areal av friksjonshylse, korrigert for poretrykkseffekter) [MPa] <engelsk>corrected sleeve friction
                during penetration of the probe (friction sleeve force divided by area of the friction sleeve, corrected for
                pore pressure effects)</engelsk>
            korrigert_nedpressnings_kraft (Union[Unset, float]): korrigert last på overflaten for nedpressing av trykksonde
                med stenger [kPa] <engelsk>corrected load on the surface for penetration of the test rods and probe</engelsk>
            nedpressing_hastighet (Union[Unset, float]): nedpressingsdistanse for trykksonde per tidsenhet (2 cm/sek)
                <engelsk>penetration rate for probe (2 cm/sec)</engelsk>
            nedpressings_kraft (Union[Unset, float]): anvendt last på overflaten for nedpressing av trykksonde med stenger
                <engelsk>applied thrust load on the surface for penetration of the test rods and probe</engelsk>
            nedpressings_tid (Union[Unset, int]): tid for nedpressing av sonden til ønsket eller annen angitt dybde, regnet
                fra forrige dybde [sek]
                <engelsk>time for penetration of the probe to the requested or any other given depth. Referring to the previous
                depth</engelsk>
            observasjon_kode (Union[Unset, str]): observasjonskoder for markering av hendelser i trykksonderingen. Kodene er
                (0..*) tallkoder gitt i en tekststreng med mellomrom mellom hver kode hvis mer enn 1. Kodene er beskrevet i
                kodelisten GeotekniskBoreObservasjonskode.  <engelsk>observation codes for marking of incidents during
                penetration. The codes are (0..*) numeric codes given in a text string with spaces between each code if more
                than 1. The codes are described in the code list GeotekniskBoreObservasjonskode. </engelsk>
            observasjon_merknad (Union[Unset, str]): merknad til observasjoner i trykksonderingen <engelsk>remarks to
                observations made during penetration</engelsk>
            poretrykk (Union[Unset, float]): vanntrykket i porevannet i grunnen, med atmosfæretrykket som referanse [kPa]
                <engelsk>the pressure in the pore water, with the atmospheric pressure as reference</engelsk>
            skj_æ_rb_ø_lge_hastighet (Union[Unset, float]): hastighet til s-bølge [m/s] <engelsk>velocity of
                s-wave</engelsk>
            temperatur (Union[Unset, float]): temperatur i jord og/eller luft ved gjennomføring av trykksonderingen [°C]
                <engelsk>temperature in soil and/or air during the testing</engelsk>
            nedpressing_trykk (Union[Unset, float]): målt spissmotstand ved nedpressing av trykksonde (spisskraft dividert
                med tverrsnittsareal av trykksonde) [MPa] <engelsk>measured cone resistance during penetration of the probe
                (point load divided by cross-sectional area of probe) [MPa].</engelsk>
    """

    anvendt_last: Union[Unset, float] = UNSET
    boret_dybde: Union[Unset, float] = UNSET
    boret_lengde: Union[Unset, float] = UNSET
    friksjon: Union[Unset, float] = UNSET
    helning: Union[Unset, float] = UNSET
    initielt_poretrykk: Union[Unset, float] = UNSET
    resistivitet: Union[Unset, float] = UNSET
    korrigert_friksjon: Union[Unset, float] = UNSET
    korrigert_nedpressnings_kraft: Union[Unset, float] = UNSET
    nedpressing_hastighet: Union[Unset, float] = UNSET
    nedpressings_kraft: Union[Unset, float] = UNSET
    nedpressings_tid: Union[Unset, int] = UNSET
    observasjon_kode: Union[Unset, str] = UNSET
    observasjon_merknad: Union[Unset, str] = UNSET
    poretrykk: Union[Unset, float] = UNSET
    skj_æ_rb_ø_lge_hastighet: Union[Unset, float] = UNSET
    temperatur: Union[Unset, float] = UNSET
    nedpressing_trykk: Union[Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        anvendt_last = self.anvendt_last

        boret_dybde = self.boret_dybde

        boret_lengde = self.boret_lengde

        friksjon = self.friksjon

        helning = self.helning

        initielt_poretrykk = self.initielt_poretrykk

        resistivitet = self.resistivitet

        korrigert_friksjon = self.korrigert_friksjon

        korrigert_nedpressnings_kraft = self.korrigert_nedpressnings_kraft

        nedpressing_hastighet = self.nedpressing_hastighet

        nedpressings_kraft = self.nedpressings_kraft

        nedpressings_tid = self.nedpressings_tid

        observasjon_kode = self.observasjon_kode

        observasjon_merknad = self.observasjon_merknad

        poretrykk = self.poretrykk

        skj_æ_rb_ø_lge_hastighet = self.skj_æ_rb_ø_lge_hastighet

        temperatur = self.temperatur

        nedpressing_trykk = self.nedpressing_trykk

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if anvendt_last is not UNSET:
            field_dict["anvendtLast"] = anvendt_last
        if boret_dybde is not UNSET:
            field_dict["boretDybde"] = boret_dybde
        if boret_lengde is not UNSET:
            field_dict["boretLengde"] = boret_lengde
        if friksjon is not UNSET:
            field_dict["friksjon"] = friksjon
        if helning is not UNSET:
            field_dict["helning"] = helning
        if initielt_poretrykk is not UNSET:
            field_dict["initieltPoretrykk"] = initielt_poretrykk
        if resistivitet is not UNSET:
            field_dict["resistivitet"] = resistivitet
        if korrigert_friksjon is not UNSET:
            field_dict["korrigertFriksjon"] = korrigert_friksjon
        if korrigert_nedpressnings_kraft is not UNSET:
            field_dict["korrigertNedpressningsKraft"] = korrigert_nedpressnings_kraft
        if nedpressing_hastighet is not UNSET:
            field_dict["nedpressingHastighet"] = nedpressing_hastighet
        if nedpressings_kraft is not UNSET:
            field_dict["nedpressingsKraft"] = nedpressings_kraft
        if nedpressings_tid is not UNSET:
            field_dict["nedpressingsTid"] = nedpressings_tid
        if observasjon_kode is not UNSET:
            field_dict["observasjonKode"] = observasjon_kode
        if observasjon_merknad is not UNSET:
            field_dict["observasjonMerknad"] = observasjon_merknad
        if poretrykk is not UNSET:
            field_dict["poretrykk"] = poretrykk
        if skj_æ_rb_ø_lge_hastighet is not UNSET:
            field_dict["skjærbølgeHastighet"] = skj_æ_rb_ø_lge_hastighet
        if temperatur is not UNSET:
            field_dict["temperatur"] = temperatur
        if nedpressing_trykk is not UNSET:
            field_dict["nedpressingTrykk"] = nedpressing_trykk

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        anvendt_last = d.pop("anvendtLast", UNSET)

        boret_dybde = d.pop("boretDybde", UNSET)

        boret_lengde = d.pop("boretLengde", UNSET)

        friksjon = d.pop("friksjon", UNSET)

        helning = d.pop("helning", UNSET)

        initielt_poretrykk = d.pop("initieltPoretrykk", UNSET)

        resistivitet = d.pop("resistivitet", UNSET)

        korrigert_friksjon = d.pop("korrigertFriksjon", UNSET)

        korrigert_nedpressnings_kraft = d.pop("korrigertNedpressningsKraft", UNSET)

        nedpressing_hastighet = d.pop("nedpressingHastighet", UNSET)

        nedpressings_kraft = d.pop("nedpressingsKraft", UNSET)

        nedpressings_tid = d.pop("nedpressingsTid", UNSET)

        observasjon_kode = d.pop("observasjonKode", UNSET)

        observasjon_merknad = d.pop("observasjonMerknad", UNSET)

        poretrykk = d.pop("poretrykk", UNSET)

        skj_æ_rb_ø_lge_hastighet = d.pop("skjærbølgeHastighet", UNSET)

        temperatur = d.pop("temperatur", UNSET)

        nedpressing_trykk = d.pop("nedpressingTrykk", UNSET)

        trykksondering_data = cls(
            anvendt_last=anvendt_last,
            boret_dybde=boret_dybde,
            boret_lengde=boret_lengde,
            friksjon=friksjon,
            helning=helning,
            initielt_poretrykk=initielt_poretrykk,
            resistivitet=resistivitet,
            korrigert_friksjon=korrigert_friksjon,
            korrigert_nedpressnings_kraft=korrigert_nedpressnings_kraft,
            nedpressing_hastighet=nedpressing_hastighet,
            nedpressings_kraft=nedpressings_kraft,
            nedpressings_tid=nedpressings_tid,
            observasjon_kode=observasjon_kode,
            observasjon_merknad=observasjon_merknad,
            poretrykk=poretrykk,
            skj_æ_rb_ø_lge_hastighet=skj_æ_rb_ø_lge_hastighet,
            temperatur=temperatur,
            nedpressing_trykk=nedpressing_trykk,
        )

        trykksondering_data.additional_properties = d
        return trykksondering_data

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
