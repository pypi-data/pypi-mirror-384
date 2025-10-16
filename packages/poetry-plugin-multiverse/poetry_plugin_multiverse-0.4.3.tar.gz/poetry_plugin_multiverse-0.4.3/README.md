# Poetry Multiverse Plugin

*Workspace support for Poetry.*

This plugin manages dependencies for multi-project workspaces, similar to tools like Cargo, Maven, and PNPM.

## Quick Start

This plugin requires Poetry 1.8 or later.
Poetry must be running on Python 3.9 or later.
(This is not necessarily the same as your project's Python version.)

1.  Install the plugin:
    ```bash
    poetry self add poetry-plugin-multiverse
    ```

2.  Create a file named multiverse.toml in the root of your workspace:
    ```bash
    touch multiverse.toml
    ```

3.  Check whether projects in the workspace are locked to the same package versions:
    ```bash
    poetry workspace check
    ```

## Plugin Development

In addition to the runtime dependencies, install:

* [Poe the Poet](https://poethepoet.natn.io)
* [poetry-dynamic-versioning[plugin]](https://github.com/mtkennerly/poetry-dynamic-versioning)
