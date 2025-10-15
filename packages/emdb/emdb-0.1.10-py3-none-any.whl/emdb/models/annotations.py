from typing import Optional, TYPE_CHECKING, List

from pydantic import BaseModel, PrivateAttr

if TYPE_CHECKING:
    from emdb.client import EMDB


class EMDBBaseAnnotation(BaseModel):
    """
    Base model for EMDB annotations.
    This model is used to represent a generic annotation in EMDB.
    """
    id: str
    sample_id: str
    provenance: str

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "EMDBBaseAnnotation":
        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
        )

    def __repr__(self):
        return self.__str__()


class ComplexPortalAnnotation(EMDBBaseAnnotation):
    title: Optional[str] = None
    score: float

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "ComplexPortalAnnotation":
        """
        Create a ComplexPortalAnnotation instance from API data.

        :param sample_id: The sample ID associated with the annotation.
        :param data: The data returned by the EMDB API.
        :return: An instance of ComplexPortalAnnotation.
        """
        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
            title=data.get("title", None),
            score=data.get("score")
        )

    def __str__(self):
        return (f"<ComplexPortalAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance} "
                f"title={self.title} "
                f"score={self.score}>")


class UniProtAnnotation(EMDBBaseAnnotation):

    def __str__(self):
        return (f"<UniProtAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance}>")


class PfamAnnotation(EMDBBaseAnnotation):
    title: Optional[str] = None
    start: int
    end: int

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "PfamAnnotation":
        """
        Create a PfamAnnotation instance from API data.

        :param sample_id: The sample ID associated with the annotation.
        :param data: The data returned by the EMDB API.
        :return: An instance of PfamAnnotation.
        """
        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
            title=data.get("title", None),
            start=data.get("start"),
            end=data.get("end")
        )

    def __str__(self):
        return (f"<PfamAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance} "
                f"title={self.title} "
                f"start={self.start} "
                f"end={self.end}>")


class InterProAnnotation(EMDBBaseAnnotation):
    title: Optional[str] = None
    start: int
    end: int

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "InterProAnnotation":
        """
        Create an InterProAnnotation instance from API data.

        :param sample_id: The sample ID associated with the annotation.
        :param data: The data returned by the EMDB API.
        :return: An instance of InterProAnnotation.
        """
        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
            title=data.get("title", None),
            start=data.get("start"),
            end=data.get("end")
        )

    def __str__(self):
        return (f"<InterProAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance} "
                f"title={self.title} "
                f"start={self.start} "
                f"end={self.end}>")


class GeneOntologyAnnotation(EMDBBaseAnnotation):
    title: Optional[str] = None
    type: str

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "GeneOntologyAnnotation":
        """
        Create a GeneOntologyAnnotation instance from API data.

        :param sample_id: The sample ID associated with the annotation.
        :param data: The data returned by the EMDB API.
        :return: An instance of GeneOntologyAnnotation.
        """
        type_char = data.get("type", "")
        type_text = ""
        if type_char == "C":
            type_text = "CELLULAR COMPONENT"
        elif type_char == "P":
            type_text = "BIOLOGICAL PROCESS"
        elif type_char == "F":
            type_text = "MOLECULAR FUNCTION"

        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
            title=data.get("title", None),
            type=type_text
        )

    def __str__(self):
        return (f"<GeneOntologyAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance} "
                f"title={self.title} "
                f"type={self.type}>")


class CathAnnotation(EMDBBaseAnnotation):
    start: int
    end: int

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "CathAnnotation":
        """
        Create a CathAnnotation instance from API data.

        :param sample_id: The sample ID associated with the annotation.
        :param data: The data returned by the EMDB API.
        :return: An instance of CathAnnotation.
        """
        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
            start=data.get("start"),
            end=data.get("end")
        )

    def __str__(self):
        return (f"<CathAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance} "
                f"start={self.start} "
                f"end={self.end}>")


class ChEBIAnnotation(EMDBBaseAnnotation):
    title: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "ChEBIAnnotation":
        """
        Create a ChEBIAnnotation instance from API data.

        :param sample_id: The sample ID associated with the annotation.
        :param data: The data returned by the EMDB API.
        :return: An instance of ChEBIAnnotation.
        """
        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
            title=data.get("title", None)
        )

    def __str__(self):
        return (f"<ChEBIAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance} "
                f"title={self.title}>")


