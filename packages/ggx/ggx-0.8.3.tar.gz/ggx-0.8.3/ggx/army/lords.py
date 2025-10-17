from ..client.game_client import GameClient
from loguru import logger
import random
import asyncio
from typing import Dict, Union, Any, List, Optional


class Lords(GameClient):
    """
    Lords management module for handling lord operations and selection.
    
    Provides functionality for retrieving lord information, listing available lords,
    and selecting optimal lords for various game operations.
    """
    
    async def get_lords(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve all lords information for the account.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Lords data dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("gli", {})
            
            if sync:
                response = await self.wait_for_response("gli")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving lords information")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving lords: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving lords: {e}")
            return False
        
    async def list_lords_id(
        self,
        lord_list: List[int],
    ) -> List[int]:
        """
        Populate a list with IDs of lords that have sufficient equipment.
        
        Args:
            lord_list: List to populate with qualified lord IDs
            
        Returns:
            Updated list of qualified lord IDs
            
        Note:
            Modifies the input list in place and also returns it
        """
        try:
            if not isinstance(lord_list, list):
                lord_list = []
            
            lords_data = await self.get_lords()
            if not isinstance(lords_data, dict):
                logger.error("Failed to retrieve lords data")
                return lord_list
            
            all_lords = lords_data.get("C", [])
            
            for lord_obj in all_lords:
                lord_id = lord_obj.get("ID")
                eq_list = lord_obj.get("EQ", [])
                # Check if lord has at least 5 equipment items
                if len(eq_list) >= 5:
                    lord_list.append(lord_id)
            
            logger.debug(f"Found {len(lord_list)} qualified lords with sufficient equipment")
            return lord_list
            
        except Exception as e:
            logger.error(f"Error listing lords IDs: {e}")
            return lord_list
        
    async def select_lord(
        self,
        user_lords: List[int]
    ) -> Optional[int]:
        """
        Select an available lord that is not currently on a mission.
        
        Args:
            user_lords: List of available lord IDs to choose from
            
        Returns:
            Selected lord ID if available, None if no lords are available
            
        Raises:
            ValueError: If user_lords is not a valid list
        """
        try:
            if not isinstance(user_lords, list):
                logger.error("user_lords must be a list of lord IDs")
                raise ValueError("Add lords list!")
            
            if not user_lords:
                logger.warning("No lords provided for selection")
                return None
            
            # Get account details
            details_response = await self.send_rpc("gcl", {})
            if not isinstance(details_response, dict):
                logger.error("Failed to retrieve account details")
                return None
                
            account_id = details_response.get("PID")
            if not account_id:
                logger.error("Could not determine account ID")
                return None
            
            # Get current movements
            moves_response = await self.send_rpc("gam", {})
            if not isinstance(moves_response, dict):
                logger.error("Failed to retrieve movements data")
                return None
            
            movements = [
                movement for movement in moves_response.get("M", []) 
                if (movement.get("M", {}).get("OID") == account_id and 
                    movement.get("UM") is not None)
            ]
            
            # Extract currently used lords
            used_lords = [
                movement["UM"]["L"].get("ID") for movement in movements 
                if movement["UM"].get("L")
            ]
            
            # Find available lords (not currently on missions)
            available_lords = list(set(user_lords) - set(used_lords))
            
            if available_lords:
                chosen_lord = random.choice(available_lords)
                logger.info(f"Selected available lord ID: {chosen_lord}")
                return chosen_lord
            else:
                logger.warning("All lords are currently on missions!")
                return None
                
        except asyncio.TimeoutError:
            logger.error("Timeout while selecting lord")
            return None
        except ConnectionError as e:
            logger.error(f"Connection lost while selecting lord: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error selecting lord: {e}")
            return None
    
    async def get_available_lords_count(self) -> int:
        """
        Get the count of currently available lords (not on missions).
        
        Returns:
            Number of available lords
        """
        try:
            user_lords = []
            await self.list_lords_id(user_lords)
            
            if not user_lords:
                return 0
            
            available_lord = await self.select_lord(user_lords)
            if available_lord is not None:
                # Count all available lords (simplified approach)
                return len(user_lords) - len([l for l in user_lords if l != available_lord])
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error counting available lords: {e}")
            return 0
    
    async def get_lord_details(self, lord_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific lord.
        
        Args:
            lord_id: ID of the lord to inspect
            
        Returns:
            Lord details dictionary if found, None otherwise
        """
        try:
            lords_data = await self.get_lords()
            if not isinstance(lords_data, dict):
                return None
            
            all_lords = lords_data.get("C", [])
            for lord_obj in all_lords:
                if lord_obj.get("ID") == lord_id:
                    return lord_obj
            
            logger.warning(f"Lord {lord_id} not found in lords data")
            return None
            
        except Exception as e:
            logger.error(f"Error getting lord details for {lord_id}: {e}")
            return None