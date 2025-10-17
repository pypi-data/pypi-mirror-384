from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union, Any


class Social(GameClient):
    """
    Social interactions module for handling player messaging and communications.
    
    Provides functionality for sending messages, reading reports, managing inbox,
    and handling various types of game notifications and communications.
    """
    
    async def send_player_sms(
        self,
        player_name: str,
        sms_title: str,
        sms_text: str,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Send a private message to another player.
        
        Args:
            player_name: Recipient player name
            sms_title: Message title/subject
            sms_text: Message content
            sync: Whether to wait for server response
            
        Returns:
            Send result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            message_data = {
                "RN": player_name,
                "MH": sms_title,
                "TXT": sms_text
            }
            
            if sync:
                response = await self.send_rpc("sms", message_data)
                return response
            else:
                await self.send_json_message("sms", message_data)
                return True

        except asyncio.TimeoutError:
            logger.error(f"Timeout while sending message to player '{player_name}'")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    async def read_messages(
        self, 
        message_id: int, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Read a specific message from inbox.
        
        Args:
            message_id: ID of the message to read
            sync: Whether to wait for server response
            
        Returns:
            Message content dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            read_data = {"MID": message_id}
            
            if sync:
                response = await self.send_rpc("rms", read_data)
                return response
            else:
                await self.send_json_message("rms", read_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while reading message {message_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while reading message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error reading message: {e}")
            return False
    
    async def delete_message(
        self, 
        message_id: int, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Delete a message from inbox.
        
        Args:
            message_id: ID of the message to delete
            sync: Whether to wait for server response
            
        Returns:
            Deletion result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            delete_data = {"MID": message_id}
            
            if sync:
                response = await self.send_rpc("dms", delete_data)
                return response
            else:
                await self.send_json_message("dms", delete_data)
                logger.info(f'Message {message_id} removed!')
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while deleting message {message_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while deleting message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting message: {e}")
            return False
        
    async def read_report(
        self, 
        message_id: int, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Read a battle or spy report.
        
        Args:
            message_id: ID of the report to read
            sync: Whether to wait for server response
            
        Returns:
            Report content dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            report_data = {"MID": message_id}
            
            if sync:
                response = await self.send_rpc("bsd", report_data)
                return response
            else:
                await self.send_json_message("bsd", report_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while reading report {message_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while reading report: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error reading report: {e}")
            return False
   
    async def read_invite(
        self, 
        message_id: int, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Read an alliance or game invitation.
        
        Args:
            message_id: ID of the invitation to read
            sync: Whether to wait for server response
            
        Returns:
            Invitation content dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            invite_data = {"MID": message_id}
            
            if sync:
                response = await self.send_rpc("bai", invite_data)
                return response
            else:
                await self.send_json_message("bai", invite_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while reading invite {message_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while reading invite: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error reading invite: {e}")
            return False
    
    async def no_battle_handle(
        self, 
        data: Dict[str, Any]
    ) -> bool:
        """
        Handle "no battle" notifications by deleting them.
        
        Args:
            data: Message data containing notifications
            
        Returns:
            True if operation completed successfully, False otherwise
        """
        try:
            msg_data = data.get("MSG", [])
            deleted_count = 0
            
            for msg_detail in msg_data:
                if msg_detail[1] == 67:  # No battle notification type
                    success = await self.delete_message(msg_detail[0], sync=False)
                    if success:
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} 'no battle' notifications")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling no battle notifications: {e}")
            return False
    
    async def spy_report_handle(
        self, 
        data: Dict[str, Any]
    ) -> Union[Dict[str, Any], bool]:
        """
        Handle spy reports and extract relevant information.
        
        Args:
            data: Message data containing spy reports
            
        Returns:
            Spy report data if successful spy report found,
            False if no relevant spy reports found
        """
        try:
            msg_data = data.get("MSG", [])
            
            for msg_detail in msg_data:
                if msg_detail[1] == 3:  # Spy report type
                    spy_check = str(msg_detail[2]).split('#', 1)[0]
                    if spy_check.startswith("1+0"):
                        report = await self.read_report(msg_detail[0])
                        if isinstance(report, dict):
                            logger.info(f"Retrieved spy report {msg_detail[0]}")
                            return report
            
            logger.debug("No relevant spy reports found in message data")
            return False
            
        except Exception as e:
            logger.error(f"Error handling spy reports: {e}")
            return False