import json
import pytz  
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

WAITING_FOR_ACCESS_CODE = "WAITING_FOR_ACCESS_CODE"
CHOOSING = "CHOOSING"
WAITING_CATEGORY_NAME = "WAITING_CATEGORY_NAME"
WAITING_PRODUCT_NAME = "WAITING_PRODUCT_NAME"
WAITING_PRODUCT_PRICE = "WAITING_PRODUCT_PRICE"
WAITING_PRODUCT_DESCRIPTION = "WAITING_PRODUCT_DESCRIPTION"
WAITING_PRODUCT_MEDIA = "WAITING_PRODUCT_MEDIA"
SELECTING_CATEGORY = "SELECTING_CATEGORY"
SELECTING_CATEGORY_TO_DELETE = "SELECTING_CATEGORY_TO_DELETE"
SELECTING_PRODUCT_TO_DELETE = "SELECTING_PRODUCT_TO_DELETE"
WAITING_CONTACT_USERNAME = "WAITING_CONTACT_USERNAME"
SELECTING_PRODUCT_TO_EDIT = "SELECTING_PRODUCT_TO_EDIT"
EDITING_PRODUCT_FIELD = "EDITING_PRODUCT_FIELD"
WAITING_NEW_VALUE = "WAITING_NEW_VALUE"
WAITING_BANNER_IMAGE = "WAITING_BANNER_IMAGE"
WAITING_BROADCAST_MESSAGE = "WAITING_BROADCAST_MESSAGE"
WAITING_ORDER_BUTTON_CONFIG = "WAITING_ORDER_BUTTON_CONFIG"
WAITING_WELCOME_MESSAGE = "WAITING_WELCOME_MESSAGE"
EDITING_CATEGORY = "EDITING_CATEGORY"
WAITING_NEW_CATEGORY_NAME = "WAITING_NEW_CATEGORY_NAME"
WAITING_BUTTON_NAME = "WAITING_BUTTON_NAME"
WAITING_BUTTON_VALUE = "WAITING_BUTTON_VALUE"
WAITING_BROADCAST_EDIT = "WAITING_BROADCAST_EDIT"
WAITING_GROUP_NAME = "WAITING_GROUP_NAME"
WAITING_GROUP_USER = "WAITING_GROUP_USER"


