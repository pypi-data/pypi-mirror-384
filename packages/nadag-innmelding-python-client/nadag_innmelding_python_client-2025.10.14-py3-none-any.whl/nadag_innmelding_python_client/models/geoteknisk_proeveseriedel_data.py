from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.lag_posisjon import LagPosisjon
from ..types import UNSET, Unset

T = TypeVar("T", bound="GeotekniskProeveseriedelData")


@_attrs_define
class GeotekniskProeveseriedelData:
    """Data som tilhører en geoteknisk prøveseriedel <engelsk>Data for a soil test part </engelsk>

    Attributes:
        lag_posisjon (Union[Unset, LagPosisjon]): kodeliste som brukes for å fortelle i hvilken del av prøvedelen som
            det er gjort undersøkelser
        pr_ø_ve_metode (Union[Unset, str]): metode benyttet for å ta prøven<engelsk>method identifier</engelsk>
        aksiel_deformasjon (Union[Unset, float]): angis i [%] <engelsk> the axial deformation (bruddef) %</engelsk>
        skj_æ_rfasthet_udrenert (Union[Unset, float]): bestemmelse av udrenert skjærfasthet ved enaksial trykkprøving i
            laboratoriet [kPa] <engelsk>the axial shear strength, the undrained shear strength by unconfined compression
            testing (sue) [kPa].</engelsk>
        detaljert_lag_sammensetning (Union[Unset, str]): tekst som beskriver lagsammensetningen <engelsk>the detailed
            layer composition, a text containing a detailed layer composition</engelsk>
        skj_æ_rfasthet_omr_ø_rt (Union[Unset, float]): skjærfasthet for en kohesjonsjordart med fullstendig omrørt
            struktur [kPa] <engelsk>the shear strength for a remoulded test material (suo) [kPa]</engelsk>
        densitet_pr_ø_vetaking (Union[Unset, float]): tyngde pr. volumenhet [kN/m3] <engelsk>gravity by unit of space
            [kN/m3]</engelsk>
        er_omr_ø_rt (Union[Unset, bool]): om prøvserien er omrørt<engelsk>indicating whether a soil test is
            disturbed</engelsk>
        lab_analyse (Union[Unset, bool]): om prøven har blitt analysert på laboratorium
            <engelsk> indicating whether the soil test has been analyzed at laboratory</engelsk>
        flyte_grense (Union[Unset, float]): bestemmelse av flytegrense ved hjelp av støt- eller konusmetode i
            laboratoriet [%] Merknad: Flytegrensen angir det vanninnhold der en omrørt leire går over fra å være flytende
            til å bli plastisk (formbar) <engelsk>determination of liquid limit flytegrense by percussionor fall cone method
            in the laboratory Note:The liquid limit corresponds to a water content where the remoulded material goes from a
            liquid to a plastic state</engelsk>
        gl_ø_de_tap (Union[Unset, float]): angis i [%] <engelsk>the loss on ignition, the loss of mass (% left of
            initial mass) due to heating</engelsk>
        plastitets_grense (Union[Unset, float]): bestemmelse av plastisitetsgrense ved hjelp av utrullingsmetode [%]
            Merknad: Også kalt utrullingsgrense som angir det vanninnhold der en omrørt leire går over fra plastisk
            (formbar) til smuldrende konsistens <engelsk>determination of the plasticity limit by a hand rolling method
            Note: Expresses the water content where a remoulded clay leaves the plastic state and starts to
            crumble</engelsk>
        sensitivitet (Union[Unset, float]): forholdet mellom uforstyrret og omrørt udrenert skjærfasthet for
            kohesjonsjord<engelsk>ratio between undisturbed and remoulded undrained shear strength for cohesive
            soils</engelsk>
        skj_æ_rfasthet_uforstyrret (Union[Unset, float]): skjærfasthet for en kohesjonsjordart med uforstyrret, intakt
            struktur [kPa] <engelsk>shear strength for cohesive soils with an intact, undisturbed structure</engelsk>
        boret_lengde (Union[Unset, float]): boret lengde i forhold til terrengoverflaten eller annet angitt
            referansenivå [m] <engelsk>drilled length related to the terrain surface or any other given reference
            level</engelsk>
        vanninnhold (Union[Unset, float]): undersøkelse for bestemmelse av prøvematerialets vanninnhold ved tørking.
            Angir forholdet mellom masse vann og masse fast stoff [%] <engelsk>determination of the water content of the
            sample by oven drying. Corresponds to the ratio between mass of water and the mass of solid particles</engelsk>
        observasjon_kode (Union[Unset, str]): observasjonskoder for markering av hendelser i sonderingen. Kodene er
            (0..*) tallkoder gitt i en tekststreng med mellomrom mellom hver kode hvis mer enn 1. Kodene er beskrevet i
            kodelisten GeotekniskBoreObservasjonskode.
            <engelsk>observation codes for marking of incidents during sounding. The codes are (0..*) numeric codes given in
            a text string with spaces between each code if more than 1. The codes are described in the code list
            GeotekniskBoreObservasjonskode.</engelsk>
        observasjon_merknad (Union[Unset, str]): merknad til observasjoner i sonderingen<engelsk>remarks to observations
            made during sounding</engelsk>
    """

    lag_posisjon: Union[Unset, LagPosisjon] = UNSET
    pr_ø_ve_metode: Union[Unset, str] = UNSET
    aksiel_deformasjon: Union[Unset, float] = UNSET
    skj_æ_rfasthet_udrenert: Union[Unset, float] = UNSET
    detaljert_lag_sammensetning: Union[Unset, str] = UNSET
    skj_æ_rfasthet_omr_ø_rt: Union[Unset, float] = UNSET
    densitet_pr_ø_vetaking: Union[Unset, float] = UNSET
    er_omr_ø_rt: Union[Unset, bool] = UNSET
    lab_analyse: Union[Unset, bool] = UNSET
    flyte_grense: Union[Unset, float] = UNSET
    gl_ø_de_tap: Union[Unset, float] = UNSET
    plastitets_grense: Union[Unset, float] = UNSET
    sensitivitet: Union[Unset, float] = UNSET
    skj_æ_rfasthet_uforstyrret: Union[Unset, float] = UNSET
    boret_lengde: Union[Unset, float] = UNSET
    vanninnhold: Union[Unset, float] = UNSET
    observasjon_kode: Union[Unset, str] = UNSET
    observasjon_merknad: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lag_posisjon: Union[Unset, str] = UNSET
        if not isinstance(self.lag_posisjon, Unset):
            lag_posisjon = self.lag_posisjon.value

        pr_ø_ve_metode = self.pr_ø_ve_metode

        aksiel_deformasjon = self.aksiel_deformasjon

        skj_æ_rfasthet_udrenert = self.skj_æ_rfasthet_udrenert

        detaljert_lag_sammensetning = self.detaljert_lag_sammensetning

        skj_æ_rfasthet_omr_ø_rt = self.skj_æ_rfasthet_omr_ø_rt

        densitet_pr_ø_vetaking = self.densitet_pr_ø_vetaking

        er_omr_ø_rt = self.er_omr_ø_rt

        lab_analyse = self.lab_analyse

        flyte_grense = self.flyte_grense

        gl_ø_de_tap = self.gl_ø_de_tap

        plastitets_grense = self.plastitets_grense

        sensitivitet = self.sensitivitet

        skj_æ_rfasthet_uforstyrret = self.skj_æ_rfasthet_uforstyrret

        boret_lengde = self.boret_lengde

        vanninnhold = self.vanninnhold

        observasjon_kode = self.observasjon_kode

        observasjon_merknad = self.observasjon_merknad

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if lag_posisjon is not UNSET:
            field_dict["lagPosisjon"] = lag_posisjon
        if pr_ø_ve_metode is not UNSET:
            field_dict["prøveMetode"] = pr_ø_ve_metode
        if aksiel_deformasjon is not UNSET:
            field_dict["aksielDeformasjon"] = aksiel_deformasjon
        if skj_æ_rfasthet_udrenert is not UNSET:
            field_dict["skjærfasthetUdrenert"] = skj_æ_rfasthet_udrenert
        if detaljert_lag_sammensetning is not UNSET:
            field_dict["detaljertLagSammensetning"] = detaljert_lag_sammensetning
        if skj_æ_rfasthet_omr_ø_rt is not UNSET:
            field_dict["skjærfasthetOmrørt"] = skj_æ_rfasthet_omr_ø_rt
        if densitet_pr_ø_vetaking is not UNSET:
            field_dict["densitetPrøvetaking"] = densitet_pr_ø_vetaking
        if er_omr_ø_rt is not UNSET:
            field_dict["erOmrørt"] = er_omr_ø_rt
        if lab_analyse is not UNSET:
            field_dict["labAnalyse"] = lab_analyse
        if flyte_grense is not UNSET:
            field_dict["flyteGrense"] = flyte_grense
        if gl_ø_de_tap is not UNSET:
            field_dict["glødeTap"] = gl_ø_de_tap
        if plastitets_grense is not UNSET:
            field_dict["plastitetsGrense"] = plastitets_grense
        if sensitivitet is not UNSET:
            field_dict["sensitivitet"] = sensitivitet
        if skj_æ_rfasthet_uforstyrret is not UNSET:
            field_dict["skjærfasthetUforstyrret"] = skj_æ_rfasthet_uforstyrret
        if boret_lengde is not UNSET:
            field_dict["boretLengde"] = boret_lengde
        if vanninnhold is not UNSET:
            field_dict["vanninnhold"] = vanninnhold
        if observasjon_kode is not UNSET:
            field_dict["observasjonKode"] = observasjon_kode
        if observasjon_merknad is not UNSET:
            field_dict["observasjonMerknad"] = observasjon_merknad

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _lag_posisjon = d.pop("lagPosisjon", UNSET)
        lag_posisjon: Union[Unset, LagPosisjon]
        if isinstance(_lag_posisjon, Unset):
            lag_posisjon = UNSET
        else:
            lag_posisjon = LagPosisjon(_lag_posisjon)

        pr_ø_ve_metode = d.pop("prøveMetode", UNSET)

        aksiel_deformasjon = d.pop("aksielDeformasjon", UNSET)

        skj_æ_rfasthet_udrenert = d.pop("skjærfasthetUdrenert", UNSET)

        detaljert_lag_sammensetning = d.pop("detaljertLagSammensetning", UNSET)

        skj_æ_rfasthet_omr_ø_rt = d.pop("skjærfasthetOmrørt", UNSET)

        densitet_pr_ø_vetaking = d.pop("densitetPrøvetaking", UNSET)

        er_omr_ø_rt = d.pop("erOmrørt", UNSET)

        lab_analyse = d.pop("labAnalyse", UNSET)

        flyte_grense = d.pop("flyteGrense", UNSET)

        gl_ø_de_tap = d.pop("glødeTap", UNSET)

        plastitets_grense = d.pop("plastitetsGrense", UNSET)

        sensitivitet = d.pop("sensitivitet", UNSET)

        skj_æ_rfasthet_uforstyrret = d.pop("skjærfasthetUforstyrret", UNSET)

        boret_lengde = d.pop("boretLengde", UNSET)

        vanninnhold = d.pop("vanninnhold", UNSET)

        observasjon_kode = d.pop("observasjonKode", UNSET)

        observasjon_merknad = d.pop("observasjonMerknad", UNSET)

        geoteknisk_proeveseriedel_data = cls(
            lag_posisjon=lag_posisjon,
            pr_ø_ve_metode=pr_ø_ve_metode,
            aksiel_deformasjon=aksiel_deformasjon,
            skj_æ_rfasthet_udrenert=skj_æ_rfasthet_udrenert,
            detaljert_lag_sammensetning=detaljert_lag_sammensetning,
            skj_æ_rfasthet_omr_ø_rt=skj_æ_rfasthet_omr_ø_rt,
            densitet_pr_ø_vetaking=densitet_pr_ø_vetaking,
            er_omr_ø_rt=er_omr_ø_rt,
            lab_analyse=lab_analyse,
            flyte_grense=flyte_grense,
            gl_ø_de_tap=gl_ø_de_tap,
            plastitets_grense=plastitets_grense,
            sensitivitet=sensitivitet,
            skj_æ_rfasthet_uforstyrret=skj_æ_rfasthet_uforstyrret,
            boret_lengde=boret_lengde,
            vanninnhold=vanninnhold,
            observasjon_kode=observasjon_kode,
            observasjon_merknad=observasjon_merknad,
        )

        geoteknisk_proeveseriedel_data.additional_properties = d
        return geoteknisk_proeveseriedel_data

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
