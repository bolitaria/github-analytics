"""
Configuración global de pytest
"""
import pytest
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configuración del entorno de testing"""
    # Configurar variables de entorno para testing
    os.environ['TESTING'] = 'True'
    os.environ['CLICKHOUSE_HOST'] = 'localhost'
    os.environ['CLICKHOUSE_PORT'] = '9001'
    
    yield
    
    # Cleanup
    if 'TESTING' in os.environ:
        del os.environ['TESTING']