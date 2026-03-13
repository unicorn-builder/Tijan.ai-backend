#!/usr/bin/env bash
# render_build.sh
# Exécuté par Render au build time (avant démarrage de l'app)
# Installe ODA File Converter pour conversion DWG → DXF

set -e

echo "==> Installation des dépendances Python..."
pip install -r requirements.txt

echo "==> Installation ODA File Converter..."

ODA_DEB="ODAFileConverter_QT5_lnxX64_8.3dll_24.8.deb"
ODA_URL="https://download.opendesign.com/guestfiles/ODAFileConverter/${ODA_DEB}"
ODA_PATH="/tmp/${ODA_DEB}"

# Télécharger ODA
if [ ! -f "/usr/bin/ODAFileConverter" ]; then
    echo "    Téléchargement ODA..."
    curl -L -o "${ODA_PATH}" "${ODA_URL}" --retry 3 --silent --show-error

    echo "    Installation du package..."
    dpkg -i "${ODA_PATH}" || apt-get install -f -y

    rm -f "${ODA_PATH}"
    echo "    ✓ ODA File Converter installé"
else
    echo "    ✓ ODA File Converter déjà présent"
fi

# Vérifier
if command -v ODAFileConverter &> /dev/null; then
    echo "    ✓ ODAFileConverter accessible"
else
    echo "    ⚠ ODAFileConverter non trouvé dans PATH — recherche..."
    find /usr -name "ODAFileConverter" 2>/dev/null | head -3
    find /opt -name "ODAFileConverter" 2>/dev/null | head -3
fi

echo "==> Build terminé."
