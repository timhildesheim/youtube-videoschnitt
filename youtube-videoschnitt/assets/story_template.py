"""Storyboard für <VIDEO-TITEL>. Alle Zeiten in QUELLZEIT (Sekunden im Original), S() rechnet um.

Wird von build.py geladen (das setzt auch den Pfad zu lib.py). Komponenten: references/components.md.
Positionen in CSS-px (1920×1080). Kamera-/Gesichtsbereich aus project.json → layout NIE überdecken.
Texte nach profil.schreibstil, Elemente nach profil.einblendungen. Vor dem Rendern: check_layout.py.
"""
from lib import *  # noqa: F401,F403  (S, q, comp, endcard, tb_window, COMPS, PR, CFG, Icons wie CHECK …)

comps = COMPS

# Häufige Positionen, an das Layout dieses Videos anpassen
L_TOP = {'left': 96, 'top': 170}     # Text links oben (Screen-Bereich, nicht über der Kamera)
R_TH = {'left': 1380, 'top': 240}    # rechts neben dem Kopf im Vollbild-Talking-Head (w ≤ 460)
L_TH = {'left': 70, 'top': 260}      # links neben dem Kopf (w=460, align='right')

NAME = PR.get('person.name') or ''
VOR, _, NACH = NAME.partition(' ')

# ── Intro (Vollbild-Talking-Head) ──
c = comp('th1', 0, 120.0, 'th')
tb = tb_window(S(6.6), 'Thema')                # Laufband-Fenster aus Wortlänge + 200 px/s (Push-ins dort weit halten)
c.th_pushins(wide_at=[tb])
c.textbehind('tb1', tb[0], None, '', 'Thema', y=140)
c.listcard('road', S(18.0), S(32.0), R_TH, 'In diesem Video', None,
           [(S(18.4), 'Schritt *eins*'), (S(22.4), 'Schritt zwei'), (S(28.0), 'Schritt drei')], w=460, isize=36)
c.tile('name', S(33.0), S(39.0), {'left': 110, 'top': 800}, PR.get('person.zusatz') or '',
       f'{VOR} *{NACH}*' if NACH else NAME, w=600, size=52)   # Namens-Bauchbinde
c.subscribe('abo1', S(80.0))                   # Abo-Störer an einer ruhigen Stelle (≈6 s, keine andere Einblendung)

# ── Screen-Teil ──
c = comp('s01', 120.0, 136.0)
c.chapter('ch1', S(120.1), S(126.0), 1, 'Kunden *finden*')

# … weitere Segmente …

# ── Outro + Endkarte ──
c = comp('th9', 1900.0, 'end', 'th')
c.th_pushins()
if PR.get('cta.aktiv'):
    c.outro_cta('oc', S(1915.0))
endcard()
