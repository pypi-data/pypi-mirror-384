import asyncio
import json
import random
import re
import inspect
from collections import deque
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable, Deque

import aiohttp
from loguru import logger
from websockets.asyncio.client import connect, ClientConnection
from websockets.exceptions import ConnectionClosed, InvalidStatus, InvalidMessage

# Configul tău existent: URL, WS_HEADERS (fără zstd), CLIENT_ORIGIN, VERSION, DEFAULT_UA_LIST, GAME_VERSION_URL etc.
from ._cfg import *  

Handler = Callable[[Any], Union[Any, Awaitable[Any]]]


class GameClient:

    """GGXS websocket engine"""

    def __init__(
        self,
        url: str,
        server_header: str,
        username: str,
        password: str,
    ) -> None:
        self.url = url
        self.server_header = server_header
        self.username = username
        self.password = password

        self.ws: Optional[ClientConnection] = None
        self.connected = asyncio.Event()
        self._stop_event = asyncio.Event()
        self._tasks: List[asyncio.Task] = []

        self._msg_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._pending_futures: Dict[str, Deque[asyncio.Future]] = {}
        self.user_agent = random.choice(DEFAULT_UA_LIST)

        # HTTP session pentru 3.13 – fără decompresie automată (evită zstd implicit)
        self._http_session: Optional[aiohttp.ClientSession] = None

# ─────────────────────────────────────────────────────────────
# Lifecycle
# ─────────────────────────────────────────────────────────────
    async def connect(self) -> None:
        """Main loop: connect + reconnect cu backoff."""
        delay, max_delay = 5.0, 60.0
        while not self._stop_event.is_set():
            try:
                await self._run_connection_session()
                delay = 5.0  # reset după o sesiune OK
            except (ConnectionClosed, asyncio.CancelledError):
                self.connected.clear()
                if self._stop_event.is_set():
                    break
            except Exception as e:
                logger.error(f"Error during connection session: {e}")
                self.connected.clear()
                if self._stop_event.is_set():
                    break
            # backoff reconectare
            if not self._stop_event.is_set():
                logger.info(f"Attempting to reconnect in {int(delay)} seconds...")
                await asyncio.sleep(delay)
                delay = min(int(delay * 1.5), max_delay)
        logger.info("Client shutdown complete.")

    async def shutdown(self) -> None:
        self._stop_event.set()
        await self.disconnect()
        current_task = asyncio.current_task()
        tasks_to_cancel = [t for t in self._tasks if t is not current_task and not t.done()]
        for task in tasks_to_cancel:
            task.cancel()
        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
        # close HTTP session
        if self._http_session is not None:
            try:
                await self._http_session.close()
            except Exception:
                pass
            self._http_session = None

    async def disconnect(self) -> None:
        self.connected.clear()
        self._cancel_pending_futures()
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self.ws = None
        logger.info("Disconnected!")

    # ─────────────────────────────────────────────────────────────
    # Session (WS handshake + tasks)
    # ─────────────────────────────────────────────────────────────
    async def _run_connection_session(self) -> None:
        """Single WS session with safe handshake (no WS compression)."""
        try:
            async with connect(
                self.url,
                origin=CLIENT_ORIGIN,
                user_agent_header=self.user_agent,
                additional_headers=WS_HEADERS,  # fără Accept-Encoding: zstd (ideal: identity)
                compression=None,               # NU negocia permessage-deflate
                max_size=2**20,
                open_timeout=20,
                close_timeout=10,
            ) as ws:
                self.ws = ws
                self.connected.set()
                logger.info(f"GGClient connected! {VERSION}")

                tasks = [
                    asyncio.create_task(self._listener(), name="listener"),
                    asyncio.create_task(self.keep_alive(), name="keep_alive"),
                    asyncio.create_task(self._nch(), name="nch"),
                ]

                if not await self._init():
                    await self._cancel_tasks(tasks)
                    await self.disconnect()
                    return

                tasks.append(asyncio.create_task(self.run_jobs(), name="run_jobs"))
                self._tasks = tasks

                try:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
                    for t in done:
                        if t.exception():
                            for p in pending:
                                if not p.done():
                                    p.cancel()
                            if pending:
                                await asyncio.gather(*pending, return_exceptions=True)
                            raise t.exception()
                except Exception as e:
                    logger.error(f"Task error: {e}")
                    await self._cancel_tasks(tasks)
                    raise
                finally:
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)

        # Handshake eșuat (ex. 400). Nu citim body-ul (poate fi zstd); doar backoff.
        except (InvalidStatus, InvalidMessage) as e:
            logger.error(f"WS handshake failed: {e}")
            await asyncio.sleep(5)
            raise

    async def _cancel_tasks(self, tasks: List[asyncio.Task]) -> None:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def run_jobs(self):
        """Add your jobs here"""
        pass

    # ─────────────────────────────────────────────────────────────
    # WS IO
    # ─────────────────────────────────────────────────────────────
    async def _listener(self) -> None:
        try:
            async for raw in self.ws:
                if self._stop_event.is_set():
                    break
                text = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else raw
                msg = self._parse_message(text)
                await self._msg_queue.put(msg)
                await self._handle_message_callbacks(msg)
        except ConnectionClosed:
            logger.warning("Connection closed, stopping listener...")
            self._cancel_pending_futures()
        except asyncio.CancelledError:
            logger.warning("Listener task cancelled.")
            self._cancel_pending_futures()
        except Exception as e:
            logger.error(f"Unexpected error in listener: {e}")
            self._cancel_pending_futures()

    async def send(self, message: str) -> None:
        if not self.ws or not self.connected.is_set():
            raise RuntimeError("GGClient not connected!")
        await self.ws.send(message)

    async def receive(self) -> Dict[str, Any]:
        return await self._msg_queue.get()

    # ─────────────────────────────────────────────────────────────
    # Protocol helpers
    # ─────────────────────────────────────────────────────────────
    async def send_message(self, parts: List[str]) -> None:
        msg = "%".join(["", *parts, ""])  # %xt%...%
        await self.send(msg)

    async def send_raw_message(self, command: str, data: List[Any]) -> None:
        json_parts = [json.dumps(x) if isinstance(x, (dict, list)) else str(x) for x in data]
        await self.send_message(["xt", self.server_header, command, "1", *json_parts])

    async def send_json_message(self, command: str, data: Dict[str, Any]) -> None:
        await self.send_message(["xt", self.server_header, command, "1", json.dumps(data)])

    async def send_xml_message(self, t: str, action: str, r: str, data: str) -> None:
        await self.send(f"<msg t='{t}'><body action='{action}' r='{r}'>{data}</body></msg>")

    def _parse_message(self, message: str) -> Dict[str, Any]:
        # XML path
        if message.startswith("<"):
            m = re.search(r"<msg t='(.*?)'><body action='(.*?)' r='(.*?)'>(.*?)</body></msg>", message)
            if not m:
                return {"type": "xml", "payload": {"t": None, "action": None, "r": None, "data": message}}
            t_val, action, r_val, data = m.groups()
            return {"type": "xml", "payload": {"t": t_val, "action": action, "r": int(r_val), "data": data}}

    
        # %xt% path
        parts = message.strip("%").split("%")
        if len(parts) < 4:
            return {"type": "raw", "payload": {"command": None, "status": None, "data": message}}
        cmd = parts[1]
        try:
            status = int(parts[3])
        except ValueError:
            status = None
        raw = "%".join(parts[4:])
        try:
            data = json.loads(raw)
        except Exception:
            data = raw
        return {"type": "json", "payload": {"command": cmd, "status": status, "data": data}}

