# soldiers.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Soldiers(GameClient):
    """Soldiers recruitment and management operations handler."""

    async def get_recruitment_queue(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Retrieve recruitment queue.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("spl", {"LID": 0})
                return response
            else:
                await self.send_json_message("spl", {"LID": 0})
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for recruitment queue response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting recruitment queue: {e}")
            return False

    async def recruit_soldiers(
        self,
        castle_id: int,
        wod_id: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Recruit soldiers.
        
        Args:
            castle_id: Castle identifier
            wod_id: Unit template identifier
            amount: Number of soldiers to recruit
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            recruitment_data = {
                "LID": 0,
                "WID": wod_id,
                "AMT": amount,
                "PO": -1,
                "PWR": 0,
                "SK": 73,
                "SID": 0,
                "AID": castle_id
            }
            
            if sync:
                response = await self.send_rpc("bup", recruitment_data)
                return response
            else:
                await self.send_json_message("bup", recruitment_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for soldier recruitment response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while recruiting soldiers: {e}")
            return False

    async def cancel_recruitment(
        self,
        slot_type: str,
        slot: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Cancel recruitment process.
        
        Args:
            slot_type: Type of slot
            slot: Slot identifier
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            cancel_data = {"LID": 0, "S": slot, "ST": slot_type}
            if sync:
                response = await self.send_rpc("mcu", cancel_data)
                return response
            else:
                await self.send_json_message("mcu", cancel_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for recruitment cancellation response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while canceling recruitment: {e}")
            return False

    async def recruitment_alliance_help(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Request alliance help for recruitment.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            help_data = {"ID": 0, "T": 6}
            if sync:
                response = await self.send_rpc("ahr", help_data)
                return response
            else:
                await self.send_json_message("ahr", help_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for alliance recruitment help response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while requesting alliance recruitment help: {e}")
            return False

    async def get_units_inventory(
        self,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve units inventory.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("gui", {})
                return response
            else:
                await self.send_json_message("gui", {})
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for units inventory response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting units inventory: {e}")
            return False

    async def delete_units(
        self,
        wod_id: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Delete units from inventory.
        
        Args:
            wod_id: Unit template identifier
            amount: Number of units to delete
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            delete_data = {
                "WID": wod_id,
                "A": amount,
                "S": 0
            }
            
            if sync:
                response = await self.send_rpc("dup", delete_data)
                return response
            else:
                await self.send_json_message("dup", delete_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for units deletion response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while deleting units: {e}")
            return False