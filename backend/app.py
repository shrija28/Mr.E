"""Flask backend entry-point."""

import os
import sys

from smartkcet.main import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
