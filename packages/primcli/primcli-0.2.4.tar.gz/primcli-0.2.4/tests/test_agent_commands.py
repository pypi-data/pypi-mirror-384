from unittest.mock import Mock
from rich.table import Table
from prim_cli.commands.agent import (
    agents_list,
    agent_info,
    agent_create,
    agent_update,
    agent_delete,
)


class TestAgentsList:
    """Test the agents_list command."""

    def test_agents_list_success_with_basic_view(
        self,
        mock_agents_list,
        mock_agent_repository,
        mock_print_functions,
        mock_console,
    ):
        """Test successful agents list with basic view."""
        # Arrange
        mock_agent_repository.get.return_value = mock_agents_list

        # Act
        agents_list(all=False)

        # Assert
        mock_print_functions["info"].assert_called_once_with("Searching for agents...")
        mock_print_functions["success"].assert_called_once_with("Found 3 agents")
        mock_console.print.assert_called_once()

        # Verify table was created with correct structure
        table_call = mock_console.print.call_args[0][0]
        assert isinstance(table_call, Table)
        assert len(table_call.columns) == 2  # Name, Updated
        assert len(table_call.rows) == 3

    def test_agents_list_success_with_detailed_view(
        self,
        mock_agents_list,
        mock_agent_repository,
        mock_print_functions,
        mock_console,
    ):
        """Test successful agents list with detailed view."""
        # Arrange
        mock_agent_repository.get.return_value = mock_agents_list

        # Act
        agents_list(all=True)

        # Assert
        mock_print_functions["info"].assert_called_once_with("Searching for agents...")
        mock_print_functions["success"].assert_called_once_with("Found 3 agents")
        mock_console.print.assert_called_once()

        # Verify detailed table was created
        table_call = mock_console.print.call_args[0][0]
        assert isinstance(table_call, Table)
        assert len(table_call.columns) == 4  # Name, Created, Updated, ID
        assert len(table_call.rows) == 3

    def test_agents_list_no_agents_found(
        self, mock_agent_repository, mock_print_functions
    ):
        """Test agents list when no agents are found."""
        # Arrange
        mock_agent_repository.get.return_value = []

        # Act
        agents_list(all=False)

        # Assert
        mock_print_functions["info"].assert_called_once_with("Searching for agents...")
        mock_print_functions["error"].assert_called_once_with("No agents found.")


class TestAgentInfo:
    """Test the agent_info command."""

    def test_agent_info_success_by_name(
        self,
        mock_agent,
        mock_agent_repository,
        mock_console,
        mock_agent_environment_repository_for_agent,
        mock_environment,
    ):
        """Test successful agent info retrieval by name."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_environment_repository_for_agent.get_by_id.return_value = (
            mock_environment
        )

        # Act
        agent_info("Test Agent")

        # Assert
        mock_agent_repository.get_by_name_or_id.assert_called_once_with("Test Agent")
        mock_agent_environment_repository_for_agent.get_by_id.assert_called_once_with(
            "test-env-id-123"
        )
        mock_console.print.assert_called_once()

        # Verify table was created
        table_call = mock_console.print.call_args[0][0]
        assert isinstance(table_call, Table)

    def test_agent_info_success_by_id(
        self,
        mock_agent,
        mock_agent_repository,
        mock_agent_environment_repository_for_agent,
        mock_environment,
    ):
        """Test successful agent info retrieval by ID."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_environment_repository_for_agent.get_by_id.return_value = (
            mock_environment
        )

        # Act
        agent_info("test-agent-id-123")

        # Assert
        mock_agent_repository.get_by_name_or_id.assert_called_once_with(
            "test-agent-id-123"
        )
        mock_agent_environment_repository_for_agent.get_by_id.assert_called_once_with(
            "test-env-id-123"
        )

    def test_agent_info_agent_not_found(
        self, mock_agent_repository, mock_print_functions
    ):
        """Test agent info when agent is not found."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = None

        # Act
        agent_info("NonExistentAgent")

        # Assert
        mock_agent_repository.get_by_name_or_id.assert_called_once_with(
            "NonExistentAgent"
        )
        mock_print_functions["error"].assert_called_once_with(
            "Agent with name or ID 'NonExistentAgent' not found."
        )

    def test_agent_info_with_no_voice(
        self,
        mock_agent,
        mock_agent_repository,
        mock_console,
        mock_agent_environment_repository_for_agent,
        mock_environment,
    ):
        """Test agent info when agent has no voice."""
        # Arrange
        mock_agent.default_voice_id = None
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_environment_repository_for_agent.get_by_id.return_value = (
            mock_environment
        )

        # Act
        agent_info("Test Agent")

        # Assert
        mock_agent_environment_repository_for_agent.get_by_id.assert_called_once_with(
            "test-env-id-123"
        )
        mock_console.print.assert_called_once()

    def test_agent_info_voice_not_found(
        self,
        mock_agent,
        mock_agent_repository,
        mock_console,
        mock_agent_environment_repository_for_agent,
        mock_environment,
    ):
        """Test agent info when voice is not found."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_environment_repository_for_agent.get_by_id.return_value = (
            mock_environment
        )

        # Act
        agent_info("Test Agent")

        # Assert
        mock_agent_environment_repository_for_agent.get_by_id.assert_called_once_with(
            "test-env-id-123"
        )
        mock_console.print.assert_called_once()


