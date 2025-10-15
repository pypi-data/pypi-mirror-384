from typing import Optional, TYPE_CHECKING, Dict, List
from pydantic import BaseModel, PrivateAttr
import re

from emdb.models.plots import PlotDataXY, PlotDataHistogram, PlotFSC, PlotVolumeEstimate

if TYPE_CHECKING:
    from emdb.client import EMDB


class EMDBValidationGeneral(BaseModel):
    """
    Represents general validation information for an EMDB entry.
    """
    volume_estimate: Optional[dict] = None
    model_map_ratio: Optional[dict] = None
    model_volume: Optional[dict] = None
    surface_ratio: Optional[dict] = None
    rawmap_contour_level: Optional[float] = None

    @classmethod
    def from_api(cls, data: Dict = None) -> "EMDBValidationGeneral":
        try:
            rawmap_contour_level = data['rawmap_contour_level']['cl']
        except KeyError:
            rawmap_contour_level = None

        return cls(
            volume_estimate=data.get("volume_estimate", None),
            model_map_ratio=data.get("model_map_ratio", None),
            model_volume=data.get("model_volume", None),
            surface_ratio=data.get("surface_ratio", None),
            rawmap_contour_level=rawmap_contour_level
        )

    def __str__(self):
        return (f"<EMDBValidationGeneral "
                f"volume_estimate={self.volume_estimate}, "
                f"model_map_ratio={self.model_map_ratio}, "
                f"model_volume={self.model_volume}, "
                f"surface_ratio={self.surface_ratio}, "
                f"rawmap_contour_level={self.rawmap_contour_level}>")

    def __repr__(self):
        return self.__str__()


class EMDBModelScore(BaseModel):
    """
    Represents the model score for an EMDB validation entry.
    """
    metric: str
    pdb_id: str
    average_color: str
    average_score: float
    residues: List[Dict]
    chains: Dict
    bar: Dict

    @classmethod
    def from_api(cls, metric, data: Dict) -> "EMDBModelScore":
        score_data = data.get("data", {})

        if metric == "ccc":
            average_color_key = "averagecc_color"
            average_score_key = "averagecc"
            chains_key = "chainccscore"
            bar_key = "ccc_bar"
            residue_key = "residue"
            score_key = "ccscore"
            color_key = "color"
        elif metric == "smoc":
            average_color_key = "averagesmoc_color"
            average_score_key = "averagesmoc"
            chains_key = "chainsmoc"
            bar_key = "smoc_bar"
            residue_key = "residue"
            score_key = "smoc_scores"
            color_key = "color"
        elif metric == "qscore":
            average_color_key = "averageqscore_color"
            average_score_key = "averageqscore"
            chains_key = "chainqscore"
            bar_key = "qscore_bar"
            residue_key = "residue"
            score_key = "qscore"
            color_key = "color"
        else:
            average_color_key = "average_color"
            average_score_key = "average_score"
            chains_key = "chainccscore"
            bar_key = "bar"
            residue_key = "residue"
            score_key = "score"
            color_key = "color"

        residues = score_data.get(residue_key, [])
        scores = score_data.get(score_key, [])
        colors = score_data.get(color_key, {})
        combined_residues = []
        for r, c, s in zip(residues, colors, scores):
            chain_pos, aa = r.split()  # "A:335", "THR"
            chain, pos = chain_pos.split(":")  # "A", "335"
            combined_residues.append({
                'chain': chain,
                'position': int(pos),
                'amino_acid': aa,
                'color': c,
                'score': s
            })

        return cls(
            metric=metric,
            pdb_id=data.get("name", "").split(".")[0],
            average_color=score_data.get(average_color_key, None),
            average_score=score_data.get(average_score_key, None),
            residues=combined_residues,
            chains=score_data.get(chains_key, None),
            bar=score_data.get(bar_key, None),
        )

    @classmethod
    def from_atom_inclusion(cls, atom_inclusion_by_level: Dict, residue_inclusion: Dict) -> "EMDBModelScore":
        """
        Create an EMDBModelScore instance from atom inclusion data.

        :param atom_inclusion_by_level: Dictionary containing atom inclusion data by level.
        :param residue_inclusion: Dictionary containing residue inclusion data.
        :return: An instance of EMDBModelScore.
        """

        cl_key = next(k for k, v in residue_inclusion.items() if isinstance(v, dict))
        score_data = residue_inclusion[cl_key]

        residues = score_data.get("residue", [])
        scores = score_data.get("inclusion", [])
        colors = score_data.get("color", {})
        combined_residues = []
        for r, c, s in zip(residues, colors, scores):
            match = re.match(r"([A-Za-z0-9]+):(\d+)\s*([A-Za-z0-9]+)", r)
            if not match:
                raise ValueError(f"Unexpected residue format: {r}")
            chain, pos, aa = match.groups()
            combined_residues.append({
                'chain': chain,
                'position': int(pos),
                'amino_acid': aa,
                'color': c,
                'score': s
            })

        return cls(
            metric="atom_inclusion",
            pdb_id=atom_inclusion_by_level.get("name", "").split(".")[0],
            average_color=atom_inclusion_by_level.get("average_ai_color", None),
            average_score=atom_inclusion_by_level.get("average_ai_model", None),
            residues=combined_residues,
            chains=atom_inclusion_by_level.get("chainaiscore", None),
            bar=atom_inclusion_by_level.get("ai_bar", None)
        )

    def __str__(self):
        return (f"<EMDBModelScore metric={self.metric}, pdb_id={self.pdb_id}, "
                f"average_color={self.average_color}, average_score={self.average_score}>")

    def __repr__(self):
        return self.__str__()


