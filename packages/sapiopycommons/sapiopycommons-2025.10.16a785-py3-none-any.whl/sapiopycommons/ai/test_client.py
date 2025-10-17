import base64
import json
import os
from enum import Enum
from typing import Any

import grpc
from sapiopylib.rest.User import SapioUser

from sapiopycommons.ai.external_credentials import ExternalCredentials
from sapiopycommons.ai.protoapi.externalcredentials.external_credentials_pb2 import ExternalCredentialsPbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import FieldValuePbo
from sapiopycommons.ai.protoapi.plan.converter.converter_pb2 import ConverterDetailsRequestPbo, \
    ConverterDetailsResponsePbo, ConvertResponsePbo, ConvertRequestPbo
from sapiopycommons.ai.protoapi.plan.converter.converter_pb2_grpc import ConverterServiceStub
from sapiopycommons.ai.protoapi.plan.item.item_container_pb2 import ContentTypePbo
from sapiopycommons.ai.protoapi.plan.tool.entry_pb2 import StepBinaryContainerPbo, StepCsvRowPbo, \
    StepCsvHeaderRowPbo, StepCsvContainerPbo, StepJsonContainerPbo, StepTextContainerPbo, \
    StepItemContainerPbo, StepInputBatchPbo
from sapiopycommons.ai.protoapi.plan.tool.tool_pb2 import ProcessStepResponsePbo, ProcessStepRequestPbo, \
    ToolDetailsRequestPbo, ToolDetailsResponsePbo, ProcessStepResponseStatusPbo
from sapiopycommons.ai.protoapi.plan.tool.tool_pb2_grpc import ToolServiceStub
from sapiopycommons.ai.protoapi.session.sapio_conn_info_pb2 import SapioConnectionInfoPbo, SapioUserSecretTypePbo
from sapiopycommons.ai.protobuf_utils import ProtobufUtils
from sapiopycommons.general.aliases import FieldValue
from sapiopycommons.general.time_util import TimeUtil


class ContainerType(Enum):
    """
    An enum of the different container contents of a StepItemContainerPbo.
    """
    BINARY = "binary"
    CSV = "csv"
    JSON = "json"
    TEXT = "text"


