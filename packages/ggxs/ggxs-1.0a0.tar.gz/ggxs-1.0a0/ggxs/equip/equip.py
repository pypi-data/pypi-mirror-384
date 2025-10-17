from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union, Any


class Equip(GameClient):
    """
    Equipment and gems management module for handling inventory operations.
    
    Provides functionality for managing equipment and gems inventory,
    including removal of unwanted items and automated cleanup operations.
    """
    
    async def get_equip_inventory(
        self, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Retrieve equipment inventory for the account.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Equipment inventory dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("gei", {})
                return response
            else:
                await self.send_json_message("gei", {})
                return True
                
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving equipment inventory")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving equipment inventory: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving equipment inventory: {e}")
            return False
        
    async def remove_equip(
        self, 
        equip_id: int, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Remove an equipment item from inventory.
        
        Args:
            equip_id: ID of the equipment to remove
            sync: Whether to wait for server response
            
        Returns:
            Removal result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            remove_data = {
                "EID": equip_id,
                "LID": -1,
                "EX": 0,
                "LFID": -1
            }
            
            if sync:
                response = await self.send_rpc("seq", remove_data)
                return response
            else:
                await self.send_json_message("seq", remove_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while removing equipment {equip_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while removing equipment: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error removing equipment: {e}")
            return False
        
    async def get_gems_inventory(
        self, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Retrieve gems inventory for the account.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Gems inventory dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("ggm", {})
                return response
            else:
                await self.send_json_message("ggm", {})
                return True
                
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving gems inventory")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving gems inventory: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving gems inventory: {e}")
            return False
    
    async def remove_gem(
        self, 
        gem_id: int, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Remove a gem from inventory.
        
        Args:
            gem_id: ID of the gem to remove
            sync: Whether to wait for server response
            
        Returns:
            Removal result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            remove_data = {
                "GID": gem_id,
                "RGEM": 0,
                "LFID": -1
            }
            
            if sync:
                response = await self.send_rpc("sge", remove_data)
                return response
            else:
                await self.send_json_message("sge", remove_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while removing gem {gem_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while removing gem: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error removing gem: {e}")
            return False
        
    async def gem_remover(
        self, 
        sync: bool = True
    ) -> bool:
        """
        Remove all gems from inventory.
        
        Args:
            sync: Whether to wait for server responses
            
        Returns:
            True if operation completed successfully, False otherwise
        """
        try:
            gems_inventory = await self.get_gems_inventory()
            if not isinstance(gems_inventory, dict):
                logger.error("Failed to retrieve gems inventory")
                return False
                
            gem_data = gems_inventory.get("GEM", [])
            for gem in gem_data:
                gem_id = gem[0]
                gem_qty = gem[1]
                for _ in range(gem_qty):
                    try:
                        await self.remove_gem(gem_id, sync=sync)
                    except Exception as e:
                        logger.error(f"Error removing gem {gem_id}: {e}")
                        continue
            
            logger.info("All useless gems have been removed")
            return True
            
        except Exception as e:
            logger.error(f"Error in gem remover: {e}")
            return False
        
    async def old_equip_remover(
        self, 
        sync: bool = True
    ) -> bool:
        """
        Remove old/useless equipment from inventory.
        
        Args:
            sync: Whether to wait for server responses
            
        Returns:
            True if operation completed successfully, False otherwise
        """
        try:
            useless_equip_ids = [1, 2, 3, 11, 12, 13]
            equip_data = await self.get_equip_inventory()
            if not isinstance(equip_data, dict):
                logger.error("Failed to retrieve equipment inventory")
                return False
                
            equip_obj = equip_data.get("I", [])
            for equip in equip_obj:
                if equip[3] in useless_equip_ids and equip[4] > 0:
                    try:
                        await self.remove_equip(equip_id=equip[0], sync=sync)
                    except Exception as e:
                        logger.error(f"Error removing equipment {equip[0]}: {e}")
                        continue
            
            logger.info("All useless equipment has been removed")
            return True
            
        except Exception as e:
            logger.error(f"Error in old equipment remover: {e}")
            return False
        
    async def handle_gems_from_npc(
        self, 
        data: Dict[str, Any]
    ) -> bool:
        """
        Handle gems obtained from NPC activities.
        
        Args:
            data: NPC activity data containing gem information
            
        Returns:
            True if operation completed successfully, False otherwise
        """
        try:
            gem_list = data.get("GEM", [])
            for gem_detail in gem_list:
                gem_id = gem_detail[0]
                success = await self.remove_gem(gem_id)
                if not success:
                    logger.warning(f"Failed to remove gem {gem_id} from NPC data")
            
            logger.info("Processed gems from NPC activity")
            return True
            
        except Exception as e:
            logger.error(f"Error handling gems from NPC: {e}")
            return False
        
        
        
    async def upgrade_in_tehnicus(
        self,
        equip_id: int,
        ruby: int = 0,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        
        """
        Upgrade your unique, legendary etc. in tehnicus.
        
        Args:
            equip_id: Equip id of your item
            ruby: Use ruby for upgrade.
            
        Returns:
            True if operation completed successfully, False otherwise
        """
        try:
            tehnicus = {"C2":ruby,"EID":equip_id}
            if sync:
                return await self.send_rpc("eqe", tehnicus)
            
            else:
                await self.send_json_message("eqe", tehnicus)
                return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while upgrading items {equip_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while upgrading items: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error upgrading items: {e}")
            return False
        
        
        
    async def upgrade_relic(
        self,
        equip_id: int,
        type: int,
        ruby: int = 0,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        
        """
        Upgrade your relic items in relicus.
        
        Args:
            equip_id: Equip id of your item.
            type: 1 - for relic equipment, 0 - for relic gem
            ruby: Use ruby for upgrade.
            
        Returns:
            True if operation completed successfully, False otherwise
        """
        try:
            relic = {"C2":ruby,"RIID":equip_id,"EQ":type}
            if sync:
                return await self.send_rpc("ere", relic)
            
            else:
                await self.send_json_message("ere", relic)
                return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while upgrading items {equip_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while upgrading items: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error upgrading items: {e}")
            return False