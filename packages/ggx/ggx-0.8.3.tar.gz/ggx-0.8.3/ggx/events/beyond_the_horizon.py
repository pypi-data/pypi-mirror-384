import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class BeyondTheHorizon(GameClient):
    """Beyond The Horizon operations handler."""

    async def get_bth_points(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Retrieve Beyond The Horizon points.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            await self.send_json_message("tsh", {})
            
            if sync:
                response = await self.wait_for_response("tsh")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while getting BTH points: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for BTH points response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting BTH points: {e}")
            return False

    async def choose_bth_castle(
        self,
        castle_id: int,
        only_rubies: int = 0,
        use_rubies: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Choose castle in Beyond The Horizon.
        
        Args:
            castle_id: Castle identifier
            only_rubies: Use only rubies flag (default: 0)
            use_rubies: Use rubies flag (default: 0)
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            castle_data = {
                "ID": castle_id,
                "OC2": only_rubies,
                "PWR": use_rubies,
                "GST": 3
            }
            
            await self.send_json_message("tsc", castle_data)
            
            if sync:
                response = await self.wait_for_response("tsc")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while choosing BTH castle: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for BTH castle choice response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while choosing BTH castle: {e}")
            return False

    async def get_bth_token(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Get Beyond The Horizon token.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            token_data = {"GST": 3}
            await self.send_json_message("glt", token_data)
            
            if sync:
                response = await self.wait_for_response("glt")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while getting BTH token: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for BTH token response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting BTH token: {e}")
            return False

    async def login_bth(
        self,
        token: str,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Login to Beyond The Horizon with token.
        
        Args:
            token: Authentication token
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            login_data = {"TLT": token}
            await self.send_json_message("tlep", login_data)
            
            if sync:
                response = await self.wait_for_response("lli")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while logging into BTH: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for BTH login response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while logging into BTH: {e}")
            return False