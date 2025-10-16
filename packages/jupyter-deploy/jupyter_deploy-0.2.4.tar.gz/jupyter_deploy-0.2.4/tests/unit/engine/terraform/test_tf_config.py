import subprocess
import unittest
from collections import OrderedDict
from pathlib import Path
from unittest.mock import Mock, patch

from pydantic import ValidationError

from jupyter_deploy.engine.terraform.tf_config import TerraformConfigHandler
from jupyter_deploy.engine.terraform.tf_constants import (
    TF_DEFAULT_PLAN_FILENAME,
    TF_ENGINE_DIR,
    TF_PRESETS_DIR,
)
from jupyter_deploy.engine.vardefs import (
    BoolTemplateVariableDefinition,
    DictStrTemplateVariableDefinition,
    FloatTemplateVariableDefinition,
    ListStrTemplateVariableDefinition,
    StrTemplateVariableDefinition,
    TemplateVariableDefinition,
)


class TestTerraformConfigHandler(unittest.TestCase):
    MOCK_OVERRIDE_PRESET_PATH = Path("/mock/path/engine/jdinputs.preset.override.tfvars")
    MOCK_RECORD_VARS_PATH = Path("/mock/path/engine/jdinputs.auto.tfvars")
    MOCK_RECORD_SECRETS_PATH = Path("/mock/path/engine/jdinputs.secrets.auto.tfvars")

    def get_mock_variable_handler_and_fns(self) -> tuple[Mock, dict[str, Mock]]:
        mock_handler = Mock()
        mock_get_recorded_variables_filepath = Mock()
        mock_get_recorded_secrets_filepath = Mock()
        mock_reset_recorded_variables = Mock()
        mock_reset_recorded_secrets = Mock()
        mock_sync_engine_varfiles = Mock()
        mock_sync_variables_config = Mock()
        mock_get_template_variables = Mock()
        mock_update_variable_records = Mock()
        mock_create_filtered_preset_file = Mock()

        mock_handler.get_recorded_variables_filepath = mock_get_recorded_variables_filepath
        mock_handler.get_recorded_secrets_filepath = mock_get_recorded_secrets_filepath
        mock_handler.reset_recorded_variables = mock_reset_recorded_variables
        mock_handler.reset_recorded_secrets = mock_reset_recorded_secrets
        mock_handler.sync_engine_varfiles_with_project_variables_config = mock_sync_engine_varfiles
        mock_handler.sync_project_variables_config = mock_sync_variables_config
        mock_handler.get_template_variables = mock_get_template_variables
        mock_handler.update_variable_records = mock_update_variable_records
        mock_handler.create_filtered_preset_file = mock_create_filtered_preset_file

        mock_get_recorded_variables_filepath.return_value = TestTerraformConfigHandler.MOCK_RECORD_VARS_PATH
        mock_get_recorded_secrets_filepath.return_value = TestTerraformConfigHandler.MOCK_RECORD_SECRETS_PATH
        mock_create_filtered_preset_file.return_value = TestTerraformConfigHandler.MOCK_OVERRIDE_PRESET_PATH

        return mock_handler, {
            "get_recorded_variables_filepath": mock_get_recorded_variables_filepath,
            "get_recorded_secrets_filepath": mock_get_recorded_secrets_filepath,
            "reset_recorded_variables": mock_reset_recorded_variables,
            "reset_recorded_secrets": mock_reset_recorded_secrets,
            "sync_engine_varfiles_with_project_variables_config": mock_sync_engine_varfiles,
            "sync_project_variables_config": mock_sync_variables_config,
            "get_template_variables": mock_get_template_variables,
            "update_variables_record": mock_update_variable_records,
            "create_filtered_preset_file": mock_create_filtered_preset_file,
        }

    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_class_can_instantiate(self, mock_variable_handler_cls: Mock) -> None:
        # Arrange
        path = Path("/fake/path")
        manifest = Mock()

        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        handler = TerraformConfigHandler(path, manifest)

        # Assert
        self.assertIsNotNone(handler)
        self.assertEqual(handler.plan_out_path, path / TF_ENGINE_DIR / TF_DEFAULT_PLAN_FILENAME)
        self.assertEqual(handler.project_manifest, manifest)
        self.assertEqual(handler.tf_variables_handler, mock_vars_handler)

        # expensive methods of EngineVariablesHandler are not called
        mock_vars_fns["get_template_variables"].assert_not_called()
        mock_vars_fns["update_variables_record"].assert_not_called()

    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_class_uses_custom_output_file_when_provided(self, mock_variable_handler_cls: Mock) -> None:
        # Arrange
        path = Path("/fake/path")
        manifest = Mock()
        custom_output = "custom-output-file"
        mock_vars_handler, _ = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        handler = TerraformConfigHandler(path, manifest, output_filename=custom_output)

        # Assert
        self.assertIsNotNone(handler)
        self.assertEqual(handler.plan_out_path, path / TF_ENGINE_DIR / custom_output)
        self.assertEqual(handler.tf_variables_handler, mock_vars_handler)

    @patch("jupyter_deploy.fs_utils.file_exists")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_verify_preset_exists_calls_fs_util(self, mock_variable_handler_cls: Mock, mock_file_exists: Mock) -> None:
        # Arrange
        path = Path("/fake/path")
        mock_vars_handler, _ = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        handler = TerraformConfigHandler(path, Mock())

        # Act
        handler.verify_preset_exists("all")

        # Assert
        mock_file_exists.assert_called_once_with(
            file_path=path / TF_ENGINE_DIR / TF_PRESETS_DIR / "defaults-all.tfvars"
        )

    @patch("jupyter_deploy.fs_utils.find_matching_filenames")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_list_presets_calls_fs_util(self, mock_variable_handler_cls: Mock, mock_find: Mock) -> None:
        mock_find.return_value = [
            "defaults-all.tfvars",
            "defaults-base.tfvars",
            "defaults-all-except-instance.tfvars",
        ]

        # Arrange
        path = Path("/fake/path")
        mock_vars_handler, _ = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        handler = TerraformConfigHandler(path, Mock())

        # Act
        presets = handler.list_presets()

        # Assert
        self.assertEqual(sorted(["all", "all-except-instance", "base", "none"]), sorted(presets))
        mock_find.assert_called_once_with(
            dir_path=handler.engine_dir_path / TF_PRESETS_DIR,
            file_pattern="defaults-*.tfvars",
        )

    @patch("jupyter_deploy.fs_utils.find_matching_filenames")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_list_presets_always_returns_none(self, mock_variable_handler_cls: Mock, mock_find: Mock) -> None:
        mock_find.return_value = []

        # Arrange
        path = Path("/fake/path")
        mock_vars_handler, _ = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        handler = TerraformConfigHandler(path, Mock())

        # Act
        presets = handler.list_presets()

        # Assert
        self.assertEqual(["none"], presets)

    @patch("jupyter_deploy.verify_utils.verify_tools_installation")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_verify_requirements_pulls_manifest_and_call_verify(
        self, mock_variable_handler_cls: Mock, mock_verify: Mock
    ) -> None:
        # Arrange
        path = Path("/fake/path")
        mock_manifest = Mock()
        mock_get_requirements = Mock()
        mock_manifest.get_requirements = mock_get_requirements

        mock_req1 = Mock()
        mock_req2 = Mock()
        mock_get_requirements.return_value = [mock_req1, mock_req2]

        mock_verify.return_value = True
        mock_vars_handler, _ = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler

        handler = TerraformConfigHandler(path, mock_manifest)

        # Act
        result = handler.verify_requirements()

        # Assert
        self.assertTrue(result)
        mock_get_requirements.assert_called_once()
        mock_verify.assert_called_once_with([mock_req1, mock_req2])

    @patch("jupyter_deploy.verify_utils.verify_tools_installation")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_verify_requirements_raises_when_checks_raise(
        self, mock_variable_handler_cls: Mock, mock_verify: Mock
    ) -> None:
        # Arrange
        mock_manifest = Mock()
        mock_get_requirements = Mock()
        mock_manifest.get_requirements = mock_get_requirements
        mock_verify.side_effect = Exception("Terraform check failed")

        mock_vars_handler, _ = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler

        handler = TerraformConfigHandler(Path("/fake/path"), mock_manifest)

        # Act & Assert
        with self.assertRaises(Exception) as e:
            handler.verify_requirements()
        self.assertEqual(str(e.exception), "Terraform check failed")

    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_reset_recorded_variables_calls_vars_handler(self, mock_variable_handler_cls: Mock) -> None:
        # Arrange
        path = Path("/fake/path")
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        handler = TerraformConfigHandler(path, Mock())

        # Act
        handler.reset_recorded_variables()

        # Assert
        mock_vars_fns["reset_recorded_variables"].assert_called_once()

    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_reset_recorded_secrets_calls_vars_handler(self, mock_variable_handler_cls: Mock) -> None:
        # Arrange
        path = Path("/fake/path")
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        handler = TerraformConfigHandler(path, Mock())

        # Act
        handler.reset_recorded_secrets()

        # Assert
        mock_vars_fns["reset_recorded_secrets"].assert_called_once()

    @patch("jupyter_deploy.cmd_utils.run_cmd_and_pipe_to_terminal")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_configure_calls_tf_init(self, mock_variable_handler_cls: Mock, mock_run_cmd: Mock) -> None:
        # Arrange
        mock_vars_handler, _ = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_run_cmd.return_value = (0, False)  # Return code 0, no timeout
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Mock the variables handler
        mock_variables_handler = Mock()
        handler.variables_handler = mock_variables_handler

        # Act
        handler.configure()

        # Assert
        self.assertGreaterEqual(mock_run_cmd.call_count, 1)
        init_cmds = mock_run_cmd.mock_calls[0][1][0]
        init_kwargs = mock_run_cmd.mock_calls[0][2]
        self.assertEqual(init_cmds[:2], ["terraform", "init"])
        self.assertEqual(init_kwargs, {"exec_dir": Path("/fake/path/engine")})

    @patch("jupyter_deploy.cmd_utils.run_cmd_and_pipe_to_terminal")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_configure_calls_tf_plan_with_a_named_plan(
        self, mock_variable_handler_cls: Mock, mock_run_cmd: Mock
    ) -> None:
        # Arrange
        # First call for init returns success
        # Second call for plan returns success
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_run_cmd.side_effect = [(0, False), (0, False)]
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Act
        result = handler.configure()

        # Assert
        # Check the second call was to plan
        self.assertTrue(result)
        self.assertEqual(mock_run_cmd.call_count, 2)

        plan_cmds = mock_run_cmd.mock_calls[1][1][0]
        plan_kwargs = mock_run_cmd.mock_calls[0][2]
        self.assertEqual(len(plan_cmds), 3)
        self.assertEqual(plan_cmds[:2], ["terraform", "plan"])
        self.assertIn("-out=", plan_cmds[2])
        self.assertEqual(plan_kwargs, {"exec_dir": Path("/fake/path/engine")})
        mock_vars_fns["sync_engine_varfiles_with_project_variables_config"].assert_called_once()

    @patch("jupyter_deploy.cmd_utils.run_cmd_and_pipe_to_terminal")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_configure_calls_tf_plan_passes_preset(self, mock_variable_handler_cls: Mock, mock_run_cmd: Mock) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        # First call for init returns success
        # Second call for plan returns success
        mock_run_cmd.side_effect = [(0, False), (0, False)]
        path = Path("/fake/path")
        handler = TerraformConfigHandler(path, Mock())

        # Act
        result = handler.configure(preset_name="all")

        # Assert
        # Check the second call was to plan
        self.assertTrue(result)
        self.assertEqual(mock_run_cmd.call_count, 2)

        plan_cmds = mock_run_cmd.mock_calls[1][1][0]
        plan_kwargs = mock_run_cmd.mock_calls[0][2]
        self.assertEqual(len(plan_cmds), 4)
        self.assertEqual(plan_cmds[:2], ["terraform", "plan"])
        self.assertIn("-out=", plan_cmds[2])
        self.assertEqual(plan_kwargs, {"exec_dir": Path("/fake/path/engine")})

        expect_called_path = path / TF_ENGINE_DIR / TF_PRESETS_DIR / "defaults-all.tfvars"
        expect_path = TestTerraformConfigHandler.MOCK_OVERRIDE_PRESET_PATH
        self.assertEqual(f"-var-file={expect_path.absolute()}", plan_cmds[3])
        mock_vars_fns["sync_engine_varfiles_with_project_variables_config"].assert_called_once()
        mock_vars_fns["create_filtered_preset_file"].assert_called_once_with(expect_called_path)

    @patch("jupyter_deploy.cmd_utils.run_cmd_and_pipe_to_terminal")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_configure_calls_tf_plan_with_variable_override(
        self, mock_variable_handler_cls: Mock, mock_run_cmd: Mock
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        # First call for init returns success
        # Second call for plan returns success
        mock_run_cmd.side_effect = [(0, False), (0, False)]
        path = Path("/fake/path")
        handler = TerraformConfigHandler(path, Mock())

        mock_var1 = Mock(spec=StrTemplateVariableDefinition)
        mock_var2 = Mock(spec=FloatTemplateVariableDefinition)
        mock_var3 = Mock(spec=BoolTemplateVariableDefinition)
        mock_var4 = Mock(spec=ListStrTemplateVariableDefinition)
        mock_var5 = Mock(spec=DictStrTemplateVariableDefinition)
        mock_variables: dict[str, TemplateVariableDefinition] = OrderedDict(
            {"var1": mock_var1, "var2": mock_var2, "var3": mock_var3, "var4": mock_var4, "var5": mock_var5}
        )
        for idx, key in enumerate(mock_variables.keys()):
            mock_variables[key].variable_name = f"var{idx + 1}"

        mock_var1.assigned_value = "some-value"
        mock_var2.assigned_value = 3.1459
        mock_var3.assigned_value = True
        mock_var4.assigned_value = ["email1@example.com", "email2@example.com"]
        mock_var5.assigned_value = {"Key1": "Val1", "Key2": "Val2"}

        # Act
        result = handler.configure(preset_name="all", variable_overrides=mock_variables)

        # Assert
        # Check the second call was to plan
        self.assertTrue(result)
        self.assertEqual(mock_run_cmd.call_count, 2)
        mock_vars_fns["sync_engine_varfiles_with_project_variables_config"].assert_called_once()
        mock_vars_fns["create_filtered_preset_file"].assert_called_once()
        plan_cmds = mock_run_cmd.mock_calls[1][1][0]

        expect_path = TestTerraformConfigHandler.MOCK_OVERRIDE_PRESET_PATH
        self.assertEqual(f"-var-file={expect_path.absolute()}", plan_cmds[3])

        plan_cmds_len = len(plan_cmds)

        # should append the 3 variables as [-var, varname:varvalue]
        self.assertEqual("-var", plan_cmds[plan_cmds_len - 10])
        self.assertEqual("var1=some-value", plan_cmds[plan_cmds_len - 9])

        self.assertEqual("-var", plan_cmds[plan_cmds_len - 8])
        self.assertEqual("var2=3.1459", plan_cmds[plan_cmds_len - 7])

        self.assertEqual("-var", plan_cmds[plan_cmds_len - 6])
        self.assertEqual("var3=true", plan_cmds[plan_cmds_len - 5])

        self.assertEqual("-var", plan_cmds[plan_cmds_len - 4])
        self.assertEqual('var4=["email1@example.com", "email2@example.com"]', plan_cmds[plan_cmds_len - 3])

        self.assertEqual("-var", plan_cmds[plan_cmds_len - 2])
        self.assertEqual('var5={"Key1": "Val1", "Key2": "Val2"}', plan_cmds[plan_cmds_len - 1])

    @patch("jupyter_deploy.cmd_utils.run_cmd_and_pipe_to_terminal")
    @patch("rich.console.Console")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_configure_does_not_call_plan_if_tf_init_fails(
        self, mock_variable_handler_cls: Mock, mock_console: Mock, mock_run_cmd: Mock
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_run_cmd.return_value = (1, False)  # Return code 1 (failure), no timeout
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Act
        result = handler.configure()

        # Assert
        self.assertFalse(result)
        self.assertEqual(mock_run_cmd.call_count, 1)  # Only init should be called
        mock_cmd_call = mock_run_cmd.mock_calls[0]
        self.assertEqual(mock_cmd_call[1][0][:2], ["terraform", "init"])
        mock_vars_fns["sync_engine_varfiles_with_project_variables_config"].assert_not_called()

    @patch("jupyter_deploy.cmd_utils.run_cmd_and_pipe_to_terminal")
    @patch("rich.console.Console")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_configure_does_not_call_plan_if_tf_init_timesout(
        self, mock_variable_handler_cls: Mock, mock_console: Mock, mock_run_cmd: Mock
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_run_cmd.return_value = (0, True)  # Return code 0, but timed out
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Act
        result = handler.configure()

        # Assert
        self.assertFalse(result)
        self.assertEqual(mock_run_cmd.call_count, 1)  # Only init should be called
        mock_cmd_call = mock_run_cmd.mock_calls[0]
        self.assertEqual(mock_cmd_call[1][0][:2], ["terraform", "init"])
        mock_vars_fns["sync_engine_varfiles_with_project_variables_config"].assert_not_called()

    @patch("jupyter_deploy.cmd_utils.run_cmd_and_pipe_to_terminal")
    @patch("rich.console.Console")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_configure_print_to_console_if_plan_fails(
        self, mock_variable_handler_cls: Mock, mock_console: Mock, mock_run_cmd: Mock
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        # First call for init returns success
        # Second call for plan returns failure
        mock_run_cmd.side_effect = [(0, False), (1, False)]
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Act
        result = handler.configure()

        # Assert
        self.assertFalse(result)
        self.assertEqual(mock_run_cmd.call_count, 2)
        mock_vars_fns["sync_engine_varfiles_with_project_variables_config"].assert_called_once()
        self.assertEqual(mock_console_instance.print.call_count, 1)
        mock_print_call = mock_console_instance.print.mock_calls[0]
        self.assertTrue(type(mock_print_call[1][0]) == str)  # noqa: E721
        self.assertTrue(len(mock_print_call[1][0]) > 0)

    @patch("jupyter_deploy.cmd_utils.run_cmd_and_pipe_to_terminal")
    @patch("rich.console.Console")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_configure_print_to_console_if_plan_timesout(
        self, mock_variable_handler_cls: Mock, mock_console: Mock, mock_run_cmd: Mock
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        # First call for init returns success
        # Second call for plan returns timeout
        mock_run_cmd.side_effect = [(0, False), (0, True)]
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Act
        result = handler.configure()

        # Assert
        self.assertFalse(result)
        self.assertEqual(mock_run_cmd.call_count, 2)
        mock_vars_fns["sync_engine_varfiles_with_project_variables_config"].assert_called_once()
        self.assertEqual(mock_console_instance.print.call_count, 1)
        mock_print_call = mock_console_instance.print.mock_calls[0]
        self.assertTrue(type(mock_print_call[1][0]) == str)  # noqa: E721
        self.assertTrue(len(mock_print_call[1][0]) > 0)

    @patch("jupyter_deploy.cmd_utils.run_cmd_and_capture_output")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_record_noop_when_both_flags_are_false(self, mock_variable_handler_cls: Mock, mock_capture: Mock) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Act
        handler.record()

        # Assert
        mock_capture.assert_not_called()
        mock_vars_fns["sync_project_variables_config"].assert_not_called()

    @patch("jupyter_deploy.fs_utils.write_inline_file_content")
    @patch("jupyter_deploy.engine.terraform.tf_plan.format_plan_variables")
    @patch("jupyter_deploy.engine.terraform.tf_plan.extract_variables_from_json_plan")
    @patch("jupyter_deploy.cmd_utils.run_cmd_and_capture_output")
    @patch("rich.console.Console")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_record_calls_plan_and_save_vars_only_on_var_flag(
        self,
        mock_variable_handler_cls: Mock,
        mock_console: Mock,
        mock_capture: Mock,
        mock_extract: Mock,
        mock_format: Mock,
        mock_write: Mock,
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        mock_capture.return_value = "i-am-a-serialized-plan"

        mock_var1 = Mock()
        mock_var2 = Mock()
        mock_secret1 = Mock()
        mock_var1.value = 1
        mock_var2.value = "two"
        mock_secret1.value = "nuclear-codes"
        mock_extract.return_value = ({"var1": mock_var1, "var2": mock_var2}, {"secret1": mock_secret1})
        mock_format.return_value = ["var1 = 1\n", 'var2 = "two"\n']

        path = Path("/fake/path")
        handler = TerraformConfigHandler(path, Mock())

        # Act
        handler.record(record_vars=True)

        # Assert
        mock_capture.assert_called_once()
        mock_plan_cmd_capture = mock_capture.mock_calls[0]
        self.assertEqual(mock_plan_cmd_capture[1][0][:3], ["terraform", "show", "-json"])

        mock_extract.assert_called_once_with("i-am-a-serialized-plan")
        mock_format.assert_called_once_with({"var1": mock_var1, "var2": mock_var2})
        mock_write.assert_called_once()

        mock_write_call = mock_write.mock_calls[0]
        self.assertEqual(mock_write_call[1][0], TestTerraformConfigHandler.MOCK_RECORD_VARS_PATH)
        self.assertIn("var1 = 1\n", mock_write_call[1][1])
        self.assertIn('var2 = "two"\n', mock_write_call[1][1])

        mock_vars_fns["sync_project_variables_config"].assert_called_once_with({"var1": 1, "var2": "two"})

    @patch("jupyter_deploy.fs_utils.write_inline_file_content")
    @patch("jupyter_deploy.engine.terraform.tf_plan.format_plan_variables")
    @patch("jupyter_deploy.engine.terraform.tf_plan.extract_variables_from_json_plan")
    @patch("jupyter_deploy.cmd_utils.run_cmd_and_capture_output")
    @patch("rich.console.Console")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_record_calls_plan_and_save_secrets_only_on_secret_flag(
        self,
        mock_variable_handler_cls: Mock,
        mock_console: Mock,
        mock_capture: Mock,
        mock_extract: Mock,
        mock_format: Mock,
        mock_write: Mock,
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        mock_capture.return_value = "i-am-a-serialized-plan"

        mock_var1 = Mock()
        mock_var2 = Mock()
        mock_secret = Mock()
        mock_var1.value = 1
        mock_var2.value = "two"
        mock_secret.value = "nuclear-codes"
        mock_extract.return_value = ({"var1": mock_var1, "var2": mock_var2}, {"secret1": mock_secret})
        mock_format.return_value = ['secret1 = "nuclear-codes"\n']

        path = Path("/fake/path")
        handler = TerraformConfigHandler(path, Mock())

        # Act
        handler.record(record_secrets=True)

        # Assert
        mock_capture.assert_called_once()
        mock_extract.assert_called_once_with("i-am-a-serialized-plan")
        mock_format.assert_called_once_with({"secret1": mock_secret})
        mock_write.assert_called_once()

        mock_write_call = mock_write.mock_calls[0]
        self.assertEqual(mock_write_call[1][0], TestTerraformConfigHandler.MOCK_RECORD_SECRETS_PATH)
        self.assertIn('secret1 = "nuclear-codes"\n', mock_write_call[1][1])

        mock_vars_fns["sync_project_variables_config"].assert_called_once_with({"secret1": "nuclear-codes"})

    @patch("jupyter_deploy.fs_utils.write_inline_file_content")
    @patch("jupyter_deploy.engine.terraform.tf_plan.format_plan_variables")
    @patch("jupyter_deploy.engine.terraform.tf_plan.extract_variables_from_json_plan")
    @patch("jupyter_deploy.cmd_utils.run_cmd_and_capture_output")
    @patch("rich.console.Console")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_record_should_call_plan_only_once_when_both_flags_are_passed(
        self,
        mock_variable_handler_cls: Mock,
        mock_console: Mock,
        mock_capture: Mock,
        mock_extract: Mock,
        mock_format: Mock,
        mock_write: Mock,
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        mock_print = Mock()
        mock_console_instance.print = mock_print
        mock_capture.return_value = "i-am-a-serialized-plan"
        mock_var1 = Mock()
        mock_var2 = Mock()
        mock_secret = Mock()
        mock_var1.value = 1
        mock_var2.value = "two"
        mock_secret.value = "nuclear-codes"
        mock_extract.return_value = ({"var1": mock_var1, "var2": mock_var2}, {"secret1": mock_secret})
        mock_format.side_effect = [["var1 = 1\n", 'var2 = "two"\n'], ['secret1 = "nuclear-codes"\n']]

        path = Path("/fake/path")
        handler = TerraformConfigHandler(path, Mock())

        # Act
        handler.record(record_vars=True, record_secrets=True)

        # Assert
        mock_capture.assert_called_once()
        mock_extract.assert_called_once_with("i-am-a-serialized-plan")
        self.assertEqual(mock_format.call_count, 2)
        self.assertEqual(mock_write.call_count, 2)

        mock_write_vars_call = mock_write.mock_calls[0]
        self.assertEqual(mock_write_vars_call[1][0], TestTerraformConfigHandler.MOCK_RECORD_VARS_PATH)
        self.assertIn("var1 = 1\n", mock_write_vars_call[1][1])
        self.assertIn('var2 = "two"\n', mock_write_vars_call[1][1])

        mock_write_secrets_call = mock_write.mock_calls[1]
        self.assertEqual(mock_write_secrets_call[1][0], TestTerraformConfigHandler.MOCK_RECORD_SECRETS_PATH)
        self.assertIn('secret1 = "nuclear-codes"\n', mock_write_secrets_call[1][1])

        mock_vars_fns["sync_project_variables_config"].assert_called_once_with(
            {"var1": 1, "var2": "two", "secret1": "nuclear-codes"}
        )

    @patch("jupyter_deploy.fs_utils.write_inline_file_content")
    @patch("jupyter_deploy.cmd_utils.run_cmd_and_capture_output")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_catches_plan_retrieve_errors_and_print(
        self,
        mock_variable_handler_cls: Mock,
        mock_capture: Mock,
        mock_write: Mock,
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_capture.side_effect = subprocess.CalledProcessError(
            1, ["terraform", "show", "-json"], "something went wrong", None
        )
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Act
        handler.record(record_vars=True)

        # Assert
        mock_write.assert_not_called()
        mock_vars_fns["sync_project_variables_config"].assert_not_called()

    @patch("jupyter_deploy.fs_utils.write_inline_file_content")
    @patch("jupyter_deploy.engine.terraform.tf_plan.extract_variables_from_json_plan")
    @patch("jupyter_deploy.cmd_utils.run_cmd_and_capture_output")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_catches_plan_validation_errors(
        self,
        mock_variable_handler_cls: Mock,
        mock_capture: Mock,
        mock_extract: Mock,
        mock_write: Mock,
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_extract.side_effect = ValidationError("some error", [])
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Act
        handler.record(record_secrets=True)

        # Assert
        mock_capture.assert_called_once()
        mock_write.assert_not_called()
        mock_vars_fns["sync_project_variables_config"].assert_not_called()

    @patch("jupyter_deploy.fs_utils.write_inline_file_content")
    @patch("jupyter_deploy.engine.terraform.tf_plan.extract_variables_from_json_plan")
    @patch("jupyter_deploy.cmd_utils.run_cmd_and_capture_output")
    @patch("jupyter_deploy.engine.terraform.tf_variables.TerraformVariablesHandler")
    def test_catches_plan_json_parse_errors(
        self,
        mock_variable_handler_cls: Mock,
        mock_capture: Mock,
        mock_extract: Mock,
        mock_write: Mock,
    ) -> None:
        # Arrange
        mock_vars_handler, mock_vars_fns = self.get_mock_variable_handler_and_fns()
        mock_variable_handler_cls.return_value = mock_vars_handler
        mock_capture.return_value = "i-am-a-serialized-plan"
        mock_extract.side_effect = ValueError("Invalid JSON")
        handler = TerraformConfigHandler(Path("/fake/path"), Mock())

        # Act
        handler.record(record_secrets=True)

        # Assert
        mock_capture.assert_called_once()
        mock_extract.assert_called_once()
        mock_write.assert_not_called()
        mock_vars_fns["sync_project_variables_config"].assert_not_called()
