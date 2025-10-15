import typing
from .utils import SingletonMeta as SingletonMeta
from Server.FlowManager import Flow as Flow

class SmilesAPI(metaclass=SingletonMeta):
    """
    API for interacting with the Smiles Manager inside Horus
    """
    def addSmiles(self, smiles: str, group: typing.Optional[str] = None) -> None:
        """
        Add a smiles string to the smiles manager

        :param smiles: The smiles string to add
        :param group: The group to add the smiles to
        """
    def addCSV(self, csv: str, group: typing.Optional[str] = None) -> None:
        """
        Adds a CSV file to the smiles manager

        :param csv: The CSV file path to add
        """
    def addSmilesWithData(self, smiles: list[dict]) -> None:
        """
        Adds a list of full SMILES object to the smiles manager

        Each object should be in the following keys:

        - smi: string -> SMILES as a string
        - label: string -> Label to display
        - extraInfo: string -> Extra info to display
        - group: string -> Group to add the smiles to
        - props: {key: value, ...} -> Properties to add to the molecule (optional)
        """
    def reset(self) -> None:
        """
        Resets the visualizer
        """
