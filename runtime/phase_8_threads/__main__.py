"""
Phase 8 - Multi-thread Chat Support
Main entry point for thread management.
"""
from .threads import ThreadManager

def main():
    """Run the thread manager."""
    manager = ThreadManager()
    thread_id = manager.create_thread()
    return {"thread_id": thread_id}

if __name__ == "__main__":
    main()
