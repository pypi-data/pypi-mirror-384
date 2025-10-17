from ..client.game_client import GameClient
from ..utils.utils import Utils
from loguru import logger
import asyncio
from typing import Dict, Union, Any, List, Optional


class Castle(GameClient):
    """
    Castle management module for handling castle operations and kingdom transfers.
    
    Provides functionality for managing castles, resources, units, and automated
    kingdom transfer operations including resource feeding and unit replenishment.
    """
    
    async def get_castles(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve basic castle information for the account.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Castles data dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("gcl", {})
            
            if sync:
                response = await self.wait_for_response("gcl")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving castles information")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving castles: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving castles: {e}")
            return False
        
    async def get_detailed_castles(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve detailed castle information including inventory and resources.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Detailed castles data dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("dcl", {})
            
            if sync:
                response = await self.wait_for_response("dcl")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving detailed castles information")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving detailed castles: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving detailed castles: {e}")
            return False
        
    async def relocate_main_castle(
        self,
        x: int,
        y: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Relocate the main castle to new coordinates.
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            sync: Whether to wait for server response
            
        Returns:
            Relocation result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("rst", {"PX": x, "PY": y})
            
            if sync:
                response = await self.wait_for_response("rst")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while relocating main castle to ({x}, {y})")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while relocating main castle: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error relocating main castle: {e}")
            return False
                
    async def go_to_castle(
        self,
        kingdom: int,
        castle_id: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Navigate to a specific castle.
        
        Args:
            kingdom: Kingdom ID of the castle
            castle_id: Castle ID to navigate to
            sync: Whether to wait for server response
            
        Returns:
            Navigation result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("jca", {"CID": castle_id, "KID": kingdom})
            
            if sync:
                response = await self.wait_for_response("jaa")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while navigating to castle {castle_id} in kingdom {kingdom}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while navigating to castle: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error navigating to castle: {e}")
            return False
    
    async def rename_castle(
        self,
        kingdom: int,
        castle_id: int,
        castle_type: int,
        name: str,
        paid: int = 0,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Rename a castle.
        
        Args:
            kingdom: Kingdom ID of the castle
            castle_id: Castle ID to rename
            castle_type: Type of the castle
            name: New name for the castle
            paid: Payment flag (0 for free, 1 for paid)
            sync: Whether to wait for server response
            
        Returns:
            Rename result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "arc",
                {
                    "CID": castle_id,
                    "P": paid,
                    "KID": kingdom,
                    "AT": castle_type,
                    "N": name
                }
            )
            
            if sync:
                response = await self.wait_for_response("arc")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while renaming castle {castle_id}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while renaming castle: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error renaming castle: {e}")
            return False
        
    async def get_castle_resources(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve castle resources information.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Resources data dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("grc", {})
            
            if sync:
                response = await self.wait_for_response("grc")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving castle resources")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving castle resources: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving castle resources: {e}")
            return False
    
    async def get_castle_production(self, sync: bool = True) -> Union[Dict[str, Any], bool]:
        """
        Retrieve castle production information.
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Production data dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message("gpa", {})
            
            if sync:
                response = await self.wait_for_response("gpa")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error("Timeout while retrieving castle production")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while retrieving castle production: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error retrieving castle production: {e}")
            return False
    
    async def send_resources_to_kingdom(
        self,
        id_sender: int,
        sender_kid: int,
        target_kid: int,
        resources: List[List[Union[str, int]]],
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Send resources from one kingdom to another.
        
        Args:
            id_sender: Sender castle ID
            sender_kid: Sender kingdom ID
            target_kid: Target kingdom ID
            resources: List of [resource_type, amount] pairs
            sync: Whether to wait for server response
            
        Returns:
            Transfer result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "kgt",
                {
                   "SCID": id_sender,
                   "SKID": sender_kid,
                   "TKID": target_kid,
                   "G": resources
                }
            )
            
            if sync:
                response = await self.wait_for_response("kgt")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while sending resources from K{sender_kid} to K{target_kid}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while sending resources: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending resources: {e}")
            return False
        
    async def send_units_to_kingdom(
        self,
        id_sender: int,
        sender_kid: int,
        target_kid: int,
        units: List[List[int]],
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Send units from one kingdom to another.
        
        Args:
            id_sender: Sender castle ID
            sender_kid: Sender kingdom ID
            target_kid: Target kingdom ID
            units: List of [unit_type, amount] pairs
            sync: Whether to wait for server response
            
        Returns:
            Transfer result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "kut",
                {
                   "SCID": id_sender,
                   "SKID": sender_kid,
                   "TKID": target_kid,
                   "CID": -1,
                   "A": units
                }
            )
            
            if sync:
                response = await self.wait_for_response("kut")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while sending units from K{sender_kid} to K{target_kid}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while sending units: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending units: {e}")
            return False
        
    async def skip_kingdom_transfer(
        self,
        skip: str,
        target_kid: int,
        transfer_type: int,
        sync: bool = True
    ) -> Union[Dict[str, Any], bool]:
        """
        Skip kingdom transfer cooldown using time skip items.
        
        Args:
            skip: Time skip item identifier
            target_kid: Target kingdom ID
            transfer_type: Type of transfer (1 for units, 2 for resources)
            sync: Whether to wait for server response
            
        Returns:
            Skip result dictionary if sync=True,
            True if request sent successfully with sync=False,
            False on error
            
        Raises:
            asyncio.TimeoutError: If response timeout occurs
            ConnectionError: If connection is lost during operation
        """
        try:
            await self.send_json_message(
                "msk",
                {
                    "MST": skip,
                    "KID": target_kid,
                    "TT": transfer_type
                }
            )
            
            if sync:
                response = await self.wait_for_response("msk")
                return response
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while skipping transfer to K{target_kid}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection lost while skipping transfer: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error skipping transfer: {e}")
            return False
        
    async def auto_units_kingdom_transfer(
        self,
        id_sender: int,
        sender_kid: int,
        target_kid: int,
        units: List[Any],
        skips: Optional[List[str]] = None,
        sync: bool = True  
    ) -> bool:
        """
        Automatically send units to another kingdom with cooldown skipping.
        
        Args:
            id_sender: Sender castle ID
            sender_kid: Sender kingdom ID
            target_kid: Target kingdom ID
            units: List of units to send
            skips: Available time skip items
            sync: Whether to wait for server responses
            
        Returns:
            True if successful, False otherwise
        """
        try:
            utils = Utils()
            send_units = await self.send_units_to_kingdom(id_sender, sender_kid, target_kid, units)
            if not isinstance(send_units, dict):
                logger.error(f"Failed to send units to kingdom: {target_kid}")
                return False
            
            kpi = send_units.get("kpi", {})
            ut_list = kpi.get("UT")
            if not ut_list or not isinstance(ut_list, list):
                logger.error("Unknown transfer time data!")
                return False
            
            time_to_transfer = ut_list[0].get("RS")
            if not isinstance(time_to_transfer, int):
                logger.error(f"Invalid time value: {ut_list[0]}")
                return False
            
            skip_list = utils.skip_calculator(time_to_transfer, skips)
            for skip in skip_list:
                await self.skip_kingdom_transfer(skip, target_kid, transfer_type=1, sync=sync)
            
            logger.info(f"All units has been sent successfully to kingdom {target_kid}!")
            return True
            
        except Exception as e:
            logger.error(f"Error in auto units kingdom transfer: {e}")
            return False
        
    async def auto_res_kingdom_transfer(
        self,
        id_sender: int,
        sender_kid: int,
        target_kid: int,
        resources: List[Any],
        skips: Optional[List[str]] = None,
        sync: bool = True  
    ) -> bool:
        """
        Automatically send resources to another kingdom with cooldown skipping.
        
        Args:
            id_sender: Sender castle ID
            sender_kid: Sender kingdom ID
            target_kid: Target kingdom ID
            resources: List of resources to send
            skips: Available time skip items
            sync: Whether to wait for server responses
            
        Returns:
            True if successful, False otherwise
        """
        try:
            utils = Utils()
            resources_sender = await self.send_resources_to_kingdom(id_sender, sender_kid, target_kid, resources)
            if not isinstance(resources_sender, dict):
                logger.error(f"Failed to send resources to kingdom: {target_kid}")
                return False
            
            kpi = resources_sender.get("kpi", {})
            rt_list = kpi.get("RT")
            if not rt_list or not isinstance(rt_list, list):
                logger.error("Unknown transfer time data!")
                return False
            
            time_to_transfer = rt_list[0].get("RS")
            if not isinstance(time_to_transfer, int):
                logger.error(f"Invalid time value: {rt_list[0]}")
                return False

            skip_list = utils.skip_calculator(time_to_transfer, skips)
            for skip in skip_list:
                await self.skip_kingdom_transfer(skip, target_kid, transfer_type=2, sync=sync)
            
            logger.info(f"All resources has been sent successfully to kingdom {target_kid}!")    
            return True
            
        except Exception as e:
            logger.error(f"Error in auto resources kingdom transfer: {e}")
            return False

    async def units_replenish(
        self,
        target_kid: int,
        wod_id: int,
        amount: int
    ) -> bool:
        """
        Replenish units in a target kingdom from donor kingdoms.
        
        Args:
            target_kid: Target kingdom ID to replenish
            wod_id: Unit type ID to replenish
            amount: Amount of units needed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account_inventory = await self.get_detailed_castles()
            inventory_data = account_inventory["C"]
            donors = []
            
            for kingdom in inventory_data:
                kid = kingdom.get("KID")
                if kid == target_kid:
                    continue
                
                for ai_block in kingdom.get("AI", []):
                    aid = ai_block.get("AID")
                    for wod, amt in ai_block.get("AC", []):
                        if wod == wod_id and amt > amount:
                            donors.append({"aid": aid, "kid": kid, "amount": amt})
                            break
                        
            if not donors:
                logger.warning("I can't find any eligible location!")
                return False
                            
            else:
                best = max(donors, key=lambda d: d["amount"])
                donor_aid = best["aid"]
                donor_amt = best["amount"]
                donor_kid = best["kid"]
                send_amt = min(donor_amt, amount)
                
                success = await self.auto_units_kingdom_transfer(donor_aid, donor_kid, target_kid, [[wod_id, send_amt]])
                if success:
                    logger.info(f"Kingdom {target_kid} refilled with {send_amt} units!")
                    return True
                return False
                     
        except Exception as e:
            logger.error(f"Error in units replenish: {e}")
            return False
        
    async def kingdom_auto_feeder(
        self,
        target_kid: int,
        min_food: int,
        min_mead: int,
        skips: Optional[List[str]] = None,
        interval: float = 60.0,
        max_transfers: int = 3,
        sync: bool = True,
        stop_event: Optional[asyncio.Event] = None,
        min_donor_stock_food: int = 100_000,
        min_donor_stock_mead: int = 100_000,
    ) -> None:
        """
        Automatically feed resources to a target kingdom from donor kingdoms.
        
        Args:
            target_kid: Target kingdom ID to feed
            min_food: Minimum food threshold
            min_mead: Minimum mead threshold
            skips: Available time skip items
            interval: Check interval in seconds
            max_transfers: Maximum transfers per check
            sync: Whether to wait for server responses
            stop_event: Event to stop the feeding loop
            min_donor_stock_food: Minimum food stock in donors
            min_donor_stock_mead: Minimum mead stock in donors
        """
        if stop_event is None:
            stop_event = asyncio.Event()

        while not stop_event.is_set():
            try:
                castles_inventory = await self.get_detailed_castles(sync=sync)
                resource_inventory = castles_inventory["C"]
                targets = [k for k in resource_inventory if k.get("KID") == target_kid]
                
                best_food_by_kid = {}
                best_mead_by_kid = {}
                
                for k in resource_inventory:
                    kid = k.get("KID")
                    if kid == target_kid:
                        continue
                    
                    for ai in k.get("AI", []):
                        aid = ai.get("AID")
                        gpa = ai.get("gpa", {}) or {}
                        food_val = int(ai.get("F", 0))
                        mead_val = int(ai.get("MEAD", 0))
                        food_prod = int(gpa.get("DF", 0))
                        mead_prod = int(gpa.get("DMEAD", 0))
                    
                        af = max(0, food_val - int(min_donor_stock_food)) if food_prod > 0 else 0
                        am = max(0, mead_val - int(min_donor_stock_mead)) if mead_prod > 0 else 0
                    
                        if af > 0:
                            cur = best_food_by_kid.get(kid)
                            if cur is None or af > cur["af"]:
                                best_food_by_kid[kid] = {"aid": aid, "af": af}
                            
                        if am > 0:
                            cur = best_mead_by_kid.get(kid)
                            if cur is None or am > cur["am"]:
                                best_mead_by_kid[kid] = {"aid": aid, "am": am}
                
                donors_food = sorted(
                    [(kid, d["aid"], d["af"]) for kid, d in best_food_by_kid.items()],
                    key=lambda t: t[2],
                    reverse=True
                )
                
                donors_mead = sorted(
                    [(kid, d["aid"], d["am"]) for kid, d in best_mead_by_kid.items()],
                    key=lambda t: t[2],
                    reverse=True
                )
                
                for t in targets:
                    kid = t.get("KID")
                    for ai in t.get("AI", []):
                        gpa = ai.get("gpa", {}) or {}
                        food_val = int(ai.get("F", 0))
                        mead_val = int(ai.get("MEAD", 0))
                        food_cap = int(gpa.get("MRF", 0))
                        mead_cap = int(gpa.get("MRMEAD", 0))
                        food_prod = int(gpa.get("DF", 0))
                        mead_prod = int(gpa.get("DMEAD", 0))
                        
                        food_deficit = max(0, (food_cap - 5) - food_val) if food_cap > 0 else 0
                        mead_deficit = max(0, (mead_cap - 5) - mead_val) if mead_cap > 0 else 0
                        need_food = (food_deficit > 0) and ((food_prod < 0) and (food_val < int(min_food)))
                        need_mead = (mead_deficit > 0) and ((mead_prod < 0) and (mead_val < int(min_mead)))
                        
                        # ——— FOOD ———
                        if need_food:
                            remaining = food_deficit
                            transfers_done = 0
                            for i, (dkid, daid, af) in enumerate(donors_food):
                                if remaining <= 0 or transfers_done >= max_transfers:
                                    break
                                if af <= 0:
                                    continue
                                send_amt = min(remaining, af)
                                try:
                                    success = await self.auto_res_kingdom_transfer(
                                        daid, dkid, kid, [["F", int(send_amt)]], skips, sync
                                    )
                                    if success:
                                        remaining -= int(send_amt)
                                        transfers_done += 1
                                        donors_food[i] = (dkid, daid, af - int(send_amt))
                                except Exception as e:
                                    logger.error(f"[FOOD] transfer error {dkid}:{daid} -> {kid}: {e}")
                            logger.success(f"[FOOD] filled {food_deficit - remaining} / {food_deficit} towards KID {kid}")
                        
                        # ——— MEAD ———
                        if need_mead:
                            remaining = mead_deficit
                            transfers_done = 0
                            for i, (dkid, daid, am) in enumerate(donors_mead):
                                if remaining <= 0 or transfers_done >= max_transfers:
                                    break
                                if am <= 0:
                                    continue
                                send_amt = min(remaining, am)
                                try:
                                    success = await self.auto_res_kingdom_transfer(
                                        daid, dkid, kid, [["MEAD", int(send_amt)]], skips, sync
                                    )
                                    if success:
                                        remaining -= int(send_amt)
                                        transfers_done += 1
                                        donors_mead[i] = (dkid, daid, am - int(send_amt))
                                except Exception as e:
                                    logger.error(f"[MEAD] transfer error {dkid}:{daid} -> {kid}: {e}")
                            
                            logger.success(f"[MEAD] filled {mead_deficit - remaining} / {mead_deficit} towards KID {kid}")
                            
            except asyncio.TimeoutError:
                logger.warning("Timeout occurred. Retry!")
            except ConnectionError as e:
                logger.error(f"Connection lost during kingdom auto feeder: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error in kingdom auto feeder: {e}")
            
            await asyncio.sleep(interval)