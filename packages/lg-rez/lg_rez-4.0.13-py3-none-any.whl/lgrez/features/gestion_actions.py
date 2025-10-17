"""lg-rez / features / Gestion des actions

Liste, création, suppression, ouverture, fermeture d'actions

"""

import datetime
from typing import Literal

from lgrez import config, commons
from lgrez.blocs import tools
from lgrez.bdd import Action, BaseAction, Tache, Utilisation, ActionTrigger, Joueur


def add_action(
    joueur: Joueur, base: BaseAction, cooldown: int = 0, charges: int | None = None, active: bool = True
) -> Action:
    """Enregistre une action et programme son ouverture le cas échéant.

    Si une action existe déjà pour ce joueur et cette base, la modifie ; sinon, en crée une nouvelle.

    Args:
        joueur, base, cooldown, charges, active: Paramètres de l'action.
    """
    action = Action.query.filter_by(joueur=joueur, base=base).first()
    if action:
        action.cooldown = cooldown
        action.charges = charges
        action.active = active
        action.update()
    else:
        action = Action(joueur=joueur, base=base, cooldown=cooldown, charges=charges, active=active)
        action.add()

    # Ajout tâche ouverture
    if action.base.trigger_debut == ActionTrigger.temporel:
        # Temporel : on programme
        Tache(
            timestamp=tools.next_occurrence(action.base.heure_debut),
            commande="open action",
            parameters={"id": action.id},
            action=action,
        ).add()

    elif action.base.trigger_debut == ActionTrigger.perma:
        # Perma : ON LANCE DIRECT (sera repoussé si jeu fermé)
        Tache(
            timestamp=datetime.datetime.now(), commande="open action", parameters={"id": action.id}, action=action
        ).add()

    return action


def delete_action(action: Action) -> None:
    """Archive une action et annule les tâches en cours liées.

    Depuis la version 2.1, l'action n'est plus supprimée mais est passée à :attr:`~.bdd.Action.active` = ``False``.

    Args:
        action: L'action à supprimer.
    """
    # Suppression tâches liées à l'action
    if action.taches:
        Tache.delete(*action.taches)

    if action.is_open:
        action.utilisation_ouverte.close()

    action.active = False
    action.update()
    # action.delete()


async def open_action(action: Action) -> None:
    """Ouvre l'action.

    Args:
        action: L'action à ouvrir.

    Opérations réalisées :
        - Vérification des conditions (cooldown, charges...) et reprogrammation si nécessaire ;
        - Gestion des tâches planifiées (planifie remind/close si applicable) ;
        - Information du joueur.
    """
    joueur = action.joueur
    chan = joueur.private_chan

    # Vérification base
    if not action.base:
        await tools.log(f"{action} : pas de base, exit")
        return

    # Vérification active
    if not action.active:
        await tools.log(f"{action} : inactive, exit (pas de reprogrammation)")
        return

    # Vérification cooldown
    if action.cooldown > 0:  # Action en cooldown
        action.cooldown = action.cooldown - 1
        config.session.commit()
        await tools.log(f"{action} : en cooldown, exit (reprogrammation si temporel).")
        if action.base.trigger_debut == ActionTrigger.temporel:
            # Programmation action du lendemain
            ts = tools.next_occurrence(action.base.heure_debut)
            Tache(timestamp=ts, commande="open action", parameters={"id": action.id}, action=action).add()
        return

    # Vérification role_actif
    if not joueur.role_actif:
        # role_actif == False : on reprogramme la tâche au lendemain tanpis
        await tools.log(f"{action} : role_actif == False, exit (reprogrammation si temporel).")
        if action.base.trigger_debut == ActionTrigger.temporel:
            ts = tools.next_occurrence(action.base.heure_debut)
            Tache(timestamp=ts, commande="open action", parameters={"id": action.id}, action=action).add()
        return

    # Vérification charges
    if action.charges == 0:
        # Plus de charges, mais action maintenue en base car refill / ...
        await tools.log(f"{action} : plus de charges, exit (reprogrammation si temporel).")
        return

    # Action "automatiques" (passives : notaire...) :
    # lance la procédure de clôture / résolution
    if action.base.trigger_fin == ActionTrigger.auto:
        if action.base.trigger_debut == ActionTrigger.temporel:
            await tools.log(
                f"Action {action.base.slug} pour {joueur.nom} pas vraiment automatique, {config.Role.mj.mention} "
                f"VENEZ M'AIDER JE PANIQUE 😱 (comme je suis vraiment sympa je vous file son chan, {chan.mention})"
            )
        else:
            await tools.log(f"{action} : automatique, appel processus de clôture")

        await close_action(action)
        return

    # Tous tests préliminaires n'ont pas return ==> Vraie action à lancer

    # Calcul heure de fin (si applicable)
    heure_fin = None
    if action.base.trigger_fin == ActionTrigger.temporel:
        heure_fin = action.base.heure_fin
        ts = tools.next_occurrence(heure_fin)
    elif action.base.trigger_fin == ActionTrigger.delta:
        # Si delta, on calcule la vraie heure de fin (pas modifié en base)
        delta = action.base.heure_fin
        ts = datetime.datetime.now() + datetime.timedelta(hours=delta.hour, minutes=delta.minute, seconds=delta.second)
        heure_fin = ts.time()

    # Programmation remind / close
    if action.base.trigger_fin in [ActionTrigger.temporel, ActionTrigger.delta]:
        remind_ts = ts - datetime.timedelta(minutes=30)
        Tache(timestamp=remind_ts, commande="remind action", parameters={"id": action.id}, action=action).add()
        Tache(timestamp=ts, commande="close action", parameters={"id": action.id}, action=action).add()
    elif action.base.trigger_fin == ActionTrigger.perma:
        # Action permanente : fermer pour le WE
        # ou rappel / réinitialisation chaque jour
        ts_matin = tools.next_occurrence(datetime.time(hour=7))
        ts_pause = tools.debut_pause()
        if ts_matin < ts_pause:
            # Réopen le lendamain
            Tache(timestamp=ts_matin, commande="open action", parameters={"id": action.id}, action=action).add()
        else:
            # Sauf si pause d'ici là
            Tache(timestamp=ts_pause, commande="close action", parameters={"id": action.id}, action=action).add()

    # Information du joueur
    if action.is_open:  # déjà ouverte
        await chan.send(
            f"{tools.montre()}  Rappel : tu peux utiliser quand tu le souhaites "
            f"ton action {tools.code(action.base.slug)} !  {config.Emoji.action}\n"
            + (f"Tu as jusqu'à {heure_fin} pour le faire. \n" if heure_fin else "")
            + tools.ital(f"Utilise `/action` pour agir.")
        )
    else:
        # on ouvre !
        util = Utilisation(action=action)
        util.add()
        util.open()
        await chan.send(
            f"{tools.montre()}  Tu peux maintenant utiliser ton action "
            f"{tools.code(action.base.slug)} !  {config.Emoji.action}\n"
            + (f"Tu as jusqu'à {heure_fin} pour le faire. \n" if heure_fin else "")
            + tools.ital(f"Utilise `/action` pour agir.")
        )

    config.session.commit()


