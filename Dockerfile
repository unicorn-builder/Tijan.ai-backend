FROM python:3.11-slim

# System dependencies for ODA + ReportLab
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libgl1 libglib2.0-0 libxkbcommon0 libfontconfig1 \
    libxcb-xinerama0 libxcb-cursor0 libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

# ODA File Converter (DWG↔DXF, free headless)
RUN curl -sL "https://dl.opendesign.com/guestfiles/Demo/ODAFileConverter_QT6_lnxX64_8.3dll_25.12.deb" -o /tmp/oda.deb \
    && dpkg -i /tmp/oda.deb || apt-get install -f -y --no-install-recommends \
    && rm -f /tmp/oda.deb \
    && echo "ODA installed: $(which ODAFileConverter 2>/dev/null || echo 'not found')"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