class EMDBValidationScores(BaseModel):
    """
    Represents the scores for an EMDB validation entry.
    """
    ccc: Optional[List[EMDBModelScore]] = None
    atom_inclusion: Optional[List[EMDBModelScore]] = None
    smoc: Optional[List[EMDBModelScore]] = None
    qscore: Optional[List[EMDBModelScore]] = None

    @classmethod
    def from_api(cls, data: Dict) -> "EMDBValidationScores":
        all_ccc_data = data.get("ccc", {})
        all_smoc_data = data.get("smoc", {})
        all_qscore_data = data.get("qscore", {})
        all_residue_inclusion = data.get("residue_inclusion", {})
        all_atom_inclusion_by_level = data.get("atom_inclusion_by_level", {})
        atom_inclusion = []
        for model_index in all_residue_inclusion.keys():
            if model_index in all_atom_inclusion_by_level:
                atom_inclusion.append(
                    EMDBModelScore.from_atom_inclusion(all_atom_inclusion_by_level[model_index], all_residue_inclusion[model_index])
                )

        return cls(
            ccc=[EMDBModelScore.from_api("ccc", ccc_data) for ccc_data in all_ccc_data.values() if ccc_data and isinstance(ccc_data, dict)],
            atom_inclusion=atom_inclusion,
            smoc=[EMDBModelScore.from_api("smoc", smoc_data) for smoc_data in all_smoc_data.values() if smoc_data and isinstance(smoc_data, dict)],
            qscore=[EMDBModelScore.from_api("qscore", qscore_data) for qscore_data in all_qscore_data.values() if qscore_data and isinstance(qscore_data, dict)],
        )

    def __str__(self):
        return (f"<EMDBValidationScores ccc={self.ccc}, atom_inclusion={self.atom_inclusion}, "
                f"smoc={self.smoc}, qscore={self.qscore}>")

    def __repr__(self):
        return self.__str__()


