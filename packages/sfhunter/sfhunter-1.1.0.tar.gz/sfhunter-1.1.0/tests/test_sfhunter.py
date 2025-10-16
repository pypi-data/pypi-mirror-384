#!/usr/bin/env python3
"""
Basic tests for SFHunter
"""

import unittest
import sys
import os

# Add the parent directory to the path to import sfhunter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sfhunter import SFHunter

class TestSFHunter(unittest.TestCase):
    """Test cases for SFHunter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.detector = SFHunter()
    
    def test_initialization(self):
        """Test SFHunter initialization"""
        self.assertIsNotNone(self.detector)
        self.assertIsNotNone(self.detector.config)
        self.assertIsNotNone(self.detector.session)
    
    def test_normalize_url(self):
        """Test URL normalization"""
        # Test URL with protocol
        urls = self.detector.normalize_url("https://example.com")
        self.assertEqual(urls, ["https://example.com"])
        
        # Test URL without protocol
        urls = self.detector.normalize_url("example.com")
        self.assertEqual(urls, ["http://example.com", "https://example.com"])
    
    def test_is_salesforce_url(self):
        """Test Salesforce URL detection"""
        # Test Salesforce URL
        self.assertTrue(self.detector.is_salesforce_url("https://mycompany.my.salesforce.com"))
        
        # Test non-Salesforce URL
        self.assertFalse(self.detector.is_salesforce_url("https://example.com"))
    
    def test_check_salesforce_headers(self):
        """Test Salesforce header detection"""
        import requests
        
        # Create a mock response with Salesforce headers
        class MockResponse:
            def __init__(self):
                self.headers = {
                    'X-SFDC-Request-ID': 'test123',
                    'Server': 'sfdcedge'
                }
        
        response = MockResponse()
        is_salesforce, signals = self.detector.check_salesforce_headers(response)
        
        self.assertTrue(is_salesforce)
        self.assertIn('SFDC Request ID', signals)
        self.assertIn('Salesforce Edge Server', signals)
    
    def test_check_salesforce_content(self):
        """Test Salesforce content detection"""
        # Test content with Salesforce indicators
        content = "This is a Salesforce Lightning application with Aura framework"
        is_salesforce, signals = self.detector.check_salesforce_content(content)
        
        self.assertTrue(is_salesforce)
        self.assertIn('Aura/Lightning', signals)
        self.assertIn('Salesforce Branding', signals)
    
    def test_create_detection_result(self):
        """Test detection result creation"""
        result = self.detector.create_detection_result(
            "https://example.com",
            "https://mycompany.my.salesforce.com",
            ["https://example.com", "https://mycompany.my.salesforce.com"],
            "redirect_chain",
            ["Salesforce Domain"]
        )
        
        self.assertEqual(result['original_url'], "https://example.com")
        self.assertEqual(result['final_url'], "https://mycompany.my.salesforce.com")
        self.assertEqual(result['detection_method'], "redirect_chain")
        self.assertEqual(result['signals'], ["Salesforce Domain"])
        self.assertEqual(result['status'], "detected")

if __name__ == '__main__':
    unittest.main()
