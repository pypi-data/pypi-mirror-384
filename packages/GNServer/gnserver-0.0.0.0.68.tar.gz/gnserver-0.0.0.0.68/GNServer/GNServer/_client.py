import os
import sys
import time
import httpx
import asyncio
import datetime
from itertools import count
from collections import deque
from typing import Any, Dict, Deque, Tuple, Union, Optional, AsyncGenerator, Callable, Literal, AsyncIterable, overload
from aioquic.quic.events import QuicEvent, StreamDataReceived, StreamReset, ConnectionTerminated
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.client import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol




class GNExceptions:
    class ConnectionError:
        class openconnector():
            """Ошибка подключения к серверу openconnector.gn"""
            
            class connection(Exception):
                def __init__(self, message="Ошибка подключения к серверу openconnector.gn. Сервер не найден."):
                    super().__init__(message)

            class timeout(Exception):
                def __init__(self, message="Ошибка подключения к серверу openconnector.gn. Проблема с сетью или сервер перегружен."):
                    super().__init__(message)

            class data(Exception):
                def __init__(self, message="Ошибка подключения к серверу openconnector.gn. Сервер не подтвердил подключение."):
                    super().__init__(message)

        class dns():
            """Ошибка подключения к серверу dns.core"""
            class connection(Exception):
                def __init__(self, message="Ошибка подключения к серверу dns.core Сервер не найден."):
                    super().__init__(message)

            class timeout(Exception):
                def __init__(self, message="Ошибка подключения к серверу dns.core Проблема с сетью или сервер перегружен"):
                    super().__init__(message)
    
            class data(Exception):
                def __init__(self, message="Ошибка подключения к серверу dns.core Сервер не подтвердил подключение."):
                    super().__init__(message)

        class connector():
            """Ошибка подключения к серверу <?>~connector.gn"""
            
            class connection(Exception):
                def __init__(self, message="Ошибка подключения к серверу <?>~connector.gn. Сервер не найден."):
                    super().__init__(message)

            class timeout(Exception):
                def __init__(self, message="Ошибка подключения к серверу <?>~connector.gn. Проблема с сетью или сервер перегружен"):
                    super().__init__(message)
    
            class data(Exception):
                def __init__(self, message="Ошибка подключения к серверу <?>~connector.gn. Сервер не подтвердил подключение."):
                    super().__init__(message)

        class client():
            """Ошибка клиента"""
            
            class connection(Exception):
                def __init__(self, message="Ошибка подключения к серверу. Сервер не найден."):
                    super().__init__(message)

            class timeout(Exception):
                def __init__(self, message="Ошибка подключения к серверу. Проблема с сетью или сервер перегружен"):
                    super().__init__(message)
    
            class data(Exception):
                def __init__(self, message="Ошибка подключения к серверу. Сервер не подтвердил подключение."):
                    super().__init__(message)
                    

from KeyisBTools import TTLDict
from KeyisBTools.cryptography.sign import s2
from KeyisBTools.cryptography import m1
from KeyisBTools.cryptography.bytes import hash, userFriendly
from KeyisBTools.models.serialization import serialize
from KeyisBTools.ranges.positionRange import in_range
from gnobjects.net.objects import GNRequest, GNResponse, Url

from ._crt import crt_client
from .models import KDCObject


import traceback

import logging

logger = logging.getLogger("GNClient")
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
logger.addHandler(console)




_log_levels: dict[str, int] = {
    "NOTSET": 0,
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "notset": 0,
    "debug": 10,
    "info": 20,
    "warning": 30,
    "error": 40,
    "critical": 50,
}

def devLog(request: GNRequest, point: str, level: int, log: str):
    """
- NOTSET	 0
- DEBUG	     10
- INFO	     20
- WARNING	 30
- ERROR	     40
- CRITICAL   50
    """
    if request.transportObject.routeProtocol.dev:
        if hasattr(request, '_devDataLog'):
            if request._devDataLogLevel <= level:
                if in_range(point, request._devDataRange):

                    log = f'[{level}]({datetime.datetime.now()}): {log}'

                    request._devDataLog.append(log)



