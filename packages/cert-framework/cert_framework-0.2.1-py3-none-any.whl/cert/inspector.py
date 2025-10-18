"""
CERT Framework Inspector

Lightweight Flask-based web UI for visualizing test results.
"""

from flask import Flask, render_template, jsonify, request
from typing import List, Dict, Any
import os


# In-memory storage for demo (replace with SQLite for production)
test_results: List[Dict[str, Any]] = []


def create_app():
    """Create Flask app instance"""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    @app.route("/")
    def index():
        """Main inspector UI"""
        return render_template("inspector.html")

    @app.route("/api/results", methods=["GET"])
    def get_results():
        """Get all test results"""
        return jsonify(test_results)

    @app.route("/api/results", methods=["POST"])
    def add_result():
        """Add a test result"""
        result = request.json
        test_results.append(result)
        return jsonify({"status": "success", "id": len(test_results) - 1})

    @app.route("/api/test", methods=["POST"])
    def run_test():
        """Execute a test"""
        _config = request.json  # TODO: Execute actual test based on config
        return jsonify({"status": "running", "id": "test-123"})

    @app.route("/health")
    def health():
        """Health check endpoint"""
        return jsonify({"status": "healthy", "version": "1.0.0"})

    return app


def run_inspector(port: int = 5000, debug: bool = False, host: str = "0.0.0.0"):
    """
    Start the inspector UI server

    Args:
        port: Port to run on (default: 5000)
        debug: Enable debug mode (default: False)
        host: Host to bind to (default: 0.0.0.0)
    """
    app = create_app()
    print(f"📊 CERT Inspector running at http://localhost:{port}")
    print("📝 Press Ctrl+C to stop")
    app.run(host=host, port=port, debug=debug)