class EMDBValidationPlots(BaseModel):
    """
    Represents the plots for an EMDB validation entry.
    """
    density_distribution: Optional[PlotDataXY] = None
    rawmap_density_distribution: Optional[PlotDataXY] = None
    rotationally_averaged_power_spectrum: Optional[PlotDataXY] = None
    rawmap_rotationally_averaged_power_spectrum: Optional[PlotDataXY] = None
    volume_estimate: Optional[PlotVolumeEstimate] = None
    masked_local_res_histogram: Optional[PlotDataHistogram] = None
    unmasked_local_res_histogram: Optional[PlotDataHistogram] = None
    fsc: Optional[PlotFSC] = None
    mmfsc: Optional[List[PlotFSC]] = None
    rawmap_mmcif: Optional[List[PlotFSC]] = None
    _recommended_contour_level: Optional[Dict[str, float]] = PrivateAttr(default=None)
    _resolution: Optional[float] = PrivateAttr(default=None)

    @classmethod
    def from_api(cls, data: Dict, rcl: Dict[str, float] = None, res: float = None) -> "EMDBValidationPlots":
        def extract_plot(obj: Optional[Dict], title: str, x_label: str, y_label: str, show_cl: bool = False, show_res: bool = False) -> Optional[PlotDataXY]:
            if obj and "x" in obj and "y" in obj:
                if show_cl:
                    return PlotDataXY(x=obj["x"], y=obj["y"], recommended_contour_level=rcl, title=title, x_label=x_label, y_label=y_label)
                elif show_res:
                    return PlotDataXY(x=obj["x"], y=obj["y"], resolution=res, title=title, x_label=x_label, y_label=y_label)
                return PlotDataXY(x=obj["x"], y=obj["y"], title=title, x_label=x_label, y_label=y_label)
            return None

        def extract_hist(obj: Optional[Dict], title: str, x_label: str, y_label: str) -> Optional[PlotDataHistogram]:
            if obj and "values" in obj and "counts" in obj:
                return PlotDataHistogram(values=obj["values"], counts=obj["counts"], title=title, x_label=x_label, y_label=y_label)
            return None

        def extract_vol_estimate(obj: Optional[Dict], title: str, x_label: str, y_label: str) -> Optional[PlotVolumeEstimate]:
            if obj and "volume" in obj and "level" in obj and "estvolume" in obj:
                return PlotVolumeEstimate(volume=obj["volume"], level=obj["level"], estimated_volume=obj["estvolume"], recommended_contour_level=rcl, title=title, x_label=x_label, y_label=y_label)
            return None

        def extract_fsc(obj: Optional[Dict], graph_type: str = "FSC") -> Optional[PlotFSC]:
            pdb_id = None
            if obj:
                if graph_type == "FSC":
                    title = "FSC"
                    if "relion_fsc" in obj:
                        fsc_data = obj["relion_fsc"]
                    elif "fsc" in obj:
                        fsc_data = obj["fsc"]
                    else:
                        return None
                elif graph_type == "MMFSC":
                    pdb_id = obj.get("name", "").split(".")[0]
                    title = f"MMFSC for {pdb_id}"
                    fsc_data = obj.get("data", {})
                else:
                    return None

                curves = fsc_data.get("curves", {})

                final_obj = PlotFSC(
                    type=graph_type,
                    fsc=curves.get("fsc", []),
                    onebit=curves.get("onebit", []),
                    halfbit=curves.get("halfbit", []),
                    cutoff_0_5=curves.get("0.5", []),
                    cutoff_0_143=curves.get("0.143", []),
                    level=curves.get("level", []),
                    resolution=res,
                    angstrom_resolution=curves.get("angstrom_resolution", None),
                    phaserandomization=curves.get("phaserandomization", None),
                    fsc_masked=curves.get("fsc_masked", None),
                    fsc_corrected=curves.get("fsc_corrected", None),
                    intersections=fsc_data.get("intersections", {}),
                    feature_zones=fsc_data.get("feature_zones", None),
                    title=title,
                    x_label="Spatial Frequency (1/Å)",
                    y_label="Correlation"
                )
                if pdb_id:
                    final_obj.pdb_id = pdb_id

                return final_obj
            return None

        class_obj = cls(
            density_distribution=extract_plot(data.get("density_distribution"), "Density distribution", "Voxel Value", "Number of voxels", show_cl=True),
            rawmap_density_distribution=extract_plot(data.get("rawmap_density_distribution"), "Rawmap Density distribution", "Voxel Value", "Number of voxels", show_cl=True),
            rotationally_averaged_power_spectrum=extract_plot(data.get("rotationally_averaged_power_spectrum"), "RAPS", "Spatial Frequency (1/Å)", "Intensity", show_res=True),
            rawmap_rotationally_averaged_power_spectrum=extract_plot(data.get("rawmap_rotationally_averaged_power_spectrum"), "Rawmap RAPS", "Spatial Frequency (1/Å)", "Intensity", show_res=True),
            volume_estimate=extract_vol_estimate(data.get("volume_estimate"), "Volume Estimate", "Contour Level", "Volume (nm³)"),
            masked_local_res_histogram=extract_hist(data.get("local_res_histogram", {}).get("masked", {}), "Masked Local Resolution Histogram", "Local Resolution (Å)", "Count"),
            unmasked_local_res_histogram=extract_hist(data.get("local_res_histogram", {}).get("unmasked", {}), "Unmasked Local Resolution Histogram", "Local Resolution (Å)", "Count"),
            fsc=extract_fsc(data, "FSC"),
            mmfsc=[extract_fsc(mmfsc_data, "MMFSC") for mmfsc_data in data.get("mmfsc", {}).values() if isinstance(mmfsc_data, dict)],
            rawmap_mmcif=[extract_fsc(rawmap_data, "MMFSC") for rawmap_data in data.get("raw_mmfsc", {}).values() if isinstance(rawmap_data, dict)],
        )
        class_obj._recommended_contour_level = rcl
        class_obj._resolution = res
        return class_obj

    def __str__(self):
        # Return just the class name and booleans showing the attributes that are set
        return (f"<EMDBValidationPlots "
                f"density_distribution={self.density_distribution is not None}, "
                f"rawmap_density_distribution={self.rawmap_density_distribution is not None}, "
                f"rotationally_averaged_power_spectrum={self.rotationally_averaged_power_spectrum is not None}, "
                f"rawmap_rotationally_averaged_power_spectrum={self.rawmap_rotationally_averaged_power_spectrum is not None}, "
                f"masked_local_res_histogram={self.masked_local_res_histogram is not None}, "
                f"unmasked_local_res_histogram={self.unmasked_local_res_histogram is not None}, "
                f"fsc={self.fsc is not None}>"
        )

    def __repr__(self):
        return self.__str__()


