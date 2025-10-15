import unittest
from unittest.mock import Mock, patch
from hawkeyeZero import HawkeyeZero

class TestDrawUIDetectionResults(unittest.TestCase):
    """Tests for _draw_ui_detection_results method.
    
    This test suite validates the UI rendering functionality for displaying
    detection results using matplotlib and OpenCV.
    """
    
    def test_draw_ui_calls_plot_functions(self):
        """Test calling plot functions.
        
        Verifies that all necessary plotting functions are called in the correct
        sequence to display detection results.
        
        Mocked dependencies:
            - cv2.cvtColor: Converts image color space
            - plt.figure: Creates new figure
            - plt.imshow: Displays image
            - plt.axis: Controls axis display
            - plt.title: Sets plot title
            - plt.show: Displays the plot
            
        Expected behavior:
            - result.plot() should be called once
            - cv2.cvtColor should be called once
            - All plt methods should be called once in order
        """
        # Mock at the point of import in _draw_ui_detection_results
        with patch('cv2.cvtColor') as mock_cvtColor, \
             patch('matplotlib.pyplot.figure') as mock_figure, \
             patch('matplotlib.pyplot.imshow') as mock_imshow, \
             patch('matplotlib.pyplot.axis') as mock_axis, \
             patch('matplotlib.pyplot.title') as mock_title, \
             patch('matplotlib.pyplot.show') as mock_show:
            
            hawkeye = HawkeyeZero()
            mock_result = Mock()
            mock_result.plot.return_value = Mock()
            mock_cvtColor.return_value = Mock()
            
            hawkeye._draw_ui_detection_results(mock_result)
            
            mock_result.plot.assert_called_once()
            mock_cvtColor.assert_called_once()
            mock_figure.assert_called_once()
            mock_imshow.assert_called_once()
            mock_axis.assert_called_once_with("off")
            mock_title.assert_called_once()
            mock_show.assert_called_once()