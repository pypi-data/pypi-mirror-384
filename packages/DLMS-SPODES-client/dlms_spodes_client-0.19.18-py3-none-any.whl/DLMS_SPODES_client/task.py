import asyncio
import random
from copy import copy
import re
from typing_extensions import deprecated
import hashlib
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, Protocol, cast, override, Self, Final, Iterable, TypeVarTuple
from itertools import count
import datetime
import time
from semver import Version as SemVer
from StructResult import result
from DLMS_SPODES.pardata import ParValues
from DLMS_SPODES.types.implementations import enums, long_unsigneds, bitstrings, octet_string, structs, arrays, integers
from DLMS_SPODES.pardata import ParData
from DLMS_SPODES.cosem_interface_classes import parameters as dlms_par
from DLMS_SPODES.cosem_interface_classes.parameter import Parameter
from DLMS_SPODES import exceptions as exc, pdu_enums as pdu
from DLMS_SPODES.cosem_interface_classes import (
    cosem_interface_class as ic,
    collection,
    overview,
    ln_pattern
)
from DLMS_SPODES.cosem_interface_classes.clock import Clock
from DLMS_SPODES.cosem_interface_classes.image_transfer.image_transfer_status import ImageTransferStatus
from DLMS_SPODES.cosem_interface_classes.image_transfer.ver0 import ImageTransferInitiate, ImageBlockTransfer, ImageToActivateInfo
from DLMS_SPODES.cosem_interface_classes.association_ln.ver0 import ObjectListType, ObjectListElement
from DLMS_SPODES.cosem_interface_classes import association_ln
from DLMS_SPODES.types import cdt, ut, cst
from DLMS_SPODES.hdlc import frame
from DLMS_SPODES.enums import Transmit, Application, Conformance
from DLMS_SPODES.firmwares import get_firmware
from DLMS_SPODES.cosem_interface_classes.image_transfer import image_transfer_status as i_t_status
from DLMSAdapter.main import AdapterException, Adapter, gag
from DLMSCommunicationProfile.osi import OSI
from .logger import LogLevel as logL
from .client import Client, Security, Data, mechanism_id, AcseServiceUser, State


firm_id_pat = re.compile(b".*(?P<fid>PWRM_M2M_[^_]{1,10}_[^_]{1,10}).+")
boot_ver_pat = re.compile(b"(?P<boot_ver>\\d{1,4}).+")


type Errors = list[Exception]


class Base[T: result.Result](Protocol):
    """Exchange task for DLMS client"""
    msg: str

    def copy(self) -> Self: ...

    @property
    def current(self) -> 'Base[T] | Self':
        return self

    async def run(self, c: Client) -> T | result.Error:
        """exception handling block"""
        try:
            return await self.physical(c)
        except (ConnectionRefusedError, TimeoutError) as e:
            return result.Error.from_e(e)
        except exc.DLMSException as e:
            return result.Error.from_e(e)
        except Exception as e:
            return result.Error.from_e(e)
        # except asyncio.CancelledError as e:
        #     await c.close()  # todo: change to DiscRequest
        #     return result.Error.from_e(exc.Abort("manual stop"))  # for handle BaseException
        finally:
            c.received_frames.clear()  # for next exchange need clear all received frames. todo: this bag, remove in future

    async def PH_connect(self, c: Client) -> result.Ok | result.Error:
        if c.media is None:
            return result.Error.from_e(exc.NoPort("no media"), "PH_connect")
        if not c.media.is_open():
            await c.media.open()
        c.level = OSI.PHYSICAL
        c.log(logL.INFO, F"Open port communication channel: {c.media}")
        # todo: replace to <data_link>
        if (
            c._objects is None
            and not isinstance(self, InitType)
        ):
            if isinstance(res := await init_type.data_link(c), result.Error):
                return res.with_msg("PH_connect")
            if isinstance(res_close := await c.close(), result.Error):  # todo: change to DiscRequest, or make not closed or reconnect !!!
                return res_close
        return result.OK

    @staticmethod
    async def physical_t(c: Client) -> result.Ok | result.Error:
        return await c.close()

    async def physical(self, c: Client) -> T | result.Error:
        if OSI.PHYSICAL not in c.level:
            if isinstance((res := await self.PH_connect(c)), result.Error):
                return res
        ret = await self.data_link(c)
        if isinstance(res_terminate := await self.physical_t(c), result.Error):
            return res_terminate
        return ret

    async def DL_connect(self, c: Client) -> None:
        """Data link Layer connect"""
        c.send_frames.clear()
        # calculate addresses  todo: move to c.com_profile(HDLC)
        c.DA = frame.Address(
            upper_address=int(c.server_SAP),
            lower_address=c.com_profile.parameters.device_address,
            length=c.addr_size
        )
        c.SA = frame.Address(upper_address=int(c.SAP))
        c.log(logL.INFO, F"{c.SA=} {c.DA=}")
        # initialize connection
        if c.settings.cipher.security != Security.NONE:
            c.log(logL.DEB, F"Security: {c.settings.cipher.security}/n"
                            F"System title: {c.settings.cipher.systemTitle.hex()}"
                            F"Authentication key: {c.settings.cipher.authenticationKey.hex()}"
                            F"Block cipher key: {c.settings.cipher.blockCipherKey.hex()}")
            if c.settings.cipher.dedicatedKey:
                c.log(logL.DEB, F"Dedicated key: {c.settings.cipher.dedicatedKey.hex()}")
        # SNRM
        c.get_SNRM_request()
        if isinstance(res_pdu := await c.read_data_block(), result.Error):
            return res_pdu
        c.level |= OSI.DATA_LINK

    async def data_link(self, c: Client) -> T | result.Error:
        if OSI.DATA_LINK not in c.level:
            await self.DL_connect(c)
        # todo: make tile
        return await self.application(c)

    async def AA(self, c: Client) -> result.Ok | result.Error:
        """Application Associate"""
        if c.invocationCounter and c.settings.cipher is not None and c.settings.cipher.security != Security.NONE:
            # create IC object. TODO: remove it after close connection, maybe???
            c.settings.proposedConformance |= Conformance.GENERAL_PROTECTION

            # my block
            IC: Data = c.objects.add_if_missing(ut.CosemClassId(1),
                                                 logical_name=cst.LogicalName(bytearray((0, c.get_channel_index(), 43, 1,
                                                                                        c.current_association.security_setup_reference.e, 255))),
                                                 version=cdt.Unsigned(0))
            tmp_client_SAP = c.current_association.associated_partners_id.client_SAP
            challenge = c.settings.ctoSChallenge
            try:
                c.aarqRequest(c.m_id)
                if isinstance(res_pdu := await c.read_data_block(), result.Error):
                    return res_pdu
                ret = c.parseAareResponse(res_pdu.value)
                c.level |= OSI.APPLICATION  # todo: it's must be result of <ret> look down
                if isinstance(res_ic := await ReadObjAttr(IC, 2).exchange(c), result.Error):
                    return res_ic
                c.settings.cipher.invocationCounter = 1 + int(res_ic.value)
                c.log(logL.DEB, "Invocation counter: " + str(c.settings.cipher.invocationCounter))
                # disconnect
                if c.media and c.media.is_open():
                    c.log(logL.DEB, "DisconnectRequest")
                    if isinstance(res_disc_req := await c.disconnect_request(), result.Error):
                        return res_disc_req
            finally:
                c.SAP = tmp_client_SAP
                c.settings.useCustomChallenge = challenge is not None
                c.settings.ctoSChallenge = challenge

            # gurux with several removed methods
            # add = self.settings.clientAddress
            # auth = self.settings.authentication
            # security = self.client.ciphering.security
            # challenge = self.client.ctoSChallenge
            # try:
            #     self.client.clientAddress = 16
            #     self.settings.authentication = Authentication.NONE
            #     self.client.ciphering.security = Security.NONE
            #     reply = GXReplyData()
            #     self.get_SNRM_request()
            #     self.status = Status.READ
            #     self.read_data_block2()
            #     self.objects.IEC_HDLS_setup.set_from_info(self.reply.data.get_data())
            #     self.connection_state = ConnectionState.HDLC
            #     self.reply.clear()
            #     self.aarqRequest()
            #     self.read_data_block2()
            #     self.parseAareResponse(reply.data)
            #     reply.clear()
            #     item = GXDLMSData(self.invocationCounter)
            #     data = self.client.read(item, 2)[0]
            #     reply = GXReplyData()
            #     self.read_data_block(data, reply)
            #     item.encodings[2] = reply.data.get_data()
            #     Update data type on read.
            #     if item.getDataType(2) == cdt.NullData.TAG:
            #         item.setDataType(2, reply.valueType)
            #     self.client.updateValue(item, 2, reply.value)
            #     self.client.ciphering.invocationCounter = 1 + item.value
            #     print("Invocation counter: " + str(self.client.ciphering.invocationCounter))
            #     if self.media and self.media.isOpen():
            #         self.log(logL.INFO, "DisconnectRequest")
            #         self.disconnect_request()
            # finally:
            #     self.settings.clientAddress = add
            #     self.settings.authentication = auth
            #     self.client.ciphering.security = security
            #     self.client.ctoSChallenge = challenge

        c.aarqRequest(c.m_id)
        if isinstance(res_pdu := await c.read_data_block(), result.Error):
            return res_pdu
        # await c.read_attr(ut.CosemAttributeDescriptor((collection.ClassID.ASSOCIATION_LN, ut.CosemObjectInstanceId("0.0.40.0.0.255"), ut.CosemObjectAttributeId(6)))) # for test only
        match c.parseAareResponse(res_pdu.value):
            case AcseServiceUser.NULL:
                c.log(logL.INFO, "Authentication success")
                c.level |= OSI.APPLICATION
            case AcseServiceUser.AUTHENTICATION_REQUIRED:
                c.getApplicationAssociationRequest()
                if isinstance(res_pdu := await c.read_data_block(), result.Error):
                    return res_pdu
                c.parseApplicationAssociationResponse(res_pdu.value)
            case _ as diagnostic:
                return result.Error.from_e(exc.AssociationResultError(diagnostic))
        if c._objects is not None:
            if c.is_universal():
                await change_ldn.exchange(c)
            else:
                await match_ldn.exchange(c)
        return result.OK

    async def application(self, c: Client) -> T | result.Error:
        if OSI.APPLICATION not in c.level:
            if isinstance(res := await self.AA(c), result.Error):
                return res
        # no tile
        return await self.exchange(c)

    async def exchange(self, c: Client) -> T | result.Error:
        """application level exchange"""

    async def connect(self, c: Client) -> result.Ok | result.Error:
        await self.PH_connect(c)
        await self.DL_connect(c)
        return await self.AA(c)