class TestAgentCreate:
    """Test the agent_create command."""

    def test_agent_create_success_with_voice(
        self,
        mock_agent_repository,
        mock_prompt,
        mock_print_functions,
    ):
        """Test successful agent creation with voice."""
        # Arrange
        mock_prompt.side_effect = ["New Agent", "A new test agent", "Test Voice"]
        mock_agent_repository.create.return_value = Mock()

        # Act
        agent_create()

        # Assert
        assert mock_prompt.call_count == 3
        mock_agent_repository.create.assert_called_once()
        mock_print_functions["success"].assert_called_once_with(
            "Agent created successfully!"
        )

    def test_agent_create_success_without_voice(
        self, mock_agent_repository, mock_prompt, mock_print_functions
    ):
        """Test successful agent creation without voice."""
        # Arrange
        mock_prompt.side_effect = ["New Agent", "A new test agent", ""]
        mock_agent_repository.create.return_value = Mock()

        # Act
        agent_create()

        # Assert
        assert mock_prompt.call_count == 3
        mock_agent_repository.create.assert_called_once()
        mock_print_functions["success"].assert_called_once_with(
            "Agent created successfully!"
        )

    def test_agent_create_with_invalid_voice_retry(
        self,
        mock_agent_repository,
        mock_prompt,
        mock_print_functions,
    ):
        """Test agent creation with voice (no validation retry needed)."""
        # Arrange
        mock_prompt.side_effect = [
            "New Agent",
            "A new test agent",
            "Test Voice",
        ]
        mock_agent_repository.create.return_value = Mock()

        # Act
        agent_create()

        # Assert
        assert mock_prompt.call_count == 3  # Name, description, voice
        mock_agent_repository.create.assert_called_once()
        mock_print_functions["success"].assert_called_once_with(
            "Agent created successfully!"
        )

    def test_agent_create_failure(
        self, mock_agent_repository, mock_prompt, mock_print_functions
    ):
        """Test agent creation failure."""
        # Arrange
        mock_prompt.side_effect = ["New Agent", "A new test agent", ""]
        mock_agent_repository.create.return_value = None

        # Act
        agent_create()

        # Assert
        mock_agent_repository.create.assert_called_once()
        mock_print_functions["error"].assert_called_once_with("Failed to create agent.")


class TestAgentUpdate:
    """Test the agent_update command."""

    def test_agent_update_success(
        self,
        mock_agent,
        mock_agent_repository,
        mock_prompt,
        mock_print_functions,
    ):
        """Test successful agent update."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_prompt.side_effect = ["Updated Agent", "Updated description", "New Voice"]
        mock_agent_repository.update_by_id.return_value = Mock()

        # Act
        agent_update("Test Agent")

        # Assert
        mock_agent_repository.get_by_name_or_id.assert_called_once_with("Test Agent")
        mock_agent_repository.update_by_id.assert_called_once()
        mock_print_functions["success"].assert_called_once_with(
            "Agent updated successfully!"
        )

    def test_agent_update_agent_not_found(
        self, mock_agent_repository, mock_print_functions
    ):
        """Test agent update when agent is not found."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = None

        # Act
        agent_update("NonExistentAgent")

        # Assert
        mock_agent_repository.get_by_name_or_id.assert_called_once_with(
            "NonExistentAgent"
        )
        mock_print_functions["error"].assert_called_once_with(
            "Agent with name or ID 'NonExistentAgent' not found."
        )

    def test_agent_update_with_current_voice(
        self,
        mock_agent,
        mock_agent_repository,
        mock_prompt,
        mock_print_functions,
    ):
        """Test agent update with current voice as default."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_prompt.side_effect = ["Updated Agent", "Updated description", "Test Voice"]
        mock_agent_repository.update_by_id.return_value = Mock()

        # Act
        agent_update("Test Agent")

        # Assert
        mock_agent_repository.update_by_id.assert_called_once()
        mock_print_functions["success"].assert_called_once_with(
            "Agent updated successfully!"
        )

    def test_agent_update_failure(
        self,
        mock_agent,
        mock_agent_repository,
        mock_prompt,
        mock_print_functions,
    ):
        """Test agent update failure."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_prompt.side_effect = ["Updated Agent", "Updated description", "Test Voice"]
        mock_agent_repository.update_by_id.return_value = None

        # Act
        agent_update("Test Agent")

        # Assert
        mock_agent_repository.update_by_id.assert_called_once()
        mock_print_functions["error"].assert_called_once_with("Failed to update agent.")


