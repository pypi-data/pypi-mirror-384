import os
import shutil
from glob import glob
from unittest import TestCase

from alembic import command
from alembic.runtime.migration import MigrationContext
from sqlalchemy import MetaData, text
from sqlalchemy.ext.automap import automap_base

from openmodule.config import settings
from openmodule.database.database import Database, database_path
from openmodule.database.migration import alembic_config

from unittest.mock import patch

_first_start = True


def truncate_all_tables(database: Database, keep=("alembic_version",)):
    assert any(x in database.db_folder for x in ["/test/"]), "deleting all tables is only for testing"
    metadata = MetaData()
    metadata.reflect(bind=database._engine)
    with database._engine.connect() as con:
        trans = con.begin()
        for table in reversed(metadata.sorted_tables):
            if table.name not in keep:
                con.execute(table.delete())
        trans.commit()


class SQLiteTestMixin(TestCase):
    """
    Mixin for database cleanup in test cases
    * use create_database = True for an automatic generation of a database
    * use create_database = False and set the database directly
    """
    create_database = True
    database = None
    database_folder: str = None  # defaults to settings.DATABASE_FOLDER
    alembic_path = "../src/database"
    database_name = "database"
    main_process_migration = True  # change if migration should be performed in a separate process
    delete_backups = True  # if True, all database backups are deleted on teardown

    @classmethod
    def get_database_folder(cls):
        return cls.database_folder or settings.DATABASE_FOLDER

    @classmethod
    def setUpClass(cls) -> None:
        if cls.main_process_migration is True:
            from openmodule.database.migration import migrate_database
            # instead of migrating db in a child process we 'mock' it in the main process to prevent some errors
            cls.patcher = patch(
                'openmodule.database.database.execute_migration',
                new=lambda x, y: migrate_database(x, y)
            )
            cls.patcher.start()

        # we only know which databases are in use on tear down, so truncating only works in teardown
        # but in order to not be annoyed by failed tests which left broken databases, we delete all databases
        # once initially
        global _first_start
        if _first_start:
            for file in glob(os.path.join(cls.get_database_folder(), "*.sqlite3")):
                os.unlink(file)
            _first_start = False
        if cls.create_database:
            cls.database = Database(cls.get_database_folder(), cls.database_name, cls.alembic_path)
        return super().setUpClass()

    @staticmethod
    def delete_database(database: Database):
        assert not database.is_open(), "database must be shutdown before it can be deleted"
        try:
            os.unlink(database_path(database.db_folder, database.name))
        except FileNotFoundError:
            pass

    def tearDown(self):
        super().tearDown()
        if self.create_database:
            truncate_all_tables(self.database)
        if self.delete_backups:
            for file in glob(os.path.join(self.get_database_folder(), f"{self.database_name}_*.sqlite3.backup")):
                os.unlink(file)

    @classmethod
    def tearDownClass(cls):
        if cls.create_database:
            cls.database.shutdown()
            os.unlink(database_path(cls.get_database_folder(), cls.database_name))
        super().tearDownClass()
        if cls.main_process_migration is True:
            cls.patcher.stop()


class AlembicMigrationTestMixin(SQLiteTestMixin):
    """
    Mixin for testing alembic migrations (up & down)
    **DO NOT** import your database models in migration testcases, as the Models don't necessarily
        match the database schema.
    Set existing_database to the *.sqlite3 file you want to use for testing. **DO NOT** place your test database
        in the <project_root>/sqlite/ folder, as it will be deleted in some cases.
    This will copy the existing_database to the test database folder to ensure that the database is not modified.
    create_database must be set to True, otherwise it is assumed that the programmer manages the database themselves.
    """
    existing_database = None

    def setUp(self):
        self.base = automap_base()
        if self.create_database:
            if self.existing_database:
                shutil.copyfile(self.existing_database, database_path(self.get_database_folder(), self.database_name))
            else:
                metadata = MetaData()
                metadata.reflect(bind=self.connection)
                metadata.drop_all(bind=self.connection)
        super().setUp()
        if self.database:
            self.reload_models()

    @property
    def connection(self):
        return self.database._engine

    def reload_models(self):
        self.base = automap_base()
        self.base.prepare(autoload_with=self.connection)

    def alembic_config(self):
        alembic_path = self.alembic_path or os.path.join(os.getcwd(), "database")
        assert os.path.exists(
            os.path.abspath(alembic_path)), f"alembic path {os.path.abspath(alembic_path)} does not exist"
        return alembic_config(self.connection, alembic_path)

    def migrate_up(self, revision="head"):
        config = self.alembic_config()
        command.upgrade(config, revision)
        with self.connection.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).fetchone()[0] == 1, "foreign keys are not enabled"
        self.reload_models()

    def migrate_down(self, revision="base"):
        config = self.alembic_config()
        command.downgrade(config, revision)
        with self.connection.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).fetchone()[0] == 1, "foreign keys are not enabled"
        self.reload_models()

    def current_revision(self):
        with self.connection.connect() as con:
            context = MigrationContext.configure(con)
            return context.get_current_revision()

    def get_model(self, name):
        return getattr(self.base.classes, name)
