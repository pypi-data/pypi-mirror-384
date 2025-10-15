import unittest
from unittest.mock import Mock, patch
from hawkeyeZero import HawkeyeZero

class TestUseModel(unittest.TestCase):
    """Tests for use_model method.
    
    This test suite validates the main model usage functionality which handles
    both development and production modes, processes input data, and optionally
    displays results.
    """
    
    @patch.object(HawkeyeZero, '_load_yolo')
    def test_use_model_empty_input_no_dev_mode(self, mock_load_yolo):
        """Test using model without input data and dev mode.
        
        Verifies that when input_data is None and dev mode is disabled,
        an appropriate error message is returned.
        
        Test setup:
            is_dev_mode: False
            input_data: None
            
        Expected behavior:
            - Should call _load_yolo once
            - Should return "Empty input_data parameter."
        """
        hawkeye = HawkeyeZero(is_dev_mode=False)
        result = hawkeye.use_model(input_data=None)
        
        self.assertEqual(result, "Empty input_data parameter.")
        mock_load_yolo.assert_called_once()
    
    @patch.object(HawkeyeZero, '_draw_ui_detection_results')
    @patch.object(HawkeyeZero, '_load_yolo')
    @patch.object(HawkeyeZero, '_train')
    @patch.object(HawkeyeZero, '_load_path')
    def test_use_model_dev_mode(self, mock_load_path, mock_train, mock_load_yolo, mock_draw):
        """Test using model in developer mode.
        
        Verifies that when dev mode is enabled, the model is trained
        using the dataset configuration.
        
        Test setup:
            is_dev_mode: True
            _load_path returns: 'dataset/data.yaml'
            
        Expected behavior:
            - Should call _load_yolo once
            - Should call _train once
            - _data should be set to 'dataset/data.yaml'
        """
        hawkeye = HawkeyeZero(is_dev_mode=True)
        hawkeye._model = Mock()  # Mock the model to prevent NoneType error
        mock_load_path.return_value = 'dataset/data.yaml'
        mock_results = [Mock()]
        hawkeye._model.return_value = mock_results
        
        result = hawkeye.use_model()
        
        mock_load_yolo.assert_called_once()
        mock_train.assert_called_once()
        self.assertEqual(hawkeye._data, 'dataset/data.yaml')
        # In dev mode with no input_data, it still tries to run model(None)
        hawkeye._model.assert_called_once_with(None)
    
    @patch.object(HawkeyeZero, '_load_yolo')
    @patch.object(HawkeyeZero, '_draw_ui_detection_results')
    def test_use_model_with_input_display_true(self, mock_draw, mock_load_yolo):
        """Test using model with data and display enabled.
        
        Verifies that when input data is provided and display_results is True,
        the model performs detection and displays the results.
        
        Test setup:
            input_data: 'image.jpg'
            display_results: True
            
        Expected behavior:
            - Should call _load_yolo once
            - Should call model with 'image.jpg'
            - Should call _draw_ui_detection_results with first result
            - Should return the detection results
        """
        hawkeye = HawkeyeZero()
        hawkeye._model = Mock()
        mock_results = [Mock()]
        hawkeye._model.return_value = mock_results
        
        result = hawkeye.use_model(input_data="image.jpg", display_results=True)
        
        mock_load_yolo.assert_called_once()
        hawkeye._model.assert_called_once_with("image.jpg")
        mock_draw.assert_called_once_with(mock_results[0])
        self.assertEqual(result, mock_results)
    
    @patch.object(HawkeyeZero, '_load_yolo')
    @patch.object(HawkeyeZero, '_draw_ui_detection_results')
    def test_use_model_with_input_display_false(self, mock_draw, mock_load_yolo):
        """Test using model without display.
        
        Verifies that when display_results is False, the model performs
        detection but does not display the results.
        
        Test setup:
            input_data: 'image.jpg'
            display_results: False
            
        Expected behavior:
            - Should call model with 'image.jpg'
            - Should NOT call _draw_ui_detection_results
            - Should return the detection results
        """
        hawkeye = HawkeyeZero()
        hawkeye._model = Mock()
        mock_results = [Mock()]
        hawkeye._model.return_value = mock_results
        
        result = hawkeye.use_model(input_data="image.jpg", display_results=False)
        
        mock_draw.assert_not_called()
        self.assertEqual(result, mock_results)