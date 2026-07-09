# 🚍 Short Bus Raid Manager

A Discord bot for organizing **Star Wars: The Old Republic** Operations and raid
signups — with a built-in moderation toolkit. Works across multiple servers.

## ✨ Raid Features

- 🎲 Random Operation Wheel (`/raid spin`) — instantly creates an 8-man raid with
  a random operation and difficulty
- 📅 Full raid creation wizard (`/raid schedule`): faction → operation/lair boss →
  difficulty → raid size → date → time → timezone → announcement channel →
  ping type → review → post
- 👑 Lair Bosses are selectable alongside full Operations, with SWTOR-accurate
  difficulty restrictions (no Nightmare Mode where it doesn't exist in-game)
- 🛡️ Tank / 💚 Healer / ⚔️ DPS / 🪑 Bench / 🌊 Floater signup
- 🕗 Every raid shows a real Discord timestamp (`<t:...>`) that auto-converts to
  each viewer's own local time, alongside the plain-text date/time
- 🔒 Officer controls on the live board: Lock/Unlock, Finish, Rebuild Board
- ⏰ Automatic reminders at 24h and 30m before raid time, plus a "starting now"
  ping that auto-locks the raid
- 🧹 Auto-deletes the raid post 2 hours after the scheduled start, with a random
  Short Bus cleanup message
- ❌ Leave raid, automatic role limits (correct for both 8-man and 16-man)
- ✅ Date/time validation in the wizard (rejects past dates and unparseable times)

All content (Operations + Lair Bosses) lives in one file, `utils/swtor_content.py` —
adding new raid content when SWTOR ships it is a one-line change there.

## 🛡️ Moderation Features

All under `/mod`:

- `kick` — kick a member
- `ban` / `unban` — ban or unban a member
- `timeout` / `untimeout` — temporarily mute a member (`10m`, `1h`, `3d`, max 28d)
- `warn` — log a warning against a member
- `warnings` — view a member's warning history
- `clearwarnings` — wipe a member's warnings

Every action is:
- Permission-checked against real Discord permissions (kick/ban/moderate/manage_guild),
  not hardcoded role names — works on any server without setup
- Blocked against moderating yourself, the bot, or anyone with an equal/higher role
- Logged to the database and (if configured) posted to a mod-log channel
- Sent to the target as a DM, best-effort

Configure per-server with `/settings`:
- `/settings modlog #channel` — where moderation actions get posted
- `/settings raidchannel #channel` — default raid announcement channel
- `/settings officerrole @role` — who counts as a raid officer (falls back to
  Administrator or a role literally named Officer/Raid Officer/Guild Master
  if unset)
- `/settings raidleaderrole @role` — who counts as a raid leader
- `/settings view` — see current settings

## 🛠️ Built With

- Python 3.14
- discord.py 2.5
- SQLite

## 🚀 Setup

1. Copy `.env.example` to `.env` and fill in `DISCORD_TOKEN` (from the
   [Discord Developer Portal](https://discord.com/developers/applications)).
2. Optionally set `DEV_GUILD_ID` in `.env` to your test server's ID for
   instant slash-command syncing while developing. Leave it blank in
   production — the bot will sync commands globally so it works on every
   server it's invited to.
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the bot:
   ```
   python bot.py
   ```

When inviting the bot to a server, make sure its OAuth2 invite includes
the `applications.commands` and `bot` scopes, along with the
**Kick Members**, **Ban Members**, **Moderate Members**, and
**Manage Guild** permissions if you want to use moderation and settings
commands there.

## 📁 Project Structure

- `cogs/` — Discord command groups (raid, moderation, settings)
- `services/` — business logic and database access
- `models/` — data classes
- `views/` — Discord UI components (buttons, modals, selects)
- `utils/` — shared helpers (embeds, logging, duration parsing)
- `logs/` — rotating log files (created automatically, not committed)

## 📄 License

This project is licensed under the MIT License.

---

Made with ❤️ by **TheRealDaakal**
