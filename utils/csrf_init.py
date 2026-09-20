#!/usr/bin/env python3
"""
CSRF protection initialization for Ahoy Indie Media
Handles CSRF token validation and error responses
"""

import structlog
from flask import request, jsonify, g
from flask_wtf.csrf import CSRFProtect, CSRFError

logger = structlog.get_logger()


def init_csrf(app):
    """Initialize CSRF protection"""
    csrf = CSRFProtect(app)
    
    # Configure CSRF to accept tokens from X-CSRFToken header for JSON requests
    @csrf.exempt
    def exempt_json_requests():
        """Analytics endpoint is exempt to avoid auth-loop issues"""
        if request.path == '/api/admin/analytics/event':
            return True
        return False
    
    # Custom CSRF error handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Handle CSRF validation errors with structured JSON response"""
        import os
        request_id = getattr(g, 'request_id', None)

        # Suppress analytics noise in dev (SPA never sends CSRF token here)
        is_dev = os.getenv("FLASK_ENV", "development") != "production"
        if is_dev and request.path == '/api/admin/analytics/event':
            pass  # silent in dev
        else:
            logger.warning("CSRF validation failed",
                          error=str(e),
                          path=request.path,
                          method=request.method,
                          request_id=request_id,
                          user_agent=request.headers.get('User-Agent', 'unknown'))
        
        return jsonify({
            "error": "CSRF validation failed",
            "reason": "Invalid or missing CSRF token",
            "request_id": request_id
        }), 400
    
    return csrf
