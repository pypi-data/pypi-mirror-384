"""
MongoDB Configuration for OS Forge
"""

import os
import yaml
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MongoDBConfig:
    """MongoDB configuration and connection management"""
    
    def __init__(self):
        # Load configuration from file if available
        config = self._load_config()
        
        # Try environment variable first, then config file, then fallback to Atlas URI (hardcoded)
        self.uri = (
            os.getenv("MONGODB_URI") or 
            config.get("mongodb", {}).get("uri") or 
            "mongodb+srv://aayushman2702:Lmaoded%4011@cluster0.eivmu.mongodb.net/Os-forge?retryWrites=true&w=majority&appName=Cluster0"
        )
        self.database_name = (
            os.getenv("MONGODB_DATABASE") or 
            config.get("mongodb", {}).get("database") or 
            "Os-forge"
        )
        self.collection_name = (
            os.getenv("MONGODB_COLLECTION") or 
            config.get("mongodb", {}).get("collection") or 
            "detailsforOS"
        )
        self.enabled = bool(self.uri)
        
        if not self.enabled:
            logger.info("MongoDB URI not provided. MongoDB features will be disabled.")
            logger.info("To enable MongoDB features, set MONGODB_URI environment variable.")
        else:
            if os.getenv("MONGODB_URI"):
                logger.info("MongoDB URI found from environment. MongoDB features will be enabled.")
            elif config.get("mongodb", {}).get("uri"):
                logger.info("MongoDB URI found from config file. MongoDB features will be enabled.")
            else:
                logger.info("Using default MongoDB URI (localhost:27017). MongoDB features will be enabled.")
        
        # Connection settings
        self.max_pool_size = 50
        self.min_pool_size = 10
        self.max_idle_time_ms = 30000
        self.server_selection_timeout_ms = 5000
        self.connect_timeout_ms = 10000
        self.socket_timeout_ms = 20000
        
        self._client: Optional[AsyncIOMotorClient] = None
        self._sync_client: Optional[MongoClient] = None
        self._database = None
        self._sync_database = None
    
    def _load_config(self) -> dict:
        """Load configuration from config.yaml file"""
        config_paths = [
            Path("config.yaml"),
            Path("~/.os-forge/config.yaml").expanduser(),
            Path("/etc/os-forge/config.yaml")
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        logger.info(f"Loaded configuration from {config_path}")
                        return config or {}
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return {}
    
    def is_enabled(self) -> bool:
        """Check if MongoDB is enabled"""
        return self.enabled
    
    async def get_async_client(self) -> AsyncIOMotorClient:
        """Get async MongoDB client"""
        if not self.enabled:
            raise RuntimeError("MongoDB is not enabled. Set MONGODB_URI environment variable.")
        
        if self._client is None:
            self._client = AsyncIOMotorClient(
                self.uri,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                maxIdleTimeMS=self.max_idle_time_ms,
                serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                connectTimeoutMS=self.connect_timeout_ms,
                socketTimeoutMS=self.socket_timeout_ms
            )
        return self._client
    
    def get_sync_client(self) -> MongoClient:
        """Get synchronous MongoDB client"""
        if not self.enabled:
            raise RuntimeError("MongoDB is not enabled. Set MONGODB_URI environment variable.")
        
        if self._sync_client is None:
            self._sync_client = MongoClient(
                self.uri,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                maxIdleTimeMS=self.max_idle_time_ms,
                serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                connectTimeoutMS=self.connect_timeout_ms,
                socketTimeoutMS=self.socket_timeout_ms
            )
        return self._sync_client
    
    async def get_database(self):
        """Get MongoDB database (async)"""
        if self._database is None:
            client = await self.get_async_client()
            self._database = client[self.database_name]
        return self._database
    
    def get_sync_database(self):
        """Get MongoDB database (sync)"""
        if self._sync_database is None:
            client = self.get_sync_client()
            self._sync_database = client[self.database_name]
        return self._sync_database
    
    async def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            client = await self.get_async_client()
            await client.admin.command('ping')
            logger.info("MongoDB connection successful")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False
    
    async def close_connections(self):
        """Close all MongoDB connections"""
        if self._client:
            self._client.close()
            self._client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        self._database = None
        self._sync_database = None

# Global MongoDB configuration instance
mongodb_config = MongoDBConfig()
