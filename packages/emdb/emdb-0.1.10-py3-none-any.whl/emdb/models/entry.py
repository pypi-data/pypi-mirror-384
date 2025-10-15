from typing import TYPE_CHECKING, Optional, Dict, List, Union

from pydantic import BaseModel, PrivateAttr

from emdb.models.files import PrimaryMapFile, HalfMapFile, AdditionalMapFile, MaskFile, FigureFile, \
    ModelCifFile, EMDBMetadataXMLFile, EMDBMetadataCIFFile

if TYPE_CHECKING:
    from emdb.client import EMDB
    from emdb.models.validation import EMDBValidation
    from emdb.models.annotations import EMDBAnnotations


class EMDBEntry(BaseModel):
    id: str
    method: Optional[str] = None
    resolution: Optional[float] = None
    admin: Dict
    citations: Dict
    related_emdb_ids: List[Dict]
    related_pdb_ids: List[Dict]
    sample: Dict
    structure_determination_list: List[Dict]
    modelling: Optional[List[Dict]] = None
    primary_map: PrimaryMapFile
    metadata_files: List[Union[EMDBMetadataXMLFile, EMDBMetadataCIFFile]] = []
    pdb_models: Optional[List[ModelCifFile]] = []
    half_maps: Optional[List[HalfMapFile]] = []
    additional_maps: Optional[List[AdditionalMapFile]] = []
    masks: Optional[List[MaskFile]] = []
    figure: FigureFile

    _client: Optional["EMDB"] = PrivateAttr(default=None)

    @classmethod
    def from_api(cls, data: dict, client: "EMDB") -> "EMDBEntry":
        """
        Create an EMDBEntry instance from API data.

        :param data: Dictionary containing EMDB entry data.
        :param client: An instance of EMDB client to interact with the API.
        :return: An instance of EMDBEntry.
        """
        emdb_id = data.get("emdb_id")
        numeric_id = emdb_id[4:]
        try:
            method = data['structure_determination_list']['structure_determination'][0]['method']
        except KeyError:
            method = None
        try:
            resolution = data['structure_determination_list']['structure_determination'][0]['image_processing'][0]['final_reconstruction']['resolution']['valueOf_']
        except KeyError:
            resolution = None
        try:
            citations = data['crossreferences']['citation_list']
        except KeyError:
            citations = {}
        try:
            related_emdb_ids = data['crossreferences']['emdb_list']['emdb_reference']
        except KeyError:
            related_emdb_ids = []
        try:
            related_pdb_ids = data['crossreferences']['pdb_list']['pdb_reference']
            pdb_models = []
            for model in related_pdb_ids:
                pdb_id = model["pdb_id"]
                model_file = ModelCifFile(pdb_id=pdb_id, filename=f"{pdb_id}_updated.cif")
                model_file._emdb_id = emdb_id
                pdb_models.append(model_file)
        except KeyError:
            related_pdb_ids = []
            pdb_models = []
        try:
            half_maps = data['interpretation']['half_map_list']['half_map']
        except KeyError:
            half_maps = None
        try:
            additional_maps = data['interpretation']['additional_map_list']['additional_map']
        except KeyError:
            additional_maps = None
        try:
            masks = data['interpretation']['segmentation_list']['segmentation']
        except KeyError:
            masks = None
        try:
            modelling = data['interpretation']['modelling_list']['modelling']
        except KeyError:
            modelling = None

        primary_map = PrimaryMapFile.from_api(data.get("map", {}))
        primary_map._emdb_id = emdb_id
        figure = FigureFile(filename=f"400_{numeric_id}.gif")
        figure._emdb_id = emdb_id

        xml_file = EMDBMetadataXMLFile(filename=f"emd-{numeric_id}-v30.xml")
        xml_file._emdb_id = emdb_id
        cif_file = EMDBMetadataCIFFile(filename=f"emd-{numeric_id}.cif.gz")
        cif_file._emdb_id = emdb_id
        metadata_files = [xml_file, cif_file]

        half_maps_objs = []
        if half_maps:
            for hm in half_maps:
                hm_file = HalfMapFile.from_api(hm)
                hm_file._emdb_id = emdb_id
                half_maps_objs.append(hm_file)

        additional_maps_objs = []
        if additional_maps:
            for am in additional_maps:
                am_file = AdditionalMapFile.from_api(am)
                am_file._emdb_id = emdb_id
                additional_maps_objs.append(am_file)

        masks_obj = []
        if masks:
            for m in masks:
                mask_file = MaskFile.from_api(m)
                mask_file._emdb_id = emdb_id
                masks_obj.append(mask_file)

        obj = cls(
            id=emdb_id,
            method=method,
            resolution=resolution,
            admin=data.get("admin", {}),
            citations=citations,
            related_emdb_ids=related_emdb_ids,
            related_pdb_ids=related_pdb_ids,
            sample=data.get("sample", {}),
            structure_determination_list=data.get("structure_determination_list", {}).get("structure_determination", []),
            modelling=modelling,
            primary_map=primary_map,
            metadata_files=metadata_files,
            pdb_models=pdb_models,
            half_maps=half_maps_objs,
            additional_maps=additional_maps_objs,
            masks=masks_obj,
            figure=figure,
        )
        obj._client = client
        return obj

    def get_validation(self) -> Optional["EMDBValidation"]:
        """
        Retrieve the validation data for this EMDB entry.

        :return: An instance of EMDBValidation if available, otherwise None.
        """
        print("Retrieving validation data for EMDB entry:", self.id)
        print("Client:", self._client)
        if self._client:
            return self._client.get_validation(self.id)
        return None

    def get_annotations(self) -> Optional["EMDBAnnotations"]:
        """
        Retrieve annotations for this EMDB entry.

        :return: An instance of EMDBAnnotations if available, otherwise None.
        """
        print("Retrieving annotations for EMDB entry:", self.id)
        if self._client:
            return self._client.get_annotations(self.id)
        return None

    @property
    def deposited_files(self) -> List[Union[PrimaryMapFile, HalfMapFile, AdditionalMapFile, MaskFile, FigureFile, ModelCifFile]]:
        """
        Retrieve all files associated with this EMDB entry.

        :return: A list of all file objects associated with the EMDB entry.
        """
        files = [self.primary_map, self.figure]
        if self.half_maps:
            files.extend(self.half_maps)
        if self.additional_maps:
            files.extend(self.additional_maps)
        if self.masks:
            files.extend(self.masks)
        if self.pdb_models:
            files.extend(self.pdb_models)
        return files

    def download_all_files(self, directory: str) -> None:
        """
        Download all files associated with this EMDB entry to the specified directory.

        :param directory: The directory where files will be downloaded.
        """
        for file in self.deposited_files:
            print(f"Downloading file: {file.filename}")
            file.download(directory)

    def __str__(self):
        return f"<EMDBEntry id={self.id}, method={self.method}, resolution={self.resolution}>"

    def __repr__(self):
        return self.__str__()
