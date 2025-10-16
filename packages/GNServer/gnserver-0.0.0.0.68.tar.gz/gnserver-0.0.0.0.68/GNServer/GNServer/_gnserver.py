
import os
import sys
from typing import Optional, Union, Callable, List
from pathlib import Path
from KeyisBTools.cryptography.bytes import userFriendly, hash3

from KeyisBTools.models.serialization import deserialize
from KeyisBTools.cryptography import m1

from ._app import App
from ._client import AsyncClient
from .models import KDCObject


class GNServer(App):
    def __init__(self):
        """
        # GNServer
        """
        super().__init__()


    @staticmethod
    def _normalize_gn_server_crt(gn_server_crt: Union[str, bytes, Path]) -> bytes:
        if isinstance(gn_server_crt, Path):
            gn_server_crt_data = open(gn_server_crt, 'rb').read()
        elif isinstance(gn_server_crt, str):
            if os.path.isfile(gn_server_crt):
                gn_server_crt_data = open(gn_server_crt, 'rb').read()
            else:
                gn_server_crt_data = userFriendly.decode(gn_server_crt)
        else:
            gn_server_crt_data = gn_server_crt
        return gn_server_crt_data



    def run(
        self,
        domain: str,
        port: int,
        gn_server_crt: Union[str, bytes, Path],
        *,
        host: str = '0.0.0.0',
        idle_timeout: float = 20.0,
        wait: bool = True,
        run: Optional[Callable] = None,
        kdc_passive_key_sync_domains: List[str] = [],
        kdc_active_key_synchronization: bool = True
    ):
        
        self.domain = domain
        

        gn_server_crt_data = self._normalize_gn_server_crt(gn_server_crt)

        def _decode(data: bytes, domain: str, st=False):
            try:
                r = m1.fastDecrypt(data, hash3(domain.encode()))
                result = deserialize(r)
                return result
            except:
                if st:
                    raise Exception('Не удалось расшифровать gn_server_crt')
                else:
                    _ = gn_server_crt_data.decode() # type: ignore
                    _2 = userFriendly.decode(_)
                    return _decode(_2, domain, st=True)
        
        gn_server_crt_: dict = _decode(gn_server_crt_data, domain=domain) # type: ignore


        if 'dns_key' in gn_server_crt_:
            dns_key = gn_server_crt_['dns_key']

            if self.client._dns_key is None:
                self.client.setDNSkey(dns_key)


        if 'kdc_key' in gn_server_crt_:

            kdc_domain, kdc_key = gn_server_crt_['kdc_domain'], gn_server_crt_['kdc_key']
                
            kdc = KDCObject(self.domain, kdc_domain, kdc_key, kdc_passive_key_sync_domains, active_key_synchronization=kdc_active_key_synchronization)
            self.setKDC(kdc)


        if 'tls_certfile' in gn_server_crt_ and 'tls_keyfile' in gn_server_crt_:
            tls_certfile = gn_server_crt_['tls_certfile']
            tls_keyfile = gn_server_crt_['tls_keyfile']
        else:
            tls_certfile = None
            tls_keyfile = None



        return super().run(
            domain=domain,
            port=port,
            tls_certfile=tls_certfile, # type: ignore
            tls_keyfile=tls_keyfile, # type: ignore
            host=host,
            idle_timeout=idle_timeout,
            wait=wait,
            run=run
        )

    def runByVMHost(self):
        """
        # Запусить через VM-host

        Заупскает сервер через процесс vm-host
        """
        argv = sys.argv[1:]
        data_enc = argv[0]

        data: dict = deserialize(userFriendly.decode(data_enc)) # type: ignore

        if data['command'] == 'gn:vm-host:start':
            self.run(
                domain=data['domain'],
                port=data['port'],
                gn_server_crt=data.get('gn_server_crt'),
                host=data.get('host', '0.0.0.0')
            )
