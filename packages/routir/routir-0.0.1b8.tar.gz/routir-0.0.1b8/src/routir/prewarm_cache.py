#!/usr/bin/env python3
"""
Pre-warm file system cache and build offset maps for collections.
Also pre-warms COLBERT index files for faster loading.
"""

import sys
import json
import time
import mmap
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

# Setup logger
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('prewarm_cache')

# Import OffsetFile - handle both module and direct execution
try:
    from src.data import OffsetFile
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent))
    from src.data import OffsetFile


def build_offset_map(collection_config: dict) -> float:
    """Build offset map for a collection if it doesn't exist."""
    start_time = time.time()
    
    doc_path = Path(collection_config['doc_path'])
    if not doc_path.exists():
        logger.error(f"Document file {doc_path} does not exist!")
        return 0.0
    
    # Determine offset map path
    offset_path = collection_config.get('cache_path')
    if not offset_path:
        offset_path = str(doc_path.with_suffix(doc_path.suffix + '.offsetmap'))
    offset_path = Path(offset_path)
    
    # Check if offset map already exists
    if offset_path.exists():
        logger.info(f"Offset map already exists at {offset_path}")
        return 0.0
    
    logger.info(f"Building offset map for {collection_config['name']}...")
    logger.info(f"  Document: {doc_path}")
    logger.info(f"  Offset map: {offset_path}")
    logger.info(f"  ID field: {collection_config['id_field']}")
    logger.info(f"  Workers: {collection_config.get('num_workers', mp.cpu_count())}")
    
    try:
        # Create offset map
        offset_file = OffsetFile(
            doc_path,
            key=lambda line: json.loads(line)[collection_config['id_field']],
            offset_fn=offset_path,
            num_workers=collection_config.get('num_workers', mp.cpu_count()),
            id_field=collection_config['id_field']
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Built offset map for {collection_config['name']} in {elapsed:.2f} seconds")
        logger.info(f"  Entries: {len(offset_file.pointer_dict):,}")
        
        # Close the file handle
        if hasattr(offset_file, 'fread'):
            offset_file.fread.close()
        
        return elapsed
        
    except Exception as e:
        logger.error(f"Failed to build offset map for {collection_config['name']}: {e}")
        logger.exception("Full traceback:")
        return 0.0


def prewarm_file(filepath: str, file_type: str = "file") -> float:
    """Load file into OS cache and return time taken."""
    start_time = time.time()
    filepath = Path(filepath)
    
    if not filepath.exists():
        logger.warning(f"{filepath} does not exist")
        return 0.0
    
    file_size = filepath.stat().st_size
    logger.info(f"Pre-warming {file_type}: {filepath} ({file_size / 1e9:.2f} GB)...")
    
    try:
        with open(filepath, 'rb') as f:
            # Use memory mapping for efficient loading
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                # Touch every page to load into cache
                chunk_size = 100 * 1024 * 1024  # 100MB chunks
                
                for i in range(0, len(m), chunk_size):
                    # Just access the memory to trigger page loading
                    _ = m[i:min(i+chunk_size, len(m))]
                    
                    # Show progress for large files
                    if file_size > 1e9:  # > 1GB
                        progress = (i / len(m)) * 100
                        print(f"  Progress: {progress:.1f}%", end='\r', flush=True)
                
                if file_size > 1e9:
                    print()  # New line after progress
                    
    except Exception as e:
        logger.error(f"Error pre-warming {filepath}: {e}")
        return 0.0
    
    elapsed = time.time() - start_time
    logger.info(f"Pre-warmed {file_type} in {elapsed:.2f} seconds")
    return elapsed


def prewarm_colbert_index_files(index_path: Path) -> float:
    """Pre-warm COLBERT index files into OS cache."""
    start_time = time.time()
    patterns = ["*.pt", "*.json", "*.faiss", "*.pkl", "*.npz"]
    total_size = 0
    file_count = 0
    
    for pattern in patterns:
        for filepath in index_path.glob(pattern):
            if filepath.is_file():
                file_size = filepath.stat().st_size
                # Pre-warm files larger than 10MB
                if file_size > 10 * 1024 * 1024:
                    logger.info(f"  Pre-warming {filepath.name} ({file_size / 1e9:.2f} GB)")
                    try:
                        with open(filepath, 'rb') as f:
                            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                                chunk_size = 100 * 1024 * 1024
                                for i in range(0, len(m), chunk_size):
                                    _ = m[i:min(i+1, len(m))]
                        total_size += file_size
                        file_count += 1
                    except Exception as e:
                        logger.debug(f"Could not pre-warm {filepath.name}: {e}")
    
    elapsed = time.time() - start_time
    logger.info(f"  Pre-warmed {file_count} index files totaling {total_size / 1e9:.2f} GB in {elapsed:.2f} seconds")
    return elapsed


def prewarm_colbert_indices(config: dict) -> float:
    """Pre-warm all COLBERT index files."""
    total_time = 0.0
    
    services = config.get('services', [])
    for service in services:
        if service.get('engine') == 'PLAIDX' and 'config' in service:
            index_path = Path(service['config'].get('index_path', ''))
            if index_path.exists():
                logger.info(f"\nPre-warming COLBERT index for service: {service['name']}")
                service_time = prewarm_colbert_index_files(index_path)
                total_time += service_time
            else:
                logger.warning(f"Index path not found for service {service['name']}: {index_path}")
    
    return total_time


def process_collection(collection_config: dict) -> tuple:
    """Build offset map and pre-warm collection files."""
    collection_name = collection_config['name']
    total_time = 0.0
    
    logger.info(f"\nProcessing collection: {collection_name}")
    logger.info("=" * 60)
    
    # Step 1: Build offset map if needed
    offset_build_time = build_offset_map(collection_config)
    total_time += offset_build_time
    
    # Step 2: Pre-warm the document file
    doc_path = collection_config['doc_path']
    doc_warm_time = prewarm_file(doc_path, "document file")
    total_time += doc_warm_time
    
    # Step 3: Pre-warm the offset map
    offset_path = collection_config.get('cache_path')
    if not offset_path:
        offset_path = str(Path(doc_path).with_suffix(Path(doc_path).suffix + '.offsetmap'))
    
    if Path(offset_path).exists():
        offset_warm_time = prewarm_file(offset_path, "offset map")
        total_time += offset_warm_time
    
    return collection_name, total_time


def main(config_path: str):
    """Main function to build offset maps and pre-warm all collections."""
    logger.info(f"Starting preprocessing for {config_path}")
    
    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)
    
    collections = config.get('collections', [])
    if not collections:
        logger.warning("No collections found in config")
        return
    
    logger.info(f"\nProcessing {len(collections)} collections...")
    
    start_time = time.time()
    
    # Process collections (building offset maps is CPU intensive, so we limit parallelism)
    max_workers = min(2, len(collections))  # Max 2 parallel to avoid overwhelming the system
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for collection in collections:
            future = executor.submit(process_collection, collection)
            futures.append(future)
        
        # Collect results
        total_processing_time = 0.0
        successful_collections = []
        failed_collections = []
        
        for future in as_completed(futures):
            try:
                name, collection_time = future.result()
                total_processing_time += collection_time
                successful_collections.append(name)
            except Exception as e:
                logger.error(f"Error processing collection: {e}")
                failed_collections.append(str(e))
    
    # Pre-warm COLBERT indices
    logger.info("\n" + "=" * 60)
    logger.info("Pre-warming COLBERT indices...")
    colbert_time = prewarm_colbert_indices(config)
    total_processing_time += colbert_time
    
    total_elapsed = time.time() - start_time
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("PREPROCESSING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total elapsed time: {total_elapsed:.2f} seconds")
    logger.info(f"Total processing time: {total_processing_time:.2f} seconds")
    logger.info(f"Successful collections: {len(successful_collections)}")
    
    if successful_collections:
        for name in successful_collections:
            logger.info(f"  ✓ {name}")
    
    if failed_collections:
        logger.error(f"Failed collections: {len(failed_collections)}")
        for error in failed_collections:
            logger.error(f"  ✗ {error}")
        sys.exit(1)
    
    logger.info("\nAll offset maps built and caches warmed. Ready to start server!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python prewarm_cache.py <config.json>")
        sys.exit(1)
    
    main(sys.argv[1])