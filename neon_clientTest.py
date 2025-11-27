# neon_client.py
import psycopg2
import logging

log = logging.getLogger("neon")


class NeonClient:
    """
    Small helper to send data to your Neon PostgreSQL database.
    """

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = psycopg2.connect(db_url)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        log.info("Connected to Neon PostgreSQL")

    def insert_environmental(self, data: dict):
        """
        Insert environmental data.
        Expected keys: temperature, humidity, timestamp
        """
        try:
            self.cur.execute(
                """
                INSERT INTO environmental_readings
                    (temperature, humidity, raw_timestamp)
                VALUES (%s, %s, %s)
                """,
                (
                    data.get("temperature"),
                    data.get("humidity"),
                    data.get("timestamp"),
                )
            )
        except Exception as e:
            log.error("Failed to insert environmental data into Neon: %s", e, exc_info=True)

    def close(self):
        try:
            self.cur.close()
            self.conn.close()
        except Exception:
            pass
        log.info("Neon connection closed")
