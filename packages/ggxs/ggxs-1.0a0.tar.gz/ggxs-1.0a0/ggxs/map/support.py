from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, List, Union


class Support(GameClient):
    """
    Support module for handling support-related operations in the game.
    """

    async def get_support_info(
        self,
        sx: int,
        sy: int,
        tx: int,
        ty: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Get detailed information about support between two castles.
        
        Args:
            sx: Source castle X coordinate.
            sy: Source castle Y coordinate.
            tx: Target castle X coordinate.
            ty: Target castle Y coordinate.
            sync: If True, waits for server response.
                  
        Returns:
            Union[Dict, bool]: Support information data if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """        
        try:
            data = {"TX": tx, "TY": ty, "SX": sx, "SY": sy}
            if sync:
                response = await self.send_rpc("sdi", data)
                return response
            else:
                await self.send_json_message("sdi", data)
                return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting support info from ({sx}, {sy}) to ({tx}, {ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during support info: {e}")
            return False
        except Exception as e:
            logger.error(f"Error getting support info from ({sx}, {sy}) to ({tx}, {ty}): {e}")
            return False

    async def send_support(
        self,
        units: List[int],
        sender_id: int,
        tx: int,
        ty: int,
        lord_id: int,
        camp_time: int = 12,
        horses_type: int = -1,
        feathers: int = 0,
        slowdown: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Send support troops to another castle.
        
        Args:
            units: List of unit counts to send.
            sender_id: Source castle ID.
            tx: Target X coordinate.
            ty: Target Y coordinate.
            lord_id: Lord ID for the support mission.
            camp_time: Camping time in hours.
            horses_type: Type of horses to use (-1 for default).
            feathers: Feathers parameter.
            slowdown: Slowdown parameter.
            sync: If True, waits for server response.
                  
        Returns:
            Union[Dict, bool]: Response data if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {
                "SID": sender_id,
                "TX": tx,
                "TY": ty,
                "LID": lord_id,
                "WT": camp_time,
                "HBW": horses_type,
                "BPC": 0,
                "PTT": feathers,
                "SD": slowdown,
                "A": units
            }
            if sync:
                response = await self.send_rpc("cds", data)
                return response
            else:
                await self.send_json_message("cds", data)
                return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout sending support from castle {sender_id} to ({tx}, {ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during support: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending support from castle {sender_id} to ({tx}, {ty}): {e}")
            return False

    async def batch_send_support(
        self,
        support_requests: List[Dict],
        delay: float = 1.0
    ) -> List[Dict]:
        """
        Send multiple support requests in sequence with delays.
        
        Args:
            support_requests: List of dictionaries containing support request parameters.
            delay: Delay in seconds between each request.
                  
        Returns:
            List[Dict]: List of results for each support request, containing:
                       - request_index: Index of the request
                       - success: Boolean indicating success
                       - data: Response data or error message
        """
        results = []

        for i, request in enumerate(support_requests):
            try:
                logger.info(f"Sending support request {i+1}/{len(support_requests)}")

                result = await self.send_support(
                    units=request["units"],
                    sender_id=request["sender_id"],
                    tx=request["tx"],
                    ty=request["ty"],
                    lord_id=request["lord_id"],
                    camp_time=request.get("camp_time", 12),
                    horses_type=request.get("horses_type", -1),
                    feathers=request.get("feathers", 0),
                    slowdown=request.get("slowdown", 0),
                    sync=True
                )

                results.append({
                    "request_index": i,
                    "success": isinstance(result, dict),
                    "data": result
                })

                if delay > 0 and i < len(support_requests) - 1:
                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Error in batch support request {i+1}: {e}")
                results.append({
                    "request_index": i,
                    "success": False,
                    "error": str(e)
                })

        success_count = sum(1 for r in results if r["success"])
        logger.info(f"Batch support sending completed: {success_count}/{len(support_requests)} successful")
        return results
