#!/bin/bash
echo "Instalando dependencias..."
python3 -m pip install --break-system-packages -r requirements.txt

echo "Coletando arquivos estaticos..."
python3 manage.py collectstatic --noinput --clear
