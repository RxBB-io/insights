import ibis
import sqlglot.expressions as sge
from ibis.backends.sql.compilers.base import SQLGlotCompiler


def patch_duplicate_ctes():
    """Stop ibis 11 writing a native query's CTEs twice under sqlglot 28+.

    ibis 11 hoists the root statement's CTEs and clears them with `args.pop("with")`
    before re-attaching them. sqlglot 28 renamed that key to `with_`, so the clear is a
    no-op and every CTE is written twice: MariaDB answers `(4004, 'Duplicate query name
    ... in WITH clause')` and DuckDB `Duplicate CTE name`.

    Nesting the query hides its CTEs from ibis, but a derived table's ORDER BY is
    ignored by MariaDB, so the rows come back unordered and a LIMIT picks the wrong
    ones. Dropping the stale copies instead gives the SQL ibis meant to write. ibis 12
    clears the right key, so this does nothing there.
    """
    if not ibis.__version__.startswith("11.") or "with_" not in sge.Select.arg_types:
        return
    if getattr(SQLGlotCompiler.translate, "_drops_duplicate_ctes", False):
        return

    translate = SQLGlotCompiler.translate

    def translate_without_duplicate_ctes(self, op, *, params):
        return drop_duplicate_ctes(translate(self, op, params=params))

    translate_without_duplicate_ctes._drops_duplicate_ctes = True
    SQLGlotCompiler.translate = translate_without_duplicate_ctes


def drop_duplicate_ctes(query):
    """Drop a CTE that is repeated, same name and same body, later in the WITH clause."""
    with_ = query.args.get("with_") if isinstance(query, sge.Expression) else None
    if not with_ or len(with_.expressions) < 2:
        return query

    ctes = with_.expressions
    kept = [
        cte
        for i, cte in enumerate(ctes)
        if not any(later.alias == cte.alias and later.this == cte.this for later in ctes[i + 1 :])
    ]
    with_.set("expressions", kept)
    return query
