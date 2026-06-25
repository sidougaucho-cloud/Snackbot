import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "TON_TOKEN_ICI")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))  # Ton ID Telegram
ADMIN_USERNAME = "@keyzer135"

logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────
# BASE DE DONNÉES EN MÉMOIRE
# (remplace par SQLite si tu veux persistance)
# ─────────────────────────────────────────────
# soldes[user_id] = float
soldes = {}

# produits : chaque produit a un id unique
# structure : { "id": str, "nom": str, "prix": float, "contenu": str, "disponible": bool }
produits = {
    # OTACOS
    "ot_01": {"cat": "otacos", "nom": "Bon Otacos 5€", "prix": 3.50, "contenu": "CODE: OTACOS-XXXX", "disponible": True},
    "ot_02": {"cat": "otacos", "nom": "Bon Otacos 10€", "prix": 7.00, "contenu": "CODE: OTACOS-YYYY", "disponible": True},
    # AUTRE SNACK
    "sn_01": {"cat": "snack", "nom": "Bon KFC 5€", "prix": 3.50, "contenu": "CODE: KFC-XXXX", "disponible": True},
    "sn_02": {"cat": "snack", "nom": "Bon McDonald's 5€", "prix": 3.50, "contenu": "CODE: MC-XXXX", "disponible": True},
    # TRADINN
    "tr_01": {"cat": "tradinn", "nom": "Crédit Tradinn 10€", "prix": 7.00, "contenu": "CODE: TR-XXXX", "disponible": True},
    "tr_02": {"cat": "tradinn", "nom": "Crédit Tradinn 20€", "prix": 13.00, "contenu": "CODE: TR-YYYY", "disponible": True},
    # RECHERCHE OSNIT (non consommable, reste dispo)
    "os_01": {"cat": "osnit", "nom": "Recherche basique", "prix": 2.00, "contenu": "Résultat envoyé par l'admin sous 24h.", "disponible": True},
    "os_02": {"cat": "osnit", "nom": "Recherche approfondie", "prix": 5.00, "contenu": "Résultat envoyé par l'admin sous 48h.", "disponible": True},
}

CATEGORIES = {
    "otacos": "🌯 Otacos",
    "snack": "🍔 Autre snack",
    "tradinn": "🎮 Tradinn",
    "osnit": "🔍 Recherche osnit",
}

# Catégories où le produit disparaît après achat
DISPARAIT_APRES_ACHAT = {"otacos", "snack", "tradinn"}

# État conversation recharge
ATTENTE_MONTANT = 1

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_solde(user_id):
    return soldes.get(user_id, 0.0)

def set_solde(user_id, montant):
    soldes[user_id] = round(montant, 2)

def is_admin(user_id):
    return user_id == ADMIN_ID

def produits_par_cat(cat):
    return {pid: p for pid, p in produits.items() if p["cat"] == cat and p["disponible"]}

def menu_principal_keyboard(user_id):
    kb = [
        [InlineKeyboardButton("🛍️ Produits", callback_data="categories")],
        [InlineKeyboardButton(f"💰 Mon solde : {get_solde(user_id):.2f}€", callback_data="solde")],
        [InlineKeyboardButton("➕ Recharger mon solde", callback_data="recharger")],
    ]
    if is_admin(user_id):
        kb.append([InlineKeyboardButton("⚙️ Panel Admin", callback_data="admin")])
    return InlineKeyboardMarkup(kb)

# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        f"👋 Bienvenue sur le shop, {user.first_name} !\n\n"
        f"Ici tu peux acheter des bons cadeaux, crédits et bien plus encore.\n\n"
        f"🛒 Parcours nos catégories, recharge ton solde et profite !\n\n"
        f"Pour toute question, contacte {ADMIN_USERNAME} 🆘"
    )
    await update.message.reply_text(msg, reply_markup=menu_principal_keyboard(user.id))

# ─────────────────────────────────────────────
# RETOUR MENU
# ─────────────────────────────────────────────
async def retour_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    msg = (
        f"🏠 Menu principal\n\n"
        f"💰 Ton solde : *{get_solde(user.id):.2f}€*"
    )
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=menu_principal_keyboard(user.id))

# ─────────────────────────────────────────────
# SOLDE
# ─────────────────────────────────────────────
async def show_solde(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Recharger", callback_data="recharger")],
        [InlineKeyboardButton("🔙 Retour", callback_data="menu")],
    ])
    await query.edit_message_text(
        f"💰 *Ton solde actuel*\n\n*{get_solde(user.id):.2f}€*",
        parse_mode="Markdown",
        reply_markup=kb
    )

