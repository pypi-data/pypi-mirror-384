# refinery.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Refinery(GameClient):
    """Refinery operations handler."""

    async def refinery_get_queue(
        self,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve refinery production queue.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("crin", {})
                return response
            else:
                await self.send_json_message("crin", {})
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for refinery queue response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting refinery queue: {e}")
            return False

    async def produce_materials(
        self,
        kingdom: int,
        castle_id: int,
        building_id: int,
        item_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Produce materials in refinery.
        
        Args:
            kingdom: Kingdom identifier
            castle_id: Castle identifier
            building_id: Building identifier
            item_id: Item identifier to produce
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            production_data = {
                "KID": kingdom,
                "AID": castle_id,
                "OID": building_id,
                "PWR": 0,
                "CRID": item_id
            }
            
            if sync:
                response = await self.send_rpc("crst", production_data)
                return response
            else:
                await self.send_json_message("crst", production_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for materials production response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while producing materials: {e}")
            return False

    async def cancel_materials_production(
        self,
        kingdom: int,
        castle_id: int,
        building_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Cancel materials production in refinery.
        
        Args:
            kingdom: Kingdom identifier
            castle_id: Castle identifier
            building_id: Building identifier
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            cancel_data = {
                "KID": kingdom,
                "AID": castle_id,
                "OID": building_id,
                "S": 0,
                "ST": "queue"
            }
            
            if sync:
                response = await self.send_rpc("crca", cancel_data)
                return response
            else:
                await self.send_json_message("crca", cancel_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for materials production cancellation response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while canceling materials production: {e}")
            return False