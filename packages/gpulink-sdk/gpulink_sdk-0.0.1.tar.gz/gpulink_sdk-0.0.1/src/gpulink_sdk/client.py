from websockets.exceptions import ConnectionClosed, WebSocketException
from typing import Optional, List, Dict, Any, Callable, Awaitable
import websockets
import traceback
import datetime
import asyncio
import base64
import hashlib
import unicodedata
import inspect
import httpx
import time
import json
import re
from gpulink_sdk import constants

base_httpx_timeout = httpx.Timeout(15.0, connect=10.0)

def time_str():
    return datetime.datetime.now().strftime("%d/%m %H:%M:%S")
def bits_to_base64(bits: str) -> str:
    if len(bits) != 32 or any(c not in '01' for c in bits):
        raise ValueError("Input must be a 32-character string of only '0' or '1'.")
    value = int(bits, 2)
    byte_data = value.to_bytes(4, byteorder='big')
    return base64.b64encode(byte_data).decode('ascii').rstrip('=')
def base64_to_bits(b64_str: str) -> str:
    padded = b64_str + '=' * ((4 - len(b64_str) % 4) % 4)
    byte_data = base64.b64decode(padded)
    value = int.from_bytes(byte_data, byteorder='big')
    return format(value, '032b')
def gpu_list_to_base64(gpu_ids: list[int]) -> str:
    if any(not (0 <= i < constants.MAX_GPUS_PER_MACHINE) for i in gpu_ids):
        raise ValueError("GPU indices must be between 0 and 31 inclusive.")
    bits = ''.join('1' if i in gpu_ids else '0' for i in range(32))
    return bits_to_base64(bits)
def base64_to_gpu_list(b64_str: str) -> list[int]:
    bits = base64_to_bits(b64_str)
    return [i for i, bit in enumerate(bits) if bit == '1']
