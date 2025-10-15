from xl_router.router import Router
from flask import Flask, request 
from flask.json import JSONEncoder
from importlib import import_module
from typing import Optional
import decimal


class JsonEncoder(JSONEncoder):
    """Custom JSON encoder that handles Decimal objects"""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return JSONEncoder.default(self, obj)


class App(Flask):
    """Extended Flask application with resource registration capabilities"""
    resources = []

    def __init__(self, config, *args, **kwargs):
        """Initialize app with custom JSON encoder and config"""
        super().__init__('', *args, **kwargs)
        self._configure_json()
        self._load_config(config)

    def _configure_json(self):
        """Configure JSON settings"""
        self.json_provider_class = JsonEncoder
        self.json.ensure_ascii = False

    def _load_config(self, config):
        """Load configuration from dict or file"""
        if isinstance(config, dict):
            self.config.from_mapping(config)
        elif isinstance(config, str) and config.endswith('.py'):
            self.config.from_pyfile(config)

    def register_extensions(self):
        """Register Flask extensions"""
        pass

    def register_resources(self):
        """Register blueprints for all resources"""
        for module_name in self.resources:
            module = import_module(f'app.core.{module_name}.resources')
            self.register_blueprint(module.router)


class RequestUtils:
    """Utility class for handling request-related operations"""
    
    @staticmethod
    def get_user_agent() -> str:
        """Get lowercase user agent string"""
        return request.user_agent.string.lower()

    @staticmethod
    def get_ip() -> str:
        """Get client IP address"""
        nodes = request.headers.getlist("X-Forwarded-For")
        return nodes[0] if nodes else request.remote_addr

    @staticmethod
    def get_rule():
        """Get current URL rule"""
        return request.url_rule

    @classmethod
    def get_platform(cls) -> int:
        """
        Get platform identifier
        Returns:
            1: Desktop (Windows/Mac)
            2: Mobile/Other
        """
        user_agent = cls.get_user_agent()
        if 'windows' in user_agent:
            return 1
        if 'mac os' in user_agent and 'iphone' not in user_agent:
            return 1
        return 2