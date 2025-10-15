import os
import google.generativeai as genai
import mysql.connector
from mysql.connector import Error
from typing import Dict, Optional, List, Tuple
from tabulate import tabulate

class WooCommerceQueryGenerator:
    def __init__(self, api_key: str):
        """
        Initialize the WooCommerce Query Generator with Gemini API
        
        Args:
            api_key: Your Google Gemini API key
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # WooCommerce database schema context
        self.schema_context = """
        You are a SQL query generator for WooCommerce databases. Generate only valid MySQL queries.
        
        WooCommerce Database Schema:
        
        1. wp_posts (products stored as post_type='product')
           - ID (product ID)
           - post_title (product name)
           - post_content (product description)
           - post_status (publish, draft, etc.)
           - post_date (creation date)
           - post_type (should be 'product')
        
        2. wp_postmeta (product metadata)
           - meta_id
           - post_id (references wp_posts.ID)
           - meta_key (e.g., _price, _stock, _sku, _sale_price, _regular_price)
           - meta_value (the actual value)
        
        3. wp_term_relationships (product categories/tags)
           - object_id (references wp_posts.ID)
           - term_taxonomy_id (references wp_term_taxonomy)
        
        4. wp_term_taxonomy
           - term_taxonomy_id
           - term_id (references wp_terms)
           - taxonomy (product_cat, product_tag, etc.)
        
        5. wp_terms (category/tag names)
           - term_id
           - name (category/tag name)
           - slug
        
        Common meta_keys:
        - _price: Current price
        - _regular_price: Regular price
        - _sale_price: Sale price
        - _stock: Stock quantity
        - _stock_status: instock, outofstock
        - _sku: Product SKU
        - _weight: Product weight
        - _length, _width, _height: Product dimensions
        
        Rules:
        1. Always use proper JOINs
        2. Filter products with post_type='product' AND post_status='publish'
        3. Use aliases for clarity
        4. Return only the SQL query, no explanations
        5. Use proper quote escaping
        """
    
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


def execute_query(
    sql_query: str,
    host: str,
    database: str,
    user: str,
    password: str,
    port: int = 3306
) -> Dict:
    """
    Execute SQL query on MySQL database and return results
    
    Args:
        sql_query: The SQL query to execute
        host: Database host (e.g., 'localhost' or '127.0.0.1')
        database: Database name
        user: Database username
        password: Database password
        port: Database port (default: 3306)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if query executed successfully
        - data: List of tuples containing query results
        - columns: List of column names
        - row_count: Number of rows returned/affected
        - error: Error message if query failed
        - query_type: Type of query (SELECT, UPDATE, INSERT, DELETE)
    """
    result = {
        'success': False,
        'data': [],
        'columns': [],
        'row_count': 0,
        'error': None,
        'query_type': 'UNKNOWN'
    }
    
    connection = None
    cursor = None
    
    try:
        # Determine query type
        query_upper = sql_query.strip().upper()
        if query_upper.startswith('SELECT'):
            result['query_type'] = 'SELECT'
        elif query_upper.startswith('UPDATE'):
            result['query_type'] = 'UPDATE'
        elif query_upper.startswith('INSERT'):
            result['query_type'] = 'INSERT'
        elif query_upper.startswith('DELETE'):
            result['query_type'] = 'DELETE'
        
        # Establish database connection
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            autocommit=False  # Manual commit for better control
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Execute the query
            cursor.execute(sql_query)
            
            # Handle different query types
            if result['query_type'] == 'SELECT':
                # Fetch results for SELECT queries
                result['data'] = cursor.fetchall()
                result['columns'] = [desc[0] for desc in cursor.description] if cursor.description else []
                result['row_count'] = len(result['data'])
            else:
                # For UPDATE, INSERT, DELETE queries
                result['row_count'] = cursor.rowcount
                connection.commit()  # Commit the transaction
                result['data'] = []
                result['columns'] = []
            
            result['success'] = True
            
    except Error as e:
        result['error'] = f"Database error: {str(e)}"
        result['success'] = False
        # Rollback on error
        if connection:
            connection.rollback()
        
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        result['success'] = False
        # Rollback on error
        if connection:
            connection.rollback()
        
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
    
    return result


def display_results(result: Dict):
    """
    Display query results in a formatted table
    
    Args:
        result: Dictionary returned from execute_query function
    """
    if not result['success']:
        print(f"❌ Query Execution Failed!")
        print(f"Error: {result['error']}\n")
        return
    
    query_type = result['query_type']
    
    # Handle SELECT queries
    if query_type == 'SELECT':
        if result['row_count'] == 0:
            print("✅ Query executed successfully!")
            print("ℹ️  No results found.\n")
            return
        
        print("✅ Query executed successfully!\n")
        print(f"📊 Results ({result['row_count']} row{'s' if result['row_count'] != 1 else ''}):")
        print("=" * 70)
        
        # Display results in a table format
        table = tabulate(
            result['data'],
            headers=result['columns'],
            tablefmt='grid',
            showindex=False
        )
        print(table)
        print("=" * 70 + "\n")
    
    # Handle UPDATE, INSERT, DELETE queries
    elif query_type in ['UPDATE', 'INSERT', 'DELETE']:
        print("✅ Query executed successfully!\n")
        
        if query_type == 'UPDATE':
            print(f"🔄 {result['row_count']} row{'s' if result['row_count'] != 1 else ''} updated.")
        elif query_type == 'INSERT':
            print(f"➕ {result['row_count']} row{'s' if result['row_count'] != 1 else ''} inserted.")
        elif query_type == 'DELETE':
            print(f"🗑️  {result['row_count']} row{'s' if result['row_count'] != 1 else ''} deleted.")
        
        print("✔️  Changes have been committed to the database.\n")
    
    # Handle unknown query types
    else:
        print("✅ Query executed successfully!\n")
        if result['row_count'] > 0:
            print(f"ℹ️  {result['row_count']} row{'s' if result['row_count'] != 1 else ''} affected.\n")


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
