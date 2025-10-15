# src/qf_common/db/client.py
from __future__ import annotations
import logging
from typing import Mapping, Sequence, Any
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

class DBClient:
    """
    Client léger pour exécuter des queries et retourner des DataFrames.
    Wrappe SQLAlchemy Engine.
    """

    def __init__(self, dsn: str, *, pool_size: int = 5, max_overflow: int = 10, echo: bool = False):
        self._engine: Engine = create_engine(
            dsn,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=echo,
            future=True,
        )

    def execute(
        self,
        query: str,
        params: Mapping[str, Any] | Sequence[Any] | None = None,
    ) -> int:
        try:
            with self._engine.begin() as conn:
                result = conn.execute(text(query), params or {})
                return result.rowcount
        except Exception as e:
            logger.error(f"Error executing write query: {e}", exc_info=True)
            raise

    def fetch_df(
        self,
        query: str,
        params: Mapping[str, Any] | Sequence[Any] | None = None,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        try:
            with self._engine.begin() as conn:
                result = conn.execute(text(query), params or {})
                rows = result.fetchall()
                if not rows:
                    return pd.DataFrame(columns=columns or result.keys())
                return pd.DataFrame(rows, columns=columns or result.keys())
        except Exception as e:
            logger.error(f"Error executing query: {e}", exc_info=True)
            raise

    def insert_df(
        self,
        df: pd.DataFrame,
        table: str,
        conflict_cols: list[str] | None = None,
        *,
        schema: str = "public",
        chunksize: int = 1000,
    ) -> int:
        """
        Insère un DataFrame dans une table PostgreSQL.
        - Si `conflict_cols` est fourni -> ON CONFLICT (...) DO NOTHING
        - Sinon -> INSERT simple

        Args:
            df: DataFrame à insérer.
            table: Nom de la table cible (sans schéma).
            conflict_cols: Colonnes formant la contrainte unique (ou index unique existant). None par défaut.
            schema: Schéma SQL (par défaut 'public').
            chunksize: Taille des batches.

        Returns:
            int: Nombre de lignes effectivement insérées.
        """
        if df.empty:
            logger.info("insert_df called with empty DataFrame → nothing done.")
            return 0

        cols = list(df.columns)
        placeholders = ", ".join([f":{c}" for c in cols])
        colnames = ", ".join([f'"{c}"' for c in cols])

        if conflict_cols:
            conflict = ", ".join([f'"{c}"' for c in conflict_cols])
            query = f"""
            INSERT INTO {schema}."{table}" ({colnames})
            VALUES ({placeholders})
            ON CONFLICT ({conflict}) DO NOTHING
            """
        else:
            query = f"""
            INSERT INTO {schema}."{table}" ({colnames})
            VALUES ({placeholders})
            """

        total_inserted = 0
        with self._engine.begin() as conn:
            for start in range(0, len(df), chunksize):
                chunk = df.iloc[start:start + chunksize]
                params = chunk.to_dict(orient="records")
                result = conn.execute(text(query), params)
                # rowcount = lignes effectivement insérées; en cas de DO NOTHING,
                # les conflictuelles ne sont pas comptées.
                total_inserted += result.rowcount

        logger.info(
            "Inserted %d rows into %s.%s%s.",
            total_inserted, schema, table,
            "" if not conflict_cols else " (conflicts ignored)"
        )
        return total_inserted
