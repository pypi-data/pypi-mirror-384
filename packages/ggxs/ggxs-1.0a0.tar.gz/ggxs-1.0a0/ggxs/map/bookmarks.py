from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union


class Bookmarks(GameClient):
    """
    Bookmarks module for managing location bookmarks in the game.
    
    Provides functionality for creating, retrieving, updating, and deleting
    bookmarks for quick access to important map locations.
    """
    
    async def get_bookmarks(
        self, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve all bookmarks for the current player.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Union[Dict, bool]: Bookmarks data if sync=True, 
                             otherwise True if request sent successfully
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("gbl", {})
                return response
            else:
                await self.send_json_message("gbl", {})
                return True
                
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving bookmarks from server")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving bookmarks: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving bookmarks: {e}")
            return False

    async def add_bookmark(
        self,
        name: str,
        x: int,
        y: int,
        kingdom: int,
        friendly: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Add a new bookmark at specified coordinates.
        
        Args:
            name: Name of the bookmark
            x: X coordinate of the bookmark location
            y: Y coordinate of the bookmark location
            kingdom: Kingdom ID where the bookmark is located
            friendly: Bookmark type (0 - enemy / 1 - friend)
            sync: Whether to wait for server response
            
        Returns:
            Union[Dict, bool]: Bookmark creation result if sync=True, 
                             otherwise True if request sent successfully
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            bookmark_data = {
                "K": kingdom,
                "X": x,
                "Y": y,
                "TY": friendly,
                "TI": -1,
                "IM": 0,
                "N": name,
                "M": []
            }
            
            if sync:
                response = await self.send_rpc("bad", bookmark_data)
                return response
            else:
                await self.send_json_message("bad", bookmark_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while adding bookmark at ({x}, {y})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while adding bookmark: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error adding bookmark: {e}")
            return False
    
    async def update_bookmark(
        self,
        kingdom: int,
        name: str,
        x: int,
        y: int,
        friendly: bool,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Update an existing bookmark with new information.
        
        Args:
            kingdom: Kingdom ID of the bookmark
            name: New name for the bookmark 
            x: New X coordinate 
            y: New Y coordinate 
            friendly: Whether location is friendly (True/False)
            sync: Whether to wait for server response
            
        Returns:
            Union[Dict, bool]: Bookmark update result if sync=True, 
                             otherwise True if request sent successfully
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            update_data = {
                "KID": kingdom,
                "X": x,
                "Y": y,
                "IF": friendly,
                "DN": name
            }
            
            if sync:
                response = await self.send_rpc("bch", update_data)
                return response
            else:
                await self.send_json_message("bch", update_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while updating bookmark at ({x}, {y})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while updating bookmark: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating bookmark: {e}")
            return False

    async def delete_bookmark(
        self,
        kingdom: int,
        x: int,
        y: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Delete a bookmark by its coordinates.
        
        Args:
            kingdom: Kingdom ID of the bookmark to delete
            x: X coordinate of the bookmark to delete
            y: Y coordinate of the bookmark to delete
            sync: Whether to wait for server response
            
        Returns:
            Union[Dict, bool]: Bookmark deletion result if sync=True, 
                             otherwise True if request sent successfully
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            delete_data = {
                "BM": [[kingdom, x, y]]
            }
            
            if sync:
                response = await self.send_rpc("bde", delete_data)
                return response
            else:
                await self.send_json_message("bde", delete_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while deleting bookmark at ({x}, {y})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while deleting bookmark: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting bookmark: {e}")
            return False