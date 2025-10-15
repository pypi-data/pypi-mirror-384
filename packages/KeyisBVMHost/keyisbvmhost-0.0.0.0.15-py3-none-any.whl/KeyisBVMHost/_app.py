import os
import re
import sys
import time
import signal
import asyncio
import datetime
import subprocess
from typing import Set, Tuple, Optional, Iterable, Union
from GNServer import App as _App, AsyncClient, GNRequest, GNResponse, Url, responses, GNServer as _GNServer
from KeyisBTools.models.serialization import serialize, deserialize
from KeyisBTools.cryptography.bytes import userFriendly

def restart_as_root():
    if os.geteuid() != 0: # type: ignore
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
restart_as_root()

def _kill_process_by_port(port: int):

    def _run(cmd: list[str]) -> Tuple[int, str, str]:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return p.returncode, p.stdout.strip(), p.stderr.strip()
        except FileNotFoundError:
            return 127, "", f"{cmd[0]} not found"

    def pids_from_fuser(port: int, proto: str) -> Set[int]:
        # fuser понимает 59367/udp и 59367/tcp (оба стека)
        rc, out, _ = _run(["fuser", f"{port}/{proto}"])
        if rc != 0:
            return set()
        return {int(x) for x in re.findall(r"\b(\d+)\b", out)}

    def pids_from_lsof(port: int, proto: str) -> Set[int]:
        # lsof -ti UDP:59367  /  lsof -ti TCP:59367
        rc, out, _ = _run(["lsof", "-ti", f"{proto.upper()}:{port}"])
        if rc != 0 or not out:
            return set()
        return {int(x) for x in out.splitlines() if x.isdigit()}

    def pids_from_ss(port: int, proto: str) -> Set[int]:
        # ss -H -uapn 'sport = :59367'  (UDP)  /  ss -H -tapn ... (TCP)
        flag = "-uapn" if proto == "udp" else "-tapn"
        rc, out, _ = _run(["ss", "-H", flag, f"sport = :{port}"])
        if rc != 0 or not out:
            return set()
        pids = set()
        for line in out.splitlines():
            # ... users:(("python3",pid=1234,fd=55))
            for m in re.finditer(r"pid=(\d+)", line):
                pids.add(int(m.group(1)))
        return pids

    def find_pids(port: int, proto: str | None) -> Set[int]:
        protos: Iterable[str] = [proto] if proto in ("udp","tcp") else ("udp","tcp")
        found: Set[int] = set()
        for pr in protos:
            # Порядок: fuser -> ss -> lsof (достаточно любого)
            found |= pids_from_fuser(port, pr)
            found |= pids_from_ss(port, pr)
            found |= pids_from_lsof(port, pr)
        # не убивать себя
        found.discard(os.getpid())
        return found

    def kill_pids(pids: Set[int]) -> None:
        if not pids:
            return
        me = os.getpid()
        for sig in (signal.SIGTERM, signal.SIGKILL): # type: ignore
            still = set()
            for pid in pids:
                if pid == me:
                    continue
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    continue
                except PermissionError:
                    print(f"[WARN] No permission to signal {pid}")
                    still.add(pid)
                    continue
                still.add(pid)
            if not still:
                return
            # подождём чуть-чуть
            for _ in range(10):
                live = set()
                for pid in still:
                    try:
                        os.kill(pid, 0)
                        live.add(pid)
                    except ProcessLookupError:
                        pass
                still = live
                if not still:
                    return
                time.sleep(0.1)

    def wait_port_free(port: int, proto: str | None, timeout: float = 3.0) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout:
            if not find_pids(port, proto):
                return True
            time.sleep(0.1)
        return not find_pids(port, proto)

    for proto in ("udp", "tcp"):
        pids = find_pids(port, proto)
    

        print(f"Гашу процессы на порту {port}: {sorted(pids)}")
        kill_pids(pids)

        if wait_port_free(port, proto):
            print(f"Порт {port} освобождён.")
        else:
            print(f"[ERROR] Не удалось освободить порт {port}. Возможно, другой netns/служба перезапускает процесс.")



from KeyisBTools.cryptography.sign import s1

import socket

def is_port_in_use(port: int, proto: str = "tcp") -> bool:
    if proto == "tcp":
        sock_type = socket.SOCK_STREAM
    elif proto == "udp":
        sock_type = socket.SOCK_DGRAM
    else:
        raise ValueError("proto должен быть 'tcp' или 'udp'")
    
    s = socket.socket(socket.AF_INET, sock_type)
    try:
        s.bind(("0.0.0.0", port))
    except OSError:
        return True
    finally:
        s.close()
    return False