_sys_s_mode = 2

async def chain_async(first_item, rest: AsyncIterable) -> AsyncGenerator:
    yield first_item
    async for x in rest:
        yield x

"""
L1 - Physical
L2 - MAC
L3 - IP
L4 - TCP/UDP
L5 - quic(packet managment)
L6 - GN(protocol managment)


"""


class AsyncClient:
    def __init__(self, domain: Optional[str] = None, server_key: Optional[Union[bytes, str]] = None):
        self.__dns_core__ipv4 = '51.250.85.38:52943'
        self.__dns_gn__ipv4: Optional[str] = None

        self.__current_session = {}
        self.__request_callbacks = {}
        self.__response_callbacks = {}

        self._active_connections: Dict[str, QuicClient] = {}

        self.__dns_client: Optional[AsyncClient] = None
        self._dns_cache: TTLDict = TTLDict()

        self._domain = domain

        self._kdc: Optional[KDCObject] = None

        
        if server_key:
            self.setDNSkey(server_key)
        else:
            self._dns_key = None

        self._configuration: dict = {
            'L5': {
                'connection': {
                    'connect_timeout': 10,
                },
                'disconnection': {
                    'idle_timeout': 60,
                    'ping_interval': 15,
                    'ping_check_interval': 5,
                }
            }
        }

    
    def setConfiguration(self, configuration: dict):
        self._configuration = configuration


    def setDNSkey(self, key: Union[bytes, str]):
        if key:
            if isinstance(key, bytes):
                self._dns_key = key
            else:
                if os.path.exists(key):
                    self._dns_key = open(key, 'rb').read()
                else:
                    self._dns_key = userFriendly.decode(key)
        else:
            self._dns_key = None

    def setKDC(self, kdc: KDCObject):
        self._kdc = kdc
        self._kdc._client = self

    def addRequestCallback(self, callback: Callable, name: str):
        self.__request_callbacks[name] = callback

    def addResponseCallback(self, callback: Callable, name: str):
        self.__response_callbacks[name] = callback

  
    async def connect(self, request: GNRequest, restart_connection: bool = False, reconnect_wait: float = 10, keep_alive: bool = True) -> 'QuicClient':
        domain = request.url.hostname
        if not restart_connection and domain in self._active_connections:
            c = self._active_connections[domain]
            if c.status == 'connecting':
                try:
                    await asyncio.wait_for(c.connect_future, reconnect_wait or self._configuration.get('L5', {}).get('connection', {}).get())
                    if c.status == 'active':
                        return c
                    elif c.status == 'connecting': # если очень долго подключаемся, то кидаем ошибку
                        await self.disconnect(domain)
                        raise GNExceptions.ConnectionError.client.timeout
                    elif c.status == 'disconnect':
                        raise GNExceptions.ConnectionError.client.connection
                except:
                    await self.disconnect(domain)
            else:
                return c

        c = QuicClient(self)
        c.status = 'connecting'
        self._active_connections[domain] = c

        data = await self.getDNS(domain, raise_errors=True)

        data = data.split(':')



        def f(domain):
            self._active_connections.pop(domain)

        c._disconnect_signal = f # type: ignore
        c._domain = domain # type: ignore
        await c.connect(data[0], int(data[1]), keep_alive=keep_alive)
        await c.connect_future

        return c

    async def disconnect(self, domain):
        if domain not in self._active_connections:
            return
        
        await self._active_connections[domain].disconnect()


    def _return_token(self, bigToken: str, s: bool = True) -> str:
        return bigToken[:128] if s else bigToken[128:]

    async def _resolve_requests_transport(self, request: GNRequest) -> GNRequest:
        
        if request.transportObject.routeProtocol.dev:
            if request.cookies is not None:
                data: Optional[dict] = request.cookies.get('gn', {}).get('request', {}).get('transport', {}).get('::dev')
                if data is not None:
                    data['params']['logs']['data'] = []
                    data['params']['data']['data'] = {}
                    request._devDataLog = data['params']['logs']['data']
                    request._devDataLogLevel = _log_levels[data['params']['logs']['data']]
                    request._devData = data['params']['data']['data']
                    request._devDataRange = data['params']['range']

        return request

    async def request(self, request: Union[GNRequest, AsyncGenerator[GNRequest, Any]], keep_alive: bool = True, restart_connection: bool = False, reconnect_wait: float = 10) -> GNResponse:

        if isinstance(request, GNRequest):
            
            request = await self._resolve_requests_transport(request)
            try:
                c = await self.connect(request, restart_connection, reconnect_wait, keep_alive=keep_alive)
            except BaseException as e:
                if isinstance(e, GNResponse):
                    return e
                else:
                    return GNResponse(str(e), payload=traceback.format_exc())
            devLog(request, '1.1.3', 10, f'Connected: {c.status}')


            for f in self.__request_callbacks.values():
                asyncio.create_task(f(request))
            logger.debug(f'Request: {request.method} {request.url}')
            r = await c.asyncRequest(request)
            logger.debug(f'Response: {request.method} {request.url} -> {r.command} {r.payload if len(str(r.payload)) < 256 else ''}')

            for f in self.__response_callbacks.values():
                asyncio.create_task(f(r))

            return r
        
        else:

            c: Optional[QuicClient] = None

            async def wrapped(request) -> AsyncGenerator[GNRequest, None]:
                async for req in request:
                    if req.gn_protocol is None:
                        req.setGNProtocol(self.__current_session['protocols'][0])
                    req._stream = True

                    for f in self.__request_callbacks.values():
                        asyncio.create_task(f(req))

                    nonlocal c
                    if c is None:  # инициализируем при первом req
                        c = await self.connect(request, restart_connection, reconnect_wait, keep_alive=keep_alive)

                    yield req

            gen = wrapped(request)
            first_req = await gen.__anext__()

            if c is None:
                raise GNExceptions.ConnectionError.client.data

            r = await c.asyncRequest(chain_async(first_req, gen))

            for f in self.__response_callbacks.values():
                asyncio.create_task(f(r))

            return r



    def isDNSCore(self, domain: str) -> bool:
        return domain.endswith(('.core', '.gw', '.gn', '.cdn', '.sys', '.gwis', '.abs'))

    @overload
    async def getDNS(self, domain: str, use_cache: bool = True, keep_alive: bool = False, raise_errors: Literal[False] = False) -> GNResponse: ...
    @overload
    async def getDNS(self, domain: str, use_cache: bool = True, keep_alive: bool = False, raise_errors: Literal[True] = True) -> str: ...

    async def getDNS(self, domain: str, use_cache: bool = True, keep_alive: bool = False, raise_errors: bool = False) -> Union[str, GNResponse]:
        if use_cache:
            resuilt = self._dns_cache.get(domain)
            if resuilt is not None:
                if raise_errors:
                    r1_data = resuilt.payload
                    result = r1_data['ip'] + ':' + str(r1_data['port']) # type: ignore
                else:
                    result = resuilt
                return result
            

        if ':' in domain and domain.split('.')[-1].split(':')[0].isdigit() and domain.split(':')[-1].isdigit():
            return domain
        
        if domain == 'api.dns.core':
            return self.__dns_core__ipv4
        
        is_dns_core = self.isDNSCore(domain)
        if not is_dns_core:
            if self.__dns_gn__ipv4 is None:
                self.__dns_gn__ipv4 = await self.getDNS('api.dns.gn', raise_errors=True)

        if self.__dns_client is None:
            self.__dns_client = AsyncClient()

        if self._dns_key is not None:
            s = s2.sign(self._dns_key)
            data = m1.encrypt(s, domain.encode(), serialize({'domain': domain}), hash(self._dns_key))
            payload = {'sign': {'alg': 'KeyisB-c-s-m1', 'data': s, 'domain': self._domain}, 'data': data}
        else:
            payload = None
        
        if is_dns_core:
            ip_dns = self.__dns_core__ipv4
        else:
            ip_dns = self.__dns_gn__ipv4

        r1 = await self.__dns_client.request(GNRequest('GET', Url(f'gn://{ip_dns}/getIp?d={domain}'), payload=payload), keep_alive=keep_alive)

        if not r1.command:
            if raise_errors:
                raise r1
            else:
                return r1

        self._dns_cache.set(domain, r1, r1.payload.get('ttl', 60)) # type: ignore

        if raise_errors:
            r1_data = r1.payload
            result = r1_data['ip'] + ':' + str(r1_data['port']) # type: ignore
        else:
            result = r1
        return result

    





    # async def requestStream(self, request: Union[GNRequest, AsyncGenerator[GNRequest, Any]]) -> AsyncGenerator[GNResponse, None]:
    #     """
    #     Build and send a async request.
    #     """
    #     if isinstance(request, GNRequest):
    #         if request.gn_protocol is None:
    #             request.setGNProtocol(self.__current_session['protocols'][0])
                
    #         for f in self.__request_callbacks.values():
    #             asyncio.create_task(f(request))

    #         async for response in self.client.asyncRequestStream(request):
                    
    #             for f in self.__response_callbacks.values():
    #                 asyncio.create_task(f(response))

    #             yield response
    #     else:
    #         async def wrapped(request) -> AsyncGenerator[GNRequest, None]:
    #             async for req in request:
    #                 if req.gn_protocol is None:
    #                     req.setGNProtocol(self.__current_session['protocols'][0])
                            
    #                 for f in self.__request_callbacks.values():
    #                     asyncio.create_task(f(req))
                        
    #                 req._stream = True
    #                 yield req
    #         async for response in self.client.asyncRequestStream(wrapped(request)):
                
    #             for f in self.__response_callbacks.values():
    #                 asyncio.create_task(f(response))

    #             yield response

