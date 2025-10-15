import unittest
import tempfile
import shutil
import subprocess
import sys
import os
from pathlib import Path
from textwrap import dedent

from ariadne import Theseus
from ariadne.ariadne import get_git_hash, get_jj_changeset


class TestExceptionHandlingEndToEnd(unittest.TestCase):
    """End-to-end tests for exception handling and resume functionality."""

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

    def _create_test_script(self, script_name: str, script_content: str) -> Path:
        """Create a test script in the temp directory."""
        script_path = Path(self.temp_dir) / script_name
        with open(script_path, 'w') as f:
            f.write(script_content)
        return script_path

    def test_exception_leaves_experiment_incomplete(self):
        """Test that a script raising an exception leaves the experiment incomplete."""

        # Create a script that raises an exception
        ariadne_parent = Path(__file__).parent
        failing_script = self._create_test_script("failing_script.py", dedent(f'''
            import sys
            sys.path.insert(0, "{ariadne_parent}")

            from ariadne import Theseus
            from pathlib import Path

            # Initialize Theseus with the same DB and exp_dir
            theseus = Theseus(
                db_path=Path("{self.db_path}"),
                exp_dir=Path("{self.exp_dir}"),
                loglevel=Theseus.LogLevel.NONE
            )

            # Start an experiment
            exp_id, run_folder = theseus.start({{"param": "value"}}, "failing_exp", "This will fail")

            # Do some work
            print(f"Started experiment {{exp_id}} in {{run_folder}}")

            # Simulate an exception during the experiment
            raise ValueError("Simulated failure during experiment")
        '''))

        # Run the failing script as a subprocess
        result = subprocess.run([sys.executable, str(failing_script)],
                              capture_output=True, text=True)

        # The script should have failed with non-zero exit code
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ValueError: Simulated failure during experiment", result.stderr)

        # Check that the experiment exists but is incomplete
        experiments = self.theseus.get("failing_exp")
        self.assertEqual(len(experiments), 1)

        exp = experiments[0]
        self.assertTrue(exp.name.startswith("failing_exp"))
        self.assertFalse(exp.completed, "Experiment should be incomplete due to exception")
        self.assertIsNone(exp.end_timestamp, "End timestamp should be None for incomplete experiment")

    def test_successful_run_marks_experiment_complete(self):
        """Test that a successful script marks the experiment as complete."""

        # Create a script that completes successfully
        ariadne_parent = Path(__file__).parent
        success_script = self._create_test_script("success_script.py", dedent(f'''
            import sys
            sys.path.insert(0, "{ariadne_parent}")

            from ariadne import Theseus
            from pathlib import Path

            # Initialize Theseus with the same DB and exp_dir
            theseus = Theseus(
                db_path=Path("{self.db_path}"),
                exp_dir=Path("{self.exp_dir}"),
                loglevel=Theseus.LogLevel.NONE
            )

            # Start an experiment
            exp_id, run_folder = theseus.start({{"param": "value"}}, "success_exp", "This will succeed")

            # Do some work
            print(f"Started experiment {{exp_id}} in {{run_folder}}")

            # Exit normally - this should trigger cleanup and mark as complete
            print("Experiment completed successfully")
        '''))

        # Run the successful script as a subprocess
        result = subprocess.run([sys.executable, str(success_script)],
                              capture_output=True, text=True)

        # The script should have succeeded
        self.assertEqual(result.returncode, 0)
        self.assertIn("Experiment completed successfully", result.stdout)

        # Check that the experiment is marked as complete
        experiments = self.theseus.get("success_exp")
        self.assertEqual(len(experiments), 1)

        exp = experiments[0]
        self.assertTrue(exp.completed, "Experiment should be complete for successful run")
        self.assertIsNotNone(exp.end_timestamp, "End timestamp should be set for completed experiment")

    def test_keyboard_interrupt_leaves_experiment_incomplete(self):
        """Test that KeyboardInterrupt (Ctrl+C) leaves experiment incomplete."""

        # Create a script that simulates a KeyboardInterrupt
        ariadne_parent = Path(__file__).parent
        interrupt_script = self._create_test_script("interrupt_script.py", dedent(f'''
            import sys
            sys.path.insert(0, "{ariadne_parent}")

            from ariadne import Theseus
            from pathlib import Path
            import signal
            import os

            theseus = Theseus(
                db_path=Path("{self.db_path}"),
                exp_dir=Path("{self.exp_dir}"),
                loglevel=Theseus.LogLevel.NONE
            )

            exp_id, run_folder = theseus.start({{"param": "value"}}, "interrupt_exp", "Will be interrupted")
            print(f"INTERRUPT_EXP_ID:{{exp_id}}")

            # Simulate a KeyboardInterrupt (SIGINT)
            os.kill(os.getpid(), signal.SIGINT)
        '''))

        # Run the interrupt script
        result = subprocess.run([sys.executable, str(interrupt_script)],
                              capture_output=True, text=True)

        # Should have been interrupted (negative exit code or specific signal code)
        self.assertNotEqual(result.returncode, 0)

        # Extract experiment ID
        interrupt_exp_id = None
        for line in result.stdout.split('\n'):
            if line.startswith("INTERRUPT_EXP_ID:"):
                interrupt_exp_id = int(line.split(':')[1])
                break

        self.assertIsNotNone(interrupt_exp_id, "Interrupt script should have created an experiment")
        assert interrupt_exp_id is not None  # Type checker hint

        # Verify experiment is incomplete due to interruption
        exp = self.theseus.get_by_id(interrupt_exp_id)
        self.assertFalse(exp.completed, "Interrupted experiment should remain incomplete")
        self.assertIsNone(exp.end_timestamp, "Interrupted experiment should have no end timestamp")

