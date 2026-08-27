import discord
from discord.ext import commands

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Signed in：{bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} CMDs.")
    except Exception as e:
        print(f"Error：{e}")

@bot.tree.command(name="deal", description="發一副橋牌，使用random()")
async def deal(interaction: discord.Interaction):
    await interaction.response.send_message("Deal started~")
    #__import__('os').system('python bridge.py')
    __import__('os').system('python3 bridge.py')

bot.run('TOKEN')