class RawQuicClient(QuicConnectionProtocol):

    SYS_RATIO_NUM = 9  # SYS 9/10
    SYS_RATIO_DEN = 10

    # ────────────────────────────────────────────────────────────────── init ─┐
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.quicClient: QuicClient = None # type: ignore

        self._queue_sys: Deque[Tuple[int, bytes, bool]] = deque()
        self._queue_user: Deque[Tuple[int, bytes, bool]] = deque()

        # <‑‑ Future | Queue[bytes | None]
        self._inflight: Dict[int, Union[asyncio.Future, asyncio.Queue[Optional[GNResponse]]]] = {}
        self._inflight_streams: Dict[int, bytearray] = {}
        self._buffer: Dict[Union[int, str], bytearray] = {}

        self._last_activity = time.time()
        self._running = True
        self._ping_id_gen = count(1)  # int64 ping‑id generator

    # ───────────────────────────────────────── private helpers ─┤
    def _activity(self):
        self._last_activity = time.time()

    async def _keepalive_loop(self):
        while self._running:
            await asyncio.sleep(self.quicClient._client._configuration.get('L5', {}).get('disconnection', {}).get('ping_check_interval', 5))
            idle_time = time.time() - self._last_activity
            if idle_time > self.quicClient._client._configuration.get('L5', {}).get('disconnection', {}).get('ping_interval', 15):
                self._quic.send_ping(next(self._ping_id_gen))
                self.transmit()
                self._last_activity = time.time()

    def stop(self):
        self._running = False

    # ───────────────────────────────────────────── events ─┤
    def quic_event_received(self, event: QuicEvent) -> None:  # noqa: C901
        # ─── DATA ───────────────────────────────────────────
        if isinstance(event, StreamDataReceived):
            handler = self._inflight.get(event.stream_id)
            if handler is None:
                return
            
            # Чтение в зависимости от режима
            if not isinstance(handler, asyncio.Queue): # стрим от сервера
                buf = self._buffer.setdefault(event.stream_id, bytearray())
                buf.extend(event.data)
                if event.end_stream:
                    self._inflight.pop(event.stream_id, None)
                    data = bytes(self._buffer.pop(event.stream_id, b""))
                    if not handler.done():
                        handler.set_result(data)
            else:
                # получаем байты
                buf = self._buffer.setdefault(event.stream_id, bytearray())
                buf.extend(event.data)

                if len(buf) < 8: # не дошел даже frame пакета
                    return
                
                # получаем длинну пакета
                mode, stream, lenght = GNResponse.type(buf)

                if mode != 4: # не наш пакет
                    self._buffer.pop(event.stream_id)
                    return
                
                if not stream: # клиент просил стрим, а сервер прислал один пакет
                    self._buffer.pop(event.stream_id)
                    return
                
                # читаем пакет
                if len(buf) < lenght: # если пакет не весь пришел, пропускаем
                    return
                
                # пакет пришел весь

                # берем пакет
                data = buf[:lenght]

                # удаляем его из буфера
                del buf[:lenght]
                    
                
                r = GNResponse.deserialize(data, _sys_s_mode)
                handler.put_nowait(r)
                if event.end_stream:
                    handler.put_nowait(None)
                    self._buffer.pop(event.stream_id)
                    self._inflight.pop(event.stream_id, None)


                

        # ─── RESET ──────────────────────────────────────────
        elif isinstance(event, StreamReset):
            handler = self._inflight.pop(event.stream_id, None)
            if handler is None:
                return
            if isinstance(handler, asyncio.Queue):
                handler.put_nowait(None)
            else:
                if not handler.done():
                    handler.set_exception(RuntimeError("stream reset"))


        elif isinstance(event, ConnectionTerminated):
            print("QUIC connection closed")
            print("Error code:", event.error_code)
            print("Reason:", event.reason_phrase)
            if self.quicClient is None:
                return
            
            self.stop()
            
            asyncio.create_task(self.quicClient.disconnect())



    def _schedule_flush(self):
        self.transmit()
        self._activity()




    async def request(self, request: Union[GNRequest, AsyncGenerator[GNRequest, Any]]):
        if isinstance(request, GNRequest):
            blob = request.serialize(_sys_s_mode)

            if self.quicClient._client._kdc is not None:
                blob = await self.quicClient._client._kdc.encode(request.url.hostname, blob)
                
            sid = self._quic.get_next_available_stream_id()
            self._quic.send_stream_data(sid, blob, end_stream=True)
            self._schedule_flush()

            
            fut = asyncio.get_running_loop().create_future()
            self._inflight[sid] = fut
            data = await fut
            
            if self.quicClient._client._kdc is not None:
                data, domain = await self.quicClient._client._kdc.decode(data)

            if data is not None:
                r = GNResponse.deserialize(data, _sys_s_mode)
                return r
            else:
                return GNResponse('gn:client:0')
        
        else:
            sid = self._quic.get_next_available_stream_id()
            #if sid in self._quic._streams and not self._quic._streams[sid].is_finished:

            async def _stream_sender(sid, request: AsyncGenerator[GNRequest, Any]):
                _last = None
                async for req in request:
                    _last = req
                    blob = req.serialize(_sys_s_mode)
                    self._quic.send_stream_data(sid, blob, end_stream=False)
                    self._schedule_flush()

                    print(f'Отправлен stream запрос {req}')
                

                _last.setPayload(None)
                _last.setMethod('gn:end-stream')
                blob = _last.serialize(_sys_s_mode)
                self._quic.send_stream_data(sid, blob, end_stream=True)
                self._schedule_flush()
            
            asyncio.create_task(_stream_sender(sid, request))

                
            fut = asyncio.get_running_loop().create_future()
            self._inflight[sid] = fut
            return await fut
    
    # async def requestStream(self, request: Union[GNRequest, AsyncGenerator[GNRequest, Any]]) -> asyncio.Queue[GNResponse]:
    #     if isinstance(request, GNRequest):
    #         blob = request.serialize(_sys_s_mode)
    #         sid = self._quic.get_next_available_stream_id()
    #         self._enqueue(sid, blob, False, False)
    #         self._schedule_flush()

            
    #         q = asyncio.Queue()
    #         self._inflight[sid] = q
    #         return q
            
    #     else:
    #         sid = self._quic.get_next_available_stream_id()

    #         async def _stream_sender(sid, request: AsyncGenerator[GNRequest, Any]):
    #             _last = None
    #             async for req in request:
    #                 _last = req
    #                 blob = req.serialize(_sys_s_mode)
    #                 self._enqueue(sid, blob, False, False)


    #                 self._schedule_flush()

    #                 print(f'Отправлен stream запрос {req}')
                

    #             _last.setPayload(None)
    #             _last.setMethod('gn:end-stream')
    #             blob = _last.serialize(_sys_s_mode)
    #             self._enqueue(sid, blob, True, False)
    #             self._schedule_flush()
            
    #         asyncio.create_task(_stream_sender(sid, request))

                
    #         q = asyncio.Queue()
    #         self._inflight[sid] = q
    #         return q

        

