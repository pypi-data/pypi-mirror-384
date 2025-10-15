import unittest
import tempfile
import shutil
import sqlite3
import json
import os
from pathlib import Path
from unittest.mock import patch

from ariadne import Theseus
from .ariadne import config_to_name


class TestTheseusCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.exp_dir = Path(self.temp_dir) / "experiments"
        self.theseus = Theseus(
            db_path=self.db_path,
            exp_dir=self.exp_dir,
            loglevel=Theseus.LogLevel.DEBUG
        )

    def tearDown(self):
        self.theseus._cleanup(-1)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_start_experiment_basic(self):
        run_config = {"learning_rate": 0.01, "epochs": 100}
        notes = "Test experiment notes"

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), \
             patch('ariadne.ariadne.get_git_hash', return_value=None):
            exp_id, run_folder = self.theseus.start(run_config, prefix="test_exp", notes=notes)

        # Verify experiment was created
        self.assertIsInstance(exp_id, int)
        self.assertTrue(run_folder.exists())

        # Verify database entry
        experiments = self.theseus.get("test_exp")
        self.assertEqual(len(experiments), 1)
        exp = experiments[0]
        self.assertTrue(exp.name.startswith("test_exp_"))
        self.assertEqual(exp.run_config, run_config)
        self.assertEqual(exp.notes, notes)
        self.assertFalse(exp.completed)

        # Verify config file was created
        config_file = run_folder / "config.json"
        self.assertTrue(config_file.exists())
        with open(config_file) as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config, run_config)

    def test_cleanup_marks_experiment_complete(self):
        """Test that cleanup marks experiments as completed - KEY FUNCTIONALITY."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), \
             patch('ariadne.ariadne.get_git_hash', return_value=None):
            exp_id, _ = self.theseus.start(run_config, prefix="cleanup_test")

        # Verify initially incomplete
        exp = self.theseus.get_by_id(exp_id)
        self.assertFalse(exp.completed)
        self.assertIsNone(exp.end_timestamp)

        # Call cleanup
        self.theseus._cleanup(exp_id)

        # Check that experiment is marked as complete
        exp = self.theseus.get_by_id(exp_id)
        self.assertTrue(exp.completed)
        self.assertIsNotNone(exp.end_timestamp)

    def test_cleanup_interrupted_experiment_stays_incomplete(self):
        """Test that cleanup doesn't mark interrupted experiments as complete - KEY FUNCTIONALITY."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), \
             patch('ariadne.ariadne.get_git_hash', return_value=None):
            exp_id, _ = self.theseus.start(run_config, prefix="interrupted_test")

        # Simulate interruption by setting the interrupted flag
        with patch.object(self.theseus, '_Theseus__interrupted', True):
            self.theseus._cleanup(exp_id)

        # Check that experiment stays incomplete
        exp = self.theseus.get_by_id(exp_id)
        self.assertFalse(exp.completed)
        self.assertIsNone(exp.end_timestamp)

        # Should still be incomplete
        exp = self.theseus.get_by_id(exp_id)
        self.assertFalse(exp.completed)

    def test_start_with_prefix(self):
        """Test start method with prefix functionality."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), patch('ariadne.ariadne.get_git_hash', return_value=None):
            exp_id, run_folder = self.theseus.start(run_config, prefix="test_exp")

        # Verify database entry has the prefixed name
        exp = self.theseus.get_by_id(exp_id)
        self.assertTrue(exp.name.startswith("test_exp_"))

    def test_start_without_prefix(self):
        """Test start method without prefix (auto-generated name)."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), patch('ariadne.ariadne.get_git_hash', return_value=None):
            exp_id, run_folder = self.theseus.start(run_config)

        # Verify experiment was created
        self.assertIsInstance(exp_id, int)
        self.assertTrue(run_folder.exists())

        # Verify database entry has auto-generated name
        exp = self.theseus.get_by_id(exp_id)
        self.assertEqual(exp.name, config_to_name(run_config))

    def test_get_experiments_by_name(self):
        """Test getting experiments by name pattern."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), patch('ariadne.ariadne.get_git_hash', return_value=None):
            self.theseus.start(run_config, prefix="test_exp_1")
            self.theseus.start(run_config, prefix="test_exp_2")
            self.theseus.start(run_config, prefix="other_exp")

        results = self.theseus.get("test_exp")
        self.assertEqual(len(results), 2)

        names = [r.name for r in results]
        # Check that the names contain the prefix we expect
        self.assertTrue(any("test_exp_1" in name for name in names))
        self.assertTrue(any("test_exp_2" in name for name in names))
        self.assertFalse(any("other_exp" in name for name in names))

    def test_peek_returns_most_recent(self):
        """Test peek returns the most recent experiment."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), patch('ariadne.ariadne.get_git_hash', return_value=None):
            self.theseus.start(run_config, prefix="first_exp")
            exp_id_2, _ = self.theseus.start(run_config, prefix="second_exp")

        most_recent = self.theseus.peek()
        assert most_recent is not None
        self.assertEqual(most_recent.id, exp_id_2)
        self.assertTrue(most_recent.name.startswith("second_exp"))

    def test_peek_empty_database(self):
        """Test peek returns None for empty database."""
        result = self.theseus.peek()
        self.assertIsNone(result)

    def test_has_method(self):
        run_config1 = {"param": "value", "other_param": 42}
        run_config2 = {"param": "different", "other_param": 42}
        run_config3 = {"param": "value", "other_param": 100}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), patch('ariadne.ariadne.get_git_hash', return_value=None):
            self.theseus.start(run_config1, prefix="exp1")
            self.theseus.start(run_config2, prefix="exp2")
            self.theseus.start(run_config3, prefix="exp3")

        results = self.theseus.has({"param": "value"})
        self.assertEqual(len(results), 2)
        names = [r.name for r in results]
        self.assertTrue(any("exp1" in name for name in names))
        self.assertTrue(any("exp3" in name for name in names))

    def test_note_append_and_replace(self):
        """Test note functionality - append and replace."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), patch('ariadne.ariadne.get_git_hash', return_value=None):
            exp_id, _ = self.theseus.start(run_config, prefix="note_test", notes="Initial notes")

        # Test append
        self.theseus.note(exp_id, "Additional notes", append=True)
        exp = self.theseus.get_by_id(exp_id)
        self.assertEqual(exp.notes, "Initial notes\nAdditional notes")

        # Test replace
        self.theseus.note(exp_id, "Replacement notes", append=False)
        exp = self.theseus.get_by_id(exp_id)
        self.assertEqual(exp.notes, "Replacement notes")

    def test_delete_experiment(self):
        """Test deleting an experiment removes DB entry and folder."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), patch('ariadne.ariadne.get_git_hash', return_value=None):
            exp_id, run_folder = self.theseus.start(run_config, prefix="delete_test")

        # Ensure folder exists
        self.assertTrue(run_folder.exists())

        # Delete experiment
        with patch('builtins.print'):  # Suppress print output
            self.theseus.delete(exp_id)

        # Check that folder is gone
        self.assertFalse(run_folder.exists())

        # Check that DB entry is gone
        with self.assertRaises(ValueError):
            self.theseus.get_by_id(exp_id)

    def test_start_test_functionality(self):
        """Test start_test method."""
        # Test noop mode
        exp_id, run_folder = self.theseus.start_test(noop=True)
        self.assertEqual(exp_id, -1)
        self.assertEqual(run_folder, Path(os.devnull))

        # Test actual temp folder creation
        exp_id, run_folder = self.theseus.start_test(noop=False)
        self.assertEqual(exp_id, -1)
        self.assertTrue(run_folder.exists())

        # Clean up
        if run_folder.exists():
            shutil.rmtree(run_folder)


