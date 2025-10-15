#!/usr/bin/env python3
"""
Enhanced Secrets Management for OS Forge
Provides secure secret storage, rotation, and access control
"""

import os
import json
import base64
import hashlib
import secrets
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecretMetadata:
    """Metadata for a stored secret"""
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    last_accessed: Optional[datetime]
    tags: List[str]
    rotation_policy: Optional[str]

@dataclass
class SecretAccessLog:
    """Log entry for secret access"""
    secret_name: str
    accessed_at: datetime
    accessed_by: str
    access_type: str  # READ, WRITE, DELETE, ROTATE
    success: bool
    ip_address: Optional[str]
    user_agent: Optional[str]

class SecretsManager:
    """Enhanced secrets management system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.secrets_dir = Path(self.config["secrets_directory"])
        self.metadata_file = self.secrets_dir / "metadata.json"
        self.access_log_file = self.secrets_dir / "access_log.json"
        self.key_file = self.secrets_dir / ".key"
        
        # Initialize encryption
        self._initialize_encryption()
        
        # Load metadata and access logs
        self.metadata = self._load_metadata()
        self.access_logs = self._load_access_logs()
        
        # Ensure secrets directory exists
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load secrets manager configuration"""
        default_config = {
            "secrets_directory": "./secrets",
            "encryption_algorithm": "fernet",
            "key_derivation_iterations": 100000,
            "access_log_retention_days": 90,
            "rotation_policies": {
                "daily": {"interval": 1, "unit": "days"},
                "weekly": {"interval": 7, "unit": "days"},
                "monthly": {"interval": 30, "unit": "days"},
                "quarterly": {"interval": 90, "unit": "days"},
                "yearly": {"interval": 365, "unit": "days"}
            },
            "default_expiration_days": 90,
            "max_access_attempts": 5,
            "lockout_duration_minutes": 30
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _initialize_encryption(self):
        """Initialize encryption key and cipher"""
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key_data = f.read()
        else:
            # Generate new key
            key_data = self._generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key_data)
            # Secure the key file
            os.chmod(self.key_file, 0o600)
        
        self.cipher = Fernet(key_data)
    
    def _generate_key(self) -> bytes:
        """Generate encryption key"""
        password = os.environ.get("SECRETS_MANAGER_PASSWORD", "default_password_change_me")
        password_bytes = password.encode()
        
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.config["key_derivation_iterations"]
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        
        return key
    
    def _load_metadata(self) -> Dict[str, SecretMetadata]:
        """Load secret metadata"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
            
            metadata = {}
            for name, meta_dict in data.items():
                meta_dict['created_at'] = datetime.fromisoformat(meta_dict['created_at'])
                meta_dict['updated_at'] = datetime.fromisoformat(meta_dict['updated_at'])
                if meta_dict.get('expires_at'):
                    meta_dict['expires_at'] = datetime.fromisoformat(meta_dict['expires_at'])
                if meta_dict.get('last_accessed'):
                    meta_dict['last_accessed'] = datetime.fromisoformat(meta_dict['last_accessed'])
                metadata[name] = SecretMetadata(**meta_dict)
            
            return metadata
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {}
    
    def _load_access_logs(self) -> List[SecretAccessLog]:
        """Load access logs"""
        if not self.access_log_file.exists():
            return []
        
        try:
            with open(self.access_log_file, 'r') as f:
                data = json.load(f)
            
            logs = []
            for log_dict in data:
                log_dict['accessed_at'] = datetime.fromisoformat(log_dict['accessed_at'])
                logs.append(SecretAccessLog(**log_dict))
            
            return logs
        except Exception as e:
            logger.error(f"Failed to load access logs: {e}")
            return []
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            data = {}
            for name, metadata in self.metadata.items():
                meta_dict = asdict(metadata)
                meta_dict['created_at'] = metadata.created_at.isoformat()
                meta_dict['updated_at'] = metadata.updated_at.isoformat()
                if metadata.expires_at:
                    meta_dict['expires_at'] = metadata.expires_at.isoformat()
                if metadata.last_accessed:
                    meta_dict['last_accessed'] = metadata.last_accessed.isoformat()
                data[name] = meta_dict
            
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _save_access_logs(self):
        """Save access logs to file"""
        try:
            data = []
            for log in self.access_logs:
                log_dict = asdict(log)
                log_dict['accessed_at'] = log.accessed_at.isoformat()
                data.append(log_dict)
            
            with open(self.access_log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save access logs: {e}")
    
    def _log_access(self, secret_name: str, access_type: str, success: bool, 
                   accessed_by: str = "system", ip_address: str = None, 
                   user_agent: str = None):
        """Log secret access"""
        log_entry = SecretAccessLog(
            secret_name=secret_name,
            accessed_at=datetime.now(),
            accessed_by=accessed_by,
            access_type=access_type,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.access_logs.append(log_entry)
        
        # Clean old logs
        cutoff_date = datetime.now() - timedelta(days=self.config["access_log_retention_days"])
        self.access_logs = [log for log in self.access_logs if log.accessed_at > cutoff_date]
        
        self._save_access_logs()
    
    def store_secret(self, name: str, value: str, description: str = "", 
                    expires_in_days: Optional[int] = None, tags: List[str] = None,
                    rotation_policy: Optional[str] = None) -> bool:
        """Store a secret securely"""
        try:
            # Validate secret name
            if not self._validate_secret_name(name):
                logger.error(f"Invalid secret name: {name}")
                return False
            
            # Check if secret already exists
            if name in self.metadata:
                logger.warning(f"Secret {name} already exists. Use update_secret to modify.")
                return False
            
            # Encrypt the secret value
            encrypted_value = self.cipher.encrypt(value.encode())
            
            # Create metadata
            now = datetime.now()
            expires_at = None
            if expires_in_days:
                expires_at = now + timedelta(days=expires_in_days)
            elif self.config["default_expiration_days"]:
                expires_at = now + timedelta(days=self.config["default_expiration_days"])
            
            metadata = SecretMetadata(
                name=name,
                description=description,
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
                access_count=0,
                last_accessed=None,
                tags=tags or [],
                rotation_policy=rotation_policy
            )
            
            # Store encrypted secret
            secret_file = self.secrets_dir / f"{name}.enc"
            with open(secret_file, 'wb') as f:
                f.write(encrypted_value)
            os.chmod(secret_file, 0o600)
            
            # Update metadata
            self.metadata[name] = metadata
            self._save_metadata()
            
            self._log_access(name, "WRITE", True)
            logger.info(f"Secret {name} stored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret {name}: {e}")
            self._log_access(name, "WRITE", False)
            return False
    
    def retrieve_secret(self, name: str, accessed_by: str = "system") -> Optional[str]:
        """Retrieve a secret"""
        try:
            if name not in self.metadata:
                logger.error(f"Secret {name} not found")
                self._log_access(name, "READ", False, accessed_by)
                return None
            
            metadata = self.metadata[name]
            
            # Check if secret is expired
            if metadata.expires_at and datetime.now() > metadata.expires_at:
                logger.error(f"Secret {name} has expired")
                self._log_access(name, "READ", False, accessed_by)
                return None
            
            # Read and decrypt secret
            secret_file = self.secrets_dir / f"{name}.enc"
            if not secret_file.exists():
                logger.error(f"Secret file for {name} not found")
                self._log_access(name, "READ", False, accessed_by)
                return None
            
            with open(secret_file, 'rb') as f:
                encrypted_value = f.read()
            
            decrypted_value = self.cipher.decrypt(encrypted_value).decode()
            
            # Update access metadata
            metadata.access_count += 1
            metadata.last_accessed = datetime.now()
            self._save_metadata()
            
            self._log_access(name, "READ", True, accessed_by)
            logger.info(f"Secret {name} retrieved successfully")
            return decrypted_value
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret {name}: {e}")
            self._log_access(name, "READ", False, accessed_by)
            return None
    
    def update_secret(self, name: str, value: str, description: str = None) -> bool:
        """Update an existing secret"""
        try:
            if name not in self.metadata:
                logger.error(f"Secret {name} not found")
                return False
            
            # Encrypt new value
            encrypted_value = self.cipher.encrypt(value.encode())
            
            # Update secret file
            secret_file = self.secrets_dir / f"{name}.enc"
            with open(secret_file, 'wb') as f:
                f.write(encrypted_value)
            
            # Update metadata
            metadata = self.metadata[name]
            metadata.updated_at = datetime.now()
            if description is not None:
                metadata.description = description
            self._save_metadata()
            
            self._log_access(name, "WRITE", True)
            logger.info(f"Secret {name} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update secret {name}: {e}")
            self._log_access(name, "WRITE", False)
            return False
    
    def delete_secret(self, name: str) -> bool:
        """Delete a secret"""
        try:
            if name not in self.metadata:
                logger.error(f"Secret {name} not found")
                return False
            
            # Remove secret file
            secret_file = self.secrets_dir / f"{name}.enc"
            if secret_file.exists():
                secret_file.unlink()
            
            # Remove from metadata
            del self.metadata[name]
            self._save_metadata()
            
            self._log_access(name, "DELETE", True)
            logger.info(f"Secret {name} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret {name}: {e}")
            self._log_access(name, "DELETE", False)
            return False
    
    def rotate_secret(self, name: str, new_value: str = None) -> bool:
        """Rotate a secret"""
        try:
            if name not in self.metadata:
                logger.error(f"Secret {name} not found")
                return False
            
            # Generate new value if not provided
            if new_value is None:
                new_value = self._generate_random_secret()
            
            # Update the secret
            success = self.update_secret(name, new_value)
            if success:
                self._log_access(name, "ROTATE", True)
                logger.info(f"Secret {name} rotated successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rotate secret {name}: {e}")
            self._log_access(name, "ROTATE", False)
            return False
    
    def _generate_random_secret(self, length: int = 32) -> str:
        """Generate a random secret"""
        return secrets.token_urlsafe(length)
    
    def _validate_secret_name(self, name: str) -> bool:
        """Validate secret name"""
        if not name or len(name) < 3:
            return False
        
        # Check for valid characters
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        if not all(c in valid_chars for c in name):
            return False
        
        return True
    
    def list_secrets(self, tags: List[str] = None, expired_only: bool = False) -> List[Dict[str, Any]]:
        """List secrets with optional filtering"""
        secrets_list = []
        
        for name, metadata in self.metadata.items():
            # Filter by tags
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            
            # Filter by expiration
            if expired_only:
                if not metadata.expires_at or datetime.now() <= metadata.expires_at:
                    continue
            elif metadata.expires_at and datetime.now() > metadata.expires_at:
                continue
            
            secrets_list.append({
                "name": name,
                "description": metadata.description,
                "created_at": metadata.created_at,
                "updated_at": metadata.updated_at,
                "expires_at": metadata.expires_at,
                "access_count": metadata.access_count,
                "last_accessed": metadata.last_accessed,
                "tags": metadata.tags,
                "rotation_policy": metadata.rotation_policy,
                "is_expired": metadata.expires_at and datetime.now() > metadata.expires_at
            })
        
        return secrets_list
    
    def get_access_logs(self, secret_name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get access logs"""
        logs = self.access_logs
        
        if secret_name:
            logs = [log for log in logs if log.secret_name == secret_name]
        
        # Sort by access time (newest first)
        logs.sort(key=lambda x: x.accessed_at, reverse=True)
        
        # Limit results
        logs = logs[:limit]
        
        return [asdict(log) for log in logs]
    
    def cleanup_expired_secrets(self) -> int:
        """Remove expired secrets"""
        expired_secrets = []
        now = datetime.now()
        
        for name, metadata in self.metadata.items():
            if metadata.expires_at and now > metadata.expires_at:
                expired_secrets.append(name)
        
        for name in expired_secrets:
            self.delete_secret(name)
        
        logger.info(f"Cleaned up {len(expired_secrets)} expired secrets")
        return len(expired_secrets)
    
    def export_secrets(self, output_path: str, format: str = "json") -> bool:
        """Export secrets (encrypted) for backup"""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "secrets_count": len(self.metadata),
                "secrets": {}
            }
            
            for name, metadata in self.metadata.items():
                secret_value = self.retrieve_secret(name)
                if secret_value:
                    export_data["secrets"][name] = {
                        "value": secret_value,
                        "metadata": asdict(metadata)
                    }
            
            if format.lower() == "json":
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Secrets exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export secrets: {e}")
            return False
    
    def import_secrets(self, import_path: str) -> int:
        """Import secrets from backup"""
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            imported_count = 0
            
            for name, secret_data in import_data.get("secrets", {}).items():
                if self.store_secret(
                    name=name,
                    value=secret_data["value"],
                    description=secret_data["metadata"]["description"],
                    tags=secret_data["metadata"]["tags"]
                ):
                    imported_count += 1
            
            logger.info(f"Imported {imported_count} secrets from {import_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import secrets: {e}")
            return 0


