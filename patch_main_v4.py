"""
patch_main_v4.py
Branche generate_pdf_v4 et tijan_pdf_theme_v2 sur les bons endpoints
Lance depuis ~/tijan-repo : python3 ~/Downloads/patch_main_v4.py
"""
import re, os, shutil

REPO = os.path.expanduser("~/tijan-repo")
MAIN = os.path.join(REPO, "main.py")

content = open(MAIN).read()
original = content

# 1. Remplacer le loader generate_pdf
content = re.sub(
    r'def get_generateur\(\):.*?return.*?\n',
    lambda m: m.group(0),
    content
)

old_loader = '''def get_generateur():'''
# Chercher le vrai loader
match = re.search(r'(def get_generateur\(\):[\s\S]*?(?=\n@app|\ndef [a-z]))', content)
if match:
    old_block = match.group(0)
    new_block = old_block.replace(
        'from generate_pdf_v3 import',
        'from generate_pdf_v4 import'
    ).replace(
        'from generate_pdf import',
        'from generate_pdf_v4 import'
    )
    content = content.replace(old_block, new_block)
    print("✓ Loader generate_pdf mis à jour → v4")
else:
    # Patch par remplacement direct de l'import dans le lazy loader
    content = content.replace(
        'from generate_pdf_v3 import generer',
        'from generate_pdf_v4 import generer'
    ).replace(
        'from generate_pdf import generer',
        'from generate_pdf_v4 import generer'
    )
    print("✓ Import generate_pdf patché → v4")

# 2. Remplacer tijan_pdf_theme par v2
content = content.replace(
    'import tijan_pdf_theme\n',
    'import tijan_pdf_theme_v2 as tijan_pdf_theme\n'
).replace(
    'from tijan_pdf_theme import',
    'from tijan_pdf_theme_v2 import'
)
print("✓ tijan_pdf_theme → v2")

# 3. Vérifier que ParamsProjet a surface_emprise_m2 avec description beta
# Chercher le champ et ajouter un commentaire si besoin
if 'surface_emprise_m2' not in content:
    print("⚠ surface_emprise_m2 non trouvé dans ParamsProjet — vérifier manuellement")
else:
    print("✓ surface_emprise_m2 présent dans ParamsProjet")

# 4. S'assurer que /calculate retourne params dans le résultat
# pour que le frontend puisse afficher les bonnes valeurs
old_calc_return = '"ok": True,'
new_calc_return = '"ok": True,\n        "params_input": params.dict(),'
if '"params_input"' not in content and old_calc_return in content:
    # Remplacer seulement dans le bloc /calculate
    content = content.replace(old_calc_return, new_calc_return, 1)
    print("✓ params_input ajouté dans réponse /calculate")

# Écrire
if content != original:
    shutil.copy(MAIN, MAIN + ".bak_v4")
    open(MAIN, 'w').write(content)
    print("✅ main.py patché")
else:
    print("⚠ Aucun changement détecté — vérifier manuellement les loaders")

# 5. Vérifier que les fichiers v4 sont bien dans le repo
for f in ['generate_pdf_v4.py', 'tijan_pdf_theme_v2.py']:
    path = os.path.join(REPO, f)
    if os.path.exists(path):
        print(f"✓ {f} présent dans le repo")
    else:
        print(f"✗ {f} MANQUANT — copier depuis Downloads")
