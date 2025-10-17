# kings_market.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class KingsMarket(GameClient):
    """King's Market operations handler."""

    async def start_protection(
        self,
        duration: int,  # 0: 7 days, 1: 14 days, 2: 21 days, 3: 60 days
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Start kingdom protection.
        
        Args:
            duration: Protection duration (0: 7 days, 1: 14 days, 2: 21 days, 3: 60 days)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            protection_data = {
                "CD": duration
            }
            
            if sync:
                response = await self.send_rpc("mps", protection_data)
                return response
            else:
                await self.send_json_message("mps", protection_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for protection start response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while starting protection: {e}")
            return False

    async def buy_production_slot(
        self,
        queue_type: int,  # 0 for barracks, 1 for workshop
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Buy additional production slot.
        
        Args:
            queue_type: Queue type (0 for barracks, 1 for workshop)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            slot_data = {
                "LID": queue_type
            }
            
            if sync:
                response = await self.send_rpc("ups", slot_data)
                return response
            else:
                await self.send_json_message("ups", slot_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for production slot purchase response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while buying production slot: {e}")
            return False

    async def buy_open_gates(
        self,
        kingdom: int,
        castle_id: int,
        duration: int,  # 0 for 6h, 1 for 12h
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Buy open gates buff.
        
        Args:
            kingdom: Kingdom identifier
            castle_id: Castle identifier
            duration: Duration (0 for 6h, 1 for 12h)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            gates_data = {
                "CID": castle_id,
                "KID": kingdom,
                "CD": duration
            }
            
            if sync:
                response = await self.send_rpc("mos", gates_data)
                return response
            else:
                await self.send_json_message("mos", gates_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for open gates purchase response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while buying open gates: {e}")
            return False

    async def buy_feast(
        self,
        kingdom: int,
        castle_id: int,
        feast_type: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Buy feast buff.
        
        Args:
            kingdom: Kingdom identifier
            castle_id: Castle identifier
            feast_type: Type of feast
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            feast_data = {
                "CID": castle_id,
                "KID": kingdom,
                "T": feast_type,
                "PO": -1,
                "PWR": 0
            }
            
            if sync:
                response = await self.send_rpc("bfs", feast_data)
                return response
            else:
                await self.send_json_message("bfs", feast_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for feast purchase response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while buying feast: {e}")
            return False