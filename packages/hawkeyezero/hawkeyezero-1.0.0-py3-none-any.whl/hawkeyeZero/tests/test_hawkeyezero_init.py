import unittest
from hawkeyeZero import HawkeyeZero

class TestHawkeyeZeroInit(unittest.TestCase):
    """Tests for HawkeyeZero object initialization.
    
    This test suite validates the proper initialization of HawkeyeZero objects
    with various parameter combinations.
    """
    
    def test_init_default_parameters(self):
        """Test initialization with default parameters.
        
        Verifies that HawkeyeZero object is created with correct default values
        when no parameters are provided.
        
        Expected behavior:
            - is_dev_mode should be False
            - model_to_use should be "best.pt"
            - _model should be None
            - _data should be None
        """
        hawkeye = HawkeyeZero()
        self.assertFalse(hawkeye.is_dev_mode)
        self.assertEqual(hawkeye.model_to_use, "best.pt")
        self.assertIsNone(hawkeye._model)
        self.assertIsNone(hawkeye._data)
    
    def test_init_custom_parameters(self):
        """Test initialization with custom parameters.
        
        Validates that HawkeyeZero accepts and properly sets custom parameters
        during initialization.
        
        Args:
            is_dev_mode (bool): Set to True for testing
            model_to_use (str): Set to "yolo11n.pt" for testing
            
        Expected behavior:
            - is_dev_mode should be True
            - model_to_use should be "yolo11n.pt"
        """
        hawkeye = HawkeyeZero(is_dev_mode=True, model_to_use="yolo11n.pt")
        self.assertTrue(hawkeye.is_dev_mode)
        self.assertEqual(hawkeye.model_to_use, "yolo11n.pt")
    
    def test_init_dev_mode_only(self):
        """Test initialization with only dev mode enabled.
        
        Verifies that when only dev mode is specified, other parameters retain
        their default values.
        
        Args:
            is_dev_mode (bool): Set to True for testing
            
        Expected behavior:
            - is_dev_mode should be True
            - model_to_use should default to "best.pt"
        """
        hawkeye = HawkeyeZero(is_dev_mode=True)
        self.assertTrue(hawkeye.is_dev_mode)
        self.assertEqual(hawkeye.model_to_use, "best.pt")