class SimpleCopy:
    def copy(self) -> Self:
        return self


class Simple[T](Base[result.Simple[T]], Protocol):
    """Simple result"""
    @override
    async def exchange(self, c: Client) -> result.SimpleOrError[T]: ...


class Boolean(Simple[bool], Protocol):
    """Simple[bool] result"""
    @override
    async def exchange(self, c: Client) -> result.SimpleOrError[bool]: ...


class CDT[T: cdt.CommonDataType](Simple[T], Protocol):
    """Simple[CDT] result"""
    @override
    async def exchange(self, c: Client) -> result.SimpleOrError[T]: ...


class _List[T](Base[result.List[T]], Protocol):
    """With List result"""
    @override
    async def exchange(self, c: Client) -> result.List[T] | result.Error: ...


class _Sequence[*Ts](Base[result.Sequence[*Ts]], Protocol):
    """With List result"""
    @override
    async def exchange(self, c: Client) -> result.Sequence[*Ts] | result.Error: ...


class OK(Base[result.Ok], Protocol):
    """Always result OK"""

    @override
    async def exchange(self, c: Client) -> result.Ok | result.Error: ...


class StrictOK(Base[result.StrictOk], Protocol):
    """Always result OK"""

    @override
    async def exchange(self, c: Client) -> result.StrictOk | result.Error: ...


@dataclass(frozen=True)
class ClientBlocking(SimpleCopy, OK):
    """complete by time or abort"""
    delay: float = field(default=99999999.0)
    msg: str = "client blocking"

    async def run(self, c: Client) -> result.Ok | result.Error:
        try:
            c.level = OSI.APPLICATION
            c.log(logL.WARN, F"blocked for {self.delay} second")
            await asyncio.sleep(self.delay)
            return result.OK
        finally:
            c.level = OSI.NONE
        return result.OK

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        raise RuntimeError(f"not support for {self.__class__.__name__}")


# todo: make with <data_link>
@dataclass
class TestDataLink(SimpleCopy, OK):
    msg: str = "test DLink"

    async def physical(self, c: Client) -> result.Ok | result.Error:
        if OSI.PHYSICAL not in c.level:
            if not c.media.is_open():
                await c.media.open()
            c.level = OSI.PHYSICAL
            c.DA = frame.Address(
                upper_address=int(c.server_SAP),
                lower_address=c.com_profile.parameters.device_address,
                length=c.addr_size
            )
            c.SA = frame.Address(upper_address=int(c.SAP))
            c.get_SNRM_request()
            if isinstance(res_pdu := await c.read_data_block(), result.Error):
                return res_pdu
            c.level |= OSI.DATA_LINK
            if isinstance(res_close := await c.close(), result.Error):  # todo: change to DiscRequest
                return res_close
        return result.Ok

    async def exchange(self, c: Client):
        return result.OK


@dataclass(frozen=True)
class Dummy(SimpleCopy, OK):
    msg: str = "dummy"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        """"""
        return result.OK


@dataclass(frozen=True)
class HardwareDisconnect(SimpleCopy, OK):
    msg: str = "hardware disconnect"

    @override
    async def exchange(self, c: Client) -> result.Ok | result.Error:
        await c.media.close()
        c.level = OSI.NONE
        msg = '' if self.msg is None else F": {self.msg}"
        c.log(logL.WARN, F"HARDWARE DISCONNECT{msg}")
        return result.OK


@dataclass(frozen=True)
class HardwareReconnect(SimpleCopy, OK):
    delay: float = 0.0
    """delay between disconnect and restore Application"""
    msg: str = "reconnect media without response"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance((res := await HardwareDisconnect().exchange(c)), result.Error):
            return res
        if self.delay != 0.0:
            c.log(logL.INFO, F"delay({self.delay})")
            await asyncio.sleep(self.delay)
        if isinstance(res_connect := await self.connect(c), result.Error):  # restore Application
            return res_connect
        return result.OK


@dataclass(frozen=True)
class Loop(OK):
    task: Base[result.Result]
    func: Callable[[Any], bool]
    delay: int = 0.0
    msg: str = "loop"
    attempt_amount: int = 0
    """0 is never end loop"""

    def copy(self) -> Self:
        return Loop(
            task=self.task.copy(),
            func=self.func,
            delay=self.delay,
            msg=self.msg,
            attempt_amount=self.attempt_amount
        )

    async def run(self, c: Client) -> result.Result:
        attempt = count()
        while not self.func(await super(Loop, self).run(c)):
            if next(attempt) == self.attempt_amount:
                return result.Error.from_e(ValueError("end of attempts"))
            await asyncio.sleep(self.delay)
        return result.OK

    async def exchange(self, c: Client) -> result.Result:
        return await self.task.exchange(c)


@dataclass
class ConditionalTask[T](Base):
    """Warning: experimental"""
    precondition_task: Base[result.Result]
    comp_value: T
    predicate: Callable[[T, T], bool]
    main_task: Base[result.Result]
    msg: str = "conditional task"

    async def exchange(self, c: Client) -> result.Result:
        res = await self.precondition_task.exchange(c)
        if self.predicate(self.comp_value, res.value):
            return await self.main_task.exchange(c)
        return result.Error.from_e(ValueError("Condition not satisfied"))


DEFAULT_DATETIME_SCHEDULER = cdt.DateTime.parse("1.1.0001")


