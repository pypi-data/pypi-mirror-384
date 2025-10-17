# tools.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Tools(GameClient):
    """Tools production operations handler."""

    async def get_production_queue(
        self, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve tools production queue.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("spl", {"LID": 1})
                return response
            else:
                await self.send_json_message("spl", {"LID": 1})
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for production queue response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting production queue: {e}")
            return False

    async def produce_tools(
        self,
        castle_id: int,
        wod_id: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Produce tools.
        
        Args:
            castle_id: Castle identifier
            wod_id: Tool template identifier
            amount: Number of tools to produce
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            production_data = {
                "LID": 1,
                "WID": wod_id,
                "AMT": amount,
                "PO": -1,
                "PWR": 0,
                "SK": 73,
                "SID": 0,
                "AID": castle_id
            }
            
            if sync:
                response = await self.send_rpc("bup", production_data)
                return response
            else:
                await self.send_json_message("bup", production_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for tools production response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while producing tools: {e}")
            return False

    async def cancel_production(
        self, 
        slot_type: str, 
        slot: int, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Cancel tools production.
        
        Args:
            slot_type: Type of slot
            slot: Slot identifier
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            cancel_data = {"LID": 1, "S": slot, "ST": slot_type}
            if sync:
                response = await self.send_rpc("mcu", cancel_data)
                return response
            else:
                await self.send_json_message("mcu", cancel_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for production cancellation response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while canceling production: {e}")
            return False