"""Flask application factory.

Creates and configures the Flask application instance, registers all Flask
blueprints, registers database teardown handlers, sets up static asset serving,
and seeds initial database state.
"""

from __future__ import annotations

import logging
import os
import sys
import warnings
from decimal import Decimal
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_file, send_from_directory
from flask_cors import CORS
from sqlalchemy import func, text

from .config import validate_startup_config
from .db.session import SessionLocal, teardown_db

# Suppress noise
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

logger = logging.getLogger("smartkcet.main")

STARTUP_CONFIG = validate_startup_config()


def create_app() -> Flask:
    _project_root = Path(__file__).resolve().parent.parent.parent
    _frontend_dir = _project_root / "frontend"

    app = Flask(__name__, static_folder=None)
    CORS(app)

    # Database Session Teardown
    app.teardown_appcontext(teardown_db)

    # Import Blueprints
    from .admin import public_syllabus_router as syllabus_public_router
    from .admin import router as admin_api_router, sub_blueprints as admin_sub_blueprints
    from .auth import router as auth_router
    from .contact import router as contact_router
    from .institution import router as institution_router
    from .institution.content import router as institution_content_router
    from .payments import router as payments_router
    from .routes.legacy import router as legacy_router
    from .routes.pages import router as pages_router
    from .student import router as student_api_router, sub_blueprints as student_sub_blueprints
    from .student.exam_access import router as exam_access_router
    from .subscription import router as subscription_router

    # Register Blueprints
    app.register_blueprint(auth_router)
    app.register_blueprint(contact_router)
    app.register_blueprint(subscription_router)
    app.register_blueprint(payments_router)
    app.register_blueprint(institution_router)
    app.register_blueprint(institution_content_router)
    app.register_blueprint(exam_access_router)
    app.register_blueprint(syllabus_public_router)

    app.register_blueprint(student_api_router)
    for bp in student_sub_blueprints:
        app.register_blueprint(bp)

    app.register_blueprint(admin_api_router)
    for bp in admin_sub_blueprints:
        app.register_blueprint(bp)

    app.register_blueprint(pages_router)
    app.register_blueprint(legacy_router)

    # Public health check
    @app.route("/api/health", methods=["GET"])
    def api_health():
        return jsonify({"status": "ok"}), 200

    # Static File Routes
    @app.route("/css/<path:filename>", methods=["GET"])
    def serve_css(filename: str):
        file_path = _frontend_dir / "css" / filename
        if file_path.exists() and file_path.is_file():
            return send_from_directory(_frontend_dir / "css", filename, mimetype="text/css")
        return jsonify({"error": "not_found"}), 404

    @app.route("/js/<path:filename>", methods=["GET"])
    def serve_js(filename: str):
        file_path = _frontend_dir / "js" / filename
        if file_path.exists() and file_path.is_file():
            return send_from_directory(_frontend_dir / "js", filename, mimetype="text/javascript")
        return jsonify({"error": "not_found"}), 404

    @app.route("/html/<path:filename>", methods=["GET"])
    def serve_html(filename: str):
        file_path = _frontend_dir / "html" / filename
        if file_path.exists() and file_path.is_file():
            return send_from_directory(_frontend_dir / "html", filename, mimetype="text/html")
        return jsonify({"error": "not_found"}), 404

    # No-cache Headers Middleware
    @app.after_request
    def add_no_cache_headers(response):
        path = request.path or ""
        if path.startswith("/api/") or path.endswith(".html") or path.endswith(".js") or path.startswith("/html/") or path.startswith("/js/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    # 404 Handler for HTML navigation
    @app.errorhandler(404)
    def page_not_found(e):
        path = request.path or ""
        is_api = path.startswith("/api/")
        is_static = path.startswith("/css/") or path.startswith("/js/")
        accept = request.headers.get("accept", "")
        wants_html = "text/html" in accept

        if not is_api and not is_static and wants_html and path != "/not-found":
            from urllib.parse import quote
            return redirect(f"/not-found?path={quote(path)}", code=302)

        return jsonify({"error": "not_found", "message": "The requested URL was not found on the server."}), 404

    # Run Database Seeding & Self-Healing
    _run_startup_seeding()

    return app


def _run_startup_seeding():
    from .db.seed import seed_admin, seed_subscription_plans
    from .db.seed_students import (
        create_institution_subscriptions,
        create_trial_subscriptions,
        seed_test_direct_subscribers,
        seed_test_institution_students,
        seed_test_institutions,
    )
    from .db.syllabus_seed import seed_syllabus
    from .db.subscription_models import Institution, SubscriptionPlan

    db = SessionLocal()

    try:
        db.execute(text("ALTER TABLE syllabus_topics ADD COLUMN textbook_filename VARCHAR(255)"))
        db.execute(text("ALTER TABLE syllabus_topics ADD COLUMN textbook_path VARCHAR(255)"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE questions ADD COLUMN source_type VARCHAR(20) NOT NULL DEFAULT 'question_paper'"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        seed_admin()
    except Exception as e:
        logger.warning("Admin seed failed (non-fatal): %s", e)

    try:
        seed_syllabus(db)
    except Exception as e:
        logger.warning("Syllabus seed failed (non-fatal): %s", e)

    try:
        seed_subscription_plans()
    except Exception as e:
        logger.warning("Subscription plans seed failed (non-fatal): %s", e)

    try:
        existing_count = db.query(func.count(Institution.id)).scalar()
        if existing_count == 0:
            institutions = seed_test_institutions(db, count=3)
            direct_students = seed_test_direct_subscribers(db, count=5)
            institution_students = seed_test_institution_students(db, institutions, count_per_institution=5)
            create_trial_subscriptions(db, direct_students)
            create_institution_subscriptions(db, institutions)
    except Exception as e:
        logger.warning("Test data seed failed (non-fatal): %s", e)

    try:
        wrong_prices = {
            Decimal("9.99"): Decimal("349.00"),
            Decimal("99.99"): Decimal("2999.00"),
        }
        for wrong_price, correct_price in wrong_prices.items():
            wrong_plans = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.price == wrong_price,
                SubscriptionPlan.plan_type == "individual"
            ).all()
            if wrong_plans:
                for plan in wrong_plans:
                    plan.price = correct_price
                    db.add(plan)
                db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("Pricing safety check failed (non-fatal): %s", e)

    db.close()


app = create_app()

__all__ = ["app", "create_app", "STARTUP_CONFIG"]
