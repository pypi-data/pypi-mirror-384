import sqlalchemy.exc
from sqlalchemy import text

from openmodule.utils.db_helper import delete_query

from openmodule_test.database import AlembicMigrationTestMixin


class AlembicMigrationTestMixinTest(AlembicMigrationTestMixin):
    alembic_path = "../tests/migration_test_database"
    main_process_migration = False  # execute migration in a child process

    def test_initial_is_base(self):
        self.assertIsNone(self.current_revision())

    def test_migrate_up_no_data(self):
        self.migrate_up("19789aa5361c")
        self.assertEqual(self.current_revision(), "19789aa5361c")
        self.migrate_up("19d887929ae7")
        self.assertEqual(self.current_revision(), "19d887929ae7")

    def test_migrate_head_no_data(self):
        self.migrate_up()
        self.assertEqual(self.current_revision(), "19d887929ae7")

    def test_migrate_down_no_data(self):
        self.migrate_up()
        self.migrate_down("19789aa5361c")
        self.assertEqual(self.current_revision(), "19789aa5361c")
        self.migrate_down("base")
        self.assertIsNone(self.current_revision())

    def test_migrate_base_no_data(self):
        self.migrate_up()
        self.migrate_down()
        self.assertIsNone(self.current_revision())

    def test_models_from_schema(self):
        self.migrate_up()
        parent_model = self.get_model("cascade_delete_parent")
        child_model = self.get_model("cascade_delete_child")
        with self.database as session:
            parent = session.query(parent_model).first()
            self.assertEqual(parent.name, 666)
            self.assertEqual(parent.id, 1)
            child = session.query(child_model).first()
            self.assertEqual(len(parent.cascade_delete_child_collection), 1)
            self.assertEqual(child, parent.cascade_delete_child_collection[0])
            self.assertEqual(child.id, 1)
            self.assertEqual(child.parent_id, 1)
            self.assertEqual(child.cascade_delete_parent, parent)

    def test_insert(self):
        self.migrate_up()
        parent_model = self.get_model("cascade_delete_parent")
        child_model = self.get_model("cascade_delete_child")
        with self.database as session:
            parent = parent_model(name=777)
            session.add(parent)
            session.commit()
            child = child_model(parent_id=parent.id)
            session.add(child)
            session.commit()

            self.assertEqual(session.query(parent_model).count(), 2)
            self.assertEqual(session.query(child_model).count(), 2)
            self.assertEqual(len(parent.cascade_delete_child_collection), 1)
            self.assertEqual(child, parent.cascade_delete_child_collection[0])
            self.assertEqual(child.id, 2)
            self.assertEqual(child.parent_id, 2)
            self.assertEqual(child.cascade_delete_parent, parent)

    def test_delete(self):
        self.migrate_up()
        parent_model = self.get_model("cascade_delete_parent")
        child_model = self.get_model("cascade_delete_child")
        with self.database as session:
            assert session.execute(text("PRAGMA foreign_keys")).fetchone()[0] == 1, "foreign keys are not enabled"
            parent = parent_model(name=777)
            session.add(parent)
            session.commit()
            child = child_model(parent_id=parent.id)
            session.add(child)
            session.commit()

            delete_query(session, session.query(parent_model).filter(parent_model.name == 777))
            session.commit()
            self.assertEqual(session.query(parent_model).count(), 1)
            self.assertEqual(session.query(child_model).count(), 1)

    def test_migration_fails_with_invalid_data(self):
        self.migrate_up()
        parent_model = self.get_model("cascade_delete_parent")
        with self.database as session:
            session.add(parent_model())
            session.commit()
        with self.assertRaises(sqlalchemy.exc.IntegrityError) as e:
            self.migrate_down("19789aa5361c")
        self.assertEqual(
            e.exception.orig.args[0], "NOT NULL constraint failed: _alembic_tmp_cascade_delete_parent.name")

    def test_auto_generated_models(self):
        with self.assertRaises(AttributeError):
            self.get_model("cascade_delete_parent")
        with self.assertRaises(AttributeError):
            self.get_model("cascade_delete_child")
        self.migrate_up()
        with self.assertRaises(AttributeError):
            self.get_model("not_existing_model")
        self.get_model("cascade_delete_parent")
        self.get_model("cascade_delete_child")
        self.migrate_down()
        with self.assertRaises(AttributeError):
            self.get_model("cascade_delete_parent")
        with self.assertRaises(AttributeError):
            self.get_model("cascade_delete_child")


class AlembicMigrationTestMixinExistingDatabaseTest(AlembicMigrationTestMixin):
    alembic_path = "../tests/migration_test_database"
    existing_database = "../tests/migration_test_database/alembic_migration_test_database.sqlite3"
    main_process_migration = False  # execute migration in a child process

    def test_ensure_data_exists(self):
        self.assertEqual(self.current_revision(), "19d887929ae7")
        parent_model = self.get_model("cascade_delete_parent")
        child_model = self.get_model("cascade_delete_child")
        with self.database as session:
            self.assertEqual(session.query(parent_model).count(), 3)
            self.assertEqual(session.query(child_model).count(), 4)

    def test_ensure_data_not_changed_1(self):
        parent_model = self.get_model("cascade_delete_parent")
        child_model = self.get_model("cascade_delete_child")
        with self.database as session:
            delete_query(session, session.query(parent_model))
            delete_query(session, session.query(child_model))
            session.commit()
        with self.database as session:
            self.assertEqual(session.query(parent_model).count(), 0)
            self.assertEqual(session.query(child_model).count(), 0)

    def test_ensure_data_not_changed_2(self):
        """
        This test should run after test_ensure_data_not_changed_1. The tearDown and setUp should have
            reloaded the database from the existing_database file.
        """
        parent_model = self.get_model("cascade_delete_parent")
        child_model = self.get_model("cascade_delete_child")
        with self.database as session:
            self.assertEqual(session.query(parent_model).count(), 3)
            self.assertEqual(session.query(child_model).count(), 4)

    def test_migration_fails_with_invalid_data(self):
        with self.assertRaises(sqlalchemy.exc.IntegrityError) as e:
            self.migrate_down("19789aa5361c")
        self.assertEqual(
            e.exception.orig.args[0], "NOT NULL constraint failed: _alembic_tmp_cascade_delete_parent.name")

    def test_migration(self):
        parent_model = self.get_model("cascade_delete_parent")
        child_model = self.get_model("cascade_delete_child")
        with self.database as session:
            delete_query(session, session.query(parent_model).filter(parent_model.name.is_(None)))
            session.commit()
            self.assertEqual(session.query(parent_model).count(), 2)
            self.assertEqual(session.query(child_model).count(), 2)

        self.migrate_down("19789aa5361c")
        parent_model = self.get_model("cascade_delete_parent")
        child_model = self.get_model("cascade_delete_child")
        with self.database as session:
            self.assertEqual(session.query(parent_model).count(), 2)
            self.assertEqual(session.query(child_model).count(), 2)
        self.migrate_down()
        self.migrate_up()
