"""Test MetaLogger import for backward compatibility."""


def test_meta_logger_import():
    """Test that MetaLogger can be imported from logger_local package."""
    try:
        from logger_local.src.meta_logger import MetaLogger
        assert MetaLogger is not None
        print("✓ MetaLogger import from logger_local.src.MetaLogger works")
    except ImportError as e:
        print(f"✗ MetaLogger import failed: {e}")
        raise

    try:
        from logger_local import MetaLogger
        assert MetaLogger is not None
        print("✓ MetaLogger import from logger_local works")
    except ImportError as e:
        print(f"✗ MetaLogger import failed: {e}")
        raise


if __name__ == "__main__":
    test_meta_logger_import()
# To run the test, execute: python test_meta_logger_import.py
