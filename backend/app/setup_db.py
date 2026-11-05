import argparse
import json
import logging

from app.database import SessionLocal, run_migrations
from app.seed import seed_if_empty, verify_checkpoint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate + seed school database")
    parser.add_argument("--skip-migrate", action="store_true", help="Only run seed")
    parser.add_argument("--force", action="store_true", help="Force reseed from JSON")
    parser.add_argument("--verify", action="store_true", help="Print checkpoint summary")
    args = parser.parse_args()

    if not args.skip_migrate:
        logger.info("Applying SQL migrations...")
        run_migrations()

    session = SessionLocal()
    try:
        seed_if_empty(session, force=args.force)
        if args.verify:
            print(json.dumps(verify_checkpoint(session), indent=2, default=str))
        else:
            from app.models import Student

            print(f"Done. Students: {session.query(Student).count()}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