# FR-47422: Created class.
class AgentOutput:
    """
    A class for holding the output of a TestClient that calls an AgentService. AgentOutput objects an be
    printed to show the output of the agent in a human-readable format.
    """
    agent_name: str

    status: str
    message: str

    # Outputs are lists of lists, where the outer lists are the different outputs of the tool, and the inner lists
    # are the entries for that output.
    binary_output: list[list[bytes]]
    csv_output: list[list[dict[str, Any]]]
    json_output: list[list[dict[str, Any]]]
    text_output: list[list[str]]

    new_records: list[dict[str, FieldValue]]

    logs: list[str]

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.binary_output = []
        self.csv_output = []
        self.json_output = []
        self.text_output = []
        self.new_records = []
        self.logs = []

    def save_outputs(self, path: str = "test_outputs", subfolder: str | None = None,
                     file_extensions: list[str] | None = None) -> None:
        """
        Save all outputs to files in the specified output directory.

        :param path: The directory to save the output files to.
        :param subfolder: An optional subfolder within the path to save the output files to. Useful for when you are
            calling the same agent multiple times for separate test cases.
        :param file_extensions: A list of file extensions to use for binary output files. The length of this list
            should match the number of binary outputs.
        """
        if not self:
            return
        output_path: str = os.path.join(path, self.agent_name)
        if subfolder:
            output_path = os.path.join(output_path, subfolder)
        os.makedirs(output_path, exist_ok=True)
        if self.binary_output and (file_extensions is None or len(file_extensions) != len(self.binary_output)):
            raise ValueError("File extensions must be provided for each binary output.")
        for i, output in enumerate(self.binary_output):
            ext: str = "." + file_extensions[i].lstrip(".")
            for j, entry in enumerate(output):
                with open(os.path.join(output_path, f"binary_output_{i}_{j}{ext}"), "wb") as f:
                    f.write(entry)
        for i, output in enumerate(self.csv_output):
            with open(os.path.join(output_path, f"csv_output_{i}.csv"), "w", encoding="utf-8") as f:
                headers = output[0].keys()
                f.write(",".join(headers) + "\n")
                for row in output:
                    f.write(",".join(f'"{str(row[h])}"' for h in headers) + "\n")
        for i, output in enumerate(self.json_output):
            for j, entry in enumerate(output):
                with open(os.path.join(output_path, f"json_output_{i}_{j}.json"), "w", encoding="utf-8") as f:
                    json.dump(entry, f, indent=2)
        for i, output in enumerate(self.text_output):
            for j, entry in enumerate(output):
                with open(os.path.join(output_path, f"text_output_{i}_{j}.txt"), "w", encoding="utf-8") as f:
                    f.write(entry)

    def __bool__(self):
        """
        Return True if the agent call was successful, False otherwise.
        """
        return self.status == "Success"

    def __str__(self):
        """
        Return a string representing a summary of the agent output.
        """
        ret_val: str = f"{self.agent_name} Output:\n"
        ret_val += f"\tStatus: {self.status}\n"
        ret_val += f"\tMessage: {self.message}\n"
        ret_val += "-" * 25 + "\n"

        if self.status == "Success":
            ret_val += f"Binary Output: {sum(len(x) for x in self.binary_output)} item(s) across {len(self.binary_output)} output(s)\n"
            for i, output in enumerate(self.binary_output, start=1):
                output: list[bytes]
                ret_val += f"\tBinary Output {i}:\n"
                for binary in output:
                    ret_val += f"\t\t{len(binary)} byte(s): {binary[:50]}...\n"

            ret_val += f"CSV Output: {sum(len(x) for x in self.csv_output)} item(s) across {len(self.csv_output)} output(s)\n"
            for i, output in enumerate(self.csv_output, start=1):
                output: list[dict[str, Any]]
                ret_val += f"\tCSV Output {i}:\n"
                ret_val += f"\t\tHeaders: {', '.join(output[0].keys())}\n"
                for j, csv_row in enumerate(output):
                    ret_val += f"\t\t{j}: {', '.join(f'{v}' for k, v in csv_row.items())}\n"

            ret_val += f"JSON Output: {sum(len(x) for x in self.json_output)} item(s) across {len(self.json_output)} output(s)\n"
            for i, output in enumerate(self.json_output, start=1):
                output: list[Any]
                ret_val += f"\tJSON Output {i}:\n"
                for json_obj in output:
                    ret_val += f"\t\t"
                    ret_val += json.dumps(json_obj, indent=2).replace("\n", "\n\t\t") + "\n"

            ret_val += f"Text Output: {sum(len(x) for x in self.text_output)} item(s) across {len(self.text_output)} output(s)\n"
            for i, output in enumerate(self.text_output, start=1):
                output: list[str]
                ret_val += f"\tText Output {i}:\n"
                for text in output:
                    ret_val += f"\t\t{text}\n"

            ret_val += f"New Records: {len(self.new_records)} item(s)\n"
            for record in self.new_records:
                ret_val += f"{json.dumps(record, indent=2)}\n"

        ret_val += f"Logs: {len(self.logs)} item(s)\n"
        for log in self.logs:
            ret_val += f"\t{log}\n"
        return ret_val