class ChEMBLAnnotation(EMDBBaseAnnotation):
    title: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "ChEMBLAnnotation":
        """
        Create a ChEMBLAnnotation instance from API data.

        :param sample_id: The sample ID associated with the annotation.
        :param data: The data returned by the EMDB API.
        :return: An instance of ChEMBLAnnotation.
        """
        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
            title=data.get("title", None)
        )

    def __str__(self):
        return (f"<ChEMBLAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance} "
                f"title={self.title}>")


class DrugBankAnnotation(EMDBBaseAnnotation):
    title: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "DrugBankAnnotation":
        """
        Create a DrugBankAnnotation instance from API data.

        :param sample_id: The sample ID associated with the annotation.
        :param data: The data returned by the EMDB API.
        :return: An instance of DrugBankAnnotation.
        """
        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
            title=data.get("title", None)
        )

    def __str__(self):
        return (f"<DrugBankAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance} "
                f"title={self.title}>")


class PDBeKbAnnotation(EMDBBaseAnnotation):
    def __str__(self):
        return (f"<PDBeKbAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance}>")


class AlphaFoldDBAnnotation(EMDBBaseAnnotation):
    def __str__(self):
        return (f"<AlphaFoldDBAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance}>")


class Scop2Annotation(EMDBBaseAnnotation):
    def __str__(self):
        return (f"<Scop2Annotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance}>")


class ORCIDAnnotation(EMDBBaseAnnotation):
    title: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict, sample_id: str) -> "ORCIDAnnotation":
        """
        Create an ORCIDAnnotation instance from API data.

        :param sample_id: The sample ID associated with the annotation.
        :param data: The data returned by the EMDB API.
        :return: An instance of ORCIDAnnotation.
        """
        return cls(
            id=data.get("id"),
            sample_id=sample_id,
            provenance=data.get("method"),
            title=data.get("title", None)
        )

    def __str__(self):
        return (f"<ORCIDAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance} "
                f"title={self.title}>")


class EMPIARAnnotation(EMDBBaseAnnotation):
    def __str__(self):
        return (f"<EMPIARAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance}>")


class PDBAnnotation(EMDBBaseAnnotation):
    def __str__(self):
        return (f"<PDBAnnotation "
                f"id={self.id} "
                f"sample_id={self.sample_id} "
                f"provenance={self.provenance}>")


class EMDBSupramoleculeSample(BaseModel):
    """
    Model for supramolecule in EMDB annotations.
    This model is used to represent a supramolecule in EMDB annotations.
    """
    id: int
    type: str
    complex_portal: Optional[List[ComplexPortalAnnotation]] = None

    @classmethod
    def from_api(cls, data: dict, mol_id: str) -> "EMDBSupramoleculeSample":
        """
        Create an EMDBSupramolecule instance from API data.

        :param mol_id: Supramolecule ID. The same ID is used in the EMDB sample.
        :param data: The data returned by the EMDB API.
        :return: An instance of EMDBSupramolecule.
        """
        cpx = []

        if "annotations" in data:
            annotations = data["annotations"]
            complex_portal_data = annotations.get("CPX", [])
            for annotation in complex_portal_data:
                cpx.append(ComplexPortalAnnotation.from_api(annotation, sample_id=mol_id))

        supramolecule =  cls(
            id=int(mol_id[1:]),
            type=data.get("type"),
        )

        if cpx:
            supramolecule.complex_portal = cpx if cpx else None

        return supramolecule

    def __str__(self):
        return (f"<EMDBSupramoleculeSample "
                f"id={self.id} "
                f"type={self.type} "
                f"complex_portal_count={len(self.complex_portal) if self.complex_portal else 0}>")