class TestAgentDelete:
    """Test the agent_delete command."""

    def test_agent_delete_success(
        self, mock_agent, mock_agent_repository, mock_confirm, mock_print_functions
    ):
        """Test successful agent deletion."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_confirm.return_value = True
        mock_agent_repository.delete_by_id.return_value = True

        # Act
        agent_delete("Test Agent")

        # Assert
        mock_agent_repository.get_by_name_or_id.assert_called_once_with("Test Agent")
        mock_confirm.assert_called_once_with(
            "Are you sure you want to delete agent 'Test Agent'?"
        )
        mock_agent_repository.delete_by_id.assert_called_once_with("test-agent-id-123")
        mock_print_functions["success"].assert_called_once_with(
            "Agent 'Test Agent' deleted successfully."
        )

    def test_agent_delete_agent_not_found(
        self, mock_agent_repository, mock_print_functions
    ):
        """Test agent deletion when agent is not found."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = None

        # Act
        agent_delete("NonExistentAgent")

        # Assert
        mock_agent_repository.get_by_name_or_id.assert_called_once_with(
            "NonExistentAgent"
        )
        mock_print_functions["info"].assert_called_once_with(
            "Unable to find agent by name or id: NonExistentAgent"
        )

    def test_agent_delete_user_cancels(
        self, mock_agent, mock_agent_repository, mock_confirm
    ):
        """Test agent deletion when user cancels."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_confirm.return_value = False

        # Act
        agent_delete("Test Agent")

        # Assert
        mock_confirm.assert_called_once_with(
            "Are you sure you want to delete agent 'Test Agent'?"
        )
        mock_agent_repository.delete_by_id.assert_not_called()

    def test_agent_delete_failure(
        self, mock_agent, mock_agent_repository, mock_confirm, mock_print_functions
    ):
        """Test agent deletion failure."""
        # Arrange
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_confirm.return_value = True
        mock_agent_repository.delete_by_id.return_value = False

        # Act
        agent_delete("Test Agent")

        # Assert
        mock_agent_repository.delete_by_id.assert_called_once_with("test-agent-id-123")
        mock_print_functions["error"].assert_called_once_with(
            "Failed to delete agent 'Test Agent'."
        )


class TestAgentCommandsIntegration:
    """Integration tests for agent commands."""

    def test_agent_commands_with_mocked_api_calls(
        self,
        mock_agents_list,
        mock_agent,
        mock_agent_repository,
        mock_prompt,
        mock_confirm,
        mock_agent_environment_repository_for_agent,
        mock_environment,
    ):
        """Test a complete workflow of agent commands with mocked API calls."""
        # Test list command
        mock_agent_repository.get.return_value = mock_agents_list
        agents_list(all=False)

        # Test info command
        mock_agent_repository.get_by_name_or_id.return_value = mock_agent
        mock_agent_environment_repository_for_agent.get_by_id.return_value = (
            mock_environment
        )
        agent_info("Test Agent")

        # Test create command
        mock_prompt.side_effect = ["New Agent", "Description", "Test Voice"]
        mock_agent_repository.create.return_value = Mock()
        agent_create()

        # Test update command
        mock_prompt.side_effect = ["Updated Agent", "Updated Description", "New Voice"]
        mock_agent_repository.update_by_id.return_value = Mock()
        agent_update("Test Agent")

        # Test delete command
        mock_confirm.return_value = True
        mock_agent_repository.delete_by_id.return_value = True
        agent_delete("Test Agent")

        # Verify all API calls were made
        assert mock_agent_repository.get.called
        assert mock_agent_repository.get_by_name_or_id.called
        assert mock_agent_repository.create.called
        assert mock_agent_repository.update_by_id.called
        assert mock_agent_repository.delete_by_id.called
