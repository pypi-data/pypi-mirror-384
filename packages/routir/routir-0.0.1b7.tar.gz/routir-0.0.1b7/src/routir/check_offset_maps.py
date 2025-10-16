#!/usr/bin/env python3
"""
Check if all offset maps are built and valid before starting the server.
"""

import sys
import json
import pickle
from pathlib import Path

def check_offset_maps(config_path: str) -> bool:
    """Check if all collections have valid offset maps."""
    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return False
    
    all_valid = True
    collections = config.get('collections', [])
    
    print(f"Checking offset maps for {len(collections)} collections...")
    print("-" * 60)
    
    for collection in collections:
        name = collection['name']
        doc_path = Path(collection['doc_path'])
        
        # Determine offset map path
        offset_path = collection.get('cache_path')
        if not offset_path:
            offset_path = str(doc_path.with_suffix(doc_path.suffix + '.offsetmap'))
        offset_path = Path(offset_path)
        
        # Check document file
        if not doc_path.exists():
            print(f"✗ {name}: Document file missing: {doc_path}")
            all_valid = False
            continue
        
        # Check offset map
        if not offset_path.exists():
            print(f"✗ {name}: Offset map missing: {offset_path}")
            all_valid = False
            continue
        
        # Try to load offset map
        try:
            with open(offset_path, 'rb') as f:
                loaded_fn, mapping = pickle.load(f)
                num_entries = len(mapping)
                size_mb = offset_path.stat().st_size / 1e6
                print(f"✓ {name}: {num_entries:,} entries, {size_mb:.1f} MB")
        except Exception as e:
            print(f"✗ {name}: Invalid offset map: {e}")
            all_valid = False
    
    print("-" * 60)
    
    if all_valid:
        print("✓ All offset maps are valid and ready!")
        return True
    else:
        print("✗ Some offset maps are missing or invalid.")
        print("  Run: python src/prestart_cache.py config.json")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_offset_maps.py <config.json>")
        sys.exit(1)
    
    if check_offset_maps(sys.argv[1]):
        sys.exit(0)
    else:
        sys.exit(1)