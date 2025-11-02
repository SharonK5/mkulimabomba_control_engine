print("=== SYSTEM TEST ===")

# Test basic Python
import sys
print(f"Python version: {sys.version}")

# Test imports
try:
    import fastapi
    print("✓ FastAPI: OK")
except ImportError as e:
    print(f"✗ FastAPI: {e}")

try:
    import sqlalchemy
    print("✓ SQLAlchemy: OK")
except ImportError as e:
    print(f"✗ SQLAlchemy: {e}")

try:
    import pydantic
    print("✓ Pydantic: OK")
except ImportError as e:
    print(f"✗ Pydantic: {e}")

try:
    from app.main import app
    print("✓ Main app: OK")
except Exception as e:
    print(f"✗ Main app: {e}")

print("=== TEST COMPLETE ===")
