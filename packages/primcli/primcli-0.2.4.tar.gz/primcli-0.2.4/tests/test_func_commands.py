import pytest
import base64
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from rich.table import Table
from prim_cli.commands.func import (
    func_list,
    func_info,
    func_create,
    func_update,
    func_delete,
    func_deploy,
)


class TestFuncList:
    """Test the func_list command."""

    def test_func_list_success(
        self,
        mock_functions_list,
        mock_agent,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_print_functions,
        mock_func_console,
    ):
        """Test successful functions list."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get.return_value = mock_functions_list

        # Act
        func_list("Test Agent")

        # Assert
        mock_func_print_functions["info"].assert_called_once_with(
            "Getting functions for Test Agent..."
        )
        mock_func_agent_repository.get_by_name_or_id.assert_called_once_with(
            "Test Agent"
        )
        mock_agent_function_repository.get.assert_called_once()
        mock_func_console.print.assert_called_once()

        # Verify table was created with correct structure
        table_call = mock_func_console.print.call_args[0][0]
        assert isinstance(table_call, Table)
        assert len(table_call.columns) == 4  # Name, Language, Updated, ID
        assert len(table_call.rows) == 3

    def test_func_list_agent_not_found(
        self, mock_func_agent_repository, mock_func_print_functions
    ):
        """Test functions list when agent is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = None

        # Act
        func_list("NonExistentAgent")

        # Assert
        mock_func_print_functions["info"].assert_called_once_with(
            "Getting functions for NonExistentAgent..."
        )
        mock_func_print_functions["error"].assert_called_once_with(
            "Agent 'NonExistentAgent' not found."
        )