class TestExceptionHandling(unittest.TestCase):
    """Test exception and error handling scenarios - KEY FUNCTIONALITY."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.exp_dir = Path(self.temp_dir) / "experiments"
        self.theseus = Theseus(
            db_path=self.db_path,
            exp_dir=self.exp_dir,
            loglevel=Theseus.LogLevel.NONE
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.theseus._cleanup(-1)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_start_cleanup_on_database_error(self):
        """Test that start cleans up temp folder if database error occurs - KEY FUNCTIONALITY."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), patch('ariadne.ariadne.get_git_hash', return_value=None):

            # Mock the cursor.execute to raise an error
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = mock_connect.return_value.__enter__.return_value
                mock_cursor = mock_conn.cursor.return_value
                mock_cursor.execute.side_effect = sqlite3.Error("Simulated database error")

                with self.assertRaises(sqlite3.Error):
                    self.theseus.start(run_config, prefix="failing_exp")

            # Check that no temporary folders are left behind
            temp_folders = []
            if self.exp_dir.exists():
                temp_folders = [f for f in os.listdir(self.exp_dir) if f.startswith("failing_exp.tmp_")]
            self.assertEqual(len(temp_folders), 0)

    def test_multiple_experiments_with_same_prefix(self):
        """Test that multiple experiments can be created with the same prefix - KEY FUNCTIONALITY."""
        run_config = {"param": "value"}

        with patch('ariadne.ariadne.get_jj_changeset', return_value=None), patch('ariadne.ariadne.get_git_hash', return_value=None):

            # Start first experiment and complete it
            first_id, _ = self.theseus.start(run_config, prefix="multi_test")
            self.theseus._cleanup(first_id)

            # Start second experiment (leave incomplete)
            second_id, second_folder = self.theseus.start(run_config, prefix="multi_test")

            # Start third experiment (leave incomplete)
            third_id, third_folder = self.theseus.start(run_config, prefix="multi_test")

            # All experiments should have unique IDs and folders
            self.assertNotEqual(first_id, second_id)
            self.assertNotEqual(second_id, third_id)
            self.assertNotEqual(second_folder, third_folder)

            # All should be retrievable by prefix
            experiments = self.theseus.get("multi_test")
            self.assertEqual(len(experiments), 3)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=1)