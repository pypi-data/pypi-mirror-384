from ..client.game_client import GameClient
from ..utils.utils import Utils
from loguru import logger
import json
import asyncio
from typing import Dict, Union, Any, List, Optional


class Attack(GameClient):
    """
    Attack module for handling military operations including attacks, conquers, and cooldown management.
    
    Provides functionality for sending attacks, conquer missions, and managing NPC cooldowns.
    """
    
    async def send_attack(
        self,
        kingdom: int,
        sx: int,
        sy: int,
        tx: int,
        ty: int,
        army: List[Any],
        lord_id: int = 0,
        horses_type: int = -1,
        feathers: int = 0,
        slowdown: int = 0,
        boosters: List[Any] = [],
        support_tools: List[Any] = [],
        final_wave: List[Any] = [],
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Send a regular attack to a target location.
        
        Args:
            kingdom: Target kingdom ID
            sx: Source X coordinate
            sy: Source Y coordinate
            tx: Target X coordinate
            ty: Target Y coordinate
            army: List of army units to send
            lord_id: Lord ID to accompany the attack (0 for none)
            horses_type: Type of horses to use (-1 for default)
            feathers: Feathers bonus for speed
            slowdown: Slowdown factor
            boosters: List of boosters to apply
            support_tools: List of support tools
            final_wave: Final wave units
            sync: Whether to wait for server response
            
        Returns:
            Attack result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            attack_data = {
                "SX": sx,
                "SY": sy,
                "TX": tx,
                "TY": ty,
                "KID": kingdom,
                "LID": lord_id,
                "WT": 0,
                "HBW": horses_type,
                "BPC": 0,
                "ATT": 0,
                "AV": 0,
                "LP": 0,
                "FC": 0,
                "PTT": feathers,
                "SD": slowdown,
                "ICA": 0,
                "CD": 99,
                "A": army,
                "BKS": boosters,
                "AST": support_tools,
                "RW": final_wave,
                "ASCT": 0,
            }
            
            if sync:
                response = await self.send_rpc("cra", attack_data)
                return response
            else:
                await self.send_json_message("cra", attack_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while sending attack from ({sx},{sy}) to ({tx},{ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while sending attack: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending attack: {e}")
            return False
    
    async def send_conquer(
        self,
        kingdom: int,
        sx: int,
        sy: int,
        tx: int,
        ty: int,
        army: List[Any],
        castellan_id: int = 0,
        horses_type: int = -1,
        feathers: int = 0,
        slowdown: int = 0,
        boosters: List[Any] = [],
        support_tools: List[Any] = [],
        final_wave: List[Any] = [],
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Send a conquer mission to capture a location.
        
        Args:
            kingdom: Target kingdom ID
            sx: Source X coordinate
            sy: Source Y coordinate
            tx: Target X coordinate
            ty: Target Y coordinate
            army: List of army units to send
            castellan_id: Castellan ID for the conquer mission
            horses_type: Type of horses to use (-1 for default)
            feathers: Feathers bonus for speed
            slowdown: Slowdown factor
            boosters: List of boosters to apply
            support_tools: List of support tools
            final_wave: Final wave units
            sync: Whether to wait for server response
            
        Returns:
            Conquer result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            conquer_data = {
                "SX": sx,
                "SY": sy,
                "TX": tx,
                "TY": ty,
                "KID": kingdom,
                "LID": castellan_id,
                "WT": 0,
                "HBW": horses_type,
                "BPC": 0,
                "ATT": 7,
                "AV": 0,
                "LP": 0,
                "FC": 0,
                "PTT": feathers,
                "SD": slowdown,
                "ICA": 0,
                "CD": 99,
                "A": army,
                "BKS": boosters,
                "AST": support_tools,
                "RW": final_wave,
                "ASCT": 0,
            }
            
            if sync:
                response = await self.send_rpc("cra", conquer_data)
                return response
            else:
                await self.send_json_message("cra", conquer_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while sending conquer from ({sx},{sy}) to ({tx},{ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while sending conquer: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending conquer: {e}")
            return False
        
    async def time_skip_npc_cooldown(
        self,
        kingdom: int,
        tx: int,
        ty: int,
        time_skip: str,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Skip NPC cooldown using time skip items.
        
        Args:
            kingdom: Target kingdom ID
            tx: Target X coordinate
            ty: Target Y coordinate
            time_skip: Time skip item identifier
            sync: Whether to wait for server response
            
        Returns:
            Skip result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            skip_data = {
                "X": tx,
                "Y": ty,
                "MID": -1,
                "NID": -1,
                "MST": time_skip,
                "KID": str(kingdom)
            }
            
            if sync:
                response = await self.send_rpc("msd", skip_data)
                return response
            else:
                await self.send_json_message("msd", skip_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while skipping NPC cooldown at ({tx},{ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while skipping NPC cooldown: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error skipping NPC cooldown: {e}")
            return False
    
    async def autoskip_npc_cooldown(
        self,
        kingdom: int,
        tx: int,
        ty: int,
        cooldown_time: int,
        skips: Optional[List[str]] = None
    ) -> None:
        """
        Automatically skip NPC cooldown using calculated time skip items.
        
        Args:
            kingdom: Target kingdom ID
            tx: Target X coordinate
            ty: Target Y coordinate
            cooldown_time: Total cooldown time in seconds
            skips: Available time skip items (optional)
        """
        try:
            utils = Utils()
            if cooldown_time > 0:
                skips_list = utils.skip_calculator(cooldown_time, skips)
                for skip in skips_list:
                    await self.time_skip_npc_cooldown(kingdom, tx, ty, skip, sync=False)
                    
        except Exception as e:
            logger.error(f"Error during auto-skip NPC cooldown: {e}")
    
    def attack_units_sum(
        self,
        waves: Union[List[Dict[str, Any]], str],
        final_wave: Union[List[Any], str]
    ) -> Dict[str, Any]:
        """
        Calculate the total number of units used in attack waves.
        
        Args:
            waves: List of wave dictionaries or JSON string
            final_wave: Final wave list or JSON string
            
        Returns:
            Dictionary containing per-wave totals and grand total
        """
        try:
            per_wave = []
            total_waves = 0
            
            if not isinstance(waves, list):
                waves = json.loads(waves)
                
            if not isinstance(final_wave, list):
                final_wave = json.loads(final_wave)
                
            for w in waves:
                wave_sum = 0
                if not isinstance(w, dict):
                    continue
                
                for side in ("L", "R", "M"):
                    part = w.get(side, {})
                    units = part.get("U", [])
                    for u in units:
                        if isinstance(u, (list, tuple)) and len(u) >= 2 and isinstance(u[1], (int, float)) and u[1] > 0:
                            wave_sum += int(u[1])
                
                per_wave.append(wave_sum)
                total_waves += wave_sum
            
            final_total = 0  
            if isinstance(final_wave, list):
                for item in final_wave:
                    if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], (int, float)) and item[1] > 0:
                        final_total += int(item[1])
            
            grand_total = total_waves + final_total
            
            return {
                "per_wave": per_wave,
                "total_waves": total_waves,
                "final_total": final_total,
                "grand_total": grand_total
            }
            
        except Exception as e:
            logger.error(f"Error calculating attack units sum: {e}")
            return {
                "per_wave": [],
                "total_waves": 0,
                "final_total": 0,
                "grand_total": 0
            }
            
            
