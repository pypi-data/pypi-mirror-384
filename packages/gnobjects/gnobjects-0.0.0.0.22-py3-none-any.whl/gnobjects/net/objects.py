import re
import os
import ast
from typing import Optional, Dict, Any, List, Union, Literal, Tuple, cast, overload, Type
import anyio
from ._func import guess_type, render_pct_async
from KeyisBTools.models.serialization import serialize, deserialize, SerializableType

from .gnTransportProtocolParser import GNTransportProtocol, parse_gn_protocol

class Url:
    
    __slots__ = (
        "transport", "route", "scheme",
        "hostname", "port", "path", "params", "fragment"
    )

    _re_hostport = re.compile(r"""
        ^
        (?P<host>\[[^\]]+\]|[^:]+)
        (?::(?P<port>\d+))?
        $
    """, re.X)

    @overload
    def __init__(self): ...
    
    @overload
    def __init__(self, url: str): ...

    @overload
    def __init__(self, url: 'Url'): ...

    def __init__(self, url: Optional[Union[str, 'Url']] = None):
        self.transport: Optional[str] = None
        self.route: Optional[str] = None
        self.scheme: str = None # type: ignore
        self.hostname: str = None # type: ignore
        self.path: str = "/"
        self.params: Dict[str, Any] = {}
        self.fragment: Optional[str] = None

        if url:
            self.setUrl(url)

    def setUrl(self, url: Union[str, 'Url']):
        if isinstance(url, Url):
            self.transport = url.transport
            self.route = url.route
            self.scheme = url.scheme
            self.hostname = url.hostname
            self.path = url.path
            self.params = url.params
            self.fragment = url.fragment
            return
            
        proto, _, rest = url.partition("://")
        if not rest:
            raise ValueError(f"Invalid URL: {url}")

        if "~~" in proto:
            t, _, s = proto.partition("~~")
            self.transport, self.route, self.scheme = t, None, s or "gn"
        elif "~" in proto:
            parts = proto.split("~")
            if len(parts) == 3:
                self.transport, self.route, self.scheme = parts
            elif len(parts) == 2:
                self.transport, self.route, self.scheme = None, parts[0], parts[1]
            else:
                raise ValueError(f"Invalid protocol chain: {proto}")
        else:
            self.transport, self.route, self.scheme = None, None, proto or "gn"

        if not self.scheme:
            self.scheme = "gn"

        hostpath, _, frag = rest.partition("#")
        self.fragment = frag if frag != "" else None

        hostpath, _, query = hostpath.partition("?")
        if self.scheme == 'lib':
            host, self.path = 'libs.gn', hostpath
        elif "/" in hostpath:
            host, path = hostpath.split("/", 1)
            self.path = "/" + path
        else:
            host, self.path = hostpath, "/"

        if not host and self.scheme != "file":
            raise ValueError(f"Missing hostname in URL: {url}")

        if host:
            m = self._re_hostport.match(host)
            if not m:
                raise ValueError(f"Invalid hostname: {host}")
            self.hostname = m.group("host")
            if self.hostname.startswith("[") and self.hostname.endswith("]"):
                self.hostname = self.hostname[1:-1] # type: ignore
            p = m.group("port")
            if p is not None:
                self.hostname += ':' + p

        self.params = {}
        if query:
            for part in query.split("&"):
                if not part:
                    continue
                k, eq, v = part.partition("=")
                if not eq:
                    self.params[k] = None
                    continue
                try:
                    val = ast.literal_eval(v)
                except Exception:
                    val = v
                self.params[k] = val

    def _build_query(self) -> str:
        if not self.params:
            return ""
        out = []
        for k, v in self.params.items():
            if v is None:
                out.append(k)
            elif isinstance(v, str):
                out.append(f"{k}={v}")
            else:
                out.append(f"{k}={repr(v)}")
        return "&".join(out)

    def build(self, parts: List[str]) -> str:
        url = ""

        if "scheme" in parts or "transport" in parts or "route" in parts:
            if self.transport and self.route:
                proto = f"{self.transport}~{self.route}~{self.scheme}"
            elif self.transport and not self.route:
                proto = f"{self.transport}~~{self.scheme}"
            elif self.route and not self.transport:
                proto = f"{self.route}~{self.scheme}"
            else:
                proto = self.scheme or "gn"
            url += proto + "://"

        if "hostname" in parts and self.hostname:
            if ":" in self.hostname:
                host = f"[{self.hostname}]"
            else:
                host = self.hostname
            url += host

        if "path" in parts and self.path:
            url += self.path

        if "params" in parts and self.params:
            q = self._build_query()
            if q:
                url += f"?{q}"

        if "fragment" in parts and self.fragment is not None:
            url += f"#{self.fragment}"

        return url

    def toString(self) -> str:
        return self.build(["transport", "route", "scheme", "hostname", "path", "params", "fragment"])

    def __str__(self):
        return self.toString()




