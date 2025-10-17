"""lg-rez / features / Process d'inscription

Étapes préliminaires pour les joueurs avant le début de saison

"""

import asyncio

import discord

from lgrez import config
from lgrez.blocs import tools, env, gsheets
from lgrez.bdd import Joueur, Role, Camp, Statut
from lgrez.blocs.journey import DiscordJourney


async def new_channel(member: discord.Member) -> discord.TextChannel:
    """Crée un nouveau salon privé.

    Peut être étendue, mais toujours appeler cette fonction pour créer le chan en lui-même,
    au risque d'altérer le fonctionnement normal du bot.

    Args:
        member: Le membre pour qui créer le salon.

    Returns:
        Le salon créé.
    """
    categ = await tools.multicateg(config.private_chan_category_name)
    chan = await member.guild.create_text_channel(
        f"{config.private_chan_prefix}{member.name}",
        topic=str(member.id),  # topic provisoire : ID du membre
        category=categ,
    )
    await chan.set_permissions(member, read_messages=True, send_messages=True)

    return chan


async def register_on_tdb(joueur: Joueur) -> None:
    """Enregistre un joueur dans le Tableau de bord.

    Peut être personnalisé à un autre système de gestion des joueurs.

    Args:
        joueur: Le joueur à enregistrer.

    Note:
        Fonction asynchrone depuis la version 2.2.2.
    """
    SHEET_ID = env.load("LGREZ_TDB_SHEET_ID")
    workbook = await gsheets.connect(SHEET_ID)
    sheet = await workbook.worksheet(config.tdb_main_sheet)
    values = await sheet.get_all_values()  # Liste de listes

    head = values[config.tdb_header_row - 1]
    # Ligne d'en-têtes (noms des colonnes), - 1 car indexé à 0

    id_index = gsheets.a_to_index(config.tdb_id_column)
    pk = head[id_index]
    if pk != Joueur.primary_col.key:
        raise ValueError(
            "Tableau de bord : la cellule "
            "`config.tdb_id_column` / `config.tdb_header_row` = "
            f"`{config.tdb_id_column}{config.tdb_header_row}` "
            f"vaut `{pk}` au lieu de la clé primaire de la table "
            f"`Joueur`, `{Joueur.primary_col.key}` !"
        )

    mstart, mstop = config.tdb_main_columns
    main_indexes = range(gsheets.a_to_index(mstart), gsheets.a_to_index(mstop) + 1)
    # Indices des colonnes à remplir
    cols = {}
    for index in main_indexes:
        col = head[index]
        if col in Joueur.attrs:
            cols[col] = Joueur.attrs[col]
        else:
            raise ValueError(
                f"Tableau de bord : l'index de la zone principale "
                f"`{col}` n'est pas une colonne de la table `Joueur` !"
                " (voir `lgrez.config.main_indexes` / "
                "`lgrez.config.tdb_header_row`)"
            )

    tstart, tstop = config.tdb_tampon_columns
    tampon_indexes = range(gsheets.a_to_index(tstart), gsheets.a_to_index(tstop) + 1)

    TDB_tampon_index = {}
    for index in tampon_indexes:
        col = head[index].partition("_")[2]
        if col in cols:
            TDB_tampon_index[col] = index
        else:
            raise ValueError(
                f"Tableau de bord : l'index de zone tampon `{head[index]}` "
                f"réfère à la colonne `{col}` (partie suivant le premier "
                f"underscore), qui n'est pas une colonne de la zone "
                "principale ! (voir `lgrez.config.tampon_indexes` / "
                "`lgrez.config.main_indexes`)"
            )

    plv = config.tdb_header_row  # Première Ligne Vide
    # (si tableau vide, suit directement le header, - 1 pour l'indexage)
    for i_row, row in enumerate(values):
        # On parcourt les lignes du TDB
        if i_row < config.tdb_header_row:
            # Ligne avant le header / le header (car décalage de 1)
            continue

        if row[id_index].isdigit():
            # Si il y a un vrai ID dans la colonne ID
            plv = i_row + 1

    modifs = [gsheets.Modif(plv, id_index, joueur.discord_id)]
    for index in main_indexes:
        val = getattr(joueur, head[index])
        modifs.append(gsheets.Modif(plv, index, val))
    for index in tampon_indexes:
        val = getattr(joueur, head[index].partition("_")[2])
        # Colonnes "tampon_<col>" ==> <col>
        modifs.append(gsheets.Modif(plv, index, val))

    try:
        await gsheets.update(sheet, *modifs)
    except gsheets.ConnectionError:
        await joueur.private_chan.send("Petit problème, on réessaie...")
        await asyncio.sleep(10)
        await gsheets.update(sheet, *modifs)


