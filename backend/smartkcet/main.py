"""Flask application factory."""

import warnings
from pathlib import Path
import os
import sys

os.environ["PYTHONUNBUFFERED"] = "1"

import nest_asyncio
from flask import Flask, jsonify, request, send_from_directory, redirect, Blueprint
from flask_cors import CORS
from fastapi.exceptions import HTTPException as FastAPIHTTPException

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
nest_asyncio.apply()

from .config import validate_startup_config  # noqa: E402
STARTUP_CONFIG = validate_startup_config()

try:
    if sys.version_info >= (3, 14):
        import logging as _logging
        _logging.getLogger("smartkcet.main").info(
            "Python 3.14 detected: skipping Groq validation"
        )
    else:
        from .rag.groq_client import validate_groq_api_key, reset_groq_client
        reset_groq_client()
        validate_groq_api_key()
except Exception as _groq_err:
    import logging as _logging
    _logging.getLogger("smartkcet.main").warning(
        "Groq API key validation failed at startup: %s.",
        _groq_err,
    )

class SmartKcetFlask(Flask):
    """Custom Flask subclass that auto-serializes Pydantic models into JSON-compatible dictionaries."""

    def make_response(self, rv):
        from pydantic import BaseModel

        def _serialize_val(val):
            if isinstance(val, BaseModel):
                return val.model_dump(mode="json") if hasattr(val, "model_dump") else val.dict()
            if isinstance(val, list) and val and isinstance(val[0], BaseModel):
                return [_serialize_val(x) for x in val]
            return val

        if isinstance(rv, tuple):
            val = _serialize_val(rv[0])
            rv = (val, *rv[1:])
        else:
            rv = _serialize_val(rv)
        return super().make_response(rv)


def create_app():
    frontend_dist = Path(__file__).resolve().parents[2] / 'frontend-react' / 'dist'
    app = SmartKcetFlask(
        __name__,
        static_folder=str(frontend_dist / 'assets'),
        static_url_path='/assets'
    )
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1 GB for large textbook uploads

    from .db.session import SessionLocal
    from flask import g

    @app.before_request
    def set_db_session():
        g.db = SessionLocal()

    @app.teardown_request
    def close_db_session(exception=None):
        db = getattr(g, 'db', None)
        if db is not None:
            db.close()
    from .admin import router as admin_api_router  # noqa: E402
    from .auth import router as auth_router  # noqa: E402
    from .contact import router as contact_router  # noqa: E402
    from .institution import router as institution_router  # noqa: E402
    from .payments import router as payments_router  # noqa: E402
    from .routes.legacy import router as legacy_router  # noqa: E402
    from .routes.pages import router as pages_router  # noqa: E402
    from .student import router as student_api_router  # noqa: E402
    from .subscription import router as subscription_router  # noqa: E402
    from .student.exam_access import router as exam_access_router  # noqa: E402

    # Register blueprints
    app.register_blueprint(auth_router, url_prefix='/api/auth')
    app.register_blueprint(contact_router)
    app.register_blueprint(subscription_router, url_prefix='/api/subscription')

    print('\n========================================')
    print('VYASAPREP PLATFORM CREDENTIALS:')
    print('Admin Login: admin@vyasaprep.com / admin (or admin@mre.com / admin)')
    print('Institution: Authenticates via registered institution accounts')
    print('========================================\n')
    app.register_blueprint(institution_router, url_prefix='/api/institution')
    app.register_blueprint(admin_api_router, url_prefix='/api/admin')
    app.register_blueprint(student_api_router, url_prefix='/api/student')
    app.register_blueprint(payments_router, url_prefix='/api/payments')
    app.register_blueprint(exam_access_router)
    app.register_blueprint(pages_router)
    app.register_blueprint(legacy_router)

    from .admin.syllabus import list_syllabus_public, get_syllabus_by_subject
    app.add_url_rule("/api/syllabus", "public_syllabus", list_syllabus_public, methods=["GET"])
    app.add_url_rule("/api/syllabus/<subject>", "public_syllabus_subject", get_syllabus_by_subject, methods=["GET"])

    @app.route("/api/health", methods=["GET"])
    def api_health():
        return jsonify({"status": "ok"})

    @app.route("/", defaults={"filepath": ""})
    @app.route("/<path:filepath>")
    def serve_react(filepath):
        if filepath.startswith("api/"):
            return jsonify({"detail": "Not Found"}), 404

        frontend_path = frontend_dist / filepath
        if filepath and frontend_path.is_file():
            return send_from_directory(frontend_dist, filepath)

        return send_from_directory(frontend_dist, "index.html")

    @app.after_request
    def add_cache_control(response):
        path = request.path
        if path.startswith("/api/") or path.endswith(".html") or path.endswith(".js") or path.startswith("/html/") or path.startswith("/js/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    @app.errorhandler(404)
    def custom_http_exception_handler(error):
        path = request.path
        is_api = path.startswith("/api/")
        is_static = path.startswith("/css/") or path.startswith("/js/")
        accept = request.headers.get("accept", "")
        wants_html = "text/html" in accept

        if not is_api and not is_static and wants_html and path != "/not-found":
            from urllib.parse import quote
            return redirect(f"/not-found?path={quote(path)}", code=302)
        
        return jsonify({"detail": "Not Found"}), 404

    @app.errorhandler(FastAPIHTTPException)
    def fastapi_http_exception_handler(error):
        detail = error.detail
        if isinstance(detail, dict):
            response = {"detail": detail}
        else:
            response = {"detail": {"message": str(detail)}}
        return jsonify(response), error.status_code

    @app.route("/css/<path:filepath>")
    def serve_css(filepath):
        return send_from_directory(os.path.join(app.static_folder, 'css'), filepath)

    @app.route("/js/<path:filepath>")
    def serve_js(filepath):
        return send_from_directory(os.path.join(app.static_folder, 'js'), filepath)

    @app.route("/html/<path:filepath>")
    def serve_html(filepath):
        return send_from_directory(os.path.join(app.static_folder, 'html'), filepath)

    return app

app = create_app()

__all__ = ["create_app", "STARTUP_CONFIG", "app"]
