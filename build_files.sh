#!/bin/bash
echo "Instalando dependencias..."
python3.10 -m pip install -r requirements.txt

echo "Coletando arquivos estaticos..."
python3.10 manage.py collectstatic --noinput --clear