# ─────────────────────────────────────────────
# CATÉGORIES
# ─────────────────────────────────────────────
async def show_categories(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = []
    for cat_id, cat_nom in CATEGORIES.items():
        kb.append([InlineKeyboardButton(cat_nom, callback_data=f"cat:{cat_id}")])
    kb.append([InlineKeyboardButton("🔙 Retour", callback_data="menu")])
    await query.edit_message_text(
        "📂 *Choisir une catégorie :*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def show_produits(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.split("cat:")[1]
    cat_nom = CATEGORIES.get(cat, cat)
    dispo = produits_par_cat(cat)

    kb = []
    if not dispo:
        kb.append([InlineKeyboardButton("❌ Aucun produit disponible", callback_data="noop")])
    else:
        for pid, p in dispo.items():
            kb.append([InlineKeyboardButton(f"{p['nom']} — {p['prix']:.2f}€", callback_data=f"prod:{pid}")])
    kb.append([InlineKeyboardButton("🔙 Catégories", callback_data="categories")])

    await query.edit_message_text(
        f"{cat_nom}\n\n🛒 *Produits disponibles :*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ─────────────────────────────────────────────
# FICHE PRODUIT
# ─────────────────────────────────────────────
async def show_produit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = query.data.split("prod:")[1]
    p = produits.get(pid)

    if not p or not p["disponible"]:
        await query.edit_message_text(
            "❌ Ce produit n'est plus disponible.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Retour", callback_data="categories")]])
        )
        return

    user_id = query.from_user.id
    solde = get_solde(user_id)
    peut_acheter = solde >= p["prix"]

    if peut_acheter:
        bouton_achat = InlineKeyboardButton(f"✅ Acheter ({p['prix']:.2f}€)", callback_data=f"acheter:{pid}")
    else:
        bouton_achat = InlineKeyboardButton("💸 Solde insuffisant — Recharger", callback_data="recharger")

    kb = InlineKeyboardMarkup([
        [bouton_achat],
        [InlineKeyboardButton("🔙 Retour", callback_data=f"cat:{p['cat']}")],
    ])

    await query.edit_message_text(
        f"*{p['nom']}*\n\n"
        f"💰 Prix : *{p['prix']:.2f}€*\n"
        f"💳 Ton solde : *{solde:.2f}€*",
        parse_mode="Markdown",
        reply_markup=kb
    )

# ─────────────────────────────────────────────
# ACHAT
# ─────────────────────────────────────────────
async def acheter(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = query.data.split("acheter:")[1]
    p = produits.get(pid)
    user = query.from_user

    if not p or not p["disponible"]:
        await query.edit_message_text("❌ Ce produit n'est plus disponible.")
        return

    solde = get_solde(user.id)
    if solde < p["prix"]:
        await query.edit_message_text(
            f"❌ Solde insuffisant.\n\nTon solde : *{solde:.2f}€*\nPrix : *{p['prix']:.2f}€*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Recharger", callback_data="recharger")]])
        )
        return

    # Déduire le solde
    set_solde(user.id, solde - p["prix"])

    # Faire disparaître si catégorie concernée
    if p["cat"] in DISPARAIT_APRES_ACHAT:
        produits[pid]["disponible"] = False

    # Notifier l'admin
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"🛒 *Nouvelle commande*\n\n"
            f"Client : {user.first_name} (@{user.username or 'sans pseudo'}) — ID: {user.id}\n"
            f"Produit : {p['nom']}\n"
            f"Prix : {p['prix']:.2f}€\n"
            f"Nouveau solde client : {get_solde(user.id):.2f}€",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu principal", callback_data="menu")]])
    await query.edit_message_text(
        f"✅ *Achat confirmé !*\n\n"
        f"Produit : *{p['nom']}*\n\n"
        f"📦 *Ton contenu :*\n`{p['contenu']}`\n\n"
        f"💰 Solde restant : *{get_solde(user.id):.2f}€*",
        parse_mode="Markdown",
        reply_markup=kb
    )

# ─────────────────────────────────────────────
# RECHARGE — ConversationHandler
# ─────────────────────────────────────────────
async def recharger_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["recharge_msg_id"] = query.message.message_id
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Annuler", callback_data="menu")]])
    await query.edit_message_text(
        "➕ *Recharger mon solde*\n\n"
        "Envoie le montant souhaité (ex: `10` ou `25.50`) :",
        parse_mode="Markdown",
        reply_markup=kb
    )
    return ATTENTE_MONTANT

