from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class Scheme(StrEnum):
    HTTP = "http"
    HTTPS = "https"
    WS = "ws"
    WSS = "wss"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


SchemeT = TypeVar("SchemeT", bound=Scheme)
OptScheme = Scheme | None
OptSchemeT = TypeVar("OptSchemeT", bound=OptScheme)


class SchemeMixin(BaseModel, Generic[OptSchemeT]):
    scheme: Annotated[OptSchemeT, Field(..., description="Scheme")]


ListOfSchemes = list[Scheme]
ListOfSchemesT = TypeVar("ListOfSchemesT", bound=ListOfSchemes)
OptListOfSchemes = ListOfSchemes | None
OptListOfSchemesT = TypeVar("OptListOfSchemesT", bound=OptListOfSchemes)


class SchemesMixin(BaseModel, Generic[OptListOfSchemesT]):
    schemes: Annotated[OptListOfSchemesT, Field(..., description="Schemes")]


SeqOfSchemes = Sequence[Scheme]
SeqOfSchemesT = TypeVar("SeqOfSchemesT", bound=SeqOfSchemes)
OptSeqOfSchemes = SeqOfSchemes | None
OptSeqOfSchemesT = TypeVar("OptSeqOfSchemesT", bound=OptSeqOfSchemes)


class Protocol(StrEnum):
    HTTP = "http"
    WEBSOCKET = "websocket"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]

    @classmethod
    def from_scheme(cls, scheme: Scheme | str) -> "Protocol":
        # Normalize to Scheme if it's a string
        if isinstance(scheme, str):
            try:
                scheme = Scheme(scheme)
            except ValueError:
                raise ValueError(f"Unknown scheme: {scheme}")

        if scheme in (Scheme.HTTP, Scheme.HTTPS):
            return cls.HTTP
        elif scheme in (Scheme.WS, Scheme.WSS):
            return cls.WEBSOCKET
        raise ValueError(f"Unknown scheme: {scheme}")


ProtocolT = TypeVar("ProtocolT", bound=Protocol)
OptProtocol = Protocol | None
OptProtocolT = TypeVar("OptProtocolT", bound=OptProtocol)


class ProtocolMixin(BaseModel, Generic[OptProtocolT]):
    method: Annotated[OptProtocolT, Field(..., description="Protocol")]


ListOfProtocols = list[Protocol]
ListOfProtocolsT = TypeVar("ListOfProtocolsT", bound=ListOfProtocols)
OptListOfProtocols = ListOfProtocols | None
OptListOfProtocolsT = TypeVar("OptListOfProtocolsT", bound=OptListOfProtocols)


class ProtocolsMixin(BaseModel, Generic[OptListOfProtocolsT]):
    methods: Annotated[OptListOfProtocolsT, Field(..., description="Protocols")]


SeqOfProtocols = Sequence[Protocol]
SeqOfProtocolsT = TypeVar("SeqOfProtocolsT", bound=SeqOfProtocols)
OptSeqOfProtocols = SeqOfProtocols | None
OptSeqOfProtocolsT = TypeVar("OptSeqOfProtocolsT", bound=OptSeqOfProtocols)