# ─────────────────────────────────────────────────────────────
# Routing & Futures
# ─────────────────────────────────────────────────────────────
    async def _handle_message_callbacks(self, msg: Dict[str, Any]) -> None:
        payload = msg.get("payload", {})
        cmd_raw = payload.get("command") or payload.get("action")
        cmd = str(cmd_raw).lower() if cmd_raw else None  # normalize: GAM -> on_gam
        if not cmd:
            return
        data = payload.get("data")
        status = payload.get("status")

        # livrează FIFO către orice future înregistrat pentru acest cmd (ignoră ACK=1)
        if cmd in self._pending_futures and (status is None or status != 1):
            q = self._pending_futures[cmd]
            while q:
                fut = q.popleft()
                if not fut.done():
                    fut.set_result(data)
                    break
            if not q:
                self._pending_futures.pop(cmd, None)

        # dispatch la handler on_<cmd>
        method_name = f"on_{cmd}"
        if hasattr(self, method_name):
            handler: Handler = getattr(self, method_name)
            try:
                if inspect.iscoroutinefunction(handler):
                    asyncio.create_task(handler(data))
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in handler {method_name}: {e}")

    def _cancel_pending_futures(self) -> None:
        for cmd, q in list(self._pending_futures.items()):
            while q:
                fut = q.popleft()
                if not fut.done():
                    fut.set_exception(ConnectionError("Connection lost"))
            self._pending_futures.pop(cmd, None)

    def _register_future(self, command: str) -> asyncio.Future:
        fut = asyncio.get_running_loop().create_future()
        q = self._pending_futures.setdefault(command, deque())
        q.append(fut)
        return fut

    async def send_rpc(self, command: str, data: Dict[str, Any], timeout: float = 5.0) -> Any:

        fut = self._register_future(command)  # înregistrează ÎNAINTE de send
        await self.send_json_message(command, data)
        try:
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            q = self._pending_futures.get(command)
            if q and fut in q:
                try:
                    q.remove(fut)
                except ValueError:
                    pass
                if not q:
                    self._pending_futures.pop(command, None)
            if not fut.done():
                fut.cancel()
            raise

    async def send_crpc(self, command: str, data: Dict[str, Any], expect: str, timeout: float = 5.0) -> Any:
        fut = self._register_future(expect)
        await self.send_json_message(command, data)
        try:
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            q = self._pending_futures.get(expect)
            if q and fut in q:
                try:
                    q.remove(fut)
                except ValueError:
                    pass
                if not q:
                    self._pending_futures.pop(expect, None)
            if not fut.done():
                fut.cancel()
            logger.error(f"Timeout waiting for response '{expect}' after sending '{command}'")
            return False

    async def send_hrpc(self, command: str, data: Dict[str, Any], handler: Handler, timeout: float = 5.0) -> Any:
        fut = self._register_future(command)
        await self.send_json_message(command, data)
        resp_data = await asyncio.wait_for(fut, timeout)
        result = handler(resp_data)
        if inspect.isawaitable(result):
            await result
        return result

