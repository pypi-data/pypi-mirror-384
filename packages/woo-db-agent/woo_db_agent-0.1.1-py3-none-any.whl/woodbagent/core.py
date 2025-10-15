"""
Core module for WooCommerce Query Generator
Handles AI-powered SQL query generation using Google Gemini API
"""

import google.generativeai as genai
from .config import WOOCOMMERCE_SCHEMA_CONTEXT


class WooCommerceQueryGenerator:
    """
    Generate SQL queries for WooCommerce databases using Google Gemini API
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the WooCommerce Query Generator with Gemini API
        
        Args:
            api_key: Your Google Gemini API key
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # WooCommerce database schema context
        self.schema_context = WOOCOMMERCE_SCHEMA_CONTEXT
    
    def generate_query(self, user_prompt: str) -> str:
        """
        Generate SQL query based on user prompt
        
        Args:
            user_prompt: Natural language query about products
            
        Returns:
            SQL query string
        """
        full_prompt = f"""{self.schema_context}
        
        User Request: {user_prompt}
        
        Generate a MySQL query for the above request. Return ONLY the SQL query, nothing else.
        """
        
        try:
            response = self.model.generate_content(full_prompt)
            sql_query = response.text.strip()
            
            # Clean up the response (remove markdown code blocks if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            elif sql_query.startswith('```'):
                sql_query = sql_query.replace('```', '').strip()
            
            return sql_query
            
        except Exception as e:
            return f"Error generating query: {str(e)}"
