import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class Wall(GameClient):
    """Wall upgrade operations handler."""

    async def upgrade_wall(
        self,
        building_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Upgrade wall building.
        
        Args:
            building_id: Wall building identifier to upgrade
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            upgrade_data = {"OID": building_id, "PWR": 0, "PO": -1}
            await self.send_json_message("eud", upgrade_data)
            
            if sync:
                response = await self.wait_for_response("eud")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while upgrading wall: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for wall upgrade response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while upgrading wall: {e}")
            return False