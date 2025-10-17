"""lg-rez / features / Synchronisation GSheets

Récupération et application des données des GSheets :
modifications décidées via le Tableau de bord et rôles

"""

from __future__ import annotations

import asyncio
import datetime
import time
import traceback
from typing import Any

from discord import app_commands
import sqlalchemy
import sqlalchemy.orm

from lgrez import config, bdd
from lgrez.blocs import tools, env, gsheets
from lgrez.bdd import Joueur, Role, Camp, BaseAction, BaseCiblage, Statut, ActionTrigger
from lgrez.blocs.journey import DiscordJourney, journey_command
from lgrez.features import gestion_actions


class TDBModif(gsheets.Modif):
    """Modification flag sur le Tableau de bord, à appliquer.

    Attributes:
        id: ID Discord du joueur concerné.
        col: Colonne de :class:`~bdd.Joueur` à modifier.
        val: Nouvelle valeur.
        row: Numéro de la ligne (0 = ligne 1).
        column: Numéro de la colonne (0 = colonne A).

    Sous-classe de :class:`.gsheets.Modif`.
    """

    def __init__(self, id: int, col: str, val: Any, row: int, column: int) -> None:
        """Initializes self."""
        super().__init__(row, column, val)
        self.id = id
        self.col = col

    def __repr__(self) -> str:
        """Returns repr(self)"""
        return f"<TDBModif id {self.id}: {self.col} = {self.val!r}>"

    def __eq__(self, other: TDBModif) -> bool:
        """Returns self == other"""
        return super().__eq__(other) and self.id == other.id and self.col == other.col


class _ComparaisonResults:
    def __init__(self) -> None:
        self.n_id = 0
        self.upd = []
        self.add = []
        self.suppr = []
        self.sub_results = None

    @property
    def n_upd(self) -> int:
        return len(self.upd)

    @property
    def n_tot_attr_upd(self) -> int:
        return sum(len(up) for up in self.upd)

    @property
    def n_add(self) -> int:
        return len(self.add)

    @property
    def n_suppr(self) -> int:
        return len(self.suppr)

    def __iadd__(self, other: _ComparaisonResults) -> _ComparaisonResults | NotImplemented:
        if isinstance(other, type(self)):
            self.n_id += other.n_id
            self.upd += other.upd
            self.add += other.add
            self.suppr += other.suppr
            if self.sub_results:
                self.sub_results += other.sub_results
            elif other.sub_results:
                self.sub_results = other.sub_results
            else:
                self.sub_results = None
            return self
        else:
            return NotImplemented

    def __add__(self, other: _ComparaisonResults) -> _ComparaisonResults | NotImplemented:
        if isinstance(other, type(self)):
            new = type(self)()
            new += self
            new += other
            return new
        else:
            return NotImplemented

    @property
    def log(self):
        r = f"- {self.n_id} entrées identiques\n"
        if self.add:
            r += f"- Nouvelles entrées ({self.n_add}) : {self.add}\n"
        if self.upd:
            r += f"- Entrées modifiées ({self.n_upd}, total attrs {self.n_tot_attr_upd}) : {self.upd}\n"
        if self.suppr:
            r += f"- Entrées supprimées ({self.n_suppr}) : {self.suppr}\n"
        return r

    @property
    def bilan(self):
        return (
            f"({self.n_id} entrées identiques - {self.n_upd} mises "
            f"à jour ({self.n_tot_attr_upd} attributs au total), "
            f"{self.n_add} ajouts, {self.n_suppr} suppressions"
        )


