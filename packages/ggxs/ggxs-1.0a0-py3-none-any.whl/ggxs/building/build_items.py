# build_items.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class BuildItems(GameClient):
    """Build items equipment operations handler."""

    async def equip_build_item(
        self,
        kingdom_id: int,
        castle_id: int,
        building_id: int,
        slot_id: int,
        item_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Equip build item on a building.
        
        Args:
            kingdom_id: Kingdom identifier
            castle_id: Castle identifier
            building_id: Building identifier
            slot_id: Slot identifier
            item_id: Item identifier to equip
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            item_data = {
                "OID": building_id,
                "CID": item_id,
                "SID": slot_id,
                "M": 0,
                "KID": kingdom_id,
                "AID": castle_id
            }
            
            if sync:
                response = await self.send_rpc("rpc", item_data)
                return response
            else:
                await self.send_json_message("rpc", item_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for build item equip response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while equipping build item: {e}")
            return False