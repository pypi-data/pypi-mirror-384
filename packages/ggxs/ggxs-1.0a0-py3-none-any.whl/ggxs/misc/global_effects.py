import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class GlobalEffects(GameClient):
    """Global effects operations handler."""

    async def get_global_effects(
        self,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve global effects information.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("usg", {})
                return response
            else:
                await self.send_json_message("usg", {})
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while getting global effects: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for global effects response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting global effects: {e}")
            return False

    async def upgrade_global_effect(
        self,
        effect_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Upgrade a global effect.
        
        Args:
            effect_id: Global effect identifier to upgrade
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("agb", {"GEID": effect_id})
                return response
            else:
                await self.send_json_message("agb", {"GEID": effect_id})
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while upgrading global effect: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for global effect upgrade response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while upgrading global effect: {e}")
            return False