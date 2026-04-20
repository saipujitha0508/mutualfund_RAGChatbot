"""
Local Scheduler
Runs the ingest pipeline locally with logging for debugging.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_phase(phase_name: str, module_path: str):
    """Run a single phase of the ingest pipeline."""
    logger.info(f"{'='*60}")
    logger.info(f"Starting Phase: {phase_name}")
    logger.info(f"{'='*60}")
    
    try:
        # Import and run the phase - import the __main__ submodule
        full_module_path = f"{module_path}.__main__"
        module = __import__(full_module_path, fromlist=['main'])
        result = module.main()
        
        logger.info(f"Phase {phase_name} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Phase {phase_name} failed: {str(e)}", exc_info=True)
        raise


def run_ingest_pipeline():
    """Run the complete ingest pipeline locally."""
    logger.info("Starting Local Ingest Pipeline")
    logger.info(f"Log file: {log_file}")
    
    phases = [
        ("Phase 4.0 - Scrape", "runtime.phase_4_0_scrape"),
        ("Phase 4.1 - Normalize", "runtime.phase_4_1_normalize"),
        ("Phase 4.2 - Chunk and Embed", "runtime.phase_4_2_chunk_embed"),
        ("Phase 4.3 - Index to Chroma", "runtime.phase_4_3_index"),
    ]
    
    results = {}
    
    for phase_name, module_path in phases:
        try:
            result = run_phase(phase_name, module_path)
            results[phase_name] = {
                'status': 'success',
                'result': result
            }
        except Exception as e:
            results[phase_name] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"Pipeline failed at {phase_name}. Stopping.")
            break
    
    # Summary
    logger.info(f"{'='*60}")
    logger.info("Pipeline Summary")
    logger.info(f"{'='*60}")
    
    for phase_name, result in results.items():
        status = result['status']
        logger.info(f"{phase_name}: {status}")
    
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_count = len(results)
    
    logger.info(f"\nTotal: {success_count}/{total_count} phases successful")
    
    if success_count == total_count:
        logger.info("Pipeline completed successfully!")
    else:
        logger.error("Pipeline failed. Check logs for details.")
    
    return results


def main():
    """Main entry point for local scheduler."""
    logger.info("Local Scheduler started")
    results = run_ingest_pipeline()
    logger.info("Local Scheduler finished")
    return results


if __name__ == "__main__":
    main()
