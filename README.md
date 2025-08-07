# Logging Bot 2025

## Avvio rapido

1. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
2. Inserisci il token del tuo bot Discord:
   - Metodo consigliato: crea una variabile d'ambiente `DISCORD_TOKEN` con il token del bot.
   - Oppure, modifica direttamente la riga nel file `bot.py` dove c'è scritto `INSERISCI_IL_TUO_TOKEN`.
3. Avvia il bot:
   ```bash
   python bot.py
   ```

## Funzionalità
- Logging completo di messaggi, canali, ruoli, nickname, avatar, join/leave, ban/unban, inviti, emoji, webhook, integrazioni, permessi, audit log, moderazione, boost, voice.
- Comando `/setup_logs` per creare automaticamente tutti i canali di log.

## Note
- Assicurati che il bot abbia i permessi amministratore e tutti gli intent attivi nel portale Discord Developer.
- Per modificare i nomi dei canali di log, edita il dizionario `DEFAULT_LOG_CHANNELS` in `bot.py`.