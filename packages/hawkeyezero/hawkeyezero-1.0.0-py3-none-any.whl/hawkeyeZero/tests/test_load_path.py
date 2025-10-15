import unittest
from unittest.mock import patch
from hawkeyeZero import HawkeyeZero

class TestLoadPath(unittest.TestCase):
    """Tests for _load_path method.
    
    This test suite validates the path loading functionality which constructs
    absolute paths from relative path components.
    """
    
    def test_load_path_correct_joining(self):
        """Test correct path joining.
        
        Verifies that _load_path correctly constructs absolute paths by joining
        directory paths with relative paths.
        
        Mocked dependencies:
            - os.path.dirname: Returns '/home/user/project'
            - os.path.abspath: Returns '/home/user/project/file.py'
            - os.path.join: Returns '/home/user/project/dataset'
            
        Expected behavior:
            - Should call os.path.abspath with the provided absolute path
            - Should call os.path.dirname to get directory
            - Should call os.path.join to combine paths
            - Should return the correctly joined path
        """
        hawkeye = HawkeyeZero()
        with patch('os.path.dirname') as mock_dirname, \
             patch('os.path.abspath') as mock_abspath, \
             patch('os.path.join') as mock_join:
            
            mock_abspath.return_value = '/home/user/project/file.py'
            mock_dirname.return_value = '/home/user/project'
            mock_join.return_value = '/home/user/project/dataset'
            
            result = hawkeye._load_path('/some/path', 'dataset')
            
            mock_abspath.assert_called_once_with('/some/path')
            mock_dirname.assert_called_once_with('/home/user/project/file.py')
            mock_join.assert_called_once_with('/home/user/project', 'dataset')
            self.assertEqual(result, '/home/user/project/dataset')