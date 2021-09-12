import pytest


@pytest.fixture()
def markdown_text():
    """Sample markdown text."""

    md = """

    <h1>Postgres Periphery</h1>
        <strong>>> <i>An non-DBA's journey to make sense of the behemoth that PostgreSQL is!</i> <<</strong>

        &nbsp;

        </div>

        ![img](./art/logo.jpg)

        ## Prelude

        * [Looking Back at Postgres - Joseph M. Hellerstein](https://arxiv.org/pdf/1901.01973.pdf) -> A comprehensive history of how PostgreSQL came into being and the minds behind it.

        ## General Concepts

        * [What is Normalization in DBMS (SQL)? 1NF, 2NF, 3NF, BCNF Database with Example - Richard Peterson](https://www.guru99.com/database-normalization.html) -> Normalization roughly means, deduplication of data in a table by leveraging foreign keys, multiple tables, and intermediary join tables. This article explains it in finer detail.

        * [OLTP vs OLAP System](https://www.guru99.com/oltp-vs-olap.html) -> OLTP is an online transactional system that manages database modification whereas OLAP is an online analysis and data retrieving process.


        ## Postgres Concepts

        * [Transactions, and sub-transactions with SAVEPOINT, 101](https://www.postgresql.org/docs/13/tutorial-transactions.html) -> ELI5 explation of how to do transactions and subtransactions.

        * [PostgreSQL Concurrency with MVCC](https://devcenter.heroku.com/articles/postgresql-concurrency) -> This explains **Transaction**, **Transaction Isolation**, **MVCC**, and how Postgres achieves MVCC with **Read Commited** and **Serializable** level transaction isolation.
    """
    return md