@dataclass
class Scheduler[T: result.Result](Base[T]):
    """𝑟𝑒𝑝𝑒𝑡𝑖𝑡𝑖𝑜𝑛_𝑑𝑒𝑙𝑎𝑦 = 𝑟𝑒𝑝𝑒𝑡𝑖𝑡𝑖𝑜𝑛_𝑑𝑒𝑙𝑎𝑦_𝑚𝑖𝑛 × (𝑟𝑒𝑝𝑒𝑡𝑖𝑡𝑖𝑜𝑛_𝑑𝑒𝑙𝑎𝑦_𝑒𝑥𝑝𝑜𝑛𝑒𝑛𝑡 × 0.01) ** 𝑛"""
    task: Base[T]
    execution_datetime: Final[cdt.DateTime] = DEFAULT_DATETIME_SCHEDULER
    start_interval: Final[int] = 0
    number_of_retries: Final[int] = 3
    total_of_retries: Final[int] = 100
    repetition_delay_min: Final[int] = 1
    repetition_delay_exponent: Final[int] = 100
    repetition_delay_max: Final[int] = 100
    msg: str = "sheduler"

    def copy(self) -> "Scheduler[T]":
        return Scheduler(
            task=self.task.copy(),
            execution_datetime=self.execution_datetime,
            start_interval=self.start_interval,
            number_of_retries=self.number_of_retries,
            total_of_retries=self.total_of_retries,
            repetition_delay_min=self.repetition_delay_min,
            repetition_delay_exponent=self.repetition_delay_exponent,
            repetition_delay_max=self.repetition_delay_max,
            msg=self.msg
        )

    async def run(self, c: Client) -> T | result.Error:
        if self.start_interval != 0:
            await asyncio.sleep(random.uniform(0, self.start_interval))
        c.log(logL.INFO, f"start {self.__class__.__name__}")
        total_of_retries = count()
        is_start: bool = True
        acc = result.ErrorAccumulator()
        while True:
            dt = self.execution_datetime.get_right_nearest_datetime(now := datetime.datetime.now())
            if dt is None:
                if is_start:
                    is_start = False
                else:
                    return acc.as_error(exc.Timeout("start time is out"), msg=self.msg)
            else:
                delay = (dt - now).total_seconds()
                c.log(logL.WARN, f"wait for {delay=}")
                await asyncio.sleep(delay)
            for n in range(self.number_of_retries):
                if next(total_of_retries) > self.total_of_retries:
                    return acc.as_error(exc.Timeout("out of total retries"), msg=self.msg)
                await asyncio.sleep(min(self.repetition_delay_max, self.repetition_delay_min*(self.repetition_delay_exponent * 0.01)**n))
                if isinstance(res := await super(Scheduler, self).run(c), result.Error):
                    acc.append_err(res.err)
                else:
                    return res

    async def exchange(self, c: Client) -> T | result.Error:
        return await self.task.exchange(c)


@dataclass
class Subtasks[U: Base[result.Result]](Protocol):
    """for register longer other tasks into task"""
    tasks: Iterable[U]

    @property
    def current(self) -> U | Self: ...


class List[T: result.Result, U: Base[result.Result]](Subtasks[U], _List[T]):
    """for exchange task sequence"""
    __is_exchange: bool
    err_ignore: bool
    msg: str
    __current: Base[T]

    def __init__(self, *tasks: Base[T], msg: str = "", err_ignore: bool = False):
        self.tasks = list(tasks)
        self.__current = self
        self.__is_exchange = False
        self.msg = self.__class__.__name__ if msg == "" else msg
        self.err_ignore = err_ignore

    def copy(self) -> Self:
        if all((isinstance(t, SimpleCopy) for t in self.tasks)):
            return self
        return List(
            *(t.copy() for t in self.tasks),
            msg=self.msg,
            err_ignore=self.err_ignore
        )

    @property
    def current(self) -> 'Base[T] | Self':
        return self.__current

    def append(self, task: Base[T]):
        if not self.__is_exchange:
            self.tasks.append(task)
        else:
            raise RuntimeError(F"append to {self.__class__.__name__} not allowed, already exchange started")

    async def exchange(self, c: Client) -> result.List[T] | result.Error:
        res = result.List()
        self.__is_exchange = True
        for t in self.tasks:
            self.__current = t
            if (
                isinstance(res_one := await t.exchange(c), result.Error)
                and not self.err_ignore
            ):
                return res_one
            res.append(res_one)
        return res


class Sequence[*Ts](Subtasks[Base[result.Result]], _Sequence[*Ts]):
    """for exchange task sequence"""
    msg: str
    err_ignore: bool
    __current: "Base[result.Result] | Sequence[*Ts]"
    tasks: tuple[Base[result.Result], ...]

    def __init__(self, *tasks: Base[result.Result], msg: str = "sequence", err_ignore: bool = False):
        self.tasks = tasks
        self.__current = self
        self.msg = self.__class__.__name__ if msg == "" else msg
        self.err_ignore = err_ignore

    def copy(self) -> "Sequence[*Ts]":
        if all((isinstance(t, SimpleCopy) for t in self.tasks)):
            return self
        return Sequence(
            *(t.copy() for t in self.tasks),
            msg=self.msg,
            err_ignore=self.err_ignore
        )

    @property
    def current(self) -> Base[result.Result] | Self:
        return self.__current

    async def exchange(self, c: Client) -> result.Sequence[*Ts] | result.Error:
        res = result.Sequence()
        for t in self.tasks:
            self.__current = t
            if isinstance(res_one := await t.exchange(c), result.Error):
                if self.err_ignore:
                    res_one = res_one.with_msg(self.msg)
                else:
                    return res_one
            res = res.add(res_one)
        return cast("result.Sequence[*Ts]", res)


@dataclass(frozen=True)
class SetLocalTime(SimpleCopy, OK):
    """without decide time transfer"""
    msg: str = "set local time"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        clock_obj: Clock = c.objects.get_object("0.0.1.0.0.255")
        if isinstance(res := await ReadAttribute(
            ln=clock_obj.logical_name,
            index=3
        ).exchange(c), result.Error):
            return ret
        delta = datetime.timedelta(minutes=int(res.value))
        dt = cst.OctetStringDateTime(datetime.datetime.now(datetime.UTC)+delta)
        if isinstance(res := await WriteAttribute(
            ln=clock_obj.logical_name,
            index=2,
            value=dt.encoding
        ).exchange(c), result.Error):
            return res
        return result.OK


@dataclass(frozen=True)
class GetFirmwareVersion(SimpleCopy, CDT):
    msg: str = "get firmware version"

    async def exchange(self, c: Client) -> result.SimpleOrError[cdt.CommonDataType]:
        return await Par2Data(Parameter(c.objects.id.f_ver.par[:6]).get_attr(c.objects.id.f_ver.par[6])).exchange(c)


@dataclass(frozen=True)
class ReadByDescriptor(SimpleCopy, Simple[bytes]):
    desc: ut.CosemMethodDescriptor
    msg: str = "get encoding by Cosem-Attribute-Descriptor"

    async def exchange(self, c: Client) -> result.SimpleOrError[bytes]:
        c.get_get_request_normal(self.desc)
        return await c.read_data_block()


@dataclass(frozen=True)
class FindFirmwareVersion(SimpleCopy, Simple[collection.ParameterValue]):
    msg: str = "try find COSEM server version, return: instance(B group), CDT"

    async def exchange(self, c: Client) -> result.SimpleOrError[collection.ParameterValue]:
        err = result.ErrorAccumulator()
        for desc in (ut.CosemAttributeDescriptor((1, "0.0.0.2.1.255", 2)), ut.CosemAttributeDescriptor((1, "0.0.96.1.2.255", 2))):
            if isinstance(res_read := await ReadByDescriptor(desc).exchange(c), result.Error):
                err.append_err(res_read.err)
                in_e, out_e = res_read.err.split(exc.ResultError)
                if (
                    out_e is None
                    and in_e.exceptions[0].result == pdu.DataAccessResult(4)
                ):
                    continue
                else:
                    return res_read
            else:
                res = result.Simple(collection.ParameterValue(
                    par=desc.instance_id.contents + desc.attribute_id.contents,
                    value=res_read.value
                ))
                res.propagate_err(err)
                return res
        return err.as_error()


@dataclass(frozen=True)
class FindFirmwareId(SimpleCopy, Simple[collection.ParameterValue]):
    msg: str = "find firmaware Identifier"

    async def exchange(self, c: Client) -> result.SimpleOrError[collection.ParameterValue]:
        err = result.ErrorAccumulator()
        for desc in (ut.CosemAttributeDescriptor((1, "0.0.0.2.0.255", 2)), ut.CosemAttributeDescriptor((1, "0.0.96.1.1.255", 2))):
            if isinstance(res_read := await ReadByDescriptor(desc).exchange(c), result.Error):
                err.append_err(res_read.err)
                in_e, out_e = res_read.err.split(exc.ResultError)
                if (
                    out_e is None
                    and in_e.exceptions[0].result == pdu.DataAccessResult(4)
                ):
                    continue
                else:
                    return res_read
            else:
                res = result.Simple(collection.ParameterValue(
                    par=desc.instance_id.contents + desc.attribute_id.contents,
                    value=res_read.value
                ))
                res.propagate_err(err)
                return res
        return err.as_error()


