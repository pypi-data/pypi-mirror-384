from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union, Any


class Movements(GameClient):
    """
    Movements module for handling army movements and retrieval operations.
    """

    async def get_movements(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve all current army movements for the player.
        
        Args:
            sync: If True, waits for server response and returns data. 
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict[str, Any], bool]: Movement data dictionary if sync=True and successful,
                                        True if sync=False and message sent successfully,
                                        False if error occurred.
        """
        try:
            if sync:
                response = await self.send_rpc("gam", {})
                return response
            else:
                await self.send_json_message("gam", {})
                return True
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving movements from server")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving movements: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving movements: {e}")
            return False

    async def retrieve_army(
        self,
        movement_id: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Recall a specific army movement by its ID.
        
        Args:
            movement_id: The ID of the movement to retrieve.
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict[str, Any], bool]: Response data dictionary if sync=True and successful,
                                        True if sync=False and message sent successfully,
                                        False if error occurred.
        """
        try:
            data = {"MID": movement_id}
            if sync:
                response = await self.send_rpc("mcm", data)
                return response
            else:
                await self.send_json_message("mcm", data)
                return True
        except asyncio.TimeoutError:
            logger.error(f"Timeout while retrieving army movement {movement_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving army: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving army: {e}")
            return False
