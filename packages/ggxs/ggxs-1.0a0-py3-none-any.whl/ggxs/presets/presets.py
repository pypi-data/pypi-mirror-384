from loguru import logger
from ..client.game_client import GameClient
import json
import re
import asyncio
from typing import Dict, Union, Any, List, Optional, Tuple


class Presets(GameClient):
    """
    Army presets management module for handling battle formations and configurations.
    
    Provides functionality for retrieving, saving, renaming, and converting
    army presets into battle wave formations.
    """
    
    async def get_presets(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve all army presets for the account.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Presets data dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            if sync:
                response = await self.send_rpc("gas", {})
                return response
            else:
                await self.send_json_message("gas", {})
                return True
                
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving army presets")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving army presets: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving army presets: {e}")
            return False
        
    async def save_new_preset(
        self,
        preset_number: int,
        formation: List[Any],
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Save a new army preset formation.
        
        Args:
            preset_number: Preset slot number (1-based)
            formation: Army formation data to save
            sync: Whether to wait for server response
            
        Returns:
            Save result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            fprs = preset_number - 1 if preset_number > 0 else 0
            preset_data = {
                "S": fprs,
                "A": formation
            }
            
            if sync:
                response = await self.send_rpc("sas", preset_data)
                return response
            else:
                await self.send_json_message("sas", preset_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while saving preset {preset_number}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while saving preset: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving preset: {e}")
            return False
        
    async def rename_preset(
        self,
        preset_number: int,
        new_name: str,
        sync: bool = True    
    ) -> Union[Dict[str, Any], bool]:
        """
        Rename an existing army preset.
        
        Args:
            preset_number: Preset slot number (1-based)
            new_name: New name for the preset
            sync: Whether to wait for server response
            
        Returns:
            Rename result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            fprs = preset_number - 1 if preset_number > 0 else 0
            rename_data = {
                "S": fprs,
                "SN": new_name
            }
            
            if sync:
                response = await self.send_rpc("upan", rename_data)
                return response
            else:
                await self.send_json_message("upan", rename_data)
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while renaming preset {preset_number} to '{new_name}'")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while renaming preset: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error renaming preset: {e}")
            return False
        
    async def select_preset(
        self,
        preset_name: str
    ) -> Optional[List[Any]]:
        """
        Select and retrieve a specific preset by name.
        
        Args:
            preset_name: Name of the preset to retrieve
            
        Returns:
            Preset formation data if found, None otherwise
        """
        try:
            preset_list = await self.get_presets()
            if not isinstance(preset_list, dict):
                logger.error("Failed to retrieve presets list")
                return None
                
            preset_data = preset_list.get("S", [])
            target = str(preset_name)
            
            for p in preset_data:
                if str(p.get("SN")) == target:
                    a_list = p.get("A", [])
                    return json.loads(a_list) if isinstance(a_list, str) else a_list
            
            available = [str(p.get("SN")) for p in preset_data]
            logger.error(f"Unknown preset: {preset_name!r}. Available: {available}")
            return None
            
        except Exception as e:
            logger.error(f"Error selecting preset '{preset_name}': {e}")
            return None
    
    def preset_to_wave(
        self, 
        data: List[Any], 
        targets_pairs: Tuple[int, int, int, int, int, int] = (6, 4, 4, 10, 4, 4)
    ) -> List[Dict[str, Dict[str, List[List[int]]]]]:
        """
        Convert preset data into battle wave formation.
        
        Args:
            data: Preset formation data
            targets_pairs: Target pair counts for each section (L_tools, R_tools, M_tools, L_units, R_units, M_units)
            
        Returns:
            List containing wave formation dictionary
        """
        try:
            def to_pairs(seq: Any) -> List[List[int]]:
                """Convert sequence to pairs of integers."""
                if not isinstance(seq, list):
                    seq = [int(n) for n in re.findall(r"-?\d+", str(seq))]
                else:
                    seq = [int(v) for v in seq]
                return [seq[i:i+2] for i in range(0, len(seq), 2)]
            
            if not isinstance(data, list):
                data = json.loads(data)
            
            # Ensure we have exactly 6 sections
            if len(data) < 6:
                data = data + [[] for _ in range(6 - len(data))]
            else:
                data = data[:6]
                
            dat = [to_pairs(ch) for ch in data]
            logger.debug(f"Converted preset data: {dat}")
            
            # Adjust each section to match target pair counts
            for i, need in enumerate(targets_pairs):
                have = len(dat[i])
                if have == 0:
                    continue
                if have < need:
                    dat[i] += [[-1, 0]] * (need - have)
                elif have > need:
                    dat[i] = dat[i][:need]
            
            return [{
                "L": {"T": dat[1], "U": dat[4]},
                "R": {"T": dat[2], "U": dat[5]},
                "M": {"T": dat[0], "U": dat[3]},
            }]
            
        except Exception as e:
            logger.error(f"Error converting preset to wave: {e}")
            return [{
                "L": {"T": [], "U": []},
                "R": {"T": [], "U": []},
                "M": {"T": [], "U": []},
            }]
    
    async def use_preset(self, preset_name: str) -> Optional[List[Dict[str, Dict[str, List[List[int]]]]]]:
        """
        Retrieve and convert a preset into battle wave formation.
        
        Args:
            preset_name: Name of the preset to use
            
        Returns:
            Wave formation data if successful, None otherwise
        """
        try:
            pdata = await self.select_preset(preset_name=preset_name)
            
            if not isinstance(pdata, list):
                logger.error(f"Preset data should be a list, not {type(pdata)}")
                return None
            
            wave = self.preset_to_wave(pdata)
            return wave
            
        except Exception as e:
            logger.error(f"Error using preset '{preset_name}': {e}")
            return None
    
    def build_final_wave(self, units: List[List[Union[int, float]]]) -> List[List[List[Union[int, float]]]]:
        """
        Build final wave formation from unit list.
        
        Args:
            units: List of [unit_id, amount] pairs
            
        Returns:
            Final wave formation data
        """
        try:
            wave = []
            for u in units:
                if (isinstance(u, (list, tuple)) and len(u) == 2 and 
                    all(isinstance(x, (int, float)) for x in u)):
                    wave.append(list(u))
            
            # Pad with empty slots to reach 8 units
            while len(wave) < 8:
                wave.append([-1, 0])
                
            wave = wave[:8]
            return [wave]
            
        except Exception as e:
            logger.error(f"Error building final wave: {e}")
            return [[[-1, 0]] * 8]