class TestFuncInfo:
    """Test the func_info command."""

    def test_func_info_success_by_name(
        self,
        mock_agent,
        mock_function,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_console,
        mock_func_confirm,
    ):
        """Test successful function info retrieval by name."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_func_confirm.return_value = False  # Don't view code

        # Act
        func_info("Test Agent", "Test Function")

        # Assert
        mock_func_agent_repository.get_by_name_or_id.assert_called_once_with(
            "Test Agent"
        )
        mock_agent_function_repository.get_by_name_or_id.assert_called_once_with(
            "Test Function"
        )
        mock_func_console.print.assert_called_once()

        # Verify table was created
        table_call = mock_func_console.print.call_args[0][0]
        assert isinstance(table_call, Table)

    def test_func_info_success_by_id(
        self,
        mock_agent,
        mock_function,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_console,
        mock_func_confirm,
    ):
        """Test successful function info retrieval by ID."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_func_confirm.return_value = False  # Don't view code

        # Act
        func_info("test-agent-id", "test-function-id")

        # Assert
        mock_func_agent_repository.get_by_name_or_id.assert_called_once_with(
            "test-agent-id"
        )
        mock_agent_function_repository.get_by_name_or_id.assert_called_once_with(
            "test-function-id"
        )

    def test_func_info_agent_not_found(
        self, mock_func_agent_repository, mock_func_print_functions
    ):
        """Test function info when agent is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = None

        # Act
        func_info("NonExistentAgent", "Test Function")

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Agent 'NonExistentAgent' not found."
        )

    def test_func_info_function_not_found(
        self,
        mock_agent,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_print_functions,
    ):
        """Test function info when function is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = None

        # Act
        func_info("Test Agent", "NonExistentFunction")

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Function 'NonExistentFunction' not found."
        )

    def test_func_info_with_zip_code_and_save(
        self,
        mock_agent,
        mock_function_zip,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_confirm,
        mock_func_console,
    ):
        """Test function info with zip code and user chooses to save."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = (
            mock_function_zip
        )
        mock_func_confirm.side_effect = [True, True]  # View code, save zip

        with patch("builtins.open", mock_open()) as mock_file:
            # Act
            func_info("Test Agent", "Test Function")

            # Assert
            mock_func_confirm.assert_called()
            mock_file.assert_called_once()

    def test_func_info_with_plain_text_code(
        self,
        mock_agent,
        mock_function_plain,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_confirm,
    ):
        """Test function info with plain text code."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = (
            mock_function_plain
        )
        mock_func_confirm.side_effect = [True, True]  # View code, remove temp file

        with (
            patch("tempfile.NamedTemporaryFile") as mock_temp,
            patch("os.remove") as mock_remove,
        ):
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test.py"

            # Act
            func_info("Test Agent", "Test Function")

            # Assert
            mock_temp.assert_called_once()
            mock_remove.assert_called_once_with("/tmp/test.py")

    def test_func_info_no_code(
        self,
        mock_agent,
        mock_function_no_code,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_confirm,
        mock_func_print_functions,
    ):
        """Test function info when function has no code."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = (
            mock_function_no_code
        )
        mock_func_confirm.return_value = True  # View code

        # Act
        func_info("Test Agent", "Test Function")

        # Assert
        mock_func_print_functions["warning"].assert_called_once_with(
            "No code found for this function."
        )


class TestFuncCreate:
    """Test the func_create command."""

    def test_func_create_success_with_directory(
        self,
        mock_agent,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_package_function,
        mock_func_print_functions,
    ):
        """Test successful function creation with directory provided."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        created_function = Mock()
        created_function.name = "Created Function"
        mock_agent_function_repository.create.return_value = created_function
        mock_package_function.return_value = (b"zip content", "python")

        with (
            patch("prim_cli.commands.func.Path") as mock_path,
            patch("builtins.open", mock_open(read_data=b"zip content")),
            patch("base64.b64encode") as mock_b64encode,
        ):
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.expanduser.return_value = mock_path_instance
            # Set up the mock to return the same instance for any Path() call
            mock_path.return_value = mock_path_instance
            mock_b64encode.return_value.decode.return_value = "base64_encoded_content"

            # Act
            func_create("Test Agent", directory="/path/to/function")

            # Assert
            mock_func_agent_repository.get_by_name_or_id.assert_called_once_with(
                "Test Agent"
            )
            mock_package_function.assert_called_once_with(mock_path_instance)
            mock_agent_function_repository.create.assert_called_once()
            mock_func_print_functions["success"].assert_called_once_with(
                "Function 'Created Function' created successfully."
            )

    def test_func_create_success_with_prompt(
        self,
        mock_agent,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_package_function,
        mock_func_prompt,
        mock_func_print_functions,
    ):
        """Test successful function creation with directory prompted."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        created_function = Mock()
        created_function.name = "Created Function"
        mock_agent_function_repository.create.return_value = created_function
        mock_func_prompt.return_value = "/path/to/function"
        mock_package_function.return_value = (b"zip content", "python")
        mock_agent_function_repository.get.return_value = []

        with (
            patch("prim_cli.commands.func.Path") as mock_path,
            patch("builtins.open", mock_open(read_data=b"zip content")),
            patch("base64.b64encode") as mock_b64encode,
        ):
            # Pre-prompt Path instance (for initial check)
            pre_prompt_path_instance = Mock()
            pre_prompt_path_instance.exists.return_value = False
            pre_prompt_path_instance.expanduser.return_value = pre_prompt_path_instance
            pre_prompt_path_instance.__str__ = lambda s: "/pre/prompt/path"
            # Post-prompt Path instance (for after prompt)
            post_prompt_path_instance = Mock()
            post_prompt_path_instance.exists.return_value = True
            post_prompt_path_instance.expanduser.return_value = (
                post_prompt_path_instance
            )
            post_prompt_path_instance.__str__ = lambda s: "/path/to/function"

            # Path() returns the correct instance based on the input path string
            def path_side_effect(arg):
                # If the argument is exactly the pre-prompt path string, return pre-prompt mock
                if arg == "/pre/prompt/path":
                    return pre_prompt_path_instance
                # Otherwise, always return post-prompt mock
                return post_prompt_path_instance

            mock_path.side_effect = path_side_effect
            mock_b64encode.return_value.decode.return_value = "base64_encoded_content"

            # Act
            func_create("Test Agent", directory=None)

            # Assert
            mock_func_prompt.assert_any_call("Enter function name")
            mock_func_prompt.assert_any_call("Enter directory path")
            assert mock_func_prompt.call_count == 2
            mock_package_function.assert_called_once_with(post_prompt_path_instance)
            mock_agent_function_repository.create.assert_called_once()
            mock_func_print_functions["success"].assert_called_once_with(
                f"Function '{created_function.name}' created successfully."
            )

    def test_func_create_agent_not_found(
        self, mock_func_agent_repository, mock_func_print_functions
    ):
        """Test function creation when agent is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = None

        # Act
        func_create("NonExistentAgent", directory="/path/to/function")

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Agent 'NonExistentAgent' not found."
        )

    def test_func_create_directory_not_found(
        self,
        mock_agent,
        mock_func_agent_repository,
        mock_func_prompt,
        mock_func_print_functions,
    ):
        """Test function creation when directory is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_func_prompt.return_value = "/nonexistent/path"

        with patch("prim_cli.commands.func.Path") as mock_path:
            # Pre-prompt Path instance (for initial check)
            pre_prompt_path_instance = Mock()
            pre_prompt_path_instance.exists.return_value = False
            pre_prompt_path_instance.expanduser.return_value = pre_prompt_path_instance
            pre_prompt_path_instance.__str__ = lambda s: "/nonexistent/path"
            # Post-prompt Path instance (for after prompt)
            post_prompt_path_instance = Mock()
            post_prompt_path_instance.exists.return_value = False
            post_prompt_path_instance.expanduser.return_value = (
                post_prompt_path_instance
            )
            post_prompt_path_instance.__str__ = lambda s: "/nonexistent/path"
            # Path() returns pre-prompt instance first, then post-prompt instance
            mock_path.side_effect = [
                pre_prompt_path_instance,
                post_prompt_path_instance,
            ]

            # Act
            func_create("Test Agent", directory=None)

            # Assert
            mock_func_print_functions["error"].assert_called_once_with(
                "Directory not found at '[cyan]/nonexistent/path[/cyan]'"
            )

    def test_func_create_failure(
        self,
        mock_agent,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_package_function,
        mock_func_print_functions,
    ):
        """Test function creation failure."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.create.return_value = None
        mock_package_function.return_value = (b"zip content", "python")

        with (
            patch("prim_cli.commands.func.Path") as mock_path,
            patch("builtins.open", mock_open(read_data=b"zip content")),
            patch("base64.b64encode") as mock_b64encode,
            patch("os.remove") as mock_remove,
        ):
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.expanduser.return_value = mock_path_instance
            # Set up the mock to return the same instance for any Path() call
            mock_path.return_value = mock_path_instance
            mock_b64encode.return_value.decode.return_value = "base64_encoded_content"

            # Act
            func_create("Test Agent", directory="/path/to/function")

            # Assert
            mock_package_function.assert_called_once_with(mock_path_instance)
            mock_func_print_functions["error"].assert_called_once_with(
                "Failed to create function for agent 'Test Agent'."
            )