class TestVersionControlIntegrationEndToEnd(unittest.TestCase):
    """End-to-end tests for version control (git/jujutsu) integration."""

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

    def _create_test_repo_script(self, repo_type: str, temp_repo_dir: str) -> Path:
        """Create a script that sets up a test repository and runs an experiment."""
        ariadne_parent = Path(__file__).parent

        if repo_type == "jj":
            setup_commands = [
                f"cd {temp_repo_dir}",
                "jj git init",
                "echo 'test file' > test.txt",
                "jj commit -m 'initial commit'"
            ]
        elif repo_type == "git":
            setup_commands = [
                f"cd {temp_repo_dir}",
                "git init",
                "git config user.email 'test@example.com'",
                "git config user.name 'Test User'",
                "echo 'test file' > test.txt",
                "git add test.txt",
                "git commit -m 'initial commit'"
            ]
        else:
            setup_commands = [f"cd {temp_repo_dir}"]  # No VCS setup

        script_content = dedent(f'''
            import sys
            import subprocess
            import os
            sys.path.insert(0, "{ariadne_parent}")

            from ariadne import Theseus
            from pathlib import Path

            # Set up repository
            commands = {setup_commands}
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="{temp_repo_dir}")
                    if result.returncode != 0 and "jj" in cmd:
                        # jj might not be available, that's expected for some tests
                        pass
                    elif result.returncode != 0:
                        print(f"Setup command failed: {{cmd}}")
                        print(f"Error: {{result.stderr}}")
                except Exception as e:
                    if "jj" in cmd:
                        # jj might not be available, that's expected for some tests
                        pass
                    else:
                        print(f"Exception running setup command: {{e}}")

            # Change to the repo directory before creating the experiment
            os.chdir("{temp_repo_dir}")

            # Initialize Theseus
            theseus = Theseus(
                db_path=Path("{self.db_path}"),
                exp_dir=Path("{self.exp_dir}"),
                loglevel=Theseus.LogLevel.DEBUG
            )

            # Start an experiment
            exp_id, run_folder = theseus.start({{"test_param": "value"}}, "vc_test", "Testing version control")
            print(f"VC_TEST_EXP_ID:{{exp_id}}")
        ''')

        script_path = Path(self.temp_dir) / f"{repo_type}_test_script.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        return script_path

    def test_jj_integration_when_available(self):
        """Test that jj changeset is captured when jj is available and repo is a jj repo."""

        # Create a temporary directory for the test repo
        temp_repo_dir = tempfile.mkdtemp()

        try:
            # Check if jj is available
            try:
                subprocess.run(["jj", "--version"], capture_output=True, check=True)
                jj_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                jj_available = False

            if not jj_available:
                self.skipTest("jj (Jujutsu) is not available on this system")

            script_path = self._create_test_repo_script("jj", temp_repo_dir)

            # Run the script
            result = subprocess.run([sys.executable, str(script_path)],
                                  capture_output=True, text=True)

            # Should succeed
            self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

            # Extract experiment ID
            exp_id = None
            for line in result.stdout.split('\n'):
                if line.startswith("VC_TEST_EXP_ID:"):
                    exp_id = int(line.split(':')[1])
                    break

            self.assertIsNotNone(exp_id, "Should have created an experiment")
            assert exp_id is not None

            # Check that experiment has jj changeset
            exp = self.theseus.get_by_id(exp_id)
            self.assertIsNotNone(exp.vc_hash, "Should have captured a version control hash")
            assert exp.vc_hash is not None
            self.assertTrue(len(exp.vc_hash) > 0, "Version control hash should not be empty")
        finally:
            shutil.rmtree(temp_repo_dir, ignore_errors=True)

    def test_git_fallback_when_jj_unavailable(self):
        """Test that git hash is captured when jj is not available but git is."""

        temp_repo_dir = tempfile.mkdtemp()

        try:
            try:
                subprocess.run(["git", "--version"], capture_output=True, check=True)
                git_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                git_available = False

            if not git_available:
                self.skipTest("git is not available on this system")

            # Create a script that sets up a git repo and temporarily makes jj unavailable
            ariadne_parent = Path(__file__).parent
            script_content = dedent(f'''
                import sys
                import subprocess
                import os
                sys.path.insert(0, "{ariadne_parent}")

                from ariadne import Theseus
                from pathlib import Path

                # Set up git repository
                os.chdir("{temp_repo_dir}")
                subprocess.run(["git", "init"], check=True)
                subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
                subprocess.run(["git", "config", "user.name", "Test User"], check=True)

                with open("test.txt", "w") as f:
                    f.write("test file")
                subprocess.run(["git", "add", "test.txt"], check=True)
                subprocess.run(["git", "commit", "-m", "initial commit"], check=True)

                # Temporarily modify PATH to exclude jj
                original_path = os.environ.get("PATH", "")
                # Create a custom PATH that doesn't include jj
                path_dirs = original_path.split(os.pathsep)
                filtered_path = []
                for path_dir in path_dirs:
                    # Skip directories that might contain jj
                    jj_path = os.path.join(path_dir, "jj")
                    if not os.path.exists(jj_path):
                        filtered_path.append(path_dir)

                os.environ["PATH"] = os.pathsep.join(filtered_path)

                # Initialize Theseus and start experiment
                theseus = Theseus(
                    db_path=Path("{self.db_path}"),
                    exp_dir=Path("{self.exp_dir}"),
                    loglevel=Theseus.LogLevel.DEBUG
                )

                exp_id, run_folder = theseus.start({{"test_param": "value"}}, "git_fallback_test", "Testing git fallback")
                print(f"GIT_FALLBACK_EXP_ID:{{exp_id}}")

                # Restore original PATH
                os.environ["PATH"] = original_path
            ''')

            script_path = Path(self.temp_dir) / "git_fallback_script.py"
            with open(script_path, 'w') as f:
                f.write(script_content)

            # Run the script
            result = subprocess.run([sys.executable, str(script_path)],
                                  capture_output=True, text=True)

            # Should succeed
            self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

            # Extract experiment ID
            exp_id = None
            for line in result.stdout.split('\n'):
                if line.startswith("GIT_FALLBACK_EXP_ID:"):
                    exp_id = int(line.split(':')[1])
                    break

            self.assertIsNotNone(exp_id, "Should have created an experiment")
            assert exp_id is not None

            # Check that experiment has git hash
            exp = self.theseus.get_by_id(exp_id)
            self.assertIsNotNone(exp.vc_hash, "Should have captured a git hash")
            assert exp.vc_hash is not None
            self.assertTrue(len(exp.vc_hash) > 0, "Git hash should not be empty")
            # Git commit hashes are 40 character hex strings
            self.assertEqual(len(exp.vc_hash), 40, "Git hash should be 40 characters")
        finally:
            shutil.rmtree(temp_repo_dir, ignore_errors=True)

    def test_no_version_control_graceful_handling(self):
        """Test that experiments work gracefully when neither jj nor git are available."""

        temp_repo_dir = tempfile.mkdtemp()

        try:
            # Create a script that makes both jj and git unavailable
            ariadne_parent = Path(__file__).parent
            script_content = dedent(f'''
                import sys
                import subprocess
                import os
                sys.path.insert(0, "{ariadne_parent}")

                from ariadne import Theseus
                from pathlib import Path

                # Set working directory to a non-git directory
                os.chdir("{temp_repo_dir}")

                # Temporarily modify PATH to exclude both jj and git
                original_path = os.environ.get("PATH", "")
                # Create a custom PATH that excludes common VCS tools
                path_dirs = original_path.split(os.pathsep)
                filtered_path = []
                for path_dir in path_dirs:
                    jj_path = os.path.join(path_dir, "jj")
                    git_path = os.path.join(path_dir, "git")
                    if not os.path.exists(jj_path) and not os.path.exists(git_path):
                        filtered_path.append(path_dir)

                os.environ["PATH"] = os.pathsep.join(filtered_path)

                # Initialize Theseus and start experiment
                theseus = Theseus(
                    db_path=Path("{self.db_path}"),
                    exp_dir=Path("{self.exp_dir}"),
                    loglevel=Theseus.LogLevel.DEBUG
                )

                exp_id, run_folder = theseus.start({{"test_param": "value"}}, "no_vc_test", "Testing no version control")
                print(f"NO_VC_EXP_ID:{{exp_id}}")

                # Restore original PATH
                os.environ["PATH"] = original_path
            ''')

            script_path = Path(self.temp_dir) / "no_vc_script.py"
            with open(script_path, 'w') as f:
                f.write(script_content)

            # Run the script
            result = subprocess.run([sys.executable, str(script_path)],
                                  capture_output=True, text=True)

            # Should succeed despite no VCS
            self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

            # Extract experiment ID
            exp_id = None
            for line in result.stdout.split('\n'):
                if line.startswith("NO_VC_EXP_ID:"):
                    exp_id = int(line.split(':')[1])
                    break

            self.assertIsNotNone(exp_id, "Should have created an experiment even without VCS")
            assert exp_id is not None

            # Check that experiment was created but has no vc_hash
            exp = self.theseus.get_by_id(exp_id)
            self.assertIsNone(exp.vc_hash, "Should have no version control hash when VCS unavailable")

        finally:
            shutil.rmtree(temp_repo_dir, ignore_errors=True)

    def test_jj_preference_over_git(self):
        """Test that jj is preferred when both jj and git are available."""

        temp_repo_dir = tempfile.mkdtemp()

        try:
            # Check if both jj and git are available
            try:
                subprocess.run(["jj", "--version"], capture_output=True, check=True)
                jj_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                jj_available = False

            try:
                subprocess.run(["git", "--version"], capture_output=True, check=True)
                git_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                git_available = False

            if not (jj_available and git_available):
                self.skipTest("Both jj and git must be available for this test")

            # Create a script that sets up both git and jj repos
            ariadne_parent = Path(__file__).parent
            script_content = dedent(f'''
                import sys
                import subprocess
                import os
                sys.path.insert(0, "{ariadne_parent}")

                from ariadne import Theseus
                from pathlib import Path

                # Set up git repository first
                os.chdir("{temp_repo_dir}")
                subprocess.run(["git", "init"], check=True)
                subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
                subprocess.run(["git", "config", "user.name", "Test User"], check=True)

                with open("test.txt", "w") as f:
                    f.write("test file")
                subprocess.run(["git", "add", "test.txt"], check=True)
                subprocess.run(["git", "commit", "-m", "initial commit"], check=True)

                # Now set up jj on top of the git repo
                try:
                    subprocess.run(["jj", "git", "init", "--colocate"], check=True)
                    subprocess.run(["jj", "commit", "-m", "jj commit"], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Failed to set up jj: {{e}}")
                    sys.exit(1)

                # Initialize Theseus and start experiment
                theseus = Theseus(
                    db_path=Path("{self.db_path}"),
                    exp_dir=Path("{self.exp_dir}"),
                    loglevel=Theseus.LogLevel.DEBUG
                )

                exp_id, run_folder = theseus.start({{"test_param": "value"}}, "jj_preference_test", "Testing jj preference")
                print(f"JJ_PREFERENCE_EXP_ID:{{exp_id}}")
            ''')

            script_path = Path(self.temp_dir) / "jj_preference_script.py"
            with open(script_path, 'w') as f:
                f.write(script_content)

            # Run the script
            result = subprocess.run([sys.executable, str(script_path)],
                                  capture_output=True, text=True)

            # Should succeed
            self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

            # Extract experiment ID
            exp_id = None
            for line in result.stdout.split('\n'):
                if line.startswith("JJ_PREFERENCE_EXP_ID:"):
                    exp_id = int(line.split(':')[1])
                    break

            self.assertIsNotNone(exp_id, "Should have created an experiment")
            assert exp_id is not None  # Type checker hint

            # Check that experiment has a changeset (preferably from jj)
            exp = self.theseus.get_by_id(exp_id)
            self.assertIsNotNone(exp.vc_hash, "Should have captured a version control hash")
            assert exp.vc_hash is not None  # Type checker hint
            self.assertTrue(len(exp.vc_hash) > 0, "Version control hash should not be empty")

            # In a colocated jj/git setup, jj uses git-compatible commit IDs, so we can't
            # distinguish by format alone. However, we can verify that jj was preferred
            # by checking that the fallback message doesn't appear in the debug output.
            debug_output = result.stdout + result.stderr
            self.assertNotIn("'jj' not found or not a jj repo, trying git...", debug_output,
                           "Should not have fallen back to git when jj is available and set up")

        finally:
            shutil.rmtree(temp_repo_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)