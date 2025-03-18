    elif query.data.startswith("view_"):
        category = query.data.replace("view_", "")
        if category in CATALOG:
            # Vérifier les permissions de groupe
            user_id = query.from_user.id
            show_category = True

            # Vérifier si c'est une catégorie de groupe
            if "groups" in admin_features._access_codes:
                for group_name in admin_features._access_codes.get("groups", {}).keys():
                    if category.startswith(f"{group_name}_"):
                        # Vérifier si l'utilisateur est membre du groupe
                        if user_id not in admin_features._access_codes["groups"][group_name]:
                            show_category = False
                            await query.answer("❌ Vous n'avez pas accès à cette catégorie", show_alert=True)
                            return CHOOSING
                        break

            if show_category:
                # Initialisation des stats si nécessaire
                if 'stats' not in CATALOG:
                    CATALOG['stats'] = {
                        "total_views": 0,
                        "category_views": {},
                        "product_views": {},
                        "last_updated": datetime.now(paris_tz).strftime("%H:%M:%S")
                    }

                if 'category_views' not in CATALOG['stats']:
                    CATALOG['stats']['category_views'] = {}

                if category not in CATALOG['stats']['category_views']:
                    CATALOG['stats']['category_views'][category] = 0

                # Mettre à jour les statistiques
                CATALOG['stats']['category_views'][category] += 1
                CATALOG['stats']['total_views'] += 1
                CATALOG['stats']['last_updated'] = datetime.now(paris_tz).strftime("%H:%M:%S")
                save_catalog(CATALOG)

                products = CATALOG[category]
        
                # Obtenir le nom d'affichage pour la catégorie (sans préfixe)
                display_category_name = category
                user_id = query.from_user.id
        
                # Retirer le préfixe du groupe pour l'affichage
                if "groups" in admin_features._access_codes:
                    for group_name, members in admin_features._access_codes["groups"].items():
                        if user_id in members and category.startswith(f"{group_name}_"):
                            display_category_name = category.replace(f"{group_name}_", "")
                            break

                # Afficher la liste des produits avec le nom de catégorie sans préfixe
                text = f"*{display_category_name}*\n\n"
                keyboard = []
                for product in products:
                    # Créer un ID court unique pour ce produit
                    nav_id = str(abs(hash(product['name'])) % 1000)
                    # Stocker les informations du produit avec cet ID
                    context.user_data[f'nav_product_{nav_id}'] = {
                        'category': category,
                        'name': product['name']
                    }
                    keyboard.append([InlineKeyboardButton(
                        product['name'],
                        callback_data=f"product_{nav_id}"  # Utiliser l'ID court
                    )])

                keyboard.append([InlineKeyboardButton("🔙 Retour au menu", callback_data="show_categories")])

                try:
                    # Suppression du dernier message de produit (photo ou vidéo) si existe
                    if 'last_product_message_id' in context.user_data:
                        try:
                            await context.bot.delete_message(
                                chat_id=query.message.chat_id,
                                message_id=context.user_data['last_product_message_id']
                            )
                            del context.user_data['last_product_message_id']
                        except:
                            pass

                    print(f"Texte du message : {text}")
                    print(f"Clavier : {keyboard}")

                    # Éditer le message existant au lieu de le supprimer et recréer
                    await query.message.edit_text(
                        text=text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
    
                    context.user_data['category_message_id'] = query.message.message_id
                    context.user_data['category_message_text'] = text
                    context.user_data['category_message_reply_markup'] = keyboard

                except Exception as e:
                    print(f"Erreur lors de la mise à jour du message des produits: {e}")
                    # Si l'édition échoue, on crée un nouveau message
                    message = await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                    context.user_data['category_message_id'] = message.message_id

                # Mettre à jour les stats des produits seulement s'il y en a
                if products:
                    if 'stats' not in CATALOG:
                        CATALOG['stats'] = {
                            "total_views": 0,
                            "category_views": {},
                            "product_views": {},
                            "last_updated": datetime.now(paris_tz).strftime("%H:%M:%S"),
                            "last_reset": datetime.now(paris_tz).strftime("%Y-%m-%d")
                        }

                    if 'product_views' not in CATALOG['stats']:
                        CATALOG['stats']['product_views'] = {}
                    if category not in CATALOG['stats']['product_views']:
                        CATALOG['stats']['product_views'][category] = {}

                    # Mettre à jour les stats pour chaque produit dans la catégorie
                    for product in products:
                        if product['name'] not in CATALOG['stats']['product_views'][category]:
                            CATALOG['stats']['product_views'][category][product['name']] = 0
                        CATALOG['stats']['product_views'][category][product['name']] += 1

                    save_catalog(CATALOG)
