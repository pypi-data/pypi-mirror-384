"""Integration tests for the SecOps CLI."""

import pytest
import subprocess
import json
import os
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


@pytest.mark.integration
def test_cli_search(cli_env, common_args):
    """Test the search command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + [
            "search",
            "--query",
            'metadata.event_type = "NETWORK_CONNECTION"',
            "--time-window",
            "1",
            "--max-events",
            "5",
        ]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert "events" in output
        assert "total_events" in output
    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_udm_search_view(cli_env, common_args):
    """Test the udm-search-view command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + [
            "udm-search-view",
            "--query",
            'metadata.event_type = "NETWORK_CONNECTION"',
            "--time-window",
            "1",
            "--max-events",
            "5",
        ]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        # The output should be a list
        assert isinstance(output, list)
        # Check for expected fields in the first response object
        if output and len(output) > 0:
            assert "complete" in output[0]
            # If there are events, check their structure
            if "events" in output[0] and "events" in output[0]["events"]:
                events = output[0]["events"]["events"]
                if events:
                    assert "metadata" in events[0].get("event", {})
                    assert "id" in events[0].get("event", {}).get("metadata")
    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_entity(cli_env, common_args):
    """Test the entity command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["entity", "--value", "8.8.8.8", "--time-window", "24"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # For entity command, we just verify it returned successfully
    # Output format can vary too much for detailed assertions
    assert result.stdout.strip() != ""
    assert "Error:" not in result.stderr


@pytest.mark.integration
def test_cli_parser_lifecycle(cli_env, common_args):
    """Test the parser command lifecycle (create, get, list, activate, deactivate, delete)."""
    test_log_type = "RESERVED_LOG_TYPE_1"

    parser_code_content = r"""
    filter {
        mutate {
          replace => {
            "event1.idm.read_only_udm.metadata.event_type" => "GENERIC_EVENT"
            "event1.idm.read_only_udm.metadata.vendor_name" =>  "ACME Labs"
          }
        }
        grok {
          match => {
            "message" => ["^(?P<_firstWord>[^\s]+)\s.*$"]
          }
          on_error => "_grok_message_failed"
        }
        if ![_grok_message_failed] {
          mutate {
            replace => {
              "event1.idm.read_only_udm.metadata.description" => "%{_firstWord}"
            }
          }
        }
        mutate {
          merge => {
            "@output" => "event1"
          }
        }
    }
    """

    # We might need to store the actual parser_id returned by create_parser
    # as Chronicle often assigns IDs. Let's assume the CLI outputs it and we parse it.
    created_parser_id = None

    try:
        # 1. Create a parser
        with tempfile.NamedTemporaryFile(
            suffix=".conf", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(parser_code_content)
            parser_code_file_path = temp_file.name

        create_cmd = (
            [
                "secops",  # Replace with your actual CLI entry point
            ]
            + common_args
            + [
                "parser",
                "create",
                "--log-type",
                test_log_type,  # Positional argument for log_type
                "--parser-code-file",
                parser_code_file_path,
                "--validated-on-empty-logs",  # Flag to set True
            ]
        )

        create_result = subprocess.run(
            create_cmd, env=cli_env, capture_output=True, text=True
        )

        assert (
            create_result.returncode == 0
        ), f"Parser creation failed: {create_result.stderr}\n{create_result.stdout}"

        # Parse the output to get the actual parser ID generated by Chronicle
        try:
            created_data = json.loads(create_result.stdout)
            # The API returns 'parserId', which is what we need to use for subsequent calls.
            created_parser_id = created_data.get("name").split("/")[-1]
            assert created_parser_id, "Failed to get parser ID from creation response."
        except json.JSONDecodeError:
            pytest.fail(
                f"Could not parse JSON from create command output: {create_result.stdout}"
            )

        # 2. Get the parser
        get_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["parser", "get", "--log-type", test_log_type, "--id", created_parser_id]
        )

        get_result = subprocess.run(
            get_cmd, env=cli_env, capture_output=True, text=True
        )

        assert (
            get_result.returncode == 0
        ), f"Get parser failed: {get_result.stderr}\n{get_result.stdout}"
        get_data = json.loads(get_result.stdout)
        assert get_data["name"].split("/")[-1] == created_parser_id
        assert get_data["name"].split("/")[-3] == test_log_type

        # 3. List parsers and verify our created parser is in the list
        list_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["parser", "list", "--log-type", test_log_type]
        )

        list_result = subprocess.run(
            list_cmd, env=cli_env, capture_output=True, text=True
        )

        assert (
            list_result.returncode == 0
        ), f"List parsers failed: {list_result.stderr}\n{list_result.stdout}"
        listed_parsers = json.loads(list_result.stdout)

        if len(listed_parsers) > 0:
            found_in_list = any(
                p.get("name").split("/")[-1] == created_parser_id
                for p in listed_parsers
            )
            assert (
                found_in_list
            ), f"Created parser {created_parser_id} not found in listed parsers for {test_log_type}"

        # Wait till state of parser changes
        time.sleep(5)

        # 4. Activate the parser (if applicable and testable - might require specific states)
        # Note: Activation typically makes a parser "live".
        # This step might depend on the parser's state and whether it's a "custom" or "release candidate".
        # For simplicity, we'll try activating the newly created one.
        activate_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "parser",
                "activate",
                "--log-type",
                test_log_type,
                "--id",
                created_parser_id,
            ]
        )
        activate_result = subprocess.run(
            activate_cmd, env=cli_env, capture_output=True, text=True
        )
        assert (
            activate_result.returncode == 0
        ), f"Parser activation failed: {activate_result.stderr}\n{activate_result.stdout}"

        # 5. Deactivate the parser
        deactivate_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "parser",
                "deactivate",
                "--log-type",
                test_log_type,
                "--id",
                created_parser_id,
            ]
        )
        deactivate_result = subprocess.run(
            deactivate_cmd, env=cli_env, capture_output=True, text=True
        )
        assert (
            deactivate_result.returncode == 0
        ), f"Parser deactivation failed: {deactivate_result.stderr}\n{deactivate_result.stdout}"

    finally:
        # Clean up: Attempt to delete the parser regardless of test outcome
        if created_parser_id:
            delete_cmd = (
                [
                    "secops",
                ]
                + common_args
                + [
                    "parser",
                    "delete",
                    "--log-type",
                    test_log_type,
                    "--id",
                    created_parser_id,
                    "--force",  # Use force to ensure deletion even if active
                ]
            )
            clean_up_result = subprocess.run(
                delete_cmd, env=cli_env, capture_output=True, text=True
            )
            if clean_up_result.returncode != 0:
                print(
                    f"WARNING: Cleanup deletion failed for {created_parser_id}: "
                    f"{clean_up_result.stderr}\n{clean_up_result.stdout}"
                )

        # Clean up temporary parser code file
        if "parser_code_file_path" in locals() and os.path.exists(
            parser_code_file_path
        ):
            os.unlink(parser_code_file_path)


@pytest.mark.integration
def test_cli_parser_list(cli_env, common_args):
    """Test the parser list command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["parser", "list"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert len(output) > 0
    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_parser_get(cli_env, common_args):
    """Test the rule get command (first need to find an existing rule ID)."""
    # First list rules to get a valid rule ID
    list_cmd = (
        [
            "secops",
        ]
        + common_args
        + ["parser", "list"]
    )

    list_result = subprocess.run(list_cmd, env=cli_env, capture_output=True, text=True)

    # Check that we have at least one rule to test with
    assert list_result.returncode == 0

    parsers = json.loads(list_result.stdout)
    if not len(parsers) > 0:
        pytest.skip("No parsers available to test the get command")

    # Get the first rule's ID
    parser_id = parsers[0]["name"].split("/")[-1]
    log_type = parsers[0]["name"].split("/")[-3]

    # Test the get command with this rule ID
    get_cmd = (
        [
            "secops",
        ]
        + common_args
        + ["parser", "get", "--log-type", log_type, "--id", parser_id]
    )

    get_result = subprocess.run(get_cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert get_result.returncode == 0

    # Try to parse the output as JSON
    parser_data = json.loads(get_result.stdout)
    assert "name" in parser_data
    assert parser_data["name"].endswith(parser_id)


@pytest.mark.integration
def test_cli_parser_run_evaluation(cli_env, common_args):
    """
    Test the 'parser run' command functionality, covering reading parser code
    and logs from files, and providing logs via multiple --log arguments.
    """
    test_log_type = f"RESERVED_LOG_TYPE_1"

    # Sample YARA-L parser code
    sample_parser_code = r"""
    filter {
        mutate {
          replace => {
            "event1.idm.read_only_udm.metadata.event_type" => "GENERIC_EVENT"
            "event1.idm.read_only_udm.metadata.vendor_name" =>  "ACME Labs"
          }
        }
        grok {
          match => {
            "message" => ["^(?P<_firstWord>[^\s]+)\s.*$"]
          }
          on_error => "_grok_message_failed"
        }
        if ![_grok_message_failed] {
          mutate {
            replace => {
              "event1.idm.read_only_udm.metadata.description" => "%{_firstWord}"
            }
          }
        }
        mutate {
          merge => {
            "@output" => "event1"
          }
        }
    }
    """

    # Sample log data for --logs-file
    sample_logs_file_content = """
    {"appDisplayName":"Azure Active Directory PowerShell","appId":"1b730912-1644-4b74-9bfd-dac224a7b894","appliedConditionalAccessPolicies":[],"clientAppUsed":"Mobile Apps and Desktop clients","conditionalAccessStatus":"success","correlationId":"8bdadb11-5851-4ff2-ad57-799c0149f606","createdDateTime":"2025-06-15T04:31:56Z","deviceDetail":{"browser":"Rich Client 5.2.8.0","deviceId":"","displayName":"","isCompliant":false,"isManaged":false,"operatingSystem":"Windows 8","trustType":""},"id":"ba6e48d0-85e9-45b0-9ce4-83eb83432200","ipAddress":"79.116.213.193","isInteractive":true,"location":{"city":"Madrid","countryOrRegion":"ES","geoCoordinates":{"altitude":null,"latitude":40.416,"longitude":-3.703},"state":"Madrid"},"resourceDisplayName":"Windows Azure Active Directory","resourceId":"00000001-0000-0000-d000-000000000000","riskDetail":"none","riskEventTypes":[],"riskEventTypes_v2":[],"riskLevelAggregated":"none","riskLevelDuringSignIn":"none","riskState":"none","status":{"additionalDetails":null,"errorCode":0,"failureReason":"Other."},"userDisplayName":"Admin Read Only","userId":"6838ec00-f384-40d8-b288-989103aed42b","userPrincipalName":"reports@example.onmicrosoft.com"}
    """

    parser_code_file_path = None
    logs_file_path = None

    try:
        # Create temporary parser code file
        with tempfile.NamedTemporaryFile(
            suffix=".yara", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(sample_parser_code)
            parser_code_file_path = temp_file.name

        # Create temporary logs file
        with tempfile.NamedTemporaryFile(
            suffix=".log", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(sample_logs_file_content)
            logs_file_path = temp_file.name

        # --- Scenario 1: Using --parser-code-file and --logs-file ---
        run_cmd_file_input = (
            [
                "secops",  # Replace with your actual CLI entry point
            ]
            + common_args
            + [
                "parser",
                "run",
                "--log-type",
                test_log_type,
                "--parser-code-file",
                parser_code_file_path,
                "--logs-file",
                logs_file_path,
                "--statedump-allowed",
            ]
        )

        run_result_file_input = subprocess.run(
            run_cmd_file_input, env=cli_env, capture_output=True, text=True
        )

        # Assert CLI command execution success
        assert (
            run_result_file_input.returncode == 0
        ), f"Parser run with files failed: {run_result_file_input.stderr}\n{run_result_file_input.stdout}"

        # Parse and assert the output
        run_output_file_input = json.loads(run_result_file_input.stdout)
        assert "parsedEvents" in run_output_file_input["runParserResults"][0]

    finally:
        # Clean up temporary files regardless of test outcome
        if parser_code_file_path and os.path.exists(parser_code_file_path):
            os.unlink(parser_code_file_path)
        if logs_file_path and os.path.exists(logs_file_path):
            os.unlink(logs_file_path)


@pytest.mark.integration
def test_cli_parser_run_with_multiple_logs(cli_env, common_args):
    """Test the 'parser run' command with multiple --log arguments."""
    test_log_type = "RESERVED_LOG_TYPE_1"

    parser_code = r"""
    filter {
        mutate {
          replace => {
            "event1.idm.read_only_udm.metadata.event_type" => "GENERIC_EVENT"
          }
        }
    }
    """

    # Test logs
    log1 = '{"event": "test1", "timestamp": "2025-01-01T00:00:00Z"}'
    log2 = '{"event": "test2", "timestamp": "2025-01-01T00:01:00Z"}'
    log3 = '{"event": "test3", "timestamp": "2025-01-01T00:02:00Z"}'

    parser_code_file_path = None

    try:
        # Create temporary parser code file
        with tempfile.NamedTemporaryFile(
            suffix=".conf", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(parser_code)
            parser_code_file_path = temp_file.name

        # Test with multiple --log arguments
        run_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "parser",
                "run",
                "--log-type",
                test_log_type,
                "--parser-code-file",
                parser_code_file_path,
                "--log",
                log1,
                "--log",
                log2,
                "--log",
                log3,
            ]
        )

        run_result = subprocess.run(
            run_cmd, env=cli_env, capture_output=True, text=True
        )

        assert (
            run_result.returncode == 0
        ), f"Parser run with multiple logs failed: {run_result.stderr}\n{run_result.stdout}"

        # Parse and verify output
        output = json.loads(run_result.stdout)
        assert "runParserResults" in output
        # Should have processed 3 logs
        assert len(output["runParserResults"]) >= 1

    finally:
        if parser_code_file_path and os.path.exists(parser_code_file_path):
            os.unlink(parser_code_file_path)


@pytest.mark.integration
def test_cli_parser_run_with_extension(cli_env, common_args):
    """Test the 'parser run' command with parser extension."""
    test_log_type = "RESERVED_LOG_TYPE_1"

    parser_code = r"""
    filter {
        mutate {
          replace => {
            "event1.idm.read_only_udm.metadata.event_type" => "GENERIC_EVENT"
          }
        }
    }
    """

    parser_extension = r"""
    filter {
        mutate {
          add_field => {
            "event1.idm.read_only_udm.metadata.product_name" => "Extended Product"
          }
        }
    }
    """

    test_log = '{"message": "Test log with extension"}'

    parser_code_file_path = None
    extension_file_path = None

    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(
            suffix=".conf", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(parser_code)
            parser_code_file_path = temp_file.name

        with tempfile.NamedTemporaryFile(
            suffix=".conf", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(parser_extension)
            extension_file_path = temp_file.name

        # Test with parser extension
        run_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "parser",
                "run",
                "--log-type",
                test_log_type,
                "--parser-code-file",
                parser_code_file_path,
                "--parser-extension-code-file",
                extension_file_path,
                "--log",
                test_log,
            ]
        )

        run_result = subprocess.run(
            run_cmd, env=cli_env, capture_output=True, text=True
        )

        assert (
            run_result.returncode == 0
        ), f"Parser run with extension failed: {run_result.stderr}\n{run_result.stdout}"

        # Verify output
        output = json.loads(run_result.stdout)
        assert "runParserResults" in output

    finally:
        if parser_code_file_path and os.path.exists(parser_code_file_path):
            os.unlink(parser_code_file_path)
        if extension_file_path and os.path.exists(extension_file_path):
            os.unlink(extension_file_path)


@pytest.mark.integration
def test_cli_parser_run_error_cases(cli_env, common_args):
    """Test error handling for the 'parser run' command."""
    test_log_type = "RESERVED_LOG_TYPE_1"

    # Test 1: Missing required arguments
    run_cmd = (
        [
            "secops",
        ]
        + common_args
        + [
            "parser",
            "run",
            "--log-type",
            test_log_type,
            # Missing parser code and logs
        ]
    )

    run_result = subprocess.run(run_cmd, env=cli_env, capture_output=True, text=True)

    assert run_result.returncode != 0, "Should fail with missing required arguments"

    # Test 2: Invalid file path
    run_cmd = (
        [
            "secops",
        ]
        + common_args
        + [
            "parser",
            "run",
            "--log-type",
            test_log_type,
            "--parser-code-file",
            "/non/existent/file.conf",
            "--logs-file",
            "/non/existent/logs.txt",
        ]
    )

    run_result = subprocess.run(run_cmd, env=cli_env, capture_output=True, text=True)

    assert run_result.returncode != 0, "Should fail with invalid file paths"
    assert "Error reading" in run_result.stderr

    # Test 3: Empty logs file
    empty_logs_file = None
    parser_file = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".log", mode="w+", delete=False
        ) as temp_file:
            # Write nothing to create empty file
            empty_logs_file = temp_file.name

        with tempfile.NamedTemporaryFile(
            suffix=".conf", mode="w+", delete=False
        ) as temp_file:
            temp_file.write("filter {}")
            parser_file = temp_file.name

        run_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "parser",
                "run",
                "--log-type",
                test_log_type,
                "--parser-code-file",
                parser_file,
                "--logs-file",
                empty_logs_file,
            ]
        )

        run_result = subprocess.run(
            run_cmd, env=cli_env, capture_output=True, text=True
        )

        # Empty logs should fail with current implementation
        assert run_result.returncode != 0
        assert "No logs provided" in run_result.stderr

    finally:
        if empty_logs_file and os.path.exists(empty_logs_file):
            os.unlink(empty_logs_file)
        if parser_file and os.path.exists(parser_file):
            os.unlink(parser_file)