class TestClient:
    """
    A client for testing an AgentService.
    """
    grpc_server_url: str
    options: list[tuple[str, Any]] | None
    connection: SapioConnectionInfoPbo
    _request_inputs: list[StepItemContainerPbo]
    _config_fields: dict[str, FieldValuePbo]
    _credentials: list[ExternalCredentialsPbo]

    def __init__(self, grpc_server_url: str, message_mb_size: int = 1024, user: SapioUser | None = None,
                 options: list[tuple[str, Any]] | None = None):
        """
        :param grpc_server_url: The URL of the gRPC server to connect to.
        :param message_mb_size: The maximum size of a sent or received message in megabytes.
        :param user: Optional SapioUser object to use for the connection. If not provided, a default connection
            will be created with test credentials.
        :param options: Optional list of gRPC channel options.
        """
        self.grpc_server_url = grpc_server_url
        self.options = [
            ('grpc.max_send_message_length', message_mb_size * 1024 * 1024),
            ('grpc.max_receive_message_length', message_mb_size * 1024 * 1024)
        ]
        if options:
            self.options.extend(options)
        self._create_connection(user)
        self._request_inputs = []
        self._config_fields = {}
        self._credentials = []

    def _create_connection(self, user: SapioUser | None = None):
        """
        Create a SapioConnectionInfoPbo object with test credentials. This method can be overridden to
        create a user with specific credentials for testing.
        """
        self.connection = SapioConnectionInfoPbo()
        self.connection.username = user.username if user else "Testing"
        self.connection.webservice_url = user.url if user else "https://localhost:8080/webservice/api"
        self.connection.app_guid = user.guid if user else "1234567890"
        self.connection.rmi_host.append("Testing")
        self.connection.rmi_port = 9001
        if user and user.password:
            self.connection.secret_type = SapioUserSecretTypePbo.PASSWORD
            self.connection.secret = "Basic " + base64.b64encode(f'{user.username}:{user.password}'.encode()).decode()
        else:
            self.connection.secret_type = SapioUserSecretTypePbo.SESSION_TOKEN
            self.connection.secret = user.api_token if user and user.api_token else "test_api_token"

    def add_binary_input(self, input_data: list[bytes]) -> None:
        """
        Add a binary input to the the next request.
        """
        self._add_input(ContainerType.BINARY, StepBinaryContainerPbo(items=input_data))

    def add_csv_input(self, input_data: list[dict[str, Any]]) -> None:
        """
        Add a CSV input to the next request.
        """
        csv_items = []
        for row in input_data:
            csv_items.append(StepCsvRowPbo(cells=[str(value) for value in row.values()]))
        header = StepCsvHeaderRowPbo(cells=list(input_data[0].keys()))
        self._add_input(ContainerType.CSV, StepCsvContainerPbo(header=header, items=csv_items))

    def add_json_input(self, input_data: list[dict[str, Any]]) -> None:
        """
        Add a JSON input to the next request.
        """
        self._add_input(ContainerType.JSON, StepJsonContainerPbo(items=[json.dumps(x) for x in input_data]))

    def add_text_input(self, input_data: list[str]) -> None:
        """
        Add a text input to the next request.
        """
        self._add_input(ContainerType.TEXT, StepTextContainerPbo(items=input_data))

    def clear_inputs(self) -> None:
        """
        Clear all inputs that have been added to the next request.
        This is useful if you want to start a new request without the previous inputs.
        """
        self._request_inputs.clear()

    def add_config_field(self, field_name: str, value: FieldValue | list[str]) -> None:
        """
        Add a configuration field value to the next request.

        :param field_name: The name of the configuration field.
        :param value: The value to set for the configuration field. If a list is provided, it will be
            converted to a comma-separated string.
        """
        if isinstance(value, list):
            value = ",".join(str(x) for x in value)
        if not isinstance(value, FieldValuePbo):
            value = ProtobufUtils.value_to_field_pbo(value)
        self._config_fields[field_name] = value

    def add_config_fields(self, config_fields: dict[str, FieldValue | list[str]]) -> None:
        """
        Add multiple configuration field values to the next request.

        :param config_fields: A dictionary of configuration field names and their corresponding values.
        """
        for x, y in config_fields.items():
            self.add_config_field(x, y)

    def clear_configs(self) -> None:
        """
        Clear all configuration field values that have been added to the next request.
        This is useful if you want to start a new request without the previous configurations.
        """
        self._config_fields.clear()

    def add_credentials(self, credentials: list[ExternalCredentials]) -> None:
        """
        Add external credentials to the connection info for the next request.

        :param credentials: A list of ExternalCredentialsPbo objects to add to the connection info.
        """
        for cred in credentials:
            self._credentials.append(cred.to_pbo())

    def clear_credentials(self) -> None:
        """
        Clear all external credentials that have been added to the next request.
        This is useful if you want to start a new request without the previous credentials.
        """
        self._credentials.clear()

    def clear_request(self) -> None:
        """
        Clear all inputs and configuration fields that have been added to the next request.
        This is useful if you want to start a new request without the previous inputs and configurations.

        Credentials are not cleared, as they may be reused across multiple requests.
        """
        self.clear_inputs()
        self.clear_configs()

    def _add_input(self, container_type: ContainerType, items: Any) -> None:
        """
        Helper method for adding inputs to the next request.
        """
        container: StepItemContainerPbo | None = None
        match container_type:
            # The content type doesn't matter when we're just testing.
            case ContainerType.BINARY:
                container = StepItemContainerPbo(content_type=ContentTypePbo(), binary_container=items)
            case ContainerType.CSV:
                container = StepItemContainerPbo(content_type=ContentTypePbo(), csv_container=items)
            case ContainerType.JSON:
                container = StepItemContainerPbo(content_type=ContentTypePbo(), json_container=items)
            case ContainerType.TEXT:
                container = StepItemContainerPbo(content_type=ContentTypePbo(), text_container=items)
            case _:
                raise ValueError(f"Unsupported container type: {container_type}")
        self._request_inputs.append(container)

    def get_service_details(self) -> ToolDetailsResponsePbo:
        """
        Get the details of the agents from the server.

        :return: A ToolDetailsResponsePbo object containing the details of the agent service.
        """
        with grpc.insecure_channel(self.grpc_server_url, options=self.options) as channel:
            stub = ToolServiceStub(channel)
            return stub.GetToolDetails(ToolDetailsRequestPbo(sapio_conn_info=self.connection))

    def call_agent(self, agent_name: str, is_verbose: bool = True, is_dry_run: bool = False) -> AgentOutput:
        """
        Send the request to the agent service for a particular agent name. This will send all the inputs that have been
        added using the add_X_input functions.

        :param agent_name: The name of the agent to call on the server.
        :param is_verbose: If True, the agent will log verbosely.
        :param is_dry_run: If True, the agent will not be executed, but the request will be validated.
        :return: An AgentOutput object containing the results of the agent service call.
        """
        print(f"Calling agent \"{agent_name}\"...")
        with grpc.insecure_channel(self.grpc_server_url, options=self.options) as channel:
            stub = ToolServiceStub(channel)

            start = TimeUtil.now_in_millis()
            response: ProcessStepResponsePbo = stub.ProcessData(
                ProcessStepRequestPbo(
                    sapio_user=self.connection,
                    tool_name=agent_name,
                    config_field_values=self._config_fields,
                    dry_run=is_dry_run,
                    verbose_logging=is_verbose,
                    external_credential=self._credentials,
                    input=[
                        StepInputBatchPbo(is_partial=False, item_container=item)
                        for item in self._request_inputs
                    ]
                )
            )
            end = TimeUtil.now_in_millis()
            print(f"Agent call completed in {(end - start) / 1000.:.3f} seconds")

            results = AgentOutput(agent_name)

            match response.status:
                case ProcessStepResponseStatusPbo.SUCCESS:
                    results.status = "Success"
                case ProcessStepResponseStatusPbo.FAILURE:
                    results.status = "Failure"
                case _:
                    results.status = "Unknown"
            results.message = response.status_message

            for item in response.output:
                container = item.item_container

                if container.HasField("binary_container"):
                    results.binary_output.append(list(container.binary_container.items))
                elif container.HasField("csv_container"):
                    csv_output: list[dict[str, Any]] = []
                    for header in container.csv_container.header.cells:
                        output_row: dict[str, Any] = {}
                        for i, row in enumerate(container.csv_container.items):
                            output_row[header] = row.cells[i]
                        csv_output.append(output_row)
                    results.csv_output.append(csv_output)
                elif container.HasField("json_container"):
                    results.json_output.append([json.loads(x) for x in container.json_container.items])
                elif container.HasField("text_container"):
                    results.text_output.append(list(container.text_container.items))

            for record in response.new_records:
                field_map: dict[str, Any] = {x: ProtobufUtils.field_pbo_to_value(y) for x, y in record.fields.items()}
                results.new_records.append(field_map)

            results.logs.extend(response.log)

            return results


