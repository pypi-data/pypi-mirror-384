from flask import request


def get_user_agent():
    """Get lowercase user agent string"""
    return request.user_agent.string.lower()

def get_ip():
    """Get client IP address"""
    nodes = request.headers.getlist("X-Forwarded-For")
    return nodes[0] if nodes else request.remote_addr

def get_rule():
    """Get current URL rule"""
    return request.url_rule

def get_platform(cls):
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