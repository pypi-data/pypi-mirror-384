from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient
import asyncio


class Tax(GameClient):
    """Tax collection operations handler."""

    async def get_tax_infos(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Retrieve tax information.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("txi", {})
                return response
            else:
                await self.send_json_message("txi", {})
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while getting tax info: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for tax info response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting tax info: {e}")
            return False

    async def start_tax(self, tax_type: int, sync: bool = True) -> Union[Dict, bool]:
        """
        Start tax collection process.
        
        Args:
            tax_type: Type of tax to start
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("txs", {"TT": tax_type, "TX": 3})
                return response
            else:
                await self.send_json_message("txs", {"TT": tax_type, "TX": 3})
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while starting tax: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for tax start response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while starting tax: {e}")
            return False

    async def collect_tax(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Collect tax rewards.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("txc", {"TR": 29})
                return response
            else:
                await self.send_json_message("txc", {"TR": 29})
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while collecting tax: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for tax collection response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while collecting tax: {e}")
            return False