@dataclass(frozen=True)
class KeepAlive(SimpleCopy, OK):
    msg: str = "keep alive(read LND.ln)"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance(res := await Par2Data(dlms_par.LDN.value).exchange(c), result.Error):
            return res
        return result.OK


class GetLDN(SimpleCopy, CDT[octet_string.LDN]):
    """:return LDN value"""
    msg: str = "get LDN"

    async def exchange(self, c: Client) -> result.SimpleOrError[octet_string.LDN]:
        if isinstance(res := await ReadByDescriptor(collection.AttrDesc.LDN_VALUE).exchange(c), result.Error):
            return res
        return result.Simple(octet_string.LDN(res.value))


# todo: possible implementation ConditionalTask
# def compare_ldn(man: bytes, ldn: octet_string.LDN) -> bool:
#     return man == ldn.get_manufacturer()
#
#
# check_LDN = ConditionalTask(
#     precondition_task=GetLDN,
#     comp_value=b"KPZ",
#     predicate=compare_ldn,
#     main_task=None
# )


@dataclass
class MatchLDN(OK):
    universal: bool = field(default=False)
    msg: str = "matching LDN"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance((res := await GetLDN().exchange(c)), result.Error):
            return res.with_msg("match LDN")
        if c.objects.LDN.value is None:
            c._objects.LDN.set_attr(2, res.value)
        elif c._objects.LDN.value == res.value:
            """secret matching"""
        elif self.universal:
            c.log(logL.WARN, F"connected to other server, change LDN")
            await init_type.exchange(c)  # todo: maybe set spec?
        else:
            return result.Error(exc.IDError(F"got {res.value=}, expected {c._objects.LDN.value}"))
        return result.OK


match_ldn = MatchLDN()
change_ldn = MatchLDN(universal=True)


@dataclass
class Lock:
    __lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)
    piece: float = field(default=0.8)
    name: str = ""

    async def acquire(self, c: Client):
        keep_alive = KeepAlive(self.name)
        while True:
            try:
                await asyncio.wait_for(self.__lock.acquire(), c.com_profile.parameters.inactivity_time_out * self.piece)  # todo: make not custom <inactivity_time_out>
                return
            except TimeoutError as e:
                await keep_alive.exchange(c)

    def release(self):
        self.__lock.release()


@dataclass
class CreateType(SimpleCopy, Simple[collection.Collection]):
    col_id: collection.ID
    msg: str = "CreateType".__class__.__name__
    obj_list: Optional[cdt.Array] = None
    wait_list: asyncio.Lock = field(init=False)
    """wait <object list>"""
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    col: collection.Collection = field(init=False)

    def __post_init__(self):
        self.col = collection.Collection(id_=self.col_id)
        """common collection"""
        self.wait_list = Lock(name="wait <object list>")

    async def exchange(self, c: Client) -> result.Simple[collection.Collection]:
        res = result.Simple(self.col)
        await self.wait_list.acquire(c)
        try:
            if self.obj_list is None:
                if isinstance(res_obj_list := await ReadByDescriptor(collection.AttrDesc.OBJECT_LIST).exchange(c), result.Error):
                    return res_obj_list
                self.obj_list = cdt.Array(res_obj_list.value, type_=structs.ObjectListElement)
            if len(self.col) == 0:
                for country_olel in filter(lambda it: ln_pattern.COUNTRY_SPECIFIC == it.logical_name, self.obj_list):
                    self.col.set_country(collection.CountrySpecificIdentifiers(country_olel.logical_name.d))
                    c.log(logL.INFO, F"set country: {self.col.country}")
                    match self.col.country:
                        case collection.CountrySpecificIdentifiers.RUSSIA:
                            country_desc = collection.AttrDesc.SPODES_VERSION
                        case _:
                            country_desc = None
                    if (
                        country_desc is not None
                        and next(filter(lambda it: country_desc.instance_id.contents == it.logical_name.contents, self.obj_list), False)
                    ):
                        if isinstance(res_country_ver := await ReadByDescriptor(country_desc).exchange(c), result.Error):
                            return res_country_ver
                        self.col.set_country_ver(collection.ParameterValue(
                            par=country_desc.instance_id.contents + country_desc.attribute_id.contents,
                            value=res_country_ver.value
                        ))
                        c.log(logL.INFO, F"set country version: {self.col.country_ver}")
                    else:
                        c.log(logL.WARN, "was not find <country specific code version> in object_list")
                    break
                else:
                    c.log(logL.WARN, "was not find <country specific code> in object_list")
                self.col.spec_map = self.col.get_spec()
                for o_l_el in self.obj_list:
                    o_l_el: structs.ObjectListElement
                    try:
                        self.col.add_if_missing(  # todo: remove add_if?
                            class_id=ut.CosemClassId(int(o_l_el.class_id)),
                            version=o_l_el.version,
                            logical_name=o_l_el.logical_name)
                    except collection.CollectionMapError as e:
                        res.append_err(e)
                self.col.add_if_missing(
                    class_id=overview.ClassID.DATA,
                    version=None,                                                                   # todo: check version else set 0
                    logical_name=cst.LogicalName.from_obis("0.0.42.0.0.255"))                       # todo: make better
            for ass in self.col.iter_classID_objects(overview.ClassID.ASSOCIATION_LN):
                ass: collection.AssociationLN
                if ass.logical_name.e != 0:
                    await ReadObjAttr(ass, 3).exchange(c)  # todo: remove from self.queue
                    if ass.associated_partners_id.client_SAP == c.SAP:
                        cur_ass = ass
                        break
            else:  # use current association if no variant
                cur_ass = self.col.add_if_missing(
                    class_id=overview.ClassID.ASSOCIATION_LN,
                    version=None,
                    logical_name=cst.LogicalName.from_obis("0.0.40.0.0.255")
                )
                await ReadObjAttr(cur_ass, 3).exchange(c)
            cur_ass.set_attr(2, self.obj_list)
            if cur_ass.associated_partners_id.client_SAP != c.SAP:
                c.log(logL.ERR, F"Wrong current server SAP: {c.SAP} use {cur_ass.associated_partners_id.client_SAP}")
            self.queue.put_nowait((cur_ass, 3))  # read forcibly <associated_partners_id>: use in MapTypeCreator(by <has_sap> method)
            reduce_ln = ln_pattern.LNPattern.parse("0.0.(40,42).0.0.255")
            """reduced objects for read"""
            for o_l_el in cur_ass.object_list:  # todo: read necessary data for create_type
                if reduce_ln == o_l_el.logical_name:
                    """nothing do it"""
                else:
                    if (obj := self.col.get(o_l_el.logical_name.contents)) is None:
                        continue
                    for access in o_l_el.access_rights.attribute_access:
                        i = int(access.attribute_id)
                        if (
                            i == 1                                                                      # skip LN
                            or not access.access_mode.is_readable()                                     # skip not readable
                            or (                                                                        # skip early gotten object_list
                                cur_ass.logical_name == o_l_el.logical_name
                                and i == 2
                            ) or (
                                access.access_mode.is_writable()                                        # skip unknown type writable element
                                and not (                                                               # except for:
                                    isinstance(obj.get_attr_element(i).DATA_TYPE, ut.CHOICE)
                                    or (
                                        isinstance(obj, collection.ProfileGeneric)
                                        and i == 3)
                                )
                            ) or obj.get_attr_element(i).classifier == collection.ic.Classifier.DYNAMIC  # skip DYNAMIC
                        ):
                            continue
                        self.queue.put_nowait((obj, i))
            for d_id in collection.get_filtered(
                    objects=self.col,
                    keys=(
                            ln_pattern.DEVICE_ID,
                            ln_pattern.PROGRAM_ENTRIES)):
                self.queue.put_nowait((d_id, 2))  # todo: make second queue2 for ReadEmptyAttribute(d_id.logical_name, 2).exchange(c)
        except TimeoutError as e:
            c.log(logL.ERR, F"can't got <object list>: {e}")
        finally:
            self.wait_list.release()
        while True:
            try:
                obj, i = self.queue.get_nowait()
            except asyncio.QueueEmpty as e:
                c.log(logL.INFO, "QueueEmpty")
                try:
                    await asyncio.wait_for(self.queue.join(), c.com_profile.parameters.inactivity_time_out)  # todo: why whis timeout??  # todo: make not custom <inactivity_time_out>
                    break
                except TimeoutError as e:
                    c.log(logL.INFO, "wait returned tasks in queue")
                    continue  # wait returned tasks in queue
            try:
                await c.read_attribute(obj, i)
            except TimeoutError as e:
                c.log(logL.ERR, F"return {obj}:{i} in queue: {e}")
                await self.queue.put((obj, i))
            except exc.Timeout as e:
                c.log(logL.ERR, F"break create type {self.col} by {e}")
                await self.queue.put((obj, i))
                raise e
            except AttributeError as e:
                c.log(logL.ERR, F"skip value wrong value for {obj}:{i}: {e}")
            except Exception as e:  # todo: make better!!!
                c.log(logL.ERR, F"skip value wrong value for {obj}:{i}: {e}")
            finally:
                self.queue.task_done()
        print("stop create")
        return res


