from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Identifikasjon")


@_attrs_define
class Identifikasjon:
    """Unik identifikasjon av et objekt, ivaretatt av den ansvarlige produsent/forvalter, som kan benyttes av eksterne
    applikasjoner som referanse til objektet.

    NOTE1 Denne eksterne objektidentifikasjonen må ikke forveksles med en tematisk objektidentifikasjon, slik som f.eks
    bygningsnummer.

    NOTE 2 Denne unike identifikatoren vil ikke endres i løpet av objektets levetid.

        Attributes:
            lokal_id (str): lokal identifikator, tildelt av dataleverendør/dataforvalter. Den lokale identifikatoren er unik
                innenfor navnerommet, ingen andre objekter har samme identifikator.

                NOTE: Det er data leverendørens ansvar å sørge for at denne lokale identifikatoren er unik innenfor navnerommet.
            navnerom (str): navnerom som unikt identifiserer datakilden til objektet, starter med to bokstavs kode jfr ISO
                3166. Benytter understreking  ("_") dersom data produsenten ikke er assosiert med bare et land.

                NOTE 1 : Verdien for nanverom vil eies av den dataprodusent som har ansvar for de unike identifikatorene og vil
                registreres i "INSPIRE external  Object Identifier Namespaces Register"

                Eksempel: NO for Norge.
            versjon_id (Union[Unset, str]): identifikasjon av en spesiell versjon av et geografisk objekt (instans),
                maksimum lengde på 25 karakterers. Dersom spesifikasjonen av et geografisk objekt med en identifikasjon
                inkludererer livsløpssyklusinformasjon, benyttes denne versjonId for å skille mellom ulike versjoner av samme
                objekt. versjonId er en unik  identifikasjon av versjonen.

                NOTE Maksimum lengde er valgt for å tillate tidsregistrering i henhold til  ISO 8601, slik som
                "2007-02-12T12:12:12+05:30" som versjonId.
    """

    lokal_id: str
    navnerom: str
    versjon_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lokal_id = self.lokal_id

        navnerom = self.navnerom

        versjon_id = self.versjon_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lokalId": lokal_id,
                "navnerom": navnerom,
            }
        )
        if versjon_id is not UNSET:
            field_dict["versjonId"] = versjon_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        lokal_id = d.pop("lokalId")

        navnerom = d.pop("navnerom")

        versjon_id = d.pop("versjonId", UNSET)

        identifikasjon = cls(
            lokal_id=lokal_id,
            navnerom=navnerom,
            versjon_id=versjon_id,
        )

        identifikasjon.additional_properties = d
        return identifikasjon

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
