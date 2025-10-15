import os
import shutil
import sys
import warnings
from typing import Optional

from alembic import command, context
from alembic.autogenerate import comparators, renderers
from alembic.config import Config
from alembic.operations import Operations, MigrateOperation
from alembic.runtime.migration import MigrationContext
from sqlalchemy import MetaData, DateTime, inspect, text
from sqlalchemy.engine import Engine

from openmodule.utils.misc_functions import utcnow


@Operations.register_operation("pre_upgrade")
class PreUpgradeOp(MigrateOperation):
    @classmethod
    def pre_upgrade(cls, operations, **kw):
        migration_context: MigrationContext = operations.migration_context
        db_file = migration_context.connection.engine.url.database
        db_dir = os.path.dirname(db_file)
        basename, _ = os.path.splitext(os.path.basename(db_file))
        timestamp = utcnow().strftime('%Y%m%d%H%M%S')
        migration_revision = migration_context.get_current_revision()
        filename = f"{basename}_{timestamp}_{migration_revision}.sqlite3.backup"

        for file in os.listdir(db_dir):
            if file.startswith(f"{basename}_") and file.endswith(".sqlite3.backup"):
                try:
                    file_timestamp = file[len(basename) + 1:len(basename) + 15]
                    file_time = utcnow().strptime(file_timestamp, '%Y%m%d%H%M%S')
                    if (utcnow() - file_time).seconds < 60:
                        # No backup if we created one in the last 60 seconds
                        break
                except Exception:
                    # ignore any issues here
                    pass
        else:
            shutil.copy(db_file, os.path.join(db_dir, filename))

        op = PreUpgradeOp(**kw)
        return operations.invoke(op)

    def reverse(self):
        # only needed to support autogenerate
        return PostDowngradeOp()


@Operations.register_operation("post_upgrade")
class PostUpgradeOp(MigrateOperation):
    @classmethod
    def post_upgrade(cls, operations, **kw):
        op = PostUpgradeOp(**kw)
        return operations.invoke(op)

    def reverse(self):
        # only needed to support autogenerate
        return PreDowngradeOp()


@Operations.register_operation("pre_downgrade")
class PreDowngradeOp(MigrateOperation):
    @classmethod
    def pre_downgrade(cls, operations, **kw):
        op = PreDowngradeOp(**kw)
        return operations.invoke(op)

    def reverse(self):
        # only needed to support autogenerate
        return PostUpgradeOp()


@Operations.register_operation("post_downgrade")
class PostDowngradeOp(MigrateOperation):
    @classmethod
    def post_downgrade(cls, operations, **kw):
        op = PostDowngradeOp(**kw)
        return operations.invoke(op)

    def reverse(self):
        # only needed to support autogenerate
        return PreUpgradeOp()


@Operations.implementation_for(PreUpgradeOp)
def pre_upgrade(operations, operation):
    # NOTE: This is currently in sync with pre_downgrade, if you want to have
    # different behavior, you'll need to change th pre_downgrade function below
    conn = operations.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    for table in tables:
        if table.startswith("_alembic_tmp_"):
            operations.drop_table(table)
    operations.execute(text("PRAGMA foreign_keys=OFF"))


@Operations.implementation_for(PostUpgradeOp)
def post_upgrade(operations, operation):
    pass


@Operations.implementation_for(PreDowngradeOp)
def pre_downgrade(operations, operation):
    pre_upgrade(operations, operation)


@Operations.implementation_for(PostDowngradeOp)
def post_downgrade(operations, operation):
    pass


@renderers.dispatch_for(PreUpgradeOp)
def render_create_sequence(autogen_context, op):
    return "op.pre_upgrade()"


@renderers.dispatch_for(PreDowngradeOp)
def render_drop_sequence(autogen_context, op):
    return "op.pre_downgrade()"


@renderers.dispatch_for(PostUpgradeOp)
def render_create_sequence(autogen_context, op):
    return "op.post_upgrade()"


@renderers.dispatch_for(PostDowngradeOp)
def render_drop_sequence(autogen_context, op):
    return "op.post_downgrade()"


@comparators.dispatch_for("schema")
def add_pre_upgrade_hooks(autogen_context, upgrade_ops, schemas):
    # only add those if any operations exist, otherwise we always have changes
    if len(upgrade_ops.ops):
        upgrade_ops.ops.insert(0, PreUpgradeOp())
        upgrade_ops.ops.append(PostUpgradeOp())


def alembic_config(connection: Engine, alembic_path: str):
    alembic_cfg = Config(os.path.join(alembic_path, "alembic.ini"),
                         attributes={
                             "configure_logging": False,
                             "connection": connection,
                         })
    alembic_cfg.set_main_option("script_location", os.path.join(alembic_path, "alembic"))
    return alembic_cfg


def migrate_database(engine: Engine, alembic_path: Optional[str] = None):
    if alembic_path is None:
        alembic_path = os.path.join(os.getcwd(), "database")
    assert os.path.exists(os.path.abspath(alembic_path)), f"alembic path {os.path.abspath(alembic_path)} does not exist"
    config = alembic_config(engine, alembic_path)
    command.upgrade(config, "head")

    with engine.connect() as connection:
        check = connection.execute(text("PRAGMA foreign_keys")).fetchone()
    assert check is not None and check[0] == 1, "foreign keys are not enabled"


def register_bases(bases, show_deprecation_warning=True):
    if show_deprecation_warning:
        warnings.warn(
            '\n\n`register_bases([...])` followed by `from openmodule.database.env import *` is deprecated.\n '
            'Please replace these lines with `run_env_py([bases...])`\n',
            DeprecationWarning
        )

    target_metadata = MetaData()

    if not isinstance(bases, list):
        bases = [bases]

    for base in bases:
        for table in base.metadata.tables.values():
            for x in table.columns:
                check_invalid_database_column_type(x.type)
            table.to_metadata(target_metadata)
    context.config.attributes["target_metadata"] = target_metadata


def run_env_py(bases):
    register_bases(bases, show_deprecation_warning=False)
    # noinspection PyUnresolvedReferences
    import openmodule.database.env
    del sys.modules["openmodule.database.env"]  # unload the module, so we can re-run it (mostly testcases)


def check_invalid_database_column_type(typ):
    from openmodule import config
    if config.run_checks():
        assert not isinstance(typ, DateTime), "Do NOT use DateTime fields, use TZDateTime fields instead"