async def close_action(action: Action) -> None:
    """Ferme l'action.

    Args:
        action: L'action à enregistrer.

    Opérations réalisées :
        - Archivage si nécessaire ;
        - Gestion des tâches planifiées (planifie prochaine ouverture si applicable) ;
        - Information du joueur (si charge-- seulement).
    """
    joueur = action.joueur
    chan = joueur.private_chan

    # Vérification base
    if not action.base:
        await tools.log(f"{action} : pas de base, exit")
        return

    # Vérification active
    if not action.active:
        await tools.log(f"{action} : inactive, exit")
        return

    # Vérification ouverte
    if not action.is_open:
        await tools.log(f"{action} : pas ouverte, exit")
        return

    deleted = False
    if not action.is_waiting:  # décision prise
        # Résolution de l'action
        # (pour l'instant juste charge -= 1 et suppression le cas échéant)
        if action.charges:
            action.charges = action.charges - 1
            pcs = " pour cette semaine" if "weekends" in action.base.refill else ""
            await chan.send(f"Il te reste {action.charges} charge(s){pcs}.")

            if action.charges == 0 and not action.base.refill:
                delete_action(action)
                deleted = True

    if not deleted:
        # Si l'action a été faite et a un cooldown, on le met
        if (not action.is_waiting) and (action.base.base_cooldown > 0):
            action.cooldown = action.base.base_cooldown

        action.utilisation_ouverte.close()

        # Programmation prochaine ouverture
        if action.base.trigger_debut == ActionTrigger.temporel:
            ts = tools.next_occurrence(action.base.heure_debut)
            Tache(timestamp=ts, commande="open action", parameters={"id": action.id}, action=action).add()
        elif action.base.trigger_debut == ActionTrigger.perma:
            # Action permanente : ouvrir après le WE
            ts = tools.fin_pause()
            Tache(timestamp=ts, commande="open action", parameters={"id": action.id}, action=action).add()

    config.session.commit()


def get_actions(
    quoi: Literal["open", "close", "remind"], trigger: ActionTrigger, heure: datetime.time | None = None
) -> list[Action]:
    """Renvoie les actions répondant à un déclencheur donné.

    Args:
        quoi: Type d'opération en cours :

          - ``"open"`` : ouverture, :attr:`Action.is_open` doit être faux;
          - ``"close"`` :  fermeture, :attr:`Action.is_open` doit être vrai;
          - ``"remind"`` : rappel, :attr:`Action.is_waiting` doit être vrai.

        trigger: valeur de ``Action.trigger_debut/fin`` à détecter.
        heure: si ``trigger == "temporel"``, ajoute la condition ``Action.heure_debut/fin == heure``.

    Returns:
        La liste des actions correspondantes.
    """
    filter = Action.active.is_(True).join(Action.base)

    if quoi == "open":
        filter &= (BaseAction.trigger_debut == trigger) & ~Action.is_open
    elif quoi == "close":
        filter &= (BaseAction.trigger_fin == trigger) & Action.is_open
    elif quoi == "remind":
        filter &= (BaseAction.trigger_fin == trigger) & Action.is_waiting
    else:
        raise commons.UserInputError("quoi", f"bad value: '{quoi}'")

    if trigger == ActionTrigger.temporel:
        if not heure:
            raise commons.UserInputError("quand", "merci de préciser une heure")

        if quoi == "open":
            filter &= BaseAction.heure_debut == heure
        else:  # close / remind
            filter &= BaseAction.heure_fin == heure

    return Action.query.filter(filter).all()
