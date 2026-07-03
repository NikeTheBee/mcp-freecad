# ROADMAP — état vs cahier des charges & plan d'action

> Audit du 2026-07-03 contre `docs/CAHIER_DES_CHARGES.md` (v1.0).
> Ordre d'exécution retenu : **A → B → D → C** (valeur décroissante / dépendances).

## 1. Fait (conforme au CDC)

| Domaine | Réalisé | Réf CDC |
|---|---|---|
| Base MCP | blwfish/freecad-mcp installé, bridge `~/.freecad-mcp`, addon AICopilot | §6.2 |
| Couches maison | `server/freecad_layers/` — state / verify / checkpoint, testées | §7 |
| Skills | 10 skills (partdesign, rocket, drone, verify, print3d, fem, exchange, assembly, gear, robotics-ros) | §9 |
| Install | `install/bootstrap.py` idempotent multi-OS, grafts épinglés | §11 Phase 0 |
| Tests | `install/run_all_tests.py` 20/20 + CI (subset core) | §13 CI |
| Publication | Repo public GitHub, README, LICENSE MIT, CREDITS, SECURITY | §13, Phase 5 |
| Robustesse | Capture crash OCCT (base), audit compat R1–R10 | NF2, §6.2 |
| Token-minimal | CLAUDE.md court, texte-seul par défaut, outils nommés | §8 |
| Rocketry | Rocket WB + stabilité Barrowman (CP, marge statique) | §4.3 |
| Fabrication | STL gaté watertight, réparation mesh, STEP/IGES | §4.5 |
| Robotique (base) | Export URDF/xacro + package ROS2 ament_cmake via CROSS | §4.2 partiel |

## 2. Divergences assumées (CDC ↔ réalisé)

| # | Divergence | Justification | Statut doc |
|---|---|---|---|
| DV1 | `skill-cfd` / `skill-cam` absents, remplacés par `skill-exchange` / `skill-gear` | CAM exige FreeCAD 1.2-dev ; CFD exige OpenFOAM externe | à retranscrire dans le CDC (tâche D) |
| DV2 | CROSS greffé au lieu de RobotCAD | CROSS suffit pour URDF/xacro sans runtime ROS2 | à retranscrire (D) |
| DV3 | Licence MIT au lieu de LGPL/GPL anticipée | rien n'est vendorisé (base et grafts clonés à l'install) | à retranscrire (D) |
| DV4 | Décisions ouvertes §15 tranchées de facto : D1=Windows, D2=MIT, D3=non (pas d'image→3D), D4=privé (gitignoré), D5=CAM différé à 1.2 | — | à retranscrire (D) |

## 3. Points faibles / manquant

| # | Manque | Impact | Couvert par |
|---|---|---|---|
| PF1 | `spawn_freecad_instance` cassé sous Windows (socket Unix) → démarrage FreeCAD encore semi-manuel (R10) | entorse au « zéro-code » §1.3 | **Tâche A** |
| PF2 | Drone = géométrie seule ; aucun équivalent analytique de Barrowman (poussée/poids, hélices) | §4.3 asymétrique | **Tâche B** |
| PF3 | Pas de skill CFD, même pour le repli §12 (export → OpenFOAM externe) | l'IA n'a pas de guide aéro | **Tâche B** |
| PF4 | Mémoire projet jamais éprouvée en réel (`project_state/`, `checkpoints/` vides) ; critère §14.1 « reprise entre 2 sessions » sans démo | crédibilité du critère | **Tâche D** |
| PF5 | CDC figé en v1.0, divergences non retranscrites | doc trompeuse pour un tiers | **Tâche D** |
| PF6 | Pas de skill-cam (même stub documentant la limite 1.2-dev) | trou §9 | **Tâche D** |
| PF7 | URDF exporté sans `ros2_control`, capteurs, ni tags Gazebo ; pas de cinématique | §4.2 partiel | **Tâche C** |
| PF8 | Portabilité NF6 revendiquée mais testée uniquement sous Windows | risque à l'adoption | hors périmètre (nécessite machines Linux/macOS) |
| PF9 | CFD interne (CfdOF) et CAM/G-code absents | assumé §12 / attendre 1.2 | hors périmètre |

## 4. Plan d'action détaillé (ordre optimal)

### A — Auto-démarrage FreeCAD par le bridge (fix R10) — PRIORITÉ 1
- Quand `:23456` ne répond pas, le bridge lance lui-même
  `freecadcmd.exe <Mod>/AICopilot/headless_server.py` en arrière-plan (Windows : TCP, pas de socket Unix),
  puis attend l'ouverture du port (timeout ~90 s).
- Résolution du binaire : `FREECAD_MCP_FREECAD_BIN` → PATH → chemins connus (même logique que bootstrap).
- Le patch vit dans le repo (`install/patches/` ou couche projet) et est réappliqué par `bootstrap.py`
  (la base `server/freecad-mcp` est gitignorée → un patch hors repo serait perdu).
- Test : arrêt de FreeCAD, appel outil → démarrage auto + réponse.

### B — skill-cfd (repli) + aéro analytique drone — PRIORITÉ 2
- `skills/skill-cfd/SKILL.md` : workflow §12 — préparer la géométrie (watertight), exporter STL/STEP,
  gabarit de cas OpenFOAM externe, limites honnêtes (pas de CFD interne sans CfdOF+OpenFOAM).
- `server/freecad_layers/aero.py` : hover thrust, rapport poussée/poids, disque hélice / charge alaire,
  autonomie estimée — verdicts texte courts (mêmes conventions que `verify`).
- MàJ `skills/skill-drone/SKILL.md` pour pointer sur ces helpers ; test dédié dans la suite.

### D — Démo mémoire + MàJ CDC + stub skill-cam — PRIORITÉ 3
- `examples/` : scénario reprise-entre-sessions rejouable (session 1 : pièce + state ; session 2 :
  reprise sans re-description) prouvant §14.1.
- CDC : encart « décisions tranchées » (DV1–DV4) + renvoi vers ce ROADMAP.
- `skills/skill-cam/SKILL.md` : stub honnête — état 1.1.x, quoi faire aujourd'hui (STL/STEP),
  bascule prévue à la sortie de 1.2.

### C — Robotique §4.2 : ros2_control / capteurs / Gazebo — PRIORITÉ 4
- Helpers d'augmentation d'URDF : injection `<ros2_control>`, capteurs (IMU, caméra, lidar) et
  plugins Gazebo dans l'URDF exporté par CROSS.
- MàJ `skills/skill-robotics-ros/SKILL.md` (invocations exactes) + test.

### Clôture
- `python install/run_all_tests.py` complet, commits atomiques par tâche, push origin.

## 5. Hors périmètre (rappel §12)
- CFD interne sérieux (OpenFOAM/CfdOF), CAM/G-code (FreeCAD 1.2-dev), simulation Gazebo live
  (runtime ROS2), génération image→3D (GPU), tests Linux/macOS.
