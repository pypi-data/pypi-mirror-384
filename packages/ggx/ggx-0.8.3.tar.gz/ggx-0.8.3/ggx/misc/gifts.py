from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient
import asyncio


class Gifts(GameClient):
    """Gifts and collection operations handler."""

    async def collect_citizen_gift(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Collect citizen gifts.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """


        try:
            await self.send_json_message("irc", {})
            
            if sync:
                response = await self.wait_for_response("irc")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while collecting citizen gift: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for citizen gift collection response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while collecting citizen gift: {e}")
            return False

    async def collect_citizen_quest(self, choice: int, sync: bool = True) -> Union[Dict, bool]:
        """
        Collect citizen quest reward.
        
        Args:
            choice: Quest choice identifier
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
    
        try:
            await self.send_json_message("jjc", {"CO": choice})
            
            if sync:
                response = await self.wait_for_response("jjc")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while collecting citizen quest: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for citizen quest collection response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while collecting citizen quest: {e}")
            return False

    async def collect_ressource_gift(self, resource_type: int, sync: bool = True) -> Union[Dict, bool]:
        """
        Collect resource gift.
        
        Args:
            resource_type: Type of resource to collect
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """


        try:
            await self.send_json_message("rcc", {"RT": resource_type})
            
            if sync:
                response = await self.wait_for_response("rcc")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while collecting resource gift: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for resource gift collection response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while collecting resource gift: {e}")
            return False