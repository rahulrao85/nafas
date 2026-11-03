"""Start Nafas locally.

    python run.py                                   → demo, http://127.0.0.1:5057
    python run.py --port 5058 --hub PATH/hub.db     → personal mode: your own nights from a home hub store
"""

import argparse
import os

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run Nafas")
    ap.add_argument("--port", type=int, default=int(os.getenv("PORT", "5057")))
    ap.add_argument("--hub", help="path to a home hub store (hub.db); turns on personal mode")
    a = ap.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    if a.hub:
        os.environ["NAFAS_PERSONAL_HUB"] = "1"
        os.environ["NAFAS_HUB_DB"] = a.hub
    from nafas.server import app
    app.run(host="127.0.0.1", port=a.port, debug=False)
