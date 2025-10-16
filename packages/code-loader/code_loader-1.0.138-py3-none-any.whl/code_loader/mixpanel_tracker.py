"""
Mixpanel tracking utilities for code-loader.
"""
import os
import sys
import getpass
import uuid
from typing import Optional, Dict, Any
import mixpanel  # type: ignore[import]

TRACKING_VERSION = '1'


class MixpanelTracker:
    """Handles Mixpanel event tracking for code-loader."""
    
    def __init__(self, token: str = "0c1710c9656bbfb1056bb46093e23ca1"):
        self.token = token
        self.mp = mixpanel.Mixpanel(token)
        self._user_id: Optional[str] = None
    
    def _get_whoami(self) -> str:
        """Get the current system username (whoami) for device identification.
        
        Returns:
            str: The system username, with fallbacks to environment variables or 'unknown'
        """
        if self._user_id is None:
            try:
                self._user_id = getpass.getuser()
            except Exception:
                # Fallback to environment variables or default
                self._user_id = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
        return self._user_id or 'unknown'
    
       
    def _get_tensorleap_user_id(self) -> Optional[str]:
        """Get the TensorLeap user ID from ~/.tensorleap/user_id if it exists."""
        try:
            user_id_path = os.path.expanduser("~/.tensorleap/user_id")
            if os.path.exists(user_id_path):
                with open(user_id_path, 'r') as f:
                    user_id = f.read().strip()
                    if user_id:
                        return user_id
        except Exception:
            pass
        return None
    
    def _get_or_create_device_id(self) -> str:
        """Get or create a device ID from ~/.tensorleap/device_id file.
        
        If the file doesn't exist, creates it with a new UUID.
        
        Returns:
            str: The device ID (UUID string)
        """
        try:
            device_id_path = os.path.expanduser("~/.tensorleap/device_id")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(device_id_path), exist_ok=True)
            
            if os.path.exists(device_id_path):
                with open(device_id_path, 'r') as f:
                    device_id = f.read().strip()
                    if device_id:
                        return device_id
            
            # Generate new device ID and save it
            device_id = str(uuid.uuid4())
            with open(device_id_path, 'w') as f:
                f.write(device_id)
            
            return device_id
        except Exception:
            # Fallback to generating a new UUID if file operations fail
            return str(uuid.uuid4())
    
    def _get_distinct_id(self) -> str:
        """Get the distinct ID for Mixpanel tracking.
        
        Priority order:
        1. TensorLeap user ID (from ~/.tensorleap/user_id)
        2. Device ID (from ~/.tensorleap/device_id, generated if not exists)
        """
        tensorleap_user_id = self._get_tensorleap_user_id()
        if tensorleap_user_id:
            return tensorleap_user_id
        
        return self._get_or_create_device_id()
    
    def track_code_loader_loaded(self, event_properties: Optional[Dict[str, Any]] = None) -> None:
        """Track code loader loaded event with device identification.
        
        Args:
            event_properties: Optional additional properties to include in the event
        """
        # Skip tracking if IS_TENSORLEAP_PLATFORM environment variable is set to 'true'
        if os.environ.get('IS_TENSORLEAP_PLATFORM') == 'true':
            return
            
        try:
            distinct_id = self._get_distinct_id()
            
            tensorleap_user_id = self._get_tensorleap_user_id()
            whoami = self._get_whoami()
            device_id = self._get_or_create_device_id()
            
            properties = {
                'tracking_version': TRACKING_VERSION,
                'service': 'code-loader',
                'whoami': whoami,
                '$device_id': device_id,  # Always use device_id for $device_id
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': os.name,
            }
            
            if tensorleap_user_id:
                properties['user_id'] = tensorleap_user_id
            
            if event_properties:
                properties.update(event_properties)
            
            self.mp.track(distinct_id, 'code_loader_loaded', properties)
        except Exception as e:
            pass


# Global tracker instance
_tracker = None


def get_tracker() -> MixpanelTracker:
    global _tracker
    if _tracker is None:
        _tracker = MixpanelTracker()
    return _tracker


def track_code_loader_loaded(event_properties: Optional[Dict[str, Any]] = None) -> None:
    get_tracker().track_code_loader_loaded(event_properties)