type ID_SAP = tuple[collection.ID, enums.ClientSAP]


@dataclass(frozen=True)
class IDSAP:
    id: collection.ID
    sap: enums.ClientSAP


@dataclass
class NonInit:
    msg: str

    def __getattr__(self, item):
        raise RuntimeError(self.msg)


class MapTypeCreator:
    adapter: Adapter
    lock: asyncio.Lock
    con: dict[[IDSAP], CreateType]

    def __init__(self, adapter: Adapter):
        self.adapter = adapter
        self.con = dict()
        self.lock = asyncio.Lock()

    async def get_collection(
            self,
            c: Client,
            col_id: collection.ID
    ) -> result.Simple[collection.Collection]:
        new_col: collection.Collection
        err: Errors
        id_sap = IDSAP(col_id, c.SAP)
        async with self.lock:
            if id_sap in self.con.keys():
                c.log(logL.INFO, F"{self.__class__.__name__} {col_id} already in container")
            else:
                c.log(logL.INFO, F"{self.__class__.__name__} register new collection: {col_id}")
                self.con[id_sap] = CreateType(col_id)
        res = await self.con[id_sap].exchange(c)
        async with self.lock:
            try:
                gotten, _ = self.adapter.get_collection(col_id).unpack()  # check for first update
                if gotten.has_sap(id_sap.sap):
                    """not need keep"""
                else:
                    self.adapter.set_collection(res.value)  # todo: make as ADAPTER.merge_collection(ret)
            except AdapterException as e:
                self.adapter.set_collection(res.value)
        res.value, err = res.value.copy().unpack()
        if err is not None:
            res.extend_err(err)
        return res


@dataclass
class InitType(SimpleCopy, Simple[collection.Collection]):
    adapter: Adapter
    msg: str = "initiate type"

    async def exchange(self, c: Client) -> result.SimpleOrError[collection.Collection]:
        if isinstance((res := await Sequence(
            GetLDN(),
            FindFirmwareId(),
            FindFirmwareVersion(),
            msg="get collection.ID",
        ).exchange(c)), result.Error):
            return res.with_msg("init type")
        ldn, f_id, f_ver = res.value
        col_id = collection.ID(ldn.get_manufacturer(), f_id, f_ver)
        try:
            if (res := self.adapter.get_collection(col_id)).value.has_sap(c.SAP):
                c.log(logL.INFO, F"find collection in {self.adapter}")
            else:
                raise AdapterException(F"was found collection from adapter with absent current {c.SAP}")
        except AdapterException as e:
            c.log(logL.WARN, F"not find into adapter: {e}")
            res = await map_type_creator.get_collection(
                c=c,
                col_id=col_id
            )
        c._objects = res.value
        c._objects.LDN.set_attr(2, ldn)
        return res


init_type: InitType
"""init after get_adapter"""
map_type_creator: MapTypeCreator
"""init after get_adapter"""


def get_adapter(value: Adapter):
    global map_type_creator, init_type
    map_type_creator = MapTypeCreator(value)
    init_type = InitType(value)


get_adapter(gag)  # Dummy Adapter


@dataclass
@deprecated("use <ReadObjAttr>")
class ReadAttribute(SimpleCopy, CDT):
    ln: collection.LNContaining
    index: int
    msg: str = "read LN attribute"

    async def exchange(self, c: Client) -> result.Simple[cdt.CommonDataType]:
        obj = c.objects.get_object(self.ln)
        return await ReadObjAttr(obj, self.index).exchange(c)


@dataclass
class ReadObjAttr(SimpleCopy, CDT):
    obj: collection.InterfaceClass
    index: int
    msg: str = "read object attribute"

    async def exchange(self, c: Client) -> result.SimpleOrError[cdt.CommonDataType]:
        # TODO: check is_readable?
        c.get_get_request_normal(
            attr_desc=self.obj.get_attr_descriptor(
                value=self.index,
                with_selection=bool(c.negotiated_conformance.selective_access)))
        start_read_time: float = time.perf_counter()
        if isinstance(res_pdu := await c.read_data_block(), result.Error):
            return res_pdu
        c.last_transfer_time = datetime.timedelta(seconds=time.perf_counter()-start_read_time)
        try:
            self.obj.set_attr(self.index, res_pdu.value)
            return result.Simple(self.obj.get_attr(self.index))
        except ValueError as e:
            return result.Error.from_e(e)
        except ut.UserfulTypesException as e:
            return result.Error.from_e(e)
        except exc.DLMSException as e:
            return result.Error.from_e(e)


@dataclass(frozen=True)
class Par2Data[T: cdt.CommonDataType](SimpleCopy, CDT[T]):
    """get CommonDataType by Parameter"""
    par: Parameter
    msg: str = "read data by Parameter"

    async def exchange(self, c: Client) -> result.SimpleOrError[T]:
        if isinstance((res_obj := c.objects.par2obj(self.par)), result.Error):
            return res_obj
        if isinstance((res := await ReadObjAttr(res_obj.value, self.par.i).exchange(c)), result.Error):
            return res
        for el in self.par.elements():
            res.value = res.value[el]
        return res


class ReadSequence(List):
    tasks: list[ReadAttribute]

    def __post_init__(self):
        assert all((isinstance(t, ReadAttribute) for t in self.tasks))


type AttrValueComp = Callable[[cdt.CommonDataType | None], bool]


def is_empty(value: cdt.CommonDataType | None) -> bool:
    """is empty attribute value"""
    return True if value is None else False


@dataclass(frozen=True)
class ReadAttributeIf(SimpleCopy, Base):
    """read if func with arg as value is True"""
    ln: collection.LNContaining
    index: int
    func: AttrValueComp
    msg: str = "read attribute with condition"

    async def exchange(self, c: Client) -> result.Simple[cdt.CommonDataType]:
        # TODO: check is_readable
        obj = c.objects.get_object(self.ln)
        if self.func(obj.get_attr(self.index)):
            return await ReadAttribute(
                ln=self.ln,
                index=self.index).exchange(c)
        else:
            return result.OK


@dataclass(frozen=True)
class ReadEmptyAttribute(SimpleCopy, Base):
    ln: collection.LNContaining
    index: int
    msg: str = "read if attribute is empty"

    async def exchange(self, c: Client) -> result.Simple[cdt.CommonDataType]:
        # TODO: check is_readable
        return await ReadAttributeIf(
            ln=self.ln,
            index=self.index,
            func=is_empty
        ).exchange(c)


@dataclass(frozen=True)
class ReadWritableAttributes(SimpleCopy, Base):
    ln: collection.LNContaining
    indexes: tuple[int, ...]
    msg: str = "read only writable attribute"

    async def exchange(self, c: Client) -> result.List[cdt.CommonDataType]:
        # TODO: check is_readable
        res = result.List()
        indexes: list[int] = []
        ass: collection.AssociationLN = c._objects.sap2association(c.SAP)
        for i in self.indexes:
            if ass.is_writable(self.ln, i):
                indexes.append(i)
        if len(indexes) != 0:
            res.append(await ReadAttributes(
                ln=self.ln,
                indexes=tuple(indexes)
            ).exchange(c))
        else:
            res.append(result.OK)
            c.log(logL.INFO, F"skip {self.__class__.__name__} operation, all is actually")
        return res


# copy past from ReadWritableAttributes
@dataclass(frozen=True)
class ActualizeAttributes(SimpleCopy, OK):
    ln: collection.LNContaining
    indexes: tuple[int, ...]
    msg: str = "read if attribute is empty or writable"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        # TODO: check is_readable
        ass: collection.AssociationLN = c.objects.sap2association(c.SAP)
        obj = c.objects.get_object(self.ln)
        indexes = [
            i for i in self.indexes if (
                obj.get_attr(i) is None
                or obj.get_attr_element(i).classifier == ic.Classifier.DYNAMIC
                or ass.is_writable(self.ln, i)
            )
        ]
        if len(indexes) != 0:
            if isinstance((res := await ReadAttributes(
                ln=self.ln,
                indexes=tuple(indexes)
            ).exchange(c)), result.Error):
                return res
        return result.OK


