import os
from src.api.app import create_app

if __name__ == "__main__":
    app = create_app()
    # Modo debug controlado por variable de entorno (solo true en desarrollo)
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(
        debug=debug_mode,
        host="0.0.0.0",
        port=int(os.getenv("FLASK_PORT", "8001"))
    )