class AsyncLogWriter:
    def __init__(self, path: str, flush_interval: int = 3):
        self.file = open(path, "a+")
        self.flush_interval = flush_interval
        self._stop = False
        self._start = False

    async def _flusher(self):
        while not self._stop:
            await asyncio.sleep(self.flush_interval)
            self.file.flush()

    def write(self, msg: str):
        self.file.write(msg + "\n")

        if not self._start:
            asyncio.create_task(self._flusher())
            self._start = True

    def close(self):
        self._stop = True
        self.file.flush()
        self.file.close()


class App():
    def __init__(self):
        self._app = _App()

        self._servers_start_files = {}

        self._access_key: Optional[str] = None

        self._default_venv_path = None
        self._default_TLS_paths = None
        self._log_dir_path: Optional[str] = None

        self._client = AsyncClient()

        self.__add_routes()



    def setAccessKey(self, key: str):
        self._access_key = key

    def setVenvPath(self, venv_path: str):
        self._default_venv_path = venv_path

    def setTLSPaths(self, cert_path: str, key_path: str) -> None:
        self._default_TLS_paths = (cert_path, key_path)

    def setLogDir(self, dir_path: str) -> None:
        if os.path.exists(dir_path):
            self._log_dir_path = dir_path
        else:
            raise Exception('Путь не найден')

    def writeLog(self, domain: str, msg: str):
        print(domain, msg)
        file: Optional[AsyncLogWriter] = self._servers_start_files[domain].get('_log_file')
        if file is not None:
            file.write(msg)


    def addServerStartFile(self,
                           domain: str,
                           file_path: str,
                           port: Optional[int] = None,
                           start_when_run: bool = False,
                           venv_path: Optional[str] = None,
                           vm_host: bool = False,
                           gn_server_crt: Optional[Union[str, bytes]] = None,
                           cert_path: Optional[str] = None,
                           key_path: Optional[str] = None,
                           host: str = '0.0.0.0',
                           log_path: Optional[str] = None
                           ):
        
        if log_path is None and self._log_dir_path is not None:
            log_path = self._log_dir_path + f'/{domain}/' + f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.log'

        if log_path and not os.path.exists(log_path):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

        gn_server_crt = _GNServer._normalize_gn_server_crt(gn_server_crt) if gn_server_crt is not None else None

        self._servers_start_files[domain] = {
            "domain": domain,
            "path": file_path,
            "port": port,
            "start_when_run": start_when_run,
            "venv_path": venv_path if venv_path is not None else self._default_venv_path,
            "vm_host": vm_host,
            "cert_path": cert_path if cert_path is not None else self._default_TLS_paths[0] if self._default_TLS_paths is not None else None,
            "key_path": key_path if key_path is not None else self._default_TLS_paths[1] if self._default_TLS_paths is not None else None,
            "host": host,
            "log_path": log_path,
            "gn_server_crt_data_raw_bytes": gn_server_crt,
            }

        
        if log_path is not None:
            file = AsyncLogWriter(log_path)
            
            self._servers_start_files[domain]["_log_file"] = file



    async def startLikeRun(self):
        for server in self._servers_start_files:
            if self._servers_start_files[server]["start_when_run"]:
                asyncio.create_task(self.startServer(server))


    async def startServer(self, domain: str, timeout: float = 30):
        if domain not in self._servers_start_files:
            self.writeLog(domain, f'No server start file found with domain: {domain}')
            raise ValueError(f"No server start file found with domain: {domain}")

        # Проверка что уже запущен
        res = await self.checkServerHealth(domain, timeout=1.0)
        if res[0]:
            return (f"Server already running: {domain}")

        server = self._servers_start_files[domain]
        path = server["path"]
        port = server["port"]
        venv_path = server["venv_path"]
        vm_host = server['vm_host']
        host = server['host']

        cert_path = server['cert_path']
        key_path = server['key_path']

        if vm_host and (cert_path is None or key_path is None):
            raise Exception('Не указаны сертификаты')

        if not os.path.isfile(path):
            raise ValueError(f"Server start file not found: {path}")

        if is_port_in_use(port, 'udp'):
            _kill_process_by_port(port)
            await asyncio.sleep(1)

        out_ = None

        if path.endswith('.py'):
            # выбираем python
            if venv_path is not None:
                if not os.path.isdir(venv_path):
                    raise ValueError(f"Virtual environment path not found: {venv_path}")
                python_executable = os.path.join(venv_path, 'bin', 'python')
                if not os.path.isfile(python_executable):
                    raise ValueError(f"Python executable not found in virtual environment: {python_executable}")
            else:
                python_executable = sys.executable

            if not vm_host:
                argv = {}
            else:
                argv = {
                    'command': 'gn:vm-host:start',
                    'domain': str(domain),
                    'port': str(port),
                    'host': str(host)
                }
            
            if cert_path is not None:
                argv['cert_path'] = cert_path

            if key_path is not None:
                argv['key_path'] = key_path

            
            if server['gn_server_crt_data_raw_bytes'] is not None:
                argv['gn_server_crt'] = server['gn_server_crt_data_raw_bytes']

            raw_argv = userFriendly.encode(serialize(argv))

            self.writeLog(domain, 'Server starting...')

            # асинхронный запуск процесса
            proc = await asyncio.create_subprocess_exec(
                python_executable, path, raw_argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            save_out = []

            async def log_stream(stream: asyncio.StreamReader, prefix: str):
                async for line in stream:
                    text = line.decode().rstrip()
                    save_out.append(text)
                    self.writeLog(domain, f"{prefix}: {text}")

            # запускаем таски на чтение stdout/stderr
            asyncio.create_task(log_stream(proc.stdout, "OUT"))
            asyncio.create_task(log_stream(proc.stderr, "ERR"))

            try:
                # ждём чуть-чуть: если процесс сразу сдохнет — фиксируем
                returncode = await asyncio.wait_for(proc.wait(), timeout=3)
                self.writeLog(domain, f"Process exited with code {returncode}")
                save_out.clear()
            except asyncio.TimeoutError:
                self.writeLog(domain, "Process timed out")
                out_ = '\n'.join(save_out)

        else:
            self.writeLog(domain, 'Server starting...')
            await asyncio.create_subprocess_exec(
                path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )

        r = await self.checkServerHealth(domain, timeout=timeout, out=out_)
        self.writeLog(domain, f'Server checkServerHealth status-> {r[0]}')
        return r


    async def _send_message_to_server(self, domain: str, path: str, payload: Optional[dict] = None, timeout: float = 1.0, res: list = []) -> Optional[GNResponse]:
        port = self._servers_start_files[domain].get("port")
        if port is None:
            raise ValueError(f"No port specified for server: {domain}")

        if path.startswith('/'):
            path = path[1:]

        c = self._client.request(GNRequest('POST', Url(f'gn://127.0.0.1:{port}/!gn-vm-host/{path}'), payload=payload), reconnect_wait=2)
        

        print(f'send request timeout: {timeout} (port: {port})')

        try:
            result = await asyncio.wait_for(c, timeout=timeout)
        except asyncio.TimeoutError:
            result = None
        
        print(f'result -> {result}')
        
        res.append(result)

    async def checkServerHealth(self, domain: str, timeout: float = 3.0, interval=5, out: Optional[str] = None):
        loop = asyncio.get_event_loop()
        end = loop.time() + timeout
        res = []
        count = 0
        while loop.time() < end:
            loop.create_task(self._send_message_to_server(domain, '/ping', timeout=timeout - interval * count, res=res))
            count+=1

            await asyncio.sleep(0.05)

            if res != []:
                return (True, out, res[0])
            else:
                await asyncio.sleep(interval)
            
        return (False, out, None)
        


    def stopServer(self, domain: str):
        if domain in self._servers_start_files:
            server = self._servers_start_files[domain]
            port = server["port"]
            if port is not None:
                _kill_process_by_port(port)
            else:
                raise ValueError(f"No port specified for server: {domain}")
        else:
            raise ValueError(f"No server start file found with domain: {domain}")

    async def reloadServer(self, domain: str, timeout: float = 1):
        if domain in self._servers_start_files:
            self.stopServer(domain)
            await asyncio.sleep(timeout)
            return await self.startServer(domain)
        else:
            raise ValueError(f"No server start file found with domain: {domain}")

    def run(self,
            domain,
            port,
            cert_path: str,
            key_path: str,
            *,
            host: str = '0.0.0.0',
            idle_timeout: float = 20.0,
            wait: bool = True
            ):
        

        self._app.run(
            domain=domain,
            port=port,
            tls_certfile=cert_path,
            tls_keyfile=key_path,

            host=host,
            idle_timeout=idle_timeout,
            wait=wait,
            run=self.startLikeRun,
        )


    def __resolve_access_key(self, request: GNRequest) -> bool:
        if self._access_key is None:
            raise ValueError("Access key is not set.")
        
        sign = request.cookies.get('vm-host-sign')

        if sign is None:
            return False

        return s1.verify(self._access_key.encode(), sign, 60)

    def __add_routes(self):
        @self._app.route('POST', '/ping')
        async def ping_handler(request: GNRequest, domain: Optional[str] = None, timeout: float = 3.0):
            if not self.__resolve_access_key(request):
                return None
            
            if not domain:
                return GNResponse('ok', {'time': datetime.datetime.now(datetime.timezone.utc).isoformat()})
            else:
                try:
                    result = await self.checkServerHealth(domain, timeout=timeout)
                    if result[0]:
                        try:
                            _time = result[2].payload.get('time')
                        except:
                            _time = None
                        return GNResponse('ok', {'message': f'Server {domain} is alive.', 'time': _time})
                    else:
                        return GNResponse('error', {'error': f'Server {domain} is not responding.'})
                except ValueError as e:
                    return GNResponse('error', {'error': str(e)})
                
        @self._app.route('GET', '/servers')
        async def list_servers_handler(request: GNRequest):
            if not self.__resolve_access_key(request):
                return None
            
            servers_info = []
            for server in self._servers_start_files.values():
                servers_info.append(server['domain'])
            return GNResponse('ok', {'servers': servers_info})



            

        @self._app.route('POST', '/start-server')
        async def start_server_handler(request: GNRequest, domain: str = ''):
            if not self.__resolve_access_key(request):
                return None
            
            if not domain:
                return GNResponse('error', {'error': 'Server domain is required.'})
            try:
                result = await self.startServer(domain)
                if result[0]:
                    return GNResponse('ok', {'message': f'Server {domain} started.'})
                else:
                    return GNResponse('error', {'error': f'Server {domain} failed to start within the timeout period. {result[1]}'})
            except ValueError as e:
                return GNResponse('error', {'error': str(e)})
            
            

        @self._app.route('POST', '/reload-server')
        async def reload_server_handler(request: GNRequest, domain: str = '', timeout: float = 0.5):
            if not self.__resolve_access_key(request):
                return None

            if not domain:
                return GNResponse('error', {'error': 'Server domain is required.'})

            try:
                result = await self.reloadServer(domain, timeout)
                if result[0]:
                    return GNResponse('ok', {'message': f'Server {domain} reloaded.'})
                else:
                    return GNResponse('error', {'error': f'Server {domain} failed to reload within the timeout period. {result[1]}'})
            except ValueError as e:
                return GNResponse('error', {'error': str(e)})
        
        @self._app.route('POST', '/stop-server')
        async def stop_server_handler(request: GNRequest, domain: str = ''):
            if not self.__resolve_access_key(request):
                return None

            if not domain:
                return GNResponse('error', {'error': 'Server domain is required.'})

            try:
                self.stopServer(domain)
                return GNResponse('ok', {'message': f'Server {domain} stopped.'})
            except ValueError as e:
                return GNResponse('error', {'error': str(e)})
        
        @self._app.route('POST', '/start-all-servers')
        async def start_all_servers_handler(request: GNRequest):
            if not self.__resolve_access_key(request):
                return None

            for server in self._servers_start_files:
                try:
                    result = await self.startServer(server)
                    if not result:
                        return GNResponse('error', {'error': f'Server {server} failed to start within the timeout period.'})
                except ValueError as e:
                    return GNResponse('error', {'error': str(e)})
        
        @self._app.route('POST', '/stop-all-servers')
        async def stop_all_servers_handler(request: GNRequest):
            if not self.__resolve_access_key(request):
                return None

            for server in self._servers_start_files:
                try:
                    self.stopServer(server)
                except ValueError as e:
                    return GNResponse('error', {'error': str(e)})

            return GNResponse('ok', {'message': 'All servers stopped.'})
        
        @self._app.route('POST', '/reload-all-servers')
        async def reload_all_servers_handler(request: GNRequest, timeout: float = 0.5):
            if not self.__resolve_access_key(request):
                return None

            for server in self._servers_start_files:
                try:
                    result = await self.reloadServer(server, timeout)
                    if not result:
                        return GNResponse('error', {'error': f'Server {server} failed to reload within the timeout period.'})
                except ValueError as e:
                    return GNResponse('error', {'error': str(e)})