class QuicClient:
    """Обёртка‑фасад над RawQuicClient."""

    def __init__(self, Client: AsyncClient):
        self._client = Client
        self._quik_core: Optional[RawQuicClient] = None
        self._client_cm = None
        self._disconnect_signal = None
        self._domain = None

        self.status: Literal['active', 'connecting', 'disconnect']

        self.connect_future = asyncio.get_event_loop().create_future()

    async def connect(self, ip: str, port: int, keep_alive: bool = True):
        self.status = 'connecting'
        cfg = QuicConfiguration(is_client=True, alpn_protocols=["gn:backend"])
        cfg.load_verify_locations(cadata=crt_client)
        cfg.idle_timeout = self._client._configuration.get('L5', {}).get('disconnection', {}).get('idle_timeout', 60)

        self._client_cm = connect(
            ip,
            port,
            configuration=cfg,
            create_protocol=RawQuicClient,
            wait_connected=True,
        )


        try:
            self._quik_core = await self._client_cm.__aenter__() # type: ignore
            self._quik_core.quicClient = self

            if keep_alive:
                asyncio.create_task(self._quik_core._keepalive_loop())

            self.status = 'active'
            if not self.connect_future.done():
                self.connect_future.set_result(True)
        except Exception as e:
            print(f'Error connecting: {e}')
            if not self.connect_future.done():
                self.connect_future.set_exception(GNExceptions.ConnectionError.client.connection)
            await self._client_cm.__aexit__(None, None, None)

    async def disconnect(self):
        self.status = 'disconnect'
        
        if self._quik_core is not None:
            self._quik_core.stop()
        

        if self._disconnect_signal is not None:
            self._disconnect_signal(self._domain)
        

        if self._quik_core is not None:


            for fut in self._quik_core._inflight.values():
                if isinstance(fut, asyncio.Queue):
                    del fut
                else:
                    fut.set_exception(Exception)



            self._quik_core.close()
            await self._quik_core.wait_closed()
            self._quik_core = None

    async def asyncRequest(self, request: Union[GNRequest, AsyncGenerator[GNRequest, Any]]) -> GNResponse:
        if self._quik_core is None:
            raise RuntimeError("Not connected")
        
        resp = await self._quik_core.request(request)
        return resp

    # async def asyncRequestStream(self, request: Union[GNRequest, AsyncGenerator[GNRequest, Any]]) -> AsyncGenerator[GNResponse, None]:
        
    #     if self._quik_core is None:
    #         raise RuntimeError("Not connected")

    #     queue = await self._quik_core.requestStream(request)

    #     while True:
    #         chunk = await queue.get()
    #         if chunk is None or chunk.command == 'gn:end-stream':
    #             break
    #         yield chunk