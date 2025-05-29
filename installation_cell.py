# Install specific Redis version known to work with LangChain (v4.5.1)
!pip install redis==4.5.1

# Install LangChain and other required packages
!pip install -q langchain-community==0.0.10 langchain-core==0.1.5 unstructured langchain_openai==0.0.2

# Print Redis version for debugging
import redis
print(f"Redis version: {redis.__version__}")

# Check if Redis search module is available
try:
    from redis.commands.search.indexDefinition import IndexDefinition
    print("Redis search module is available")
except ImportError:
    print("Redis search module is NOT available")

# Add a small delay to ensure installation completes
import time
time.sleep(2)

# Start Redis Stack server
%%sh
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update > /dev/null 2>&1
sudo apt-get install redis-stack-server > /dev/null 2>&1
redis-stack-server --daemonize yes

# Verify Redis installation
!redis-cli ping

# Set up OpenAI API key
import os
from getpass import getpass

# Prompt for OpenAI API key if not already set
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass("Enter your OpenAI API key: ")
    
print("OpenAI API key is set")
