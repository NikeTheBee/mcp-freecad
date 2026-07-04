# MCP FREECAD 🇫🇷

[![Tests](https://github.com/NikeTheBee/mcp-freecad/actions/workflows/tests.yml/badge.svg)](https://github.com/NikeTheBee/mcp-freecad/actions/workflows/tests.yml)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](LICENSE)
🇬🇧 [English version](README.md)

Concevez des projets **mécaniques, aéro et robotiques** dans **FreeCAD** en **langage naturel** —
zéro code à écrire — via n'importe quel client IA parlant **MCP**. Pensé pour un coût de tokens
minimal et des sessions de conception longues et robustes.

> Décrivez l'intention (« un châssis de quad 450 mm avec bras repliables », « une fusée 3 ailerons
> avec nez ogival ») ; l'IA modélise, vérifie la géométrie, sauvegarde des points de reprise, et
> prépare la fabrication.

## Objectif du projet : l'IA locale d'abord
Le but final est la **CAO pilotée par des modèles d'IA LOCAUX** — tout tourne sur votre machine,
sans dépendance au cloud. C'est pourquoi l'architecture repose sur **MCP**, un protocole ouvert :
n'importe quel agent MCP avec un LLM local peut la piloter, aujourd'hui ou demain. Les modèles
frontier (ex. Claude Code) sont pour l'instant en avance sur les longs enchaînements d'outils,
donc ils servent de client de référence **en attendant** — mais rien n'y est verrouillé. Quand le
local rattrapera, on change le client et on garde toute la pile (serveur, skills, couches).

## Installation (une commande)
```
git clone https://github.com/NikeTheBee/mcp-freecad "MCP FREECAD" && cd "MCP FREECAD"
python install/bootstrap.py --with-grafts
```
Prérequis : **FreeCAD 1.1.x**, **Python 3.10+**, **git**, un client MCP (ex. Claude Code).
`bootstrap.py` détecte FreeCAD, installe le serveur + le workbench + le bridge, applique les
correctifs maison (démarrage auto de FreeCAD, authentification du socket), enregistre le serveur
MCP et lance les tests. Idempotent : relançable sans risque.

## Vérifier
```
python install/run_all_tests.py
```
La suite couvre : greffes métier (fusée/drone/robotique), noyau PartDesign, couches maison
(mémoire projet, vérification géométrique, checkpoints), export STL/STEP, FEM, engrenages,
assemblages, **auto-démarrage** et **authentification du socket**, et une boucle MCP de bout en
bout. FreeCAD est démarré automatiquement si besoin.

## Exemple
> « Crée une boîte de 10×20×30 mm. »

L'IA appelle les outils `freecad`, FreeCAD construit la boîte paramétrique en headless, et l'IA
répond avec le volume / la boîte englobante en texte — pas de capture d'écran sur le chemin
nominal (économie de tokens).

## Capacités
Modélisation paramétrique (sketch, Pad/Pocket, variantes par feuille de calcul) · fusée (CP et
stabilité Barrowman) · drone (profils NACA + dimensionnement analytique : poussée/poids, puissance
de vol stationnaire, autonomie) · robotique (URDF/xacro + package ROS2, tags ros2_control/capteurs/
Gazebo) · fabrication (STL vérifié étanche, STEP/IGES, réparation de maillage) · FEM (CalculiX) ·
assemblages & engrenages · mémoire de projet entre sessions · checkpoints/rollback ·
sécurité (RPC localhost + jeton partagé, scan de secrets — voir [SECURITY.md](SECURITY.md)).

La connaissance métier vit dans [`skills/`](skills) (10+ skills chargés à la demande).
Spécification complète : [`docs/CAHIER_DES_CHARGES.md`](docs/CAHIER_DES_CHARGES.md) ·
Audit & plan : [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Licence
[CC BY-NC 4.0](LICENSE) © 2026 NikeTheBee — chacun est libre de **télécharger, modifier et
partager**, à deux conditions : **citation obligatoire** (créditer NikeTheBee ET les projets tiers
de [`CREDITS.md`](CREDITS.md)), et **pas d'usage commercial** sans autorisation écrite préalable.
Résumé lisible : [`NOTICE`](NOTICE). FreeCAD et les workbenches greffés gardent leurs propres
licences (LGPL-2.1, non vendorisés ici).
