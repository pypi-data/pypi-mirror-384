import unittest
from unittest.mock import Mock
from hawkeyeZero import HawkeyeZero

class TestExport(unittest.TestCase):
    """Tests for export method.
    
    This test suite validates the model export functionality which converts
    the trained model to different formats for deployment.
    """
    
    def test_export_calls_model_export(self):
        """Test calling model export method.
        
        Verifies that the export method correctly passes export parameters
        to the YOLO model's export function.
        
        Test setup:
            _model: Mock object
            export_args: {'format': 'onnx', 'imgsz': 640}
            
        Expected behavior:
            - Should call model.export once with the provided arguments
        """
        hawkeye = HawkeyeZero()
        hawkeye._model = Mock()
        export_args = {'format': 'onnx', 'imgsz': 640}
        
        hawkeye.export(export_args)
        
        hawkeye._model.export.assert_called_once_with(**export_args)
    
    def test_export_with_empty_args(self):
        """Test export with empty arguments.
        
        Verifies that the export method handles the case where no export
        arguments are provided.
        
        Test setup:
            _model: Mock object
            export_args: {}
            
        Expected behavior:
            - Should call model.export once with no arguments
        """
        hawkeye = HawkeyeZero()
        hawkeye._model = Mock()
        
        hawkeye.export({})
        
        hawkeye._model.export.assert_called_once_with()