def _compare_items(
    existants: dict, new: dict, table: type, cols: dict, primary_key: str, bc_cols: dict | None = None
) -> _ComparaisonResults:
    """Utility function for /fillroles: compare table items and dicts"""
    res = _ComparaisonResults()
    if table == BaseAction:
        res.sub_results = _ComparaisonResults()

    # --- 5 : Pour chaque ligne : Mise à jour / Ajout
    for pk, args in new.items():
        pk = args[primary_key]
        if pk in existants:
            # Instance existante
            actual = existants[pk]
            attr_upd = []
            for col in cols.keys():
                if getattr(actual, col) != args[col]:
                    setattr(actual, col, args[col])
                    attr_upd.append(col)

            if table == BaseAction:
                # Many-to-many BaseAction <-> Rôle
                if set(actual.roles) != set(args["roles"]):
                    actual.roles = args["roles"]
                    attr_upd.append("roles")

                # BaseCiblages : on compare avec ceux existants !
                bcs = args["base_ciblages"]
                for bc_args in bcs:
                    bc_args["base_action"] = actual  # si création

                bc_existants = {bc.slug: bc for bc in actual.base_ciblages}
                new_bcs = {bc["slug"]: bc for bc in bcs}
                sub_res = _compare_items(bc_existants, new_bcs, BaseCiblage, cols=bc_cols, primary_key="slug")
                res.sub_results += sub_res

            if attr_upd:
                res.upd.append({actual: attr_upd})
            else:
                res.n_id += 1

        else:
            # Créer l'instance
            if table == BaseAction:  # BaseCiblages
                bcs = [BaseCiblage(**bc_args) for bc_args in args["base_ciblages"]]
                args["base_ciblages"] = bcs
                res.sub_results.add.extend(bcs)
            inst = table(**args)
            inst.add()
            res.add.append(inst)

    # --- 6 : Drop anciennes instances
    for pk, act in existants.items():
        if pk not in new:
            config.session.delete(act)
            # pas .delete(), pour ne pas commit
            res.suppr.append(act.primary_key)

    return res


def transtype(value: Any, cst) -> sqlalchemy.schema.Column | bdd.base.TableMeta | sqlalchemy.orm.RelationshipProperty:
    """Utilitaire : caste une donnée brute d'un GSheet selon sa colonne.

    Args:
        value (Any): valeur à transtyper.
        cst: Colonne, table ou relationship (many-to-one) associée.

    Types pris en charge dans le cas d'une colonne :

        - :class:`sqlalchemy.types.String` et dérivés (``Text``, ``Varchar``...)
        - :class:`sqlalchemy.types.Integer` et dérivés (``BigInteger``...)
        - :class:`sqlalchemy.types.Boolean`
        - :class:`sqlalchemy.types.Time`
        - :class:`sqlalchemy.types.Enum`

    Dans le cas d'une table ou d'une relation many-to-one vers une table, ``value`` est interprété
    comme la clé primaire de la table / de la table liée.  Les valeurs interprétées ``None`` ne sont
    pas acceptées, même dans le cas d'une relation avec contrainte One-to-many faite *nullable*.

    Returns:
        L'objet Python correspondant au type de la colonne / table liée (:class:`str`, :class:`int`,
        :class:`bool`, :class:`datetime.time`, :class:`enum.Enum`, :class:`.bdd.base.TableBase`) ou ``None``

    Raises:
        ValueError: la conversion n'est pas possible (ou ``value`` est évaluée ``None``
            et la colonne n'est pas *nullable*).
        TypeError: type de colonne non pris en charge.
    """
    if isinstance(cst, sqlalchemy.orm.RelationshipProperty):
        # Relationship
        table = cst.entity.entity  # SQLAlchemy black magic
        if not isinstance(value, table.primary_col.type.python_type):
            raise ValueError(
                f"Valeur '{value}' incorrecte pour la colonne '{cst.key}' "
                f"(one-to-many avec '{table.__name__}', de clé primaire "
                f"'{table.primary_col.name}', type '{table.primary_col.type}')"
            ) from None

        inst = table.query.get(value)
        if inst is None:
            raise ValueError(
                f"Valeur '{value}' incorrecte pour la colonne '{cst.key}': "
                f"instance de '{table.__name__}' correspondante non trouvée."
            )

        return inst

    elif isinstance(cst, bdd.base.TableMeta):
        # Table
        if not isinstance(value, cst.primary_col.type.python_type):
            raise ValueError(
                f"Valeur '{value}' incorrecte pour la table '{cst.__name__}', "
                f"de clé primaire '{cst.primary_col.name}', type "
                f"'{cst.primary_col.type}')"
            ) from None

        inst = cst.query.get(value)
        if inst is None:
            raise ValueError(
                f"Valeur '{value}' incorrecte pour la table '{cst.__name__}': instance correspondante non trouvée."
            )

        return inst

    # Colonne propre
    try:
        if value in (None, "", "None", "none", "Null", "null"):
            if not cst.nullable:
                if cst.default is None:
                    raise ValueError
                else:
                    return cst.default.arg
            return None
        if isinstance(cst.type, sqlalchemy.Enum):
            enum = cst.type.python_type
            try:
                return enum[value]
            except KeyError:
                raise ValueError
        if isinstance(cst.type, sqlalchemy.String):
            return str(value)
        if isinstance(cst.type, sqlalchemy.Integer):
            return int(value)
        if isinstance(cst.type, sqlalchemy.Boolean):
            if value in {True, 1} or (isinstance(value, str) and value.lower() in {"true", "vrai", "1"}):
                return True
            elif value in {False, 0} or (isinstance(value, str) and value.lower() in {"false", "faux", "0"}):
                return False
            else:
                raise ValueError
        if isinstance(cst.type, sqlalchemy.Time):  # hh:mm
            try:
                h, m, _ = value.split(":")
            except ValueError:
                h, m = value.split(":")
            return datetime.time(hour=int(h), minute=int(m))

        raise TypeError(f"Unhandled type for column '{cst.key}': '{cst.type}'")

    except (ValueError, TypeError):
        raise ValueError(
            f"Valeur '{value}' incorrecte pour la colonne '{cst.key}' "
            f"(type '{cst.type}'/{'NOT NULL' if not cst.nullable else ''})"
        ) from None