def main():
    """CLI interface for secrets manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OS Forge Secrets Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Store command
    store_parser = subparsers.add_parser("store", help="Store a secret")
    store_parser.add_argument("name", help="Secret name")
    store_parser.add_argument("value", help="Secret value")
    store_parser.add_argument("--description", help="Secret description")
    store_parser.add_argument("--expires-in-days", type=int, help="Expiration in days")
    store_parser.add_argument("--tags", nargs="+", help="Secret tags")
    store_parser.add_argument("--rotation-policy", help="Rotation policy")
    
    # Retrieve command
    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve a secret")
    retrieve_parser.add_argument("name", help="Secret name")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List secrets")
    list_parser.add_argument("--tags", nargs="+", help="Filter by tags")
    list_parser.add_argument("--expired-only", action="store_true", help="Show only expired secrets")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update a secret")
    update_parser.add_argument("name", help="Secret name")
    update_parser.add_argument("value", help="New secret value")
    update_parser.add_argument("--description", help="New description")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a secret")
    delete_parser.add_argument("name", help="Secret name")
    
    # Rotate command
    rotate_parser = subparsers.add_parser("rotate", help="Rotate a secret")
    rotate_parser.add_argument("name", help="Secret name")
    rotate_parser.add_argument("--new-value", help="New secret value")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show access logs")
    logs_parser.add_argument("--secret-name", help="Filter by secret name")
    logs_parser.add_argument("--limit", type=int, default=50, help="Limit number of logs")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up expired secrets")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export secrets")
    export_parser.add_argument("output_path", help="Output file path")
    export_parser.add_argument("--format", default="json", help="Export format")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import secrets")
    import_parser.add_argument("import_path", help="Import file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = SecretsManager()
    
    try:
        if args.command == "store":
            success = manager.store_secret(
                name=args.name,
                value=args.value,
                description=args.description,
                expires_in_days=args.expires_in_days,
                tags=args.tags,
                rotation_policy=args.rotation_policy
            )
            print("Secret stored successfully" if success else "Failed to store secret")
            
        elif args.command == "retrieve":
            value = manager.retrieve_secret(args.name)
            if value:
                print(value)
            else:
                print("Secret not found or expired")
                
        elif args.command == "list":
            secrets = manager.list_secrets(tags=args.tags, expired_only=args.expired_only)
            if secrets:
                print(f"{'Name':<20} {'Description':<30} {'Expires':<20} {'Access Count':<12}")
                print("-" * 82)
                for secret in secrets:
                    expires_str = secret['expires_at'].strftime('%Y-%m-%d') if secret['expires_at'] else 'Never'
                    print(f"{secret['name']:<20} {secret['description']:<30} {expires_str:<20} {secret['access_count']:<12}")
            else:
                print("No secrets found")
                
        elif args.command == "update":
            success = manager.update_secret(args.name, args.value, args.description)
            print("Secret updated successfully" if success else "Failed to update secret")
            
        elif args.command == "delete":
            success = manager.delete_secret(args.name)
            print("Secret deleted successfully" if success else "Failed to delete secret")
            
        elif args.command == "rotate":
            success = manager.rotate_secret(args.name, args.new_value)
            print("Secret rotated successfully" if success else "Failed to rotate secret")
            
        elif args.command == "logs":
            logs = manager.get_access_logs(args.secret_name, args.limit)
            if logs:
                print(f"{'Secret':<20} {'Accessed At':<20} {'Type':<8} {'Success':<8} {'Accessed By':<15}")
                print("-" * 71)
                for log in logs:
                    accessed_at = log['accessed_at'][:19]  # Remove microseconds
                    print(f"{log['secret_name']:<20} {accessed_at:<20} {log['access_type']:<8} {log['success']:<8} {log['accessed_by']:<15}")
            else:
                print("No access logs found")
                
        elif args.command == "cleanup":
            count = manager.cleanup_expired_secrets()
            print(f"Cleaned up {count} expired secrets")
            
        elif args.command == "export":
            success = manager.export_secrets(args.output_path, args.format)
            print("Secrets exported successfully" if success else "Failed to export secrets")
            
        elif args.command == "import":
            count = manager.import_secrets(args.import_path)
            print(f"Imported {count} secrets")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
