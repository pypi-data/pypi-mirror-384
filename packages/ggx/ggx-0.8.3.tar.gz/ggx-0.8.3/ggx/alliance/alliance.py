from ..client.game_client import GameClient
from loguru import logger
import asyncio
from typing import Dict, Union, Any, List, Optional


class Alliance(GameClient):
    """
    Alliance module for handling alliance-related operations.
    
    Provides functionality for alliance management, chat, member operations, and announcements.
    """
    
    async def get_chat(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve alliance chat messages.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Chat data dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("acl", {})
            
            if sync:
                response = await self.wait_for_response("acl")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving alliance chat")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving alliance chat: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving alliance chat: {e}")
            return False
    
    async def write_on_chat(
        self,
        message: str,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Write a message in the alliance chat.
        
        Args:
            message: The message to send
            sync: Whether to wait for server response
            
        Returns:
            Send result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "acm",
                {
                    "M": message
                }
            )
            
            if sync:
                response = await self.wait_for_response("acm")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while writing to alliance chat")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while writing to alliance chat: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error writing to alliance chat: {e}")
            return False
        
    async def help_alliance_member(
        self, 
        kingdom: int, 
        help_id: int, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Help a specific alliance member.
        
        Args:
            kingdom: Kingdom ID of the member to help
            help_id: Help request ID
            sync: Whether to wait for server response
            
        Returns:
            Help result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("ahc", {"LID": help_id, "KID": kingdom})
            
            if sync:
                response = await self.wait_for_response("ahc")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while helping alliance member {help_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while helping alliance member: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error helping alliance member: {e}")
            return False
    
    async def help_alliance_all(
        self, 
        kingdom: int, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Help all alliance members in a kingdom.
        
        Args:
            kingdom: Kingdom ID to help all members in
            sync: Whether to wait for server response
            
        Returns:
            Help result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("aha", {"KID": kingdom})
            
            if sync:
                response = await self.wait_for_response("aha")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while helping all alliance members in kingdom {kingdom}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while helping all alliance members: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error helping all alliance members: {e}")
            return False
    
    async def invite_player(
        self,
        user_id: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Invite a player to the alliance.
        
        Args:
            user_id: ID of the player to invite
            sync: Whether to wait for server response
            
        Returns:
            Invite result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "aip",
                {
                    "SV": user_id
                }
            )
            
            if sync:
                response = await self.wait_for_response("aip")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while inviting player {user_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while inviting player: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error inviting player: {e}")
            return False
    
    async def rank_player(
        self,
        account_id: int,
        rank: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Change a player's rank in the alliance.
        
        Args:
            account_id: Account ID of the player
            rank: New rank (0-8, where 0 is leader)
            sync: Whether to wait for server response
            
        Returns:
            Rank change result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "arm",
                {
                    "PID": account_id,
                    "R": rank
                }  
            )
            
            if sync:
                response = await self.wait_for_response("arm")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while changing rank for player {account_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while changing player rank: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error changing player rank: {e}")
            return False
    
    async def mass_message(
        self,
        text: str,
        title: Optional[str] = None,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Send a mass message to alliance members.
        
        Args:
            text: Message text
            title: Message title (optional)
            sync: Whether to wait for server response
            
        Returns:
            Message send result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "anl",
                {
                    "SJ": title,
                    "TXT": text
                }
            )
            
            if sync:
                response = await self.wait_for_response("anl")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while sending mass message")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while sending mass message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending mass message: {e}")
            return False
    
    async def leave_alliance(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Leave the current alliance.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Leave result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("aqi", {})
            
            if sync:
                response = await self.wait_for_response("aqi")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while leaving alliance")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while leaving alliance: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error leaving alliance: {e}")
            return False
    
    async def kickout_player(
        self,
        account_id: int,   
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Kick a player from the alliance.
        
        Args:
            account_id: Account ID of the player to kick
            sync: Whether to wait for server response
            
        Returns:
            Kick result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "akm",
                {
                    "PID": account_id
                }  
            )
            
            if sync:
                response = await self.wait_for_response("akm")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while kicking player {account_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while kicking player: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error kicking player: {e}")
            return False
    
    async def create_alliance(
        self,
        alliance_name: str,
        alliance_state: int,
        description: str,
        lang: str,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Create a new alliance.
        
        Args:
            alliance_name: Name of the new alliance
            alliance_state: Alliance state/type
            description: Alliance description
            lang: Alliance language
            sync: Whether to wait for server response
            
        Returns:
            Creation result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "afo",
                {
                    "PO": -1,
                    "PWR": 0,
                    "IA": alliance_state,
                    "N": alliance_name,
                    "D": description,
                    "ALL": lang
                }
            )
            
            if sync:
                response = await self.wait_for_response("afo")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while creating alliance {alliance_name}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while creating alliance: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating alliance: {e}")
            return False
    
    async def alliance_info(
        self,
        alliance_id: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Get information about a specific alliance.
        
        Args:
            alliance_id: ID of the alliance to query
            sync: Whether to wait for server response
            
        Returns:
            Alliance info dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("ain", {"AID": alliance_id})
            
            if sync:
                response = await self.wait_for_response("ain")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while getting alliance info {alliance_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while getting alliance info: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error getting alliance info: {e}")
            return False
    
    async def get_alliance(
        self,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Get current alliance information.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Alliance data dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("all", {})
            
            if sync:
                response = await self.wait_for_response("all")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while getting current alliance")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while getting current alliance: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error getting current alliance: {e}")
            return False
    
    async def get_alliance_discussions_panel(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Get alliance discussions panel.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Discussions panel data if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("gat", {})
            
            if sync:
                response = await self.wait_for_response("gat")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while getting alliance discussions panel")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while getting alliance discussions panel: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error getting alliance discussions panel: {e}")
            return False
    
    async def post_alliance_announce(
        self,
        announce_text: str, 
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Post an alliance announcement.
        
        Args:
            announce_text: Text of the announcement
            sync: Whether to wait for server response
            
        Returns:
            Announcement result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "acd",
                {
                    "T": 0,
                    "TXT": announce_text
                }
            )
            
            if sync:
                response = await self.wait_for_response("gat")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while posting alliance announcement")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while posting alliance announcement: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error posting alliance announcement: {e}")
            return False
    
    async def postin_alliance_discussions_panel(
        self,
        title: str,
        text: str,
        rank_list: List[int] = [0, 1, 2],
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Post in alliance discussions panel.
        
        Args:
            title: Post title
            text: Post content
            rank_list: List of ranks that can view the post
            sync: Whether to wait for server response
            
        Returns:
            Post result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "atc",
                {
                    "N": title,
                    "RG": rank_list,
                    "R": text
                }
            )
            
            if sync:
                response = await self.wait_for_response("gat")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while posting in alliance discussions panel")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while posting in alliance discussions panel: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error posting in alliance discussions panel: {e}")
            return False
    
    async def get_online_members(self) -> List[int]:
        """
        Get list of online alliance members.
        
        Returns:
            List of online member account IDs
        """
        try:
            get_all = await self.get_alliance()
            alliance_id = get_all.get("AID", None)
            main_all_info = await self.alliance_info(alliance_id=alliance_id)
            
            all_resp = main_all_info.get("A", {})
            user_data = all_resp.get("AMI", {})
            online_members = [member[0] for member in user_data if member[4] == 0]
            
            return online_members
            
        except Exception as e:
            logger.error(f"Error getting online alliance members: {e}")
            return []
    
    async def accept_alliance_invite(
        self,
        invite_id: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Accept an alliance invitation.
        
        Args:
            invite_id: Invitation ID to accept
            sync: Whether to wait for server response
            
        Returns:
            Acceptance result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "aai",
                {
                    "MID": invite_id,
                    "D": 1
                }
            )
            
            if sync:
                response = await self.wait_for_response("aai")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while accepting alliance invite {invite_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while accepting alliance invite: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error accepting alliance invite: {e}")
            return False