#!/usr/bin/env python3
"""
Simple Price Tracker - Hello World with PostgreSQL
A minimal Python application that demonstrates database connectivity.
"""

import os
import time
import psycopg2
from datetime import datetime

def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'price_tracker_db'),
            user=os.getenv('DB_USER', 'admin'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def test_database():
    """Test database connectivity and create a simple table."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Create a simple test table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS hello_world (
                    id SERIAL PRIMARY KEY,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert a test message
            cur.execute(
                "INSERT INTO hello_world (message) VALUES (%s)",
                (f"Hello from Price Tracker at {datetime.now()}",)
            )
            
            # Query the data
            cur.execute("SELECT * FROM hello_world ORDER BY timestamp DESC LIMIT 5")
            rows = cur.fetchall()
            
            conn.commit()
            
            print("✅ Database connection successful!")
            print("📊 Recent messages from database:")
            for row in rows:
                print(f"   - {row[1]} (ID: {row[0]})")
            
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main application function."""
    print("🚀 Starting Simple Price Tracker...")
    print("=" * 50)
    
    # Show environment info
    print(f"📋 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 Database Host: {os.getenv('DB_HOST', 'localhost')}")
    print(f"🗄️  Database Name: {os.getenv('DB_NAME', 'price_tracker_db')}")
    print(f"👤 Database User: {os.getenv('DB_USER', 'admin')}")
    
    # Test database connection
    if test_database():
        print("\n🎉 Application is running successfully!")
        print("💡 This is a minimal app demonstrating PostgreSQL connectivity.")
        print("🔧 Ready for GitHub Actions deployment!")
    else:
        print("\n❌ Application failed to start properly.")
        return 1
    
    # Keep the application running
    print("\n⏳ Application is running... (Press Ctrl+C to stop)")
    try:
        while True:
            time.sleep(30)  # Sleep for 30 seconds
            print(f"💓 Heartbeat: {datetime.now()}")
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    
    return 0

if __name__ == '__main__':
    exit(main()) 