# extension.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Extension(GameClient):
    """Extension operations handler."""

    async def buy_extension(
        self,
        x: int,
        y: int,
        rotated: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Buy and place extension.
        
        Args:
            x: X coordinate
            y: Y coordinate
            rotated: Rotation flag
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            extension_data = {"X": x, "Y": y, "R": rotated, "CT": 1}
            if sync:
                response = await self.send_rpc("ebe", extension_data)
                return response
            else:
                await self.send_json_message("ebe", extension_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for extension purchase response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while buying extension: {e}")
            return False

    async def collect_extension_gift(
        self,
        building_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Collect extension gift.
        
        Args:
            building_id: Building identifier
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("etc", {"OID": building_id})
                return response
            else:
                await self.send_json_message("etc", {"OID": building_id})
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for extension gift collection response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while collecting extension gift: {e}")
            return False