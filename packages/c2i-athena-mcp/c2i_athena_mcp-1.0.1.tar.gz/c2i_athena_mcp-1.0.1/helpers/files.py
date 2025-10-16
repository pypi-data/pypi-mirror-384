import os
import pandas as pd
from typing import Dict, List, Any
from mcp.server.fastmcp import Context

def save_data_to_csv(ctx: Context, data: List[Dict[str, Any]], filename: str, output_dir: str = None) -> str:
    """
    Save data directly to a CSV file in the specified output directory.
    
    Args:
        ctx: Context object for logging
        data: List of dictionaries containing the data to save
        filename: Name of the CSV file (without .csv extension)
        output_dir: Output directory (defaults to 'outputs' folder in current directory)
        
    Returns:
        Path to the saved CSV file
    """
    if not data:
        ctx.warning("No data to save")
        return "No data to save"
    
    # Set default output directory
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "outputs")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create DataFrame from data
    df = pd.DataFrame(data)
    
    # Add .csv extension if not present
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    file_path = os.path.join(output_dir, filename)
    df.to_csv(file_path, index=False)
    
    ctx.info(f"Data saved to {file_path} ({len(data)} rows)")
    return file_path
