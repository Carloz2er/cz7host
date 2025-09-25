import discord
from discord.ext import commands
import asyncio
import datetime
import platform

class MultiShardBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix='!',
            intents=intents,
            shard_count=SHARD_COUNT,
            activity=discord.Activity(type=discord.ActivityType.watching, name=f"{SHARD_COUNT} shards")
        )
        
        self.start_time = datetime.datetime.utcnow()
        self.shard_status = {}

    async def on_ready(self):
        print(f'✅ Bot conectado como {self.user}')
        print(f'📊 Shards: {self.shard_count}')
        print(f'🏠 Servidores: {len(self.guilds)}')
        print(f'👥 Usuários: {len(self.users)}')
        
        # Inicializa status dos shards
        for shard_id in self.shards:
            self.shard_status[shard_id] = {
                'status': 'online',
                'latency': self.latency,
                'guilds': len([g for g in self.guilds if g.shard_id == shard_id]),
                'last_heartbeat': datetime.datetime.utcnow()
            }

    async def on_shard_ready(self, shard_id):
        print(f'🔧 Shard {shard_id} está pronto!')
        self.shard_status[shard_id] = {
            'status': 'online',
            'latency': self.latency,
            'guilds': len([g for g in self.guilds if g.shard_id == shard_id]),
            'last_heartbeat': datetime.datetime.utcnow()
        }

    async def on_shard_connect(self, shard_id):
        print(f'🔌 Shard {shard_id} conectado')
        self.shard_status[shard_id]['status'] = 'connected'

    async def on_shard_disconnect(self, shard_id):
        print(f'🔴 Shard {shard_id} desconectado')
        self.shard_status[shard_id]['status'] = 'disconnected'

    async def on_shard_resumed(self, shard_id):
        print(f'🟢 Shard {shard_id} reconectado')
        self.shard_status[shard_id]['status'] = 'resumed'

    def get_shard_info(self, shard_id):
        """Retorna informações específicas de um shard"""
        shard = self.shards.get(shard_id)
        if not shard:
            return None
            
        return {
            'id': shard_id,
            'latency': round(shard.latency * 1000, 2),  # ms
            'status': self.shard_status[shard_id]['status'],
            'guilds': self.shard_status[shard_id]['guilds'],
            'is_ws_ratelimited': shard.is_ws_ratelimited,
            'heartbeat': self.shard_status[shard_id]['last_heartbeat'].strftime('%H:%M:%S')
        }

    def get_all_shards_info(self):
        """Retorna informações de todos os shards"""
        shards_info = []
        for shard_id in range(self.shard_count):
            shard_info = self.get_shard_info(shard_id)
            if shard_info:
                shards_info.append(shard_info)
        return shards_info

# Configuração
from config import SHARD_COUNT, DISCORD_TOKEN

bot = MultiShardBot()