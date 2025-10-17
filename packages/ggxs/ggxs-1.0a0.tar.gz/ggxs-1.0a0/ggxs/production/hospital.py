# hospital.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Hospital(GameClient):
    """Hospital and healing operations handler."""

    async def heal(
        self, 
        wod_id: int, 
        amount: int, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Heal wounded units.
        
        Args:
            wod_id: Unit template identifier
            amount: Number of units to heal
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            heal_data = {"U": wod_id, "A": amount}
            if sync:
                response = await self.send_rpc("hru", heal_data)
                return response
            else:
                await self.send_json_message("hru", heal_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for heal response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while healing units: {e}")
            return False

    async def cancel_heal(
        self, 
        slot_id: int, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Cancel healing process.
        
        Args:
            slot_id: Healing slot identifier
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            cancel_data = {"S": slot_id}
            if sync:
                response = await self.send_rpc("hcs", cancel_data)
                return response
            else:
                await self.send_json_message("hcs", cancel_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for heal cancellation response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while canceling heal: {e}")
            return False

    async def skip_heal(
        self, 
        slot_id: int, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Skip healing process.
        
        Args:
            slot_id: Healing slot identifier
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            skip_data = {"S": slot_id}
            if sync:
                response = await self.send_rpc("hss", skip_data)
                return response
            else:
                await self.send_json_message("hss", skip_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for heal skip response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while skipping heal: {e}")
            return False

    async def delete_wounded(
        self, 
        wod_id: int, 
        amount: int, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Delete wounded units.
        
        Args:
            wod_id: Unit template identifier
            amount: Number of units to delete
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            delete_data = {"U": wod_id, "A": amount}
            if sync:
                response = await self.send_rpc("hdu", delete_data)
                return response
            else:
                await self.send_json_message("hdu", delete_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for wounded units deletion response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while deleting wounded units: {e}")
            return False

    async def ask_alliance_help_heal(
        self, 
        package_id: int, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Request alliance help for healing.
        
        Args:
            package_id: Package identifier
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            help_data = {"ID": package_id, "T": 2}
            if sync:
                response = await self.send_rpc("ahr", help_data)
                return response
            else:
                await self.send_json_message("ahr", help_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for alliance heal help response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while requesting alliance heal help: {e}")
            return False