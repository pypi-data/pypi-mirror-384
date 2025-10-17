# repair.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Repair(GameClient):
    """Building repair operations handler."""

    async def repair_building(
        self,
        building_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Repair a building.
        
        Args:
            building_id: Building identifier to repair
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            repair_data = {"OID": building_id, "PO": -1, "PWR": 0}
            if sync:
                response = await self.send_rpc("rbu", repair_data)
                return response
            else:
                await self.send_json_message("rbu", repair_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for building repair response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while repairing building: {e}")
            return False

    async def ask_alliance_help_repair(
        self,
        building_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Request alliance help for building repair.
        
        Args:
            building_id: Building identifier needing repair
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            help_data = {"ID": building_id, "T": 3}
            if sync:
                response = await self.send_rpc("ahr", help_data)
                return response
            else:
                await self.send_json_message("ahr", help_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for alliance repair help response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while requesting alliance repair help: {e}")
            return False