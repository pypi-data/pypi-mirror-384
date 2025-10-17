from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union, Any, List


class Defense(GameClient):
    """
    Defense management module for handling castle defense configurations.
    
    Provides functionality for retrieving and modifying castle defense settings
    including keep, wall, and moat defenses with various tools and unit configurations.
    """
    
    async def get_castle_defense(
        self, 
        x: int, 
        y: int, 
        castle_id: int, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Retrieve current defense configuration for a castle.
        
        Args:
            x: Castle X coordinate
            y: Castle Y coordinate
            castle_id: Castle ID to check defenses for
            sync: Whether to wait for server response
            
        Returns:
            Defense configuration dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "dfc", {"CX": x, "CY": y, "AID": castle_id, "KID": -1, "SSV": 0}
            )
            
            if sync:
                response = await self.wait_for_response("dfc")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while retrieving defense for castle {castle_id} at ({x}, {y})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving castle defense: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving castle defense: {e}")
            return False
            
    async def change_keep_defense(
        self,
        x: int,
        y: int,
        castle_id: int,
        min_units_to_consume_tools: int,
        melee_percentage: int,
        tools: List[List[int]],
        support_tools: List[List[int]],
        sync: bool = True   
    ) -> Union[Dict[str, Any], bool]:
        """
        Change the keep defense configuration for a castle.
        
        Args:
            x: Castle X coordinate
            y: Castle Y coordinate
            castle_id: Castle ID to modify
            min_units_to_consume_tools: Minimum units required to consume tools
            melee_percentage: Percentage of melee units to deploy
            tools: List of tool configurations [tool_id, amount]
            support_tools: List of support tool configurations [tool_id, amount]
            sync: Whether to wait for server response
            
        Returns:
            Defense change result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "dfk",
                {
                    "CX": x,
                    "CY": y,
                    "AID": castle_id,
                    "MAUCT": min_units_to_consume_tools,
                    "UC": melee_percentage,
                    "S": tools,
                    "STS": support_tools,
                }
            )
            
            if sync:
                response = await self.wait_for_response("dfk")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while changing keep defense for castle {castle_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while changing keep defense: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error changing keep defense: {e}")
            return False
            
    async def change_wall_defense(
        self,
        x: int,
        y: int,
        castle_id: int,
        left_tools: List[List[int]],
        left_unit_percentage: int,
        left_melee_percentage: int,
        middle_tools: List[List[int]],
        middle_unit_percentage: int,
        middle_melee_percentage: int,
        right_tools: List[List[int]],
        right_unit_percentage: int,
        right_melee_percentage: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Change the wall defense configuration for a castle.
        
        Args:
            x: Castle X coordinate
            y: Castle Y coordinate
            castle_id: Castle ID to modify
            left_tools: Left section tools [tool_id, amount]
            left_unit_percentage: Left section unit deployment percentage
            left_melee_percentage: Left section melee unit percentage
            middle_tools: Middle section tools [tool_id, amount]
            middle_unit_percentage: Middle section unit deployment percentage
            middle_melee_percentage: Middle section melee unit percentage
            right_tools: Right section tools [tool_id, amount]
            right_unit_percentage: Right section unit deployment percentage
            right_melee_percentage: Right section melee unit percentage
            sync: Whether to wait for server response
            
        Returns:
            Defense change result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "dfw",
                {
                    "CX": x,
                    "CY": y,
                    "AID": castle_id,
                    "L": {
                        "S": left_tools,
                        "UP": left_unit_percentage,
                        "UC": left_melee_percentage
                    },
                    "M": {
                        "S": middle_tools,
                        "UP": middle_unit_percentage,
                        "UC": middle_melee_percentage
                    },
                    "R": {
                        "S": right_tools,
                        "UP": right_unit_percentage,
                        "UC": right_melee_percentage,
                    }
                }
            )
            
            if sync:
                response = await self.wait_for_response("dfw")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while changing wall defense for castle {castle_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while changing wall defense: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error changing wall defense: {e}")
            return False
            
    async def change_moat_defense(
        self,
        x: int,
        y: int,
        castle_id: int,
        left_tools: List[List[int]],
        middle_tools: List[List[int]],
        right_tools: List[List[int]],
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Change the moat defense configuration for a castle.
        
        Args:
            x: Castle X coordinate
            y: Castle Y coordinate
            castle_id: Castle ID to modify
            left_tools: Left section tools [tool_id, amount]
            middle_tools: Middle section tools [tool_id, amount]
            right_tools: Right section tools [tool_id, amount]
            sync: Whether to wait for server response
            
        Returns:
            Defense change result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "dfm",
                {
                    "CX": x,
                    "CY": y,
                    "AID": castle_id,
                    "LS": left_tools,
                    "MS": middle_tools,
                    "RS": right_tools
                }
            )
            
            if sync:
                response = await self.wait_for_response("dfm")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while changing moat defense for castle {castle_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while changing moat defense: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error changing moat defense: {e}")
            return False