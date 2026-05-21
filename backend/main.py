
import sys
from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from src.application.services import OutfitCatalogService, ScreenshotService 
from src.infrastructure.file_repository import FileRepository 
from src.presentation.routes import create_api_blueprint, register_static_routes


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(ROOT / "frontend"),
        static_url_path="",
    )
    CORS(app)

    repository = FileRepository(ROOT)
    outfit_service = OutfitCatalogService(repository)
    screenshot_service = ScreenshotService(repository)

    app.register_blueprint(
        create_api_blueprint(outfit_service, screenshot_service, repository)
    )
    register_static_routes(app, ROOT)

    frontend = ROOT / "frontend"

    @app.route("/")
    def index():
        return send_from_directory(frontend, "index.html")

    @app.route("/<path:path>")
    def frontend_files(path):
        target = frontend / path
        if target.is_file():
            return send_from_directory(frontend, path)
        return send_from_directory(frontend, "index.html")

    return app


if __name__ == "__main__":
    application = create_app()
    print("AI Outfit Try-On running at http://localhost:5000")
    application.run(host="0.0.0.0", port=5000, debug=True)
