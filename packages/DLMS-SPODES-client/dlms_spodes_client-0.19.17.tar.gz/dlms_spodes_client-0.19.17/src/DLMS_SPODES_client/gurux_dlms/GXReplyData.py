from dataclasses import dataclass, field
from typing import Optional, Any
from DLMS_SPODES.enums import XDLMSAPDU
from .GXByteBuffer import GXByteBuffer
from .enums import RequestTypes


@dataclass
class GXReplyData:
    command: Optional[XDLMSAPDU] = None
    """Received command"""
    moreData: RequestTypes = RequestTypes.NONE
    """Is more data available"""
    data: GXByteBuffer = field(init=False, default_factory=GXByteBuffer)
    """Received data"""
    complete: bool = False
    """Is frame complete"""
    error: int = 0
    """Received error"""
    value: Any = None
    commandType: int = 0
    """Received command type"""
    frameId: int = 0
    """HDLC frame ID"""
    dataValue: Any = None
    totalCount: int = 0
    """Expected count of element in the array"""
    readPosition: int = 0
    """Last read position.  This is used in peek to solve how far data is read"""
    packetLength: int = 0
    """Packet length"""
    peek: bool = False
    """Try get value"""
    cipherIndex: int = 0
    """Cipher index is position where data is decrypted"""
    blockNumber: int = 0
    """GBT block number"""
    blockNumberAck: int = 0
    """GBT block number ACK"""
    streaming: bool = False
    """Is GBT streaming in use"""
    windowSize: int = 0
    """GBT Window size.  This is for internal use"""
    clientAddress: int = 0
    """Client address of the notification message. Notification message sets this"""
    serverAddress: int = 0
    """ Server address of the notification message. Notification message sets this"""

    def clear(self):
        """" Reset data values to default. """
        self.moreData = RequestTypes.NONE
        self.command = None
        self.commandType = 0
        self.data.capacity = 0
        self.complete = False
        self.error = 0
        self.totalCount = 0
        self.dataValue = None
        self.readPosition = 0
        self.packetLength = 0
        self.cipherIndex = 0
        self.value = None

    def isMoreData(self):
        """ Is more data available. """
        return self.moreData != RequestTypes.NONE and self.error == 0

    def isNotify(self):
        """ Is notify message. """
        return self.command == XDLMSAPDU.EVENT_NOTIFICATION_REQUEST or self.command == XDLMSAPDU.DATA_NOTIFICATION or self.command == XDLMSAPDU.INFORMATION_REPORT_REQUEST

    def getTotalCount(self):
        """ Get total count of element in the array.  If this method is used peek must be set true."""
        return self.totalCount

    def getCount(self):
        """  Get count of read elements.  If this method is used peek must be set true."""
        if isinstance(self.dataValue, list):
            return len(self.dataValue)
        return 0

    def isStreaming(self) -> bool:
        """ Is GBT streaming. """
        return self.streaming and (self.blockNumberAck * self.windowSize) + 1 > self.blockNumber

    def __str__(self) -> str:
        return str(self.data) if self.data else ""
