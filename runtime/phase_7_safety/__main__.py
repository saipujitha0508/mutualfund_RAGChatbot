"""
Phase 7 - Safety and Refusal
Main entry point for the safety layer.
"""
from .safety import SafetyLayer

def main():
    """Run the safety layer."""
    safety = SafetyLayer()
    # Test with a sample query
    should_answer, reason = safety.should_answer("What is the expense ratio?")
    return {"should_answer": should_answer, "reason": reason}

if __name__ == "__main__":
    main()