async def get_sync() -> list[TDBModif]:
    """Récupère les modifications en attente sur le TDB.

    Charge les données du Tableau de bord (variable d'environment ``LGREZ_TDB_SHEET_ID``),
    compare les informations qui y figurent avec celles de la base de données (:class:`.bdd.Joueur`).

    Supprime les joueurs en base absents du Tableau de bord, lève une erreur dans le cas inverse,
    n'applique aucune autre modification.

    Returns:
        La liste des modifications à apporter

    Note:
        Fonction asynchrone depuis la version 2.2.2.
    """
    # RÉCUPÉRATION INFOS GSHEET ET VÉRIFICATIONS

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

    # CONVERSION INFOS GSHEET EN PSEUDO-UTILISATEURS

    joueurs_TDB = []  # Joueurs tels qu'actuellement dans le TDB
    ids_TDB = []  # discord_ids des différents joueurs du TDB
    rows_TDB = {}  # Lignes ou sont les différents joueurs du TDB

    for i_row, row in enumerate(values):
        # On parcourt les lignes du TDB
        if i_row < config.tdb_header_row:
            # Ligne avant le header / le header (car décalage de 1)
            continue

        id_cell = row[id_index]
        if not id_cell.isdigit():
            # La cellule ne contient pas un ID ==> skip
            continue

        id = int(id_cell)
        # Construction dictionnaire correspondant à l'utilisateur
        joueur_TDB = {head[index]: transtype(row[index], cols[head[index]]) for index in main_indexes}
        joueur_TDB[pk] = id
        joueurs_TDB.append(joueur_TDB)
        ids_TDB.append(id)
        rows_TDB[id] = i_row

    # RÉCUPÉRATION UTILISATEURS BDD

    joueurs_BDD = {joueur.discord_id: joueur for joueur in Joueur.query.all()}

    # COMPARAISON

    for id, joueur in list(joueurs_BDD.items()):
        if id not in ids_TDB:
            # Joueur en base supprimé du TDB
            del joueurs_BDD[id]
            joueur.delete()

    modifs = []  # modifs à porter au TDB (liste de TDBModifs)
    for joueur_TDB in joueurs_TDB:  # Différences
        id = joueur_TDB[pk]

        try:
            joueur = joueurs_BDD[id]
        except KeyError:  # Joueur en base pas dans le TDB
            raise ValueError(f"Joueur `{joueur_TDB['nom']}` hors base : vérifier processus d'inscription") from None

        for col in cols:
            if getattr(joueur, col) != joueur_TDB[col]:
                # Si <col> diffère entre TDB et cache,
                # on ajoute la modif (avec update du tampon)
                modifs.append(
                    TDBModif(id=id, col=col, val=joueur_TDB[col], row=rows_TDB[id], column=TDB_tampon_index[col])
                )

    return modifs


