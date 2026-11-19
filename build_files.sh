#!/bin/bash
echo "Instalando dependencias..."
python3 -m pip install -r requirements.txt

echo "Coletando arquivos estaticos..."
python3 manage.py collectstatic --noinput --clear
