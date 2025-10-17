import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Events(GameClient):
    """Events operations handler."""

    async def get_events(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Retrieve available events.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            await self.send_json_message("sei", {})
            
            if sync:
                response = await self.wait_for_response("sei")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while getting events: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for events response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting events: {e}")
            return False

    async def get_event_points(
        self,
        event_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve event points for specific event.
        
        Args:
            event_id: Event identifier
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            points_data = {"EID": event_id}
            await self.send_json_message("pep", points_data)
            
            if sync:
                response = await self.wait_for_response("pep")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while getting event points: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for event points response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting event points: {e}")
            return False

    async def get_ranking(
        self,
        ranking_type: int,
        category: int = -1,
        search_value: int = -1,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve ranking information.
        
        Args:
            ranking_type: Type of ranking
            category: Category identifier (default: -1)
            search_value: Search value (default: -1)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            ranking_data = {
                "LT": ranking_type,
                "LID": category,
                "SV": search_value
            }
            
            await self.send_json_message("hgh", ranking_data)
            
            if sync:
                response = await self.wait_for_response("hgh")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while getting ranking: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for ranking response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting ranking: {e}")
            return False

    async def choose_event_difficulty(
        self,
        event_id: int,
        difficulty_id: int,
        premium_unlock: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Choose event difficulty level.
        
        Args:
            event_id: Event identifier
            difficulty_id: Difficulty level identifier
            premium_unlock: Premium unlock flag (default: 0)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            difficulty_data = {
                "EID": event_id,
                "EDID": difficulty_id,
                "C2U": premium_unlock
            }
            
            await self.send_json_message("sede", difficulty_data)
            
            if sync:
                response = await self.wait_for_response("sede")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while choosing event difficulty: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for event difficulty response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while choosing event difficulty: {e}")
            return False