"""
Command-line interface for WooCommerce Gemini Query Generator
"""

import os
from .core import WooCommerceQueryGenerator
from .executor import execute_query, display_results


def main():
    """
    Main function to run the query generator
    """
    # Get API key from environment variable or user input
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("Gemini API key not found in environment variables.")
        api_key = input("Please enter your Gemini API key: ").strip()
    
    if not api_key:
        print("Error: API key is required.")
        return
    
    # Get database credentials
    print("\n" + "=" * 70)
    print("  Database Configuration")
    print("=" * 70)
    
    db_config = {
        'host': os.getenv('DB_HOST') or input("Database Host (default: localhost): ").strip() or 'localhost',
        'database': os.getenv('DB_NAME') or input("Database Name: ").strip(),
        'user': os.getenv('DB_USER') or input("Database User: ").strip(),
        'password': os.getenv('DB_PASSWORD') or input("Database Password: ").strip(),
        'port': int(os.getenv('DB_PORT', 3306))
    }
    
    if not db_config['database'] or not db_config['user']:
        print("Error: Database name and user are required.")
        return
    
    # Test database connection
    print("\n🔌 Testing database connection...")
    test_result = execute_query(
        "SELECT 1",
        **db_config
    )
    
    if not test_result['success']:
        print(f"❌ Failed to connect to database: {test_result['error']}")
        return
    
    print("✅ Database connection successful!\n")
    
    # Initialize the generator
    generator = WooCommerceQueryGenerator(api_key)
    
    # Welcome message
    print("=" * 70)
    print("  WooCommerce SQL Query Generator (Powered by Gemini API)")
    print("=" * 70)
    print("\nDescribe what you want to know about your WooCommerce products")
    print("in plain English, and I'll generate and execute the query for you!")
    print("\nType 'exit' or 'quit' to stop.")
    print("=" * 70 + "\n")
    
    # Main interaction loop
    while True:
        # Prompt user for input
        user_input = input("🛍️  What would you like to know about your products?\n➤  ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Thank you for using WooCommerce Query Generator. Goodbye!\n")
            break
        
        if not user_input:
            print("⚠️  Please enter a valid query.\n")
            continue
        
        # Generate query
        print("\n⏳ Generating SQL query...\n")
        sql_query = generator.generate_query(user_input)
        
        # Check if query generation failed
        if sql_query.startswith("Error generating query"):
            print(f"❌ {sql_query}\n")
            continue
        
        # Display generated query
        print("📝 Generated SQL Query:")
        print("-" * 70)
        print(sql_query)
        print("-" * 70 + "\n")
        
        # Execute the query
        print("⚙️  Executing query on database...\n")
        result = execute_query(sql_query, **db_config)
        
        # Display results
        display_results(result)
        
        # Ask if user wants to continue
        continue_prompt = input("Press Enter to ask another question (or type 'exit' to quit): ").strip()
        if continue_prompt.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Thank you for using WooCommerce Query Generator. Goodbye!\n")
            break
        print()


if __name__ == "__main__":
    main()
