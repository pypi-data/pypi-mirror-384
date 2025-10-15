"""
CLI command for MongoDB migration
"""

import asyncio
import typer
from pathlib import Path
import logging

from database.migration import run_migration
from database.mongodb_manager import mongodb_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer(name="mongodb-migration", help="MongoDB migration utilities")

@app.command()
def migrate(
    sqlite_db_path: str = typer.Option("policy_guard.db", help="Path to SQLite database"),
    verify: bool = typer.Option(True, help="Verify migration after completion")
):
    """Migrate data from SQLite to MongoDB"""
    typer.echo("Starting SQLite to MongoDB migration...")
    
    # Check if SQLite database exists
    if not Path(sqlite_db_path).exists():
        typer.secho(f"SQLite database not found: {sqlite_db_path}", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    try:
        # Run migration
        results, verification = asyncio.run(run_migration(sqlite_db_path))
        
        typer.secho("Migration completed successfully!", fg=typer.colors.GREEN)
        typer.echo(f"Results: {results}")
        
        if verify:
            typer.echo(f"Verification: {verification}")
            
            if verification.get("migration_successful", False):
                typer.secho("Migration verification passed!", fg=typer.colors.GREEN)
            else:
                typer.secho("Migration verification failed!", fg=typer.colors.RED)
        
    except Exception as e:
        typer.secho(f"Migration failed: {str(e)}", fg=typer.colors.RED)
        logger.error(f"Migration error: {e}")
        raise typer.Exit(1)

@app.command()
def test_connection():
    """Test MongoDB connection"""
    typer.echo("Testing MongoDB connection...")
    
    async def test():
        try:
            success = await mongodb_manager.initialize()
            if success:
                typer.secho("MongoDB connection successful!", fg=typer.colors.GREEN)
                
                # Test basic operations
                db = await mongodb_manager.config.get_database()
                collections = await db.list_collection_names()
                typer.echo(f"Available collections: {collections}")
                
                await mongodb_manager.close()
                return True
            else:
                typer.secho("MongoDB connection failed!", fg=typer.colors.RED)
                return False
        except Exception as e:
            typer.secho(f"MongoDB connection error: {str(e)}", fg=typer.colors.RED)
            return False
    
    success = asyncio.run(test())
    if not success:
        raise typer.Exit(1)

@app.command()
def cleanup(
    days: int = typer.Option(90, help="Days of data to keep")
):
    """Clean up old data from MongoDB"""
    typer.echo(f"Cleaning up data older than {days} days...")
    
    async def cleanup_data():
        try:
            await mongodb_manager.initialize()
            await mongodb_manager.cleanup_old_data(days)
            typer.secho("Cleanup completed successfully!", fg=typer.colors.GREEN)
            await mongodb_manager.close()
        except Exception as e:
            typer.secho(f"Cleanup failed: {str(e)}", fg=typer.colors.RED)
            raise typer.Exit(1)
    
    asyncio.run(cleanup_data())

@app.command()
def stats():
    """Show MongoDB database statistics"""
    typer.echo("Fetching MongoDB statistics...")
    
    async def get_stats():
        try:
            await mongodb_manager.initialize()
            db = await mongodb_manager.config.get_database()
            
            typer.echo(f"Database: {mongodb_manager.config.database_name}")
            typer.echo(f"Collections:")
            
            collections = await db.list_collection_names()
            for collection_name in collections:
                collection = db[collection_name]
                count = await collection.count_documents({})
                typer.echo(f"  {collection_name}: {count} documents")
            
            await mongodb_manager.close()
            
        except Exception as e:
            typer.secho(f"Failed to get statistics: {str(e)}", fg=typer.colors.RED)
            raise typer.Exit(1)
    
    asyncio.run(get_stats())

if __name__ == "__main__":
    app()
