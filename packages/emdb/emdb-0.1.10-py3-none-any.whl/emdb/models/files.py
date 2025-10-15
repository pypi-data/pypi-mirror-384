from abc import abstractmethod, ABC
from typing import Optional, Dict

import requests
from pydantic import BaseModel, PrivateAttr

from emdb.exceptions import EMDBFileNotFoundError


class BaseFile(BaseModel, ABC):
    """
    Base model for EMDB files.
    """
    filename: str
    format: Optional[str] = None
    size_kbytes: Optional[float] = None

    _emdb_id: Optional[str] = PrivateAttr(default=None)

    _BASE_FTP_URL: str = PrivateAttr("https://ftp.ebi.ac.uk/pub/databases/emdb/structures")
    _BASE_PDB_URL: str = PrivateAttr("https://www.ebi.ac.uk/pdbe/entry-files/download")
    _BASE_FIGURES_URL: str = PrivateAttr("https://www.ebi.ac.uk/emdb/images/entry")

    @property
    @abstractmethod
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    def from_api(cls, data: dict) -> "BaseFile":
        """
        Create an EMDBBaseFile instance from API data.

        :param data: Dictionary containing file data.
        :return: An instance of EMDBBaseFile.
        """
        return cls(
            filename=data.get("file", ""),
            size_kbytes=data.get("size_kbytes", None),
            format= data.get("format", None)
        )

    def download(self, output_path: str):
        """
        Download the file from the source path to the specified output path.

        :param output_path: The local path where the file should be saved.
        """
        # If output_path is a directory, append the filename
        if output_path.endswith('/'):
            output_path += self.filename

        response = requests.get(self.source_path)
        print("Path",self.source_path)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded {self.filename} to {output_path}")
        else:
            raise EMDBFileNotFoundError(self._emdb_id, self.filename)

    def __str__(self):
        return f"<BaseFile filename={self.filename}, size_kbytes={self.size_kbytes}, format={self.format}>"

    def __repr__(self):
        return self.__str__()


class BaseMapFile(BaseFile):
    """
    Base model for EMDB map files.
    """
    symmetry: Optional[Dict] = None
    data_type: str
    dimensions: Dict
    origin: Dict
    spacing: Dict
    cell: Dict
    axis_order: Dict
    statistics: Optional[Dict] = None
    pixel_spacing: Dict
    contour_list: Optional[Dict] = None
    label: Optional[str] = None
    annotation_details: Optional[str] = None
    details: Optional[str] = None

    @property
    @abstractmethod
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    def from_api(cls, data: dict) -> "BaseMapFile":
        """
        Create an EMDBBaseMapFile instance from API data.

        :param data: Dictionary containing map file data.
        :return: An instance of EMDBBaseMapFile.
        """
        return cls(
            filename=data.get("file", ""),
            size_kbytes=data.get("size_kbytes", None),
            format=data.get("format", None),
            symmetry=data.get("symmetry", None),
            data_type=data.get("data_type", ""),
            dimensions=data.get("dimensions", {}),
            origin=data.get("origin", {}),
            spacing=data.get("spacing", {}),
            cell=data.get("cell", {}),
            axis_order=data.get("axis_order", {}),
            statistics=data.get("statistics", None),
            pixel_spacing=data.get("pixel_spacing", {}),
            contour_list=data.get("contour_list", None),
            label=data.get("label", None),
            annotation_details=data.get("annotation_details", None),
            details=data.get("details", None),
        )

    def __str__(self):
        return f"<BaseMapFile filename={self.filename}, size_kbytes={self.size_kbytes}, format={self.format}, data_type={self.data_type}>"


class PrimaryMapFile(BaseMapFile):
    """
    Model for the primary map file in an EMDB entry.
    """
    @property
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        return f"{self._BASE_FTP_URL}/{self._emdb_id}/map/{self.filename}"

    def __str__(self):
        return f"<PrimaryMapFile filename={self.filename}, size_kbytes={self.size_kbytes}, format={self.format}>"


class HalfMapFile(BaseMapFile):
    """
    Model for half map files in an EMDB entry.
    """
    @property
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        return f"{self._BASE_FTP_URL}/{self._emdb_id}/other/{self.filename}"

    def __str__(self):
        return f"<HalfMapFile filename={self.filename}, size_kbytes={self.size_kbytes}, format={self.format}>"


class AdditionalMapFile(BaseMapFile):
    """
    Model for additional map files in an EMDB entry.
    """
    @property
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        return f"{self._BASE_FTP_URL}/{self._emdb_id}/other/{self.filename}"

    def __str__(self):
        return f"<AdditionalMapFile filename={self.filename}, size_kbytes={self.size_kbytes}, format={self.format}>"


# class SliceMapFile(BaseMapFile):
#     """
#     Model for slice map files in an EMDB entry.
#     """
#     @property
#     @abstractmethod
#     def source_path(self) -> str:
#         """
#         Abstract property to get the source path of the file.
#         Must be implemented in subclasses.
#         """
#         return f"{self._BASE_FTP_URL}/other/{self.filename}"
#
#     def __str__(self):
#         return f"<SliceMapFile filename={self.filename}, size_kbytes={self.size_kbytes}, format={self.format}>"


class MaskFile(BaseFile):
    """
    Model for mask files in an EMDB entry.
    """
    details: Optional[str] = None
    map_file: Optional[BaseMapFile] = None

    @property
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        return f"{self._BASE_FTP_URL}/{self._emdb_id}/masks/{self.filename}"

    @classmethod
    def from_api(cls, data: dict) -> "MaskFile":
        """
        Create an EMDBMaskFile instance from API data.

        :param data: Dictionary containing mask file data.
        :return: An instance of EMDBMaskFile.
        """
        return cls(
            filename=data.get("file", ""),
            details=data.get("details", None),
            map_file=BaseMapFile.from_api(data.get("mask_details", {})) if data.get("mask_details") else None,
        )

    def __str__(self):
        return f"<MaskFile filename={self.filename}>"


class FigureFile(BaseFile):
    """
    Model for figure files in an EMDB entry.
    """
    @property
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        return f"{self._BASE_FIGURES_URL}/{self._emdb_id}/{self.filename}"

    def __str__(self):
        return f"<FigureFile filename={self.filename}>"


class ModelCifFile(BaseFile):
    """
    Model for PDB model files in an EMDB entry.
    """
    pdb_id: str

    @property
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        return f"{self._BASE_PDB_URL}/{self.filename}"

    def __str__(self):
        return f"<ModelCifFile pdb_id={self.pdb_id} filename={self.filename}>"


class EMDBMetadataXMLFile(BaseFile):
    """
    Model for XML files in an EMDB entry.
    """
    @property
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        return f"{self._BASE_FTP_URL}/{self._emdb_id}/header/{self.filename}"

    def __str__(self):
        return f"<EMDBMetadataXMLFile filename={self.filename}>"


class EMDBMetadataCIFFile(BaseFile):
    """
    Model for CIF files in an EMDB entry.
    """
    @property
    def source_path(self) -> str:
        """
        Abstract property to get the source path of the file.
        Must be implemented in subclasses.
        """
        return f"{self._BASE_FTP_URL}/{self._emdb_id}/metadata/{self.filename}"

    def __str__(self):
        return f"<EMDBMetadataCIFFile filename={self.filename}>"

