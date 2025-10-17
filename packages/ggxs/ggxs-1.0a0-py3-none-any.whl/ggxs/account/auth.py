from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union, Any


class Auth(GameClient):
    """
    Authentication module for handling user registration, login, and account verification.
    
    Provides functionality for checking username availability, user existence,
    registration, and token-based authentication.
    """
    
    async def check_username_availability(
        self,
        name: str,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Check if a username is available for registration.
        
        Args:
            name: Username to check
            sync: Whether to wait for server response
            
        Returns:
            Availability result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("vpn", {"PN": name})
                return response
            else:
                await self.send_json_message("vpn", {"PN": name})
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while checking username availability for '{name}'")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while checking username availability: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking username availability: {e}")
            return False

    async def check_user_exists(
        self,
        name: str,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Check if a user exists in the system.
        
        Args:
            name: Username to check
            sync: Whether to wait for server response
            
        Returns:
            User existence result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("vln", {"NOM": name})
                return response
            else:
                await self.send_json_message("vln", {"NOM": name})
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while checking user existence for '{name}'")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while checking user existence: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking user existence: {e}")
            return False
        
    async def register(
        self, 
        username: str, 
        email: str, 
        password: str,
        token: str, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Register a new user account.
        
        Args:
            username: Desired username
            email: User email address
            password: Account password
            token: Registration token/captcha
            sync: Whether to wait for server response
            
        Returns:
            Registration result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            register_data = {
                "DID": 0,
                "CONM": 175,
                "RTM": 24,
                "campainPId": -1,
                "campainCr": -1,
                "campainLP": -1,
                "adID": -1,
                "timeZone": 14,
                "username": username,
                "email": email,
                "password": password,
                "accountId": "1674256959939529708",
                "ggsLanguageCode": "en",
                "referrer": "https://empire.goodgamestudios.com",
                "distributorId": 0,
                "connectionTime": 175,
                "roundTripTime": 24,
                "campaignVars": ";https://empire.goodgamestudios.com;;;;;;-1;-1;;1674256959939529708;380635;;;;;",
                "campaignVars_adid": "-1",
                "campaignVars_lp": "-1",
                "campaignVars_creative": "-1",
                "campaignVars_partnerId": "-1",
                "campaignVars_websiteId": "380635",
                "timezone": 14,
                "PN": username,
                "PW": password,
                "REF": "https://empire.goodgamestudios.com",
                "LANG": "en",
                "AID": "1674256959939529708",
                "GCI": "",
                "SID": 9,
                "PLFID": 1,
                "NID": 1,
                "IC": "",
                "RCT": token
            }
            
            if sync:
                response = await self.send_rpc("lre", register_data)
                return response
            else:
                await self.send_json_message("lre", register_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while registering user '{username}'")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost during user registration: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during user registration: {e}")
            return False
        
    async def login_with_token(
        self, 
        name: str, 
        password: str, 
        token: str, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Login with username, password and security token.
        
        Args:
            name: Username
            password: Account password
            token: Security token/captcha
            sync: Whether to wait for server response
            
        Returns:
            Login result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            login_data = {
                "CONM": 175,
                "RTM": 24,
                "ID": 0,
                "PL": 1,
                "NOM": name,
                "PW": password,
                "LT": None,
                "LANG": "fr",
                "DID": "0",
                "AID": "1674256959939529708",
                "KID": "",
                "REF": "https://empire.goodgamestudios.com",
                "GCI": "",
                "SID": 9,
                "PLFID": 1,
                "RCT": token,
            }
            
            if sync:
                response = await self.send_rpc("lli", login_data)
                return response
            else:
                await self.send_json_message("lli", login_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while logging in user '{name}'")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost during user login: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during user login: {e}")
            return False