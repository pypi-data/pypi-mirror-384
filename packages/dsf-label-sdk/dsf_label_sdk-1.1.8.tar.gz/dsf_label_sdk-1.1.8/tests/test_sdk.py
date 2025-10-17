# tests/test_sdk.py
"""Unit tests for the SDK"""

import pytest
from unittest.mock import Mock, patch
from dsf_label_sdk import LabelSDK, ValidationError, LicenseError


class TestLabelSDK:
    """Test suite for LabelSDK"""
    
    def test_community_initialization(self):
        """Test community tier initialization"""
        sdk = LabelSDK()
        assert sdk.tier == 'community'
        assert sdk.license_key is None
    
    def test_invalid_tier_raises_error(self):
        """Test invalid tier raises ValidationError"""
        with pytest.raises(ValidationError):
            LabelSDK(tier='invalid')
    
    @patch('dsf_label_sdk.client.requests.Session.post')
    def test_evaluate_success(self, mock_post):
        """Test successful evaluation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'score': 0.85,
            'tier': 'community',
            'confidence_level': 0.65
        }
        mock_post.return_value = mock_response
        
        sdk = LabelSDK()
        result = sdk.evaluate(
            data={'field1': 5},
            config={'field1': {'default': 10, 'weight': 1.0}}
        )
        
        assert result.score == 0.85
        assert result.tier == 'community'
        assert result.is_above_threshold is True
    
    def test_batch_evaluate_requires_premium(self):
        """Test batch evaluation requires premium tier"""
        sdk = LabelSDK()  # Community tier
        
        with pytest.raises(LicenseError):
            sdk.batch_evaluate([{'field1': 5}])
    
    def test_config_builder(self):
        """Test config builder functionality"""
        sdk = LabelSDK()
        config = (sdk.create_config()
            .add_field('temp', default=20, weight=1.0)
            .add_field('pressure', default=1.0, weight=0.8)
        )
        
        config_dict = config.to_dict()
        assert 'temp' in config_dict
        assert config_dict['temp']['default'] == 20
        assert config_dict['temp']['weight'] == 1.0