class EMDBMacromoleculeSample(BaseModel):
    """
    Model for macromolecule sample in EMDB annotations.
    This model is used to represent a macromolecule sample in EMDB annotations.
    """
    id: int
    type: str
    uniprot: List[UniProtAnnotation] = []
    pfam: List[PfamAnnotation] = []
    interpro: List[InterProAnnotation] = []
    gene_ontology: List[GeneOntologyAnnotation] = []
    gene_ontology_cell: List[GeneOntologyAnnotation] = []
    gene_ontology_process: List[GeneOntologyAnnotation] = []
    gene_ontology_function: List[GeneOntologyAnnotation] = []
    cath: List[CathAnnotation] = []
    chebi: List[ChEBIAnnotation] = []
    chembl: List[ChEMBLAnnotation] = []
    drugbank: List[DrugBankAnnotation] = []
    pdbekb: List[PDBeKbAnnotation] = []
    alphafolddb: List[AlphaFoldDBAnnotation] = []
    scop2: List[Scop2Annotation] = []

    @classmethod
    def from_api(cls, data: dict, mol_id: str) -> "EMDBMacromoleculeSample":
        """
        Create an EMDBMacromoleculeSample instance from API data.

        :param mol_id: Macromolecule ID. The same ID is used in the EMDB sample.
        :param data: The data returned by the EMDB API.
        :return: An instance of EMDBMacromoleculeSample.
        """
        uniprot = []
        pfam = []
        interpro = []
        gene_ontology = []
        gene_ontology_cell = []
        gene_ontology_process = []
        gene_ontology_function = []
        cath = []
        chebi = []
        chembl = []
        drugbank = []
        pdbekb = []
        alphafolddb = []
        scop2 = []

        if "annotations" in data:
            annotations = data["annotations"]
            uniprot_data = annotations.get("UNIPROT", [])
            for annotation in uniprot_data:
                uniprot.append(UniProtAnnotation.from_api(annotation, sample_id=mol_id))
            pfam_data = annotations.get("PFAM", [])
            for annotation in pfam_data:
                pfam.append(PfamAnnotation.from_api(annotation, sample_id=mol_id))
            interpro_data = annotations.get("INTERPRO", [])
            for annotation in interpro_data:
                interpro.append(InterProAnnotation.from_api(annotation, sample_id=mol_id))
            gene_ontology_data = annotations.get("GO", {})
            gene_ontology_cell_data = gene_ontology_data.get("C", [])
            gene_ontology_process_data = gene_ontology_data.get("P", [])
            gene_ontology_function_data = gene_ontology_data.get("F", [])
            for annotation in gene_ontology_cell_data:
                gene_ontology_cell.append(GeneOntologyAnnotation.from_api(annotation, sample_id=mol_id))
                gene_ontology.append(GeneOntologyAnnotation.from_api(annotation, sample_id=mol_id))
            for annotation in gene_ontology_process_data:
                gene_ontology_process.append(GeneOntologyAnnotation.from_api(annotation, sample_id=mol_id))
                gene_ontology.append(GeneOntologyAnnotation.from_api(annotation, sample_id=mol_id))
            for annotation in gene_ontology_function_data:
                gene_ontology_function.append(GeneOntologyAnnotation.from_api(annotation, sample_id=mol_id))
                gene_ontology.append(GeneOntologyAnnotation.from_api(annotation, sample_id=mol_id))
            cath_data = annotations.get("CATH", [])
            for annotation in cath_data:
                cath.append(CathAnnotation.from_api(annotation, sample_id=mol_id))
            chebi_data = annotations.get("CHEBI", [])
            for annotation in chebi_data:
                chebi.append(ChEBIAnnotation.from_api(annotation, sample_id=mol_id))
            chembl_data = annotations.get("CHEMBL", [])
            for annotation in chembl_data:
                chembl.append(ChEMBLAnnotation.from_api(annotation, sample_id=mol_id))
            drugbank_data = annotations.get("DRUGBANK", [])
            for annotation in drugbank_data:
                drugbank.append(DrugBankAnnotation.from_api(annotation, sample_id=mol_id))
            pdbekb_data = annotations.get("PDBEKB", [])
            for annotation in pdbekb_data:
                pdbekb.append(PDBeKbAnnotation.from_api(annotation, sample_id=mol_id))
            alphafolddb_data = annotations.get("ALPHAFOLDDB", [])
            for annotation in alphafolddb_data:
                alphafolddb.append(AlphaFoldDBAnnotation.from_api(annotation, sample_id=mol_id))
            scop2_data = annotations.get("SCOP2", [])
            for annotation in scop2_data:
                scop2.append(Scop2Annotation.from_api(annotation, sample_id=mol_id))

        macromolecule = cls(
            id=int(mol_id[1:]),
            type=data.get("type", ""),
            uniprot=uniprot,
            pfam=pfam,
            interpro=interpro,
            gene_ontology=gene_ontology,
            gene_ontology_cell=gene_ontology_cell,
            gene_ontology_process=gene_ontology_process,
            gene_ontology_function=gene_ontology_function,
            cath=cath,
            chebi=chebi,
            chembl=chembl,
            drugbank=drugbank,
            pdbekb=pdbekb,
            alphafolddb=alphafolddb,
            scop2=scop2
        )

        return macromolecule

    def __str__(self):
        return (f"<EMDBMacromoleculeSample "
                f"id={self.id} "
                f"type={self.type} "
                f"uniprot_count={len(self.uniprot) if self.uniprot else 0} "
                f"pfam_count={len(self.pfam) if self.pfam else 0} "
                f"interpro_count={len(self.interpro) if self.interpro else 0} "
                f"gene_ontology_count={len(self.gene_ontology) if self.gene_ontology else 0} "
                f"cath_count={len(self.cath) if self.cath else 0} "
                f"chebi_count={len(self.chebi) if self.chebi else 0} "
                f"chembl_count={len(self.chembl) if self.chembl else 0} "
                f"drugbank_count={len(self.drugbank) if self.drugbank else 0} "
                f"pdbekb_count={len(self.pdbekb) if self.pdbekb else 0} "
                f"alphafolddb_count={len(self.alphafolddb) if self.alphafolddb else 0} "
                f"scop2_count={len(self.scop2) if self.scop2 else 0}>")