class Method(StrEnum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


MethodT = TypeVar("MethodT", bound=Method)
OptMethod = Method | None
OptMethodT = TypeVar("OptMethodT", bound=OptMethod)


class MethodMixin(BaseModel, Generic[OptMethodT]):
    method: Annotated[OptMethodT, Field(..., description="Method")]


ListOfMethods = list[Method]
ListOfMethodsT = TypeVar("ListOfMethodsT", bound=ListOfMethods)
OptListOfMethods = ListOfMethods | None
OptListOfMethodsT = TypeVar("OptListOfMethodsT", bound=OptListOfMethods)


class MethodsMixin(BaseModel, Generic[OptListOfMethodsT]):
    methods: Annotated[OptListOfMethodsT, Field(..., description="Methods")]


SeqOfMethods = Sequence[Method]
SeqOfMethodsT = TypeVar("SeqOfMethodsT", bound=SeqOfMethods)
OptSeqOfMethods = SeqOfMethods | None
OptSeqOfMethodsT = TypeVar("OptSeqOfMethodsT", bound=OptSeqOfMethods)


class Header(StrEnum):
    # --- Authentication & Authorization ---
    AUTHORIZATION = "authorization"
    PROXY_AUTHORIZATION = "proxy-authorization"
    WWW_AUTHENTICATE = "www-authenticate"

    # --- Content & Caching ---
    CACHE_CONTROL = "cache-control"
    CONTENT_DISPOSITION = "content-disposition"
    CONTENT_ENCODING = "content-encoding"
    CONTENT_LENGTH = "content-length"
    CONTENT_TYPE = "content-type"
    ETAG = "etag"
    LAST_MODIFIED = "last-modified"
    EXPIRES = "expires"
    VARY = "vary"

    # --- Client & Request Context ---
    ACCEPT = "accept"
    ACCEPT_ENCODING = "accept-encoding"
    ACCEPT_LANGUAGE = "accept-language"
    ACCEPT_CHARSET = "accept-charset"
    HOST = "host"
    ORIGIN = "origin"
    REFERER = "referer"
    USER_AGENT = "user-agent"

    # --- Range / Conditional Requests ---
    RANGE = "range"
    CONTENT_RANGE = "content-range"
    IF_MATCH = "if-match"
    IF_NONE_MATCH = "if-none-match"
    IF_MODIFIED_SINCE = "if-modified-since"
    IF_UNMODIFIED_SINCE = "if-unmodified-since"

    # --- Correlation / Observability ---
    X_COMPLETED_AT = "x-completed-at"
    X_CONNECTION_ID = "x-connection-id"
    X_DURATION = "x-duration"
    X_EXECUTED_AT = "x-executed-at"
    X_OPERATION_ID = "x-operation-id"
    X_TRACE_ID = "x-trace-id"
    X_SPAN_ID = "x-span-id"

    # --- Organization / User Context ---
    X_ORGANIZATION_ID = "x-organization-id"
    X_USER_ID = "x-user-id"

    # --- API Keys / Clients ---
    X_API_KEY = "x-api-key"
    X_CLIENT_ID = "x-client-id"
    X_CLIENT_SECRET = "x-client-secret"
    X_SIGNATURE = "x-signature"

    # --- Cookies & Sessions ---
    COOKIE = "cookie"
    SET_COOKIE = "set-cookie"

    # --- Redirects & Responses ---
    LOCATION = "location"
    ALLOW = "allow"
    RETRY_AFTER = "retry-after"
    LINK = "link"

    # --- Proxy / Networking ---
    FORWARDED = "forwarded"
    X_FORWARDED_FOR = "x-forwarded-for"
    X_FORWARDED_PROTO = "x-forwarded-proto"
    X_FORWARDED_HOST = "x-forwarded-host"
    X_FORWARDED_PORT = "x-forwarded-port"
    X_REAL_IP = "x-real-ip"

    # --- Security ---
    STRICT_TRANSPORT_SECURITY = "strict-transport-security"
    CONTENT_SECURITY_POLICY = "content-security-policy"
    X_FRAME_OPTIONS = "x-frame-options"
    X_CONTENT_TYPE_OPTIONS = "x-content-type-options"
    REFERRER_POLICY = "referrer-policy"
    PERMISSIONS_POLICY = "permissions-policy"

    # --- Experimental / Misc ---
    X_NEW_AUTHORIZATION = "x-new-authorization"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


HeaderT = TypeVar("HeaderT", bound=Header)
OptHeader = Header | None
OptHeaderT = TypeVar("OptHeaderT", bound=OptHeader)


class HeaderMixin(BaseModel, Generic[OptHeaderT]):
    header: Annotated[OptHeaderT, Field(..., description="Header")]


ListOfHeaders = list[Header]
ListOfHeadersT = TypeVar("ListOfHeadersT", bound=ListOfHeaders)
OptListOfHeaders = ListOfHeaders | None
OptListOfHeadersT = TypeVar("OptListOfHeadersT", bound=OptListOfHeaders)


class HeadersMixin(BaseModel, Generic[OptListOfHeadersT]):
    headers: Annotated[OptListOfHeadersT, Field(..., description="Headers")]


SeqOfHeaders = Sequence[Header]
SeqOfHeadersT = TypeVar("SeqOfHeadersT", bound=SeqOfHeaders)
OptSeqOfHeaders = SeqOfHeaders | None
OptSeqOfHeadersT = TypeVar("OptSeqOfHeadersT", bound=OptSeqOfHeaders)