class TestConverterClient:
    """
    A client for testing a ConverterService.
    """
    grpc_server_url: str
    options: list[tuple[str, Any]] | None

    def __init__(self, grpc_server_url: str, options: list[tuple[str, Any]] | None = None):
        """
        :param grpc_server_url: The URL of the gRPC server to connect to.
        :param options: Optional list of gRPC channel options.
        """
        self.grpc_server_url = grpc_server_url
        self.options = options

    def get_converter_details(self) -> ConverterDetailsResponsePbo:
        """
        Get the details of the converters from the server.

        :return: A ToolDetailsResponsePbo object containing the details of the converter service.
        """
        with grpc.insecure_channel(self.grpc_server_url, options=self.options) as channel:
            stub = ConverterServiceStub(channel)
            return stub.GetConverterDetails(ConverterDetailsRequestPbo())

    def convert_content(self, input_container: StepItemContainerPbo, target_type: ContentTypePbo) \
            -> StepItemContainerPbo:
        """
        Convert the content of the input container to the target content type.

        :param input_container: The input container to convert. This container must have a ContentTypePbo set that
            matches one of the input types that the converter service supports.
        :param target_type: The target content type to convert to. This must match one of the target types that the
            converter service supports.
        :return: A StepItemContainerPbo object containing the converted content.
        """
        with grpc.insecure_channel(self.grpc_server_url, options=self.options) as channel:
            stub = ConverterServiceStub(channel)
            response: ConvertResponsePbo = stub.ConvertContent(
                ConvertRequestPbo(item_container=input_container, target_content_type=target_type)
            )
            return response.item_container
