import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Quests(GameClient):
    """Quests operations handler."""

    async def get_quests(
        self,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve available quests.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("dcl", {"CD": 1})
                return response
            else:
                await self.send_json_message("dcl", {"CD": 1})
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while getting quests: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for quests response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting quests: {e}")
            return False

    async def complete_message_quest(
        self,
        quest_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Complete a message-based quest.
        
        Args:
            quest_id: Quest identifier to complete
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            if sync:
                response = await self.send_rpc("qsc", {"QID": quest_id})
                return response
            else:
                await self.send_json_message("qsc", {"QID": quest_id})
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while completing message quest: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for message quest completion response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while completing message quest: {e}")
            return False

    async def complete_donation_quest(
        self,
        quest_id: int,
        food: int = 0,
        wood: int = 0,
        stone: int = 0,
        gold: int = 0,
        oil: int = 0,
        coal: int = 0,
        iron: int = 0,
        glass: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Complete a donation quest with specified resources.
        
        Args:
            quest_id: Quest identifier to complete
            food: Food amount to donate
            wood: Wood amount to donate
            stone: Stone amount to donate
            gold: Gold amount to donate
            oil: Oil amount to donate
            coal: Coal amount to donate
            iron: Iron amount to donate
            glass: Glass amount to donate
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            donation_data = {
                "QID": quest_id,
                "F": food,
                "W": wood,
                "S": stone,
                "C1": gold,
                "O": oil,
                "C": coal,
                "I": iron,
                "G": glass,
                "PWR": 0,
                "PO": -1
            }
            
            if sync:
                response = await self.send_rpc("qdr", donation_data)
                return response
            else:
                await self.send_json_message("qdr", donation_data)
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while completing donation quest: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for donation quest completion response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while completing donation quest: {e}")
            return False

    async def tracking_recommended_quests(self) -> bool:
        """
        Enable tracking of recommended quests.
        
        Returns:
            True if successful, False on error
        """
        try:
            await self.send_json_message("ctr", {"TQR": 0})
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while tracking recommended quests: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while tracking recommended quests: {e}")
            return False

    async def complete_quest_condition(
        self,
        quest_id: int,
        condition: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Complete a specific quest condition.
        
        Args:
            quest_id: Quest identifier
            condition: Condition identifier to complete
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            condition_data = {
                "QTID": quest_id,
                "QC": condition
            }
            
            if sync:
                response = await self.send_rpc("fcq", condition_data)
                return response
            else:
                await self.send_json_message("fcq", condition_data)
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while completing quest condition: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for quest condition completion response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while completing quest condition: {e}")
            return False