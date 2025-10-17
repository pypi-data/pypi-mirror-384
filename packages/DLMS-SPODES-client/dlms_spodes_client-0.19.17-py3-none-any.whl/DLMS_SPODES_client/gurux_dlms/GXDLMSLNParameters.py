from dataclasses import dataclass
from . import GXDLMSSettings, GXByteBuffer, ResponseType
from .enums import ErrorCode
from DLMS_SPODES.enums import SetRequest, XDLMSAPDU, ACSEAPDU


@dataclass
class GXDLMSLNParameters:
    settings: GXDLMSSettings
    invokeId: int
    command: XDLMSAPDU | ACSEAPDU
    requestType: ResponseType | SetRequest  # | ActionRequestType
    attributeDescriptor: GXByteBuffer | None
    data: GXByteBuffer | None
    # Reply status.
    status: ErrorCode | int
    windowSize: int = 1
    streaming: bool = False
    """ Is this last block in send. """

    def __post_init__(self):
        self.blockIndex = self.settings.blockIndex
        self.blockNumberAck = self.settings.blockNumberAck
        self.time = None
        """ Send date and time.  This is used in Data notification messages. """
        self.multipleBlocks = self.settings.is_multiple_block()
        """ Are there more data to send or more data to receive"""
        self.lastBlock = self.settings.count == self.settings.index
        """ Is this last block in send. """
        if self.settings:
            self.settings.command = self.command
            if self.command == XDLMSAPDU.GET_REQUEST and self.requestType != ResponseType.WITH_DATABLOCK:
                self.settings.commandType = self.requestType
