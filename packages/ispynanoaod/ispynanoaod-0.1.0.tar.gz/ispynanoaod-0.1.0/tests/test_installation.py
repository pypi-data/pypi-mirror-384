#!/usr/bin/env python
"""
Test script to verify installation works.
"""

def test_basic_import():
    """Test basic package import."""
    print("Testing basic import...")
    try:
        import ispynanoaod 
        print("Package import successful!")
        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

def test_components():
    """Test importing individual components."""
    print("\nTesting component imports...")
    
    try:
        from ispynanoaod import EventDisplay, DataLoader
        print("Core components imported!")
        
        # Test creating instances
        display = EventDisplay(width=400, height=300)
        loader = DataLoader()
        
        print("Component instances created!")
        return True
        
    except Exception as e:
        print(f"Component test failed: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies are available."""
    print("\nTesting dependencies...")
    
    deps = ['uproot', 'awkward', 'numpy', 'pythreejs', 'ipywidgets', 'IPython']
    missing = []
    
    for dep in deps:
        try:
            __import__(dep)
            print(f"{dep}")
        except ImportError:
            print(f"{dep} - MISSING")
            missing.append(dep)
    
    if missing:
        print(f"\nInstall missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    print("ispynanoaod Installation Test")
    print("=" * 40)
    
    # Run tests
    import_ok = test_basic_import()
    deps_ok = test_dependencies()
    
    if import_ok and deps_ok:
        components_ok = test_components()
    else:
        components_ok = False
    
    print("\n" + "=" * 40)
    if import_ok and deps_ok and components_ok:
        print("All tests passed! Installation successful!")
        print("\nYou can now use:")
        print("import ispynanaod")
        print("display = ispynanoaod.EventDisplay()")
    else:
        print("Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