def sha256_b64(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    digest = hashlib.sha256(s.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")
def to_uuid_format(s: str) -> str:
    s = s.replace("-", "").lower()
    if len(s) != 32:
        raise ValueError("Received invalid UID")
    parts = [s[:8], s[8:12], s[12:16], s[16:20], s[20:]]
    return "-".join(parts)

logging_enabled=False

class log:
    def success (self, message):
        global logging_enabled
        if not logging_enabled:
            return
        print(f"\033[92m[GPULINK-SDK] [SUCCESS] {time_str()} | {message}\033[0m")
    def warning (self, message):
        global logging_enabled
        if not logging_enabled:
            return
        print(f"\033[33m[GPULINK-SDK] [WARNING] {time_str()} | {message}\033[0m")
    def error (self, message):
        global logging_enabled
        if not logging_enabled:
            return
        print(f"\033[91m[GPULINK-SDK] [ERROR] {time_str()} | {message}\033[0m")
    def info (self, message):
        global logging_enabled
        if not logging_enabled:
            return
        print(f"\033[94m[GPULINK-SDK] [INFO] {time_str()} | {message}\033[0m")

class GPULinkClient:
    def __init__(self, api_key: str, report_gpu_requirements: Callable[..., Awaitable[Any]], show_logs=True):
        global logging_enabled
        self._api_key = api_key
        self.report_gpu_requirements = report_gpu_requirements

        logging_enabled = bool(show_logs)

        self.current_websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.is_running = False

        self.reconnect_delay = float(constants.INIT_WS_RECONNECT_DELAY)

        self.banned_till = 0

        self.logger = log()
        self.last_reported_hash = None
    
    def _reset_reconnect_delay(self):
        """Reset reconnect delay to initial value."""
        self.reconnect_delay = float(constants.INIT_WS_RECONNECT_DELAY)
    
    def _increase_reconnect_delay(self):
        """Increase reconnect delay with exponential backoff."""
        self.reconnect_delay = min(
            self.reconnect_delay * constants.WS_RECONNECT_BACKOFF_MULTIPLIER,
            constants.MAX_WS_RECONNECT_DELAY
        )

    async def _connect_websocket(self) -> bool:
        ws_url = f"wss://{constants.BASE_API}/gpu-allowance-api?api_token={self._api_key}"

        try:
            self.logger.info(f"Connecting to WebSocket")
            self.current_websocket = await asyncio.wait_for(
                websockets.connect(
                    ws_url,
                    ping_interval=constants.WS_PING_INTERVAL,
                    ping_timeout=constants.WS_TIMEOUT,
                    close_timeout=5
                ),
                timeout=constants.WS_TIMEOUT
            )
            
            self.is_connected = True
            self._reset_reconnect_delay()
            self.logger.success(f"Connected to WebSocket")
            return True
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout connecting to WebSocket")
        except Exception as e:
            self.logger.warning(f"Failed to connect to WebSocket")
            #print(traceback.format_exc())
        
        return False

    async def _disconnect_websocket(self):
        """Safely disconnect the current websocket."""
        if self.current_websocket:
            try:
                await asyncio.wait_for(self.current_websocket.close(), timeout=5)
            except Exception as e:
                self.logger.debug(f"Error closing websocket: {e}")
            finally:
                self.current_websocket = None
                self.is_connected = False
    async def _websocket_manager(self):
        """Manage websocket connection with automatic reconnection."""
        while self.is_running:
            try:
                remaining_ban_time = self.banned_till - time.time()
                self.authorized = False
                if remaining_ban_time > 0.1:
                    self.logger.error(f"Invalid Credentials, reconnect try in {remaining_ban_time:.2f} s")
                    await asyncio.sleep(remaining_ban_time)
                
                # Try to connect if not connected
                if not self.is_connected:
                    if await self._connect_websocket():
                        # Start receiver task
                        receiver_task = asyncio.create_task(self._websocket_receiver())
                        await receiver_task
                    else:
                        # Connection failed, wait before retry
                        self._increase_reconnect_delay()
                        self.logger.info(f"Retrying connection in {self.reconnect_delay:.1f}s")
                        await asyncio.sleep(self.reconnect_delay)
                
                # Clean up disconnected websocket
                if not self.is_connected:
                    await self._disconnect_websocket()
                self.authorized = False
            except Exception as e:
                self.logger.error(f"Error in websocket manager: {e}")
                self.authorized = False
                await self._disconnect_websocket()
                await asyncio.sleep(self.reconnect_delay)
            self.logger.error("Disconnected from remote")
    
    async def _websocket_receiver(self):
        """Handle incoming websocket messages."""
        while self.is_connected and self.current_websocket:
            try:
                message = await asyncio.wait_for(
                    self.current_websocket.recv(),
                    timeout=constants.WS_TIMEOUT
                )
                
                if message == "BAN_15":
                    self.banned_till = time.time() + 15 * 60
                elif message == "BAN_30":
                    self.banned_till = time.time() + 30 * 60
                elif message == "AUTH_SUCCESS":
                    self.authorized = True
                    self.logger.success("Authorized to remote")
                else:
                    try:
                        data = json.loads(message)
                        if type(data) == dict:
                            data_keys = data.keys()
                            if "error" in data_keys:
                                self.logger.error(f"Remote sent error: {str(data.get('error'))}")
                            elif "data" in data_keys:
                                this_hash = sha256_b64(message)
                                await self.current_websocket.send(json.dumps({
                                    "hash": this_hash
                                }))
                                if self.last_reported_hash != this_hash:
                                    final_data = {}
                                    for uid in data["data"].keys():
                                        c = data["data"][uid]
                                        final_data[to_uuid_format(uid)] = {
                                            "needed_gpus": base64_to_gpu_list(c.get('n')) if isinstance(c.get('n'), str) else [],
                                            "available_gpus": base64_to_gpu_list(c.get('f')) if isinstance(c.get('f'), str) else []
                                        }
                                    await self.report_gpu_requirements(final_data)
                                self.last_reported_hash = this_hash
                        #self.logger.info(f"Received message: {data}")
                    except json.JSONDecodeError:
                        if message[:6] != "Echo: ":
                            self.logger.warning(f"Received non-JSON message: {message}")
                    
            except asyncio.TimeoutError:
                self.logger.warning("Websocket receive timeout")
                break
            except ConnectionClosed:
                self.logger.info("Websocket connection closed")
                break
            except WebSocketException as e:
                self.logger.error(f"Websocket error: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in websocket receiver: {e}")
                break
        
        self.is_connected = False
    
    async def _heartbeat_service(self):
        while self.is_running:
            try:
                if self.is_connected and self.current_websocket:
                    await self.current_websocket.send(json.dumps({
                        "hb": True
                    }))
            except Exception as e:
                pass
            await asyncio.sleep(2)
    
    async def service(self):
        if not inspect.iscoroutinefunction(self.report_gpu_requirements):
            raise TypeError("report_gpu_requirements must be async!")
        if self.is_running:
            self.logger.warning("Service is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting service")
        try:
            # Start websocket manager and sender tasks
            self.websocket_task = asyncio.create_task(self._websocket_manager())
            # Wait for both tasks
            await asyncio.gather(self.websocket_task, self._heartbeat_service())
        except Exception as e:
            self.logger.error(f"Service error: {e}")
        finally:
            await self.stop()

    async def submit_available_gpus(self, data: dict):
        if not isinstance(data, dict):
            raise Exception("Data must be in format {\"<uid>\": [<available gpu ids>]}")
        to_submit_data = {}
        for key in data.keys():
            key_cleaned = key.replace('-', '')
            if re.fullmatch(r'[0-9a-fA-F]{32}', key_cleaned):
                value = data[key]
                if not isinstance(value, list):
                    raise Exception(f"UID \"{key}\" value isn't a valid array of available gpu ids")
                to_submit_data[key_cleaned] = gpu_list_to_base64(value)
            else:
                raise Exception(f"\"{key}\" is not valid kubernetes uid")
        if self.is_connected and self.current_websocket and self.authorized:
            try:
                await self.current_websocket.send(json.dumps({
                    "available_gpus_submit": to_submit_data
                }))
            except Exception as ei:
                self.logger.error(f"Failed sending submit_available_gpus {str(ei)}")
        else:
            self.logger.error("WebSocket not connected, can't submit_available_gpus")

    async def get_deployer_image(self):
        async with httpx.AsyncClient(timeout=base_httpx_timeout) as client:
            response = await client.get(f"https://{constants.BASE_API}/deployer_image.json")
            response.raise_for_status()
            json_res = response.json()
            if isinstance(json_res.get('image'), str):
                return json_res.get('image')
            else:
                raise Exception("Can't get deployer image")
    async def list_machines(self):
        async with httpx.AsyncClient(timeout=base_httpx_timeout) as client:
            response = await client.get(f"https://{constants.BASE_API}/list_machines", headers={"Authorization": f"Bearer {self._api_key}"})
            response.raise_for_status()
            r = response.json()
            if isinstance(r, list):
                parsed_res = []
                for item in r:
                    parsed_res.append({
                        "uid": to_uuid_format(item["uid"]),
                        "node_name": item["node_name"],
                        "last_online": item["last_online"],
                        "net": item["net"]
                    })
                return parsed_res
            else:
                raise Exception("Result not list")
    async def announce_machine(self, data):
        async with httpx.AsyncClient(timeout=base_httpx_timeout) as client:
            response = await client.post(f"https://{constants.BASE_API}/announce_machine", headers={"Authorization": f"Bearer {self._api_key}"}, params=data)
            response.raise_for_status()
            return response.json()