@dataclass(frozen=True)
class ReadAttributes(SimpleCopy, _List[cdt.CommonDataType]):
    ln: collection.LNContaining
    indexes: tuple[int, ...]
    msg: str = ""

    async def exchange(self, c: Client) -> result.List[cdt.CommonDataType] | result.Error:
        res = result.List()
        obj = c.objects.get_object(self.ln)
        # TODO: check for Get-Request-With-List
        for i in self.indexes:
            res.append(await ReadObjAttr(obj, i).exchange(c))
        return res


@dataclass
@deprecated("use <Write2>")
class Write(SimpleCopy, OK):
    """write with ParameterData struct"""
    par_data: ParData
    msg: str = "write attribute"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance(res_obj := c.objects.par2obj(self.par_data.par), result.Error):
            return res_obj
        if self.par_data.par.n_elements == 0:
            enc = self.par_data.data.encoding
        elif isinstance(res_read := await ReadObjAttr(res_obj.value, self.par_data.par.i).exchange(c), result.Error):
            return res_read
        else:
            data = a_data
            for el in self.par_data.par.elements():
                data = data[el]
            data.set(self.par_data.data)
            enc = data.encoding
        data = c.get_set_request_normal(
            obj=res_obj.value,
            attr_index=self.par_data.par.i,
            value=enc)
        if isinstance(res_pdu := await c.read_data_block(), result.Error):
            return res_pdu
        return result.OK


@dataclass(frozen=True)
class Write2(SimpleCopy, OK):
    """write with ParameterData struct"""
    par: Parameter
    data: cdt.CommonDataType
    msg: str = "write Data"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance(res_obj := c.objects.par2obj(self.par), result.Error):
            return res_obj
        if self.par.n_elements == 0:
            enc = self.data.encoding
        elif isinstance(res_read := await Par2Data[cdt.CommonDataType](self.par.attr).exchange(c), result.Error):
            return res_read
        else:
            data = res_read.value
            for el in self.par.elements():
                data = data[el]
            data.set(self.data)
            enc = data.encoding
        data = c.get_set_request_normal(
            obj=res_obj.value,
            attr_index=self.par.i,
            value=enc)
        if isinstance(res_pdu := await c.read_data_block(), result.Error):
            return res_pdu
        return result.OK


@dataclass
@deprecated("use <WriteTranscript>")
class WriteParValue(SimpleCopy, OK):
    """write with ParameterValues struct"""
    par_value: ParValues[cdt.Transcript]
    msg: str = "write attribute by Transcript"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance(res1 := c.objects.par2obj(self.par_value.par), result.Error):
            return res1
        obj = res1.value
        if (a_data := res1.value.get_attr(self.par_value.par.i)) is None:
            if isinstance((res := await Par2Data(self.par_value.par).exchange(c)), result.Error):
                return res
            else:
                a_data = res.value
        s_u = c._objects.par2su(self.par_value.par)
        if isinstance(s_u, cdt.ScalUnitType):
            value: cdt.Transcript = str(float(self.par_value.data) * 10 ** -int(s_u.scaler))
        else:
            value = self.par_value.data
        if self.par_value.par.n_elements == 0:
            set_data = a_data.parse(value)
        elif isinstance((res := await Par2Data(par).exchange(c)), result.Error):
            return res
        else:
            data = a_data
            for el in self.par_value.par.elements():
                data = data[el]
            new_data = data.parse(value)  # todo: can't use with CHOICE
            data.set(new_data)
            set_data = a_data
        data = c.get_set_request_normal(
            obj=obj,
            attr_index=self.par_value.par.i,
            value=set_data.encoding)
        if isinstance(res_pdu := await c.read_data_block(), result.Error):
            return res_pdu
        return result.OK


@dataclass
@deprecated("use <Write>")
class WriteAttribute(SimpleCopy, OK):
    ln: collection.LNContaining
    index: int
    value: bytes | str | int | list | tuple | datetime.datetime
    msg: str = ""

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        obj = c._objects.get_object(self.ln)
        if isinstance(self.value, (str, int, list, tuple, datetime.datetime)):
            value2 = await c.encode(
                obj=obj,
                index=self.index,
                value=self.value)
            enc = value2.encoding
        else:
            enc = self.value
        data = c.get_set_request_normal(
            obj=obj,
            attr_index=self.index,
            value=enc)
        if isinstance(res_pdu := await c.read_data_block(), result.Error):
            return res_pdu
        return result.OK  # todo: return Data-Access-Result


@deprecated("use Execute")
@dataclass
class ExecuteByDesc(SimpleCopy, Base):
    """execute method by method descriptor # TODO: rewrite this"""
    desc: ut.CosemMethodDescriptor
    msg: str = "old execute"

    async def exchange(self, c: Client) -> result.Result:
        try:
            await c.execute_method(self.desc)
            return result.Simple(pdu.ActionResult.SUCCESS)
        except Exception as e:
            return result.Error.from_e(exc.DLMSException(F'Исполнение {self.desc}'))


@deprecated("use Execute2")
@dataclass
class Execute(SimpleCopy, OK):
    """execute method"""
    ln: collection.LNContaining
    index: int
    value: cdt.CommonDataType = None  # todo: maybe use simple bytes
    msg: str = "execute method"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        obj = c._objects.get_object(self.ln)
        try:
            await c.execute_method2(obj, self.index, self.value)
            return result.OK
        except Exception as e:
            return result.Error.from_e(exc.DLMSException(F'Исполнение {self.desc}'))


@dataclass(frozen=True)
class Execute2(SimpleCopy, OK):
    """execute method"""
    par: Parameter
    data: cdt.CommonDataType
    msg: str = "Execute method"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance(res := c.objects.par2obj(self.par), result.Error):
            return res
        try:
            data = c.get_action_request_normal(
                meth_desc=res.value.get_meth_descriptor(self.par.i),
                method=self.data
            )
            if isinstance(res_pdu := await c.read_data_block(), result.Error):
                return res_pdu
            return result.OK
        except Exception as e:
            return result.Error.from_e(e)


class WriteTime(SimpleCopy, Base):
    msg: str = "write Clock.time depend from transfer time"

    async def exchange(self, c: Client):
        try:
            obj = c._objects.clock
            c.get_get_request_normal(obj.get_attr_descriptor(3))
            if isinstance(res_pdu := await c.read_data_block(), result.Error):
                return res_pdu
            tz = obj.get_attr_element(3).DATA_TYPE(res_pdu.value)
            res = await WriteAttribute(
                ln=obj.logical_name,
                index=2,
                value=(datetime.datetime.utcnow() + datetime.timedelta(minutes=int(tz)) + c.last_transfer_time)
            ).exchange(c)
            return res
        except Exception as e:
            # logger.info(F'ERROR: write Clock: attribute 2 {e}')
            return result.Error.from_e(exc.DLMSException(F"write time: {e}"))


