from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union, Any


class Account(GameClient):
    """
    Account management module for handling user account operations.
    
    Provides functionality for retrieving account information, managing email settings,
    changing usernames, passwords, and other account-related operations.
    """
    
    async def get_account_infos(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve comprehensive account information for the current user.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Account information dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("gpi", {})
                return response
            else:
                await self.send_json_message("gpi", {})
                return True
                
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving account information")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving account information: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving account information: {e}")
            return False
        
    async def register_email(
        self,
        email: str,
        subscribe: bool = False,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Register or update email address for the account.
        
        Args:
            email: Email address to register
            subscribe: Whether to subscribe to newsletter
            sync: Whether to wait for server response
            
        Returns:
            Email registration result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            email_data = {"MAIL": email, "NEWSLETTER": subscribe}
            
            if sync:
                response = await self.send_rpc("vpm", email_data)
                return response
            else:
                await self.send_json_message("vpm", email_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while registering email '{email}'")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while registering email: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error registering email: {e}")
            return False

    async def get_username_change_infos(
        self, sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Retrieve information about username change options and limitations.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Username change information dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("gnci", {})
                return response
            else:
                await self.send_json_message("gnci", {})
                return True
                
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving username change information")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving username change information: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving username change information: {e}")
            return False

    async def change_username(
        self, new_username: str, sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Change the account username.
        
        Args:
            new_username: New username to set
            sync: Whether to wait for server response
            
        Returns:
            Username change result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("cpne", {"PN": new_username})
                return response
            else:
                await self.send_json_message("cpne", {"PN": new_username})
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while changing username to '{new_username}'")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while changing username: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error changing username: {e}")
            return False

    async def change_password(
        self,
        old_password: str,
        new_password: str,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Change the account password.
        
        Args:
            old_password: Current account password
            new_password: New password to set
            sync: Whether to wait for server response
            
        Returns:
            Password change result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            password_data = {"OPW": old_password, "NPW": new_password}
            
            if sync:
                response = await self.send_rpc("scp", password_data)
                return response
            else:
                await self.send_json_message("scp", password_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error("Timeout while changing password")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while changing password: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error changing password: {e}")
            return False

    async def ask_email_change(
        self, new_email: str, sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Request an email address change for the account.
        
        Args:
            new_email: New email address to set
            sync: Whether to wait for server response
            
        Returns:
            Email change request result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("rmc", {"PMA": new_email})
                return response
            else:
                await self.send_json_message("rmc", {"PMA": new_email})
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while requesting email change to '{new_email}'")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while requesting email change: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error requesting email change: {e}")
            return False

    async def get_email_change_status(
        self, sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Retrieve the status of a pending email change request.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Email change status dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("mns", {})
                return response
            else:
                await self.send_json_message("mns", {})
                return True
                
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving email change status")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving email change status: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving email change status: {e}")
            return False

    async def cancel_email_change(
        self, sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Cancel a pending email change request.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Cancellation result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("cmc", {})
                return response
            else:
                await self.send_json_message("cmc", {})
                return True
                
        except asyncio.TimeoutError:
            logger.error("Timeout while canceling email change")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while canceling email change: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error canceling email change: {e}")
            return False