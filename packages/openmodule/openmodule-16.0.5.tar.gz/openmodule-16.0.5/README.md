# OpenModule V2

[TOC]

## Quickstart

You can install this library via pip:
```bash
pip install openmodule
```

#### Development with Feature Branches

During development it might be necessary to install a version of openmodule, where no pip package exists.
Below you can find how to install a certain openmodule branch for your application with pip.

##### Openmodule

Bash command:
```bash
pip install "git+https://gitlab.com/arivo-public/device-python/openmodule@<branch>#egg=openmodule"
```

requirements.txt:
```text
git+https://gitlab.com/arivo-public/device-python/openmodule@<branch>#egg=openmodule
```

##### Openmodule Test

Bash command:
```bash
pip install "git+https://gitlab.com/arivo-public/device-python/openmodule@<branch>#egg=openmodule-test&subdirectory=openmodule_test"
```

requirements.txt:
```text
git+https://gitlab.com/arivo-public/device-python/openmodule@<branch>#egg=openmodule-test&subdirectory=openmodule_test
```

##### Openmodule Commands

Bash command:
```bash
pip install "git+https://gitlab.com/arivo-public/device-python/openmodule@<branch>#egg=openmodule-commands&subdirectory=openmodule_commands
```

requirements.txt:
```text
git+https://gitlab.com/arivo-public/device-python/openmodule@<branch>#egg=openmodule-commands&subdirectory=openmodule_commands
```

#### Local Development

Sometimes you want to test local changes of the Openmodule library in device services and therefore you can do a local
installation of the library. We use the
[editable installs](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs) of Pip for this.

##### Openmodule

bash command:
```bash
pip install -e <path_to_openmodule_root>
```

##### Openmodule Test

bash command:
```bash
pip install -e <path_to_openmodule_root>/openmodule_test/
```

##### Openmodule Commands

bash command:
```bash
pip install -e <path_to_openmodule_root>/openmodule_commands/
```

## Changes

- [Breaking Changes](docs/migrations.md)
- [Known Issues](docs/known_issues.md)

## Documentation

### Openmodule

- [Getting Started](docs/getting_started.md)
- [Coding Standard](docs/coding_standard.md)
- [Settings](docs/settings.md)
- [RPC](docs/rpc.md)
- [Health](docs/health.md)
- [Database](docs/database.md)
- [Eventlog](docs/event_sending.md)
- [Package Reader](docs/package_reader.md)
- [Anonymization](docs/anonymization.md)
- [Connection Status Listener](docs/connection_status_listener.md)
- [Settings Provider](docs/settings_provider.md)
- [Access Service](docs/access_service.md)
- [CSV Export](docs/csv_export.md)
- [Translations](docs/translation.md)
- [Utils](docs/utils.md)
- [Deprecated Features](docs/deprecated.md)
- [Testing](docs/testing.md)
- [File Cleanup](docs/cleanup.md)

### Openmodule Commands

- [Openmodule Commands](docs/commands.md)