class TestFuncUpdate:
    """Test the func_update command."""

    def test_func_update_success_with_directory(
        self,
        mock_agent,
        mock_function,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_agent_environment_repository,
        mock_package_function,
        mock_func_print_functions,
    ):
        """Test successful function update with directory provided."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_function_repository.update_by_id.return_value = mock_function
        mock_agent_environment_repository.get.return_value = []
        mock_package_function.return_value = (b"zip content", "python")

        with (
            patch("prim_cli.commands.func.Path") as mock_path,
            patch("builtins.open", mock_open(read_data=b"zip content")),
            patch("base64.b64encode") as mock_b64encode,
            patch("os.remove") as mock_remove,
        ):
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.expanduser.return_value = mock_path_instance
            # Set up the mock to return the same instance for any Path() call
            mock_path.return_value = mock_path_instance
            mock_b64encode.return_value.decode.return_value = "base64_encoded_content"

            # Act
            func_update("Test Agent", "Test Function", directory="/path/to/function")

            # Assert
            mock_func_agent_repository.get_by_name_or_id.assert_called_once_with(
                "Test Agent"
            )
            mock_agent_function_repository.get_by_name_or_id.assert_called_once_with(
                "Test Function"
            )
            mock_package_function.assert_called_once()
            mock_agent_function_repository.update_by_id.assert_called_once()
            mock_func_print_functions["success"].assert_called_once_with(
                "Function 'Test Function' updated successfully."
            )

    def test_func_update_agent_not_found(
        self, mock_func_agent_repository, mock_func_print_functions
    ):
        """Test function update when agent is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = None

        # Act
        func_update("NonExistentAgent", "Test Function", directory="/path/to/function")

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Agent 'NonExistentAgent' not found."
        )

    def test_func_update_function_not_found(
        self,
        mock_agent,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_print_functions,
    ):
        """Test function update when function is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = None

        # Act
        func_update("Test Agent", "NonExistentFunction", directory="/path/to/function")

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Function 'NonExistentFunction' not found."
        )

    def test_func_update_failure(
        self,
        mock_agent,
        mock_function,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_agent_environment_repository,
        mock_package_function,
        mock_func_print_functions,
    ):
        """Test function update failure."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_function_repository.update_by_id.return_value = None
        mock_agent_environment_repository.get.return_value = []
        mock_package_function.return_value = (b"zip content", "python")

        with (
            patch("prim_cli.commands.func.Path") as mock_path,
            patch("builtins.open", mock_open(read_data=b"zip content")),
            patch("base64.b64encode") as mock_b64encode,
            patch("os.remove") as mock_remove,
        ):
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.expanduser.return_value = mock_path_instance
            # Set up the mock to return the same instance for any Path() call
            mock_path.return_value = mock_path_instance
            mock_b64encode.return_value.decode.return_value = "base64_encoded_content"

            # Act
            func_update("Test Agent", "Test Function", directory="/path/to/function")

            # Assert
            mock_func_print_functions["error"].assert_called_once_with(
                "Failed to update function 'Test Function'."
            )


