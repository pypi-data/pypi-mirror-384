import typing
from .utils import SingletonMeta as SingletonMeta
from Server.FlowManager import Flow as Flow
from Server.server import HorusSocket as HorusSocket
from _typeshed import Incomplete

class Extensions(metaclass=SingletonMeta):
    socketio: Incomplete
    def __init__(self, socketio: typing.Optional['HorusSocket'] = None) -> None: ...
    def open(self, pluginID: str, pageID: str, data: typing.Optional[typing.Dict[str, typing.Any]] = None, title: str = 'Extension') -> None:
        """
        Opens the given extension (PluginPage) and passes the given data to it.

        :param pluginID: The ID of the plugin that contains the desired PluginPage (Extension).
        :param pageID: The ID of the PluginPage that represents the extension.
        :param data: The data to pass to the extension.
        """
    def storeExtensionResults(self, pluginID: str, pageID: str, data: typing.Optional[typing.Dict[str, typing.Any]] = None, title: str = 'Results') -> None:
        """
        Stores the results of the extension in the flow to be opened at any time.

        :param pluginID: The ID of the plugin that contains the desired PluginPage (Extension).
        :param pageID: The ID of the PluginPage that represents the extension.
        :param data: The results of the extension.
        :param title: The title of the results. This will be displayed on top of the block that produced the results.
        """
    def loadHTML(self, html: str, title: str, store: bool = True) -> None:
        """
        Loads the given HTML into the extension.

        :param html: The path to the HTML to load .
        :param title: The title of the 'Result'.         This will be displayed on top of the block that produced the HTML.
        :param store: Whether to store the HTML as results or to open it inmediately.
        :param asString: Whether the passed HTML is a string or an html file.
        """
    def loadImage(self, image: str, title: str, store: bool = True) -> None:
        """
        Loads the given image into the extension.

        The image will be stored inside the flow.

        :param image: The path to the image to load. Supports png, jpg and gif.
        :param title: The title of the 'Result'.         This will be displayed on top of the block that produced the image.
        :param store: Whether to store the image as results or to open it inmediately.
        """
    def loadText(self, text: str, title: str, store: bool = True) -> None:
        """
        Loads the given text into the extension.

        :param text: The text to load.
        :param title: The title of the 'Result'.         This will be displayed on top of the block that produced the text.
        :param store: Whether to store the text as results or to open it inmediately.
        """
    def loadCSV(self, csv: str, title: str, store: bool = True) -> None:
        """
        Loads the given CSV into the extension.

        :param csv: The path to the CSV to load.
        :param title: The title of the 'Result'.         This will be displayed on top of the block that produced the CSV.
        :param store: Whether to store the CSV as results or to open it inmediately.
        """
    def loadPlot(self, plotCSV: str, title: str, store: bool = True) -> None:
        """
        Loads the given CSV as a Plot into the extension.

        :param csv: The path to the CSV to load as plot.
        :param title: The title of the plot.         This will be displayed on top of the block that produced the Plot.
        :param store: Whether to store the Plot as results or to open it inmediately.
        """
    def loadPDF(self, pdf: str, title: str, store: bool = True) -> None:
        """
        Loads the given PDF into the extension.

        :param pdf: The path to the PDF to load.
        :param title: The title of the 'Result'.         This will be displayed on top of the block that produced the PDF.
        :param store: Whether to store the PDF as results or to open it inmediately.
        """
    def loadFile(self, filePath: str, title: str, store: bool = True, readOnly: bool = False, format: typing.Optional[str] = None) -> None:
        '''
        Loads the given file into the Horus File Editor.

        :param filePath: The path to the file to load.
        :param title: The title of the \'Result\'.         This will be displayed on top of the block that produced the file.
        :param store: Whether to store the file as results or to open it inmediately.
        :param readOnly: Whether to open the file in read-only mode.
        :param format: The format of the file (e.g., "text", "json", "csv", "shell"). If not provided, inferred from the file extension.
        '''