async def recharger_montant(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    texte = update.message.text.strip().replace(",", ".")

    try:
        montant = float(texte)
        if montant <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Montant invalide. Envoie un nombre (ex: `10` ou `15.50`).", parse_mode="Markdown")
        return ATTENTE_MONTANT

    # Notifier l'admin
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"💳 *Demande de recharge*\n\n"
            f"Client : {user.first_name} (@{user.username or 'sans pseudo'}) — ID: {user.id}\n"
            f"Montant demandé : *{montant:.2f}€*\n\n"
            f"Envoie-lui le lien PayPal pour ce montant.",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    # Supprimer le message de l'utilisateur
    try:
        await update.message.delete()
    except Exception:
        pass

    # Répondre dans la fenêtre bot
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu principal", callback_data="menu")]])
    await ctx.bot.send_message(
        user.id,
        f"⏳ *Demande de recharge envoyée !*\n\n"
        f"Montant : *{montant:.2f}€*\n\n"
        f"Un administrateur va t'envoyer le lien PayPal très prochainement.\n\n"
        f"Contact : {ADMIN_USERNAME} 🆘",
        parse_mode="Markdown",
        reply_markup=kb
    )
    return ConversationHandler.END

async def recharger_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    await query.edit_message_text(
        f"🏠 Menu principal\n\n💰 Ton solde : *{get_solde(user.id):.2f}€*",
        parse_mode="Markdown",
        reply_markup=menu_principal_keyboard(user.id)
    )
    return ConversationHandler.END

# ─────────────────────────────────────────────
# PANEL ADMIN
# ─────────────────────────────────────────────
async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("Accès refusé.", show_alert=True)
        return

    total_produits = sum(1 for p in produits.values() if p["disponible"])
    total_soldes = sum(soldes.values())

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Créditer un solde", callback_data="admin_crediter")],
        [InlineKeyboardButton("📦 Gérer les produits", callback_data="admin_produits")],
        [InlineKeyboardButton("🔙 Retour", callback_data="menu")],
    ])
    await query.edit_message_text(
        f"⚙️ *Panel Admin*\n\n"
        f"Produits disponibles : {total_produits}\n"
        f"Soldes totaux en circulation : {total_soldes:.2f}€\n"
        f"Utilisateurs avec solde : {len(soldes)}",
        parse_mode="Markdown",
        reply_markup=kb
    )

async def admin_crediter(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Retour", callback_data="admin")]])
    await query.edit_message_text(
        "💰 *Créditer un solde*\n\n"
        "Utilise la commande :\n`/crediter USER_ID MONTANT`\n\n"
        "Exemple : `/crediter 123456789 15.00`",
        parse_mode="Markdown",
        reply_markup=kb
    )

async def cmd_crediter(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = ctx.args
    if len(args) != 2:
        await update.message.reply_text("Usage : /crediter USER_ID MONTANT")
        return
    try:
        uid = int(args[0])
        montant = float(args[1].replace(",", "."))
        if montant <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Paramètres invalides.")
        return

    ancien = get_solde(uid)
    set_solde(uid, ancien + montant)
    nouveau = get_solde(uid)

    # Notifier le client
    try:
        await ctx.bot.send_message(
            uid,
            f"✅ *Ton solde a été rechargé !*\n\n"
            f"Montant ajouté : *+{montant:.2f}€*\n"
            f"Nouveau solde : *{nouveau:.2f}€*",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ Solde de {uid} crédité.\nAncien : {ancien:.2f}€ → Nouveau : {nouveau:.2f}€"
    )

async def admin_produits(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    lines = []
    for pid, p in produits.items():
        statut = "✅" if p["disponible"] else "❌"
        lines.append(f"{statut} [{pid}] {p['nom']} — {p['prix']:.2f}€")
    msg = "📦 *Produits*\n\n" + "\n".join(lines) + "\n\nPour modifier, édite directement le code."
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Retour", callback_data="admin")]])
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=kb)

# Noop (bouton désactivé)
async def noop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ConversationHandler pour recharge
    conv_recharge = ConversationHandler(
        entry_points=[CallbackQueryHandler(recharger_start, pattern="^recharger$")],
        states={
            ATTENTE_MONTANT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recharger_montant),
            ],
        },
        fallbacks=[CallbackQueryHandler(recharger_cancel, pattern="^menu$")],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crediter", cmd_crediter))
    app.add_handler(conv_recharge)
    app.add_handler(CallbackQueryHandler(retour_menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(show_solde, pattern="^solde$"))
    app.add_handler(CallbackQueryHandler(show_categories, pattern="^categories$"))
    app.add_handler(CallbackQueryHandler(show_produits, pattern="^cat:"))
    app.add_handler(CallbackQueryHandler(show_produit, pattern="^prod:"))
    app.add_handler(CallbackQueryHandler(acheter, pattern="^acheter:"))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin$"))
    app.add_handler(CallbackQueryHandler(admin_crediter, pattern="^admin_crediter$"))
    app.add_handler(CallbackQueryHandler(admin_produits, pattern="^admin_produits$"))
    app.add_handler(CallbackQueryHandler(noop, pattern="^noop$"))

    print("✅ Bot démarré.")
    app.run_polling()

if __name__ == "__main__":
    main()
