import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SHARD_COUNT = 2  # Número de shards (ajuste conforme necessário)