import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.borlengde_til_berg import BorlengdeTilBerg
    from ..models.identifikasjon import Identifikasjon
    from ..models.point import Point
    from ..models.posisjonskvalitet_nadag import PosisjonskvalitetNADAG


T = TypeVar("T", bound="GeovitenskapligBorehullUndersoekelse")


@_attrs_define
class GeovitenskapligBorehullUndersoekelse:
    """et enkelt fysisk undersøkelsespunkt som inneholder beskrivelsen av borehullforløpet

    Merknad: Flere undersøkelser kan tilhøre det samme borehullet, men det er undersøkelsen som representerer de enkelte
    sonderinger / boringer.

    <engelsk>a pysical borehole which contain a description of the borehole geometry Note: Several investigations can
    belong to the same borehole, and it is the investigation which contain the geometry along the borehole. </engelsk>

        Attributes:
            datafangstdato (Union[Unset, datetime.datetime]): dato når objektet siste gang ble registrert/observert/målt i
                terrenget

                Merknad: I mange tilfeller er denne forskjellig fra Oppdateringsdato, da registrerte endringer kan bufres i en
                kortere eller lengre periode før disse legges inn i databasen.
                Ved førstegangsregistrering settes Datafangstdato lik førsteDatafangstdato.
            digitaliseringsmålestokk (Union[Unset, int]): kartmålestokk registreringene/ datene er hentet fra/ registrert på

                Eksempel: 1:50 000 = 50000.
            identifikasjon (Union[Unset, Identifikasjon]): Unik identifikasjon av et objekt, ivaretatt av den ansvarlige
                produsent/forvalter, som kan benyttes av eksterne applikasjoner som referanse til objektet.

                NOTE1 Denne eksterne objektidentifikasjonen må ikke forveksles med en tematisk objektidentifikasjon, slik som
                f.eks bygningsnummer.

                NOTE 2 Denne unike identifikatoren vil ikke endres i løpet av objektets levetid.
            kvalitet (Union[Unset, PosisjonskvalitetNADAG]): Posisjonskvalitet slik den brukes i NADAG (Nasjonal Database
                for Grunnundersøkelser).
                (En realisering av den generelle Posisjonskvalitet)
            oppdateringsdato (Union[Unset, datetime.datetime]): dato for siste endring på objektetdataene

                Merknad:
                Oppdateringsdato kan være forskjellig fra Datafangsdato ved at data som er registrert kan bufres en kortere
                eller lengre periode før disse legges inn i datasystemet (databasen).

                -Definition-
                Date and time at which this version of the spatial object was inserted or changed in the spatial data set.
            posisjon (Union[Unset, Point]):
            bore_beskrivelse (Union[Unset, str]): forklaring av hva som er utført og/eller observert i denne undersøkelsen

                <engelsk>
                a general description of actions performed and/or observed in this investigation
                </engelsk>
            borehull_forl_ø_p (Union[Unset, list['Point']]):
            boret_azimuth (Union[Unset, float]): vinkelen mellom en referansevektor i et referanseplan og en annen vektor i
                det samme planet som peker mot noe av interesse [°]

                <engelsk>
                The vector from an observer (origin) to a point of interest is projected perpendicularly onto a reference plane,
                the angle between the projected vector and the reference vector on the reference plane is called the azimuth
                </engelsk>
            boret_helningsgrad (Union[Unset, float]): helning hvor 90 grader er vertikalt, 0 grader er horisontalt [°]

                <engelsk>
                the inclination of the borehole

                Note: 90 degrees represent the vertical inclination and 0 degrees the horizontal
                </engelsk>
            boret_lengde (Union[Unset, float]): total lengde av borehullets forløp, tilsvarer dyp ved vertikal boring [m]

                <engelsk>
                total length of the investigation in the physical borehole, the same as depth in a vertical borehole
                </engelsk>
            boret_lengde_til_berg (Union[Unset, BorlengdeTilBerg]): dybde til fjell som ikke er målt men basert på tolkning

                <engelsk>
                depth to bedrock based on interpretation
                </engelsk>
            dybde_fra_gitt_posisjon (Union[Unset, float]): avstanden fra måleutstyret og ned til det punkt på jordoverflaten
                hvor boring/måling faktisk starter [m]

                Merknad: Borehullundersøkelsens posisjon er vanligvis angitt med x,y,z-koordinat. Disse verdiene representerer
                vanligvis et punkt på jordoverflaten. Dybden fra denne gitte posisjon vil da være 0. Hvis boringen derimot er
                utført fra flåte,  skip eller is, er det viktig at dybdeFraGittPosisjon blir angitt. Denne vil da være avstanden
                fra måleutstyrets senter (0 dybde) og ned til havbunnen, innsjøbunnen eller elvebunnen hvor sonderingen/boringen
                faktisk starter fra).

                <engelsk>
                distance from the drill or measure equipment down to the vertical level where the borehole/measurement actually
                begins

                Note: This is important to specify if the drilling/sounding is performed from e.g. a raft, ship or from ice. The
                depth will then be the depth from the measuring equipments origin (0 depth) and down to where drilling/sounding
                actually begins (on the sea surface, bottom of a lake or river, etc.)

                </engelsk>
            dybde_fra_vannoverflaten (Union[Unset, float]): den lengden hvor sonderingsutstyret befinner seg i vann [m]

                Merknad: Av spesiell interesse hvis boring er utført fra is eller fra flåte/skip.

                <engelsk>
                free water depth at the location of the sounding [m]

                Note: Of special interest if drilling is performed from raft or ice.
                </engelsk>
            lenke_til_tileggsinfo (Union[Unset, str]): lenke til hvor en finner tilleggsinformasjon om
                borehullsundersøkelsen

                Merknad: URL/URI for aktuelt dokument, bilde, video etc.

                <engelsk>
                link to extra information about the borehole investigation
                Note: URL/URI for the particular document, picture, video
                </engelsk>
            opphav (Union[Unset, str]): referanse til opphavsmaterialet, kildematerialet, organisasjons/publiseringskilde

                Merknad:
                Kan også beskrive navn på person og årsak til oppdatering

                <engelsk>
                reference to copyright, source, organization/publication source

                Note: May also include name of person and cause of update

                </engelsk>
            unders_ø_kelse_slutt (Union[Unset, datetime.datetime]): tidspunkt for stopp av undersøkelsen
                <engelsk>
                end time/date for the investigation
                </engelsk>
            unders_ø_kelse_start (Union[Unset, datetime.datetime]): tidspunkt for start av undersøkelsen
                <engelsk>
                start time/date for the investigation
                </engelsk>
            v_æ_rforhold_ved_boring (Union[Unset, str]): beskrivelse av værforhold under utførelsen av borehullundersøkelsen
                <engelsk>
                Weather conditions - general description.
                </engelsk>
    """

    datafangstdato: Union[Unset, datetime.datetime] = UNSET
    digitaliseringsmålestokk: Union[Unset, int] = UNSET
    identifikasjon: Union[Unset, "Identifikasjon"] = UNSET
    kvalitet: Union[Unset, "PosisjonskvalitetNADAG"] = UNSET
    oppdateringsdato: Union[Unset, datetime.datetime] = UNSET
    posisjon: Union[Unset, "Point"] = UNSET
    bore_beskrivelse: Union[Unset, str] = UNSET
    borehull_forl_ø_p: Union[Unset, list["Point"]] = UNSET
    boret_azimuth: Union[Unset, float] = UNSET
    boret_helningsgrad: Union[Unset, float] = UNSET
    boret_lengde: Union[Unset, float] = UNSET
    boret_lengde_til_berg: Union[Unset, "BorlengdeTilBerg"] = UNSET
    dybde_fra_gitt_posisjon: Union[Unset, float] = UNSET
    dybde_fra_vannoverflaten: Union[Unset, float] = UNSET
    lenke_til_tileggsinfo: Union[Unset, str] = UNSET
    opphav: Union[Unset, str] = UNSET
    unders_ø_kelse_slutt: Union[Unset, datetime.datetime] = UNSET
    unders_ø_kelse_start: Union[Unset, datetime.datetime] = UNSET
    v_æ_rforhold_ved_boring: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        datafangstdato: Union[Unset, str] = UNSET
        if not isinstance(self.datafangstdato, Unset):
            datafangstdato = self.datafangstdato.isoformat()

        digitaliseringsmålestokk = self.digitaliseringsmålestokk

        identifikasjon: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.identifikasjon, Unset):
            identifikasjon = self.identifikasjon.to_dict()

        kvalitet: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.kvalitet, Unset):
            kvalitet = self.kvalitet.to_dict()

        oppdateringsdato: Union[Unset, str] = UNSET
        if not isinstance(self.oppdateringsdato, Unset):
            oppdateringsdato = self.oppdateringsdato.isoformat()

        posisjon: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.posisjon, Unset):
            posisjon = self.posisjon.to_dict()

        bore_beskrivelse = self.bore_beskrivelse

        borehull_forl_ø_p: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.borehull_forl_ø_p, Unset):
            borehull_forl_ø_p = []
            for componentsschemas_line_string_item_data in self.borehull_forl_ø_p:
                componentsschemas_line_string_item = componentsschemas_line_string_item_data.to_dict()
                borehull_forl_ø_p.append(componentsschemas_line_string_item)

        boret_azimuth = self.boret_azimuth

        boret_helningsgrad = self.boret_helningsgrad

        boret_lengde = self.boret_lengde

        boret_lengde_til_berg: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.boret_lengde_til_berg, Unset):
            boret_lengde_til_berg = self.boret_lengde_til_berg.to_dict()

        dybde_fra_gitt_posisjon = self.dybde_fra_gitt_posisjon

        dybde_fra_vannoverflaten = self.dybde_fra_vannoverflaten

        lenke_til_tileggsinfo = self.lenke_til_tileggsinfo

        opphav = self.opphav

        unders_ø_kelse_slutt: Union[Unset, str] = UNSET
        if not isinstance(self.unders_ø_kelse_slutt, Unset):
            unders_ø_kelse_slutt = self.unders_ø_kelse_slutt.isoformat()

        unders_ø_kelse_start: Union[Unset, str] = UNSET
        if not isinstance(self.unders_ø_kelse_start, Unset):
            unders_ø_kelse_start = self.unders_ø_kelse_start.isoformat()

        v_æ_rforhold_ved_boring = self.v_æ_rforhold_ved_boring

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if datafangstdato is not UNSET:
            field_dict["datafangstdato"] = datafangstdato
        if digitaliseringsmålestokk is not UNSET:
            field_dict["digitaliseringsmålestokk"] = digitaliseringsmålestokk
        if identifikasjon is not UNSET:
            field_dict["identifikasjon"] = identifikasjon
        if kvalitet is not UNSET:
            field_dict["kvalitet"] = kvalitet
        if oppdateringsdato is not UNSET:
            field_dict["oppdateringsdato"] = oppdateringsdato
        if posisjon is not UNSET:
            field_dict["posisjon"] = posisjon
        if bore_beskrivelse is not UNSET:
            field_dict["boreBeskrivelse"] = bore_beskrivelse
        if borehull_forl_ø_p is not UNSET:
            field_dict["borehullForløp"] = borehull_forl_ø_p
        if boret_azimuth is not UNSET:
            field_dict["boretAzimuth"] = boret_azimuth
        if boret_helningsgrad is not UNSET:
            field_dict["boretHelningsgrad"] = boret_helningsgrad
        if boret_lengde is not UNSET:
            field_dict["boretLengde"] = boret_lengde
        if boret_lengde_til_berg is not UNSET:
            field_dict["boretLengdeTilBerg"] = boret_lengde_til_berg
        if dybde_fra_gitt_posisjon is not UNSET:
            field_dict["dybdeFraGittPosisjon"] = dybde_fra_gitt_posisjon
        if dybde_fra_vannoverflaten is not UNSET:
            field_dict["dybdeFraVannoverflaten"] = dybde_fra_vannoverflaten
        if lenke_til_tileggsinfo is not UNSET:
            field_dict["lenkeTilTileggsinfo"] = lenke_til_tileggsinfo
        if opphav is not UNSET:
            field_dict["opphav"] = opphav
        if unders_ø_kelse_slutt is not UNSET:
            field_dict["undersøkelseSlutt"] = unders_ø_kelse_slutt
        if unders_ø_kelse_start is not UNSET:
            field_dict["undersøkelseStart"] = unders_ø_kelse_start
        if v_æ_rforhold_ved_boring is not UNSET:
            field_dict["værforholdVedBoring"] = v_æ_rforhold_ved_boring

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.borlengde_til_berg import BorlengdeTilBerg
        from ..models.identifikasjon import Identifikasjon
        from ..models.point import Point
        from ..models.posisjonskvalitet_nadag import PosisjonskvalitetNADAG

        d = dict(src_dict)
        _datafangstdato = d.pop("datafangstdato", UNSET)
        datafangstdato: Union[Unset, datetime.datetime]
        if isinstance(_datafangstdato, Unset):
            datafangstdato = UNSET
        else:
            datafangstdato = isoparse(_datafangstdato)

        digitaliseringsmålestokk = d.pop("digitaliseringsmålestokk", UNSET)

        _identifikasjon = d.pop("identifikasjon", UNSET)
        identifikasjon: Union[Unset, Identifikasjon]
        if isinstance(_identifikasjon, Unset):
            identifikasjon = UNSET
        else:
            identifikasjon = Identifikasjon.from_dict(_identifikasjon)

        _kvalitet = d.pop("kvalitet", UNSET)
        kvalitet: Union[Unset, PosisjonskvalitetNADAG]
        if isinstance(_kvalitet, Unset):
            kvalitet = UNSET
        else:
            kvalitet = PosisjonskvalitetNADAG.from_dict(_kvalitet)

        _oppdateringsdato = d.pop("oppdateringsdato", UNSET)
        oppdateringsdato: Union[Unset, datetime.datetime]
        if isinstance(_oppdateringsdato, Unset):
            oppdateringsdato = UNSET
        else:
            oppdateringsdato = isoparse(_oppdateringsdato)

        _posisjon = d.pop("posisjon", UNSET)
        posisjon: Union[Unset, Point]
        if isinstance(_posisjon, Unset):
            posisjon = UNSET
        else:
            posisjon = Point.from_dict(_posisjon)

        bore_beskrivelse = d.pop("boreBeskrivelse", UNSET)

        borehull_forl_ø_p = []
        _borehull_forl_ø_p = d.pop("borehullForløp", UNSET)
        for componentsschemas_line_string_item_data in _borehull_forl_ø_p or []:
            componentsschemas_line_string_item = Point.from_dict(componentsschemas_line_string_item_data)

            borehull_forl_ø_p.append(componentsschemas_line_string_item)

        boret_azimuth = d.pop("boretAzimuth", UNSET)

        boret_helningsgrad = d.pop("boretHelningsgrad", UNSET)

        boret_lengde = d.pop("boretLengde", UNSET)

        _boret_lengde_til_berg = d.pop("boretLengdeTilBerg", UNSET)
        boret_lengde_til_berg: Union[Unset, BorlengdeTilBerg]
        if isinstance(_boret_lengde_til_berg, Unset):
            boret_lengde_til_berg = UNSET
        else:
            boret_lengde_til_berg = BorlengdeTilBerg.from_dict(_boret_lengde_til_berg)

        dybde_fra_gitt_posisjon = d.pop("dybdeFraGittPosisjon", UNSET)

        dybde_fra_vannoverflaten = d.pop("dybdeFraVannoverflaten", UNSET)

        lenke_til_tileggsinfo = d.pop("lenkeTilTileggsinfo", UNSET)

        opphav = d.pop("opphav", UNSET)

        _unders_ø_kelse_slutt = d.pop("undersøkelseSlutt", UNSET)
        unders_ø_kelse_slutt: Union[Unset, datetime.datetime]
        if isinstance(_unders_ø_kelse_slutt, Unset):
            unders_ø_kelse_slutt = UNSET
        else:
            unders_ø_kelse_slutt = isoparse(_unders_ø_kelse_slutt)

        _unders_ø_kelse_start = d.pop("undersøkelseStart", UNSET)
        unders_ø_kelse_start: Union[Unset, datetime.datetime]
        if isinstance(_unders_ø_kelse_start, Unset):
            unders_ø_kelse_start = UNSET
        else:
            unders_ø_kelse_start = isoparse(_unders_ø_kelse_start)

        v_æ_rforhold_ved_boring = d.pop("værforholdVedBoring", UNSET)

        geovitenskaplig_borehull_undersoekelse = cls(
            datafangstdato=datafangstdato,
            digitaliseringsmålestokk=digitaliseringsmålestokk,
            identifikasjon=identifikasjon,
            kvalitet=kvalitet,
            oppdateringsdato=oppdateringsdato,
            posisjon=posisjon,
            bore_beskrivelse=bore_beskrivelse,
            borehull_forl_ø_p=borehull_forl_ø_p,
            boret_azimuth=boret_azimuth,
            boret_helningsgrad=boret_helningsgrad,
            boret_lengde=boret_lengde,
            boret_lengde_til_berg=boret_lengde_til_berg,
            dybde_fra_gitt_posisjon=dybde_fra_gitt_posisjon,
            dybde_fra_vannoverflaten=dybde_fra_vannoverflaten,
            lenke_til_tileggsinfo=lenke_til_tileggsinfo,
            opphav=opphav,
            unders_ø_kelse_slutt=unders_ø_kelse_slutt,
            unders_ø_kelse_start=unders_ø_kelse_start,
            v_æ_rforhold_ved_boring=v_æ_rforhold_ved_boring,
        )

        geovitenskaplig_borehull_undersoekelse.additional_properties = d
        return geovitenskaplig_borehull_undersoekelse

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
