import typing
from .utils import SingletonMeta as SingletonMeta
from Server.FlowManager import Flow as Flow
from enum import Enum
from pydantic import BaseModel
from typing import Any, Dict, Literal, Optional, Union

class ColorTheme(str, Enum):
    """
    A list of the color themes available in Mol*
    """
    atom_id: str
    carbohydrate_symbol: str
    cartoon: str
    chain_id: str
    element_index: str
    element_symbol: str
    entity_id: str
    entity_source: str
    external_structure: str
    external_volume: str
    formal_charge: str
    hydrophobicity: str
    illustrative: str
    model_index: str
    molecule_type: str
    occupancy: str
    operator_hkl: str
    operator_name: str
    partial_charge: str
    polymer_id: str
    polymer_index: str
    residue_name: str
    secondary_structure: str
    sequence_id: str
    shape_group: str
    structure_index: str
    trajectory_index: str
    uncertainty: str
    unit_index: str
    uniform: str
    volume_segment: str
    volume_value: str
    default: str

class SizeTheme(str, Enum):
    """
    A list of the size themes available in Mol*
    """
    physical: str
    shape_group: str
    uncertainty: str
    uniform: str
    volume_value: str
    default: str

class MolRepresentations(str, Enum):
    """
    Available molstar representations
    """
    CARTOON: str
    BACKBONE: str
    BALL_AND_STICK: str
    CARBOHYDRATE: str
    ELLIPSOID: str
    GAUSSIAN_SURFACE: str
    GAUSSIAN_VOLUME: str
    LABEL: str
    LINE: str
    MOLECULAR_SURFACE: str
    ORIENTATION: str
    PLANE: str
    POINT: str
    PUTTY: str
    SPACEFILL: str

class MolstarThemeOptions(BaseModel):
    """
    Options for updating a model's theme
    """
    representation: MolRepresentations
    representationParams: Optional[dict[str, Any]]
    color: Optional[Union[ColorTheme, str]]
    colorParams: Optional[dict[str, Any]]
    size: Optional[Union[SizeTheme, str]]
    sizeParams: Optional[Dict[str, Any]]
    class Config:
        use_enum_values: bool

class SelectionLanguage(str, Enum):
    """Selection language types supported by Mol*"""
    MOL_SCRIPT: str
    VMD: str
    PYMOL: str
    JMOL: str

class MolecularSelection(BaseModel):
    """
    Comprehensive molecular selection model supporting all Mol* selection types
    """
    script: Optional[str]
    language: Optional[SelectionLanguage]
    chain: Optional[str]
    auth_chain: Optional[str]
    entity: Optional[str]
    residue: Optional[int]
    auth_residue: Optional[int]
    residue_range: Optional[dict]
    auth_residue_range: Optional[dict]
    atom_name: Optional[str]
    auth_atom_name: Optional[str]
    element_symbol: Optional[str]
    atom_id: Optional[int]
    atom_index: Optional[int]
    insertion_code: Optional[str]
    chain_and_residue: Optional[dict]
    auth_chain_and_residue: Optional[dict]
    secondary_structure: Optional[Literal['helix', 'sheet', 'coil']]
    type: Optional[Literal['all', 'polymer', 'protein', 'nucleic', 'water', 'ion', 'lipid', 'branched', 'ligand', 'non-standard', 'coarse']]
    within_distance: Optional[dict]

class MolstarAPI(metaclass=SingletonMeta):
    """
    API for interacting with Mol* visualizer inside Horus
    """
    def addMolecule(self, filePath: str, label: typing.Optional[str] = None, theme: typing.Optional[MolstarThemeOptions] = None) -> None:
        """
        Adds the given Molecule file to Mol*

        :param filePath: The path to the molecule file
        :param label: The label for the molecule. Optional. Defaults to the filename
        """
    def addComponent(self, label: str, selectionLabel: str, selection: MolecularSelection, theme: typing.Optional[MolstarThemeOptions] = None):
        """
        Adds a component to an existing structure given the label and a selection.

        :param label: The loaded structure to which apply the component
        :param selectionLabel: The new component label
        :param selection: The specific selection of the structure provided in the label
        :param theme: Custom theme to apply to the selection
        """
    def loadTrajectory(self, topology: str, trajectory: str, label: typing.Optional[str] = None) -> None:
        """
        Adds the given trajectory file to Mol*

        :param topology: The path to the topology file
        :param trajectory: The path to the trajectory file
        :param label: The label for the trajectory. Optional. Defaults to the filename
        """
    def focusResidue(self, residue: int, structureLabel: typing.Optional[str] = None, chain: typing.Optional[str] = None, nearRadius: int = 5) -> None:
        """
        Focuses on the given residue

        :param residue: The sequence number of the residue to focus
        :param structureLabel: The label of the structure to focus
        :param chain: The chain ID of the residue to focus
        :param nearRadius: The radius around the residue to display nearby residues
        """
    def addSphere(self, center: list[float], radius: float, color: typing.Optional[str] = None, opacity: float = 1) -> None:
        """
        Adds a sphere to the scene.

        :param x: The x coordinate of the sphere in Angstroms
        :param y: The y coordinate of the sphere in Angstroms
        :param z: The z coordinate of the sphere in Angstroms
        :param radius: The radius of the sphere in Angstroms
        :param color: The color of the sphere as an RGB hex string (i.e. #0000FF)
        :param opacity: The opacity of the sphere (0.0 - 1.0)
        """
    def addBox(self, center: list[float], sides: typing.Optional[list[float]] = None, lineSize: float = 1, color: typing.Optional[str] = None, opacity: float = 1) -> None:
        """
        Adds a box to the scene.

        :param center: The x, y and z coordinates of the center of the box as a list of [x, y ,z]
        :param sides: The a, b and c lengths of the box as a list of [a, b ,c].
        Defaults to [1, 1, 1]
        :param lineSize: The width of the lines. Defaults to 1.
        :param color: The color of the box as an RGB hex string (i.e. #0000FF)
        Defaults to random color.
        :param opacity: The opacity of the box (0.0 - 1.0). Defaults to 1.
        """
    def setBackgroundColor(self, color: str) -> None:
        """
        Sets the background color of the scene

        :param color: The color to set the background to as an RGB hex string (i.e. #0000FF)
        """
    def setSpin(self, speed: float = 1) -> None:
        """
        Sets the spin of the molecule.

        :param speed: The rotation speed. Defaults to 1. To stop it, set the speed to 0
        """
    def reset(self) -> None:
        """
        Resets the visualizer
        """
