# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
from contrast.utils.deprecated_middleware import deprecated_wsgi


FlaskMiddleware = deprecated_wsgi("flask")