# ─────────────────────────────────────────────────────────────
# Protocol specifics (WS): init + login pe WS
# ─────────────────────────────────────────────────────────────
    async def _init(self) -> bool:
        """Choose between login/register"""
        await self._init_socket()
        return await self.login(self.username, self.password)

    async def _init_socket(self) -> None:
        try:
            await self.send_xml_message("sys", "verChk", "0", "<ver v='166' />")
            await self.send_xml_message(
                "sys", "login", "0",
                f"<login z='{self.server_header}'><nick><![CDATA[]]></nick><pword><![CDATA[1123010%fr%0]]></pword></login>"
            )
            await self.send_xml_message("sys", "autoJoin", "-1", "")
            await self.send_xml_message("sys", "roundTrip", "1", "")
        except Exception as e:
            logger.error(f"Error during socket initialization: {e}")
            raise

    async def login(self, username: str, password: str) -> bool:
        if not self.connected.is_set():
            logger.error("Not connected yet!")
            return False
        try:
            payload = {
                "CONM": 175,
                "RTM": 24,
                "ID": 0,
                "PL": 1,
                "NOM": username,
                "PW": password,
                "LT": None,
                "LANG": "fr",
                "DID": "0",
                "AID": "1674256959939529708",
                "KID": "",
                "REF": "https://empire.goodgamestudios.com",
                "GCI": "",
                "SID": 9,
                "PLFID": 1,
            }
            resp = await self.send_rpc("lli", payload, timeout=5.0)

            # serverul uneori răspunde cu dict gol / non-dict pe success
            if not isinstance(resp, dict):
                logger.success("Login successful!")
                return True
            if isinstance(resp, dict) and not resp:
                logger.warning("Wrong username or password!")
                return False
            if isinstance(resp, dict) and "CD" in resp:
                cooldown_value = resp["CD"]
                logger.debug(f"Connection locked by the server! Reconnect in {cooldown_value} sec!")
                await asyncio.sleep(cooldown_value)
                return False
            logger.info("Login successful!")
            return True
        except asyncio.TimeoutError:
            logger.error("Login timeout - server not responding")
            return False
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False

    # ─────────────────────────────────────────────────────────────
    # Periodic tasks (special ping + nch)
    # ─────────────────────────────────────────────────────────────
    async def keep_alive(self, interval: int = 60) -> None:
        """Trimite ping-ul *special* cerut de server."""
        try:
            await self.connected.wait()
            while self.connected.is_set() and not self._stop_event.is_set():
                await asyncio.sleep(interval)
                try:
                    await self.send_raw_message("pin", ["<RoundHouseKick>"])
                except Exception as e:
                    logger.error(f"Error sending keep-alive: {e}")
                    break
        except asyncio.CancelledError:
            logger.warning("Keep-alive task cancelled.")

    async def _nch(self, interval: int = 360) -> None:
        """Trimite periodic mesajul NCH."""
        try:
            await self.connected.wait()
            while self.connected.is_set() and not self._stop_event.is_set():
                await asyncio.sleep(interval)
                try:
                    await self.send(f"%xt%{self.server_header}%nch%1%")
                except Exception as e:
                    logger.error(f"Error sending NCH: {e}")
                    break
        except asyncio.CancelledError:
            logger.warning("NCH task cancelled.")

# ─────────────────────────────────────────────────────────────
# HTTP helpers (aiohttp 3.13) – fără auto-decompresie
# ─────────────────────────────────────────────────────────────
    async def _get_http_session(self) -> aiohttp.ClientSession:
        if self._http_session is None or self._http_session.closed:
            # În 3.13 dezactivăm decompresia implicită – comportament ca 3.12
            self._http_session = aiohttp.ClientSession(
                auto_decompress=False,
                raise_for_status=False,
                headers=AD_HEADERS,
                )
        return self._http_session

    async def fetch_game_db(self) -> Dict[str, Any]:
        """Exemplu de fetch folosind aiohttp 3.13, fără decompresie automată."""
        session = await self._get_http_session()
        async with session.get(GAME_VERSION_URL) as resp:
            resp.raise_for_status()
            text = await resp.text()
            _, version = text.strip().split("=", 1)
            version = version.strip()
        db_url = f"https://empire-html5.goodgamestudios.com/default/items/items_v{version}.json"
        async with session.get(db_url) as db_resp:
            db_resp.raise_for_status()
            return await db_resp.json()


