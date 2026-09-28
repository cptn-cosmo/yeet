"""
Yeet - Main Entrypoint
App ID: gay.geeks.Yeet
"""

import sys
import logging

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    from .app import YeetApplication
    app = YeetApplication(sys.argv)
    app.start()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
