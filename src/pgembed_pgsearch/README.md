# pgembed-pgsearch

ParadeDB [`pg_search`](https://github.com/paradedb/paradedb) (`v0.27.0`) as a
separate `pgembed` extension package.

## Installation

```bash
pip install pgembed pgembed-pgsearch
```

## Usage

`pg_search` `v0.27.0` requires:
1. `'pg_search'` loaded via `shared_preload_libraries` at server start.
2. The `vector` (`pgvector`) extension (bundled in base `pgembed`, automatically created when calling `server.create_extension("pg_search")`).

```python
import pgembed

assert pgembed.has_extension("pg_search")

with pgembed.get_server(
    "/path/to/data",
    shared_preload_libraries=["pg_search"],
) as server:
    server.create_extension("pg_search")
```

## License

`pg_search` is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.