def _pack(mode: int, flag: bool, number: int) -> bytes:
    if not (1 <= mode <= 4): raise ValueError("mode должен быть 1..4")
    if number >= (1 << 61): raise ValueError("number должен быть < 2^61")
    value = ((mode - 1) & 0b11) << 62
    value |= (1 << 61) if flag else 0
    value |= number & ((1 << 61) - 1)
    return value.to_bytes(8, "big")

def _unpack(data: bytes):
    if len(data) < 8: raise Exception('len < 8')
    value = int.from_bytes(data[:8], "big")
    mode = ((value >> 62) & 0b11) + 1
    flag = bool((value >> 61) & 1)
    number = value & ((1 << 61) - 1)
    return mode, flag, number


class CORSObject:
    def __init__(self,
                 allow_origins: Optional[List[str]] = None,
                 allow_methods: Optional[List[str]] = None,
                 allow_client_types: List[Literal['net', 'client', 'server']] = ['net'],
                 allow_transport_protocols: Optional[List[str]] = None,
                 allow_route_protocols: Optional[List[str]] = None,
                 allow_request_protocols: Optional[List[str]] = None
                 ) -> None:
        """
        # Механизм контроля доступа


        :allow_origins: Список доменов, с которых разрешен запрос.
        :allow_methods: Разрешенные методы для запроса.
        :allow_client_types: Какие типы клиентов могут использовать.

        - `net` - Пользователи и другие службы сети `GN`

        - `client` - (TBD) Пользователи напрямую. Без использования прокси серверов сети `GN`

        - `server` - Другие `origin` сервера сети `GN`

        :allow_transport_protocols: (TBD)
        :allow_route_protocols: (TBD)
        :allow_request_protocols: (TBD)
        """
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods
        self.allow_client_types = allow_client_types
        self.allow_transport_protocols = allow_transport_protocols
        self.allow_route_protocols = allow_route_protocols
        self.allow_request_protocols = allow_request_protocols

            


    
    def serialize(self) -> Dict[int, Union[str, bool, List[str], None]]:
        return {
            0: self.allow_origins,
            1: self.allow_methods,
            2: self.allow_client_types, # type: ignore
        
            3: self.allow_transport_protocols,
            4: self.allow_route_protocols,
            5: self.allow_request_protocols
        }

    @staticmethod
    def deserialize(data: Dict[int, Any]) -> 'CORSObject':
        return CORSObject(
            allow_origins=data.get(0, None),
            allow_methods=data.get(1, None),
            allow_client_types=data.get(2, ['net']),

            allow_transport_protocols=data.get(3, None),
            allow_route_protocols=data.get(4, None),
            allow_request_protocols=data.get(5, None)
        )