class EMDBAnnotations(BaseModel):
    """
    Model for EMDB annotations.
    This model is used to store annotations related to an EMDB entry.
    """
    emdb_id: str
    macromolecules: List[EMDBMacromoleculeSample] = []
    supramolecules: List[EMDBSupramoleculeSample] = []
    orcid: Optional[List[ORCIDAnnotation]] = None
    empiar: Optional[List[EMPIARAnnotation]] = None
    pdb: Optional[List[PDBAnnotation]] = None
    _client: Optional["EMDB"] = PrivateAttr(default=None)

    @classmethod
    def from_api(cls, data: dict, client: "EMDB") -> "EMDBAnnotations":
        """
        Create an EMDBAnnotations instance from API data.

        :param data: The data returned by the EMDB API.
        :param client: The EMDB client instance used to make the API request.
        :return: An instance of EMDBAnnotations.
        """
        orcid = []
        empiar = []
        pdb = []
        if "annotations" in data:
            annotations = data["annotations"]

            orcids = annotations.get("ORCID", [])
            for annotation in orcids:
                orcid.append(ORCIDAnnotation.from_api(annotation, sample_id="all"))
            empiars = annotations.get("EMPIAR", [])
            for annotation in empiars:
                empiar.append(EMPIARAnnotation.from_api(annotation, sample_id="all"))
            pdbs = annotations.get("PDB", [])
            for annotation in pdbs:
                pdb.append(PDBAnnotation.from_api(annotation, sample_id="all"))

        obj = cls(
            emdb_id=data.get("emdb_id"),
            macromolecules=[
                EMDBMacromoleculeSample.from_api(mol_data, mol_id) for mol_id, mol_data in data.get("macromolecules", {}).items()
            ],
            supramolecules=[
                EMDBSupramoleculeSample.from_api(supramol_data, supramol_id) for supramol_id, supramol_data in data.get("supramolecules", {}).items()
            ],
            _client=client
        )

        if orcid:
            obj.orcid = orcid
        if empiar:
            obj.empiar = empiar
        if pdb:
            obj.pdb = pdb

        return obj

    def __str__(self):
        return (f"<EMDBAnnotations "
                f"emdb_id={self.emdb_id} "
                f"orcid_count={len(self.orcid) if self.orcid else 0} "
                f"empiar_count={len(self.empiar) if self.empiar else 0} "
                f"pdb_count={len(self.pdb) if self.pdb else 0}"
                f">")


