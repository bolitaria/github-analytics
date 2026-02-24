#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth.models import User, clickhouse_client

def init_users():
    # Crear tabla si no existe
    User.create_table()
    
    # Crear usuario admin si no existe
    admin = User.get_by_username('admin')
    if not admin:
        User.create('admin', 'admin123', role='admin')
        print("Usuario admin creado (admin/admin123)")
    else:
        print("Usuario admin ya existe")

if __name__ == '__main__':
    init_users()