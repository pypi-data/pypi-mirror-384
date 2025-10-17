from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Generator, Union, List, Tuple


class Map(GameClient):
    """
    Map module for handling map-related operations in the game.
    Provides functionality for scanning map chunks, finding NPCs and players,
    and retrieving target information for both PvE and PvP encounters.
    """

    async def get_map_chunks_as(
        self,
        kingdom: int,
        x: int,
        y: int
    ) -> bool:
        """
        Get map chunks asynchronously without waiting for response.
        
        Args:
            kingdom: Kingdom ID to scan.
            x: Starting X coordinate for the map chunk.
            y: Starting Y coordinate for the map chunk.
            
        Returns:
            bool: True if message was sent successfully, False if error occurred.
        """
        try:
            await self.send_json_message("gaa", {
                "KID": kingdom,
                "AX1": x,
                "AY1": y,
                "AX2": x + 12,
                "AY2": y + 12
            })
            return True
        except ConnectionError as e:
            logger.error(f"Connection error during scan map chuncks async: {e}")
            return False
        except Exception as e:
            logger.error(f"Error getting map chunks async at coordinates ({x}, {y}): {e}")
            return False

    async def get_map_chunks_sync(
        self,
        kingdom: int,
        x: int,
        y: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Get map chunks with optional synchronous response.
        
        Args:
            kingdom: Kingdom ID to scan.
            x: Starting X coordinate for the map chunk.
            y: Starting Y coordinate for the map chunk.
            sync: If True, waits for server response and returns data.
                  If False, sends message asynchronously without waiting for response.
                  
        Returns:
            Union[Dict, bool]: Map data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"KID": kingdom, "AX1": x, "AY1": y, "AX2": x + 12, "AY2": y + 12}
            if sync:
                response = await self.send_rpc("gaa", data)
                return response
            else:
                await self.send_json_message("gaa", data)
                return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting map chunks at coordinates ({x}, {y})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during scan map sync: {e}")
            return False
        except Exception as e:
            logger.error(f"Error getting map chunks sync at coordinates ({x}, {y}): {e}")
            return False

    async def get_closest_npc(
        self,
        kingdom: int,
        npc_type: int,
        min_level: int = 1,
        max_level: int = -1,
        owner_id: int = -1,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Find closest NPC with filtering options.
        
        Args:
            kingdom: Kingdom ID to search in.
            npc_type: Type of NPC to find.
            min_level: Minimum NPC level (default: 1).
            max_level: Maximum NPC level (default: -1 for no limit).
            owner_id: Owner ID filter (default: -1 for any).
            sync: If True, waits for server response.
                  
        Returns:
            Union[Dict, bool]: NPC data dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"T": npc_type, "KID": kingdom, "LMIN": min_level, "LMAX": max_level, "NID": owner_id}
            if sync:
                response = await self.send_rpc("fnm", data)
                return response
            else:
                await self.send_json_message("fnm", data)
                return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout finding closest NPC of type {npc_type} in kingdom {kingdom}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during finding npc: {e}")
            return False
        except Exception as e:
            logger.error(f"Error finding closest NPC of type {npc_type}: {e}")
            return False

    async def get_npc_target_infos(
        self,
        tx: int,
        ty: int,
        sx: int,
        sy: int,
        kid: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Get detailed information about an NPC target.
        
        Args:
            tx: Target X coordinate.
            ty: Target Y coordinate.
            sx: Source X coordinate.
            sy: Source Y coordinate.
            kid: Kingdom ID.
            sync: If True, waits for server response.
                  
        Returns:
            Union[Dict, bool]: NPC target information dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"TX": tx, "TY": ty, "SX": sx, "SY": sy, "KID": kid}
            if sync:
                response = await self.send_rpc("adi", data)
                return response
            else:
                await self.send_json_message("adi", data)
                return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting NPC info at target coordinates ({tx}, {ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during get npc target info: {e}")
            return False
        except Exception as e:
            logger.error(f"Error getting NPC target info at ({tx}, {ty}): {e}")
            return False

    async def get_pvp_target_infos(
        self,
        tx: int,
        ty: int,
        sx: int,
        sy: int,
        kid: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Get detailed information about a PvP target.
        
        Args:
            tx: Target X coordinate.
            ty: Target Y coordinate.
            sx: Source X coordinate.
            sy: Source Y coordinate.
            kid: Kingdom ID.
            sync: If True, waits for server response.
                  
        Returns:
            Union[Dict, bool]: PvP target information dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"TX": tx, "TY": ty, "SX": sx, "SY": sy, "KID": kid}
            if sync:
                response = await self.send_rpc("aci", data)
                return response
            else:
                await self.send_json_message("aci", data)
                return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting PvP info at target coordinates ({tx}, {ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during getting PvP info: {e}")
            return False
        except Exception as e:
            logger.error(f"Error getting PvP target info at ({tx}, {ty}): {e}")
            return False

    async def find_by_name(
        self,
        user_name: str,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Find player by name in the game world.
        
        Args:
            user_name: Player name to search for.
            sync: If True, waits for server response.
                  
        Returns:
            Union[Dict, bool]: Player information dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"PN": user_name}
            if sync:
                response = await self.send_rpc("wsp", data)
                return response
            else:
                await self.send_json_message("wsp", data)
                return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout finding player with name: {user_name}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during finding player with name: {e}")
            return False
        except Exception as e:
            logger.error(f"Error finding player by name '{user_name}': {e}")
            return False

    def _spiral_coords(self, max_radius: int, cx: int, cy: int) -> Generator[Tuple[int, int], None, None]:
        """
        Generate spiral coordinates around a center point.
        
        Args:
            max_radius: Maximum radius from center to generate coordinates.
            cx: Center X coordinate.
            cy: Center Y coordinate.
            
        Yields:
            Tuple[int, int]: Coordinates (x, y) in spiral pattern around center.
        """
        step = 13
        seen = set()

        for radius in range(step, max_radius + 1, step):
            for x in range(cx - radius, cx + radius + 1, step):
                pt = (x, cy - radius)
                if pt not in seen:
                    seen.add(pt)
                    yield pt
            for y in range(cy - radius, cy + radius + 1, step):
                pt = (cx + radius, y)
                if pt not in seen:
                    seen.add(pt)
                    yield pt
            for x in range(cx + radius, cx - radius - 1, -step):
                pt = (x, cy + radius)
                if pt not in seen:
                    seen.add(pt)
                    yield pt
            for y in range(cy + radius, cy - radius - 1, -step):
                pt = (cx - radius, y)
                if pt not in seen:
                    seen.add(pt)
                    yield pt

        seen.clear()

    async def map_scanner(
        self,
        kingdom: int,
        max_radius: int,
        castle_x: int,
        castle_y: int,
        delay: float = 0.01
    ) -> int:
        """
        Scan map in spiral pattern around specified coordinates.
        
        Args:
            kingdom: Kingdom ID to scan.
            max_radius: Maximum scanning radius from center coordinates.
            castle_x: Center X coordinate for scanning.
            castle_y: Center Y coordinate for scanning.
            delay: Delay in seconds between each chunk request (default: 0.01).
            
        Returns:
            int: Number of successfully scanned map chunks.
        """
        scanned_count = 0
        try:
            logger.info(f"Starting map scan around coordinates ({castle_x}, {castle_y}) with radius {max_radius}")

            for x, y in self._spiral_coords(max_radius=max_radius, cx=castle_x, cy=castle_y):
                success = await self.get_map_chunks_as(kingdom, x, y)
                if success:
                    scanned_count += 1
                if delay > 0:
                    await asyncio.sleep(delay)

            logger.info(f"Map scan complete. Successfully scanned {scanned_count} chunks")
            return scanned_count
        except ConnectionError as e:
            logger.error(f"Connection error during map scanning: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during map scanning around ({castle_x}, {castle_y}): {e}")
            return scanned_count

    async def map_multi_scanner(
        self,
        kingdom: int,
        max_radius: int,
        castle_x: int,
        castle_y: int,
        interval: float,
        delay: float = 0.01
    ) -> None:
        """
        Continuous map scanner with configurable intervals between scans.
        
        Args:
            kingdom: Kingdom ID to scan.
            max_radius: Maximum scanning radius from center coordinates.
            castle_x: Center X coordinate for scanning.
            castle_y: Center Y coordinate for scanning.
            interval: Time interval in seconds between complete scan cycles.
            delay: Delay in seconds between each chunk request (default: 0.01).
            
        Note:
            This function runs indefinitely until cancelled. Use a flag to stop.
        """
        scan_count = 0

        while True:
            try:
                scan_count += 1
                logger.info(f"Starting continuous scan iteration #{scan_count}")

                chunks_scanned = await self.map_scanner(kingdom, max_radius, castle_x, castle_y, delay)

                logger.info(f"Completed scan #{scan_count}. Scanned {chunks_scanned} chunks. Next scan in {interval} seconds")
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Continuous map scanning cancelled by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous map scanning iteration #{scan_count}: {e}")
                await asyncio.sleep(10)

    async def get_conquer_outpost_infos(
        self,
        tx: int,
        ty: int,
        sx: int,
        sy: int,
        kid: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Get detailed information about a conquer outpost target.
        
        Args:
            tx: Target X coordinate.
            ty: Target Y coordinate.
            sx: Source X coordinate.
            sy: Source Y coordinate.
            kid: Kingdom ID.
            sync: If True, waits for server response.
                  
        Returns:
            Union[Dict, bool]: Conquer outpost information dictionary if sync=True and successful,
                              True if sync=False and message sent successfully,
                              False if error occurred.
        """
        try:
            data = {"TX": tx, "TY": ty, "SX": sx, "SY": sy, "KID": kid}
            if sync:
                response = await self.send_rpc("coi", data)
                return response
            else:
                await self.send_json_message("coi", data)
                return True
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting conquer outpost info at target coordinates ({tx}, {ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during multi map scanning: {e}")
            return False
        except Exception as e:
            logger.error(f"Error getting conquer outpost info at ({tx}, {ty}): {e}")
            return False

    async def batch_get_map_chunks(
        self,
        kingdom: int,
        coordinates: List[Tuple[int, int]],
        batch_size: int = 5,
        delay: float = 0.1
    ) -> int:
        """
        Get multiple map chunks in batches for better performance.
        
        Args:
            kingdom: Kingdom ID to scan.
            coordinates: List of coordinate tuples (x, y) to scan.
            batch_size: Number of concurrent requests per batch (default: 5).
            delay: Delay in seconds between batches (default: 0.1).
            
        Returns:
            int: Number of successfully processed map chunk requests.
        """
        success_count = 0

        for i in range(0, len(coordinates), batch_size):
            batch = coordinates[i:i + batch_size]
            tasks = [self.get_map_chunks_as(kingdom, x, y) for x, y in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if result is True:
                    success_count += 1

            if delay > 0 and i + batch_size < len(coordinates):
                await asyncio.sleep(delay)

        logger.info(f"Batch map chunk requests completed: {success_count} successful out of {len(coordinates)} total requests")
        return success_count

    async def calculate_travel_time(
        self,
        sx: int,
        sy: int,
        tx: int,
        ty: int,
        march_speed: float = 1.0
    ) -> float:
        """
        Calculate estimated travel time for support troops between two points.
        
        Args:
            sx: Source X coordinate.
            sy: Source Y coordinate.
            tx: Target X coordinate.
            ty: Target Y coordinate.
            march_speed: March speed multiplier (default: 1.0).
            
        Returns:
            float: Estimated travel time in minutes.
        """
        try:
            distance = ((tx - sx) ** 2 + (ty - sy) ** 2) ** 0.5
            base_time_per_unit = 2.0  # minutes per unit distance
            travel_time = (distance * base_time_per_unit) / march_speed
            logger.debug(f"Calculated support travel time: {travel_time:.2f} minutes for distance {distance:.2f}")
            return travel_time
        except Exception as e:
            logger.error(f"Error calculating support travel time: {e}")
            return 0.0
