Additional files for the proxy. Reduces the size of the main skorplandgpt package.

Currently, only stores the migration.sql files for skorplandgpt-proxy.

To install, run:

```bash
pip install skorplandgpt-proxy-extras
```
OR 

```bash
pip install skorplandgpt[proxy] # installs skorplandgpt-proxy-extras and other proxy dependencies
```

To use the migrations, run:

```bash
skorplandgpt --use_prisma_migrate
```

