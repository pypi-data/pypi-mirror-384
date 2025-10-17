import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class OuterRealms(GameClient):
    """Outer Realms operations handler."""

    async def get_outer_realms_points(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Retrieve Outer Realms points.
        
        Args:
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict, bool]: Outer Realms points data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            if sync:
                return await self.send_rpc("tsh", {})
            else:
                await self.send_json_message("tsh", {})
                return True
        except ConnectionError as e:
            logger.error(f"Connection error while getting Outer Realms points: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for Outer Realms points response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting Outer Realms points: {e}")
            return False

    async def choose_outer_realms_castle(
        self,
        castle_id: int,
        only_rubies: int = 0,
        use_rubies: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Choose castle in Outer Realms.
        
        Args:
            castle_id: The ID of the castle to choose.
            only_rubies: Flag to use only rubies (default: 0).
            use_rubies: Flag to use rubies (default: 0).
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict, bool]: Response data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"ID": castle_id, "OC2": only_rubies, "PWR": use_rubies, "GST": 3}
            if sync:
                return await self.send_rpc("tsc", data)
            else:
                await self.send_json_message("tsc", data)
                return True
        except ConnectionError as e:
            logger.error(f"Connection error while choosing Outer Realms castle: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for Outer Realms castle choice response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while choosing Outer Realms castle: {e}")
            return False

    async def get_outer_realms_token(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Get Outer Realms token.
        
        Args:
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict, bool]: Token data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"GST": 3}
            if sync:
                return await self.send_rpc("glt", data)
            else:
                await self.send_json_message("glt", data)
                return True
        except ConnectionError as e:
            logger.error(f"Connection error while getting Outer Realms token: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for Outer Realms token response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting Outer Realms token: {e}")
            return False

    async def login_outer_realms(self, token: str, sync: bool = True) -> Union[Dict, bool]:
        """
        Login to Outer Realms with token.
        Request cmd: 'tlep' → expected response cmd: 'lli'
        
        Args:
            token: The Outer Realms token to use for login.
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict, bool]: Login response data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"TLT": token}
            if sync:
                # folosim crpc ca să așteptăm 'lli' după ce trimitem 'tlep'
                return await self.send_crpc("tlep", data, expect="lli")
            else:
                await self.send_json_message("tlep", data)
                return True
        except ConnectionError as e:
            logger.error(f"Connection error while logging into Outer Realms: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for Outer Realms login response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while logging into Outer Realms: {e}")
            return False
