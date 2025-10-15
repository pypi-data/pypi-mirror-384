import unittest
from unittest.mock import Mock
from hawkeyeZero import HawkeyeZero

class TestVal(unittest.TestCase):
    """Tests for val method.
    
    This test suite validates the model validation functionality which evaluates
    the model's performance on a validation dataset.
    """
    
    def test_val_calls_model_val(self):
        """Test calling model validation method.
        
        Verifies that the val method correctly calls the YOLO model's validation
        function with the dataset configuration.
        
        Test setup:
            _model: Mock object
            _data: 'data.yaml'
            
        Expected behavior:
            - Should call model.val once with 'data.yaml'
        """
        hawkeye = HawkeyeZero()
        hawkeye._model = Mock()
        hawkeye._data = 'data.yaml'
        
        hawkeye.val()
        
        hawkeye._model.val.assert_called_once_with('data.yaml')