#!/usr/bin/env python3
"""
Update All Notebooks to Use Redis Cloud
Systematically updates all workshop notebooks to use Redis Cloud by default
"""

import os
import json
import re
from pathlib import Path

# Redis Cloud configuration
REDIS_CLOUD_CONFIG = {
    'host': 'redis-15306.c329.us-east4-1.gce.redns.redis-cloud.com',
    'port': 15306,
    'username': 'default',
    'password': 'ftswOcgMB8dLCnjbKMMDBg3DNnpi1KO5'
}

def find_notebooks():
    """Find all Jupyter notebooks in the workshops"""
    notebooks = []
    
    # Workshop directories to check
    workshop_dirs = [
        '01-RedisJSON_Search',
        '02-Vector_Similarity_Search', 
        '03-Advanced_RedisSearch',
        '05-LangChain_Redis',
        '06-LlamaIndex_Redis'
    ]
    
    for workshop_dir in workshop_dirs:
        if os.path.exists(workshop_dir):
            for file in Path(workshop_dir).glob('*.ipynb'):
                notebooks.append(str(file))
    
    return notebooks

def update_notebook_redis_config(notebook_path):
    """Update a single notebook to use Redis Cloud"""
    print(f"📝 Updating {notebook_path}...")
    
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        updated = False
        
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                source = cell.get('source', [])
                
                # Convert source to string if it's a list
                if isinstance(source, list):
                    source_str = ''.join(source)
                else:
                    source_str = source
                
                # Check if this cell contains Redis configuration
                if ('REDIS_HOST' in source_str and 'localhost' in source_str) or \
                   ('redis-stack-server' in source_str):
                    
                    # Update Redis configuration
                    new_source = update_redis_config_in_source(source_str)
                    
                    if new_source != source_str:
                        # Convert back to list format
                        cell['source'] = new_source.split('\n')
                        # Ensure each line ends with \n except the last
                        for i in range(len(cell['source']) - 1):
                            if not cell['source'][i].endswith('\n'):
                                cell['source'][i] += '\n'
                        updated = True
        
        if updated:
            # Write back the updated notebook
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=1, ensure_ascii=False)
            print(f"✅ Updated {notebook_path}")
            return True
        else:
            print(f"ℹ️  No Redis config found in {notebook_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {notebook_path}: {e}")
        return False

def update_redis_config_in_source(source_str):
    """Update Redis configuration in source code"""
    
    # Comment out redis-stack-server installation
    if 'redis-stack-server --daemonize yes' in source_str:
        source_str = re.sub(
            r'(.*redis-stack-server.*)',
            r'# \1  # COMMENTED OUT - Using Redis Cloud by default',
            source_str
        )
        source_str = re.sub(
            r'(.*curl -fsSL.*redis.*)',
            r'# \1  # COMMENTED OUT - Using Redis Cloud by default',
            source_str
        )
        source_str = re.sub(
            r'(.*apt-get.*redis.*)',
            r'# \1  # COMMENTED OUT - Using Redis Cloud by default',
            source_str
        )
        source_str += '\nprint("✅ Using Redis Cloud - no local installation needed!")\n'
    
    # Update Redis connection variables
    if 'REDIS_HOST = os.getenv("REDIS_HOST", "localhost")' in source_str:
        source_str = source_str.replace(
            'REDIS_HOST = os.getenv("REDIS_HOST", "localhost")',
            f'REDIS_HOST = os.getenv("REDIS_HOST", "{REDIS_CLOUD_CONFIG["host"]}")'
        )
        
        source_str = source_str.replace(
            'REDIS_PORT = os.getenv("REDIS_PORT", "6379")',
            f'REDIS_PORT = os.getenv("REDIS_PORT", "{REDIS_CLOUD_CONFIG["port"]}")'
        )
        
        source_str = source_str.replace(
            'REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")',
            f'REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "{REDIS_CLOUD_CONFIG["password"]}")'
        )
        
        # Add username if not present
        if 'REDIS_USERNAME' not in source_str:
            username_line = f'REDIS_USERNAME = os.getenv("REDIS_USERNAME", "{REDIS_CLOUD_CONFIG["username"]}")\n'
            # Insert after REDIS_PASSWORD line
            source_str = re.sub(
                r'(REDIS_PASSWORD = .*\n)',
                r'\1' + username_line,
                source_str
            )
        
        # Add Redis Cloud comment
        if '# Redis Cloud Configuration' not in source_str:
            source_str = re.sub(
                r'(import os\n)',
                r'\1\n# Redis Cloud Configuration (Default)\n# Using Redis Cloud for persistent data storage\n',
                source_str
            )
        
        # Update commented examples
        source_str = re.sub(
            r'#REDIS_HOST="redis-18374\..*"',
            f'# Example: REDIS_HOST="{REDIS_CLOUD_CONFIG["host"]}"',
            source_str
        )
        
        # Add connection info
        if 'print(' not in source_str or 'Connecting to Redis' not in source_str:
            source_str += f'\nprint(f"🔗 Connecting to Redis Cloud: {{REDIS_HOST}}:{{REDIS_PORT}}")\n'
    
    return source_str

def create_summary_report(results):
    """Create a summary report of updates"""
    print("\n" + "="*60)
    print("📊 REDIS CLOUD UPDATE SUMMARY")
    print("="*60)
    
    updated_count = sum(1 for result in results if result['updated'])
    total_count = len(results)
    
    print(f"📝 Total notebooks processed: {total_count}")
    print(f"✅ Successfully updated: {updated_count}")
    print(f"ℹ️  No changes needed: {total_count - updated_count}")
    
    print(f"\n🔗 Redis Cloud Configuration:")
    print(f"   Host: {REDIS_CLOUD_CONFIG['host']}")
    print(f"   Port: {REDIS_CLOUD_CONFIG['port']}")
    print(f"   Username: {REDIS_CLOUD_CONFIG['username']}")
    
    print(f"\n📁 Updated notebooks:")
    for result in results:
        if result['updated']:
            print(f"   ✅ {result['notebook']}")
    
    print(f"\n📁 Notebooks with no Redis config:")
    for result in results:
        if not result['updated']:
            print(f"   ℹ️  {result['notebook']}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Test notebooks to ensure Redis Cloud connectivity")
    print(f"   2. Update any remaining Python files manually")
    print(f"   3. Run workshops to verify persistent data storage")
    print(f"   4. Enjoy seamless data persistence across sessions!")

def main():
    """Main update process"""
    print("🚀 Updating All Notebooks to Use Redis Cloud")
    print("="*60)
    
    # Find all notebooks
    notebooks = find_notebooks()
    
    if not notebooks:
        print("❌ No notebooks found to update")
        return
    
    print(f"📝 Found {len(notebooks)} notebooks to check")
    
    # Update each notebook
    results = []
    for notebook in notebooks:
        updated = update_notebook_redis_config(notebook)
        results.append({
            'notebook': notebook,
            'updated': updated
        })
    
    # Create summary report
    create_summary_report(results)
    
    print(f"\n🎉 Redis Cloud update process complete!")

if __name__ == "__main__":
    main()
