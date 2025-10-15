#!/usr/bin/env python3
"""
Test PhdWin database integration with RESAID
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from resaid.database import PhdWinDatabase
    print("✓ PhdWinDatabase imported successfully")
    
    # Test PhdWin database interface
    phd_file = "reference/TxWells.phz"
    if not os.path.exists(phd_file):
        print(f"✗ PhdWin database not found: {phd_file}")
        sys.exit(1)
    
    print(f"Testing PhdWin database: {phd_file}")
    
    # Create PhdWin database interface
    db = PhdWinDatabase(phd_file)
    print(f"✓ Database type detected: {db.db_type}")
    
    # Try to connect
    if db.connect():
        print("✓ Database connection successful")
        
        # Get tables
        tables = db.get_tables()
        print(f"✓ Tables found: {len(tables)}")
        for table in tables[:5]:  # Show first 5 tables
            print(f"  - {table}")
        
        # Test table columns for first table
        if tables:
            first_table = tables[0]
            columns = db.get_table_columns(first_table)
            print(f"✓ Columns in {first_table}: {len(columns)}")
            for col in columns[:5]:  # Show first 5 columns
                print(f"  - {col}")
        
        db.close()
        print("✓ Database connection closed")
        
    else:
        print("✗ Database connection failed")
    
    print("✓ PhdWin integration test completed")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
