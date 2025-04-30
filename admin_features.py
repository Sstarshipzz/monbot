import json
import pytz  
import random
import string
import asyncio
from datetime import datetime, timedelta
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
WAITING_CODE_NUMBER = "WAITING_CODE_NUMBER"

class AdminFeatures:
    STATES = {
        'CHOOSING': 'CHOOSING',
        'WAITING_CODE_NUMBER': 'WAITING_CODE_NUMBER'
    }
    def __init__(self, users_file: str = 'data/users.json', access_codes_file: str = 'data/access_codes.json', broadcasts_file: str = 'data/broadcasts.json', config_file: str = 'config/config.json'):
        from main import CATALOG, save_catalog  
        self.CATALOG = CATALOG
        self.save_catalog = save_catalog
        self.users_file = users_file
        self.access_codes_file = access_codes_file
        self.broadcasts_file = broadcasts_file
        self.config_file = config_file
        self._users = self._load_users()
        self.admin_ids = self._load_admin_ids()
        self._access_codes = self._load_access_codes()
        self.broadcasts = self._load_broadcasts()
        self.polls_file = 'data/polls.json'
        self.polls = self._load_polls()

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

    def _load_admin_ids(self) -> list:
        """Charge les IDs admin depuis le fichier de configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('admin_ids', [])
        except Exception as e:
            print(f"Erreur lors du chargement des admin IDs : {e}")
            return []

    def authorize_user(self, user_id: int) -> bool:
        """Ajoute un utilisateur à la liste des utilisateurs autorisés"""
        try:
            if "authorized_users" not in self._access_codes:
                self._access_codes["authorized_users"] = []
        
            user_id = int(user_id)
            if user_id not in self._access_codes["authorized_users"]:
                self._access_codes["authorized_users"].append(user_id)
                self._save_access_codes()
                return True
            return False
        except Exception as e:
            print(f"Erreur lors de l'autorisation de l'utilisateur : {e}")
            return False

    def mark_code_as_used(self, code: str, user_id: int) -> bool:
        """Marque un code comme utilisé et autorise l'utilisateur"""
        try:
            if "codes" not in self._access_codes:
                return False
        
            for code_entry in self._access_codes["codes"]:
                if code_entry["code"] == code and not code_entry["used"]:
                    code_entry["used"] = True
                    code_entry["used_by"] = user_id
                    self.authorize_user(user_id)
                    self._save_access_codes()
                    return True
            return False
        except Exception as e:
            print(f"Erreur lors du marquage du code comme utilisé : {e}")
            return False

    def generate_temp_code(self, generator_id: int, generator_username: str = None) -> tuple:
        """Génère un code d'accès temporaire"""
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        expiration = (datetime.utcnow() + timedelta(days=2)).isoformat()  # 48h

        if "codes" not in self._access_codes:
            self._access_codes["codes"] = []

        # Ajouter le code dans la section "codes"
        self._access_codes["codes"].append({
            'code': code,
            'expiration': expiration,
            'created_by': generator_id,  # Utiliser le même format que les autres codes
            'used': False
        })

        self._save_access_codes()
        return code, expiration

    def list_temp_codes(self, show_used: bool = False) -> list:
        """Liste les codes temporaires"""
        current_time = datetime.utcnow().isoformat()
        codes = self._access_codes.get("codes", [])

        if show_used:
            # Retourner uniquement les codes marqués comme utilisés
            return [code for code in codes if code.get("used") is True]
        else:
            # Retourner les codes non utilisés et non expirés
            return [code for code in codes 
                    if not code.get("used") and code.get("expiration", "") > current_time]

    def cleanup_expired_codes(self):
        """Supprime complètement les codes expirés"""
        current_time = datetime.utcnow().isoformat()
    
        if "codes" not in self._access_codes:
            return
    
        # Garder uniquement les codes non expirés
        self._access_codes["codes"] = [
            code for code in self._access_codes["codes"]
            if code["expiration"] > current_time
        ]
    
        # Sauvegarder les modifications
        self._save_access_codes()

    def mark_code_as_used(self, code: str, user_id: int, username: str = None) -> bool:
        """Marque un code comme utilisé et autorise l'utilisateur"""
        try:
            if "codes" not in self._access_codes:
                return False
        
            for code_entry in self._access_codes["codes"]:
                if code_entry["code"] == code and not code_entry["used"]:
                    code_entry["used"] = True
                    code_entry["used_by"] = {
                        "id": user_id,
                        "username": username
                    }
                    # Ajouter l'utilisateur à la liste des autorisés
                    if "authorized_users" not in self._access_codes:
                        self._access_codes["authorized_users"] = []
                    if user_id not in self._access_codes["authorized_users"]:
                        self._access_codes["authorized_users"].append(user_id)
                    self._save_access_codes()
                    return True
            return False
        except Exception as e:
            print(f"Erreur lors du marquage du code comme utilisé : {e}")
            return False

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
                for broadcast_id, broadcast in broadcasts.items():
                    if 'message_ids' not in broadcast:
                        broadcast['message_ids'] = {}
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
        
    def _load_polls(self):
        """Charge les sondages depuis le fichier"""
        try:
            with open(self.polls_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_polls(self):
        """Sauvegarde les sondages"""
        try:
            with open(self.polls_file, 'w', encoding='utf-8') as f:
                json.dump(self.polls, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des sondages : {e}")

    def _create_poll_message(self, poll):
        """Crée le message formaté du sondage"""
        options_text = ""
        total_votes = sum(int(count) for count in poll['votes'].values())

        for i, option in enumerate(poll['options']):
            votes = int(poll['votes'].get(str(i), 0))
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            bar_length = int((percentage / 100) * 20)
            progress_bar = "█" * bar_length + "▒" * (20 - bar_length)
    
            options_text += f"\n{i+1}. {option}\n"
            options_text += f"{progress_bar} {votes} votes ({percentage:.1f}%)\n"

        text = (
            f"📊 *SONDAGE*\n\n"
            f"❓ {poll['question']}\n\n"
            f"{options_text}\n"
            f"👥 Total des votes : {total_votes}\n\n"
            f"⚠️ Un seul vote par personne"
        )

        return text

    def list_active_codes(self):
        """Liste tous les codes actifs et supprime les codes expirés"""
        current_time = datetime.utcnow().isoformat()
    
        try:
            with open('config/access_codes.json', 'r') as f:
                codes = json.load(f)
        except FileNotFoundError:
            return []
   
        active_codes = [code for code in codes if code["expiration"] > current_time]
    
        if len(active_codes) != len(codes):
            with open('config/access_codes.json', 'w') as f:
                json.dump(active_codes, f, indent=4)
    
        return active_codes

    def _create_poll_keyboard(self, poll_id):
        """Crée le clavier pour le sondage"""
        poll = self.polls[poll_id]
        keyboard = []
    
        # Options de vote
        for i, option in enumerate(poll['options']):
            keyboard.append([
                InlineKeyboardButton(
                    option,
                    callback_data=f"vote_{poll_id}_{i}"
                )
            ])
    
        # Bouton menu (utilise start_cmd comme pour les broadcasts)
        keyboard.append([
            InlineKeyboardButton("🔄 Menu Principal", callback_data="start_cmd")
        ])
    
        return keyboard

    async def view_poll_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche les détails d'un sondage et options de gestion"""
        query = update.callback_query
        await query.answer()
    
        try:
            # Extraire l'ID du sondage
            _, poll_id = query.data.split("view_poll_")
        
            if poll_id not in self.polls:
                await query.edit_message_text(
                    "❌ Ce sondage n'existe plus!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Retour", callback_data="view_active_polls")
                    ]])
                )
                return "CHOOSING"
        
            poll = self.polls[poll_id]
            poll_text = self._create_poll_message(poll)
        
            # Ajouter les boutons de gestion
            keyboard = [
                [InlineKeyboardButton("❌ Supprimer le sondage", callback_data=f"delete_poll_{poll_id}")],
                [InlineKeyboardButton("🔙 Retour", callback_data="view_active_polls")]
            ]
        
            await query.edit_message_text(
                f"{poll_text}\n\n"
                f"📅 Créé le : {poll['created_at']}\n"
                f"👥 Nombre de votants : {len(poll.get('voters', {}))}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        
        except Exception as e:
            print(f"Erreur dans view_poll_details: {e}")
            await query.edit_message_text(
                "Une erreur est survenue!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="view_active_polls")
                ]])
            )
    
        return "CHOOSING"

    async def delete_poll(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Supprime un sondage"""
        query = update.callback_query
        await query.answer()
    
        try:
            # Extraire l'ID du sondage
            _, poll_id = query.data.split("delete_poll_")
        
            if poll_id not in self.polls:
                await query.edit_message_text(
                    "❌ Ce sondage n'existe plus!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Retour", callback_data="view_active_polls")
                    ]])
                )
                return "CHOOSING"
        
            poll = self.polls[poll_id]
        
            # Supprimer le message du sondage pour tous les utilisateurs
            for chat_id, message_id in poll['message_ids'].items():
                try:
                    await context.bot.delete_message(
                        chat_id=int(chat_id),
                        message_id=message_id
                    )
                except Exception as e:
                    print(f"Erreur suppression message pour {chat_id}: {e}")
        
            # Supprimer le sondage de la liste
            del self.polls[poll_id]
            self._save_polls()
        
            await query.edit_message_text(
                "✅ Sondage supprimé avec succès!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="view_active_polls")
                ]])
            )
        
        except Exception as e:
            print(f"Erreur dans delete_poll: {e}")
            await query.edit_message_text(
                "Une erreur est survenue!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Retour", callback_data="view_active_polls")
                ]])
            )
    
        return "CHOOSING"

    async def handle_generate_multiple_codes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la génération de plusieurs codes d'accès"""
        if str(update.effective_user.id) not in self.admin_ids:
            await update.callback_query.answer("❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
            return self.STATES['CHOOSING']

        keyboard = [
            [InlineKeyboardButton("1️⃣ Un code", callback_data="gen_code_1")],
            [InlineKeyboardButton("5️⃣ Cinq codes", callback_data="gen_code_5")],
            [InlineKeyboardButton("🔢 Nombre personnalisé", callback_data="gen_code_custom")],
            [InlineKeyboardButton("🔙 Retour", callback_data="back_to_home")]
        ]
    
        await update.callback_query.edit_message_text(
            "🎫 Génération de codes d'accès\n\n"
            "Choisissez le nombre de codes à générer :",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return self.STATES['CHOOSING']

    async def check_and_clean_unauthorized_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Vérifie si l'utilisateur est autorisé lorsque le contrôle d'accès est activé
        Si non autorisé : supprime les messages et retourne True
        Si autorisé : retourne False
        """
        if self.is_access_control_enabled() and not self.is_user_authorized(update.effective_user.id):
            chat_id = update.effective_chat.id
        
            message_keys = [
                'menu_message_id', 
                'banner_message_id',
                'category_message_id',
                'last_product_message_id',
                'instruction_message_id'
            ]

            for key in message_keys:
                if key in context.user_data:
                    try:
                        await context.bot.delete_message(
                            chat_id=chat_id,
                            message_id=context.user_data[key]
                        )
                    except Exception as e:
                        print(f"Error deleting message {key}: {e}")
                    del context.user_data[key]

            if update.callback_query and update.callback_query.message:
                try:
                    await update.callback_query.message.delete()
                except Exception as e:
                    print(f"Error deleting callback message: {e}")

            warning_msg = await context.bot.send_message(
                chat_id=chat_id,
                text="🔒 Accès non autorisé. Le contrôle d'accès est activé.\nVeuillez utiliser /start et entrez votre code d'accès'."
            )

            async def delete_warning():
                await asyncio.sleep(3)
                try:
                    await warning_msg.delete()
                except Exception as e:
                    print(f"Error deleting warning message: {e}")

            asyncio.create_task(delete_warning())
            return True
        return False

    async def handle_custom_code_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la demande de nombre personnalisé de codes"""
        if str(update.effective_user.id) not in self.admin_ids:
            await update.callback_query.answer("❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
            return self.STATES['CHOOSING']
    
        keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="generate_multiple_codes")]]
    
        await update.callback_query.edit_message_text(
            "🔢 Génération personnalisée\n\n"
            "Envoyez le nombre de codes que vous souhaitez générer (maximum 20) :",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return self.STATES['WAITING_CODE_NUMBER']

    async def handle_code_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Traite le nombre de codes demandé"""
        try:
            # Vérifier les permissions admin
            if str(update.effective_user.id) not in self.admin_ids:
                await update.message.reply_text("❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
                return self.STATES['CHOOSING']

            try:
                num = int(update.message.text)
                if num <= 0 or num > 20:
                    raise ValueError()
            
                # Supprimer le message de l'utilisateur
                try:
                    await update.message.delete()
                except:
                    pass
        
                codes_text = "🎫 *Codes générés :*\n\n"
                for _ in range(num):
                    code, expiration = self.generate_temp_code()
                    exp_date = datetime.fromisoformat(expiration)
                    exp_str = exp_date.strftime("%d/%m/%Y à %H:%M")
                    codes_text += f"*Code d'accès temporaire :*\n"
                    codes_text += f"`{code}\n"
                    codes_text += f"⚠️ Code à usage unique\n"
                    codes_text += f"⏰ Expire le {exp_str}`\n\n"
        
                keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="back_to_codes_menu")]]
        
                await update.message.reply_text(
                    codes_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return self.STATES['CHOOSING']
        
            except ValueError:
                keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="back_to_codes_menu")]]
                await update.message.reply_text(
                    "❌ Erreur : Veuillez entrer un nombre valide entre 1 et 20.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return self.STATES['WAITING_CODE_NUMBER']
            
        except Exception as e:
            print(f"Erreur dans handle_code_number_input : {e}")
            keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="back_to_codes_menu")]]
            await update.message.reply_text(
                "❌ Une erreur est survenue.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return self.STATES['CHOOSING']

    async def generate_codes(self, update: Update, context: ContextTypes.DEFAULT_TYPE, num_codes: int = 1):
        """Génère un nombre spécifié de codes"""
        if str(update.effective_user.id) not in self.admin_ids:
            await update.callback_query.answer("❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
            return self.STATES['CHOOSING']

        codes_text = "🎫 *Codes générés :*\n\n"
        for _ in range(num_codes):
            code, expiration = self.generate_temp_code(
                update.effective_user.id,
                update.effective_user.username
            )
            exp_date = datetime.fromisoformat(expiration)
            exp_str = exp_date.strftime("%d/%m/%Y à %H:%M")
        
            # Format amélioré avec titre en gras non copiable et contenu copiable
            codes_text += "*Code d'accès temporaire :*\n"
            codes_text += f"`{code}\n"
            codes_text += "⚠️ Code à usage unique\n"
            codes_text += f"⏰ Expire le {exp_str}`\n\n"
    
        keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="generate_multiple_codes")]]
    
        await update.callback_query.edit_message_text(
            codes_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return self.STATES['CHOOSING']

    async def back_to_generate_codes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):  # Ajout de self
        """Retourne au menu de génération de codes"""
        if str(update.effective_user.id) not in self.admin_ids:
            await update.callback_query.answer("❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
            return self.STATES['CHOOSING']

        query = update.callback_query
        await query.answer()
    
        keyboard = [
            [InlineKeyboardButton("1️⃣ Un code", callback_data="gen_code_1")],
            [InlineKeyboardButton("5️⃣ Cinq codes", callback_data="gen_code_5")],
            [InlineKeyboardButton("🔢 Nombre personnalisé (20 maximum)", callback_data="gen_code_custom")],
            [InlineKeyboardButton("🔙 Retour", callback_data="back_to_home")]
        ]
    
        await query.edit_message_text(
            "🎫 Génération de codes d'accès\n\n"
            "Choisissez le nombre de codes à générer :",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return self.STATES['CHOOSING']

    async def show_codes_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche l'historique des codes"""
        try:
            if str(update.effective_user.id) not in self.admin_ids:
                await update.callback_query.answer("❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
                return self.STATES['CHOOSING']

            showing_used = context.user_data.get('showing_used_codes', False)
            all_codes = self.list_temp_codes(showing_used)

            # Paginer les résultats
            if len(all_codes) > 10:
                current_page = context.user_data.get('codes_page', 0)
                total_pages = (len(all_codes) + 9) // 10
                start_idx = current_page * 10
                end_idx = min(start_idx + 10, len(all_codes))
                codes = all_codes[start_idx:end_idx]
            else:
                codes = all_codes
                current_page = 0
                total_pages = 1

            if not codes:
                text = "📜 *Aucun code à afficher*"
            else:
                text = "📜 *Codes " + ("utilisés" if showing_used else "actifs") + " :*\n\n"
                for code in codes:
                    text += "*Code d'accès temporaire :*\n"
                    if showing_used and "used_by" in code:
                        used_by = code["used_by"]
                        user_id = used_by.get("id", "N/A")

                        # Récupérer les informations de l'utilisateur
                        user_data = self._users.get(str(user_id), {})
                        username = user_data.get('username', '')
                        first_name = user_data.get('first_name', '')
                        last_name = user_data.get('last_name', '')

                        # Échapper les caractères spéciaux
                        if username:
                            username = username.replace('_', r'\_').replace('*', r'\*').replace('`', r'\`')
                        if first_name:
                            first_name = first_name.replace('_', r'\_').replace('*', r'\*').replace('`', r'\`')
                        if last_name:
                            last_name = last_name.replace('_', r'\_').replace('*', r'\*').replace('`', r'\`')

                        # Construire le nom d'affichage
                        display_parts = []
                        if first_name:
                            display_parts.append(first_name)
                        if last_name:
                            display_parts.append(last_name)

                        if username:
                            display_name = f"@{username}"
                        elif display_parts:
                            display_name = " ".join(display_parts)
                        else:
                            display_name = str(user_id)

                        text += f"`{code['code']}`\n"
                        text += f"✅ Utilisé par : {display_name} (`{user_id}`)\n\n"
                    else:
                        exp_date = datetime.fromisoformat(code["expiration"])
                        exp_str = exp_date.strftime("%d/%m/%Y à %H:%M")
                        text += f"`{code['code']}\n"
                        text += f"⚠️ Code à usage unique\n"
                        text += f"⏰ Expire le {exp_str}`\n\n"

            active_btn_text = "📍 Codes actifs" if not showing_used else "Codes actifs"
            used_btn_text = "📍 Codes utilisés" if showing_used else "Codes utilisés"

            keyboard = [
                [
                    InlineKeyboardButton(active_btn_text, callback_data="show_active_codes"),
                    InlineKeyboardButton(used_btn_text, callback_data="show_used_codes")
                ],
                [InlineKeyboardButton("🔙 Retour", callback_data="back_to_home")]
            ]

            # Ajouter les boutons de pagination si nécessaire
            if len(all_codes) > 10:
                nav_buttons = []
                if current_page > 0:
                    nav_buttons.append(InlineKeyboardButton("◀️", callback_data="prev_codes_page"))
                nav_buttons.append(InlineKeyboardButton(f"{current_page + 1}/{total_pages}", callback_data="current_page"))
                if current_page < total_pages - 1:
                    nav_buttons.append(InlineKeyboardButton("▶️", callback_data="next_codes_page"))
            
                if nav_buttons:
                    keyboard.insert(-2, nav_buttons)

            await update.callback_query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return self.STATES['CHOOSING']
    
        except TelegramBadRequest as e:
            if str(e) == "Message is not modified":
                await update.callback_query.answer("Liste déjà à jour!")
            else:
                raise
            return self.STATES['CHOOSING']

    async def toggle_codes_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bascule entre codes actifs et utilisés"""
        if str(update.effective_user.id) not in self.admin_ids:
            await update.callback_query.answer("❌ Vous n'êtes pas autorisé à utiliser cette fonction.")
            return self.STATES['CHOOSING']
    
        context.user_data['showing_used_codes'] = update.callback_query.data == "show_used_codes"
        return await self.show_codes_history(update, context)

    async def handle_codes_pagination(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la pagination des codes"""
        query = update.callback_query.data
        current_page = context.user_data.get('codes_page', 0)
    
        codes = self.list_temp_codes(context.user_data.get('showing_used_codes', False))
        total_pages = (len(codes) + 9) // 10

        if query == "prev_codes_page" and current_page > 0:
            context.user_data['codes_page'] = current_page - 1
        elif query == "next_codes_page" and current_page < total_pages - 1:
            context.user_data['codes_page'] = current_page + 1
    
        return await self.show_codes_history(update, context)

    async def manage_polls(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les sondages"""
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("➕ Nouveau sondage", callback_data="create_poll")],
            [InlineKeyboardButton("📊 Voir sondages actifs", callback_data="view_active_polls")],
            [InlineKeyboardButton("🔙 Retour", callback_data="admin")]
        ]

        await query.edit_message_text(
            "📊 *Gestion des sondages*\n\n"
            "• Créez un nouveau sondage\n"
            "• Consultez les sondages actifs",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return "CHOOSING"

    async def create_poll(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Démarre la création d'un sondage"""
        query = update.callback_query
        await query.answer()

        # Initialiser le sondage dans le context
        context.user_data['temp_poll'] = {
            'question': None,
            'options': [],
            'votes': {},
            'voters': {}
        }

        # Message demandant la question
        message = await query.edit_message_text(
            "📊 *Création d'un nouveau sondage*\n\n"
            "Envoyez la question de votre sondage :",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Annuler", callback_data="manage_polls")
            ]]),
            parse_mode='Markdown'
        )
    
        # Sauvegarder l'ID du message pour le supprimer plus tard
        context.user_data['creation_message_id'] = message.message_id
        context.user_data['creation_chat_id'] = update.effective_chat.id

        return "WAITING_POLL_QUESTION"

    async def handle_poll_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la réception de la question du sondage"""
        question = update.message.text
        context.user_data['temp_poll'] = {
            'question': question,
            'options': []
        }

        # Supprimer le message de la question
        await update.message.delete()

        # Supprimer le message de création initial
        try:
            await context.bot.delete_message(
                chat_id=context.user_data['creation_chat_id'],
                message_id=context.user_data['creation_message_id']
            )
        except Exception as e:
            print(f"Erreur lors de la suppression du message de création : {e}")

        # Créer le message des options qui sera réutilisé
        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✍️ Envoyez maintenant les options de réponse, une par message.\n\n"
                 "Options actuelles :\n\n"
                 "Aucune option ajoutée.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Terminé", callback_data="finish_poll_options"),
                InlineKeyboardButton("🔙 Annuler", callback_data="manage_polls")
            ]])
        )

        # Sauvegarder l'ID du message pour le mettre à jour plus tard
        context.user_data['options_message_id'] = message.message_id

        return "WAITING_POLL_OPTIONS"

    async def handle_poll_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la réception des options du sondage"""
        option = update.message.text
    
        # Ajouter l'option
        context.user_data['temp_poll']['options'].append(option)
    
        # Supprimer le message de l'option
        await update.message.delete()

        # Mettre à jour le message existant avec la nouvelle option
        options_text = "\n".join([f"- {opt}" for opt in context.user_data['temp_poll']['options']])
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data['options_message_id'],
            text="✍️ Envoyez maintenant les options de réponse, une par message.\n\n"
                 f"Options actuelles :\n\n{options_text}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Terminé", callback_data="finish_poll_options"),
                InlineKeyboardButton("🔙 Annuler", callback_data="manage_polls")
            ]])
        )

        return "WAITING_POLL_OPTIONS"

    async def finish_poll_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Finalise la création du sondage"""
        query = update.callback_query
        await query.answer()

        if len(context.user_data['temp_poll']['options']) < 2:
            await query.edit_message_text(
                "❌ Le sondage doit avoir au moins 2 options.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Réessayer", callback_data="create_poll"),
                    InlineKeyboardButton("🔙 Annuler", callback_data="manage_polls")
                ]])
            )
            return "CHOOSING"

        # Créer le sondage
        poll_id = str(len(self.polls) + 1)
        poll = {
            'id': poll_id,
            'creator_id': update.effective_user.id,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'question': context.user_data['temp_poll']['question'],
            'options': context.user_data['temp_poll']['options'],
            'votes': {str(i): 0 for i in range(len(context.user_data['temp_poll']['options']))},
            'voters': {},
            'message_ids': {}
        }

        # Sauvegarder le sondage
        self.polls[poll_id] = poll
        self._save_polls()

        # Créer le message du sondage
        poll_text = self._create_poll_message(poll)
        keyboard = self._create_poll_keyboard(poll_id)

        # Envoyer le sondage aux utilisateurs autorisés
        success_count = 0
        failed_count = 0

        for user_id in self._access_codes.get("authorized_users", []):
            try:
                message = await context.bot.send_message(
                    chat_id=user_id,
                    text=poll_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                poll['message_ids'][str(user_id)] = message.message_id
                success_count += 1
            except Exception as e:
                print(f"Erreur lors de l'envoi du sondage à {user_id}: {e}")
                failed_count += 1

        # Mettre à jour les message_ids
        self.polls[poll_id] = poll
        self._save_polls()

        # Message de confirmation temporaire
        confirmation_message = await query.edit_message_text(
            f"✅ Sondage créé et envoyé avec succès!\n\n"
            f"📊 Statistiques :\n"
            f"✓ Envois réussis : {success_count}\n"
            f"❌ Échecs : {failed_count}"
        )

        # Programmer la suppression du message après 2 secondes
        await asyncio.sleep(2)
        try:
            await confirmation_message.delete()
        except Exception as e:
            print(f"Erreur lors de la suppression du message de confirmation : {e}")

        return "CHOOSING"

    async def view_active_polls(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la liste des sondages actifs"""
        query = update.callback_query
        await query.answer()

        keyboard = []
    
        if self.polls:
            for poll_id, poll in self.polls.items():
                question = poll.get('question', '')[:30]
                keyboard.append([InlineKeyboardButton(
                    f"📊 {question}...",
                    callback_data=f"view_poll_{poll_id}"
                )])
        else:
            keyboard.append([InlineKeyboardButton("Aucun sondage actif", callback_data="noop")])
    
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="manage_polls")])

        await query.edit_message_text(
            "📊 *Sondages actifs*\n\n"
            "Sélectionnez un sondage pour le gérer :",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return "CHOOSING"

    async def handle_vote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les votes sur un sondage"""
        query = update.callback_query
        user_id = update.effective_user.id
    
        print(f"\n=== Tentative de vote ===")
        print(f"User ID: {user_id}")
        print(f"Callback data reçu: {query.data}")
        print(f"Message ID: {query.message.message_id}")
    
        try:
            _, poll_id, option_index = query.data.split("_")
            option_index = str(option_index)
        
            if poll_id not in self.polls:
                await query.answer("Ce sondage n'existe plus!", show_alert=True)
                return

            poll = self.polls[poll_id]
            user_id_str = str(user_id)

            # Vérifier si l'utilisateur peut voter (est dans message_ids)
            if user_id_str not in poll['message_ids']:
                print(f"Utilisateur {user_id} n'est pas autorisé à voter")
                await query.answer("Vous n'êtes pas autorisé à voter!", show_alert=True)
                return

            if user_id_str in poll.get('voters', {}):
                print(f"Utilisateur {user_id} a déjà voté")
                await query.answer("Vous avez déjà voté!", show_alert=True)
                return "CHOOSING"

            # Voter
            if 'votes' not in poll:
                poll['votes'] = {}
            if 'voters' not in poll:
                poll['voters'] = {}
            
            poll['votes'][option_index] = poll['votes'].get(option_index, 0) + 1
            poll['voters'][user_id_str] = option_index
        
            # Sauvegarder et mettre à jour
            self.polls[poll_id] = poll
            self._save_polls()

            # Mettre à jour tous les messages
            poll_text = self._create_poll_message(poll)
            keyboard = self._create_poll_keyboard(poll_id)

            for chat_id, message_id in poll['message_ids'].items():
                try:
                    await context.bot.edit_message_text(
                        chat_id=int(chat_id),
                        message_id=message_id,
                        text=poll_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Erreur mise à jour pour {chat_id}: {e}")

            await query.answer("✅ Vote enregistré!", show_alert=True)

        except Exception as e:
            print(f"Erreur dans handle_vote: {e}")
            import traceback
            traceback.print_exc()
            await query.answer("Une erreur est survenue!", show_alert=True)

        return "CHOOSING"

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
        """Supprime le groupe sélectionné et ses catégories associées"""
        query = update.callback_query
        await query.answer()

        group_name = query.data.replace("confirm_delete_group_", "")
        print(f"Tentative de suppression du groupe: {group_name}")

        # Recharger le CATALOG depuis le fichier
        try:
            with open('config/catalog.json', 'r', encoding='utf-8') as f:
                self.CATALOG = json.load(f)
            print(f"Catalogue chargé avec succès")
        except Exception as e:
            print(f"Erreur lors du rechargement du catalog: {e}")
            return

        if group_name in self._access_codes.get("groups", {}):
            # Supprimer le groupe des access_codes
            del self._access_codes["groups"][group_name]
            self._save_access_codes()
            print(f"Groupe {group_name} supprimé des access_codes")

            # Liste des préfixes possibles pour ce groupe
            group_prefixes = [
                f"{group_name}_",
                f"{group_name.lower()}_",
                f"{group_name.upper()}_",
                f"{group_name.capitalize()}_"
            ]

            # Créer un nouveau catalogue
            new_catalog = {}
            
            # Copier et nettoyer les catégories
            for category, content in self.CATALOG.items():
                if category == 'stats':
                    continue
                    
                # Vérifier si c'est une catégorie du groupe
                is_group_category = any(category.startswith(prefix) for prefix in group_prefixes)
                
                if is_group_category:
                    # Ne pas copier les catégories du groupe
                    print(f"Suppression de la catégorie de groupe: {category}")
                    continue
                else:
                    # Pour les catégories publiques, filtrer les produits du groupe
                    if isinstance(content, list):
                        filtered_products = []
                        for product in content:
                            if isinstance(product, dict) and 'name' in product:
                                is_group_product = any(product['name'].startswith(prefix) 
                                                     for prefix in group_prefixes)
                                if not is_group_product:
                                    filtered_products.append(product)
                                else:
                                    print(f"Suppression du produit de groupe {product['name']} de la catégorie {category}")
                        
                        # Toujours conserver la catégorie, même si elle est vide
                        new_catalog[category] = filtered_products
                        print(f"Catégorie publique {category} conservée avec {len(filtered_products)} produits")

            # Gérer les statistiques
            new_stats = {
                'total_views': 0,
                'category_views': {},
                'product_views': {},
                'last_updated': datetime.now().strftime('%H:%M:%S'),
                'last_reset': self.CATALOG.get('stats', {}).get('last_reset', datetime.now().strftime('%Y-%m-%d'))
            }

            # Copier les statistiques des éléments non supprimés
            old_stats = self.CATALOG.get('stats', {})
            
            # Copier les vues des catégories (seulement pour les catégories non-groupe)
            for category, views in old_stats.get('category_views', {}).items():
                if not any(category.startswith(prefix) for prefix in group_prefixes):
                    new_stats['category_views'][category] = views
                    new_stats['total_views'] += views

            # Copier les vues des produits (sauf ceux du groupe)
            for category, products in old_stats.get('product_views', {}).items():
                if not any(category.startswith(prefix) for prefix in group_prefixes):
                    new_stats['product_views'][category] = {}
                    for product_name, product_views in products.items():
                        # Ne pas copier les stats des produits du groupe
                        if not any(product_name.startswith(prefix) for prefix in group_prefixes):
                            new_stats['product_views'][category][product_name] = product_views

            # Ajouter les statistiques au catalogue
            new_catalog['stats'] = new_stats

            # Mettre à jour et sauvegarder le catalogue
            self.CATALOG = new_catalog
            print(f"Nouveau catalogue créé avec {len(new_catalog) - 1} catégories")

            try:
                with open('config/catalog.json', 'w', encoding='utf-8') as f:
                    json.dump(self.CATALOG, f, indent=4, ensure_ascii=False)
                print("Catalogue sauvegardé avec succès")

                # Mettre à jour la variable globale CATALOG
                global CATALOG
                CATALOG = self.CATALOG

            except Exception as e:
                print(f"Erreur lors de la sauvegarde: {e}")
                await query.edit_message_text(
                    "❌ Erreur lors de la sauvegarde du catalogue.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Retour", callback_data="manage_groups")
                    ]])
                )
                return CHOOSING

            await query.edit_message_text(
                f"✅ Groupe *{group_name}* et tous ses contenus supprimés avec succès!",
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

    async def ban_user(self, user_id: int, context: ContextTypes.DEFAULT_TYPE = None) -> bool:
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
        
            # Si on a le context, on supprime les messages précédents
            if context and hasattr(context, 'user_data'):
                chat_id = user_id  # Le chat_id est le même que le user_id dans un chat privé
            
                # Liste des clés des messages à supprimer
                messages_to_delete = [
                    'menu_message_id',
                    'banner_message_id',
                    'category_message_id',
                    'last_product_message_id',
                    'initial_welcome_message_id'
                ]
            
                # Supprimer les messages un par un
                for message_key in messages_to_delete:
                    if message_key in context.user_data:
                        try:
                            await context.bot.delete_message(
                                chat_id=chat_id,
                                message_id=context.user_data[message_key]
                            )
                            del context.user_data[message_key]
                        except Exception as e:
                            print(f"Erreur lors de la suppression du message {message_key}: {e}")
            
                # Vider toutes les données utilisateur
                context.user_data.clear()
        
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
            # Vérifier si l'utilisateur est admin
            if not self.is_user_authorized(update.effective_user.id):
                return

            # Vérifier les arguments
            args = update.message.text.split()
            if len(args) < 2:
                message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Usage : /ban <user_id>"
                )
                await asyncio.sleep(3)
                await message.delete()
                return

            # Récupérer l'ID de l'utilisateur à bannir
            try:
                target_user_id = int(args[1])
                target_chat_id = target_user_id  # Dans Telegram, user_id = chat_id pour les conversations privées
            except ValueError:
                message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ L'ID utilisateur doit être un nombre"
                )
                await asyncio.sleep(3)
                await message.delete()
                return

            # Supprimer tous les messages du bot pour l'utilisateur banni
            try:
                # Essayer de supprimer les derniers messages dans le chat avec l'utilisateur
                for i in range(50):  # Essayer de supprimer les 50 derniers messages
                    try:
                        await context.bot.delete_message(
                            chat_id=target_chat_id,
                            message_id=update.message.message_id - i
                        )
                    except Exception:
                        continue
            except Exception as e:
                print(f"Erreur lors de la suppression des messages: {e}")

            # Bannir l'utilisateur
            if await self.ban_user(target_user_id, context):
                message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ Utilisateur {target_user_id} banni avec succès"
                )
            else:
                message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Erreur lors du bannissement de l'utilisateur"
                )

            # Supprimer la commande /ban
            try:
                await update.message.delete()
            except Exception:
                pass

            await asyncio.sleep(3)
            await message.delete()

        except Exception as e:
            print(f"Erreur dans handle_ban_command: {e}")
            message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Une erreur est survenue"
            )
            await asyncio.sleep(3)
            await message.delete()
            
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
