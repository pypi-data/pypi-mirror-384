# buildings_inventory.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class BuildingsInventory(GameClient):
    """Buildings inventory operations handler."""

    async def get_building_inventory(
        self,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve building inventory.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("sin", {})
                return response
            else:
                await self.send_json_message("sin", {})
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for building inventory response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting building inventory: {e}")
            return False

    async def store_building(
        self,
        building_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Store a building in inventory.
        
        Args:
            building_id: Building identifier to store
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("sob", {"OID": building_id})
                return response
            else:
                await self.send_json_message("sob", {"OID": building_id})
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for building store response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while storing building: {e}")
            return False

    async def sell_building_inventory(
        self,
        wod_id: int,
        amount: int,
        unique_id: int = -1,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Sell building from inventory.
        
        Args:
            wod_id: Building template identifier
            amount: Number of buildings to sell
            unique_id: Unique identifier (default: -1)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            sell_data = {"WID": wod_id, "AMT": amount, "UID": unique_id}
            if sync:
                response = await self.send_rpc("sds", sell_data)
                return response
            else:
                await self.send_json_message("sds", sell_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for building inventory sell response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while selling building inventory: {e}")
            return False