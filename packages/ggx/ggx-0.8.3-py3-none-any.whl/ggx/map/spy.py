from ..client.game_client import GameClient
from loguru import logger
from typing import Dict, Union
import asyncio


class Spy(GameClient):
    """
    Client extension for handling spy operations in the game.
    
    Provides methods for sending spies, sabotage missions, and retrieving spy information.
    """
    
    async def send_spy(
        self,
        kingdom: int,
        source_id: int,
        tx: int,
        ty: int,
        spies_nr: int,
        precision: int,
        horses_type: int = -1,
        slowdown: int = 0,
        feathers: int = 0,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Send spies to gather intelligence on a target location.
        
        Args:
            kingdom: Target kingdom ID
            source_id: Source building ID
            tx: Target X coordinate
            ty: Target Y coordinate
            spies_nr: Number of spies to send
            precision: Spy precision level (0-100)
            horses_type: Type of horses to use (-1 for default)
            slowdown: Slowdown factor
            feathers: Feathers bonus
            sync: Whether to wait for response
            
        Returns:
            Response dictionary if sync=True, otherwise True on success
            
        Raises:
            ConnectionError: If connection is lost during operation
            TimeoutError: If response timeout occurs
        """
        try:
            await self.send_json_message(
                "csm",
                {
                    "SID": source_id,
                    "TX": tx,
                    "TY": ty,
                    "SC": spies_nr,
                    "ST": 0,  # Spy mission type
                    "SE": precision,
                    "HBW": horses_type,
                    "KID": kingdom,
                    "PTT": feathers,
                    "SD": slowdown
                }
            )
            
            if sync:
                response = await self.wait_for_response("csm")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for spy response")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during spy mission: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in send_spy: {e}")
            return False
        
    async def send_sabotage(
        self,
        kingdom: int,
        source_id: int,
        tx: int,
        ty: int,
        spies_nr: int,
        burn_percent: int = 50,
        horses_type: int = 0,
        feathers: int = 0,
        slowdown: int = 0,
        sync: bool = True   
    ) -> Union[Dict, bool]:
        """
        Send spies on a sabotage mission to burn resources.
        
        Args:
            kingdom: Target kingdom ID
            source_id: Source building ID
            tx: Target X coordinate
            ty: Target Y coordinate
            spies_nr: Number of spies to send
            burn_percent: Percentage of resources to burn (0-100)
            horses_type: Type of horses to use
            feathers: Feathers bonus
            slowdown: Slowdown factor
            sync: Whether to wait for response
            
        Returns:
            Response dictionary if sync=True, otherwise True on success
            
        Raises:
            ConnectionError: If connection is lost during operation
            TimeoutError: If response timeout occurs
        """
        try:
            await self.send_json_message(
                "csm",
                {
                    "SID": source_id,
                    "TX": tx,
                    "TY": ty,
                    "SC": spies_nr,
                    "ST": 2,  # Sabotage mission type
                    "SE": burn_percent,
                    "HBW": horses_type,
                    "KID": kingdom,
                    "PTT": feathers,
                    "SD": slowdown
                }
            )
            
            if sync:
                response = await self.wait_for_response("csm")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for sabotage response")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during sabotage: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in send_sabotage: {e}")
            return False
        
    async def get_spy_info(
        self,
        kingdom: int,
        tx: int,
        ty: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Retrieve spy information for a specific location.
        
        Args:
            kingdom: Target kingdom ID
            tx: Target X coordinate
            ty: Target Y coordinate
            sync: Whether to wait for response
            
        Returns:
            Spy information dictionary if sync=True, otherwise True on success
            
        Raises:
            ConnectionError: If connection is lost during operation
            TimeoutError: If response timeout occurs
        """
        try:
            await self.send_json_message(
                "ssi",
                {
                    "TX": tx,
                    "TY": ty,
                    "KID": kingdom
                }
            )
            
            if sync:
                response = await self.wait_for_response("ssi")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for spy info response")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error while getting spy info: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in get_spy_info: {e}")
            return False
    