@pytest.mark.integration
def test_cli_rule_list(cli_env, common_args):
    """Test the rule list command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["rule", "list"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert "rules" in output
    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_rule_list_with_pagination(cli_env, common_args):
    """Test the rule list command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["rule", "list"]
        + ["--page-size", "1"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert "rules" in output
        assert len(output.get("rules")) == 1
    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_rule_search(cli_env, common_args):
    """Test the rule search command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["rule", "search", "--query", ".*"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert "rules" in output
    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_stats(cli_env, common_args):
    """Test the stats command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + [
            "stats",
            "--query",
            """metadata.event_type = "NETWORK_CONNECTION"
match:
  principal.hostname
outcome:
  $count = count(metadata.id)
order:
  $count desc""",
            "--time-window",
            "1",
            "--max-events",
            "10",
            "--max-values",
            "5",
            "--timeout",
            "180"
        ]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert "columns" in output
        assert "rows" in output
        assert "total_rows" in output
    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_iocs(cli_env, common_args):
    """Test the iocs command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["iocs", "--time-window", "48", "--max-matches", "5"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert "matches" in output
    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_log_types(cli_env, common_args):
    """Test the log types command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["log", "types"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON - should be a list of log types
    assert result.stdout.strip() != ""
    assert "Error:" not in result.stderr


@pytest.mark.integration
def test_cli_rule_get(cli_env, common_args):
    """Test the rule get command (first need to find an existing rule ID)."""
    # First list rules to get a valid rule ID
    list_cmd = (
        [
            "secops",
        ]
        + common_args
        + ["rule", "list"]
    )

    list_result = subprocess.run(list_cmd, env=cli_env, capture_output=True, text=True)

    # Check that we have at least one rule to test with
    assert list_result.returncode == 0

    rules = json.loads(list_result.stdout)
    if not rules.get("rules"):
        pytest.skip("No rules available to test the get command")

    # Get the first rule's ID
    rule_id = rules["rules"][0]["name"].split("/")[-1]

    # Test the get command with this rule ID
    get_cmd = (
        [
            "secops",
        ]
        + common_args
        + ["rule", "get", "--id", rule_id]
    )

    get_result = subprocess.run(get_cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert get_result.returncode == 0

    # Try to parse the output as JSON
    rule_data = json.loads(get_result.stdout)
    assert "name" in rule_data
    assert rule_data["name"].endswith(rule_id)


@pytest.mark.integration
def test_cli_rule_validate(cli_env, common_args):
    """Test the rule validate command."""
    # Create a temporary file with a simple valid rule
    with tempfile.NamedTemporaryFile(
        suffix=".yaral", mode="w+", delete=False
    ) as temp_file:
        temp_file.write(
            """
rule test_rule {
    meta:
        description = "Test rule for validation"
        author = "Test Author"
        severity = "Low"
        yara_version = "YL2.0"
        rule_version = "1.0"
    events:
        $e.metadata.event_type = "NETWORK_CONNECTION"
    condition:
        $e
}
"""
        )
        temp_file_path = temp_file.name

    try:
        # Execute the CLI command
        cmd = (
            [
                "secops",
            ]
            + common_args
            + ["rule", "validate", "--file", temp_file_path]
        )

        result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

        # Check that the command executed successfully
        assert result.returncode == 0

        # Should return "Rule is valid."
        assert "Rule is valid" in result.stdout
    finally:
        # Clean up
        os.unlink(temp_file_path)


@pytest.mark.integration
def test_cli_rule_test(cli_env, common_args):
    """Test the rule test command."""
    # Create a temporary file with a simple valid rule
    with tempfile.NamedTemporaryFile(
        suffix=".yaral", mode="w+", delete=False
    ) as temp_file:
        temp_file.write(
            """
rule test_network_connection {
    meta:
        description = "Test rule for network connections"
        author = "CLI Test"
        severity = "Low"
        yara_version = "YL2.0"
        rule_version = "1.0"
    events:
        $e.metadata.event_type = "NETWORK_CONNECTION"
    condition:
        $e
}
"""
        )
        temp_file_path = temp_file.name

    try:
        # Test 1: Basic test with time window
        cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "rule",
                "test",
                "--file",
                temp_file_path,
                "--time-window",
                "10",  # Use a small time window for faster testing
                "--max-results",
                "5",  # Limit to 5 results for faster testing
            ]
        )

        result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

        # The command may fail in some environments due to permissions or lack of data
        # So we'll skip the test rather than fail it in those cases
        if (
            "permission" in result.stderr.lower()
            or "not authorized" in result.stderr.lower()
        ):
            pytest.skip(f"Skipping test due to permission issues: {result.stderr}")

        # If we get a success response, check that it contains expected output elements
        if result.returncode == 0:
            # The output should be a JSON array (could be empty)
            try:
                output = json.loads(result.stdout)
                # Should be a list (array) of events
                assert isinstance(output, list)
            except json.JSONDecodeError:
                pytest.fail(f"Expected JSON output but got: {result.stdout}")

        # Test 2: Test with specific date range
        cmd_date_range = (
            [
                "secops",
            ]
            + common_args
            + [
                "rule",
                "test",
                "--file",
                temp_file_path,
                "--start-time",
                (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "--end-time",
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "--max-results",
                "5",  # Limit to 5 results for faster testing
            ]
        )

        result_date_range = subprocess.run(
            cmd_date_range, env=cli_env, capture_output=True, text=True
        )

        # If we get a success response, check that it contains expected output elements
        if result_date_range.returncode == 0:
            # The output should be a JSON array (could be empty)
            try:
                output = json.loads(result_date_range.stdout)
                # Should be a list (array) of events
                assert isinstance(output, list)
            except json.JSONDecodeError:
                pytest.fail(f"Expected JSON output but got: {result_date_range.stdout}")

    except Exception as e:
        pytest.fail(f"Unexpected error in CLI rule test command: {str(e)}")
    finally:
        # Clean up
        os.unlink(temp_file_path)


@pytest.mark.integration
def test_cli_rule_lifecycle(cli_env, common_args):
    """Test rule creation, update, enable/disable, and deletion (full lifecycle)."""
    # Create temp files for the rule
    with tempfile.NamedTemporaryFile(
        suffix=".yaral", mode="w+", delete=False
    ) as temp_file:
        temp_file.write(
            """
rule test_cli_rule {
    meta:
        description = "Test rule for CLI testing"
        author = "CLI Test"
        severity = "Low"
        yara_version = "YL2.0"
        rule_version = "1.0"
    events:
        $e.metadata.event_type = "NETWORK_CONNECTION"
    condition:
        $e
}
"""
        )
        rule_file_path = temp_file.name

    with tempfile.NamedTemporaryFile(
        suffix=".yaral", mode="w+", delete=False
    ) as update_file:
        update_file.write(
            """
rule test_cli_rule {
    meta:
        description = "Updated test rule for CLI testing"
        author = "CLI Test"
        severity = "Medium"
        yara_version = "YL2.0"
        rule_version = "1.1"
    events:
        $e.metadata.event_type = "NETWORK_CONNECTION"
    condition:
        $e
}
"""
        )
        update_file_path = update_file.name

    try:
        # 1. Create the rule
        create_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["rule", "create", "--file", rule_file_path]
        )

        create_result = subprocess.run(
            create_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that the command executed successfully
        assert create_result.returncode == 0

        # Extract the rule ID
        rule_data = json.loads(create_result.stdout)
        rule_id = rule_data["name"].split("/")[-1]

        # 2. Update the rule
        update_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["rule", "update", "--id", rule_id, "--file", update_file_path]
        )

        update_result = subprocess.run(
            update_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that the update command executed successfully
        assert update_result.returncode == 0

        # 3. Enable the rule
        enable_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["rule", "enable", "--id", rule_id, "--enabled", "true"]
        )

        enable_result = subprocess.run(
            enable_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that the enable command executed successfully
        assert enable_result.returncode == 0

        # 4. Disable the rule
        disable_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["rule", "enable", "--id", rule_id, "--enabled", "false"]
        )

        disable_result = subprocess.run(
            disable_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that the disable command executed successfully
        assert disable_result.returncode == 0

        # 5. Delete the rule
        delete_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["rule", "delete", "--id", rule_id, "--force"]
        )

        delete_result = subprocess.run(
            delete_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that the delete command executed successfully
        assert delete_result.returncode == 0

    finally:
        # Clean up temp files
        os.unlink(rule_file_path)
        os.unlink(update_file_path)


@pytest.mark.integration
def test_cli_alert(cli_env, common_args):
    """Test the alert command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["alert", "--time-window", "24", "--max-alerts", "5"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert "complete" in output

        # If there are alerts with cases, test case retrieval
        alerts = output.get("alerts", {}).get("alerts", [])
        case_ids = [alert.get("caseName") for alert in alerts if alert.get("caseName")]

        if case_ids:
            # Test case retrieval with the found case IDs
            case_cmd = (
                [
                    "secops",
                ]
                + common_args
                + [
                    "case",
                    "--ids",
                    ",".join(case_ids[:3]),
                ]  # Test with up to 3 case IDs
            )

            case_result = subprocess.run(
                case_cmd, env=cli_env, capture_output=True, text=True
            )

            # Case retrieval might fail if cases are not accessible, which is OK
            if case_result.returncode == 0:
                try:
                    case_output = json.loads(case_result.stdout)
                    assert "cases" in case_output
                    print(
                        f"Successfully retrieved {len(case_output.get('cases', []))} cases"
                    )
                except json.JSONDecodeError:
                    print("Could not parse case output as JSON")
            else:
                print(f"Case retrieval failed (this is OK): {case_result.stderr}")

    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_log_ingest_with_labels(cli_env, common_args):
    """Test the log ingest command with labels."""
    # Create a temporary file with a sample OKTA log
    with tempfile.NamedTemporaryFile(
        suffix=".json", mode="w+", delete=False
    ) as temp_file:
        # Create an OKTA log similar to the examples/ingest_logs.py format
        current_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        okta_log = {
            "actor": {
                "displayName": "CLI Test User",
                "alternateId": "cli_test@example.com",
            },
            "client": {
                "ipAddress": "192.168.1.100",
                "userAgent": {"os": "Mac OS X", "browser": "SAFARI"},
            },
            "displayMessage": "User login to Okta via CLI test",
            "eventType": "user.session.start",
            "outcome": {"result": "SUCCESS"},
            "published": current_time,
        }
        temp_file.write(json.dumps(okta_log))
        temp_file_path = temp_file.name

    try:
        # Test 1: Test with JSON format labels
        json_labels = '{"environment": "test", "source": "cli_test", "version": "1.0"}'

        json_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "log",
                "ingest",
                "--type",
                "OKTA",
                "--file",
                temp_file_path,
                "--labels",
                json_labels,
            ]
        )

        json_result = subprocess.run(
            json_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that the command executed successfully with JSON labels
        assert (
            json_result.returncode == 0
        ), f"Command failed with stderr: {json_result.stderr}"

        # Try to parse the output as JSON - just check it's valid JSON, not specific fields
        try:
            json_output = json.loads(json_result.stdout)
            # The response might be an empty object {}, which is still valid
            assert isinstance(json_output, dict)
        except json.JSONDecodeError:
            # If not valid JSON, check for expected error messages
            assert "Error:" not in json_result.stdout

        # Test 2: Test with key=value format labels
        kv_labels = "environment=integration,source=cli_integration_test,team=security"

        kv_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "log",
                "ingest",
                "--type",
                "OKTA",
                "--file",
                temp_file_path,
                "--labels",
                kv_labels,
            ]
        )

        kv_result = subprocess.run(kv_cmd, env=cli_env, capture_output=True, text=True)

        # Check that the command executed successfully with key=value labels
        assert (
            kv_result.returncode == 0
        ), f"Command failed with stderr: {kv_result.stderr}"

        # Try to parse the output as JSON - just check it's valid JSON, not specific fields
        try:
            kv_output = json.loads(kv_result.stdout)
            # The response might be an empty object {}, which is still valid
            assert isinstance(kv_output, dict)
        except json.JSONDecodeError:
            # If not valid JSON, check for expected error messages
            assert "Error:" not in kv_result.stdout

    finally:
        # Clean up
        os.unlink(temp_file_path)


@pytest.mark.integration
def test_cli_log_ingest_windows_multiline(cli_env, common_args):
    """Test the log ingest command with Windows multi-line logs."""
    # Create a temporary file with sample Windows Event logs (multi-line format)
    with tempfile.NamedTemporaryFile(
        suffix=".log", mode="w+", delete=False
    ) as temp_file:
        # Create Windows Event logs with multiple events
        windows_logs = """Log Name:      Security
Source:        Microsoft-Windows-Security-Auditing
Event ID:      4624
Task Category: Logon
Keywords:      Audit Success
Level:         Information
Description:   An account was successfully logged on.

Log Name:      System
Source:        Microsoft-Windows-Kernel-Power
Event ID:      41
Task Category: (63)
Keywords:      (70368744177664),(2)
Level:         Critical
Description:   The system has rebooted without cleanly shutting down first.
"""
        temp_file.write(windows_logs)
        temp_file_path = temp_file.name

    try:
        # Test with Windows log format
        cmd = [
            "secops",
        ] + common_args + [
            "log",
            "ingest",
            "--type",
            "WINDOWS_FIREWALL",
            "--file",
            temp_file_path,
        ]

        result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

        # Check that the command executed successfully
        assert (
            result.returncode == 0
        ), f"Command failed with stderr: {result.stderr}"

        # Check that the output contains expected information
        try:
            json_output = json.loads(result.stdout)
            # Verify the response is valid
            assert isinstance(json_output, dict)
            # Print the result for debugging if needed
            print(f"Windows log ingest response: {json_output}")
        except json.JSONDecodeError:
            # If not valid JSON, check for expected error messages
            assert "Error:" not in result.stdout

    finally:
        # Clean up
        os.unlink(temp_file_path)


@pytest.mark.integration
def test_cli_log_ingest_syslog_singleline(cli_env, common_args):
    """Test the log ingest command with Syslog single-line logs.
    
    This test validates that the CLI can properly handle single-line logs
    in Syslog format (a different format than Windows logs) for ingestion.
    """
    # Create a temporary file with sample Syslog entries (single-line per event format)
    with tempfile.NamedTemporaryFile(
        suffix=".log", mode="w+", delete=False
    ) as temp_file:
        # Create Syslog entries in standard format
        syslog_entries = """<34>Oct 11 22:14:15 server1 sshd[12345]: Failed password for invalid user test from 192.168.1.100 port 45678 ssh2
<34>Oct 11 22:15:20 server1 su: pam_unix(su-l:auth): authentication failure; logname=user uid=1000 euid=0 tty=/dev/pts/0 ruser=user rhost= user=root
<33>Oct 11 22:16:10 server1 sudo: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/cat /etc/shadow
<30>Oct 11 22:17:01 server1 CRON[12346]: (root) CMD (/usr/local/bin/backup.sh)
<29>Oct 11 22:18:22 server1 kernel: [12345.123456] iptables: IN=eth0 OUT= MAC=00:11:22:33:44:55:66:77:88:99:aa:bb:cc:dd SRC=10.0.0.1 DST=10.0.0.2 LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=12345 DF PROTO=TCP SPT=12345 DPT=80 WINDOW=65535 RES=0x00 SYN URGP=0
"""
        temp_file.write(syslog_entries)
        temp_file_path = temp_file.name

    try:
        # Test with Syslog log format
        cmd = [
            "secops",
        ] + common_args + [
            "log",
            "ingest",
            "--type",
            "AUDITD",
            "--file",
            temp_file_path,
        ]

        result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

        # Check that the command executed successfully
        assert (
            result.returncode == 0
        ), f"Command failed with stderr: {result.stderr}"

        # Check that the output contains expected information
        try:
            json_output = json.loads(result.stdout)
            # Verify the response is valid
            assert isinstance(json_output, dict)
            # Print the result for debugging if needed
            print(f"Syslog ingest response: {json_output}")
        except json.JSONDecodeError:
            # If not valid JSON, check for expected error messages
            assert "Error:" not in result.stdout

    finally:
        # Clean up
        os.unlink(temp_file_path)


@pytest.mark.integration
def test_cli_export_log_types(cli_env, common_args):
    """Test the export log-types command."""
    # Execute the CLI command
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["export", "log-types", "--time-window", "24"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert "log_types" in output
    except json.JSONDecodeError:
        # If not valid JSON, check for expected error messages
        assert "Error:" not in result.stdout


@pytest.mark.integration
def test_cli_gemini(cli_env, common_args):
    """Test the gemini command."""
    # Execute the CLI command - Gemini output will be text by default, not JSON
    cmd = (
        [
            "secops",
        ]
        + common_args
        + ["gemini", "--query", "What is Windows event ID 4625?"]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    # Note: this may fail if Gemini is not enabled for the account
    if "users must opt-in before using Gemini" in result.stderr:
        pytest.skip("Test skipped: User account has not been opted-in to Gemini.")

    assert result.returncode == 0

    # For Gemini, just check that we got some text response
    assert len(result.stdout.strip()) > 0
    assert "Error:" not in result.stderr


@pytest.mark.integration
def test_cli_rule_detections(cli_env, common_args):
    """Test the rule detections command"""
    # First list rules to get a valid rule ID
    list_cmd = (
        [
            "secops",
        ]
        + common_args
        + ["rule", "list"]
    )

    list_result = subprocess.run(list_cmd, env=cli_env, capture_output=True, text=True)

    # Check that we have at least one rule to test with
    assert list_result.returncode == 0

    rules = json.loads(list_result.stdout)
    if not rules.get("rules"):
        pytest.skip("No rules available to test the detections command")

    # Get the first rule's ID
    rule_id = rules["rules"][0]["name"].split("/")[-1]

    # Create time range parameters
    start_time = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Test with both time range and list_basis parameters
    list_basis = "CREATED_TIME"  # Could be one of "LIST_BASIS_UNSPECIFIED", "CREATED_TIME", "DETECTION_TIME"
    
    cmd = (
        [
            "secops",
        ]
        + common_args
        + [
            "rule",
            "detections",
            "--rule_id",
            rule_id,
            "--start-time",
            start_time,
            "--end-time",
            end_time,
            "--list-basis",
            list_basis,
        ]
    )

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        print(f"Successfully retrieved detections with time range and list_basis for rule {rule_id}")
    except json.JSONDecodeError:
        pytest.fail(f"Expected JSON output but got: {result.stdout}")


@pytest.mark.integration
def test_cli_help(cli_env):
    """Test the help command."""
    # Execute the CLI command
    cmd = ["secops", "--help"]

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # Check that the command executed successfully
    assert result.returncode == 0

    # Should contain help text
    assert "usage: secops" in result.stdout
    assert "Command to execute" in result.stdout


@pytest.mark.integration
def test_cli_version(cli_env):
    """Test retrieving the CLI version (using --version)."""
    # This assumes there's a --version flag; let's check if it exists
    cmd = ["secops", "--version"]

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)

    # If version flag exists, it should return successfully
    if result.returncode != 0:
        # If not, we'll skip this test
        pytest.skip("secops CLI does not support --version flag")

    # Should include a version number in the format x.y.z
    import re

    assert re.search(r"\d+\.\d+\.\d+", result.stdout)


@pytest.mark.integration
def test_cli_config_lifecycle(cli_env):
    """Test config set, view, and clear commands."""
    # Create temp directory for config file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override the CONFIG_DIR and CONFIG_FILE with temp directory
        with patch("secops.cli.CONFIG_DIR", Path(temp_dir)), patch(
            "secops.cli.CONFIG_FILE", Path(temp_dir) / "config.json"
        ):

            # 1. Set configuration - standard parameters
            set_cmd = [
                "secops",
                "config",
                "set",
                "--customer-id",
                "test-customer-id",
                "--project-id",
                "test-project-id",
                "--region",
                "test-region",
            ]

            set_result = subprocess.run(
                set_cmd, env=cli_env, capture_output=True, text=True
            )

            # Check that the set command executed successfully
            assert set_result.returncode == 0
            assert "Configuration saved" in set_result.stdout

            # 2. Set time-related configuration
            time_set_cmd = [
                "secops",
                "config",
                "set",
                "--start-time",
                "2023-01-01T00:00:00Z",
                "--end-time",
                "2023-01-02T00:00:00Z",
                "--time-window",
                "48",
            ]

            time_set_result = subprocess.run(
                time_set_cmd, env=cli_env, capture_output=True, text=True
            )

            # Check that the time set command executed successfully
            assert time_set_result.returncode == 0
            assert "Configuration saved" in time_set_result.stdout

            # 3. View configuration
            view_cmd = ["secops", "config", "view"]

            view_result = subprocess.run(
                view_cmd, env=cli_env, capture_output=True, text=True
            )

            # Check that the view command executed successfully
            assert view_result.returncode == 0
            assert "test-customer-id" in view_result.stdout
            assert "test-project-id" in view_result.stdout
            assert "test-region" in view_result.stdout
            assert "2023-01-01T00:00:00Z" in view_result.stdout
            assert "2023-01-02T00:00:00Z" in view_result.stdout
            assert "48" in view_result.stdout

            # 4. Run a command that should use the configuration
            search_cmd = [
                "secops",
                "search",
                "--query",
                'metadata.event_type = "NETWORK_CONNECTION"',
                "--max-events",
                "1",
            ]

            search_result = subprocess.run(
                search_cmd, env=cli_env, capture_output=True, text=True
            )

            # This might fail if the test credentials don't work, so we'll just check that it tried to use them

            # 5. Clear configuration
            clear_cmd = ["secops", "config", "clear"]

            clear_result = subprocess.run(
                clear_cmd, env=cli_env, capture_output=True, text=True
            )

            # Check that the clear command executed successfully
            assert clear_result.returncode == 0
            assert "Configuration cleared" in clear_result.stdout

            # 6. View again to confirm it's cleared
            view_cmd = ["secops", "config", "view"]

            view_result = subprocess.run(
                view_cmd, env=cli_env, capture_output=True, text=True
            )

            # Check that the view command shows no configuration
            assert view_result.returncode == 0
            assert "No configuration found" in view_result.stdout


@pytest.mark.integration
def test_cli_replace_data_table_rows(cli_env, common_args):
    """Test the data-table replace-rows command."""
    # Generate unique name for data table using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    table_name = f"test_replace_rows_{timestamp}"

    try:
        # 1. Create a data table with initial rows
        print("\n>>> Creating data table with initial rows")
        header = json.dumps(
            {
                "hostname": "STRING",
                "ip_address": "STRING",
                "description": "STRING",
            }
        )
        initial_rows = json.dumps(
            [
                ["initial1.example.com", "10.0.0.1", "Initial host 1"],
                ["initial2.example.com", "10.0.0.2", "Initial host 2"],
                ["initial3.example.com", "10.0.0.3", "Initial host 3"],
            ]
        )

        # Create the data table
        create_cmd = (
            ["secops"]
            + common_args
            + [
                "data-table",
                "create",
                "--name",
                table_name,
                "--description",
                "CLI Test for Replace Rows",
                "--header",
                header,
                "--rows",
                initial_rows,
            ]
        )

        create_result = subprocess.run(
            create_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that creation was successful
        assert (
            create_result.returncode == 0
        ), f"Creation failed: {create_result.stderr}"
        print("Data table created successfully")

        # 2. List rows to verify initial state
        print("Verifying initial rows")
        list_rows_cmd = (
            ["secops"]
            + common_args
            + ["data-table", "list-rows", "--name", table_name]
        )

        list_rows_result = subprocess.run(
            list_rows_cmd, env=cli_env, capture_output=True, text=True
        )

        assert list_rows_result.returncode == 0
        initial_rows_data = json.loads(list_rows_result.stdout)
        assert (
            len(initial_rows_data) == 3
        ), f"Expected 3 initial rows, got {len(initial_rows_data)}"
        print(f"Verified {len(initial_rows_data)} initial rows")

        # 3. Replace rows with new data
        print("\n>>> Replacing rows with new data")
        replacement_rows = json.dumps(
            [
                ["replaced1.example.com", "192.168.1.1", "Replaced host 1"],
                ["replaced2.example.com", "192.168.1.2", "Replaced host 2"],
            ]
        )

        replace_rows_cmd = (
            ["secops"]
            + common_args
            + [
                "data-table",
                "replace-rows",
                "--name",
                table_name,
                "--rows",
                replacement_rows,
            ]
        )

        replace_result = subprocess.run(
            replace_rows_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that replacement was successful
        assert (
            replace_result.returncode == 0
        ), f"Replacement failed: {replace_result.stderr}"
        print("Rows replaced successfully")

        # 4. List rows again to verify replacement
        print("Verifying replaced rows")
        list_rows_result = subprocess.run(
            list_rows_cmd, env=cli_env, capture_output=True, text=True
        )

        assert list_rows_result.returncode == 0
        replaced_rows_data = json.loads(list_rows_result.stdout)
        assert (
            len(replaced_rows_data) == 2
        ), f"Expected 2 rows after replacement, got {len(replaced_rows_data)}"
        print(f"Verified {len(replaced_rows_data)} rows after replacement")

        # Verify the content of the replaced rows
        found_hosts = set(row["values"][0] for row in replaced_rows_data)
        expected_hosts = {"replaced1.example.com", "replaced2.example.com"}
        assert (
            found_hosts == expected_hosts
        ), f"Expected hosts {expected_hosts}, got {found_hosts}"
        print("Row content verified successfully")

    except Exception as e:
        # Clean up in case of test failure
        pytest.fail(f"Replace rows CLI test failed: {e}")

    finally:
        # Clean up the data table
        try:
            subprocess.run(
                [
                    "secops",
                ]
                + common_args
                + ["data-table", "delete", "--name", table_name, "--force"],
                env=cli_env,
                capture_output=True,
            )
        except Exception as cleanup_error:
            print(
                f"Warning: Failed to clean up data table {table_name}: {cleanup_error}"
            )


@pytest.mark.integration
def test_cli_data_tables(cli_env, common_args):
    """Test the data-table command lifecycle."""
    # Generate unique name for data table using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    table_name = f"test_cli_dt_{timestamp}"

    try:
        # 1. Create a data table
        header = json.dumps(
            {"hostname": "STRING", "ip_address": "STRING", "description": "STRING"}
        )
        column_options = json.dumps({"ip_address": {"repeatedValues": True}})
        rows = json.dumps(
            [
                ["host1.example.com", "192.168.1.10", "Test host 1"],
                ["host2.example.com", "192.168.1.11", "Test host 2"],
            ]
        )

        create_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "data-table",
                "create",
                "--name",
                table_name,
                "--description",
                "CLI Test Data Table",
                "--header",
                header,
                "--column-options",
                column_options,
                "--rows",
                rows,
            ]
        )

        create_result = subprocess.run(
            create_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that creation was successful
        assert create_result.returncode == 0, f"Creation failed: {create_result.stderr}"

        # 2. Get the data table
        get_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["data-table", "get", "--name", table_name]
        )

        get_result = subprocess.run(
            get_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that get was successful
        assert get_result.returncode == 0
        table_data = json.loads(get_result.stdout)
        assert table_data["name"].endswith(table_name)
        assert table_data["description"] == "CLI Test Data Table"
        assert len(table_data["columnInfo"]) == 3

        # 3. List rows
        list_rows_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["data-table", "list-rows", "--name", table_name]
        )

        list_rows_result = subprocess.run(
            list_rows_cmd, env=cli_env, capture_output=True, text=True
        )

        assert list_rows_result.returncode == 0
        rows_data = json.loads(list_rows_result.stdout)
        assert len(rows_data) == 2  # We added 2 rows during creation

        # 4. Add more rows
        new_rows = json.dumps([["host3.example.com", "192.168.1.12", "Test host 3"]])
        add_rows_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["data-table", "add-rows", "--name", table_name, "--rows", new_rows]
        )

        add_rows_result = subprocess.run(
            add_rows_cmd, env=cli_env, capture_output=True, text=True
        )

        assert add_rows_result.returncode == 0

        # 5. List rows again to verify the addition
        list_rows_result = subprocess.run(
            list_rows_cmd, env=cli_env, capture_output=True, text=True
        )

        assert list_rows_result.returncode == 0
        updated_rows_data = json.loads(list_rows_result.stdout)
        assert len(updated_rows_data) == 3  # Now should have 3 rows

        # 6. Delete a row
        # First, get the row ID
        row_id = updated_rows_data[0]["name"].split("/")[-1]

        delete_row_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["data-table", "delete-rows", "--name", table_name, "--row-ids", row_id]
        )

        delete_row_result = subprocess.run(
            delete_row_cmd, env=cli_env, capture_output=True, text=True
        )

        assert delete_row_result.returncode == 0

        # 7. List data tables
        list_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["data-table", "list"]
        )

        list_result = subprocess.run(
            list_cmd, env=cli_env, capture_output=True, text=True
        )

        assert list_result.returncode == 0
        tables = json.loads(list_result.stdout)
        # Find our table in the list
        found = False
        for table in tables:
            if table["name"].endswith(table_name):
                found = True
                break
        assert found, f"Couldn't find {table_name} in list of tables"

        # 8. Delete the table
        delete_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["data-table", "delete", "--name", table_name, "--force"]
        )

        delete_result = subprocess.run(
            delete_cmd, env=cli_env, capture_output=True, text=True
        )

        assert delete_result.returncode == 0

    except Exception as e:
        # Clean up in case of test failure
        try:
            subprocess.run(
                [
                    "secops",
                ]
                + common_args
                + ["data-table", "delete", "--name", table_name, "--force"],
                env=cli_env,
                capture_output=True,
            )
        except:
            pass
        raise


@pytest.mark.integration
def test_cli_update_data_table(cli_env, common_args):
    """Test the data-table update command.

    This test creates a data table, updates its properties, verifies the
    changes, and then cleans up by deleting the data table.
    """
    # Generate unique name for data table using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    table_name = f"test_cli_update_dt_{timestamp}"

    try:
        # 1. Create a data table
        header = json.dumps(
            {
                "hostname": "STRING",
                "ip_address": "STRING",
                "description": "STRING",
            }
        )
        initial_description = "Initial CLI data table description"

        create_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "data-table",
                "create",
                "--name",
                table_name,
                "--description",
                initial_description,
                "--header",
                header,
            ]
        )

        create_result = subprocess.run(
            create_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that creation was successful
        assert (
            create_result.returncode == 0
        ), f"Creation failed: {create_result.stderr}"

        # 2. Update the data table with new description and TTL
        updated_description = "Updated CLI data table description"
        updated_ttl = "48h"

        update_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "data-table",
                "update",
                "--name",
                table_name,
                "--description",
                updated_description,
                "--row-time-to-live",
                updated_ttl,
            ]
        )

        update_result = subprocess.run(
            update_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that update was successful
        assert (
            update_result.returncode == 0
        ), f"Update failed: {update_result.stderr}"

        # 3. Get the data table to verify updates
        get_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["data-table", "get", "--name", table_name]
        )

        get_result = subprocess.run(
            get_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that get was successful
        assert get_result.returncode == 0
        updated_table = json.loads(get_result.stdout)

        # Verify the updates were applied
        assert updated_table["description"] == updated_description
        assert updated_table["rowTimeToLive"] == updated_ttl

        # 4. Test partial update with only description
        final_description = "Final CLI data table description"

        partial_update_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "data-table",
                "update",
                "--name",
                table_name,
                "--description",
                final_description,
            ]
        )

        partial_update_result = subprocess.run(
            partial_update_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that partial update was successful
        assert partial_update_result.returncode == 0

        # 5. Get the data table again to verify partial update
        get_result = subprocess.run(
            get_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that get was successful
        assert get_result.returncode == 0
        final_table = json.loads(get_result.stdout)

        # Verify only description was updated, TTL remained the same
        assert final_table["description"] == final_description
        assert final_table["rowTimeToLive"] == updated_ttl

    except Exception as e:
        # Clean up in case of test failure
        try:
            subprocess.run(
                [
                    "secops",
                ]
                + common_args
                + ["data-table", "delete", "--name", table_name, "--force"],
                env=cli_env,
                capture_output=True,
            )
        except:
            pass
        raise e
    finally:
        # Clean up after test
        try:
            subprocess.run(
                [
                    "secops",
                ]
                + common_args
                + ["data-table", "delete", "--name", table_name, "--force"],
                env=cli_env,
                capture_output=True,
            )
        except:
            pass


@pytest.mark.integration
def test_cli_reference_lists(cli_env, common_args):
    """Test the reference-list command lifecycle."""
    # Generate unique name for reference list using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    list_name = f"test_cli_rl_{timestamp}"

    try:
        # 1. Create a reference list
        # Create a temporary file with reference list entries
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w+", delete=False
        ) as temp_file:
            temp_file.write("malicious.example.com\n")
            temp_file.write("suspicious.example.org\n")
            temp_file.write("evil.example.net\n")
            entries_file_path = temp_file.name

        create_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "reference-list",
                "create",
                "--name",
                list_name,
                "--description",
                "CLI Test Reference List",
                "--entries-file",
                entries_file_path,
                "--syntax-type",
                "STRING",
            ]
        )

        create_result = subprocess.run(
            create_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that creation was successful
        assert create_result.returncode == 0, f"Creation failed: {create_result.stderr}"

        # 2. Get the reference list
        get_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["reference-list", "get", "--name", list_name, "--view", "FULL"]
        )

        get_result = subprocess.run(
            get_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that get was successful
        assert get_result.returncode == 0
        list_data = json.loads(get_result.stdout)
        assert list_data["name"].endswith(list_name)
        assert list_data["description"] == "CLI Test Reference List"
        assert len(list_data["entries"]) == 3

        # 3. List reference lists
        list_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["reference-list", "list"]
        )

        list_result = subprocess.run(
            list_cmd, env=cli_env, capture_output=True, text=True
        )

        assert list_result.returncode == 0
        lists = json.loads(list_result.stdout)
        # Find our list in the result
        found = False
        for ref_list in lists:
            if ref_list["name"].endswith(list_name):
                found = True
                break
        assert found, f"Couldn't find {list_name} in list of reference lists"

        # 4. Update the reference list with new entries
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w+", delete=False
        ) as temp_update_file:
            temp_update_file.write("updated.example.com\n")
            temp_update_file.write("new.example.org\n")
            update_file_path = temp_update_file.name

        update_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "reference-list",
                "update",
                "--name",
                list_name,
                "--description",
                "Updated CLI Test Reference List",
                "--entries-file",
                update_file_path,
            ]
        )

        update_result = subprocess.run(
            update_cmd, env=cli_env, capture_output=True, text=True
        )

        assert update_result.returncode == 0

        # 5. Get the updated reference list to verify changes
        get_updated_result = subprocess.run(
            get_cmd, env=cli_env, capture_output=True, text=True
        )

        assert get_updated_result.returncode == 0
        updated_data = json.loads(get_updated_result.stdout)
        assert updated_data["description"] == "Updated CLI Test Reference List"
        assert len(updated_data["entries"]) == 2

        # Add a delay before deletion to allow API to fully process previous operations
        time.sleep(5)

        # Note: Reference list deletion is not currently supported by the API
        print(
            f"Skipping deletion of reference list {list_name} - deletion not supported by API"
        )

    except Exception as e:
        # Note: Reference list deletion is not currently supported by the API,
        # so we can't clean up test reference lists
        print(
            f"Warning: Test reference list {list_name} will remain since deletion is not supported"
        )
        raise
    finally:
        # Clean up temp files
        if "entries_file_path" in locals():
            os.unlink(entries_file_path)
        if "update_file_path" in locals():
            os.unlink(update_file_path)


@pytest.mark.integration
def test_cli_reference_list_create_delete(cli_env, common_args):
    """Test simple reference list create and delete operations."""
    # Generate unique name for reference list using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    list_name = f"test_cli_simple_{timestamp}"

    try:
        # 1. Create a reference list with simple inline entries
        create_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "reference-list",
                "create",
                "--name",
                list_name,
                "--description",
                "Simple Test Reference List",
                "--entries",
                "test1.example.com,test2.example.com",
                "--syntax-type",
                "STRING",
            ]
        )

        create_result = subprocess.run(
            create_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that creation was successful
        assert create_result.returncode == 0, f"Creation failed: {create_result.stderr}"
        print(f"Reference list created: {list_name}")

        # 2. Get the reference list to confirm creation
        get_cmd = (
            [
                "secops",
            ]
            + common_args
            + ["reference-list", "get", "--name", list_name]
        )

        get_result = subprocess.run(
            get_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check that get was successful
        assert get_result.returncode == 0, f"Get failed: {get_result.stderr}"
        list_data = json.loads(get_result.stdout)
        print(f"Successfully retrieved reference list: {list_data['name']}")

        # Note: Reference list deletion is not currently supported by the API
        print(
            f"Skipping deletion of reference list {list_name} - deletion not supported by API"
        )

    except Exception as e:
        print(f"Test failed with exception: {e}")
        # Note: Reference list deletion is not currently supported by the API,
        # so we can't clean up test reference lists
        print(
            f"Warning: Test reference list {list_name} will remain since deletion is not supported"
        )
        raise


@pytest.mark.integration
def test_cli_reference_list_api_investigation(cli_env, common_args):
    """Test reference list API interactions directly using the SecOpsClient."""
    from secops import SecOpsClient
    from secops.chronicle.reference_list import (
        ReferenceListSyntaxType,
        ReferenceListView,
    )
    from tests.config import CHRONICLE_CONFIG

    # Generate unique name for reference list
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    list_name = f"test_cli_api_{timestamp}"

    # Create a direct client instance
    client = SecOpsClient()
    chronicle = client.chronicle(**CHRONICLE_CONFIG)

    print("\n=== Reference List API Test ===\n")

    try:
        # 1. Create a reference list
        print(f"Creating reference list: {list_name}")
        created = chronicle.create_reference_list(
            name=list_name,
            description="API Test Reference List",
            entries=["test1.example.com", "test2.example.com"],
            syntax_type=ReferenceListSyntaxType.STRING,
        )
        print(f"Creation response: {created}")
        print(f"Reference list name: {created.get('name', 'N/A')}")

        # 2. Get the reference list
        print(f"\nGetting reference list: {list_name}")
        retrieved = chronicle.get_reference_list(list_name, view=ReferenceListView.FULL)
        print(f"Get response: {retrieved}")
        print(f"Retrieved name: {retrieved.get('name', 'N/A')}")

        # 3. List reference lists and check if ours is included
        print("\nListing all reference lists")
        all_lists = chronicle.list_reference_lists()
        found = False
        for ref_list in all_lists:
            if ref_list.get("name", "").endswith(list_name):
                found = True
                print(f"Found in list: {ref_list.get('name')}")
                break

        if not found:
            print(f"WARNING: Reference list {list_name} not found in list results")

        # 4. Examine delete endpoint
        # Print what the delete URL would be
        instance_id = CHRONICLE_CONFIG.get("customer_id")
        project_id = CHRONICLE_CONFIG.get("project_id")
        region = CHRONICLE_CONFIG.get("region", "us")
        base_url = f"https://{region}-chronicle.googleapis.com/v1alpha"

        delete_url = f"{base_url}/{project_id}/locations/{region}/instances/{instance_id}/referenceLists/{list_name}"
        print(f"\nDelete would use URL: {delete_url}")

        # Note: Reference list deletion is not currently supported by the API
        print(
            f"\nSkipping deletion of reference list {list_name} - deletion not supported by API"
        )

    except Exception as e:
        print(f"Test encountered an error: {e}")
        raise


@pytest.mark.integration
def test_cli_parser_run_with_auto_parser(cli_env, common_args):
    """Test the 'parser run' command using auto parser selection.

    This test runs OKTA logs against active OKTA
    without explicitly providing the parser file or code in the run command.
    """
    test_log_type = "OKTA"

    # Test logs
    test_log = """{"actor":{"alternateId":"mark.taylor@cymbal-investments.org","displayName":"Mark Taylor","id":"00u4j7xcb5N6zfiRP5d8","type":"User"},"client":{"userAgent":{"rawUserAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36","os":"Windows 10","browser":"CHROME"},"ipAddress":"96.6.127.53","geographicalContext":{"city":"New York","state":"New York","country":"United States","postalCode":"10118","geolocation":{"lat":40.7123,"lon":-74.0068}}},"displayMessage":"Max sign in attempts exceeded","eventType":"user.account.lock","outcome":{"result":"FAILURE","reason":"LOCKED_OUT"},"published":"2025-06-19T21:51:50.116Z","securityContext":{"asNumber":20940,"asOrg":"akamai technologies inc.","isp":"akamai international b.v.","domain":"akamaitechnologies.com","isProxy":false},"severity":"DEBUG","legacyEventType":"core.user_auth.account_locked","uuid":"5b90a94a-d7ba-11ea-834a-85c24a1b2121","version":"0"}"""

    run_cmd = (
        [
            "secops",
        ]
        + common_args
        + [
            "parser",
            "run",
            "--log-type",
            test_log_type,
            "--log",
            test_log,
        ]
    )

    run_result = subprocess.run(
        run_cmd, env=cli_env, capture_output=True, text=True
    )

    # Check the run executed successfully
    assert (
        run_result.returncode == 0
    ), f"Parser run failed: {run_result.stderr}"

    # Parse and verify output
    output = json.loads(run_result.stdout)
    assert "runParserResults" in output

    # Should have processed both logs
    assert (
        len(output["runParserResults"]) > 0
    ), "Expected log parsing results"

@pytest.mark.integration
def test_cli_generate_udm_key_value_mapping(cli_env, common_args):
    """Test the generate-udm-mapping command."""
    log_file_path = ""
    try:
        # Create a temporary file with sample JSON log content
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w+", delete=False
        ) as temp_file:
            # Sample JSON log similar to what's used in the API test
            json_log = """
            {
                "events": [
                    {
                        "id": "123",
                        "user": "test_user",
                        "source_ip": "192.168.1.10",
                        "destination_url": "www.example.com",
                        "action_taken": "allowed",
                        "timestamp": 1588059648129
                    },
                    {
                        "id": "231",
                        "user": "test_user2",
                        "source_ip": "192.168.1.9",
                        "destination_url": "www.example2.com",
                        "action_taken": "allowed",
                        "timestamp": 1588059649129
                    }
                ]
            }
            """
            temp_file.write(json_log)
            temp_file.flush()
            log_file_path = temp_file.name

        print(f"\nTesting generate-udm-mapping with file: {log_file_path}")
        generating_udm_cmd = (
            [
                "secops",
            ]
            + common_args
            + [
                "log",
                "generate-udm-mapping",
                "--log-format",
                "JSON",
                "--log-file",
                log_file_path,
            ]
        )

        gum_result = subprocess.run(
            generating_udm_cmd, env=cli_env, capture_output=True, text=True
        )

        # Check the run executed successfully
        assert (
            gum_result.returncode == 0
        ), f"Generate UDM key/value mapping failed: {gum_result.stderr}"

        mapping_data = json.loads(gum_result.stdout)

        expected_fields = [
            "events.0.id",
            "events.0.user",
            "events.1.id",
            "events.1.user",
        ]

        # Check for expected fields
        assert all(field in mapping_data for field in expected_fields)

    except Exception as e:
        print(f"Error during generate-udm-mapping CLI test: {str(e)}")
        raise
    finally:
        # Clean up temp files
        if "log_file_path" in locals() and os.path.exists(log_file_path):
            os.unlink(log_file_path)


@pytest.mark.integration
def test_cli_udm_field_values(cli_env, common_args):
    """Test the search udm-field-values command with pagination."""
    # Execute the CLI command with page size parameter
    cmd = [
        "secops",
    ] + common_args + [
        "search", 
        "udm-field-values",
        "--query", 
        "source",
        "--page-size",
        "2"  # Small page size to test pagination
    ]

    result = subprocess.run(cmd, env=cli_env, capture_output=True, text=True)
    
    # Check that the command executed successfully
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    # Try to parse the output as JSON
    try:
        output = json.loads(result.stdout)
        
        # Verify basic response structure
        assert "valueMatches" in output, "Response should contain valueMatches"
        assert "fieldMatches" in output, "Response should contain fieldMatches"
        assert "fieldMatchRegex" in output, "Response should contain fieldMatchRegex"
        
        # Verify query is reflected in response
        assert output["fieldMatchRegex"] == "source", "Field match regex should match query"
        
        # Verify pagination is working
        assert len(output["valueMatches"]) <= 2, "Should respect page size parameter"
        
    except json.JSONDecodeError:
        # If not valid JSON, fail the test
        assert False, f"Output is not valid JSON: {result.stdout}"