async def validate_sync(modifs: list[TDBModif]) -> None:
    """Valide des modifications sur le Tableau de bord (case plus en rouge).

    Args:
        modifs: liste des modifications à apporter.

    Modifie sur le Tableau de bord (variable d'environment ``LGREZ_TDB_SHEET_ID``)
    et applique les modifications contenues dans ``modifs``.

    Note:
        Fonction asynchrone depuis la version 2.2.2.
    """
    SHEET_ID = env.load("LGREZ_TDB_SHEET_ID")
    workbook = await gsheets.connect(SHEET_ID)  # Tableau de bord
    sheet = await workbook.worksheet(config.tdb_main_sheet)

    try:
        await gsheets.update(sheet, *modifs)
    except gsheets.ConnectionError:
        await asyncio.sleep(10)
        await gsheets.update(sheet, *modifs)


async def modif_joueur(joueur_id: int, modifs: list[TDBModif], silent: bool = False) -> tuple[list[TDBModif], str]:
    """Attribue les modifications demandées au joueur

    Args:
        joueur_id: ID Discord du joueur concerné.
        modifs: Liste des modifications à apporter.
        silent: Si ``True``, ne notifie pas le joueur des modifications.

    Returns:
        La liste des modifications appliquées et le changelog textuel associé (pour log global).

    Raises:
        ValueError: pas de joueur d'ID ``joueur_id`` en base

    Pour chaque modification dans ``modifs``, applique les conséquences adéquates
    (rôles, nouvelles actions, tâches planifiées...) et informe le joueur si ``silent`` vaut ``False``.
    """
    joueur = Joueur.query.get(joueur_id)
    if not joueur:
        raise ValueError(f"/sync : joueur d'ID {joueur_id} introuvable")

    member = joueur.member
    chan = joueur.private_chan

    changelog = f"\n- {member.display_name} (@{member.name}#{member.discriminator}) :\n"
    notif = ""
    af = ":arrow_forward:"  # Flèche introduisant chaque modif

    if not modifs:
        changelog += f"    [NO MODIFS]\n"
        return [], changelog

    done = []
    for modif in modifs:
        changelog += f"    - {modif.col} : {modif.val}\n"

        if modif.col == "nom":  # Renommage joueur
            await member.edit(nick=modif.val)
            await chan.edit(name=f"{config.private_chan_prefix}{modif.val}")
            if not silent:
                notif += f"{af} Tu t'appelles maintenant {tools.bold(modif.val)}.\n"

        elif modif.col == "chambre" and not silent:  # Modification chambre
            notif += f"{af} Tu habites maintenant en chambre {tools.bold(modif.val)}.\n"

        elif modif.col == "statut":
            if modif.val == Statut.vivant:  # Statut = vivant
                await member.add_roles(config.Role.joueur_en_vie)
                await member.remove_roles(config.Role.joueur_mort)
                if not silent:
                    notif += f"{af} Tu es maintenant en vie. EN VIE !!!\n"

            elif modif.val == Statut.mort:  # Statut = mort
                await member.add_roles(config.Role.joueur_mort)
                await member.remove_roles(config.Role.joueur_en_vie)
                if not silent:
                    notif += (
                        f"{af} Tu es malheureusement décédé(e) :cry:\n"
                        "Ça arrive même aux meilleurs, en espérant "
                        "que ta mort ait été belle !\n"
                    )
                # Actions à la mort
                await process_mort(joueur)

            elif modif.val == Statut.MV:  # Statut = MV
                await member.add_roles(config.Role.joueur_en_vie)
                await member.remove_roles(config.Role.joueur_mort)
                if not silent:
                    notif += (
                        f"{af} Oh ! Tu viens d'être réduit(e) au statut de "
                        "mort-vivant... Un MJ viendra te voir très vite, "
                        "si ce n'est déjà fait, mais retient que la partie "
                        "n'est pas finie pour toi !\n"
                    )

            elif not silent:  # Statut = autre
                notif += f"{af} Nouveau statut : {tools.bold(modif.val)} !\n"

        elif modif.col == "role":  # Modification rôle
            new_role = modif.val
            for action in joueur.actions_actives:
                if action.base in joueur.role.base_actions:
                    # Suppression anciennes actions de rôle
                    gestion_actions.delete_action(action)

            for base in new_role.base_actions:
                # Ajout et création des tâches si trigger temporel
                gestion_actions.add_action(joueur=joueur, base=base, cooldown=0, charges=base.base_charges)

            if not silent:
                notif += (
                    f"{af} Ton nouveau rôle, si tu l'acceptes : "
                    f"{tools.bold(new_role.nom_complet)} !\nQue ce soit pour "
                    "un jour ou pour le reste de la partie, renseigne-toi en "
                    f"tapant {tools.code(f'/roles {new_role.nom}')}.\n"
                )

        elif modif.col == "camp" and not silent:  # Modification camp
            notif += f"{af} Tu fais maintenant partie du camp « {tools.bold(modif.val.nom)} ».\n"

        elif modif.col == "votant_village" and not silent:
            if modif.val:  # votant_village = True
                notif += f"{af} Tu peux maintenant participer aux votes du village !\n"
            else:  # votant_village = False
                notif += f"{af} Tu ne peux maintenant plus participer aux votes du village.\n"

        elif modif.col == "votant_loups" and not silent:
            if modif.val:  # votant_loups = True
                notif += f"{af} Tu peux maintenant participer aux votes des loups ! Amuse-toi bien :wolf:\n"
            else:  # votant_loups = False
                notif += f"{af} Tu ne peux maintenant plus participer aux votes des loups.\n"

        elif modif.col == "role_actif" and not silent:
            if modif.val:  # role_actif = True
                notif += f"{af} Tu peux maintenant utiliser tes pouvoirs !\n"
            else:  # role_actif = False
                notif += f"{af} Tu ne peux maintenant plus utiliser aucun pouvoir.\n"

        setattr(joueur, modif.col, modif.val)
        # Dans tous les cas, on modifie en base
        # (après, pour pouvoir accéder aux vieux attribus plus haut)
        done.append(modif)

    if not silent:
        await chan.send(
            f":zap: {member.mention} Une action divine vient "
            f"de modifier ton existence ! :zap:\n\n{notif}\n"
            + tools.ital(":warning: Si tu penses qu'il y a erreur, appelle un MJ au plus vite !")
        )

    return done, changelog


