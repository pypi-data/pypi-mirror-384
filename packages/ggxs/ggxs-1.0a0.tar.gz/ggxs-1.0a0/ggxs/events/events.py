import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Events(GameClient):
    """Events operations handler."""

    async def get_events(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Retrieve available events.
        
        Args:
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict, bool]: Events data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            if sync:
                response = await self.send_rpc("sei", {})
                return response
            else:
                await self.send_json_message("sei", {})
                return True
        except ConnectionError as e:
            logger.error(f"Connection error while getting events: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for events response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting events: {e}")
            return False

    async def get_event_points(self, event_id: int, sync: bool = True) -> Union[Dict, bool]:
        """
        Retrieve event points for specific event.
        
        Args:
            event_id: The ID of the event to get points for.
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict, bool]: Event points data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"EID": event_id}
            if sync:
                response = await self.send_rpc("pep", data)
                return response
            else:
                await self.send_json_message("pep", data)
                return True
        except ConnectionError as e:
            logger.error(f"Connection error while getting event points: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for event points response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting event points: {e}")
            return False

    async def get_ranking(
        self,
        ranking_type: int,
        category: int = -1,
        search_value: int = -1,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve ranking information.
        
        Args:
            ranking_type: Type of ranking to retrieve.
            category: Category filter for ranking (default: -1 for all).
            search_value: Additional search parameter (default: -1).
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict, bool]: Ranking data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"LT": ranking_type, "LID": category, "SV": search_value}
            if sync:
                response = await self.send_rpc("hgh", data)
                return response
            else:
                await self.send_json_message("hgh", data)
                return True
        except ConnectionError as e:
            logger.error(f"Connection error while getting ranking: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for ranking response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting ranking: {e}")
            return False

    async def choose_event_difficulty(
        self,
        event_id: int,
        difficulty_id: int,
        premium_unlock: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Choose event difficulty level.
        
        Args:
            event_id: The ID of the event.
            difficulty_id: The difficulty level to choose.
            premium_unlock: Premium unlock flag (default: 0).
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict, bool]: Response data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"EID": event_id, "EDID": difficulty_id, "C2U": premium_unlock}
            if sync:
                response = await self.send_rpc("sede", data)
                return response
            else:
                await self.send_json_message("sede", data)
                return True
        except ConnectionError as e:
            logger.error(f"Connection error while choosing event difficulty: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for event difficulty response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while choosing event difficulty: {e}")
            return False
