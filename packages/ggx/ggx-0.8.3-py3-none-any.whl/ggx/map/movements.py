from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union, Any


class Movements(GameClient):
    """
    Movements module for handling army movements and retrieval operations.
    
    Provides functionality for retrieving movement information and recalling armies.
    """
    
    async def get_movements(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve all current army movements for the player.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Movements data dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("gam", {})
            
            if sync:
                response = await self.wait_for_response("gam")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving movements from server")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving movements: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving movements: {e}")
            return False

    async def retrieve_army(
        self,
        movement_id: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Recall a specific army movement by its ID.
        
        Args:
            movement_id: The ID of the movement to recall
            sync: Whether to wait for server response
            
        Returns:
            Retrieval result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("mcm", {"MID": movement_id})
            
            if sync:
                response = await self.wait_for_response("mcm")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while retrieving army movement {movement_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving army: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving army: {e}")
            return False