class TemplateObject:
    def __init__(self,
                 vars_backend: Optional[Dict[str, Any]] = None,
                 vars_proxy: Optional[List[str]] = None,
                 vars_frontend: Optional[List[str]] = None
                 ) -> None:
        """
        
        - local side - "%{var}"

        - proxy - "!{var}"

        - user side - "&{var}"

        To substitute variables on the proxy and client, they must be requested from the server. To do this, add them to vars_proxy and vars_frontend

        If a template starts with "%" it is substituted on the server (gn:backend).

        If a template starts with "!" it is substituted on the proxy (gn:proxy).

        If a template starts with "&" it is substituted on the user side (gn:frontend).
        """

        self._vars_backend = vars_backend or {}
        self._vars_proxy = vars_proxy
        self._vars_frontend = vars_frontend
    
    def addVariable(self, name: str, value: Optional[Union[str, int, float, bool]], replacementPlace: Literal['backend', 'proxy', 'frontend'] = 'backend'):
        if not name.startswith(('%', "!", "&")):
            name = {'backend':"%", 'proxy':"!", 'frontend': "&"}[replacementPlace] + name

        if name.startswith('%'):
            self._vars_backend[name[1:]] = value
        elif name.startswith('!'):
            self._vars_proxy.append(name[1:])
        elif name.startswith('&'):
            self._vars_frontend.append(name[1:])
    
    
    def serialize(self) -> Dict[str, Union[Dict[str, Union[str, int, float, bool]], List[str]]]:
        d = {}
        
        if self._vars_proxy:
            d['proxy'] = self._vars_proxy

        if self._vars_frontend:
            d['frontend'] = self._vars_frontend
        
        return d

    @staticmethod
    def deserialize(data: Dict[str, Union[Dict[str, Union[str, int, float, bool]], List[str]]]) -> 'TemplateObject':
        return TemplateObject(
            None,
            data.get('proxy', {}), # type: ignore
            data.get('frontend', {}) # type: ignore
        )

class FileObject:

    @overload
    def __init__(
        self,
        path: str,
        template: Optional[TemplateObject] = ...,
        name: Optional[str] = ...
    ) -> None: ...
    
    @overload
    def __init__(
        self,
        data: bytes,
        mime_type: str,
        template: Optional[TemplateObject] = ...,
        name: Optional[str] = ...
    ) -> None: ...

    def __init__( # type: ignore
        self,
        path_or_data: Union[str, bytes],
        mime_type: Optional[str] = None,
        template: Optional[TemplateObject] = None,
        name: Optional[str] = None
    ) -> None:
        self._path: Optional[str] = None
        self._data: Optional[bytes] = None
        self._mime_type: Optional[str] = None
        self._template: Optional[TemplateObject] = None
        self._name: Optional[str] = name

        self._is_assembly: Optional[Tuple[Optional[str], dict]] = None

        if isinstance(path_or_data, str):
            if template is None and mime_type is not None and not isinstance(mime_type, str):
                template = cast(TemplateObject, mime_type)
                mime_type = None


            self._path = path_or_data
            self._template = template

            if mime_type is None:
                self._mime_type = guess_type(path_or_data)

        elif isinstance(path_or_data, bytes):
            self._data = path_or_data
            self._mime_type = mime_type
            self._template = template

        else:
            raise TypeError(f"path_or_data: ожидается str или bytes, получено {type(path_or_data)!r}")

    
    async def assembly(self) -> Tuple[Optional[str], dict]:
        """
        Assembles a file. Reads the file and substitutes templates.
        """
        if self._is_assembly is not None:
            return self._is_assembly

        if self._data is None:
            if not isinstance(self._path, str):
                raise Exception('Ошибка сбоки файла -> Путь к файлу не str')
            
            if not os.path.exists(self._path):
                raise Exception(f'Ошибка сбоки файла -> Файл не найден {self._path}')

            try:
                async with await anyio.open_file(self._path, mode="rb") as file:
                    self._data = await file.read()
            except Exception as e:
                raise Exception(f'Ошибка сбоки файла -> Ошиибка при чтении файла: {e}')
        
        self._is_assembly = (self._name, {'data': self._data, 'mime-type': self._mime_type})

        if self._template is not None:
            self._data = await render_pct_async(self._data, self._template._vars_backend)

            template = self._template.serialize()

            self._is_assembly[1]['templates'] = template

    
        return self._is_assembly


