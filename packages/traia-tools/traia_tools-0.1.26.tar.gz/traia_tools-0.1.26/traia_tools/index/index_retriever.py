import json
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_traia_tools_index() -> Dict[str, Any]:
    """
    Retrieve the traia_tools_index.json from the package.
    
    Returns:
        Dict[str, Any]: The contents of the tools index JSON file
        
    Raises:
        FileNotFoundError: If the tools index file cannot be found
        json.JSONDecodeError: If the tools index file is not valid JSON
    """
    try:
        # Get the directory where this module is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        index_file_path = os.path.join(current_dir, 'traia_tools_index.json')
        
        # Read and parse the JSON file
        with open(index_file_path, 'r') as f:
            return json.load(f), index_file_path
            
    except FileNotFoundError:
        logger.error("traia_tools_index.json not found in the package")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing traia_tools_index.json: {str(e)}")
        raise


if __name__ == "__main__":
    # Test the function
    try:
        tools_index, index_file_path = get_traia_tools_index()
        print("Successfully fetched tools index:")
        print(json.dumps(tools_index, indent=2))
        print(f"Index file path: {index_file_path}")
    except Exception as e:
        print(f"Error fetching tools index: {str(e)}") 