class AdminFeatures:
    def __init__(self, users_file: str = 'data/users.json', access_codes_file: str = 'data/access_codes.json', broadcasts_file: str = 'data/broadcasts.json'):
        self.users_file = users_file
        self.access_codes_file = access_codes_file
        self.broadcasts_file = broadcasts_file
        self._users = self._load_users()
        self._access_codes = self._load_access_codes()
        self.broadcasts = self._load_broadcasts()

    def _load_access_codes(self):
        """Charge les codes d'accès depuis le fichier"""
        try:
            with open(self.access_codes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            print(f"Access codes file not found: {self.access_codes_file}")
            return {"authorized_users": []}
        except json.JSONDecodeError as e:
            print(f"Error decoding access codes file: {e}")
            return {"authorized_users": []}
        except Exception as e:
            print(f"Unexpected error loading access codes: {e}")
            return {"authorized_users": []}

    def is_user_authorized(self, user_id: int) -> bool:
        """Vérifie si l'utilisateur est autorisé"""
        # Recharger les codes d'accès à chaque vérification
        self._access_codes = self._load_access_codes()
        
        # Convertir l'ID en nombre et vérifier sa présence
        return int(user_id) in self._access_codes.get("authorized_users", [])

    def is_user_banned(self, user_id: int) -> bool:
        """Vérifie si l'utilisateur est banni"""
        self._access_codes = self._load_access_codes()
        return int(user_id) in self._access_codes.get("banned_users", [])

    def reload_access_codes(self):
        """Recharge les codes d'accès depuis le fichier"""
        self._access_codes = self._load_access_codes()
        return self._access_codes.get("authorized_users", [])

    def _load_users(self):
        """Charge les utilisateurs depuis le fichier"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_users(self):
        """Sauvegarde les utilisateurs"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self._users, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des utilisateurs : {e}")

    def _create_message_keyboard(self):
        """Crée le clavier standard pour les messages"""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Menu Principal", callback_data="start_cmd")
        ]])

    def _load_broadcasts(self):
        """Charge les broadcasts depuis le fichier"""
        try:
            with open(self.broadcasts_file, 'r', encoding='utf-8') as f:
                broadcasts = json.load(f)
                # Vérifier et corriger la structure de chaque broadcast
                for broadcast_id, broadcast in broadcasts.items():
                    if 'message_ids' not in broadcast:
                        broadcast['message_ids'] = {}
                    # Assurer que les user_ids sont des strings
                    if 'message_ids' in broadcast:
                        broadcast['message_ids'] = {
                            str(user_id): msg_id 
                            for user_id, msg_id in broadcast['message_ids'].items()
                        }
                return broadcasts
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print("Erreur de décodage JSON, création d'un nouveau fichier broadcasts")
            return {}

    def _save_broadcasts(self):
        """Sauvegarde les broadcasts"""
        try:
            with open(self.broadcasts_file, 'w', encoding='utf-8') as f:
                json.dump(self.broadcasts, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des broadcasts : {e}")

    def _save_access_codes(self):
        """Sauvegarde les codes d'accès"""
        try:
            with open(self.access_codes_file, 'w', encoding='utf-8') as f:
                json.dump(self._access_codes, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des codes d'accès : {e}")

    def is_user_in_group(self, user_id: int, group_name: str) -> bool:
        """Vérifie si l'utilisateur appartient à un groupe spécifique"""
        self._access_codes = self._load_access_codes()
        groups = self._access_codes.get("groups", {})
        return int(user_id) in groups.get(group_name, [])

    async def manage_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche le menu de gestion des groupes"""
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("➕ Créer un groupe", callback_data="create_group")],
            [InlineKeyboardButton("➕ Ajouter un utilisateur", callback_data="add_group_user")],
            [InlineKeyboardButton("❌ Retirer un utilisateur", callback_data="remove_group_user")],
            [InlineKeyboardButton("🗑️ Supprimer un groupe", callback_data="delete_group")],
            [InlineKeyboardButton("📋 Liste des groupes", callback_data="list_groups")],
            [InlineKeyboardButton("🔙 Retour", callback_data="admin")]
        ]

        await query.edit_message_text(
            "👥 *Gestion des groupes*\n\n"
            "Sélectionnez une action à effectuer :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return CHOOSING

    async def remove_group_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la liste des groupes pour retirer un utilisateur"""
        query = update.callback_query
        await query.answer()

        # Vérifie si des groupes existent
        groups = self._access_codes.get("groups", {})
        if not groups:
            await query.edit_message_text(
                "❌ Aucun groupe n'existe.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")
                ]]),
                parse_mode='Markdown'
            )
            return CHOOSING

        # Créer la liste des groupes qui ont au moins un membre
        keyboard = []
        for group_name, members in groups.items():
            if members:  # Ne montre que les groupes qui ont des membres
                keyboard.append([InlineKeyboardButton(
                    f"{group_name} ({len(members)} membres)",
                    callback_data=f"remove_from_group_{group_name}"
                )])

        if not keyboard:  # Si aucun groupe n'a de membres
            await query.edit_message_text(
                "❌ Aucun groupe ne contient de membres à retirer.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")
                ]]),
                parse_mode='Markdown'
            )
            return CHOOSING

        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")])

        await query.edit_message_text(
            "👥 *Retirer un utilisateur d'un groupe*\n\n"
            "Sélectionnez le groupe :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

        return CHOOSING

    async def select_user_to_remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la liste des utilisateurs d'un groupe pour en retirer un"""
        query = update.callback_query
        await query.answer()

        group_name = query.data.replace("remove_from_group_", "")
        members = self._access_codes.get("groups", {}).get(group_name, [])

        if not members:
            await query.edit_message_text(
                "❌ Ce groupe ne contient aucun membre.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="remove_group_user")
                ]]),
                parse_mode='Markdown'
            )
            return CHOOSING

        keyboard = []
        for user_id in members:
            try:
                # Récupérer les informations de l'utilisateur depuis le cache ou les données sauvegardées
                user_info = self._user_info.get(str(user_id), {"username": str(user_id)})
                display_name = user_info.get("username", str(user_id))
            
                keyboard.append([InlineKeyboardButton(
                    display_name,
                    callback_data=f"remove_user_{group_name}_{user_id}"
                )])
            except Exception as e:
                print(f"Erreur lors de la création du bouton pour l'utilisateur {user_id}: {e}")

        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="remove_group_user")])

        await query.edit_message_text(
            f"👥 *Retirer un utilisateur du groupe {group_name}*\n\n"
            "Sélectionnez l'utilisateur à retirer :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

        return CHOOSING

    async def remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Retire l'utilisateur sélectionné du groupe"""
        query = update.callback_query
        await query.answer()
    
        try:
            # Extraire les informations du callback_data
            parts = query.data.split("_")
            if len(parts) >= 4:  # S'assurer qu'il y a assez de parties
                group_name = parts[2]  # La troisième partie est le nom du groupe
                user_id = int(parts[3])  # La quatrième partie est l'ID utilisateur
            
                if group_name in self._access_codes.get("groups", {}) and user_id in self._access_codes["groups"][group_name]:
                    self._access_codes["groups"][group_name].remove(user_id)
                    self._save_access_codes()
            
                    await query.edit_message_text(
                        f"✅ Utilisateur retiré du groupe *{group_name}* avec succès!",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("➕ Retirer un autre utilisateur", callback_data="remove_group_user")],
                            [InlineKeyboardButton("📋 Liste des groupes", callback_data="list_groups")],
                            [InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")]
                        ]),
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        "❌ L'utilisateur n'est plus dans ce groupe.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")
                        ]])
                    )
            else:
                raise ValueError("Format de callback_data invalide")
            
        except Exception as e:
            print(f"Erreur lors du retrait de l'utilisateur: {e}")
            await query.edit_message_text(
                "❌ Une erreur s'est produite lors du retrait de l'utilisateur.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")
                ]])
            )
    
        return CHOOSING

    async def select_user_to_remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la liste des utilisateurs d'un groupe pour en retirer un"""
        query = update.callback_query
        await query.answer()
    
        group_name = query.data.replace("remove_from_group_", "")
        members = self._access_codes.get("groups", {}).get(group_name, [])
    
        if not members:
            await query.edit_message_text(
                f"❌ Le groupe *{group_name}* n'a pas de membres.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="remove_group_user")
                ]]),
                parse_mode='Markdown'
            )
            return CHOOSING

        keyboard = []
        for member_id in members:
            user_data = self._users.get(str(member_id), {})
            username = user_data.get('username', '')
            first_name = user_data.get('first_name', '')
            display_name = f"@{username}" if username else first_name or str(member_id)
            keyboard.append([InlineKeyboardButton(
                display_name,
                callback_data=f"remove_user_{group_name}_{member_id}"
            )])
    
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="remove_group_user")])

        await query.edit_message_text(
            f"👥 *Retirer un utilisateur du groupe {group_name}*\n\n"
            "Sélectionnez l'utilisateur à retirer :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return CHOOSING

    #async def remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Retire l'utilisateur sélectionné du groupe"""
        query = update.callback_query
        await query.answer()
    
        _, group_name, user_id = query.data.split("_", 2)
        user_id = int(user_id)
    
        if user_id in self._access_codes["groups"][group_name]:
            self._access_codes["groups"][group_name].remove(user_id)
            self._save_access_codes()
        
            await query.edit_message_text(
                f"✅ Utilisateur retiré du groupe *{group_name}* avec succès!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Retirer un autre utilisateur", callback_data="remove_group_user")],
                    [InlineKeyboardButton("📋 Liste des groupes", callback_data="list_groups")],
                    [InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")]
                ]),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ L'utilisateur n'est plus dans ce groupe.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")
                ]])
            )
        return CHOOSING

    async def delete_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la liste des groupes à supprimer"""
        query = update.callback_query
        await query.answer()

        groups = self._access_codes.get("groups", {})
        if not groups:
            await query.edit_message_text(
                "❌ Aucun groupe n'existe.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")
                ]])
            )
            return CHOOSING

        keyboard = []
        for group_name in groups.keys():
            keyboard.append([InlineKeyboardButton(
                f"🗑️ {group_name}",
                callback_data=f"confirm_delete_group_{group_name}"
            )])
    
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")])

        await query.edit_message_text(
            "🗑️ *Supprimer un groupe*\n\n"
            "Sélectionnez le groupe à supprimer :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return CHOOSING

    async def confirm_delete_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Supprime le groupe sélectionné"""
        query = update.callback_query
        await query.answer()
    
        group_name = query.data.replace("confirm_delete_group_", "")
    
        if group_name in self._access_codes.get("groups", {}):
            del self._access_codes["groups"][group_name]
            self._save_access_codes()
        
            await query.edit_message_text(
                f"✅ Groupe *{group_name}* supprimé avec succès!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗑️ Supprimer un autre groupe", callback_data="delete_group")],
                    [InlineKeyboardButton("📋 Liste des groupes", callback_data="list_groups")],
                    [InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")]
                ]),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ Ce groupe n'existe plus.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")
                ]])
            )
        return CHOOSING

    async def list_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la liste des groupes et leurs membres"""
        query = update.callback_query
        await query.answer()

        text = "📋 *Liste des groupes*\n\n"
        groups = self._access_codes.get("groups", {})

        def escape_markdown(text):
            """Échappe les caractères spéciaux Markdown"""
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f"\\{char}")
            return text

        if not groups:
            text += "Aucun groupe créé."
        else:
            for group_name, members in groups.items():
                text += f"*{escape_markdown(group_name)}*\n"
                if members:
                    for member_id in members:
                        user_data = self._users.get(str(member_id), {})
                        username = user_data.get('username', '')
                        first_name = user_data.get('first_name', '')
                        if username:
                            display_name = f"@{escape_markdown(username)}"
                        else:
                            display_name = escape_markdown(first_name) if first_name else str(member_id)
                        text += f"└ {display_name}\n"
                else:
                    text += "└ Aucun membre\n"
                text += "\n"

        keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")]]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return CHOOSING

    async def start_create_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Démarre le processus de création d'un groupe"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "👥 *Création d'un nouveau groupe*\n\n"
            "Envoyez le nom du nouveau groupe :",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Annuler", callback_data="manage_groups")
            ]]),
            parse_mode='Markdown'
        )
        return WAITING_GROUP_NAME

    async def handle_group_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la création d'un nouveau groupe"""
        group_name = update.message.text.strip()
    
        # Vérifier si le groupe existe déjà
        if "groups" in self._access_codes and group_name in self._access_codes["groups"]:
            await update.message.reply_text(
                "❌ Ce groupe existe déjà.\n"
                "Veuillez choisir un autre nom:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Annuler", callback_data="manage_groups")
                ]])
            )
            return WAITING_GROUP_NAME

        # Créer le groupe
        if "groups" not in self._access_codes:
            self._access_codes["groups"] = {}
    
        self._access_codes["groups"][group_name] = []
        self._save_access_codes()

        # Supprimer les messages
        try:
            # Supprimer le message précédent
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id - 1
            )
            # Supprimer le message de l'utilisateur
            await update.message.delete()
        except Exception as e:
            print(f"Erreur lors de la suppression des messages: {e}")

        # Afficher le menu de gestion des groupes avec message de succès
        keyboard = [
            [InlineKeyboardButton("➕ Créer un groupe", callback_data="create_group")],
            [InlineKeyboardButton("➕ Ajouter un utilisateur", callback_data="add_group_user")],
            [InlineKeyboardButton("❌ Retirer un utilisateur", callback_data="remove_group_user")],
            [InlineKeyboardButton("🗑️ Supprimer un groupe", callback_data="delete_group")],
            [InlineKeyboardButton("📋 Liste des groupes", callback_data="list_groups")],
            [InlineKeyboardButton("🔙 Retour", callback_data="admin")]
        ]

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Groupe *{group_name}* créé avec succès!\n\n"
                 "👥 *Gestion des groupes*\n"
                 "Sélectionnez une action à effectuer :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
        return CHOOSING

    async def show_add_user_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la liste des groupes pour ajouter un utilisateur"""
        query = update.callback_query
        await query.answer()

        groups = self._access_codes.get("groups", {})
        if not groups:
            await query.edit_message_text(
                "❌ Aucun groupe n'existe.\n"
                "Créez d'abord un groupe.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")
                ]])
            )
            return CHOOSING

        keyboard = []
        for group_name in groups.keys():
            keyboard.append([InlineKeyboardButton(
                group_name,
                callback_data=f"select_group_{group_name}"
            )])
    
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")])

        await query.edit_message_text(
            "👥 *Ajouter un utilisateur*\n\n"
            "Sélectionnez le groupe :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return CHOOSING

    async def select_group_for_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la sélection du groupe pour ajouter un utilisateur"""
        query = update.callback_query
        await query.answer()
    
        group_name = query.data.replace("select_group_", "")
        context.user_data['selected_group'] = group_name

        await query.edit_message_text(
            f"👤 *Ajout d'un utilisateur au groupe {group_name}*\n\n"
            "Envoyez l'ID ou le @username de l'utilisateur :",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour", callback_data="add_group_user")
            ]]),
            parse_mode='Markdown'
        )
        return WAITING_GROUP_USER

    async def handle_group_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère l'ajout d'un utilisateur à un groupe"""
        user_input = update.message.text.strip()
        group_name = context.user_data.get('selected_group')
    
        if not group_name or group_name not in self._access_codes.get("groups", {}):
            await update.message.reply_text("❌ Erreur: groupe non trouvé.")
            return CHOOSING

        # Traiter l'entrée de l'utilisateur
        if user_input.startswith('@'):
            username = user_input[1:]
            user_id = None
            # Chercher l'ID correspondant au username
            for uid, data in self._users.items():
                if data.get('username') == username:
                    user_id = int(uid)
                    break
        else:
            try:
                user_id = int(user_input)
            except ValueError:
                await update.message.reply_text(
                    "❌ Format invalide. Envoyez un ID valide ou un @username:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Annuler", callback_data="manage_groups")
                    ]])
                )
                return WAITING_GROUP_USER

        if user_id is None:
            await update.message.reply_text(
                "❌ Utilisateur non trouvé.\n"
                "Envoyez un ID valide ou un @username:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Annuler", callback_data="manage_groups")
                ]])
            )
            return WAITING_GROUP_USER

        # Ajouter l'utilisateur au groupe
        if user_id not in self._access_codes["groups"][group_name]:
            self._access_codes["groups"][group_name].append(user_id)
            self._save_access_codes()

        # Supprimer les messages
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id - 1
            )
            await update.message.delete()
        except Exception as e:
            print(f"Erreur lors de la suppression des messages: {e}")

        # Afficher le menu avec confirmation
        keyboard = [
            [InlineKeyboardButton("➕ Ajouter un autre utilisateur", callback_data="add_group_user")],
            [InlineKeyboardButton("📋 Liste des groupes", callback_data="list_groups")],
            [InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")]
        ]

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Utilisateur ajouté au groupe *{group_name}* avec succès!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

        return CHOOSING

    async def select_group_for_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la sélection du groupe lors de la création d'une catégorie"""
        query = update.callback_query
        await query.answer()
    
        _, group_name, category_name = query.data.replace("select_group_for_category_", "").split("_", 2)
        user_id = update.effective_user.id
    
        # Vérifier que l'utilisateur est toujours membre du groupe
        if user_id not in self._access_codes["groups"].get(group_name, []):
            await query.edit_message_text(
                "❌ Vous n'êtes plus membre de ce groupe.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="admin")
                ]])
            )
            return CHOOSING
        
        # Créer la catégorie avec le préfixe du groupe
        full_category_name = f"{group_name}_{category_name}"
    
        if full_category_name in CATALOG:
            await query.edit_message_text(
                "❌ Cette catégorie existe déjà.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="admin")
                ]])
            )
            return CHOOSING
        
        CATALOG[full_category_name] = []
        save_catalog(CATALOG)
    
        await query.edit_message_text(
            f"✅ Catégorie *{category_name}* créée avec succès dans le groupe *{group_name}*!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Ajouter une autre catégorie", callback_data="add_category")],
                [InlineKeyboardButton("🔙 Retour", callback_data="admin")]
            ]),
            parse_mode='Markdown'
        )
        return CHOOSING

    async def handle_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /group"""
        try:
            # Vérifier si l'utilisateur est admin
            if str(update.effective_user.id) not in ADMIN_IDS:
                return

            # Supprimer la commande
            try:
                await update.message.delete()
            except Exception as e:
                print(f"Erreur lors de la suppression de la commande group: {e}")

            # Vérifier les arguments
            if not context.args or len(context.args) < 2:
                keyboard = [
                    [InlineKeyboardButton("➕ Créer un groupe", callback_data="create_group")],
                    [InlineKeyboardButton("➕ Ajouter un utilisateur", callback_data="add_group_user")],
                    [InlineKeyboardButton("❌ Retirer un utilisateur", callback_data="remove_group_user")],
                    [InlineKeyboardButton("🗑️ Supprimer un groupe", callback_data="delete_group")],
                    [InlineKeyboardButton("📋 Liste des groupes", callback_data="list_groups")],
                    [InlineKeyboardButton("🔙 Retour", callback_data="admin")]
                ]

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="👥 *Gestion des groupes*\n\n"
                         "Sélectionnez une action à effectuer :",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return

            action = context.args[0].lower()
            group_name = context.args[1]

            if action not in ['add', 'remove', 'create', 'delete']:
                message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Action invalide. Utilisez: add, remove, create, ou delete"
                )
                await asyncio.sleep(3)
                await message.delete()
                return

            # Créer un groupe
            if action == 'create':
                if "groups" not in self._access_codes:
                    self._access_codes["groups"] = {}
            
                if group_name in self._access_codes["groups"]:
                    message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ Ce groupe existe déjà."
                    )
                    await asyncio.sleep(3)
                    await message.delete()
                    return

                self._access_codes["groups"][group_name] = []
                self._save_access_codes()
            
                message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ Groupe '{group_name}' créé avec succès!"
                )
                await asyncio.sleep(3)
                await message.delete()
                return

            # Supprimer un groupe
            if action == 'delete':
                if group_name in self._access_codes.get("groups", {}):
                    del self._access_codes["groups"][group_name]
                    self._save_access_codes()
                    message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"✅ Groupe '{group_name}' supprimé avec succès!"
                    )
                else:
                    message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ Groupe non trouvé."
                    )
                await asyncio.sleep(3)
                await message.delete()
                return

            # Ajouter ou retirer un utilisateur
            if len(context.args) < 3:
                message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Utilisateur non spécifié."
                )
                await asyncio.sleep(3)
                await message.delete()
                return

            user_input = context.args[2]
        
            # Traiter l'entrée utilisateur
            if user_input.startswith('@'):
                username = user_input[1:]
                user_id = None
                for uid, data in self._users.items():
                    if data.get('username') == username:
                        user_id = int(uid)
                        break
            else:
                try:
                    user_id = int(user_input)
                except ValueError:
                    message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ Format d'ID utilisateur invalide."
                    )
                    await asyncio.sleep(3)
                    await message.delete()
                    return

            if user_id is None:
                message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Utilisateur non trouvé."
                )
                await asyncio.sleep(3)
                await message.delete()
                return

            if action == 'add':
                if group_name not in self._access_codes.get("groups", {}):
                    self._access_codes["groups"][group_name] = []
            
                if user_id not in self._access_codes["groups"][group_name]:
                    self._access_codes["groups"][group_name].append(user_id)
                    self._save_access_codes()
                    message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"✅ Utilisateur ajouté au groupe '{group_name}'!"
                    )
                else:
                    message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ L'utilisateur est déjà dans ce groupe."
                    )

            elif action == 'remove':
                if group_name in self._access_codes.get("groups", {}) and user_id in self._access_codes["groups"][group_name]:
                    self._access_codes["groups"][group_name].remove(user_id)
                    self._save_access_codes()
                    message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"✅ Utilisateur retiré du groupe '{group_name}'!"
                    )
                else:
                    message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ L'utilisateur n'est pas dans ce groupe."
                    )

            await asyncio.sleep(3)
            await message.delete()

        except Exception as e:
            print(f"Erreur dans handle_group_command: {e}")
            message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Une erreur est survenue."
            )
            await asyncio.sleep(3)
            await message.delete()

    async def ban_user(self, user_id: int) -> bool:
        """Banni un utilisateur"""
        try:
            # Convertir en int si c'est un string
            user_id = int(user_id)
        
            # Retirer l'utilisateur des codes d'accès s'il y est
            if user_id in self._access_codes.get("authorized_users", []):
                self._access_codes["authorized_users"].remove(user_id)
                self._save_access_codes()

            # Ajouter l'utilisateur à la liste des bannis si elle existe, sinon la créer
            if "banned_users" not in self._access_codes:
                self._access_codes["banned_users"] = []
        
            if user_id not in self._access_codes["banned_users"]:
                self._access_codes["banned_users"].append(user_id)
                self._save_access_codes()
        
            return True
        except Exception as e:
            print(f"Erreur lors du bannissement de l'utilisateur : {e}")
            return False

    async def unban_user(self, user_id: int) -> bool:
        """Débanni un utilisateur"""
        try:
            user_id = int(user_id)
            if "banned_users" in self._access_codes and user_id in self._access_codes["banned_users"]:
                self._access_codes["banned_users"].remove(user_id)
                self._save_access_codes()
            return True
        except Exception as e:
            print(f"Erreur lors du débannissement de l'utilisateur : {e}")
            return False

    async def show_banned_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la liste des utilisateurs bannis"""
        try:
            banned_users = self._access_codes.get("banned_users", [])
        
            text = "🚫 *Utilisateurs bannis*\n\n"
        
            if not banned_users:
                text += "Aucun utilisateur banni."
                keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="manage_users")]]
            else:
                text += "Sélectionnez un utilisateur pour le débannir :\n\n"
                keyboard = []
            
                for user_id in banned_users:
                    user_data = self._users.get(str(user_id), {})
                    username = user_data.get('username')
                    first_name = user_data.get('first_name')
                    last_name = user_data.get('last_name')
                
                    if username:
                        display_name = f"@{username}"
                    elif first_name and last_name:
                        display_name = f"{first_name} {last_name}"
                    elif first_name:
                        display_name = first_name
                    elif last_name:
                        display_name = last_name
                    else:
                        display_name = f"Utilisateur {user_id}"
                
                    text += f"• {display_name} (`{user_id}`)\n"
                    keyboard.append([InlineKeyboardButton(
                        f"🔓 Débannir {display_name}",
                        callback_data=f"unban_{user_id}"
                    )])
            
                keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="manage_users")])
        
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        
            return "CHOOSING"
        
        except Exception as e:
            print(f"Erreur dans show_banned_users : {e}")
            return "CHOOSING"

    async def handle_ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /ban"""
        try:
            # Supprimer la commande /ban
            try:
                await update.message.delete()
            except Exception as e:
                print(f"Erreur lors de la suppression de la commande ban: {e}")

            # Vérifier si l'utilisateur est admin
            if not self.is_user_authorized(update.effective_user.id):
                return

            # Vérifier les arguments
            if not context.args:
                message = await update.message.reply_text(
                    "❌ Usage : /ban <user_id> ou /ban @username"
                )
                # Supprimer le message après 3 secondes
                async def delete_message():
                    await asyncio.sleep(3)
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"Error deleting message: {e}")
                asyncio.create_task(delete_message())
                return

            target = context.args[0]
        
            # Si c'est un username
            if target.startswith('@'):
                username = target[1:]
                user_found = False
                for user_id, user_data in self._users.items():
                    if user_data.get('username') == username:
                        target = user_id
                        user_found = True
                        break
                if not user_found:
                    message = await update.message.reply_text("❌ Utilisateur non trouvé.")
                    # Supprimer le message après 3 secondes
                    async def delete_message():
                        await asyncio.sleep(3)
                        try:
                            await message.delete()
                        except Exception as e:
                            print(f"Error deleting message: {e}")
                    asyncio.create_task(delete_message())
                    return

            # Bannir l'utilisateur
            if await self.ban_user(target):
                message = await update.message.reply_text(f"✅ Utilisateur {target} banni avec succès.")
            else:
                message = await update.message.reply_text("❌ Erreur lors du bannissement.")

            # Supprimer le message de confirmation après 3 secondes
            async def delete_message():
                await asyncio.sleep(3)
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")
        
            asyncio.create_task(delete_message())

        except Exception as e:
            print(f"Erreur dans handle_ban_command : {e}")
            message = await update.message.reply_text("❌ Une erreur est survenue.")
        
            # Supprimer le message d'erreur après 3 secondes
            async def delete_message():
                await asyncio.sleep(3)
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")
        
            asyncio.create_task(delete_message())

    async def handle_unban_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère le débannissement depuis le callback"""
        try:
            query = update.callback_query
            user_id = int(query.data.replace("unban_", ""))
        
            if await self.unban_user(user_id):
                # Message temporaire
                confirmation = await query.edit_message_text(
                    f"✅ Utilisateur {user_id} débanni avec succès.",
                    parse_mode='Markdown'
                )
            
                # Attendre 2 secondes
                await asyncio.sleep(2)
            
                # Retourner à la liste des bannis
                await self.show_banned_users(update, context)
            else:
                await query.answer("❌ Erreur lors du débannissement.")
            
        except Exception as e:
            print(f"Erreur dans handle_unban_callback : {e}")
            await query.answer("❌ Une erreur est survenue.")

    async def register_user(self, user):
        """Enregistre ou met à jour un utilisateur"""
        user_id = str(user.id)
        paris_tz = pytz.timezone('Europe/Paris')
        paris_time = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(paris_tz)
        
        self._users[user_id] = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'last_seen': paris_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_users()

    async def handle_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Démarre le processus de diffusion"""
        try:
            context.user_data.clear()
            context.user_data['broadcast_chat_id'] = update.effective_chat.id
            
            keyboard = [
                [InlineKeyboardButton("❌ Annuler", callback_data="admin")]
            ]
            
            message = await update.callback_query.edit_message_text(
                "📢 *Nouveau message de diffusion*\n\n"
                "Envoyez le message que vous souhaitez diffuser aux utilisateurs autorisés.\n"
                "Vous pouvez envoyer du texte, des photos ou des vidéos.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            context.user_data['instruction_message_id'] = message.message_id
            return "WAITING_BROADCAST_MESSAGE"
        except Exception as e:
            print(f"Erreur dans handle_broadcast : {e}")
            return "CHOOSING"

    async def manage_broadcasts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les annonces existantes"""
        keyboard = []
        if self.broadcasts:
            for broadcast_id, broadcast in self.broadcasts.items():
                keyboard.append([InlineKeyboardButton(
                    f"📢 {broadcast['content'][:30]}...",
                    callback_data=f"edit_broadcast_{broadcast_id}"
                )])
        
        keyboard.append([InlineKeyboardButton("➕ Nouvelle annonce", callback_data="start_broadcast")])
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="admin")])
        
        await update.callback_query.edit_message_text(
            "📢 *Gestion des annonces*\n\n"
            "Sélectionnez une annonce à modifier ou créez-en une nouvelle.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return "CHOOSING"

    async def edit_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Permet de modifier une annonce existante"""
        query = update.callback_query
        broadcast_id = query.data.replace("edit_broadcast_", "")
    
        if broadcast_id in self.broadcasts:
            broadcast = self.broadcasts[broadcast_id]
            keyboard = [
                [InlineKeyboardButton("✏️ Modifier l'annonce", callback_data=f"edit_broadcast_content_{broadcast_id}")],
                [InlineKeyboardButton("❌ Supprimer", callback_data=f"delete_broadcast_{broadcast_id}")],
                [InlineKeyboardButton("🔙 Retour", callback_data="manage_broadcasts")]
            ]
        
            await query.edit_message_text(
                f"📢 *Gestion de l'annonce*\n\n"
                f"Message actuel :\n{broadcast['content'][:200]}...",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(
                "❌ Cette annonce n'existe plus.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="manage_broadcasts")
                ]])
            )
    
        return "CHOOSING"

    async def edit_broadcast_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Démarre l'édition d'une annonce"""
        query = update.callback_query
        broadcast_id = query.data.replace("edit_broadcast_content_", "")

        context.user_data['editing_broadcast_id'] = broadcast_id

        # Envoyer le message d'instruction et stocker son ID
        message = await query.edit_message_text(
            "✏️ *Modification de l'annonce*\n\n"
            "Envoyez un nouveau message (texte et/ou média) pour remplacer cette annonce.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Annuler", callback_data=f"edit_broadcast_{broadcast_id}")
            ]])
        )
    
        # Stocker l'ID du message d'instruction
        context.user_data['instruction_message_id'] = message.message_id

        return "WAITING_BROADCAST_EDIT"

    async def handle_broadcast_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Traite la modification d'une annonce"""
        try:
            broadcast_id = context.user_data.get('editing_broadcast_id')
            if not broadcast_id or broadcast_id not in self.broadcasts:
                return "CHOOSING"

            # Supprimer les messages intermédiaires
            try:
                await update.message.delete()
                if 'instruction_message_id' in context.user_data:
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=context.user_data['instruction_message_id']
                    )
            except Exception as e:
                print(f"Error deleting messages: {e}")

            admin_id = update.effective_user.id
            new_content = update.message.text if update.message.text else update.message.caption if update.message.caption else "Media sans texte"
        
            # Convertir les nouvelles entités
            new_entities = None
            if update.message.entities:
                new_entities = [{'type': entity.type, 
                               'offset': entity.offset,
                               'length': entity.length} 
                              for entity in update.message.entities]
            elif update.message.caption_entities:
                new_entities = [{'type': entity.type, 
                               'offset': entity.offset,
                               'length': entity.length} 
                              for entity in update.message.caption_entities]

            broadcast = self.broadcasts[broadcast_id]
            broadcast['content'] = new_content
            broadcast['entities'] = new_entities

            success = 0
            failed = 0
            messages_updated = []
        
            # Tenter de modifier les messages existants
            for user_id, msg_id in broadcast['message_ids'].items():
                if int(user_id) == admin_id:  # Skip l'admin
                    continue
                try:
                    await context.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=msg_id,
                        text=new_content,
                        entities=update.message.entities,
                        reply_markup=self._create_message_keyboard()
                    )
                    success += 1
                    messages_updated.append(user_id)
                except Exception as e:
                    print(f"Error updating message for user {user_id}: {e}")
                    failed += 1

            # Pour les utilisateurs qui n'ont pas reçu le message
            for user_id in self._users.keys():
                if (str(user_id) not in messages_updated and 
                    self.is_user_authorized(int(user_id)) and 
                    int(user_id) != admin_id):  # Skip l'admin
                    try:
                        sent_msg = await context.bot.send_message(
                            chat_id=user_id,
                            text=new_content,
                            entities=update.message.entities,
                            reply_markup=self._create_message_keyboard()
                        )
                        broadcast['message_ids'][str(user_id)] = sent_msg.message_id
                        success += 1
                    except Exception as e:
                        print(f"Error sending new message to user {user_id}: {e}")
                        failed += 1

            self._save_broadcasts()

            # Créer la bannière de gestion des annonces
            keyboard = []
            if self.broadcasts:
                for b_id, broadcast in self.broadcasts.items():
                    keyboard.append([InlineKeyboardButton(
                        f"📢 {broadcast['content'][:30]}...",
                        callback_data=f"edit_broadcast_{b_id}"
                    )])
        
            keyboard.append([InlineKeyboardButton("➕ Nouvelle annonce", callback_data="start_broadcast")])
            keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="admin")])
        
            # Envoyer la nouvelle bannière avec le contenu de l'annonce
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="📢 *Gestion des annonces*\n\n"
                     "Sélectionnez une annonce à modifier ou créez-en une nouvelle.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            # Message de confirmation avec le contenu
            confirmation_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"✅ Message modifié ({success} succès, {failed} échecs)\n\n"
                     f"📝 *Contenu de l'annonce :*\n{new_content}",
                parse_mode='Markdown'
            )

            # Programmer la suppression du message après 3 secondes
            async def delete_message():
                await asyncio.sleep(3)
                try:
                    await confirmation_message.delete()
                except Exception as e:
                    print(f"Error deleting confirmation message: {e}")

            asyncio.create_task(delete_message())

            return "CHOOSING"

        except Exception as e:
            print(f"Error in handle_broadcast_edit: {e}")
            return "CHOOSING"

    async def resend_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Renvoie une annonce existante"""
        query = update.callback_query
        broadcast_id = query.data.replace("resend_broadcast_", "")

        if broadcast_id not in self.broadcasts:
            await query.edit_message_text(
                "❌ Cette annonce n'existe plus.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="manage_broadcasts")
                ]])
            )
            return "CHOOSING"

        broadcast = self.broadcasts[broadcast_id]
        success = 0
        failed = 0

        progress_message = await query.edit_message_text(
            "📤 *Renvoi de l'annonce en cours...*",
            parse_mode='Markdown'
        )

        for user_id in self._users.keys():
            user_id_int = int(user_id)
            if not self.is_user_authorized(user_id_int):
                print(f"User {user_id_int} not authorized")
                continue
        
            try:
                if broadcast['type'] == 'photo' and broadcast['file_id']:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=broadcast['file_id'],
                        caption=broadcast['caption'] if broadcast['caption'] else '',
                        parse_mode='Markdown',  # Ajout du parse_mode
                        reply_markup=self._create_message_keyboard()
                    )
                else:
                    message_text = broadcast.get('content', '')
                    if not message_text:
                        print(f"No content found for broadcast {broadcast_id}")
                        continue
        
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        parse_mode='Markdown',  # Ajout du parse_mode
                        reply_markup=self._create_message_keyboard()
                    )
                success += 1
                print(f"Successfully sent to user {user_id}")
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                failed += 1

        keyboard = [
            [InlineKeyboardButton("📢 Retour aux annonces", callback_data="manage_broadcasts")],
            [InlineKeyboardButton("🔙 Menu admin", callback_data="admin")]
        ]

        await progress_message.edit_text(
            f"✅ *Annonce renvoyée !*\n\n"
            f"📊 *Rapport d'envoi :*\n"
            f"• Envois réussis : {success}\n"
            f"• Échecs : {failed}\n"
            f"• Total : {success + failed}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return "CHOOSING"

    async def delete_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Supprime une annonce"""
        query = update.callback_query
        broadcast_id = query.data.replace("delete_broadcast_", "")
        
        if broadcast_id in self.broadcasts:
            del self.broadcasts[broadcast_id]
            self._save_broadcasts()  # Sauvegarder après suppression
        await query.edit_message_text(
            "✅ *L'annonce a été supprimée avec succès !*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Retour aux annonces", callback_data="manage_broadcasts")
            ]])
        )
        
        return "CHOOSING"

    async def send_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Envoie le message aux utilisateurs autorisés"""
        success = 0
        failed = 0
        chat_id = update.effective_chat.id
        message_ids = {}  # Pour stocker les IDs des messages envoyés

        try:
            # Supprimer les messages précédents
            try:
                await update.message.delete()
                if 'instruction_message_id' in context.user_data:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=context.user_data['instruction_message_id']
                    )
            except Exception as e:
                print(f"Erreur lors de la suppression du message: {e}")

            # Enregistrer le broadcast
            broadcast_id = str(datetime.now().timestamp())
            message_content = update.message.text if update.message.text else update.message.caption if update.message.caption else "Media sans texte"
        
            # Convertir les entités en format sérialisable
            entities = None
            if update.message.entities:
                entities = [{'type': entity.type, 
                            'offset': entity.offset,
                            'length': entity.length} 
                           for entity in update.message.entities]
            elif update.message.caption_entities:
                entities = [{'type': entity.type, 
                            'offset': entity.offset,
                            'length': entity.length} 
                           for entity in update.message.caption_entities]
    
            self.broadcasts[broadcast_id] = {
                'content': message_content,
                'type': 'photo' if update.message.photo else 'text',
                'file_id': update.message.photo[-1].file_id if update.message.photo else None,
                'caption': update.message.caption if update.message.photo else None,
                'entities': entities,  # Stocker les entités converties
                'message_ids': {},
                'parse_mode': None  # On n'utilise plus parse_mode car on utilise les entités
            }

            # Message de progression
            progress_message = await context.bot.send_message(
                chat_id=chat_id,
                text="📤 <b>Envoi du message en cours...</b>",
                parse_mode='HTML'
            )

            # Envoi aux utilisateurs autorisés
            for user_id in self._users.keys():
                user_id_int = int(user_id)
                if not self.is_user_authorized(user_id_int) or user_id_int == update.effective_user.id:  # Skip non-autorisés et admin
                    print(f"User {user_id_int} skipped")
                    continue
            
                try:
                    if update.message.photo:
                        sent_msg = await context.bot.send_photo(
                            chat_id=user_id,
                            photo=update.message.photo[-1].file_id,
                            caption=update.message.caption if update.message.caption else '',
                            caption_entities=update.message.caption_entities,
                            reply_markup=self._create_message_keyboard()
                        )
                    else:
                        sent_msg = await context.bot.send_message(
                            chat_id=user_id,
                            text=message_content,
                            entities=update.message.entities,
                            reply_markup=self._create_message_keyboard()
                        )
                    self.broadcasts[broadcast_id]['message_ids'][str(user_id)] = sent_msg.message_id  # Assurer que user_id est un string
                    success += 1
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")
                    failed += 1

            # Sauvegarder les broadcasts
            self._save_broadcasts()

            # Rapport final
            keyboard = [
                [InlineKeyboardButton("📢 Gérer les annonces", callback_data="manage_broadcasts")],
                [InlineKeyboardButton("🔙 Menu admin", callback_data="admin")]
            ]

            await progress_message.edit_text(
                f"✅ *Message envoyé avec succès !*\n\n"
                f"📊 *Rapport d'envoi :*\n"
                f"• Envois réussis : {success}\n"
                f"• Échecs : {failed}\n"
                f"• Total : {success + failed}",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            return "CHOOSING"

        except Exception as e:
            print(f"Erreur lors de l'envoi du broadcast : {e}")
            return "CHOOSING"

    async def handle_user_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère l'affichage des statistiques utilisateurs"""
        try:
            # Récupérer la page actuelle depuis le callback_data ou initialiser à 0
            query = update.callback_query
            current_page = 0
            if query and query.data.startswith("user_page_"):
                current_page = int(query.data.replace("user_page_", ""))

            # Nombre d'utilisateurs par page
            users_per_page = 10
        
            # Récupérer les listes d'utilisateurs autorisés et bannis
            authorized_users = set(self._access_codes.get("authorized_users", []))
            banned_users = set(self._access_codes.get("banned_users", []))
        
            # Créer des listes séparées pour chaque catégorie
            authorized_list = []
            banned_list = []
            pending_list = []

            for user_id, user_data in self._users.items():
                user_id_int = int(user_id)
                if user_id_int in authorized_users:
                    authorized_list.append((user_id, user_data))
                elif user_id_int in banned_users:
                    banned_list.append((user_id, user_data))
                else:
                    pending_list.append((user_id, user_data))

            # Combiner les listes dans l'ordre : autorisés, en attente, bannis
            relevant_users = authorized_list + pending_list + banned_list

            total_pages = (len(relevant_users) + users_per_page - 1) // users_per_page

            # Calculer les indices de début et de fin pour la page actuelle
            start_idx = current_page * users_per_page
            end_idx = min(start_idx + users_per_page, len(relevant_users))

            # Construire le texte
            text = "👥 *Gestion des utilisateurs*\n\n"
            text += f"✅ Utilisateurs autorisés : {len(authorized_users)}\n"
            text += f"⏳ Utilisateurs en attente : {len(pending_list)}\n"
            text += f"🚫 Utilisateurs bannis : {len(banned_users)}\n"

            # Ajouter l'information sur les groupes
            groups = self._access_codes.get("groups", {})
            for group_name, group_users in groups.items():
                text += f"👥 Groupe {group_name} : {len(group_users)}\n"
            if total_pages > 1:
                text += f"Page {current_page + 1}/{total_pages}\n"
            text += "\n"

            if relevant_users:
                for user_id, user_data in relevant_users[start_idx:end_idx]:
                    user_id_int = int(user_id)
                    # Format de la date
                    last_seen = user_data.get('last_seen', 'Jamais')
                    try:
                        dt = datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S")
                        last_seen = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        pass

                    # Construire le nom d'affichage
                    username = user_data.get('username')
                    first_name = user_data.get('first_name')
                    last_name = user_data.get('last_name')
                
                    if username:
                        display_name = f"@{username}"
                    elif first_name and last_name:
                        display_name = f"{first_name} {last_name}"
                    elif first_name:
                        display_name = first_name
                    elif last_name:
                        display_name = last_name
                    else:
                        display_name = "Sans nom"

                    # Échapper les caractères spéciaux Markdown
                    display_name = display_name.replace('_', '\\_').replace('*', '\\*')
                
                    # Déterminer le statut
                    if user_id_int in banned_users:
                        status = "🚫"
                    elif user_id_int in authorized_users:
                        status = "✅"
                    else:
                        status = "⏳"
                
                    text += f"{status} {display_name} (`{user_id}`)\n"
                    text += f"  └ Dernière activité : {last_seen}\n"
            else:
                text += "Aucun utilisateur enregistré."

            # Construire le clavier avec la pagination
            keyboard = []
        
            # Boutons de pagination
            if total_pages > 1:
                nav_buttons = []
            
                # Bouton page précédente
                if current_page > 0:
                    nav_buttons.append(InlineKeyboardButton(
                        "◀️", callback_data=f"user_page_{current_page - 1}"))
            
                # Bouton page actuelle
                nav_buttons.append(InlineKeyboardButton(
                    f"{current_page + 1}/{total_pages}", callback_data="current_page"))
            
                # Bouton page suivante
                if current_page < total_pages - 1:
                    nav_buttons.append(InlineKeyboardButton(
                        "▶️", callback_data=f"user_page_{current_page + 1}"))
            
                keyboard.append(nav_buttons)

            # Autres boutons
            keyboard.extend([
                [InlineKeyboardButton("🚫 Utilisateurs bannis", callback_data="show_banned")],
                [InlineKeyboardButton("🔙 Retour", callback_data="admin")]
            ])

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )

            return "CHOOSING"

        except Exception as e:
            print(f"Erreur dans handle_user_management : {e}")
            await update.callback_query.edit_message_text(
                "Erreur lors de l'affichage des utilisateurs.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="admin")
                ]])
            )
            return "CHOOSING"

    async def add_user_buttons(self, keyboard: list) -> list:
        """Ajoute les boutons de gestion utilisateurs au clavier admin existant"""
        try:
            keyboard.insert(-1, [InlineKeyboardButton("👥 Gérer utilisateurs", callback_data="manage_users")])
        except Exception as e:
            print(f"Erreur lors de l'ajout des boutons admin : {e}")
        return keyboard
