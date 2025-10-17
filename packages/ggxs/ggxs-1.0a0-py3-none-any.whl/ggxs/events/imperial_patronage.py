import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class ImperialPatronage(GameClient):
    """Imperial Patronage operations handler."""

    async def open_imperial_patronage(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Open Imperial Patronage interface.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            await self.send_json_message("gdti", {})
            
            if sync:
                response = await self.wait_for_response("gdti")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while opening imperial patronage: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for imperial patronage response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while opening imperial patronage: {e}")
            return False

    async def give_imperial_patronage(
        self,
        devise_id: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Give Imperial Patronage donation.
        
        Args:
            devise_id: Devise identifier
            amount: Amount to donate
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            donation_data = {
                "DIV": [{
                    "DII": devise_id, 
                    "DIA": amount
                }]
            }
            
            await self.send_json_message("ddi", donation_data)
            
            if sync:
                response = await self.wait_for_response("ddi")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while giving imperial patronage: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for imperial patronage donation response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while giving imperial patronage: {e}")
            return False