async def process_mort(joueur: Joueur) -> None:
    """Applique les conséquences de la mort d'un joueur.

        * Ouverture des actions à la mort (chasseur...)
        * Archivage des boudoirs devenus inutiles.

    Args:
        joueur: Le joueur qui vient de mourir.
    """
    # Actions à la mort
    for action in joueur.actions_actives:
        if action.base.trigger_debut == ActionTrigger.mort:
            await gestion_actions.open_action(action)

    # Boudoirs au cimetière
    for boudoir in joueur.boudoirs:
        vivants = [jr for jr in boudoir.joueurs if jr.est_vivant]
        if len(vivants) <= 2:
            # <= car le joueur actuel est encore vivant, le changement
            # d'attribut est fait après
            if tools.in_multicateg(boudoir.chan.category, config.old_boudoirs_category_name):
                # Boudoir déjà au cimetière
                continue
            await boudoir.chan.send(tools.ital("[Ce boudoir contient moins de deux joueurs vivants, archivage...]"))
            categ = await tools.multicateg(config.old_boudoirs_category_name)
            await boudoir.chan.edit(category=categ)

        elif joueur == boudoir.gerant:
            # Mort du gérant (et pas cimetière) : transférer le boudoir
            bouderies = [
                bouderie for bouderie in boudoir.bouderies if bouderie.joueur != joueur and bouderie.joueur.est_vivant
            ]
            oldest_bouderie = min(bouderies, key=lambda b: b.ts_added)
            boudoir.gerant = oldest_bouderie.joueur
            boudoir.update()
            await boudoir.chan.send(
                f":warning: L'actuel gérant(e) de ce boudoir, {joueur.nom}, "
                "vient de mourir (RIP). En conséquence, ce boudoir a été "
                "transféré au membre l'ayant rejoint il y a le plus "
                f"longtemps, à savoir {boudoir.gerant.member.mention}."
            )
            await boudoir.chan.send(
                tools.ital(
                    "Le boudoir peut être transféré à un autre membre à l'aide de la commande `/boudoir transfer`."
                )
            )


