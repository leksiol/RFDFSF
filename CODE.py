import discord
import pandas as pd
import asyncio
import calendar
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
from dotenv import load_dotenv  # Pour charger le token depuis .env

# ===== CONFIGURATION =====
# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer le token Discord depuis la variable d'environnement
TOKEN = os.getenv("TOKEN")  # Assure-toi que le token est dans ton fichier .env

CHANNEL_ID = 1354041426924802068  # Remplace par l'ID du salon où envoyer le message
EXCEL_FILE = "Asia_Take_JDS JDM X.xlsx"  # Nom du fichier Excel
SHEET_NAME = "Sheet1"  # Nom de la feuille Excel

# Chargement du fichier Excel
df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

def get_weekday_name(day, month, year):
    """Retourne le nom du jour de la semaine pour une date donnée."""
    date_obj = datetime(year, month, day)
    return calendar.day_name[date_obj.weekday()]

def get_message():
    """Retourne le message associé à la probabilité pour la date du jour."""
    today = datetime.today()
    day, month, year = today.day, today.month, today.year
    
    weekday_fr = {
        "Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", 
        "Thursday": "Jeudi", "Friday": "Vendredi"
    }
    weekday = get_weekday_name(day, month, year)
    jour_semaine = weekday_fr.get(weekday, None)
    
    if not jour_semaine:
        return "Cette date tombe un week-end donc no trading !."
    
    # Chercher la probabilité
    result = df[(df["JourSemaine"] == jour_semaine) & (df["Jour"] == day)]
    
    if not result.empty:
        proba = result["Valeur"].values[0]
        return f"Nous sommes le {today.strftime('%d %B %Y')} et aujourd'hui : " + ("✅ Let's go trading!" if proba <= 30 else "❌ Pas de trade.")
    else:
        return "Aucune donnée pour cette date."

# ===== CONFIGURATION DU BOT =====
intents = discord.Intents.default()
intents.messages = True  # Autorise l'accès aux messages
intents.message_content = True  # Permet de lire le contenu des messages

bot = commands.Bot(command_prefix="!", intents=intents)

# Variable pour stocker le dernier message envoyé
last_message = None

async def send_daily_message():
    global last_message  # Accède à la variable globale
    
    await bot.wait_until_ready()
    print("✅ Fonction send_daily_message exécutée")  # Vérification
    
    channel = bot.get_channel(CHANNEL_ID)
    
    if channel:
        message = get_message()
        print(f"📢 Message envoyé : {message}")  # Vérification du message
        
        # Si un message précédent existe, le supprimer
        if last_message:
            await last_message.delete()
            print("🗑 Message précédent supprimé.")
        
        # Envoyer le nouveau message et le sauvegarder
        last_message = await channel.send(message)
    else:
        print("❌ Erreur : Le bot ne trouve pas le salon !")

# ===== PLANIFICATION =====
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())  # Corrige le problème d'event loop

scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_message, "cron", hour=20, minute=15)  # Envoi à 0h01

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté !")
    
    # Vérification du salon
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        print(f"📢 Salon trouvé : {channel.name} (ID: {CHANNEL_ID})")
    else:
        print("❌ Erreur : Salon introuvable. Vérifie l'ID.")
    
    if not scheduler.running:
        scheduler.start()
        print("⏰ Scheduler démarré !")  # Vérification

# ===== COMMANDE TEST POUR VÉRIFIER L'ENVOI =====
@bot.command()
async def test(ctx):
    """Commande pour tester l'envoi d'un message"""
    message = get_message()
    await ctx.send(f"📢 Test Message : {message}")

# ===== LANCEMENT DU BOT =====
bot.run(TOKEN)
