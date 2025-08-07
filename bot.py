import logging
import os
import json
from datetime import datetime
import discord
from discord.ext import commands
from discord import app_commands, Embed, Color, Interaction

LOGS_CONFIG_FILE = "logs_channels.json"
LOGS_CATEGORY_NAME = "📑・LOGS SERVER"
DEFAULT_LOG_CHANNELS = {
    "messaggi": "💬・messaggi",
    "messaggi_modificati": "✏️・messaggi-modificati",
    "messaggi_cancellati": "🗑️・messaggi-cancellati",
    "join_leave": "👋・join-leave",
    "ban_unban": "🔨・ban-unban",
    "ruoli": "🎭・ruoli",
    "canali": "📁・canali",
    "nickname": "📝・nickname",
    "avatar": "🖼️・avatar",
    "voice": "🔊・voice",
    "inviti": "🔗・inviti",
    "emoji": "😃・emoji",
    "webhook": "🌐・webhook",
    "integrazioni": "🔌・integrazioni",
    "audit": "🕵️・audit-log",
    "moderazione": "🛡️・moderazione",
    "boost": "🚀・boost",
    "permessi": "🔑・permessi",
    "thread": "🧵・thread",
    "stage": "🎤・stage",
    "stickers": "🏷️・stickers",
    "scheduled_events": "📅・eventi-programmati",
    "guild_update": "🏛️・server-update",
    "member_update": "👤・member-update",
    "role_update": "🛠️・ruoli-update",
    "channel_update": "🔄・canali-update"
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== GESTIONE FILE LOGS ==========

def load_logs_channels():
    if not os.path.exists(LOGS_CONFIG_FILE):
        return {}
    try:
        with open(LOGS_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Controllo integrità dati
            if not isinstance(data, dict):
                print("❌ logs_channels.json corrotto: non è un dizionario.")
                return {}
            # Rimuovi guild_id non validi
            valid_data = {}
            for gid, channels in data.items():
                if not gid.isdigit() or not isinstance(channels, dict):
                    continue
                valid_channels = {}
                for log_type, channel_id in channels.items():
                    if log_type in DEFAULT_LOG_CHANNELS and isinstance(channel_id, int):
                        valid_channels[log_type] = channel_id
                if valid_channels:
                    valid_data[gid] = valid_channels
            return valid_data
    except Exception as e:
        print(f"❌ Errore caricamento logs_channels.json: {e}")
        return {}

def save_logs_channels(data):
    try:
        # Salva solo guild_id e log_type validi
        safe_data = {}
        for gid, channels in data.items():
            if not str(gid).isdigit():
                continue
            safe_channels = {}
            for log_type, channel_id in channels.items():
                if log_type in DEFAULT_LOG_CHANNELS and isinstance(channel_id, int):
                    safe_channels[log_type] = channel_id
            if safe_channels:
                safe_data[str(gid)] = safe_channels
        with open(LOGS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(safe_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Errore salvataggio logs_channels.json: {e}")

logs_channels = load_logs_channels()

async def get_log_channel(guild, log_type):
    guild_id = str(guild.id)
    if guild_id in logs_channels and log_type in logs_channels[guild_id]:
        channel_id = logs_channels[guild_id][log_type]
        channel = guild.get_channel(channel_id)
        # Controllo sicurezza: il canale esiste ancora?
        if channel and isinstance(channel, discord.TextChannel):
            return channel
        else:
            # Se il canale non esiste più, rimuovilo dal json
            logs_channels[guild_id].pop(log_type, None)
            save_logs_channels(logs_channels)
    return None

# ========== COMANDO SETUP LOGS ==========

@bot.tree.command(name="setup_logs", description="Configura automaticamente tutti i canali di log.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_logs(interaction: Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("> ❌ **Questo comando può essere usato solo in un server.**", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }

    # Crea o trova la categoria
    category = discord.utils.get(guild.categories, name=LOGS_CATEGORY_NAME)
    if not category:
        try:
            category = await guild.create_category(LOGS_CATEGORY_NAME, overwrites=overwrites)
        except Exception as e:
            await interaction.followup.send(f"❌ Errore creazione categoria: {e}", ephemeral=True)
            return
    
    created_channels = {}
    for log_key, log_name in DEFAULT_LOG_CHANNELS.items():
        channel = discord.utils.get(category.channels, name=log_name.lower())
        if not channel:
            try:
                channel = await guild.create_text_channel(
                    log_name,
                    category=category,
                    overwrites=overwrites,
                    topic=f"🔔 Log automatico: {log_name}"
                )
            except Exception as e:
                await interaction.followup.send(f"❌ Errore creazione canale {log_name}: {e}", ephemeral=True)
                continue
        created_channels[log_key] = channel.id

    # Salva nel file json
    logs_channels[str(guild.id)] = created_channels
    save_logs_channels(logs_channels)

    embed = Embed(
        title="🟢 Log configurati con successo!",
        description="> Tutti i canali di log sono stati **creati** e **configurati** correttamente.\n\n"
                    "Puoi personalizzare i permessi o la posizione dei canali a tuo piacimento.",
        color=Color.green()
    )
    embed.set_footer(text="Log System • 2025", icon_url=bot.user.display_avatar.url)
    await interaction.followup.send(embed=embed)

# ========== EVENTI DI LOGGING ==========

def log_embed(
    title: str,
    description: str,
    color=Color.blurple(),
    fields=None,
    author=None,
    thumbnail=None,
    footer=None,
    timestamp=True
):
    embed = Embed(
        title=title,
        description=description,
        color=color
    )
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    if author:
        embed.set_author(name=author[0], icon_url=author[1] if len(author) > 1 else discord.Embed.Empty)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if footer:
        embed.set_footer(text=footer)
    else:
        embed.set_footer(text="Log System • 2025")
    if timestamp:
        embed.timestamp = datetime.utcnow()
    return embed

async def send_log(guild, log_type, embed):
    channel = await get_log_channel(guild, log_type)
    if channel:
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"❌ Errore invio log ({log_type}): {e}")

# ========== AVVIO DEL BOT ==========

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN") or "INSERISCI_IL_TUO_TOKEN"
    if TOKEN == "INSERISCI_IL_TUO_TOKEN":
        print("❌ Inserisci il token del bot in una variabile d'ambiente DISCORD_TOKEN o direttamente nel codice!")
    else:
        # --- Sincronizzazione dei comandi slash ---
        @bot.event
        async def on_ready():
            print(f"✅ Bot connesso come {bot.user}")
            try:
                synced = await bot.tree.sync()
                print(f"🔄 Comandi slash sincronizzati: {len(synced)}")
            except Exception as e:
                print(f"❌ Errore sincronizzazione comandi slash: {e}")

        # ========== EVENTI DI LOGGING AVANZATI ==========

        # Log messaggi inviati
        @bot.event
        async def on_message(message):
            if message.author.bot or not message.guild:
                return
            embed = log_embed(
                title="💬 Nuovo messaggio",
                description=f"**{message.author.mention}** ha inviato un messaggio in {message.channel.mention}",
                color=Color.blue(),
                fields=[
                    ("Contenuto", message.content[:1024] if message.content else "*Nessun testo*", False),
                    ("ID Utente", str(message.author.id), True),
                    ("ID Messaggio", str(message.id), True)
                ],
                author=(str(message.author), message.author.display_avatar.url),
                timestamp=True
            )
            await send_log(message.guild, "messaggi", embed)
            await bot.process_commands(message)

        # Log messaggi modificati
        @bot.event
        async def on_message_edit(before, after):
            if before.author.bot or not before.guild:
                return
            if before.content == after.content:
                return
            embed = log_embed(
                title="✏️ Messaggio modificato",
                description=f"**{before.author.mention}** ha modificato un messaggio in {before.channel.mention}",
                color=Color.orange(),
                fields=[
                    ("Prima", before.content[:1024] if before.content else "*Vuoto*", False),
                    ("Dopo", after.content[:1024] if after.content else "*Vuoto*", False),
                    ("ID Messaggio", str(before.id), True)
                ],
                author=(str(before.author), before.author.display_avatar.url),
                timestamp=True
            )
            await send_log(before.guild, "messaggi_modificati", embed)

        # Log messaggi cancellati
        @bot.event
        async def on_message_delete(message):
            if message.author.bot or not message.guild:
                return
            embed = log_embed(
                title="🗑️ Messaggio eliminato",
                description=f"**{message.author.mention}** ha eliminato un messaggio in {message.channel.mention}",
                color=Color.red(),
                fields=[
                    ("Contenuto", message.content[:1024] if message.content else "*Nessun testo*", False),
                    ("ID Messaggio", str(message.id), True)
                ],
                author=(str(message.author), message.author.display_avatar.url),
                timestamp=True
            )
            await send_log(message.guild, "messaggi_cancellati", embed)

        # Log join/leave
        @bot.event
        async def on_member_join(member):
            if not member.guild:
                return
            embed = log_embed(
                title="👋 Utente entrato",
                description=f"{member.mention} è entrato nel server.",
                color=Color.green(),
                fields=[
                    ("ID Utente", str(member.id), True),
                    ("Account creato", member.created_at.strftime('%d/%m/%Y %H:%M'), True)
                ],
                author=(str(member), member.display_avatar.url),
                timestamp=True
            )
            await send_log(member.guild, "join_leave", embed)

        @bot.event
        async def on_member_remove(member):
            if not member.guild:
                return
            embed = log_embed(
                title="👋 Utente uscito",
                description=f"{member.mention} ha lasciato il server.",
                color=Color.red(),
                fields=[
                    ("ID Utente", str(member.id), True),
                    ("Account creato", member.created_at.strftime('%d/%m/%Y %H:%M'), True)
                ],
                author=(str(member), member.display_avatar.url),
                timestamp=True
            )
            await send_log(member.guild, "join_leave", embed)

        # Log ban/unban
        @bot.event
        async def on_member_ban(guild, user):
            embed = log_embed(
                title="🔨 Utente bannato",
                description=f"{user.mention if hasattr(user, 'mention') else user} è stato **bannato**.",
                color=Color.red(),
                fields=[
                    ("ID Utente", str(user.id), True)
                ],
                author=(str(user), user.display_avatar.url if hasattr(user, "display_avatar") else None),
                timestamp=True
            )
            await send_log(guild, "ban_unban", embed)

        @bot.event
        async def on_member_unban(guild, user):
            embed = log_embed(
                title="🔨 Utente sbannato",
                description=f"{user.mention if hasattr(user, 'mention') else user} è stato **sbannato**.",
                color=Color.green(),
                fields=[
                    ("ID Utente", str(user.id), True)
                ],
                author=(str(user), user.display_avatar.url if hasattr(user, "display_avatar") else None),
                timestamp=True
            )
            await send_log(guild, "ban_unban", embed)

        # Log ruoli creati/eliminati/modificati
        @bot.event
        async def on_guild_role_create(role):
            embed = log_embed(
                title="🎭 Ruolo creato",
                description=f"Ruolo `{role.name}` creato.",
                color=Color.green(),
                fields=[
                    ("ID Ruolo", str(role.id), True)
                ],
                timestamp=True
            )
            await send_log(role.guild, "ruoli", embed)

        @bot.event
        async def on_guild_role_delete(role):
            embed = log_embed(
                title="🎭 Ruolo eliminato",
                description=f"Ruolo `{role.name}` eliminato.",
                color=Color.red(),
                fields=[
                    ("ID Ruolo", str(role.id), True)
                ],
                timestamp=True
            )
            await send_log(role.guild, "ruoli", embed)

        @bot.event
        async def on_guild_role_update(before, after):
            changes = []
            if before.name != after.name:
                changes.append(f"Nome: `{before.name}` → `{after.name}`")
            if before.permissions != after.permissions:
                changes.append("Permessi modificati")
            if before.color != after.color:
                changes.append(f"Colore: `{before.color}` → `{after.color}`")
            if not changes:
                return
            embed = log_embed(
                title="🛠️ Ruolo modificato",
                description=f"Ruolo `{before.name}` modificato.\n" + "\n".join(changes),
                color=Color.orange(),
                fields=[
                    ("ID Ruolo", str(before.id), True)
                ],
                timestamp=True
            )
            await send_log(after.guild, "role_update", embed)

        # Log canali creati/eliminati/modificati
        @bot.event
        async def on_guild_channel_create(channel):
            embed = log_embed(
                title="📁 Canale creato",
                description=f"Canale `{channel.name}` creato ({str(channel.type)})",
                color=Color.green(),
                fields=[
                    ("ID Canale", str(channel.id), True)
                ],
                timestamp=True
            )
            await send_log(channel.guild, "canali", embed)

        @bot.event
        async def on_guild_channel_delete(channel):
            embed = log_embed(
                title="📁 Canale eliminato",
                description=f"Canale `{channel.name}` eliminato ({str(channel.type)})",
                color=Color.red(),
                fields=[
                    ("ID Canale", str(channel.id), True)
                ],
                timestamp=True
            )
            await send_log(channel.guild, "canali", embed)

        @bot.event
        async def on_guild_channel_update(before, after):
            changes = []
            if before.name != after.name:
                changes.append(f"Nome: `{before.name}` → `{after.name}`")
            if before.topic != after.topic:
                changes.append("Topic modificato")
            if before.category != after.category:
                changes.append("Categoria modificata")
            if not changes:
                return
            embed = log_embed(
                title="🔄 Canale modificato",
                description=f"Canale `{before.name}` modificato.\n" + "\n".join(changes),
                color=Color.orange(),
                fields=[
                    ("ID Canale", str(before.id), True)
                ],
                timestamp=True
            )
            await send_log(after.guild, "channel_update", embed)

        # Log nickname e avatar
        @bot.event
        async def on_user_update(before, after):
            if before.avatar != after.avatar:
                embed = log_embed(
                    title="🖼️ Avatar cambiato",
                    description=f"{after.mention if hasattr(after, 'mention') else after} ha cambiato avatar.",
                    color=Color.blurple(),
                    fields=[
                        ("ID Utente", str(after.id), True)
                    ],
                    thumbnail=after.display_avatar.url if hasattr(after, "display_avatar") else None,
                    timestamp=True
                )
                # Non c'è guild, quindi logga su tutte le guild dove è presente
                for guild in bot.guilds:
                    member = guild.get_member(after.id)
                    if member:
                        await send_log(guild, "avatar", embed)
            if hasattr(before, "display_name") and hasattr(after, "display_name") and before.display_name != after.display_name:
                embed = log_embed(
                    title="📝 Nickname cambiato",
                    description=f"{after.mention if hasattr(after, 'mention') else after} ha cambiato nickname.",
                    color=Color.blurple(),
                    fields=[
                        ("Prima", before.display_name, True),
                        ("Dopo", after.display_name, True),
                        ("ID Utente", str(after.id), True)
                    ],
                    timestamp=True
                )
                for guild in bot.guilds:
                    member = guild.get_member(after.id)
                    if member:
                        await send_log(guild, "nickname", embed)

        # Log boost
        @bot.event
        async def on_member_update(before, after):
            if before.premium_since != after.premium_since:
                if after.premium_since:
                    embed = log_embed(
                        title="🚀 Boost ricevuto",
                        description=f"{after.mention} ha boostato il server!",
                        color=Color.purple(),
                        fields=[
                            ("ID Utente", str(after.id), True)
                        ],
                        timestamp=True
                    )
                else:
                    embed = log_embed(
                        title="🚀 Boost rimosso",
                        description=f"{after.mention} ha rimosso il boost dal server.",
                        color=Color.red(),
                        fields=[
                            ("ID Utente", str(after.id), True)
                        ],
                        timestamp=True
                    )
                await send_log(after.guild, "boost", embed)

        # Log inviti
        @bot.event
        async def on_invite_create(invite):
            embed = log_embed(
                title="🔗 Invito creato",
                description=f"Invito creato da {invite.inviter.mention if invite.inviter else 'N/A'} per {invite.channel.mention}",
                color=Color.green(),
                fields=[
                    ("Codice", invite.code, True),
                    ("Scadenza", str(invite.max_age) if invite.max_age else "Mai", True)
                ],
                timestamp=True
            )
            await send_log(invite.guild, "inviti", embed)

        @bot.event
        async def on_invite_delete(invite):
            embed = log_embed(
                title="🔗 Invito eliminato",
                description=f"Invito eliminato per {invite.channel.mention}",
                color=Color.red(),
                fields=[
                    ("Codice", invite.code, True)
                ],
                timestamp=True
            )
            await send_log(invite.guild, "inviti", embed)

        # Log emoji
        @bot.event
        async def on_guild_emojis_update(guild, before, after):
            before_set = set(e.id for e in before)
            after_set = set(e.id for e in after)
            added = [e for e in after if e.id not in before_set]
            removed = [e for e in before if e.id not in after_set]
            for emoji in added:
                embed = log_embed(
                    title="😃 Emoji aggiunta",
                    description=f"Emoji `{emoji.name}` aggiunta.",
                    color=Color.green(),
                    fields=[
                        ("ID Emoji", str(emoji.id), True)
                    ],
                    thumbnail=emoji.url,
                    timestamp=True
                )
                await send_log(guild, "emoji", embed)
            for emoji in removed:
                embed = log_embed(
                    title="😃 Emoji rimossa",
                    description=f"Emoji `{emoji.name}` rimossa.",
                    color=Color.red(),
                    fields=[
                        ("ID Emoji", str(emoji.id), True)
                    ],
                    thumbnail=emoji.url,
                    timestamp=True
                )
                await send_log(guild, "emoji", embed)

        # Log webhook
        @bot.event
        async def on_webhooks_update(channel):
            embed = log_embed(
                title="🌐 Webhook aggiornato",
                description=f"Webhook aggiornato nel canale {channel.mention}",
                color=Color.blurple(),
                fields=[
                    ("ID Canale", str(channel.id), True)
                ],
                timestamp=True
            )
            await send_log(channel.guild, "webhook", embed)

        # Log integrazioni
        @bot.event
        async def on_guild_integrations_update(guild):
            embed = log_embed(
                title="🔌 Integrazioni aggiornate",
                description=f"Le integrazioni del server sono state aggiornate.",
                color=Color.blurple(),
                timestamp=True
            )
            await send_log(guild, "integrazioni", embed)

        # Log audit
        @bot.event
        async def on_audit_log_entry_create(entry):
            embed = log_embed(
                title="🕵️ Audit Log",
                description=f"Nuova voce nell'audit log: {entry.action}",
                color=Color.blurple(),
                fields=[
                    ("Utente", str(entry.user) if entry.user else "N/A", True),
                    ("Target", str(entry.target) if entry.target else "N/A", True)
                ],
                timestamp=True
            )
            await send_log(entry.guild, "audit", embed)

        # Log moderazione (kick)
        @bot.event
        async def on_member_kick(member):
            embed = log_embed(
                title="🛡️ Utente kickato",
                description=f"{member.mention} è stato kickato dal server.",
                color=Color.red(),
                fields=[
                    ("ID Utente", str(member.id), True)
                ],
                timestamp=True
            )
            await send_log(member.guild, "moderazione", embed)

        # Log permessi
        @bot.event
        async def on_guild_update(before, after):
            if before.verification_level != after.verification_level:
                embed = log_embed(
                    title="🔑 Livello verifica cambiato",
                    description=f"Livello verifica: `{before.verification_level}` → `{after.verification_level}`",
                    color=Color.orange(),
                    timestamp=True
                )
                await send_log(after, "permessi", embed)
            if before.name != after.name:
                embed = log_embed(
                    title="🏛️ Nome server cambiato",
                    description=f"Nome: `{before.name}` → `{after.name}`",
                    color=Color.orange(),
                    timestamp=True
                )
                await send_log(after, "guild_update", embed)

        # Log thread
        @bot.event
        async def on_thread_create(thread):
            embed = log_embed(
                title="🧵 Thread creato",
                description=f"Thread `{thread.name}` creato in {thread.parent.mention if thread.parent else 'N/A'}",
                color=Color.green(),
                fields=[
                    ("ID Thread", str(thread.id), True)
                ],
                timestamp=True
            )
            await send_log(thread.guild, "thread", embed)

        @bot.event
        async def on_thread_delete(thread):
            embed = log_embed(
                title="🧵 Thread eliminato",
                description=f"Thread `{thread.name}` eliminato.",
                color=Color.red(),
                fields=[
                    ("ID Thread", str(thread.id), True)
                ],
                timestamp=True
            )
            await send_log(thread.guild, "thread", embed)

        # Log stage
        @bot.event
        async def on_stage_instance_create(stage_instance):
            embed = log_embed(
                title="🎤 Stage creato",
                description=f"Stage `{stage_instance.topic}` creato in {stage_instance.channel.mention}",
                color=Color.green(),
                timestamp=True
            )
            await send_log(stage_instance.guild, "stage", embed)

        @bot.event
        async def on_stage_instance_delete(stage_instance):
            embed = log_embed(
                title="🎤 Stage eliminato",
                description=f"Stage `{stage_instance.topic}` eliminato in {stage_instance.channel.mention}",
                color=Color.red(),
                timestamp=True
            )
            await send_log(stage_instance.guild, "stage", embed)

        # Log stickers
        @bot.event
        async def on_guild_stickers_update(guild, before, after):
            before_set = set(s.id for s in before)
            after_set = set(s.id for s in after)
            added = [s for s in after if s.id not in before_set]
            removed = [s for s in before if s.id not in after_set]
            for sticker in added:
                embed = log_embed(
                    title="🏷️ Sticker aggiunto",
                    description=f"Sticker `{sticker.name}` aggiunto.",
                    color=Color.green(),
                    fields=[
                        ("ID Sticker", str(sticker.id), True)
                    ],
                    timestamp=True
                )
                await send_log(guild, "stickers", embed)
            for sticker in removed:
                embed = log_embed(
                    title="🏷️ Sticker rimosso",
                    description=f"Sticker `{sticker.name}` rimosso.",
                    color=Color.red(),
                    fields=[
                        ("ID Sticker", str(sticker.id), True)
                    ],
                    timestamp=True
                )
                await send_log(guild, "stickers", embed)

        # Log eventi programmati
        @bot.event
        async def on_scheduled_event_create(event):
            embed = log_embed(
                title="📅 Evento programmato creato",
                description=f"Evento `{event.name}` creato.",
                color=Color.green(),
                fields=[
                    ("ID Evento", str(event.id), True)
                ],
                timestamp=True
            )
            await send_log(event.guild, "scheduled_events", embed)

        @bot.event
        async def on_scheduled_event_delete(event):
            embed = log_embed(
                title="📅 Evento programmato eliminato",
                description=f"Evento `{event.name}` eliminato.",
                color=Color.red(),
                fields=[
                    ("ID Evento", str(event.id), True)
                ],
                timestamp=True
            )
            await send_log(event.guild, "scheduled_events", embed)

        # Sicurezza: catch errori globali
        @bot.event
        async def on_error(event, *args, **kwargs):
            logging.exception(f"Errore nell'evento {event}")

        bot.run(TOKEN)
