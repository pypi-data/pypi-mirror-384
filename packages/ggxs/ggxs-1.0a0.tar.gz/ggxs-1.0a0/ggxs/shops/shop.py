# shop.py
import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Shop(GameClient):
    """Shop and purchasing operations handler."""

    async def buy_package_generic(
        self,
        kingdom: int,
        shop_type: int,
        shop_id: int,
        package_id: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Generic method to buy packages from various shops.
        
        Args:
            kingdom: Kingdom identifier
            shop_type: Type of shop
            shop_id: Shop identifier
            package_id: Package identifier to buy
            amount: Number of packages to buy
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            package_data = {
                "PID": package_id,
                "BT": shop_type,
                "TID": shop_id,
                "AMT": amount,
                "KID": kingdom,
                "AID": -1,
                "PC2": -1,
                "BA": 0,
                "PWR": 0,
                "_PO": -1
            }
            
            if sync:
                response = await self.send_rpc("sbp", package_data)
                return response
            else:
                await self.send_json_message("sbp", package_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for package purchase response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while buying package: {e}")
            return False

    async def buy_from_master_blacksmith(
        self,
        kingdom: int,
        package_id: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Buy package from Master Blacksmith shop.
        
        Args:
            kingdom: Kingdom identifier
            package_id: Package identifier to buy
            amount: Number of packages to buy
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        return await self.buy_package_generic(kingdom, 0, 116, package_id, amount, sync)

    async def buy_from_armorer(
        self,
        kingdom: int,
        package_id: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Buy package from Armorer shop.
        
        Args:
            kingdom: Kingdom identifier
            package_id: Package identifier to buy
            amount: Number of packages to buy
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        return await self.buy_package_generic(kingdom, 0, 27, package_id, amount, sync)

    async def buy_from_nomad_shop(
        self,
        kingdom: int,
        package_id: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Buy package from Nomad Shop.
        
        Args:
            kingdom: Kingdom identifier
            package_id: Package identifier to buy
            amount: Number of packages to buy
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        return await self.buy_package_generic(kingdom, 0, 94, package_id, amount, sync)

    async def buy_from_blade_coast(
        self,
        kingdom: int,
        package_id: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Buy package from Blade Coast shop.
        
        Args:
            kingdom: Kingdom identifier
            package_id: Package identifier to buy
            amount: Number of packages to buy
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        return await self.buy_package_generic(kingdom, 0, 4, package_id, amount, sync)

    async def set_buying_castle(
        self,
        castle_id: int,
        kingdom: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Set the castle for purchasing operations.
        
        Args:
            castle_id: Castle identifier
            kingdom: Kingdom identifier (default: 0)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            castle_data = {
                "CID": castle_id,
                "KID": kingdom
            }
            
            if sync:
                response = await self.send_rpc("gbc", castle_data)
                return response
            else:
                await self.send_json_message("gbc", castle_data)
                return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for buying castle response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while setting buying castle: {e}")
            return False