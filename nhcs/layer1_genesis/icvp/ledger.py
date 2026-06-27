"""
Global Knowledge Ledger — SQLite-backed append-only store.

Schema per record:
  concept_id  : UUID str
  did         : DID str (submitter)
  timestamp   : ISO8601 str
  signature   : str
  betti       : JSON list[int]
  merit       : JSON dict (MeritScores)
  votes       : JSON list[ICVPVote]
  consensus   : JSON dict (ConsensusProtocol tally summary)
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS ledger (
    concept_id  TEXT PRIMARY KEY,
    did         TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    betti       TEXT NOT NULL,
    merit       TEXT NOT NULL,
    votes       TEXT NOT NULL,
    consensus   TEXT NOT NULL
);
"""


class GlobalKnowledgeLedger:
    """
    Append-only ledger of validated concepts.

    Parameters
    ----------
    db_path : str | Path
        Path to the SQLite database file.
        Use ":memory:" for in-process tests.
    """

    def __init__(self, db_path: str | Path = "nhcs_ledger.db") -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()
        logger.info("Ledger opened at %s.", self.db_path)

    def commit(
        self,
        concept_id: str,
        did: str,
        betti: list[int],
        merit_dict: dict,
        votes_list: list[dict],
        consensus_dict: dict,
    ) -> None:
        """
        Append a validated concept. Raises ValueError if concept_id exists.
        """
        ts = datetime.now(tz=timezone.utc).isoformat()
        try:
            self._conn.execute(
                "INSERT INTO ledger VALUES (?,?,?,?,?,?,?)",
                (
                    concept_id,
                    did,
                    ts,
                    json.dumps(betti),
                    json.dumps(merit_dict),
                    json.dumps(votes_list),
                    json.dumps(consensus_dict),
                ),
            )
            self._conn.commit()
            logger.info("Ledger committed concept %s.", concept_id)
        except sqlite3.IntegrityError:
            raise ValueError(f"Concept {concept_id} already in ledger.")

    def get(self, concept_id: str) -> dict | None:
        cur = self._conn.execute(
            "SELECT * FROM ledger WHERE concept_id=?", (concept_id,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = ["concept_id", "did", "timestamp", "betti", "merit", "votes", "consensus"]
        record = dict(zip(cols, row))
        for key in ("betti", "merit", "votes", "consensus"):
            record[key] = json.loads(record[key])
        return record

    def all_concept_ids(self) -> list[str]:
        cur = self._conn.execute("SELECT concept_id FROM ledger ORDER BY timestamp")
        return [row[0] for row in cur.fetchall()]

    def __len__(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM ledger")
        return cur.fetchone()[0]

    def close(self) -> None:
        self._conn.close()
