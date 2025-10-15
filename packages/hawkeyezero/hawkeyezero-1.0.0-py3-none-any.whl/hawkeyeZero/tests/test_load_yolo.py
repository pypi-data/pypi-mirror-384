import unittest
from unittest.mock import patch
from hawkeyeZero import HawkeyeZero

class TestLoadYolo(unittest.TestCase):
    """Tests for _load_yolo method.
    
    This test suite validates the YOLO model loading functionality which
    initializes the YOLO object with the appropriate model weights.
    """
    
    @patch('hawkeyeZero.model.YOLO')
    @patch('hawkeyeZero.constants.MODELS_TO_USE', ['yolo11n.pt'])
    @patch('hawkeyeZero.constants.MODEL_PARAMETERS', {'name': 'test_model'})
    def test_load_yolo_default_model(self, mock_yolo):
        """Test loading default YOLO model.
        
        Verifies that the default YOLO model (yolo11n.pt) is loaded correctly
        without constructing a full path.
        
        Test setup:
            MODELS_TO_USE: ['yolo11n.pt']
            MODEL_PARAMETERS: {'name': 'test_model'}
            model_to_use: 'yolo11n.pt'
            
        Expected behavior:
            - Should call YOLO with 'yolo11n.pt' directly
            - _model should not be None after loading
        """
        hawkeye = HawkeyeZero(model_to_use="yolo11n.pt")
        hawkeye._load_yolo()
        
        mock_yolo.assert_called_once_with("yolo11n.pt")
        self.assertIsNotNone(hawkeye._model)
    
    @patch('hawkeyeZero.model.YOLO')
    @patch('hawkeyeZero.constants.MODELS_TO_USE', ['best.pt'])
    @patch('hawkeyeZero.constants.MODEL_PARAMETERS', {'name': 'test_model'})
    def test_load_yolo_custom_model(self, mock_yolo):
        """Test loading custom model.
        
        Verifies that custom models are loaded with a full path constructed
        using the _load_path method.
        
        Test setup:
            MODELS_TO_USE: ['best.pt']
            MODEL_PARAMETERS: {'name': 'test_model'}
            model_to_use: 'best.pt'
            _load_path returns: '/path/to/model/best.pt'
            
        Expected behavior:
            - Should call YOLO with the full path '/path/to/model/best.pt'
        """
        hawkeye = HawkeyeZero(model_to_use="best.pt")
        with patch.object(hawkeye, '_load_path', return_value='/path/to/model/best.pt'):
            hawkeye._load_yolo()
            
            mock_yolo.assert_called_once_with('/path/to/model/best.pt')
    
    @patch('hawkeyeZero.model.YOLO')
    @patch('hawkeyeZero.constants.MODELS_TO_USE', ['yolo11n.pt'])
    def test_load_yolo_unavailable_model(self, mock_yolo):
        """Test attempting to load unavailable model.
        
        Verifies behavior when loading a model not in the available list.
        The _is_model_available method checks if model is in MODELS_TO_USE.
        
        Test setup:
            MODELS_TO_USE: ['yolo11n.pt']
            model_to_use: 'unavailable.pt'
            
        Expected behavior:
            - _is_model_available returns False
            - YOLO should not be called
            - _model should remain None
        """
        hawkeye = HawkeyeZero(model_to_use="unavailable.pt")
        hawkeye._load_yolo()
        
        # Model is not in MODELS_TO_USE, so YOLO should not be called
        mock_yolo.assert_not_called()
        self.assertIsNone(hawkeye._model)