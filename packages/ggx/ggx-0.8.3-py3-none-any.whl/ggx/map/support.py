from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, List, Union


class Support(GameClient):
    """
    Support module for handling support-related operations in the game.
    Provides functionality for sending support troops to other players
    and retrieving support information between castles.
    """
    
    async def get_support_info(
        self,
        sx: int,
        sy: int,
        tx: int,
        ty: int,
        sync: bool = True 
    ) -> Union[Dict, bool]:
        """
        Get detailed information about support between two castles.
        
        Args:
            sx: Source castle X coordinate
            sy: Source castle Y coordinate
            tx: Target castle X coordinate
            ty: Target castle Y coordinate
            sync: Whether to wait for server response
            
        Returns:
            Union[Dict, bool]: Support information data if sync=True, 
                             otherwise True if request sent successfully
            
        Example:
            >>> support_info = await support.get_support_info(100, 200, 150, 250)
            >>> print(support_info)
        """
        try:
            await self.send_json_message(
                "sdi",
                {
                    "TX": tx,
                    "TY": ty,
                    "SX": sx,
                    "SY": sy
                }
            )
            
            if sync:
                response = await self.wait_for_response("sdi")
                return response
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting support info from ({sx}, {sy}) to ({tx}, {ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during support info: {e}")
            return False
        except Exception as e:
            logger.error(f"Error getting support info from ({sx}, {sy}) to ({tx}, {ty}): {e}")
            return False
        
    async def send_support(
        self,
        units: List[int],
        sender_id: int,
        tx: int,
        ty: int,
        lord_id: int,
        camp_time: int = 12,
        horses_type: int = -1,
        feathers: int = 0,
        slowdown: int = 0,
        sync: bool = True 
    ) -> Union[Dict, bool]:
        """
        Send support troops to another castle.
        
        Args:
            units: List of unit counts to send as support
            sender_id: ID of the sender castle
            tx: Target castle X coordinate
            ty: Target castle Y coordinate
            lord_id: Lord ID to send with the support
            camp_time: Camp time in hours (default: 12)
            horses_type: Horses type for the support (default: -1 for auto)
            feathers: Number of feathers to include (default: 0)
            slowdown: Slowdown factor for the march (default: 0)
            sync: Whether to wait for server response
            
        Returns:
            Union[Dict, bool]: Support sending result if sync=True, 
                             otherwise True if request sent successfully
            
        Example:
            >>> units = [[10, 5], [217, 200]] 
            >>> result = await support.send_support(
            ...     units=units,
            ...     sender_id=12345,
            ...     tx=150,
            ...     ty=250,
            ...     lord_id=6
            ... )
        """
        try:
            await self.send_json_message(
                "cds",
                {
                    "SID": sender_id,
                    "TX": tx,
                    "TY": ty,
                    "LID": lord_id,
                    "WT": camp_time,
                    "HBW": horses_type,
                    "BPC": 0,
                    "PTT": feathers,
                    "SD": slowdown,
                    "A": units
                }
            )
            
            if sync:
                response = await self.wait_for_response("cds")
                return response
            return True
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout sending support from castle {sender_id} to ({tx}, {ty})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error during support: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending support from castle {sender_id} to ({tx}, {ty}): {e}")
            return False

 

    async def batch_send_support(
        self,
        support_requests: List[Dict],
        delay: float = 1.0
    ) -> List[Dict]:
        """
        Send multiple support requests in sequence with delays.
        
        Args:
            support_requests: List of support request dictionaries, each containing:
                - units: List of unit counts
                - sender_id: Sender castle ID
                - tx: Target X coordinate
                - ty: Target Y coordinate
                - lord_id: Lord ID
            delay: Delay between support sends in seconds
            
        Returns:
            List[Dict]: List of results for each support request
        """
        results = []
        
        for i, request in enumerate(support_requests):
            try:
                logger.info(f"Sending support request {i+1}/{len(support_requests)}")
                
                result = await self.send_support(
                    units=request["units"],
                    sender_id=request["sender_id"],
                    tx=request["tx"],
                    ty=request["ty"],
                    lord_id=request["lord_id"],
                    camp_time=request.get("camp_time", 12),
                    horses_type=request.get("horses_type", -1),
                    feathers=request.get("feathers", 0),
                    slowdown=request.get("slowdown", 0),
                    sync=True
                )
                
                results.append({
                    "request_index": i,
                    "success": isinstance(result, dict),
                    "data": result
                })
                
                # Add delay between requests to avoid rate limiting
                if delay > 0 and i < len(support_requests) - 1:
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error in batch support request {i+1}: {e}")
                results.append({
                    "request_index": i,
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        logger.info(f"Batch support sending completed: {success_count}/{len(support_requests)} successful")
        return results

