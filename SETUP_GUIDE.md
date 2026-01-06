# 🐺 Wolfbot Setup Guide

## Quick Start - Get Your Bot Running in 5 Minutes!

### Step 1: Discord Bot (REQUIRED) ⭐

1. **Create Your Bot:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click **"New Application"** 
   - Give it a name (e.g., "Wolfbot")
   - Click **"Create"**

2. **Get Your Bot Token:**
   - Click on **"Bot"** in the left sidebar
   - Click **"Add Bot"** if needed
   - Click **"Reset Token"** and then **"Copy"**
   - Open `.env` file and paste it after `DISCORD_TOKEN=`

3. **Enable Required Intents:**
   - Scroll down to **"Privileged Gateway Intents"**
   - ✅ Enable **"PRESENCE INTENT"**
   - ✅ Enable **"SERVER MEMBERS INTENT"**
   - ✅ Enable **"MESSAGE CONTENT INTENT"**
   - Click **"Save Changes"**

4. **Invite Bot to Your Server:**
   - Click on **"OAuth2"** → **"URL Generator"** in left sidebar
   - Under **SCOPES**, select: ☑️ `bot` ☑️ `applications.commands`
   - Under **BOT PERMISSIONS**, select: ☑️ `Administrator` (or customize)
   - Copy the generated URL at the bottom
   - Paste in your browser and select your Discord server
   - Click **"Authorize"**

**Your bot is now ready!** You can start it with `python src/bot.py`

---

## Step 2: OpenAI Integration (OPTIONAL) 🤖

**What it enables:** AI chat responses, image generation with DALL-E

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Click your profile icon → **"View API keys"**
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-...`)
6. Paste in `.env` after `OPENAI_API_KEY=`

**Note:** OpenAI requires payment. Check [pricing here](https://openai.com/pricing)

---

## Step 3: Twitch Integration (OPTIONAL) 📺

**What it enables:** Live stream notifications, clip sharing, stream monitoring

### Part A: Register Twitch Application

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. Click **"Register Your Application"**
3. Fill in:
   - **Name:** Wolfbot (or your bot name)
   - **OAuth Redirect URLs:** `http://localhost:3000`
   - **Category:** Chat Bot
4. Click **"Create"**
5. Click **"Manage"** on your application
6. Copy **"Client ID"** → paste in `.env` after `TWITCH_CLIENT_ID=`
7. Click **"New Secret"** → Copy and paste after `TWITCH_CLIENT_SECRET=`

### Part B: Get Access Token (Choose One Method)

**Method 1: Twitch CLI (Easiest)**
```bash
# Install Twitch CLI: https://dev.twitch.tv/docs/cli/
twitch token -u -s "channel:read:subscriptions channel:read:redemptions"
```
Copy the Access Token and Refresh Token to `.env`

**Method 2: Manual OAuth**
1. Replace `YOUR_CLIENT_ID` in this URL:
```
https://id.twitch.tv/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:3000&response_type=code&scope=channel:read:subscriptions+channel:read:redemptions
```
2. Visit the URL and authorize
3. Copy the `code` from the redirect URL
4. Exchange code for tokens (see [Twitch Auth Docs](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/))

### Part C: Get Your Broadcaster ID

**Easy Way:** Use [StreamWeasels Tool](https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/)

**Manual Way:**
```bash
curl -X GET 'https://api.twitch.tv/helix/users?login=YOUR_CHANNEL_NAME' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Client-Id: YOUR_CLIENT_ID'
```
The response contains your `"id"` - that's your broadcaster ID

---

## Step 4: Discord Server IDs (For Twitch Integration) 🆔

### Enable Developer Mode First:
1. Open Discord
2. Settings ⚙️ → **App Settings** → **Advanced**
3. Enable **"Developer Mode"** ✅

### Get Your IDs:

**Server (Guild) ID:**
- Right-click your server name → **"Copy Server ID"**

**Role ID:** (for "Live" notification role)
- Server Settings → Roles
- Right-click the role → **"Copy Role ID"**

**Channel IDs:** (for announcements, clips, etc.)
- Right-click each channel → **"Copy Channel ID"**

Paste all IDs in the `.env` file in their respective places.

---

## 📋 Setup Checklist

- [ ] Created Discord bot application
- [ ] Copied Discord bot token to `.env`
- [ ] Enabled all 3 Privileged Gateway Intents
- [ ] Invited bot to Discord server
- [ ] (Optional) Set up OpenAI API key
- [ ] (Optional) Set up Twitch application
- [ ] (Optional) Got Twitch access tokens
- [ ] (Optional) Got Discord server/channel/role IDs
- [ ] Saved `.env` file
- [ ] Ready to start bot: `python src/bot.py`

---

## 🚀 Running Your Bot

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Start the bot
python src/bot.py
```

If everything is configured correctly, you should see:
```
✓ Bot logged in as YourBotName#1234
✓ Connected to X servers
```

---

## 🆘 Troubleshooting

### Bot won't start / "Privileged intent provided is not enabled"
- Go to Discord Developer Portal → Your App → Bot
- Enable all 3 Privileged Gateway Intents
- Save and restart bot

### Bot can't read messages
- Enable **MESSAGE CONTENT INTENT** in Discord Developer Portal

### "DISCORD_TOKEN is not configured"
- Check that `.env` file is in the project root
- Make sure token is pasted correctly (no extra spaces)
- Token should not be in quotes

### Twitch integration not working
- Verify access token hasn't expired
- Check all Twitch credentials are correct
- Make sure channel IDs and guild ID are valid

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

---

## 📚 Additional Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [OpenAI Platform](https://platform.openai.com/)
- [Twitch Developer Docs](https://dev.twitch.tv/docs/)
- [API Manager Guide](API_MANAGER_GUIDE.md)

---

## 🔒 Security Tips

- ⚠️ **NEVER share your `.env` file**
- ⚠️ **NEVER commit `.env` to version control**
- ⚠️ **Keep your bot token secret**
- If you accidentally expose your token, reset it immediately in Discord Developer Portal
- `.env` is already in `.gitignore` - don't remove it!

---

**Need more help?** Check the main [README.md](README.md) or open an issue on GitHub.

Happy botting! 🐺✨
