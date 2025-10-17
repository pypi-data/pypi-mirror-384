from typing import Dict, Union, List, Any, Tuple
from loguru import logger
import asyncio

from ..client.game_client import GameClient


class Misc(GameClient):
    """Miscellaneous game operations handler."""

    async def change_emblem(
        self,
        bg_type: int,
        bg_color_1: int,
        bg_color_2: int,
        icons_type: int,
        icon_id_1: int,
        icon_color_1: int,
        icon_id_2: int,
        icon_color_2: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Change player emblem configuration.
        
        Args:
            bg_type: Background type identifier
            bg_color_1: Primary background color
            bg_color_2: Secondary background color
            icons_type: Icons type identifier
            icon_id_1: First icon identifier
            icon_color_1: First icon color
            icon_id_2: Second icon identifier
            icon_color_2: Second icon color
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            emblem_data = {
                "CAE": {
                    "BGT": bg_type,
                    "BGC1": bg_color_1,
                    "BGC2": bg_color_2,
                    "SPT": icons_type,
                    "S1": icon_id_1,
                    "SC1": icon_color_1,
                    "S2": icon_id_2,
                    "SC2": icon_color_2,
                }
            }
            
            if sync:
                response = await self.send_rpc("cem", emblem_data)
                return response
            else:
                await self.send_json_message("cem", emblem_data)
                return True
                
        except ConnectionError as e:
            logger.error(f"Connection error while changing emblem: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for emblem change response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while changing emblem: {e}")
            return False

    def spy_units_sum(
        self,
        game_db: Dict,
        def_setup: List[Any]
    ) -> int:
        """
        Calculate total number of spy units from defense setup.
        
        Args:
            game_db: Game database containing unit information
            def_setup: Defense setup configuration containing unit pairs
            
        Returns:
            Total number of spy units as integer
        """
        logger.debug("Calculating spy units sum from defense setup")
        
        try:
            units_db = (game_db or {}).get("units", [])
            
            # Filter soldier units
            soldiers = [
                u for u in units_db
                if u.get("group") == "Unit" and u.get("role") in ("soldier", "ranged", "melee")
            ]
            sold_ids = {u["wodID"] for u in soldiers}
            

            def to_pairs(obj: Any) -> List[Tuple[int, int]]:
                """
                Convert various data structures to list of unit pairs.
                
                Args:
                    obj: Input object (dict, list, tuple, or None)
                    
                Returns:
                    List of (wodID, amount) pairs
                """
                if obj is None:
                    return []

                if isinstance(obj, dict):
                    # Extract all pairs from dictionary values
                    pairs = []
                    for values in obj.values():
                        if isinstance(values, (list, tuple)):
                            pairs.extend(self._validate_pairs(values))
                    
                    return pairs

                if isinstance(obj, (list, tuple)):
                    pairs = self._validate_pairs(obj)
                    logger.debug(f"Converted list/tuple to {len(pairs)} unit pairs")
                    return pairs
                
                logger.warning(f"Unsupported object type for pair conversion: {type(obj)}")
                return []

            # Convert defense setup to pairs and calculate total
            pairs = to_pairs(def_setup)
            total_units = 0
            valid_pairs_count = 0
            
            for w, a in pairs:
                if w in sold_ids and isinstance(a, int) and a > 0:
                    total_units += a
                    valid_pairs_count += 1
            
            logger.info(f"Spy units calculation complete: {total_units} units from {valid_pairs_count} valid pairs")
            return int(total_units)
            
        except Exception as e:
            logger.error(f"Error calculating spy units sum: {e}")
            return 0

    def _validate_pairs(self, obj: Union[List, Tuple]) -> List[Tuple[int, int]]:
        """
        Validate and extract unit pairs from list/tuple.
        
        Args:
            obj: List or tuple containing unit data
            
        Returns:
            List of validated (wodID, amount) pairs
        """
        pairs = []
        
        for item in obj:
            if (isinstance(item, (list, tuple)) and len(item) == 2 and 
                all(isinstance(x, int) for x in item)):
                pairs.append(tuple(item))
            elif isinstance(item, (list, tuple)):
                # Handle nested structures
                for sub_item in item:
                    if (isinstance(sub_item, (list, tuple)) and len(sub_item) == 2 and
                        all(isinstance(x, int) for x in sub_item)):
                        pairs.append(tuple(sub_item))
        
        return pairs

    def incoming_attack_sum(
        self,
        game_db: Dict,
        attack_setup: Any
    ) -> int:
        """
        Calculate total number of units in incoming attack.
        
        Args:
            game_db: Game database containing unit information
            attack_setup: Attack setup configuration (int, dict, or list)
            
        Returns:
            Total number of attacking units as integer
        """
        logger.debug("Calculating incoming attack sum")
        
        try:
            units_db = (game_db or {}).get("units", [])
            
            # Filter soldier units
            soldiers = [
                u for u in units_db if u.get("group") == "Unit" and u.get("role") in ("soldier", "ranged", "melee")
            ]
            sold_ids = {u["wodID"] for u in soldiers}
            
            # Handle integer attack setup (direct unit count)
            if isinstance(attack_setup, int):
                logger.info(f"Direct attack unit count provided: {attack_setup}")
                return attack_setup

            # Handle dictionary attack setup
            if isinstance(attack_setup, dict):
                logger.debug("Processing dictionary-based attack setup")
                attack_data = [pair for values in attack_setup.values() for pair in self._validate_pairs(values)]
                soldiers_list = [{"wodID": w, "amount": a} for w, a in attack_data if w in sold_ids and isinstance(a, int) and a > 0]
                total_units = sum(unit["amount"] for unit in soldiers_list)
                logger.info(f"Attack units from dictionary: {total_units} units from {len(soldiers_list)} valid soldier entries")
                return int(total_units)

            logger.warning(f"Unsupported attack setup type: {type(attack_setup)}")
            return 0
            
        except Exception as e:
            logger.error(f"Error calculating incoming attack sum: {e}")
            return 0