class GNRequest:
    """
    # Запрос для сети `GN`
    """
    def __init__(
        self,
        method: str,
        url: Url,
        payload: Optional[SerializableType] = None,
        cookies: Optional[dict] = None,
        transport: Optional[str] = None,
        route: Optional[str] = None,
        stream: bool = False,
        origin: Optional[str] = None
    ):
        self._method = method
        self._url = url
        self._payload = payload
        self._cookies = cookies
        self._transport = transport
        self._route = route
        self._stream = stream
        self._origin = origin

        if transport is None:
            self.setTransport()


        self.user = self.__user(self)
        """
        # Информация о пользователе

        Доступена только на сервере
        """

        self.client = self.__client(self)
        """
        # Информация о клиенте

        Доступена только на сервере
        """

    class __user:
        def __init__(self, request: 'GNRequest') -> None:
            self.__request = request
            self._data = {}
        
        @property
        def gwisid(self) -> int:
            """
            # ID объекта

            Возвращает уникальный идентификатор объекта в системе `GW`

            Этот идентификатор используется для управления объектами в системе.

            Может использоваться для идентификации пользователя.
            
            :return: int
            """
            return self._data.get("gwisid", 0)
        
        @property
        def sessionId(self) -> int:
            """
            # ID сессии

            Возвращает уникальный идентификатор сессии пользователя в сети `GN`
            
            Этот идентификатор используется для отслеживания состояния сессии пользователя в системе.

            Может использоваться для идентификации пользователя.
            
            :return: int
            """
            return self._data.get("session_id", 0)
        
        @property
        def nickname(self) -> str:
            """
            # Никнейм объекта

            Возвращает никнейм объекта в системе `GW`

            Никнейм используется для идентификации объекта в системе пользователями.

            Может использоваться для идентификации пользователя.

            :return: str
            """
            return self._data.get("nickname", "")

        @property
        def objectType(self) -> int:
            """
            # Тип объекта

            Возвращает тип объекта в системе `GW`
            
            Тип объекта используется для определения роли и функциональности объекта в системе.

            Возможные значения:
            - `0`: `GBN`
            - `2`: `Пользователь`
            - `3`: `Компания`
            - `4`: `Проект`
            - `5`: `Продукт`

            :return: int
            """
            return self._data.get("object_type", 0)
        
        @property
        def viewingType(self) -> int:
            """
            # Тип просмотра

            Возвращает тип просмотра объекта в системе `GW`

            Тип просмотра может быть установлен объекту для определения уровня доступа к объекту.

            Возможные значения:
            - `0`: Просмотр доступен только владельцу объекта
            - `1`: Просмотр не ограничен
            - `2`: Просмотр только авторизованным пользователям
            - `3`: Просмотр только для официально подтвержденных пользователей 

            :return: int
            """
            return self._data.get("viewing_type", 0)

        @property
        def description(self) -> str:
            """
            # Описание объекта

            Возвращает описание объекта в системе `GW`

            Описание может содержать дополнительную информацию о объекте.

            :return: str
            """
            return self._data.get("description", "")

        @property
        def name(self) -> str:
            """
            # Имя объекта

            Возвращает имя объекта в системе `GW`

            ```python
            Имя НЕ может быть использовано для идентификации объекта в системе пользователями.
            ```

            Может использоваться для определения объекта ТОЛЬКО пользователями.

            :return: str
            """
            return self._data.get("name", "")
        
        @property
        def owner(self) -> Optional[int]:
            """
            # `gwisid` владельца объекта

            Возвращает уникальный идентификатор `gwisid` владельца объекта в системе `GW`

            Этот идентификатор используется для определения владельца объекта.

            :return: Optional[int]
            Если владелец не установлен, возвращает None.
            """
            return self._data.get("owner", None)
        
        @property
        def officiallyConfirmed(self) -> bool:
            """
            # Официально подтвержденный объект

            Возвращает `True`, если объект официально подтвержден в системе `GW`

            Официально подтвержденные объекты могут иметь дополнительные права и возможности.

            :return: bool
            """
            return self._data.get("of_conf", False)

    class __client:
        model_client_types: Dict[int, str] = {
                1: 'net',
                2: 'server',
                4: 'client'
            }
        
        def __init__(self, request: 'GNRequest') -> None:
            self.__request = request
            self._data = {}

        @property
        def remote_addr(self) -> Tuple[str, int]:
            """
            # `Tuple(IP, port)` клиента
            
            :return: Tuple[str, int]
            """
            return self._data.get("remote_addr", ())
        
        @property
        def ip(self) -> str:
            """
            # IP клиента
            
            :return: str
            """
            return self._data.get("remote_addr", ())[0]
        
        @property
        def port(self) -> int:
            """
            # Port клиента
            
            :return: int
            """
            return self._data.get("remote_addr", ())[1]
        
        @property
        def type(self) -> Literal['net', 'client', 'server']:
            """
            # Тип клиента

            - `net` - Пользователи и другие службы сети `GN`

            - `client` - Пользователи напрямую. Без использования прокси серверов сети `GN`

            - `server` - Другие `origin` сервера сети `GN`
                
            :return: Literal['net', 'client', 'server']
            """
            return self.model_client_types[self._data['client-type']]
        
        @property
        def type_int(self) -> Literal[1, 4, 2]:
            """
            # Тип клиента (int)

            - `1` - net - Пользователи и другие службы сети `GN`

            - `4` - client - Пользователи напрямую. Без использования прокси серверов сети `GN`

            - `2` - server - Другие `origin` сервера сети `GN`
            
            :return: int
            """
            return self._data['client-type']

        @property
        def domain(self) -> Optional[str]:
            """
            # Домен сервера

            `None`, если запрос совершает не сервер
            
            :return: Optional[str]
            """
            return self._data.get("domain", None)
        


    def serialize(self, mode: int = 0) -> bytes:
        if self._transport is None: self.setTransport()
        if self._route is None: self.setRoute()
        d: Dict[Any, Any] = {
            1: self._method,
            2: str(self._url),
            7: self._route,
            8: self._transport
        }
        
        if self._cookies is not None:
            d[4] = self._cookies
        if self._payload is not None:
            d[5] = self._payload
        if not mode:
            d[6] = self.stream
        if d[7] == 'gn:net':
            d[7] = True
        if self.user._data != {}:
            d[9] = self.user._data
        if self._origin is not None:
            d[10] = self._origin
        blob = serialize(d)
        return _pack(mode, self.stream, len(blob) + 8) + blob if mode else blob

    @staticmethod
    def deserialize(data: bytes, mode: int = 0) -> 'GNRequest':
        if mode:
            if len(data) < 8:
                raise Exception('len')
            _mode, stream, length = _unpack(data[:8])
            if _mode != mode:
                raise Exception('decrypt error')
            data = data[8:length]
        else:
            stream = None
        unpacked: dict = deserialize(data) # type: ignore
        _url = Url(unpacked[2])
        route_ = unpacked.get(7)
        if mode:
            if route_ is True:
                route_ = 'gn:net'
        

        r = GNRequest(
            method=unpacked[1],
            url=_url,
            payload=unpacked.get(5),
            cookies=unpacked.get(4),
            stream=stream if stream is not None else unpacked.get(6), # type: ignore
            transport=unpacked.get(8),
            route=route_,
            origin=unpacked.get(10)
        )
        r.user._data = unpacked.get(9) # type: ignore
        r.client._data['client-type'] = _mode # type: ignore
        return r
    @staticmethod
    def type(data: bytes) -> Tuple[int, bool, int]:
        return _unpack(data)

    @property
    def method(self) -> str:
        """
        # Метод запроса

        GET, POST, PUT, DELETE и т.д.
        """
        return self._method
    
    def setMethod(self, method: str):
        """
        # Метод запроса
        
        :param method: Метод запроса (GET, POST, PUT, DELETE и т.д.)
        """
        self._method = method
    
    @property
    def url(self) -> Url:
        """
        # URL запроса.
        """
        return self._url

    def setUrl(self, url: Url):
        """
        # URL запроса
        
        :param url: `URL` запроса в виде объекта `Url`.
        """
        self._url = url

    @property
    def payload(self) -> Optional[SerializableType]:
        """
        # Полезная нагрузка запроса

        `Dict`, `List`, `bytes`, `int`, `str` и другие типы с поддержкой байтов.

        Все поддерживаемые типа описанны в `KeyisBTools.models.serialization.SerializableType`
        
        Если полезная нагрузка не установлена, возвращает None.
        """
        return self._payload

    def setPayload(self, payload: Optional[dict]):
        """
        # Полезная нагрузка запроса

        `Dict`, `List`, `bytes`, `int`, `str` и другие типы с поддержкой байтов.

        Все поддерживаемые типа описанны в `KeyisBTools.models.serialization.SerializableType`

        :param payload: Dict с поддержкой байтов.
        """
        self._payload = payload

    @property
    def cookies(self) -> Optional[dict]:
        return self._cookies

    def setCookies(self, cookies: dict):
        self._cookies = cookies
        
    @property
    def transportObject(self) -> GNTransportProtocol:
        """
        # Транспортный протокол (объект)

        `GN` протокол используется для подключения к сети `GN`.
        """
        return parse_gn_protocol(self._transport)

    @property
    def transport(self) -> str:
        """
        # Транспортный протокол.

        """
        return self._transport
    
    def setTransport(self, transport: Optional[str] = None):
        """
        Устанавливает `GN` протокол.

        :param transport: `GN` протокол (например, '`gn:tcp:quik`', '`gn:quik:real`',..).

        Если не указан, используется `gn:quik:real`.
        """
        if transport is None:
            transport = 'gn:quik:real'
        self._transport = transport

    @property
    def route(self) -> Optional[str]:
        """
        # Маршрут запроса.

        Маршрут используется для определения пути запроса в сети `GN`.

        Если маршрут не установлен, возвращает `None`.
        """
        return self._route
    
    def setRoute(self, route: Optional[str] = None):
        """
        # Маршрут запроса.

        :param route: Маршрут запроса (например, `gn:net`).

        Если не указан, используется `gn:net`.
        """
        if route is None:
            route = 'gn:net'
        self._route = route

    @property
    def stream(self) -> bool:
        return self._stream

    def __repr__(self):
        return f"<GNRequest [{self._method} {self._url}] [{self._transport}]>"

