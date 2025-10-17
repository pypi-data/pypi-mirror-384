from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient
import asyncio


class Tutorial(GameClient):
    """Tutorial and new player operations handler."""

    async def choose_hero(
        self,
        hero_id: int = 802,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Choose hero during tutorial.
        
        Args:
            hero_id: Hero identifier (default: 802)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            await self.send_json_message("hdc", {"HID": hero_id})
            
            if sync:
                response = await self.wait_for_response("hdc")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while choosing hero: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for hero choice response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while choosing hero: {e}")
            return False

    async def skip_generals_intro(
        self,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Skip generals introduction.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            await self.send_json_message("sgi", {})
            
            if sync:
                response = await self.wait_for_response("sgi")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while skipping generals intro: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for skip intro response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while skipping generals intro: {e}")
            return False

    async def collect_noob_gift(
        self,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Collect new player gift.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            await self.send_json_message("uoa", {})
            
            if sync:
                response = await self.wait_for_response("uoa")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while collecting noob gift: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for noob gift collection response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while collecting noob gift: {e}")
            return False