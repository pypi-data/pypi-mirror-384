import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient


class BestSeller(GameClient):
    """Best seller shop operations handler."""

    async def buy_from_bestseller(
        self,
        bestseller_id: int,
        package_type: int,
        amount: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Buy package from best seller shop.
        
        Args:
            bestseller_id: Best seller offer identifier
            package_type: Type of package to buy
            amount: Number of packages to buy
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """
        try:
            bestseller_data = {
                "OID": package_type,
                "AMT": amount,
                "POID": bestseller_id
            }
            
            await self.send_json_message("bso", bestseller_data)
            
            if sync:
                response = await self.wait_for_response("bso")
                return response
            return True
            
        except ConnectionError as e:
            logger.error(f"Connection error while buying from bestseller: {e}")
            return False
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for bestseller purchase response")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while buying from bestseller: {e}")
            return False