DESCRIPTION = """Commandes de synchronisation des GSheets vers la BDD et les joueurs"""


@app_commands.command()
@tools.mjs_only
@journey_command
async def sync(journey: DiscordJourney, *, silent: bool = False):
    """Récupère et applique les modifs du Tableau de bord (COMMANDE MJ)

    Args:
        silent: Si spécifié à True, les joueurs ne sont pas notifiés des modifications.

    Cette commande va récupérer les modifications en attente sur le Tableau de bord (lignes en rouge),
    modifier la BDD, et appliquer les modifications dans Discord le cas échéant :
    renommage des utilisateurs, modification des rôles...
    """
    await journey.interaction.response.defer()

    # Récupération de la liste des modifs
    modifs = await get_sync()
    silent = bool(silent)
    changelog = f"Synchronisation TDB (silencieux = {silent}) :"

    if not modifs:
        await journey.send("Pas de nouvelles modifications.")
        return

    dic = {}  # Dictionnaire {ID joueur: modifs}
    for modif in modifs:
        if modif.id not in dic:
            dic[modif.id] = []
        dic[modif.id].append(modif)

    await journey.ok_cancel(
        f"{len(modifs)} modification(s) trouvée(s) pour {len(dic)} joueur(s), go ? (silent = {silent})"
    )

    # Go sync
    done = []
    mess = ""
    for joueur_id, modifs in dic.items():
        # Joueur dont au moins un attribut a été modifié
        try:
            dn, cgl = await modif_joueur(int(joueur_id), modifs, silent)
        except Exception:
            # Erreur lors d'une des modifs
            changelog += traceback.format_exc()
            mess += f":warning: Erreur joueur {joueur_id}, passage au suivant (voir logs pour les détails)\n"
        else:
            # Pas d'erreur pour ce joueur, on enregistre
            done.extend(dn)
            changelog += cgl

    if done:
        # Au moins une modification a été appliquée
        config.session.commit()
        await validate_sync(done)

    await tools.log(changelog, code=True)
    await journey.send(mess + f":arrow_forward: Fait (voir {config.Channel.logs.mention} pour le détail)")