@dataclass
class ImageTransfer(SimpleCopy, StrictOK):
    par: dlms_par.ImageTransfer
    image: bytes
    waiting_for_activation: float = 10.0
    n_t_b: int = field(init=False, default=0)
    """not transferred block"""
    n_blocks: int = field(init=False)
    msg: str = "image transfer"

    def __post_init__(self) -> None:
        self.ITI = ImageTransferInitiate((
            bytearray(hashlib.md5(self.image).digest()),  # todo: make custom this
            cdt.DoubleLongUnsigned(len(self.image))
        ))

    async def exchange(self, c: Client) -> result.StrictOk | result.Error:
        """ update image if blocks is fulls ver 3"""
        offset: int
        res_block_size: result.SimpleOrError[cdt.DoubleLongUnsigned]
        res_status: result.SimpleOrError[i_t_status.ImageTransferStatus]
        res_activate_info: result.SimpleOrError[ImageToActivateInfo]
        res_ntb: result.SimpleOrError[cdt.DoubleLongUnsigned]
        res_tbs: result.SimpleOrError[cdt.BitString]
        previous_status: Optional[i_t_status.ImageTransferStatus] = None
        res = result.StrictOk()
        if isinstance(res_block_size := await Par2Data(self.par.image_block_size).exchange(c), result.Error):
            return res_block_size
        block_size = int(res_block_size.value)
        self.n_blocks, mod = divmod(len(self.image), block_size)
        if mod != 0:
            self.n_blocks += 1
        # TODO: need common counter for exit from infinity loop
        if isinstance(res_status := await Par2Data(self.par.image_transfer_status).exchange(c), result.Error):
            return res_status
        if isinstance(res_activate_info := await Par2Data(self.par.image_to_activate_info).exchange(c), result.Error):
            return res_activate_info
        if (
            res_status.value in (i_t_status.TRANSFER_NOT_INITIATED, i_t_status.VERIFICATION_FAILED, i_t_status.ACTIVATION_FAILED)
            or len(res_activate_info.value) == 0
            or res_activate_info.value[0].image_to_activate_identification != self.ITI.image_identifier
        ):
            if isinstance(res_initiate := await Execute2(self.par.image_transfer_initiate, self.ITI).exchange(c), result.Error):
                return res_initiate
            c.log(logL.INFO, "Start initiate Image Transfer")
            if isinstance(res_status := await Par2Data(self.par.image_transfer_status).exchange(c), result.Error):
                return res_status
        elif res_status.value == i_t_status.ACTIVATION_SUCCESSFUL:
            # image in outside memory and already activated early, but erased by hard programming. Need again go to activation
            res_status.value = i_t_status.VERIFICATION_SUCCESSFUL
        else:
            c.log(logL.INFO, "already INITIATED")
            if isinstance(res_ntb := await Par2Data(self.par.image_first_not_transferred_block_number).exchange(c), result.Error):
                return res_ntb
            self.n_t_b = int(res_ntb.value)
            if self.n_t_b > (len(self.image) / block_size):  # all blocks were send
                if isinstance(res_verify := await VerifyImage(self.par).exchange(c), result.Error):
                    return res_verify
                c.log(logL.INFO, "Start Verify Transfer")
        while True:
            c.log(logL.STATE, F"{res_status.value=}")
            match res_status.value:
                case i_t_status.VERIFICATION_FAILED if res_status.value == previous_status:
                    return result.Error.from_e(exc.DLMSException(), "Verification Error")
                case i_t_status.TRANSFER_INITIATED if res_status.value == previous_status:
                    res.append_e(exc.DLMSException("Expected Switch to Verification Initiated status, got Initiated"))
                case i_t_status.TRANSFER_NOT_INITIATED:
                    res.append_e(exc.DLMSException("Got Not initiated status after call Initiation"))
                case i_t_status.TRANSFER_INITIATED:
                    while self.n_t_b < self.n_blocks:
                        offset = self.n_t_b * block_size
                        if isinstance(res_tr_block := await TransferBlock(
                            par=self.par,
                            number=cdt.DoubleLongUnsigned(self.n_t_b),
                            value=cdt.OctetString(bytearray(self.image[offset: offset + block_size]))
                        ).exchange(c), result.Error):
                            return res_tr_block
                        self.n_t_b += 1  # todo: maybe get from SERVER - await get_not_transferred_block.exchange(c)
                    c.log(logL.INFO, "All blocks transferred")
                    if isinstance(res_verify := await VerifyImage(self.par).exchange(c), result.Error):
                        return res_verify
                case i_t_status.VERIFICATION_INITIATED:
                    c.log(logL.INFO, "read bitstring. It must grow")
                    # TODO: calculate time for waiting or read growing bitstring ?
                    if isinstance(res_tbs := await Par2Data(self.par.image_transferred_blocks_status).exchange(c), result.Error):
                        return res_tbs
                    if len(res_tbs.value) < self.n_t_b:
                        c.log(logL.INFO, F"Got blocks[{len(res_tbs.value)}]")  # todo: remove
                    else:
                        c.log(logL.INFO, "All Bits solved")
                case i_t_status.VERIFICATION_FAILED:
                    if isinstance(res_tbs := await Par2Data(self.par.image_transferred_blocks_status).exchange(c), result.Error):
                        return res_tbs
                    valid = tuple(res_tbs.value)
                    c.log(logL.INFO, F"Got blocks[{len(res_tbs.value)}]")  # todo: remove
                    for i in filter(lambda it: valid[it] == b'\x00', range(len(valid))):
                        offset = i * block_size
                        if isinstance(res_tr_block := await TransferBlock(
                            par=self.par,
                            number=cdt.DoubleLongUnsigned(i),
                            value=cdt.OctetString(bytearray(self.image[offset: offset + block_size]))
                        ).exchange(c), result.Error):
                            return res_tr_block
                    if isinstance(res_verify := await VerifyImage(self.par).exchange(c), result.Error):
                        return res_verify
                    c.log(logL.INFO, "Start Verify Transfer")
                case i_t_status.VERIFICATION_SUCCESSFUL:
                    if isinstance(res_tbs := await Par2Data(self.par.image_transferred_blocks_status).exchange(c), result.Error):
                        return res_tbs
                    valid = tuple(res_tbs.value)
                    if isinstance(res_ntb := await Par2Data(self.par.image_first_not_transferred_block_number).exchange(c), result.Error):
                        return res_ntb
                    self.n_t_b = int(res_ntb.value)
                    if isinstance(res_activate_info := await Par2Data(self.par.image_to_activate_info).exchange(c), result.Error):
                        return res_activate_info
                    c.log(logL.INFO, F"md5:{res_activate_info.value[0].image_to_activate_signature}")
                    if any(map(lambda it: it == b'\x00', valid)):
                        if isinstance(res_initiate := await Execute2(self.par.image_transfer_initiate, self.ITI).exchange(c), result.Error):
                            return res_initiate
                        c.log(logL.INFO, "Start initiate Image Transfer, after wrong verify. Exist 0 blocks")
                        return res.as_error(exc.DLMSException("Exist 0 blocks"))
                    elif self.n_t_b < len(valid):
                        if isinstance(res_initiate := await Execute2(self.par.image_transfer_initiate, self.ITI).exchange(c), result.Error):
                            return res_initiate
                        c.log(logL.INFO, "Start initiate Image Transfer, after wrong verify. Got not transferred block")
                        return res.as_error(exc.DLMSException(F"Got {res_ntb.value} not transferred block"))
                    elif res_activate_info.value[0].image_to_activate_signature != res_activate_info.value[0].image_to_activate_identification:
                        if isinstance(res_initiate := await Execute2(self.par.image_transfer_initiate, self.ITI).exchange(c), result.Error):
                            return res_initiate
                        return res.as_error(exc.DLMSException(
                            F"Signature not match to Identification: got {res_activate_info.value[0].image_to_activate_signature}, "
                            F"expected {res_activate_info.value[0].image_to_activate_identification}"),
                            "Start initiate Image Transfer, after wrong verify")
                    else:
                        if isinstance(res_activate := await ActivateImage(self.par).exchange(c), result.Error):
                            return res_activate
                        c.log(logL.INFO, "Start Activate Transfer")
                case i_t_status.ACTIVATION_INITIATED:
                    try:
                        await c.disconnect_request()
                    except TimeoutError as e:
                        c.log(logL.ERR, F"can't use <disconnect request>: {e}")
                    if isinstance(res_reconnect := await HardwareReconnect(
                            delay=self.waiting_for_activation,
                            msg="expected reboot server after upgrade"
                    ).exchange(c), result.Error):
                        return res_reconnect
                case i_t_status.ACTIVATION_SUCCESSFUL:
                    if isinstance(res_activate_info := await Par2Data(self.par.image_to_activate_info).exchange(c), result.Error):
                        return res_activate_info
                    if res_activate_info.value[0].image_to_activate_identification == self.ITI.image_identifier:
                        c.log(logL.INFO, "already activated this image")
                        return res
                    else:
                        if isinstance(res_initiate := await Execute2(self.par.image_transfer_initiate, self.ITI).exchange(c), result.Error):
                            return res_initiate
                        c.log(logL.INFO, "Start initiate Image Transfer")
                        # TODO: need wait clearing memory in device ~5 sec
                case i_t_status.ACTIVATION_FAILED:
                    return res.as_error(exc.DLMSException(), "Ошибка активации...")
                case err:
                    return res.as_error(exc.DLMSException(), f"Unknown image transfer status: {err}")
            previous_status = res_status.value
            await asyncio.sleep(1)  # TODO: tune it
            if isinstance(res_status := await Par2Data(self.par.image_transfer_status).exchange(c), result.Error):
                return res_status
            c.log(logL.INFO, f"{res_status.value=}")


