"""
Host Key Storage Implementation

Provides host key storage and retrieval functionality for
maintaining known host keys and verification.
"""

from typing import Dict, Optional, Any, List
import os
import base64
import logging
from ..exceptions import SSHException
from ..crypto.pkey import PKey


class HostKeyStorage:
    """
    Host key storage implementation.
    
    Manages storage and retrieval of known host keys for
    host verification and security policy enforcement.
    """
    
    def __init__(self, filename: Optional[str] = None) -> None:
        """
        Initialize host key storage.
        
        Args:
            filename: Path to known_hosts file (optional)
        """
        self._filename = filename or os.path.expanduser("~/.ssh/known_hosts")
        self._keys: Dict[str, List[PKey]] = {}
        self._logger = logging.getLogger(__name__)
        
        # Try to load existing keys
        try:
            self.load()
        except Exception as e:
            self._logger.debug(f"Could not load host keys from {self._filename}: {e}")
    
    def load(self) -> None:
        """
        Load host keys from storage file.
        
        Raises:
            SSHException: If loading fails
        """
        if not os.path.exists(self._filename):
            self._logger.debug(f"Host key file {self._filename} does not exist")
            return
        
        try:
            with open(self._filename, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    try:
                        self._parse_host_key_line(line)
                    except Exception as e:
                        self._logger.warning(f"Error parsing line {line_num} in {self._filename}: {e}")
                        
        except Exception as e:
            raise SSHException(f"Failed to load host keys from {self._filename}: {e}")
    
    def _parse_host_key_line(self, line: str) -> None:
        """
        Parse a single host key line from known_hosts format.
        
        Args:
            line: Line to parse
        """
        parts = line.split()
        if len(parts) < 3:
            return  # Invalid line format
        
        hostnames_part = parts[0]
        key_type = parts[1]
        key_data = parts[2]
        
        # Parse hostnames (can be comma-separated)
        hostnames = [h.strip() for h in hostnames_part.split(',')]
        
        try:
            # Decode base64 key data
            key_bytes = base64.b64decode(key_data)
            
            # Create appropriate key object based on type
            key = self._create_key_from_type_and_data(key_type, key_bytes)
            
            if key:
                # Add key for each hostname
                for hostname in hostnames:
                    if hostname not in self._keys:
                        self._keys[hostname] = []
                    self._keys[hostname].append(key)
                    
        except Exception as e:
            self._logger.debug(f"Failed to parse key data: {e}")
    
    def _create_key_from_type_and_data(self, key_type: str, key_data: bytes) -> Optional[PKey]:
        """
        Create PKey instance from key type and data.
        
        Args:
            key_type: SSH key type string
            key_data: Key data bytes
            
        Returns:
            PKey instance or None if unsupported
        """
        try:
            # Import key classes
            from ..crypto.pkey import Ed25519Key, ECDSAKey, RSAKey
            
            if key_type == "ssh-ed25519":
                key = Ed25519Key()
                key.load_public_key(key_data)
                return key
            elif key_type.startswith("ecdsa-sha2-"):
                key = ECDSAKey()
                key.load_public_key(key_data)
                return key
            elif key_type.startswith("ssh-rsa") or key_type.startswith("rsa-sha2-"):
                key = RSAKey()
                key.load_public_key(key_data)
                return key
            else:
                self._logger.debug(f"Unsupported key type: {key_type}")
                return None
                
        except Exception as e:
            self._logger.debug(f"Failed to create key from type {key_type}: {e}")
            return None
    
    def save(self) -> None:
        """
        Save host keys to storage file.
        
        Raises:
            SSHException: If saving fails
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self._filename), exist_ok=True)
            
            with open(self._filename, 'w', encoding='utf-8') as f:
                f.write("# SSH known hosts file\n")
                f.write("# Generated by ssh_library\n\n")
                
                for hostname, keys in self._keys.items():
                    for key in keys:
                        try:
                            key_data = base64.b64encode(key.get_public_key_bytes()).decode('ascii')
                            f.write(f"{hostname} {key.algorithm_name} {key_data}\n")
                        except Exception as e:
                            self._logger.warning(f"Failed to save key for {hostname}: {e}")
                            
        except Exception as e:
            raise SSHException(f"Failed to save host keys to {self._filename}: {e}")
    
    def add(self, hostname: str, key: PKey) -> None:
        """
        Add host key to storage.
        
        Args:
            hostname: Server hostname
            key: Host key to store
        """
        if hostname not in self._keys:
            self._keys[hostname] = []
        
        # Check if key already exists
        for existing_key in self._keys[hostname]:
            if existing_key == key:
                return  # Key already exists
        
        # Add new key
        self._keys[hostname].append(key)
        self._logger.debug(f"Added host key for {hostname}: {key.algorithm_name}")
    
    def get(self, hostname: str) -> Optional[PKey]:
        """
        Get host key for hostname.
        
        Args:
            hostname: Server hostname
            
        Returns:
            Host key if found, None otherwise
        """
        if hostname in self._keys and self._keys[hostname]:
            # Return the first key (most recent or preferred)
            return self._keys[hostname][0]
        return None
    
    def get_all(self, hostname: str) -> List[PKey]:
        """
        Get all host keys for hostname.
        
        Args:
            hostname: Server hostname
            
        Returns:
            List of host keys
        """
        return self._keys.get(hostname, [])
    
    def remove(self, hostname: str, key: Optional[PKey] = None) -> bool:
        """
        Remove host key(s) for hostname.
        
        Args:
            hostname: Server hostname
            key: Specific key to remove (if None, removes all keys for hostname)
            
        Returns:
            True if any keys were removed
        """
        if hostname not in self._keys:
            return False
        
        if key is None:
            # Remove all keys for hostname
            del self._keys[hostname]
            return True
        else:
            # Remove specific key
            try:
                self._keys[hostname].remove(key)
                if not self._keys[hostname]:
                    del self._keys[hostname]
                return True
            except ValueError:
                return False