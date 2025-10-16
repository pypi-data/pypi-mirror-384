#!/usr/bin/env python3
"""
Check total size of COLBERT indexes and document collections to determine if RAM loading is feasible.
"""

import sys
import json
import os
import psutil
from pathlib import Path
from typing import Dict, List, Tuple

def get_dir_size(path: Path) -> int:
    """Get total size of a directory in bytes."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    except (PermissionError, FileNotFoundError):
        pass
    return total

def format_bytes(bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

def analyze_indexes(config_path: str) -> None:
    """Analyze index sizes and RAM availability."""
    
    # Load config
    with open(config_path) as f:
        config = json.load(f)
    
    print("=" * 70)
    print("INDEX SIZE ANALYSIS")
    print("=" * 70)
    
    # Analyze COLBERT indexes
    print("\nCOLBERT Indexes:")
    print("-" * 70)
    
    colbert_sizes = []
    for service in config.get('services', []):
        if service.get('engine') == 'PLAIDX':
            index_path = Path(service['config']['index_path'])
            if index_path.exists():
                size = get_dir_size(index_path)
                colbert_sizes.append((service['name'], index_path, size))
                print(f"{service['name']:30} {format_bytes(size):>15} {str(index_path)}")
                
                # Show largest files in this index
                large_files = []
                for file in index_path.rglob('*'):
                    if file.is_file() and file.stat().st_size > 100 * 1024 * 1024:  # > 100MB
                        large_files.append((file.name, file.stat().st_size))
                
                if large_files:
                    large_files.sort(key=lambda x: x[1], reverse=True)
                    for fname, fsize in large_files[:3]:  # Top 3 files
                        print(f"  └─ {fname:26} {format_bytes(fsize):>15}")
            else:
                print(f"{service['name']:30} {'NOT FOUND':>15} {str(index_path)}")
    
    # Analyze document collections
    print("\nDocument Collections:")
    print("-" * 70)
    
    doc_sizes = []
    for collection in config.get('collections', []):
        doc_path = Path(collection['doc_path'])
        offset_path = collection.get('cache_path', str(doc_path) + '.offsetmap')
        offset_path = Path(offset_path)
        
        doc_size = doc_path.stat().st_size if doc_path.exists() else 0
        offset_size = offset_path.stat().st_size if offset_path.exists() else 0
        total_size = doc_size + offset_size
        
        doc_sizes.append((collection['name'], total_size))
        
        print(f"{collection['name']:30} {format_bytes(total_size):>15}")
        if doc_path.exists():
            print(f"  ├─ Document:                 {format_bytes(doc_size):>15}")
        if offset_path.exists():
            print(f"  └─ Offset map:               {format_bytes(offset_size):>15}")
    
    # Calculate totals
    total_colbert = sum(size for _, _, size in colbert_sizes)
    total_docs = sum(size for _, size in doc_sizes)
    grand_total = total_colbert + total_docs
    
    print("\nSummary:")
    print("-" * 70)
    print(f"Total COLBERT indexes:         {format_bytes(total_colbert):>15}")
    print(f"Total document collections:    {format_bytes(total_docs):>15}")
    print(f"GRAND TOTAL:                   {format_bytes(grand_total):>15}")
    
    # System memory analysis
    mem = psutil.virtual_memory()
    print("\nSystem Memory:")
    print("-" * 70)
    print(f"Total RAM:                     {format_bytes(mem.total):>15}")
    print(f"Available RAM:                 {format_bytes(mem.available):>15}")
    print(f"Used RAM:                      {format_bytes(mem.used):>15} ({mem.percent:.1f}%)")
    
    # Recommendations
    print("\nRecommendations:")
    print("=" * 70)
    
    # For RAM disk
    safe_ram_size = mem.available * 0.8  # Use only 80% of available RAM
    
    if grand_total < safe_ram_size:
        print("✓ RAM DISK FEASIBLE: All indexes can fit in RAM!")
        print(f"  Recommended RAM disk size: {format_bytes(int(grand_total * 1.2))}")
        print("\n  To create RAM disk:")
        print(f"  sudo mkdir -p /mnt/ramdisk")
        print(f"  sudo mount -t tmpfs -o size={int(grand_total * 1.2 / 1e9) + 1}G tmpfs /mnt/ramdisk")
    else:
        print("✗ RAM DISK NOT FEASIBLE: Indexes too large for available RAM")
        
        # Check if just COLBERT fits
        if total_colbert < safe_ram_size:
            print("\n  However, COLBERT indexes alone could fit in RAM:")
            print(f"  Recommended RAM disk size: {format_bytes(int(total_colbert * 1.2))}")
            print("\n  To create RAM disk for COLBERT only:")
            print(f"  sudo mkdir -p /mnt/ramdisk")
            print(f"  sudo mount -t tmpfs -o size={int(total_colbert * 1.2 / 1e9) + 1}G tmpfs /mnt/ramdisk")
    
    # For SSD
    print("\n✓ SSD OPTIMIZATION: Move largest files to SSD")
    print("  Recommended files to move:")
    
    # Find largest files across all indexes
    all_large_files = []
    for service in config.get('services', []):
        if service.get('engine') == 'PLAIDX':
            index_path = Path(service['config']['index_path'])
            if index_path.exists():
                for file in index_path.rglob('*'):
                    if file.is_file() and file.stat().st_size > 500 * 1024 * 1024:  # > 500MB
                        all_large_files.append((file, file.stat().st_size))
    
    all_large_files.sort(key=lambda x: x[1], reverse=True)
    total_to_move = 0
    for file, size in all_large_files[:5]:  # Top 5 files
        print(f"  - {file.name:30} {format_bytes(size):>15}")
        total_to_move += size
    
    if all_large_files:
        print(f"\n  Moving these {len(all_large_files[:5])} files would save {format_bytes(total_to_move)} of slow disk I/O")

    # Show example commands
    if all_large_files and total_to_move > 1e9:  # If more than 1GB
        print("\n  Example move commands:")
        example_file = all_large_files[0][0]
        print(f"  mkdir -p /fast/ssd/colbert_cache")
        print(f"  mv {example_file} /fast/ssd/colbert_cache/")
        print(f"  ln -s /fast/ssd/colbert_cache/{example_file.name} {example_file}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_index_sizes.py <config.json>")
        sys.exit(1)
    
    analyze_indexes(sys.argv[1])