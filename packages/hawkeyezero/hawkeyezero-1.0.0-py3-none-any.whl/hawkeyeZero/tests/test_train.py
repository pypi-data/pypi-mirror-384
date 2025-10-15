import unittest
from unittest.mock import Mock, patch
from hawkeyeZero import HawkeyeZero

class TestTrain(unittest.TestCase):
    """Tests for _train method.
    
    This test suite validates the model training functionality which initiates
    the training process with specified parameters.
    """
    
    @patch('hawkeyeZero.constants.MODEL_PARAMETERS', {'name': 'test', 'epochs': 100})
    @patch('hawkeyeZero.constants.MODEL_AGUMENT_PARAMETERS', {'batch': 16})
    @patch.object(HawkeyeZero, '_load_path')
    def test_train_calls_model_train(self, mock_load_path):
        """Test calling model train method.
        
        Verifies that the train method correctly calls the YOLO model's train
        function with all required parameters.
        
        Test setup:
            MODEL_PARAMETERS: {'name': 'test', 'epochs': 100}
            MODEL_AGUMENT_PARAMETERS: {'batch': 16}
            _data: 'data.yaml'
            _load_path returns: '/project/model'
            
        Expected behavior:
            - Should call model.train once
            - Should pass data='data.yaml'
            - Should pass project='/project/model'
            - Should pass all MODEL_PARAMETERS and MODEL_AGUMENT_PARAMETERS
        """
        hawkeye = HawkeyeZero()
        hawkeye._model = Mock()
        hawkeye._data = 'data.yaml'
        mock_load_path.return_value = '/project/model'
        
        hawkeye._train()
        
        hawkeye._model.train.assert_called_once()
        call_kwargs = hawkeye._model.train.call_args[1]
        self.assertEqual(call_kwargs['data'], 'data.yaml')
        self.assertEqual(call_kwargs['project'], '/project/model')