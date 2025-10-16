from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

__NAMESPACE__ = "http://schemas.nav.gov.hu/NTCA/1.0/common"


@dataclass
class BasicHeaderType:
    """
    A kérés tranzakcionális adatai Transactional data of the request.

    :ivar request_id: A kérés/válasz azonosítója, minden üzenetváltásnál
        - adószámonként - egyedi Identifier of the request/response,
        unique with the taxnumber in every data exchange transaction
    :ivar timestamp: A kérés/válasz keletkezésének UTC ideje UTC time of
        the request/response
    :ivar request_version: A kérés/válasz verziószáma, hogy a hívó
        melyik interfész verzió szerint küld adatot és várja a választ
        Request version number, indicating which datastructure the
        client sends data in, and in which the response is expected
    :ivar header_version: A header verziószáma Header version number
    """

    request_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "requestId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
            "min_length": 1,
            "max_length": 30,
            "pattern": r"[+a-zA-Z0-9_]{1,30}",
        },
    )
    timestamp: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,3})?Z",
        },
    )
    request_version: Optional[str] = field(
        default=None,
        metadata={
            "name": "requestVersion",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
            "min_length": 1,
            "max_length": 15,
        },
    )
    header_version: Optional[str] = field(
        default=None,
        metadata={
            "name": "headerVersion",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "min_length": 1,
            "max_length": 15,
        },
    )


class BusinessResultCodeType(Enum):
    """
    Üzleti eredmény kód típus Business result code type.

    :cvar ERROR: Hiba Error
    :cvar WARN: Figyelmeztetés Warn
    :cvar INFO: Tájékoztatás Information
    """

    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


@dataclass
class CryptoType:
    """
    Kriptográfiai metódust leíró típus Denoting type of cryptographic method.
    """

    value: str = field(
        default="",
        metadata={
            "required": True,
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    crypto_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "cryptoType",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )


class FunctionCodeType(Enum):
    """
    Funkciókód típus Function code type.

    :cvar OK: Sikeres művelet Successful operation
    :cvar ERROR: Hiba Error
    """

    OK = "OK"
    ERROR = "ERROR"


@dataclass
class NotificationType:
    """
    Értesítés Notification.

    :ivar notification_code: Értesítés kód Notification code
    :ivar notification_text: Értesítés szöveg Notification text
    """

    notification_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "notificationCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )
    notification_text: Optional[str] = field(
        default=None,
        metadata={
            "name": "notificationText",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
            "min_length": 1,
            "max_length": 1024,
            "pattern": r".*[^\s].*",
        },
    )


class TechnicalResultCodeType(Enum):
    """
    Technikai eredmény kód típus Technical result code type.

    :cvar CRITICAL: Kritikus hiba Critical error
    :cvar ERROR: Hiba Error
    """

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"


@dataclass
class NotificationsType:
    """
    Egyéb értesítések Miscellaneous notifications.

    :ivar notification: Értesítés Notification
    """

    notification: list[NotificationType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "min_occurs": 1,
        },
    )


@dataclass
class TechnicalValidationResultType:
    """
    Technikai validációs választípus Technical validation response type.

    :ivar validation_result_code: Validációs eredmény Validation result
    :ivar validation_error_code: Validációs hibakód Validation error
        code
    :ivar message: Feldolgozási üzenet Processing message
    """

    validation_result_code: Optional[TechnicalResultCodeType] = field(
        default=None,
        metadata={
            "name": "validationResultCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
        },
    )
    validation_error_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "validationErrorCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )
    message: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "min_length": 1,
            "max_length": 1024,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class UserHeaderType:
    """
    A kérés authentikációs adatai Authentication data of the request.

    :ivar login: A technikai felhasználó login neve Login name of the
        technical user
    :ivar password_hash: A technikai felhasználó jelszavának hash értéke
        Hash value of the technical user's password
    :ivar tax_number: A rendszerben regisztrált adózó adószáma, aki
        nevében a technikai felhasználó tevékenykedik The taxpayer's tax
        number, whose name the technical user operates in
    :ivar request_signature: A kérés aláírásának hash értéke Hash value
        of the request's signature
    """

    login: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
            "min_length": 6,
            "max_length": 15,
            "pattern": r"[a-zA-Z0-9]{6,15}",
        },
    )
    password_hash: Optional[CryptoType] = field(
        default=None,
        metadata={
            "name": "passwordHash",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
        },
    )
    tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "taxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    request_signature: Optional[CryptoType] = field(
        default=None,
        metadata={
            "name": "requestSignature",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
        },
    )


@dataclass
class BasicRequestType:
    """
    Alap kérés adatok Basic request data.

    :ivar header: A kérés tranzakcionális adatai Transactional data of
        the request
    :ivar user: A kérés authentikációs adatai Authentication data of the
        request
    """

    header: Optional[BasicHeaderType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
        },
    )
    user: Optional[UserHeaderType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
        },
    )


@dataclass
class BasicResultType:
    """
    Alap válaszeredmény adatok Basic result data.

    :ivar func_code: Feldolgozási eredmény Processing result
    :ivar error_code: A feldolgozási hibakód Processing error code
    :ivar message: Feldolgozási üzenet Processing message
    :ivar notifications: Egyéb értesítések Miscellaneous notifications
    """

    func_code: Optional[FunctionCodeType] = field(
        default=None,
        metadata={
            "name": "funcCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
        },
    )
    error_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "errorCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    message: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "min_length": 1,
            "max_length": 1024,
            "pattern": r".*[^\s].*",
        },
    )
    notifications: Optional[NotificationsType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
        },
    )


@dataclass
class BasicResponseType:
    """
    Alap válasz adatok Basic response data.

    :ivar header: A válasz tranzakcionális adatai Transactional data of
        the response
    :ivar result: Alap válaszeredmény adatok Basic result data
    """

    header: Optional[BasicHeaderType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
        },
    )
    result: Optional[BasicResultType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/NTCA/1.0/common",
            "required": True,
        },
    )


@dataclass
class GeneralExceptionResponse(BasicResultType):
    """
    Az összes REST operációra vonatkozó kivétel válasz generikus elementje General
    exception response of every REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/NTCA/1.0/common"


@dataclass
class GeneralErrorHeaderResponseType(BasicResponseType):
    """
    Általános hibatípus minden REST operációra Generic fault type for every REST
    operation.
    """


@dataclass
class GeneralErrorHeaderResponse(GeneralErrorHeaderResponseType):
    """
    Az összes REST operációra vonatkozó hibaválasz generikus elementje General
    error response of every REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/NTCA/1.0/common"
