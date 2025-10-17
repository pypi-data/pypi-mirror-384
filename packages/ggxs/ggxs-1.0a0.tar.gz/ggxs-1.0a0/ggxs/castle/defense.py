from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union, Any, List




class Defense(GameClient):
    """
    Defense management module for handling castle defense configurations.
    """

    async def get_castle_defense(
        self,
        x: int,
        y: int,
        castle_id: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Retrieve current defense configuration for a castle.

        Sends RPC command 'dfc' to get detailed defense information including
        keep, wall, and moat configurations for the specified castle.

        Args:
            x: X coordinate of the castle location
            y: Y coordinate of the castle location
            castle_id: Unique identifier of the castle (AID)
            sync: If True, waits for response and returns data. If False, sends
                  message without waiting for response and returns True.

        Returns:
            Union[Dict[str, Any], bool]: Defense configuration data dictionary if sync=True 
                                        and successful, True if async mode, False on error.

        Raises:
            Logs timeout, connection, and unexpected errors but doesn't raise exceptions.
        """
        try:
            data = {"CX": x, "CY": y, "AID": castle_id, "KID": -1, "SSV": 0}
            if sync:
                response = await self.send_rpc("dfc", data)
                return response
            else:
                await self.send_json_message("dfc", data)
                return True
        except asyncio.TimeoutError:
            logger.error(f"Timeout while retrieving defense for castle {castle_id} at ({x}, {y})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving castle defense: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving castle defense: {e}")
            return False

    async def change_keep_defense(
        self,
        x: int,
        y: int,
        castle_id: int,
        min_units_to_consume_tools: int,
        melee_percentage: int,
        tools: List[List[int]],
        support_tools: List[List[int]],
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Change the keep defense configuration for a castle.

        Sends RPC command 'dfk' to update keep defense settings including tool
        consumption thresholds and melee unit percentages.

        Args:
            x: X coordinate of the castle location
            y: Y coordinate of the castle location
            castle_id: Unique identifier of the castle (AID)
            min_units_to_consume_tools: Minimum number of units required to consume tools
            melee_percentage: Percentage of melee units in defense formation
            tools: List of defense tools configuration [tool_id, quantity] pairs
            support_tools: List of support tools configuration [tool_id, quantity] pairs
            sync: If True, waits for response and returns data. If False, sends
                  message without waiting for response and returns True.

        Returns:
            Union[Dict[str, Any], bool]: Response data if sync=True and successful,
                                        True if async mode, False on error.
        """
        try:
            data = {
                "CX": x,
                "CY": y,
                "AID": castle_id,
                "MAUCT": min_units_to_consume_tools,
                "UC": melee_percentage,
                "S": tools,
                "STS": support_tools,
            }
            if sync:
                response = await self.send_rpc("dfk", data)
                return response
            else:
                await self.send_json_message("dfk", data)
                return True
        except asyncio.TimeoutError:
            logger.error(f"Timeout while changing keep defense for castle {castle_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while changing keep defense: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error changing keep defense: {e}")
            return False

    async def change_wall_defense(
        self,
        x: int,
        y: int,
        castle_id: int,
        left_tools: List[List[int]],
        left_unit_percentage: int,
        left_melee_percentage: int,
        middle_tools: List[List[int]],
        middle_unit_percentage: int,
        middle_melee_percentage: int,
        right_tools: List[List[int]],
        right_unit_percentage: int,
        right_melee_percentage: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Change the wall defense configuration for a castle.

        Sends RPC command 'dfw' to update wall defense settings for left, middle,
        and right wall sections with individual tool and unit configurations.

        Args:
            x: X coordinate of the castle location
            y: Y coordinate of the castle location
            castle_id: Unique identifier of the castle (AID)
            left_tools: Defense tools for left wall section [tool_id, quantity] pairs
            left_unit_percentage: Unit percentage allocation for left section
            left_melee_percentage: Melee unit percentage for left section
            middle_tools: Defense tools for middle wall section [tool_id, quantity] pairs
            middle_unit_percentage: Unit percentage allocation for middle section
            middle_melee_percentage: Melee unit percentage for middle section
            right_tools: Defense tools for right wall section [tool_id, quantity] pairs
            right_unit_percentage: Unit percentage allocation for right section
            right_melee_percentage: Melee unit percentage for right section
            sync: If True, waits for response and returns data. If False, sends
                  message without waiting for response and returns True.

        Returns:
            Union[Dict[str, Any], bool]: Response data if sync=True and successful,
                                        True if async mode, False on error.
        """
        try:
            data = {
                "CX": x,
                "CY": y,
                "AID": castle_id,
                "L": {"S": left_tools, "UP": left_unit_percentage, "UC": left_melee_percentage},
                "M": {"S": middle_tools, "UP": middle_unit_percentage, "UC": middle_melee_percentage},
                "R": {"S": right_tools, "UP": right_unit_percentage, "UC": right_melee_percentage},
            }
            if sync:
                response = await self.send_rpc("dfw", data)
                return response
            else:
                await self.send_json_message("dfw", data)
                return True
        except asyncio.TimeoutError:
            logger.error(f"Timeout while changing wall defense for castle {castle_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while changing wall defense: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error changing wall defense: {e}")
            return False

    async def change_moat_defense(
        self,
        x: int,
        y: int,
        castle_id: int,
        left_tools: List[List[int]],
        middle_tools: List[List[int]],
        right_tools: List[List[int]],
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Change the moat defense configuration for a castle.

        Sends RPC command 'dfm' to update moat defense tool placements for
        left, middle, and right moat sections.

        Args:
            x: X coordinate of the castle location
            y: Y coordinate of the castle location
            castle_id: Unique identifier of the castle (AID)
            left_tools: Moat tools for left section [tool_id, quantity] pairs
            middle_tools: Moat tools for middle section [tool_id, quantity] pairs
            right_tools: Moat tools for right section [tool_id, quantity] pairs
            sync: If True, waits for response and returns data. If False, sends
                  message without waiting for response and returns True.

        Returns:
            Union[Dict[str, Any], bool]: Response data if sync=True and successful,
                                        True if async mode, False on error.
        """
        try:
            data = {"CX": x, "CY": y, "AID": castle_id, "LS": left_tools, "MS": middle_tools, "RS": right_tools}
            if sync:
                response = await self.send_rpc("dfm", data)
                return response
            else:
                await self.send_json_message("dfm", data)
                return True
        except asyncio.TimeoutError:
            logger.error(f"Timeout while changing moat defense for castle {castle_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while changing moat defense: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error changing moat defense: {e}")
            return False