class EMDBValidation(BaseModel):
    """
    Represents the validation information for an EMDB entry.
    """
    id: str
    resolution: Optional[float]
    recommended_contour_level: Optional[Dict[str, float]]
    general: EMDBValidationGeneral
    scores: EMDBValidationScores
    plots: EMDBValidationPlots
    _client: Optional["EMDB"] = PrivateAttr(default=None)

    @classmethod
    def from_api(cls, emdb_id: str, data: dict, client: "EMDB") -> "EMDBValidation":
        """
        Create an EMDBValidation instance from API data.

        :param emdb_id: The EMDB ID of the entry to retrieve validation data for.
        :param data: Dictionary containing EMDB validation data.
        :param client: An instance of EMDB client to interact with the API.
        :return: An instance of EMDBValidation.
        """
        data = data[emdb_id[4:]]
        try:
            resolution = data['resolution']['value']
        except KeyError:
            resolution = None
        try:
            recc_contour_level = data['recommended_contour_level']
        except KeyError:
            recc_contour_level = None

        obj = cls(
            id=emdb_id,
            resolution=resolution,
            recommended_contour_level=recc_contour_level,
            general=EMDBValidationGeneral.from_api(data),
            scores=EMDBValidationScores.from_api(data),
            plots=EMDBValidationPlots.from_api(data, rcl=recc_contour_level, res=resolution),
        )
        obj._client = client
        return obj

    def __str__(self):
        return f"<EMDBValidation id={self.id}, resolution={self.resolution}, recommended_contour_level={self.recommended_contour_level}>"

    def __repr__(self):
        return self.__str__()