@app_commands.command()
@tools.mjs_only
@journey_command
async def fillroles(journey: DiscordJourney):
    """Remplit les tables et #roles depuis le GSheet ad hoc (COMMANDE MJ)

    - Remplit les tables :class:`.bdd.Camp`, :class:`.bdd.Role`, :class:`.bdd.BaseAction`
        et :class:`.bdd.BaseCiblage` avec les informations du Google Sheets "Rôles et actions"
        (variable d'environnement ``LGREZ_ROLES_SHEET_ID``) ;
    - Vide le chan ``#roles`` puis le remplit avec les descriptifs de chaque rôle et camp.

    Utile à chaque début de saison / changement dans les rôles/actions.
    Met à jour les entrées déjà en base, créé les nouvelles, supprime celles obsolètes.
    """
    # ==== Mise à jour tables ===
    SHEET_ID = env.load("LGREZ_ROLES_SHEET_ID")
    workbook = await gsheets.connect(SHEET_ID)  # Rôles et actions

    for table in [Camp, Role, BaseAction]:
        await journey.send(f"Remplissage de la table {tools.code(table.__name__)}...")
        # --- 1 : Récupération des valeurs
        async with journey.channel.typing():
            try:
                sheet = await workbook.worksheet(table.__tablename__)
            except gsheets.WorksheetNotFound:
                raise ValueError(
                    f"/fillroles : feuille '{table.__tablename__}' non trouvée dans le GSheet "
                    "*Rôles et actions* (`LGREZ_ROLES_SHEET_ID`)"
                ) from None

            values = await sheet.get_all_values()
            # Liste de liste des valeurs des cellules

        # --- 2 : Détermination colonnes à récupérer
        cols = table.columns  # "dictionnaire" nom -> colonne
        cols = {col: cols[col] for col in cols.keys() if col != "id" and not col.startswith("_")}  # Colonnes publiques
        if table == Role:
            cols["camp"] = Role.attrs["camp"]
        elif table == BaseAction:
            # BaseCiblages : au bout de la feuille
            bc_cols = BaseCiblage.columns
            bc_cols = {col: bc_cols[col] for col in bc_cols.keys() if col != "id" and not col.startswith("_")}
            bc_cols_for_ith = []
            for i in range(config.max_ciblages_per_action):
                prefix = f"c{i + 1}_"
                bc_cols_for_ith.append(
                    {
                        # colonne -> nom dans la table pour le ièmme
                        col: f"{prefix}{col}"
                        for col in bc_cols
                    }
                )
        primary_key = table.primary_col.key

        # --- 3 : Localisation des colonnes (indices GSheet)
        cols_index = {}
        try:
            for key in cols.keys():
                cols_index[key] = values[0].index(key)
            if table == BaseAction:
                key = "roles"
                roles_idx = values[0].index(key)
                # BaseCiblages : au bout de la feuille
                ciblages_idx = []
                for bc_cols_names in bc_cols_for_ith:
                    idx = {}
                    for col, key in bc_cols_names.items():
                        idx[col] = values[0].index(key)
                    ciblages_idx.append(idx)
        except ValueError:
            raise ValueError(
                f"/fillroles : colonne '{key}' non trouvée dans la feuille '{table.__tablename__}' du GSheet "
                "*Rôles et actions* (`LGREZ_ROLES_SHEET_ID`)"
            ) from None

        # --- 4 : Construction dictionnaires de comparaison
        existants = {item.primary_key: item for item in table.query.all()}
        new = {}
        for row in values[1:]:
            args = {key: transtype(row[cols_index[key]], col) for key, col in cols.items()}

            if table == BaseAction:
                # Many-to-many BaseAction <-> Rôle
                roles = row[roles_idx].strip()
                if roles.startswith("#"):
                    args["roles"] = []
                else:
                    args["roles"] = [transtype(slug.strip(), Role) for slug in roles.split(",") if slug]
                # BaseCiblages
                new_bcs = []
                for idx in ciblages_idx:
                    if row[idx["slug"]]:  # ciblage défini
                        bc_args = {key: transtype(row[idx[key]], col) for key, col in bc_cols.items()}
                        new_bcs.append(bc_args)
                args["base_ciblages"] = new_bcs

            new[args[primary_key]] = args

        # --- 5 : Comparaison et MAJ
        res = _compare_items(existants, new, table, cols, primary_key, bc_cols=bc_cols if table == BaseAction else None)
        config.session.commit()

        await journey.send(f"> Table {tools.code(table.__name__)} remplie ! " + res.bilan)
        await tools.log(f"`/fillroles` > {table.__name__}:\n{res.log}")
        if table == BaseAction:
            sub_res = res.sub_results
            await journey.send(f"> Table {tools.code('BaseCiblage')} remplie simultanément " + sub_res.bilan)
            await tools.log(f"`/fillroles` > BaseCiblage:\n{sub_res.log}")

    # ==== Remplissage #rôles ===
    chan_roles = config.Channel.roles
    if not await journey.yes_no(f"Purger et re-remplir {chan_roles.mention} ?"):
        await journey.send(f"Fini (voir {config.Channel.logs.mention}).")
        return

    await journey.send(f"Vidage de {chan_roles.mention}...")
    async with journey.channel.typing():
        await chan_roles.purge(limit=1000)

    camps = Camp.query.filter_by(public=True).all()
    est = sum(len(camp.roles) + 2 for camp in camps) + 1
    await journey.send(f"Remplissage... (temps estimé : {est} secondes)")

    t0 = time.time()
    await chan_roles.send("Voici la liste des rôles (voir aussi `/roles`) :")
    async with journey.channel.typing():
        shortcuts = []
        for camp in camps:
            if not camp.roles:
                continue

            mess = await chan_roles.send(camp.nom, embed=camp.embed)
            shortcuts.append(mess)

            for role in camp.roles:
                if role.actif:
                    await chan_roles.send(embed=role.embed)

        for mess in shortcuts:
            await mess.reply("Accès rapide :             \N{UPWARDS BLACK ARROW}")

    rt = time.time() - t0
    await journey.send(f"{chan_roles.mention} rempli ! (en {rt:.4} secondes)")