# Routine d'inscription (fonction appelée par la commande /co)
async def main(member: discord.Member) -> None:
    """Routine d'inscription complète d'un joueur.

    Args:
        member: Le joueur à inscrire.

    Crée et paramètre le salon privé du joueur, lui pose des questions et l'inscrit en base.

    Personnalisation : voir :obj:`.config.demande_chambre`, :obj:`.config.chambre_mj`,
    :func:`.config.additional_inscription_step` et :obj:`.config.debut_saison`.

    Commande appelée à l'arrivée sur le serveur, utiliser :meth:`\/co <.bot.Special.Special.co.callback>`
    pour trigger cette commande depuis Discord.
    """
    try:
        joueur = Joueur.from_member(member)
    except ValueError:  # Joueur pas encore inscrit en base
        pass
    else:  # Joueur dans la bdd = déjà inscrit
        chan = joueur.private_chan
        await chan.set_permissions(member, read_messages=True, send_messages=True)
        await chan.send(f"Saloww ! {member.mention} tu es déjà inscrit, viens un peu ici !")
        return

    if chan := next((chan for chan in config.guild.text_channels if chan.topic == str(member.id)), None):
        # Inscription en cours (topic du chan = ID du membre)
        await chan.set_permissions(member, read_messages=True, send_messages=True)
        await chan.send(f"Tu as déjà un salon à ton nom, {member.mention}, par ici !")

    else:  # Pas d'inscription déjà en cours : création channel
        chan = await new_channel(member)

    # Récupération nom et renommages

    await chan.send(
        f"Bienvenue {member.mention} ! Je suis le bot à qui tu auras affaire tout au long de la partie.\n"
        "Tu es ici sur ton salon textuel privé, auquel seul toi et les MJ ont accès ! "
        "C'est ici que tu lanceras toutes les commandes pour voter, te renseigner... "
        "mais aussi que les MJ discuteront avec toi en cas de soucis.\n\n"
        "Pas de panique, je vais tout t'expliquer !"
    )

    class InscriptionView(discord.ui.View):
        @discord.ui.button(label="Terminer mon inscription", style=discord.ButtonStyle.success)
        async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
            async with DiscordJourney(interaction) as journey:
                await _inscription_process(journey, member, chan)

        async def on_error(self, _interaction: discord.Interaction, error: Exception, _item: discord.ui.Item) -> None:
            raise error

    await chan.send("Avant toute chose, finalisons ton inscription !", view=InscriptionView(timeout=None))