class TestFuncDelete:
    """Test the func_delete command."""

    def test_func_delete_success(
        self,
        mock_agent,
        mock_function,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_confirm,
        mock_func_print_functions,
    ):
        """Test successful function deletion."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_function_repository.delete_by_id.return_value = True
        mock_func_confirm.return_value = True

        # Act
        func_delete("Test Agent", "Test Function")

        # Assert
        mock_func_agent_repository.get_by_name_or_id.assert_called_once_with(
            "Test Agent"
        )
        mock_agent_function_repository.get_by_name_or_id.assert_called_once_with(
            "Test Function"
        )
        mock_func_confirm.assert_called_once_with(
            "Are you sure you want to delete function 'Test Function'?"
        )
        mock_agent_function_repository.delete_by_id.assert_called_once_with(
            mock_function.id
        )
        mock_func_print_functions["success"].assert_called_once_with(
            "Function 'Test Function' deleted successfully."
        )

    def test_func_delete_agent_not_found(
        self, mock_func_agent_repository, mock_func_print_functions
    ):
        """Test function deletion when agent is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = None

        # Act
        func_delete("NonExistentAgent", "Test Function")

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Agent 'NonExistentAgent' not found."
        )

    def test_func_delete_function_not_found(
        self,
        mock_agent,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_print_functions,
    ):
        """Test function deletion when function is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = None

        # Act
        func_delete("Test Agent", "NonExistentFunction")

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Function 'NonExistentFunction' not found."
        )

    def test_func_delete_user_cancels(
        self,
        mock_agent,
        mock_function,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_confirm,
    ):
        """Test function deletion when user cancels."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_func_confirm.return_value = False

        # Act
        func_delete("Test Agent", "Test Function")

        # Assert
        mock_func_confirm.assert_called_once_with(
            "Are you sure you want to delete function 'Test Function'?"
        )
        mock_agent_function_repository.delete_by_id.assert_not_called()

    def test_func_delete_failure(
        self,
        mock_agent,
        mock_function,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_confirm,
        mock_func_print_functions,
    ):
        """Test function deletion failure."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_function_repository.delete_by_id.return_value = False
        mock_func_confirm.return_value = True

        # Act
        func_delete("Test Agent", "Test Function")

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Failed to delete function 'Test Function'."
        )


class TestFuncDeploy:
    """Test the func_deploy command."""

    def test_func_deploy_success_with_env(
        self,
        mock_agent,
        mock_function,
        mock_environment,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_agent_environment_repository,
        mock_func_confirm,
        mock_func_print_functions,
    ):
        """Test successful function deployment with environment provided."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_environment_repository.get_by_name_or_id.return_value = (
            mock_environment
        )
        mock_agent_environment_repository.update_by_id.return_value = mock_environment
        mock_func_confirm.return_value = True

        # Act
        func_deploy("Test Agent", "Test Function", env_name_or_id="Test Environment")

        # Assert
        mock_func_agent_repository.get_by_name_or_id.assert_called_once_with(
            "Test Agent"
        )
        mock_agent_function_repository.get_by_name_or_id.assert_called_once_with(
            "Test Function"
        )
        mock_agent_environment_repository.get_by_name_or_id.assert_called_once_with(
            "Test Environment"
        )
        mock_func_confirm.assert_called_once_with(
            "Deploy function 'Test Function' to environment 'Test Environment'?",
            default=True,
        )
        mock_agent_environment_repository.update_by_id.assert_called_once()
        mock_func_print_functions["success"].assert_called_once_with(
            "Function 'Test Function' deployed to environment 'Test Environment' successfully."
        )

    def test_func_deploy_success_with_prompt(
        self,
        mock_agent,
        mock_function,
        mock_environment,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_agent_environment_repository,
        mock_func_prompt,
        mock_func_confirm,
        mock_func_print_functions,
    ):
        """Test successful function deployment with environment prompted."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_environment_repository.get_by_name_or_id.return_value = (
            mock_environment
        )
        mock_agent_environment_repository.update_by_id.return_value = mock_environment
        mock_func_prompt.return_value = "Test Environment"
        mock_func_confirm.return_value = True

        # Act
        func_deploy("Test Agent", "Test Function", env_name_or_id=None)

        # Assert
        mock_func_prompt.assert_called_once_with("Enter environment name or ID")
        mock_agent_environment_repository.get_by_name_or_id.assert_called_once_with(
            "Test Environment"
        )
        mock_func_print_functions["success"].assert_called_once_with(
            "Function 'Test Function' deployed to environment 'Test Environment' successfully."
        )

    def test_func_deploy_agent_not_found(
        self, mock_func_agent_repository, mock_func_print_functions
    ):
        """Test function deployment when agent is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = None

        # Act
        func_deploy(
            "NonExistentAgent", "Test Function", env_name_or_id="Test Environment"
        )

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Agent 'NonExistentAgent' not found."
        )

    def test_func_deploy_function_not_found(
        self,
        mock_agent,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_func_print_functions,
    ):
        """Test function deployment when function is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = None

        # Act
        func_deploy(
            "Test Agent", "NonExistentFunction", env_name_or_id="Test Environment"
        )

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Function 'NonExistentFunction' not found."
        )

    def test_func_deploy_environment_not_found(
        self,
        mock_agent,
        mock_function,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_agent_environment_repository,
        mock_func_prompt,
        mock_func_print_functions,
    ):
        """Test function deployment when environment is not found."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_environment_repository.get_by_name_or_id.return_value = None
        mock_func_prompt.return_value = "NonExistentEnvironment"

        # Act
        func_deploy("Test Agent", "Test Function", env_name_or_id=None)

        # Assert
        mock_func_prompt.assert_called_once_with("Enter environment name or ID")
        mock_func_print_functions["error"].assert_called_once_with(
            "Environment 'NonExistentEnvironment' not found."
        )

    def test_func_deploy_user_cancels(
        self,
        mock_agent,
        mock_function,
        mock_environment,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_agent_environment_repository,
        mock_func_confirm,
        mock_func_print_functions,
    ):
        """Test function deployment when user cancels."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_environment_repository.get_by_name_or_id.return_value = (
            mock_environment
        )
        mock_func_confirm.return_value = False

        # Act
        func_deploy("Test Agent", "Test Function", env_name_or_id="Test Environment")

        # Assert
        mock_func_confirm.assert_called_once_with(
            "Deploy function 'Test Function' to environment 'Test Environment'?",
            default=True,
        )
        mock_agent_environment_repository.update_by_id.assert_not_called()
        mock_func_print_functions["info"].assert_called_once_with(
            "Deployment cancelled."
        )

    def test_func_deploy_failure(
        self,
        mock_agent,
        mock_function,
        mock_environment,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_agent_environment_repository,
        mock_func_confirm,
        mock_func_print_functions,
    ):
        """Test function deployment failure."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_environment_repository.get_by_name_or_id.return_value = (
            mock_environment
        )
        mock_agent_environment_repository.update_by_id.return_value = None
        mock_func_confirm.return_value = True

        # Act
        func_deploy("Test Agent", "Test Function", env_name_or_id="Test Environment")

        # Assert
        mock_func_print_functions["error"].assert_called_once_with(
            "Failed to deploy function 'Test Function' to environment 'Test Environment'."
        )