class GNResponse(Exception):
    """
    # Ответ на запрос для сети `GN`
    """
    def __init__(self,
                 command: Union[str, int, bool],
                 payload: Optional[SerializableType] = None,
                 files: Optional[Union[str, FileObject,  List[FileObject]]] = None,
                 cors: Optional[CORSObject] = None,
                 cookies: Optional[dict] = None
                 ):
        self._command = command
        self._payload = payload
        self._stream = False
        self._cors = cors
        self._files = files
        self._cookies = cookies

        self.command = CommandObject(command)
        """
        # Команда запроса `CommandObject`
        """

    async def assembly(self) -> 'GNResponse':
        """
        Сборка ответа в формат gn для отправки
        """

        if self._files is not None:
            _files = {}
            if not isinstance(self._files, list):
                self._files = {0:self._files}

            if isinstance(self._files, dict):
                for file in self._files.values():
                    if not isinstance(file, dict):
                        if isinstance(file, str):
                            file = FileObject(file)

                        name, assembly_file = await file.assembly()
                        _files[name or 0] = assembly_file

            self._files = _files


        return self

    def serialize(self, mode: int = 0) -> bytes:
        d: Dict[Any, Any] = {
            1: self._command
        }

        if self._payload is not None:
            d[2] = self._payload

        if not mode:
            d[3] = self.stream
        
        if self._cors is not None:
            d[4] = self._cors.serialize()

        if self._files:
            d[5] = self._files

        if self._cookies:
            d[6] = self._cookies


        blob = serialize(d)
        return _pack(mode, self.stream, len(blob) + 8) + blob if mode else blob
    
    @staticmethod
    def deserialize(data: bytes, mode: int = 0) -> 'GNResponse':
        if mode:
            if len(data) < 8:
                raise Exception('len')
            
            _mode, stream, length = _unpack(data[:8])

            if _mode != mode:
                raise Exception('decrypt error')

            data = data[8:length]
        else:
            stream = None

                

        unpacked: Dict = deserialize(data) # type: ignore

        cm = unpacked.get(1)

        r = GNResponse(
            command=cm or 'gn:no-command',
            payload=unpacked.get(2),
            cors=CORSObject.deserialize(unpacked[4]) if 4 in unpacked else None

        )
        r._stream = stream if stream is not None else unpacked.get(3)
        r._files = unpacked.get(5)
        r._cookies = unpacked.get(6)
        return r
    
    @staticmethod
    def type(data: bytes) -> Tuple[int, bool, int]:
        return _unpack(data)

    @property
    def payload(self) -> Optional[SerializableType]:
        return self._payload
    
    @property
    def stream(self) -> bool:
        return self._stream
    
    @property
    def cors(self) -> Optional[CORSObject]:
        return self._cors
    
    @property
    def files(self) -> Optional[Union[str, FileObject,  List[FileObject]]]:
        return self._files
    
    @property
    def cookies(self) -> Optional[dict]:
        return self._cookies
    
    def __repr__(self):
        return f"<GNResponse [{self._command}]>"
    
    def __str__(self) -> str:
        return f"[GNResponse]: {self._command} {self._payload}"


