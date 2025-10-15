"""
Basic tests for WooCommerce Gemini Query Generator
"""

import pytest
from woocommerce_gemini_query import WooCommerceQueryGenerator
from woocommerce_gemini_query.executor import _detect_query_type, format_results_as_dict


class TestQueryGenerator:
    """Test WooCommerceQueryGenerator class"""
    
    def test_initialization_with_valid_key(self):
        """Test that generator initializes with valid API key"""
        generator = WooCommerceQueryGenerator(api_key="test_key_123")
        assert generator is not None
        assert generator.schema_context is not None
    
    def test_initialization_without_key(self):
        """Test that generator raises error without API key"""
        with pytest.raises(ValueError):
            WooCommerceQueryGenerator(api_key="")
    
    def test_empty_prompt_raises_error(self):
        """Test that empty prompt raises ValueError"""
        generator = WooCommerceQueryGenerator(api_key="test_key_123")
        with pytest.raises(ValueError):
            generator.generate_query("")


class TestQueryTypeDetection:
    """Test query type detection"""
    
    def test_detect_select_query(self):
        """Test SELECT query detection"""
        query = "SELECT * FROM wp_posts WHERE post_type='product'"
        assert _detect_query_type(query) == 'SELECT'
    
    def test_detect_update_query(self):
        """Test UPDATE query detection"""
        query = "UPDATE wp_postmeta SET meta_value='50' WHERE meta_key='_price'"
        assert _detect_query_type(query) == 'UPDATE'
    
    def test_detect_insert_query(self):
        """Test INSERT query detection"""
        query = "INSERT INTO wp_posts (post_title) VALUES ('New Product')"
        assert _detect_query_type(query) == 'INSERT'
    
    def test_detect_delete_query(self):
        """Test DELETE query detection"""
        query = "DELETE FROM wp_posts WHERE post_status='draft'"
        assert _detect_query_type(query) == 'DELETE'
    
    def test_detect_unknown_query(self):
        """Test unknown query type"""
        query = "SHOW TABLES"
        assert _detect_query_type(query) == 'UNKNOWN'


class TestResultFormatting:
    """Test result formatting functions"""
    
    def test_format_select_results(self):
        """Test formatting SELECT query results"""
        result = {
            'success': True,
            'query_type': 'SELECT',
            'row_count': 2,
            'columns': ['id', 'name'],
            'data': [(1, 'Product A'), (2, 'Product B')]
        }
        
        formatted = format_results_as_dict(result)
        
        assert formatted['success'] is True
        assert formatted['row_count'] == 2
        assert len(formatted['data']) == 2
        assert formatted['data'][0]['name'] == 'Product A'
    
    def test_format_update_results(self):
        """Test formatting UPDATE query results"""
        result = {
            'success': True,
            'query_type': 'UPDATE',
            'row_count': 5,
            'columns': [],
            'data': []
        }
        
        formatted = format_results_as_dict(result)
        
        assert formatted['success'] is True
        assert formatted['rows_affected'] == 5
        assert 'data' not in formatted
    
    def test_format_error_results(self):
        """Test formatting error results"""
        result = {
            'success': False,
            'error': 'Connection failed'
        }
        
        formatted = format_results_as_dict(result)
        
        assert formatted['success'] is False
        assert formatted['error'] == 'Connection failed'


class TestImports:
    """Test that all public API is importable"""
    
    def test_import_main_class(self):
        """Test importing WooCommerceQueryGenerator"""
        from woocommerce_gemini_query import WooCommerceQueryGenerator
        assert WooCommerceQueryGenerator is not None
    
    def test_import_execute_query(self):
        """Test importing execute_query"""
        from woocommerce_gemini_query import execute_query
        assert execute_query is not None
    
    def test_import_display_results(self):
        """Test importing display_results"""
        from woocommerce_gemini_query import display_results
        assert display_results is not None
    
    def test_package_version(self):
        """Test that package has version"""
        from woocommerce_gemini_query import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)
    
    def test_package_author(self):
        """Test that package has author"""
        from woocommerce_gemini_query import __author__
        assert __author__ is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
