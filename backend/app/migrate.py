import logging

from app.database import run_migrations

logging.basicConfig(level=logging.INFO)


def main() -> None:
    logging.info("Running SQL migrations...")
    run_migrations()
    logging.info("Migrations complete.")


if __name__ == "__main__":
    main()
