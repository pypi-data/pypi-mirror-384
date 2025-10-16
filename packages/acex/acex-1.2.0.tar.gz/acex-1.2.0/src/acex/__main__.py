
"""
ACEX main module entry point
This file is executed when running: python -m acex
"""

try:
    from acex.cli.main import app
    
    if __name__ == "__main__":
        app()
        
except ImportError:
    # Fallback if CLI dependencies are not available
    print("CLI dependencies not available. Install with: pip install acex[cli]")
    exit(1)