async def _inscription_process(journey: DiscordJourney, member: discord.Member, chan: discord.TextChannel) -> None:
    await journey.send(
        "Très bien !\nD'abord, un point règles nécessaire :\n\n"
        + tools.quote_bloc(
            "En t'inscrivant au Loup-Garou de la Rez, tu garantis vouloir participer à cette édition et "
            "t'engages à respecter les règles du jeu. Si tu venais à entraver le bon déroulement de la partie "
            "pour une raison ou une autre, les MJ s'autorisent à te mute ou t'expulser du Discord sans préavis."
        )
    )

    await tools.sleep(chan, 5)

    if not await journey.yes_no("C'est bon pour toi ?"):
        await journey.send(
            f"Pas de soucis. Si tu changes d'avis ou que c'est un missclick, appelle un MJ aled ({tools.code('@MJ')})."
        )
        return

    await journey.buttons(
        "Parfait. Je vais d'abord avoir besoin de ton (vrai) nom, celui par lequel on t'appelle au quotidien. "
        "Attention, tout troll sera foudracanonné™ !",
        {None: discord.ui.Button(label="Go !", style=discord.ButtonStyle.success)},
    )

    ok = False
    while not ok:
        prenom, nom_famille = await journey.modal("À qui avons-nous l'honneur ?", "Prénom", "Nom")
        nom = f"{prenom.strip().title()} {nom_famille.strip().title()}"

        ok = await journey.yes_no(
            f"Tu me dis donc t'appeler {tools.bold(nom)}. C'est bon pour toi ? Pas d'erreur, pas de troll ?"
        )

    await chan.edit(name=config.private_chan_prefix + nom)  # Renommage conv
    if member.top_role < config.Role.mj:
        # Renommage joueur (ne peut pas renommer les MJ)
        await member.edit(nick=nom)

    await journey.send(
        "Parfait ! Je t'ai renommé(e) pour que tout le monde te reconnaisse, et j'ai renommé cette conversation."
    )

    if config.demande_chambre:
        await tools.sleep(chan, 3)
        if await journey.yes_no("Bien, dernière chose : habites-tu à la Rez ?"):
            (chambre,) = await journey.modal("Et où te trouve-t-on ?", "Numéro de chambre")
        else:
            chambre = config.chambre_mj
    else:
        chambre = None

    res = await config.additional_inscription_step(journey, member, chan)
    if res is False:
        return

    if config.demande_chambre:
        await journey.send(f"{nom}, en chambre {chambre}... Je t'inscris en base !")
    else:
        await journey.send(f"{nom}... Je t'inscris en base !")

    async with chan.typing():
        # Enregistrement en base

        joueur = Joueur(
            discord_id=member.id,
            chan_id_=chan.id,
            nom=member.display_name,
            chambre=chambre,
            statut=Statut.vivant,
            role=Role.default(),
            camp=Camp.default(),
            votant_village=True,
            votant_loups=False,
            role_actif=False,
        )
        joueur.add()

        # Ajout sur le TDB

        await register_on_tdb(joueur)

        # Grant accès aux channels joueurs et information

        await member.add_roles(config.Role.joueur_en_vie)
        await chan.edit(topic="Ta conversation privée avec le bot, c'est ici que tout se passera !")

    # Conseiller d'ACTIVER TOUTES LES NOTIFS du chan
    # (et mentions only pour le reste, en activant @everyone)
    await chan.send(
        f"Tu es maintenant inscrit(e) ! Je t'ai attribué le rôle {config.Role.joueur_en_vie.mention}, "
        "qui te donne l'accès à tout plein de nouveaux salons à découvrir."
    )
    await chan.send(
        "Juste quelques dernières choses :\n "
        "- Plein de commandes te sont d'ores et déjà accessibles ! "
        f"Découvre les toutes en tapant `/` dans la zone d'envoi de messages ;\n"
        f"- Si tu as besoin d'aide, mentionne simplement les MJs ({tools.code('@' + config.Role.mj.name)}) "
        "et on viendra voir ce qui se passe !\n "
        "- Si ce n'est pas le cas, je te conseille fortement d'installer Discord sur ton téléphone, et "
        f"d'{tools.bold('activer toutes les notifications')} pour ce salon ! Promis, pas de spam :innocent:\n"
        'Pour le reste du serveur, tu peux le mettre en "mentions only",'
        f"en activant le {tools.code('@everyone')} – il est limité ;\n\n"
        "Enfin, n'hésite pas à me parler, j'ai toujours quelques réponses en stock..."
    )

    await tools.sleep(chan, 5)
    await chan.send(
        f"Voilà, c'est tout bon ! Installe toi bien confortablement, la partie commence le {config.debut_saison}."
    )

    # Log
    await tools.log(
        f"Inscription de {member.name}#{member.discriminator} réussie\n"
        f" - Nom : {nom}\n - Chambre : {chambre}\n"
        f" - Channel créé : {chan.mention}"
    )