@dataclass(frozen=True)
class TransferBlock(SimpleCopy, OK):
    par: dlms_par.ImageTransfer
    number: cdt.DoubleLongUnsigned
    value: cdt.OctetString
    msg: str = "transfer block"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance(res := await Execute2(
            par=self.par.image_block_transfer,
            data=ImageBlockTransfer((self.number, self.value))
        ).exchange(c), result.Error):
            return res
        return result.OK


@dataclass(frozen=True)
class VerifyImage(SimpleCopy, OK):
    par: dlms_par.ImageTransfer
    msg: str = "Verify image"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance(res := await Execute2(self.par.image_verify, integers.INTEGER_0).exchange(c), result.Error):
            return res
        return result.OK


@dataclass(frozen=True)
class ActivateImage(SimpleCopy, OK):
    par: dlms_par.ImageTransfer
    msg: str = "Activate image"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance(res := await Execute2(self.par.image_activate, integers.INTEGER_0).exchange(c), result.Error):
            return res
        return result.OK


# todo: don't work with new API, remake
class TestAll(OK):
    """read all attributes with check access"""  # todo: add Write with access
    msg: str = "test all"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        # todo: refactoring with <append_err>
        res = result.ErrorAccumulator()
        if isinstance(res_objects := c.objects.sap2objects(c.SAP), result.Error):
            return res_objects
        ass: collection.AssociationLN = c.objects.sap2association(c.SAP)
        for obj in res_objects.value:
            indexes: list[int] = [i for i, _ in obj.get_index_with_attributes()]
            c.log(logL.INFO, F"start read {obj} attr: {', '.join(map(str, indexes))}")
            for i in indexes:
                is_readable = ass.is_readable(
                    ln=obj.logical_name,
                    index=i)
                if isinstance(res_read := await ReadObjAttr(obj, i).exchange(c), result.Error):
                    if (
                        res_read.has(pdu.DataAccessResult.READ_WRITE_DENIED, exc.ResultError)
                        and not is_readable
                    ):
                        c.log(logL.INFO, F"success ReadAccess TEST")
                    else:
                        res.append_err(res_read.err)
                elif not is_readable:
                    res.append_e(PermissionError(f"{obj} with attr={i} must be unreadable"))
                    indexes.remove(i)
        return res.result


@dataclass
class ApplyTemplate(SimpleCopy, Base):
    template: collection.Template
    msg: str = "apply template"

    async def exchange(self, c: Client) -> result.Result:
        # todo: search col
        attr: cdt.CommonDataType
        res = result.StrictOk()
        for col in self.template.collections:
            if col == c.objects:
                use_col = col
                break
        else:
            c.log(logL.ERR, F"not find collection for {c}")
            raise asyncio.CancelledError()
        for ln, indexes in self.template.used.items():
            if (obj := res.propagate_err(use_col.logicalName2obj(ln))) is not None:
                for i in indexes:
                    if (attr := obj.get_attr(i)) is not None:
                        res.propagate_err(await WriteAttribute(
                            ln=ln,
                            index=i,
                            value=attr.encoding
                        ).exchange(c))
                    else:
                        res.append_e(exc.EmptyObj(F"skip apply {self.template} {ln}:{i}: no value"))
        return res


@dataclass
class ReadTemplate(OK):
    template: collection.Template
    msg: str = "read template"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        # todo: copypast from <ApplyTemplate>
        attr: cdt.CommonDataType
        res = result.ErrorAccumulator()
        for col in self.template.collections:
            if col == c._objects:
                use_col = col
                break
        else:
            c.log(logL.ERR, F"not find collection for {c}")
            raise asyncio.CancelledError()
        for ln, indexes in self.template.used.items():
            try:
                obj = use_col.get_object(ln)  # todo: maybe not need
            except exc.NoObject as e:
                c.log(logL.WARN, F"skip apply {self.template}: {e}")
                continue
            res.propagate_err(
                await ReadAttributes(
                    ln=ln,
                    indexes=tuple(indexes)
                ).exchange(c))
        return res.result


@dataclass
class AccessValidate(OK):
    """check all access rights for current SAP"""
    with_correct: bool = False
    msg: str = "all access validate"

    # todo: make with result.Error
    async def exchange(self, c: Client) -> result.Ok | result.Error:
        res = result.ErrorAccumulator()
        obj_l: ObjectListType
        el: ObjectListElement
        a_a_i: association_ln.abstract.AttributeAccessItem
        if (obj_l := c.objects.sap2association(c.SAP).object_list) is None:
            return result.Error.from_e(exc.EmptyObj(F"empty object_list for {c._objects.sap2association(c.SAP)}"))
        for el in obj_l:
            for a_a_i in el.access_rights.attribute_access:
                if a_a_i.access_mode.is_readable():
                    i = int(a_a_i.attribute_id)
                    if isinstance(res_read :=await ReadByDescriptor(ut.CosemAttributeDescriptor((
                            int(el.class_id),
                            el.logical_name.contents,
                            i
                    ))).exchange(c), result.Error):
                        res.append_err(res_read.err)
                        if self.with_correct:
                            a_a_i.access_mode.set(1)  # todo: make better in future
                    elif a_a_i.access_mode.is_writable():
                        if isinstance(res_write :=await WriteAttribute(
                            ln=el.logical_name,
                            index=i,
                            value=res_read.value
                        ).exchange(c), result.Error):
                            res.append_err(res_write.err)
        return res.result


@dataclass
@deprecated("use <WriteList>")
class WriteParDatas(SimpleCopy, _List[result.Ok]):
    """write by ParData list"""
    par_datas: list[ParData]
    msg: str = ""

    async def exchange(self, c: Client) -> result.List[result.Ok] | result.Error:
        res = result.List()
        for pardata in self.par_datas:
            res.append(await WriteAttribute(
                ln=pardata.par.ln,
                index=pardata.par.i,
                value=pardata.data.encoding
            ).exchange(c))
        return res


class WriteList(SimpleCopy, _List[result.Ok]):
    """write by list"""
    par_datas: tuple[tuple[Parameter, cdt.CommonDataType], ...]
    err_ignore: bool

    def __init__(self, *par_datas: tuple[Parameter, cdt.CommonDataType], err_ignore: bool = False, msg: str = "write list") -> None:
        self.par_datas = par_datas
        self.err_ignore = err_ignore
        self.msg = msg

    async def exchange(self, c: Client) -> result.List[result.Ok] | result.Error:
        res = result.List[result.Ok]()
        for par, data in self.par_datas:
            if (
                isinstance(res_one := await Write2(par, data).exchange(c), result.Error)
                and not self.err_ignore
            ):
                return res_one
            res.append(res_one)
        return res


@dataclass(frozen=True)
class WriteTranscript(SimpleCopy, OK):
    """write by ParValues[Transcript]"""
    par: Parameter
    value: cdt.Transcript
    msg: str = "write with transcript"

    async def exchange(self, c: Client) -> result.Ok | result.Error:
        if isinstance((res := await Par2Data[cdt.CommonDataType](self.par).exchange(c)), result.Error):
            return res
        if isinstance(res.value, cdt.Digital):
            s_u = c.objects.par2su(self.par)
            if isinstance(s_u, cdt.ScalUnitType):
                if not isinstance(self.value, str):
                    return result.Error.from_e(TypeError(), f"for {self.par} got type: {self.value}, expected String")
                try:
                    data = res.value.parse(value := str(float(self.value) * 10 ** -int(s_u.scaler)))
                except ValueError as e:
                    return result.Error.from_e(e, f"for {self.par} got value: {self.value}, expected Float or Digital")
            else:
                data = res.value.parse(self.value)
        else:
            data = res.value.parse(self.value)
        return await Write2(self.par, data).exchange(c)


class WriteTranscripts(SimpleCopy, _List[result.Ok]):
    """write by ParValues[Transcript] list"""
    par_values: tuple[tuple[Parameter, cdt.Transcript], ...]
    err_ignore: bool

    def __init__(self, *par_values: tuple[Parameter, cdt.Transcript], err_ignore: bool = False, msg: str ="write transcripts"):
        self.par_values = par_values
        self.err_ignore = err_ignore
        self.msg = msg

    async def exchange(self, c: Client) -> result.List[result.Ok] | result.Error:
        res = result.List[result.Ok]()
        for par, value in self.par_values:
            if (
                isinstance(res_one := await WriteTranscript(par, value).exchange(c), result.Error)
                and not self.err_ignore
            ):
                return res_one
            res.append(res_one)
        return res
