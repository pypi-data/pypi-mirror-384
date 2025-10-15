from typing import Sequence, Tuple

from sqlalchemy import String, Text, cast, desc, func, literal, or_
from sqlalchemy.dialects.postgresql import REGCONFIG
from sqlalchemy.sql.elements import ColumnElement, UnaryExpression


def free_search(
    columns: Sequence[ColumnElement],
    query: str,
    threshold: float,
    exact: bool = True,
    tokenize: bool = True,
) -> Tuple[Sequence[ColumnElement], Sequence[UnaryExpression]]:
    """Build WHERE conditions and ORDER BY clauses for a free-text search.

    :param columns: List of SQLAlchemy column expressions to search.
    :param query: The search string.
    :param threshold: Similarity threshold for fuzzy matching.
    :param exact: If True, perform exact or phrase search; otherwise fuzzy.
    :param tokenize: If True, use full-text search; otherwise simple comparisons.

    :return: A tuple (conditions, order_by), where:
        - conditions: SQL boolean expressions for WHERE.
        - order_by: SQL expressions for ORDER BY.
    """
    # Helper: cast query to Text
    txt_query = literal(query).cast(Text)

    def similarity_expressions() -> Sequence[UnaryExpression]:
        return [func.similarity(cast(col, Text), txt_query) for col in columns]

    # Non-tokenized logic
    if not tokenize:
        if exact:
            low = query.lower()
            exprs = [func.lower(cast(col, Text)) == low for col in columns]
            return [or_(*exprs)], []
        sims = similarity_expressions()
        best = func.greatest(*sims)
        return [best > threshold], [desc(best)]

    # Tokenized logic: build TSVECTOR
    concatenated = func.concat_ws(" ", *[cast(col, String) for col in columns])
    tsv = func.to_tsvector(literal("english", type_=REGCONFIG), concatenated)

    if exact:
        tsq = func.phraseto_tsquery("english", query)
        rank = func.ts_rank_cd(tsv, tsq)
        return [tsv.op("@@")(tsq)], [desc(rank)]

    # Combined fuzzy + full-text
    tsq = func.websearch_to_tsquery("english", query)
    rank = func.ts_rank_cd(tsv, tsq)
    sims = similarity_expressions()
    best = func.greatest(*sims)
    combined = func.greatest(rank, best)
    cond = or_(tsv.op("@@")(tsq), best > threshold)
    return [cond], [desc(combined)]
