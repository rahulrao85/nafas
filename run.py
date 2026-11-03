"""Start Nafas locally: python run.py  →  http://127.0.0.1:5057"""

import os

from nafas.server import app

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    port = int(os.getenv("PORT", "5057"))
    app.run(host="127.0.0.1", port=port, debug=False)
