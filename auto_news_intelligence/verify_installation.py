#!/usr/bin/env python3
"""Verification script to test all new components"""

import sys

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import url_manager
        print("✓ url_manager imported successfully")
    except Exception as e:
        print(f"✗ url_manager import failed: {e}")
        return False
    
    try:
        import pipeline_runner
        print("✓ pipeline_runner imported successfully")
    except Exception as e:
        print(f"✗ pipeline_runner import failed: {e}")
        return False
    
    try:
        from pipeline import classifier, deduplicator
        print("✓ pipeline modules imported successfully")
    except Exception as e:
        print(f"✗ pipeline modules import failed: {e}")
        return False
    
    return True


def test_url_manager():
    """Test URL manager functions"""
    print("\nTesting URL manager...")
    
    try:
        import url_manager
        
        # Test parse_urls_from_text
        test_text = """
        https://example.com/article1
        https://example.com/article2
        Some text https://example.com/article3 more text
        """
        urls = url_manager.parse_urls_from_text(test_text)
        assert len(urls) == 3, f"Expected 3 URLs, got {len(urls)}"
        print(f"✓ parse_urls_from_text works (found {len(urls)} URLs)")
        
        # Test load_master_urls (should work even if file doesn't exist)
        existing = url_manager.load_master_urls()
        print(f"✓ load_master_urls works (found {len(existing)} existing URLs)")
        
        return True
    except Exception as e:
        print(f"✗ URL manager test failed: {e}")
        return False


def test_deduplicator():
    """Test enhanced deduplicator functions"""
    print("\nTesting enhanced deduplicator...")
    
    try:
        from pipeline.deduplicator import extract_named_entities, compute_cluster_coherence
        import numpy as np
        
        # Test entity extraction
        text = "Tesla Model 3 2024 price announced"
        entities = extract_named_entities(text)
        assert 'tesla' in entities, "Should extract 'tesla'"
        assert '2024' in entities, "Should extract '2024'"
        print(f"✓ extract_named_entities works (found {len(entities)} entities)")
        
        # Test coherence computation
        sim_matrix = np.array([[1.0, 0.9], [0.9, 1.0]])
        coherence = compute_cluster_coherence([0, 1], sim_matrix)
        assert 0.0 <= coherence <= 1.0, "Coherence should be between 0 and 1"
        print(f"✓ compute_cluster_coherence works (score: {coherence:.2f})")
        
        return True
    except Exception as e:
        print(f"✗ Deduplicator test failed: {e}")
        return False


def test_classifier():
    """Test classifier with cluster_reason"""
    print("\nTesting enhanced classifier...")
    
    try:
        from pipeline.classifier import Classifier
        
        # Check that _generate_cluster_reason method exists
        assert hasattr(Classifier, '_generate_cluster_reason'), \
            "Classifier should have _generate_cluster_reason method"
        print("✓ Classifier has _generate_cluster_reason method")
        
        return True
    except Exception as e:
        print(f"✗ Classifier test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("AUTO NEWS INTELLIGENCE v2.0 - VERIFICATION")
    print("=" * 60)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
        print("\n⚠ Import test failed. Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Test URL manager
    if not test_url_manager():
        all_passed = False
    
    # Test deduplicator
    if not test_deduplicator():
        all_passed = False
    
    # Test classifier
    if not test_classifier():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nYou can now:")
        print("  1. Run the admin UI: streamlit run app_upload.py")
        print("  2. Or use command line: python3 runner.py")
    else:
        print("⚠ SOME TESTS FAILED")
        print("Please check the errors above and fix them.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