class TestFuncCommandsIntegration:
    """Integration tests for func commands."""

    def test_func_commands_with_mocked_api_calls(
        self,
        mock_functions_list,
        mock_agent,
        mock_function,
        mock_environment,
        mock_func_agent_repository,
        mock_agent_function_repository,
        mock_agent_environment_repository,
        mock_func_prompt,
        mock_func_confirm,
        mock_func_print_functions,
        mock_func_console,
        mock_package_function,
    ):
        """Test func commands with mocked API calls."""
        # Arrange
        mock_func_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_function_repository.get.return_value = mock_functions_list
        mock_agent_function_repository.get_by_name_or_id.return_value = mock_function
        mock_agent_function_repository.create.return_value = mock_function
        mock_agent_function_repository.update_by_id.return_value = mock_function
        mock_agent_function_repository.delete_by_id.return_value = True
        mock_agent_environment_repository.get.return_value = [mock_environment]
        mock_agent_environment_repository.get_by_name_or_id.return_value = (
            mock_environment
        )
        mock_agent_environment_repository.update_by_id.return_value = mock_environment
        mock_func_prompt.return_value = "Test Environment"
        mock_func_confirm.return_value = True
        mock_package_function.return_value = (b"zip content", "python")

        with (
            patch("prim_cli.commands.func.Path") as mock_path,
            patch("builtins.open", mock_open(read_data=b"zip content")),
            patch("base64.b64encode") as mock_b64encode,
        ):
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.expanduser.return_value = mock_path_instance
            mock_path.return_value = mock_path_instance
            mock_b64encode.return_value.decode.return_value = "base64_encoded_content"

            # Act & Assert - Test all commands
            func_list("Test Agent")
            func_info("Test Agent", "Test Function")
            func_create("Test Agent", directory="/path/to/function")
            func_update("Test Agent", "Test Function", directory="/path/to/function")
            func_delete("Test Agent", "Test Function")
            func_deploy(
                "Test Agent", "Test Function", env_name_or_id="Test Environment"
            )

            # Verify all commands executed successfully
            assert mock_func_console.print.call_count >= 2
            assert mock_func_print_functions["success"].call_count >= 3
