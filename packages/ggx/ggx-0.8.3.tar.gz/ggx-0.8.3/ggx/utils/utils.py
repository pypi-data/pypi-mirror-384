from loguru import logger
import asyncio
import aiohttp
from typing import List, Optional, Tuple, Dict, Any


class Utils:
    """
    Utility class providing common functionality for CAPTCHA solving and time calculations.
    
    Provides methods for reCAPTCHA token retrieval and time skip calculations
    for various game operations.
    """
    
    API_IN_URL = "http://2captcha.com/in.php"
    API_RES_URL = "http://2captcha.com/res.php"
    
    def __init__(self):
        """
        Initialize Utils with default configuration for CAPTCHA solving.
        """
        self.polling_interval = 5
        self.max_attempts = 20
        self.site_key = '6Lc7w34oAAAAAFKhfmln41m96VQm4MNqEdpCYm-k'
        self.site_url = 'https://empire.goodgamestudios.com/'
    
    async def get_recaptcha_token(self, api_key: str) -> str:
        """
        Retrieve reCAPTCHA token using 2Captcha service.
        
        Args:
            api_key: 2Captcha API key
            
        Returns:
            reCAPTCHA token string
            
        Raises:
            RuntimeError: If CAPTCHA submission or retrieval fails
            TimeoutError: If CAPTCHA solving times out
            ConnectionError: If network connection fails
        """
        payload = {
            'key': api_key,
            'method': 'userrecaptcha',
            'googlekey': self.site_key,
            'pageurl': self.site_url,
            'json': 1
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Submit CAPTCHA to 2Captcha
                async with session.post(self.API_IN_URL, data=payload) as resp:
                    if resp.status != 200:
                        raise ConnectionError(f"2Captcha API returned status {resp.status}")
                    
                    data = await resp.json()
                    if data.get('status') != 1:
                        logger.error(f"2Captcha submission error: {data}")
                        raise RuntimeError(f"Submit failed: {data.get('request')}")

                    request_id = data.get('request')
                    logger.info(f"Submitted CAPTCHA, request ID: {request_id}")

                # Poll for CAPTCHA solution
                for attempt in range(self.max_attempts):
                    await asyncio.sleep(self.polling_interval)
                    params = {
                        'key': api_key,
                        'action': 'get',
                        'id': request_id,
                        'json': 1
                    }
                    
                    async with session.get(self.API_RES_URL, params=params) as res:
                        if res.status != 200:
                            logger.warning(f"2Captcha API returned status {res.status}, retrying...")
                            continue
                            
                        result = await res.json()
                        if result.get('status') == 1:
                            token = result.get('request')
                            logger.info("Successfully retrieved token from 2Captcha")
                            return token
                        elif result.get('request') == 'CAPCHA_NOT_READY':
                            logger.debug(f"Attempt {attempt+1}/{self.max_attempts}: CAPTCHA not ready")
                            continue
                        else:
                            logger.error(f"2Captcha retrieval error: {result}")
                            raise RuntimeError(f"Get failed: {result.get('request')}")

                raise TimeoutError("2Captcha solving timed out")
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during CAPTCHA solving: {e}")
            raise ConnectionError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during CAPTCHA solving: {e}")
            raise
    
    def skip_calculator(
        self,
        time: int,
        skip_type: Optional[List[str]] = None
    ) -> List[str]:
        """
        Calculate optimal time skip combinations for a given time duration.
        
        Args:
            time: Time in seconds to skip
            skip_type: List of allowed skip types. If None, all types are allowed.
                     Available types: ["MS1", "MS2", "MS3", "MS4", "MS5", "MS6", "MS7"]
            
        Returns:
            List of skip labels in optimal order
            
        Raises:
            ValueError: If no valid skip types are available
        """
        try:
            # All available skip values: (seconds, label)
            all_skip_values = [
                (86400, "MS7"),  # 24 hours
                (18000, "MS6"),  # 5 hours
                (3600, "MS5"),   # 1 hour
                (1800, "MS4"),   # 30 minutes
                (600, "MS3"),    # 10 minutes
                (300, "MS2"),    # 5 minutes
                (60, "MS1")      # 1 minute
            ]
            
            # Filter skip values based on allowed types
            if skip_type:
                skip_values = [(sec, lbl) for sec, lbl in all_skip_values if lbl in skip_type]
                if not skip_values:
                    logger.error("No valid skip types provided or available")
                    raise ValueError("Your skips are not allowed or invalid!")
            else:
                skip_values = all_skip_values
            
            # Convert time to minutes for dynamic programming
            minutes = time // 60
            skip_minutes = [(sec // 60, label) for sec, label in skip_values]
            
            # Dynamic programming to find optimal skip combination
            INF = float('inf')
            dp = [INF] * (minutes + 1)
            prev = [None] * (minutes + 1)
            dp[0] = 0
            
            for i in range(1, minutes + 1):
                for m, label in skip_minutes:
                    if i >= m and dp[i - m] + 1 < dp[i]:
                        dp[i] = dp[i - m] + 1
                        prev[i] = (i - m, label)
            
            # Reconstruct skip sequence
            skips = []
            cur = minutes
            while cur > 0 and prev[cur]:
                j, label = prev[cur]
                skips.append(label)
                cur = j
            
            # Calculate remaining time and add final skip if needed
            used = sum(sec * skips.count(lbl) for sec, lbl in all_skip_values)
            rem = time - used
            
            if rem > 0:
                # Find smallest skip that covers remaining time
                for sec, label in sorted(all_skip_values, key=lambda x: x[0]):
                    if sec >= rem:
                        skips.append(label)
                        break
            
            logger.debug(f"Calculated {len(skips)} skips for {time} seconds: {skips}")
            return skips
            
        except Exception as e:
            logger.error(f"Error in skip calculator: {e}")
            # Return fallback - use largest available skip
            if skip_type:
                available_skips = [lbl for sec, lbl in all_skip_values if lbl in skip_type]
            else:
                available_skips = [lbl for sec, lbl in all_skip_values]
            
            if available_skips:
                return [available_skips[0]]  # Use first available skip as fallback
            else:
                logger.error("No skip types available for fallback")
                return []