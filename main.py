from bot import bot
from config import DISCORD_TOKEN
import discord
from discord.ext import commands
import datetime
import time

@bot.command(name='ping')
async def ping(ctx):
    """Comando de ping que mostra qual shard respondeu"""
    shard_id = ctx.guild.shard_id if ctx.guild else 0
    latency = round(bot.latency * 1000, 2)
    
    # Cria embed colorido baseado na latência
    if latency < 100:
        color = 0x00ff00  # Verde
    elif latency < 300:
        color = 0xffff00  # Amarelo
    else:
        color = 0xff0000  # Vermelho
    
    embed = discord.Embed(
        title="🏓 Pong!",
        color=color,
        timestamp=datetime.datetime.utcnow()
    )
    
    embed.add_field(name="📡 Latência", value=f"`{latency}ms`", inline=True)
    embed.add_field(name="🔧 Shard", value=f"`{shard_id}`", inline=True)
    embed.add_field(name="🌐 Shards Totais", value=f"`{bot.shard_count}`", inline=True)
    embed.add_field(name="🏠 Servidores", value=f"`{len(bot.guilds)}`", inline=True)
    embed.add_field(name="👥 Usuários", value=f"`{len(bot.users)}`", inline=True)
    embed.add_field(name="⚡ Uptime", value=f"`{get_uptime(bot)}`", inline=True)
    
    # Adiciona footer com shard específico
    embed.set_footer(text=f"Resposta do Shard {shard_id} • {ctx.author.name}", 
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    
    await ctx.send(embed=embed)

@bot.command(name='shardinfo')
async def shard_info(ctx, shard_id: int = None):
    """Mostra informações de um shard específico ou de todos"""
    if shard_id is not None:
        # Informações de shard específico
        shard_info = bot.get_shard_info(shard_id)
        if not shard_info:
            await ctx.send(f"❌ Shard `{shard_id}` não encontrado!")
            return
            
        embed = discord.Embed(
            title=f"🔧 Informações do Shard {shard_id}",
            color=0x0099ff
        )
        
        status_emoji = {
            'online': '🟢',
            'connected': '🔵', 
            'disconnected': '🔴',
            'resumed': '🟡'
        }
        
        embed.add_field(name="Status", value=f"{status_emoji.get(shard_info['status'], '⚫')} {shard_info['status']}", inline=True)
        embed.add_field(name="Latência", value=f"`{shard_info['latency']}ms`", inline=True)
        embed.add_field(name="Servidores", value=f"`{shard_info['guilds']}`", inline=True)
        embed.add_field(name="Rate Limited", value=f"`{shard_info['is_ws_ratelimited']}`", inline=True)
        embed.add_field(name="Último Heartbeat", value=f"`{shard_info['heartbeat']}`", inline=True)
        
        await ctx.send(embed=embed)
        
    else:
        # Informações de todos os shards
        shards_info = bot.get_all_shards_info()
        
        embed = discord.Embed(
            title="🔧 Status de Todos os Shards",
            color=0x00ff00
        )
        
        for shard in shards_info:
            status_emoji = '🟢' if shard['latency'] < 200 else '🟡' if shard['latency'] < 500 else '🔴'
            
            embed.add_field(
                name=f"Shard {shard['id']} {status_emoji}",
                value=f"Latência: `{shard['latency']}ms`\nServidores: `{shard['guilds']}`\nStatus: `{shard['status']}`",
                inline=True
            )
        
        total_guilds = sum(shard['guilds'] for shard in shards_info)
        avg_latency = sum(shard['latency'] for shard in shards_info) / len(shards_info)
        
        embed.add_field(
            name="📊 Resumo",
            value=f"Total Servidores: `{total_guilds}`\nMédia Latência: `{round(avg_latency, 2)}ms`\nShards Ativos: `{len(shards_info)}/{bot.shard_count}`",
            inline=False
        )
        
        await ctx.send(embed=embed)

@bot.command(name='shardtest')
async def shard_test(ctx):
    """Testa resposta de todos os shards"""
    message = await ctx.send("🔄 Testando shards...")
    
    results = []
    for shard_id in range(bot.shard_count):
        shard_info = bot.get_shard_info(shard_id)
        if shard_info:
            status = "✅ Online" if shard_info['latency'] < 1000 else "⚠️ Lento" if shard_info['latency'] < 3000 else "❌ Offline"
            results.append(f"Shard {shard_id}: {status} ({shard_info['latency']}ms)")
        else:
            results.append(f"Shard {shard_id}: ❌ Indisponível")
    
    embed = discord.Embed(
        title="🧪 Teste de Shards",
        description="\n".join(results),
        color=0x00ff00
    )
    
    await message.edit(content="", embed=embed)

def get_uptime(bot):
    """Calcula o tempo online do bot"""
    delta = datetime.datetime.utcnow() - bot.start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    else:
        return f"{hours}h {minutes}m {seconds}s"

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Erro no comando {ctx.command}: {error}")

# Inicialização do bot
if __name__ == "__main__":
    print("🚀 Iniciando bot com multi-shard...")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")