from .fastcommands import AllGNFastCommands

class CommandObject(AllGNFastCommands):
    def __init__(self, value: Union[str, int, bool]):
        if not isinstance(value, (str, int, bool)):
            raise TypeError("Command must be str, int or bool")
        
        self.value = value
        """
        # Значение команды
        """

    def __getattribute__(self, name: str):
        if name == 'ok':
            return self.__bool__()
        if name in AllGNFastCommands.__dict__.keys():
            a: Type[AllGNFastCommands.ok] = getattr(AllGNFastCommands, name)
            return self.value == a.cls_command
        return super().__getattribute__(name)

    def __eq__(self, other):
        if isinstance(other, CommandObject):
            return self.value == other.value
        return self.value == other
    

    def __ne__(self, other):
        return not self.__eq__(other)

    def __bool__(self):
        
        if isinstance(self.value, bool):
            return self.value
        elif isinstance(self.value, int):
            return self.value == 200
        else:
            return self.value == 'ok' or self.value.endswith((':ok', ':200'))
        
    def __str__(self) -> str:
        if isinstance(self.value, str):
            return self.value
        elif isinstance(self.value, bool):
            if self.value:
                return 'ok'
            else:
                return 'gn:error:false'
        elif isinstance(self.value, int):
            if self.value == 200:
                return 'ok'
            else:
                return f'gn:error:{self.value}'
        else:
            return ''
            
    def __repr__(self):
        return f"CommandObject({self.value!r})"

    def _serializebleType(self):
        if isinstance(self.value, str):
            if self.value == 'ok':
                return True
            return self.value
        elif isinstance(self.value, bool):
            return self.value
        elif isinstance(self.value, int):
            return self.value
        else:
            return False