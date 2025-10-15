"""Tests for PyMolFold plugin functionality"""
import os
import pytest
from unittest.mock import Mock, patch, ANY
from pathlib import Path
import tempfile

# Mock PyMOL cmd module
class MockCmd:
    def extend(self, name, func):
        pass
    def load(self, filename):
        pass
    def do(self, command):
        pass
    
# Replace PyMOL's cmd with our mock
import sys
sys.modules['pymol'] = Mock()
sys.modules['pymol.cmd'] = MockCmd()

# Now we can import our module
from pymolfold.version import __version__
from pymolfold import utils
import pymolfold.plugin as plugin
from pymolfold.predictors import (
    Boltz2Predictor,
    ESM3Predictor,
    # ESMFoldPredictor,
    # PyMolFoldPredictor
)

# Test data
TEST_SEQUENCE = "GGFTRGGFFHKYTREWQ"
MOCK_PDB = """
ATOM      1  N   GLY A   1      -5.210  14.804   3.635  1.00  0.62           N  
ATOM      2  CA  GLY A   1      -4.219  13.812   3.250  1.00  0.62           C  
ATOM      3  C   GLY A   1      -4.703  12.877   2.158  1.00  0.62           C  
ATOM      4  O   GLY A   1      -5.906  12.769   1.914  1.00  0.62           O  
ATOM      5  N   GLY A   2      -4.585  12.624   1.619  1.00  0.64           N  
ATOM      6  CA  GLY A   2      -4.750  11.750   0.469  1.00  0.64           C  
ATOM      7  C   GLY A   2      -4.608  10.279   0.812  1.00  0.64           C  
ATOM      8  O   GLY A   2      -3.847   9.917   1.711  1.00  0.64           O  
ATOM      9  N   PHE A   3      -5.008   9.624   0.650  1.00  0.68           N  
ATOM     10  CA  PHE A   3      -5.031   8.188   0.898  1.00  0.68           C  
ATOM     11  C   PHE A   3      -4.232   7.442  -0.163  1.00  0.68           C  
ATOM     12  CB  PHE A   3      -6.472   7.669   0.931  1.00  0.68           C  
ATOM     13  O   PHE A   3      -4.321   7.758  -1.351  1.00  0.68           O  
ATOM     14  CG  PHE A   3      -6.962   7.321   2.311  1.00  0.68           C  
ATOM     15  CD1 PHE A   3      -6.665   6.088   2.878  1.00  0.68           C  
ATOM     16  CD2 PHE A   3      -7.719   8.228   3.041  1.00  0.68           C  
ATOM     17  CE1 PHE A   3      -7.116   5.763   4.155  1.00  0.68           C  
ATOM     18  CE2 PHE A   3      -8.173   7.910   4.318  1.00  0.68           C  
ATOM     19  CZ  PHE A   3      -7.872   6.677   4.873  1.00  0.68           C  
ATOM     20  N   THR A   4      -3.956   7.003  -0.072  1.00  0.71           N  
ATOM     21  CA  THR A   4      -2.891   6.188  -0.645  1.00  0.71           C  
ATOM     22  C   THR A   4      -3.468   5.088  -1.532  1.00  0.71           C  
ATOM     23  CB  THR A   4      -2.017   5.557   0.456  1.00  0.71           C  
ATOM     24  O   THR A   4      -4.559   4.578  -1.267  1.00  0.71           O  
ATOM     25  CG2 THR A   4      -0.836   6.457   0.803  1.00  0.71           C  
ATOM     26  OG1 THR A   4      -2.811   5.355   1.631  1.00  0.71           O  
ATOM     27  N   ARG A   5      -3.175   4.693  -2.139  1.00  0.79           N  
ATOM     28  CA  ARG A   5      -3.312   3.688  -3.188  1.00  0.79           C  
ATOM     29  C   ARG A   5      -3.060   2.287  -2.639  1.00  0.79           C  
ATOM     30  CB  ARG A   5      -2.351   3.979  -4.342  1.00  0.79           C  
ATOM     31  O   ARG A   5      -2.503   2.132  -1.551  1.00  0.79           O  
ATOM     32  CG  ARG A   5      -2.978   4.766  -5.482  1.00  0.79           C  
ATOM     33  CD  ARG A   5      -2.035   4.885  -6.671  1.00  0.79           C  
ATOM     34  NE  ARG A   5      -2.513   5.865  -7.642  1.00  0.79           N  
ATOM     35  NH1 ARG A   5      -0.827   5.477  -9.173  1.00  0.79           N  
ATOM     36  NH2 ARG A   5      -2.448   7.036  -9.617  1.00  0.79           N  
ATOM     37  CZ  ARG A   5      -1.928   6.124  -8.808  1.00  0.79           C  
ATOM     38  N   GLY A   6      -3.134   1.533  -2.687  1.00  0.83           N  
ATOM     39  CA  GLY A   6      -3.094   0.117  -2.359  1.00  0.83           C  
ATOM     40  C   GLY A   6      -1.688  -0.400  -2.118  1.00  0.83           C  
ATOM     41  O   GLY A   6      -0.709   0.289  -2.410  1.00  0.83           O  
ATOM     42  N   GLY A   7      -1.317  -1.044  -1.624  1.00  0.86           N  
ATOM     43  CA  GLY A   7      -0.059  -1.703  -1.312  1.00  0.86           C  
ATOM     44  C   GLY A   7      -0.234  -2.967  -0.492  1.00  0.86           C  
ATOM     45  O   GLY A   7      -1.349  -3.297  -0.081  1.00  0.86           O 
"""

