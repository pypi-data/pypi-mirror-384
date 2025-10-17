import asyncio
from typing import Dict, Union, List, Optional
from loguru import logger
from ..client.game_client import GameClient


class Buildings(GameClient):
    """Buildings construction and management operations handler."""

    async def build(
        self,
        wod_id: int,
        x: int,
        y: int,
        rotated: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Construct a new building.
        
        Args:
            wod_id: Building template identifier
            x: X coordinate
            y: Y coordinate
            rotated: Rotation flag (default: 0)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            build_data = {
                "WID": wod_id,
                "X": x,
                "Y": y,
                "R": rotated,
                "PWR": 0,
                "PO": -1,
                "DOID": -1,
            }
            
            await self.send_json_message("ebu", build_data)
            
            if sync:
                response = await self.wait_for_response("ebu")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while building: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for build response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while building: {e}")
            return False

    async def upgrade_building(
        self, 
        building_id: int, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Upgrade an existing building.
        
        Args:
            building_id: Building identifier to upgrade
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            upgrade_data = {"OID": building_id, "PWR": 0, "PO": -1}
            await self.send_json_message("eup", upgrade_data)
            
            if sync:
                response = await self.wait_for_response("eup")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while upgrading building: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for building upgrade response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while upgrading building: {e}")
            return False

    async def move_building(
        self,
        building_id: int,
        x: int,
        y: int,
        rotated: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Move a building to new coordinates.
        
        Args:
            building_id: Building identifier to move
            x: New X coordinate
            y: New Y coordinate
            rotated: Rotation flag (default: 0)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            move_data = {"OID": building_id, "X": x, "Y": y, "R": rotated}
            await self.send_json_message("emo", move_data)
            
            if sync:
                response = await self.wait_for_response("emo")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while moving building: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for building move response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while moving building: {e}")
            return False

    async def sell_building(
        self, 
        building_id: int, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Sell a building.
        
        Args:
            building_id: Building identifier to sell
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            await self.send_json_message("sbd", {"OID": building_id})
            
            if sync:
                response = await self.wait_for_response("sbd")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while selling building: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for building sell response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while selling building: {e}")
            return False

    async def destroy_building(
        self, 
        building_id: int, 
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Destroy a building.
        
        Args:
            building_id: Building identifier to destroy
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            await self.send_json_message("edo", {"OID": building_id})
            
            if sync:
                response = await self.wait_for_response("edo")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while destroying building: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for building destroy response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while destroying building: {e}")
            return False

    async def skip_construction_free(
        self,
        building_id: int,
        free_skip: int = 1,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Skip construction using free skip.
        
        Args:
            building_id: Building identifier
            free_skip: Free skip flag (default: 1)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            skip_data = {"OID": building_id, "FS": free_skip}
            await self.send_json_message("fco", skip_data)
            
            if sync:
                response = await self.wait_for_response("fco")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while skipping construction: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for construction skip response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while skipping construction: {e}")
            return False

    async def time_skip_construction(
        self,
        building_id: int,
        time_skip: str,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Skip construction using time skip.
        
        Args:
            building_id: Building identifier
            time_skip: Time skip value
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            time_skip_data = {"OID": building_id, "MST": time_skip}
            await self.send_json_message("msb", time_skip_data)
            
            if sync:
                response = await self.wait_for_response("msb")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while time skipping construction: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for time skip response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while time skipping construction: {e}")
            return False



    async def instant_build(
        self,
        building_id: int,
        wod_id: int,
        x: int,
        y: int,
        rotated: int = 0,
        time_skips: List[str] = None,
        cooldown: int = 0,
        free_skip: int = 1,
        sync: bool = True
    ) -> None:
        """
        Perform instant building construction with skips.
        
        Args:
            building_id: Building identifier
            wod_id: Building template identifier
            x: X coordinate
            y: Y coordinate
            rotated: Rotation flag (default: 0)
            time_skips: List of time skip values
            cooldown: Cooldown in seconds (default: 0)
            free_skip: Free skip flag (default: 1)
            sync: Whether to wait for completion
        """
        try:
            await self.build(wod_id, x, y, rotated, sync=False)
            
            if time_skips:
                for skip in time_skips:
                    await self.time_skip_construction(building_id, skip, sync=False)
            
            if cooldown > 0:
                await asyncio.sleep(cooldown)
                
            await self.skip_construction_free(building_id, free_skip, sync=False)
            
            if sync:
                await self.wait_finish_construction(building_id, timeout=30)
                
        except Exception as e:
            logger.error(f"Error during instant build: {e}")

    async def instant_upgrade(
        self,
        building_id: int,
        time_skips: List[str] = None,
        cooldown: int = 0,
        free_skip: int = 1,
        sync: bool = True
    ) -> None:
        """
        Perform instant building upgrade with skips.
        
        Args:
            building_id: Building identifier
            time_skips: List of time skip values
            cooldown: Cooldown in seconds (default: 0)
            free_skip: Free skip flag (default: 1)
            sync: Whether to wait for completion
        """
        try:
            await self.upgrade_building(building_id, sync=False)
            
            if time_skips:
                for skip in time_skips:
                    await self.time_skip_construction(building_id, skip, sync=False)
            
            if cooldown > 0:
                await asyncio.sleep(cooldown)
                
            await self.skip_construction_free(building_id, free_skip, sync=False)
            
            if sync:
                await self.wait_finish_construction(building_id, timeout=30)
                
        except Exception as e:
            logger.error(f"Error during instant upgrade: {e}")

    async def instant_destroy(
        self,
        building_id: int,
        time_skips: List[str] = None,
        cooldown: int = 0,
        free_skip: int = 1,
        sync: bool = True
    ) -> None:
        """
        Perform instant building destruction with skips.
        
        Args:
            building_id: Building identifier
            time_skips: List of time skip values
            cooldown: Cooldown in seconds (default: 0)
            free_skip: Free skip flag (default: 1)
            sync: Whether to wait for completion
        """
        try:
            await self.destroy_building(building_id, sync=False)
            
            if time_skips:
                for skip in time_skips:
                    await self.time_skip_construction(building_id, skip, sync=False)
            
            if cooldown > 0:
                await asyncio.sleep(cooldown)
                
            await self.skip_construction_free(building_id, free_skip, sync=False)
            
        except Exception as e:
            logger.error(f"Error during instant destroy: {e}")