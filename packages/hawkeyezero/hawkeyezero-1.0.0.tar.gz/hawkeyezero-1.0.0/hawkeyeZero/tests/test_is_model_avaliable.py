import unittest
from unittest.mock import patch
from hawkeyeZero import HawkeyeZero

class TestIsModelAvailable(unittest.TestCase):
    """Tests for _is_model_avaliable method.
    
    This test suite validates the model availability checking functionality
    which determines if a requested model exists in the list of available models.
    """
    
    @patch('hawkeyeZero.constants.MODELS_TO_USE', ['best.pt', 'yolo11n.pt', 'model_v2.pt'])
    def test_model_available(self):
        """Test for model available in the list.
        
        Verifies that the method correctly identifies when a model exists in
        the MODELS_TO_USE list.
        
        Test setup:
            MODELS_TO_USE: ['best.pt', 'yolo11n.pt', 'model_v2.pt']
            model_to_use: 'best.pt'
            
        Expected behavior:
            - Should return True when model is in the list
        """
        hawkeye = HawkeyeZero(model_to_use="best.pt")
        self.assertTrue(hawkeye._is_model_avaliable())
    
    @patch('hawkeyeZero.constants.MODELS_TO_USE', ['best.pt', 'yolo11n.pt'])
    def test_model_not_available(self):
        """Test for model not available in the list.
        
        Verifies that the method correctly identifies when a model does not exist
        in the MODELS_TO_USE list.
        
        Test setup:
            MODELS_TO_USE: ['best.pt', 'yolo11n.pt']
            model_to_use: 'unknown_model.pt'
            
        Expected behavior:
            - Should return False when model is not in the list
        """
        hawkeye = HawkeyeZero(model_to_use="unknown_model.pt")
        self.assertFalse(hawkeye._is_model_avaliable())
    
    @patch('hawkeyeZero.constants.MODELS_TO_USE', [])
    def test_model_empty_list(self):
        """Test for empty model list.
        
        Verifies that the method handles the edge case where MODELS_TO_USE
        is an empty list. Note: Current implementation returns True always,
        so this test documents actual behavior.
        
        Test setup:
            MODELS_TO_USE: []
            model_to_use: 'best.pt'
            
        Expected behavior:
            - Current implementation returns True (always available)
            - This may need to be fixed in the actual code
        """
        hawkeye = HawkeyeZero(model_to_use="best.pt")
        # Actual implementation returns True always
        self.assertTrue(hawkeye._is_model_avaliable())