@pytest.fixture
def temp_workdir():
    """Create a temporary working directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_path = plugin.ABS_PATH
        plugin.ABS_PATH = tmpdir
        yield Path(tmpdir)
        plugin.ABS_PATH = original_path

@pytest.fixture
def mock_predictors():
    """Mock all predictors"""
    with patch('pymolfold.predictors.Boltz2Predictor') as mock_boltz, \
         patch('pymolfold.predictors.ESM3Predictor') as mock_esm3:
        #  patch('pymolfold.predictors.ESMFoldPredictor') as mock_esmfold, \
        #  patch('pymolfold.predictors.PyMolFoldPredictor') as mock_pymolfold:
        
        # Setup mock returns
        for mock in [mock_boltz, mock_esm3]: #, mock_esmfold, mock_pymolfold]:
            mock.return_value.predict.return_value = {
                'structures': [{
                    'structure': MOCK_PDB,
                    'source': 'test_prediction'
                }]
            }
        yield {
            'boltz2': mock_boltz,
            'esm3': mock_esm3,
            # 'esmfold': mock_esmfold,
            # 'pymolfold': mock_pymolfold
        }

def test_set_workdir(temp_workdir):
    """Test setting working directory"""
    test_path = "/test/path"
    plugin.set_workdir(test_path)
    assert plugin.ABS_PATH == test_path

    # Test expanding home directory
    plugin.set_workdir("~/test")
    assert plugin.ABS_PATH == os.path.expanduser("~/test")

def test_clean_sequence():
    """Test sequence cleaning function"""
    test_cases = [
        ("ABC/DEF", "ABC:DEF"),
        ("abc", "ABC"),
        ("A B C", "ABC"),
        ("A::B", "A:B"),
        (":::ABC:::", "ABC"),
    ]
    for input_seq, expected in test_cases:
        assert utils.clean_sequence(input_seq) == expected

def test_boltz2_prediction(temp_workdir, mock_predictors):
    """Test Boltz2 structure prediction"""
    plugin.query_boltz2(TEST_SEQUENCE, name="test")
    
    mock_predictor = mock_predictors['boltz2'].return_value
    mock_predictor.predict.assert_called_once()
    
    # Check that prediction was made with correct sequence
    args, kwargs = mock_predictor.predict.call_args
    assert utils.clean_sequence(TEST_SEQUENCE) == args[0]
    
    # Check that structure was saved
    output_file = temp_workdir / "test_prediction.cif"
    assert output_file.exists()

def test_esm3_prediction(temp_workdir, mock_predictors):
    """Test ESM3 structure prediction"""
    plugin.query_esm3(
        TEST_SEQUENCE,
        name="test",
        temperature=0.8,
        num_steps=10,
        model_name="esm3-small"
    )
    
    mock_predictor = mock_predictors['esm3'].return_value
    mock_predictor.predict.assert_called_once()
    
    # Check parameters were passed correctly
    args, kwargs = mock_predictor.predict.call_args
    assert kwargs['temperature'] == 0.8
    assert kwargs['num_steps'] == 10
    assert kwargs['model_name'] == "esm3-small"

# def test_esmfold_prediction(temp_workdir, mock_predictors):
#     """Test ESMFold prediction with failover"""
#     # Test successful prediction
#     plugin.query_esmfold(TEST_SEQUENCE, name="test")
#     mock_predictors['esmfold'].return_value.predict.assert_called_once()
    
#     # Test failover to PyMolFold
#     mock_predictors['esmfold'].return_value.predict.side_effect = RuntimeError(
#         "internal server error"
#     )
#     plugin.query_esmfold(TEST_SEQUENCE, name="test_failover")
#     mock_predictors['pymolfold'].return_value.predict.assert_called_once()

# def test_pymolfold_prediction(temp_workdir, mock_predictors):
#     """Test PyMolFold server prediction"""
#     plugin.query_pymolfold(TEST_SEQUENCE, name="test")
#     mock_predictors['pymolfold'].return_value.predict.assert_called_once()

def test_error_handling(temp_workdir, mock_predictors):
    """Test error handling in prediction functions"""
    # Setup mock to raise an error
    mock_predictors['boltz2'].return_value.predict.side_effect = Exception("Test error")
    
    # Should not raise but print error
    plugin.query_boltz2(TEST_SEQUENCE)
    
    # No files should have been created
    assert len(list(temp_workdir.iterdir())) == 0

def test_plugin_initialization():
    """Test plugin initialization and command registration"""
    with patch('pymol.cmd') as mock_cmd:
        plugin.__init_plugin__()
        
        # Check that all commands were registered
        expected_commands = [
            'boltz2', 'esm3', #'esmfold', 'pymolfold',
            'set_workdir', 'set_base_url', 'color_plddt',
            'fetch_am', 'fetch_af'
        ]
        
        assert mock_cmd.extend.call_count >= len(expected_commands)
        for cmd_name in expected_commands:
            mock_cmd.extend.assert_any_call(cmd_name, ANY)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])