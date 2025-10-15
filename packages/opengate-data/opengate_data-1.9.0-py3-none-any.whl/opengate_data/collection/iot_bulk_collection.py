import json
import os
from datetime import datetime
from typing import Any

import pandas as pd

from opengate_data.utils.utils import send_request, handle_exception, validate_type, set_method_call, parse_json


class IotBulkCollectionBuilder:
    """ Collection Bulk Builder """

    def __init__(self, opengate_client):
        self.client = opengate_client
        self.headers = self.client.headers
        self.requires: dict[str, Any] = {}
        self.device_identifier: str | None = None
        self.version: str | None = None
        self.payload: dict = {"devices": {}}
        self.method_calls: list = []

    @set_method_call
    def add_device_datastream_datapoints(
        self,
        device_id: str,
        datastream_id: str,
        datapoints: list[
            tuple[int | float | bool | dict | list | str, None | datetime | int, None | str, None | str]
        ],
        feed: str | None = None,  # feed opcional, puede pasarse como "100" o 100
    ) -> "IotBulkCollectionBuilder":
        """
        Add the datastream identifier and a list of datapoints with their value and at for data collection.

        add_datastream_datapoints("datastream_identifier", [(value, at, source, source_info)])

        Multiple datastreams can be grouped under a single identifier

        Args:
            datastream_id (str): The identifier for the datastream to which the datapoints will be added.
            datapoints (list[tuple[int | float | bool | dict | list, None | datetime | int, None | datetime | int]]): A list of tuples where each tuple
                represents a datapoint.  Each tuple contains the datapoint value and an optional timestamp ('at'):
                    value: Collected value
                    at: Number with the time in miliseconds from epoch of the measurement. If this field is None, the platform will assign the server current time to the datapoint whe data is received.

        Returns:
            IotCollectionBuilder: Returns itself to allow for method chaining.

        Example:
            ~~~python
            builder.add_datastream_datapoints("datastream_identifier_1", [(value1, datetime.now()), (value2, None, "HTTP-Basic", "OK")])
            builder.add_datastream_datapoints("datastream_identifier_2", [(value3, None), (value4, 1431602523123)])
            ~~~
        """
        validate_type(device_id, str, "Device identifier")
        validate_type(datastream_id, str, "Datastream identifier")
        validate_type(datapoints, list, "Datapoints")

        if feed is not None:
            validate_type(feed, str, "Feed")

        normalized: list[tuple] = []

        for dp in datapoints:
            if not isinstance(dp, tuple):
                raise ValueError("Each datapoint must be a tuple")

            value, at, fr, src, src_info = None, None, None, None, None

            if len(dp) == 2:
                value, at = dp
            elif len(dp) == 3:
                value, at, third = dp
                if isinstance(third, (int, datetime)) or third is None:
                    fr = third
                else:
                    src = third
            elif len(dp) == 4:
                value, at, third, fourth = dp
                if isinstance(third, (int, datetime)) or third is None:
                    fr, src = third, fourth
                else:
                    src, src_info = third, fourth
            elif len(dp) == 5:
                value, at, fr, src, src_info = dp
            else:
                raise ValueError("Each datapoint must have between 2 and 5 elements.")

            validate_type(at, (type(None), datetime, int), "At")
            validate_type(fr, (type(None), datetime, int), "From")
            validate_type(value, (int, float, bool, dict, list, str), "Value")
            if src is not None:
                validate_type(src, str, "Source")
            if src_info is not None:
                validate_type(src_info, str, "SourceInfo")

            normalized.append((value, at, fr, src, src_info))

        return self.add_device_datastream_datapoints_with_from(
            device_id, datastream_id, normalized, feed=feed
        )


    @set_method_call
    def add_device_datastream_datapoints_with_from(
        self,
        device_id: str,
        datastream_id: str,
        datapoints: list[
            tuple[int | float | bool | dict | list | str, None | datetime | int, None | datetime | int, None | str, None | str]
        ],
        feed: str | None = None,
    ) -> "IotBulkCollectionBuilder":
        """
        Add the datastream identifier and a list of datapoints with their value, at and from for data collection.

        add_datastream_datapoints_with_from("datastream_identifier", [(value, at, from, Source, SourceInfo)])

        Multiple datastreams can be grouped under a single identifier

        Args:
            datastream_id (str): The identifier for the datastream to which the datapoints will be added.
            datapoints (list[tuple[int | float | bool | dict, None | datetime | int, None | datetime | int]]): A list of tuples where each tuple
                represents a datapoint.  Each tuple contains the datapoint value and an optional timestamp ('at') ('from):
                    value: Collected value
                    at: Number with the time in miliseconds from epoch of the measurement. If this field is None, the platform will assign the server current time to the datapoint whe data is received.
                    from: Number with the time in miliseconds from epoch of the start period of measurement. This indicates that value is the same within this time interval (from, at).

        Returns:
            IotCollectionBuilder: Returns itself to allow for method chaining.

        Example:
            ~~~python
            builder.add_datastream_datapoints_with_from("datastream_identifier_1", [(value, 1431602523123, None), (value, None, None, "HTTP-Basic", "OK")])
            builder.add_datastream_datapoints_with_from("datastream_identifier_2", [(value, None, datetime.now()), (value, 1431602523123, datetime.now())])
            ~~~
        """
        validate_type(device_id, str, "Device identifier")
        validate_type(datastream_id, str, "Datastream identifier")
        validate_type(datapoints, list, "Datapoints")

        if feed is not None:
            validate_type(feed, str, "Feed")

        if not datapoints:
            raise ValueError("Datastream must contain at least one datapoint")

        if device_id not in self.payload['devices']:
            self.payload['devices'][device_id] = {
                "datastreams": [],
                "version": "1.0.0",
                "origin_device": None,
            }

        device_data = self.payload['devices'][device_id]

        datastream = next((ds for ds in device_data['datastreams'] if ds['id'] == datastream_id), None)
        if not datastream:
            datastream = {"id": datastream_id, "datapoints": []}
            if feed is not None:
                datastream["feed"] = feed
            device_data['datastreams'].append(datastream)
        elif feed is not None and "feed" not in datastream:
            datastream["feed"] = feed

        for dp in datapoints:
            if not isinstance(dp, tuple):
                raise ValueError("Each datapoint must be a tuple")
            if len(dp) < 3:
                raise ValueError("Each datapoint must be at least (value, at, from)")

            value, at, from_ = dp[0], dp[1], dp[2]
            source = dp[3] if len(dp) >= 4 else None
            source_info = dp[4] if len(dp) >= 5 else None

            validate_type(value, (int, float, bool, dict, list, str), "Value")
            validate_type(at, (type(None), datetime, int), "At")
            validate_type(from_, (type(None), datetime, int), "From")
            if source is not None:
                validate_type(source, str, "Source")
            if source_info is not None:
                validate_type(source_info, str, "SourceInfo")

            dp_dict: dict[str, Any] = {"value": value}
            if at is not None:
                dp_dict["at"] = int(at.timestamp() * 1000) if isinstance(at, datetime) else at
            if from_ is not None:
                dp_dict["from"] = int(from_.timestamp() * 1000) if isinstance(from_, datetime) else from_
            if source is not None:
                dp_dict["source"] = source
            if source_info is not None:
                dp_dict["sourceInfo"] = source_info

            datastream["datapoints"].append(dp_dict)

        return self


    @set_method_call
    def from_dataframe(self, df: pd.DataFrame) -> "IotBulkCollectionBuilder":
        """
        Processes a DataFrame to extract device, data and datapoints, and adds them to the payload.

        Args:
            df (pd.DataFrame): The DataFrame containing the device data and datapoints. The DataFrame
                               is expected to have columns that match the expected structure for device
                               datastreams and datapoints.
        Returns:
            IotBulkCollectionBuilder: Returns itself to allow for method chaining.

        Example:
            ~~~python
                import pandas as pd

                df = pd.DataFrame({
                     'device_id': ['device'], ['device2'],
                     'datastream': ['1'],['2'],
                     'value': [value, value2],
                     'at': [datetime.now(), 2000]
                })
                builder.from_dataframe(df)
            ~~~
        """
        validate_type(df, pd.DataFrame, "Dataframe")
        self._process_dataframe(df)
        return self

    @set_method_call
    def from_spreadsheet(self, path: str, sheet_name_index: int | str) -> "IotBulkCollectionBuilder":
        """
        Loads data from a spreadsheet, processes it, and adds the resulting device data and datapoints
        to the payload. This method is particularly useful for bulk data operations where data is
        stored in spreadsheet format.

        Args:
            path (str): The file path to the spreadsheet to load.
            sheet_name_index (int | str): The sheet name or index to load from the spreadsheet.

        Returns:
            IotBulkCollectionBuilder: Returns itself to allow for method chaining.

        Example:
            ~~~python
                builder.from_spreadsheet("file.xslx", "sheet_name)
                builder.from_spreadsheet("file.xslx", 1)
            ~~~
        """
        validate_type(path, str, "Path")
        validate_type(sheet_name_index, (int, str), "Sheet name index")

        absolute_path = os.path.abspath(path)
        df = pd.read_excel(absolute_path, sheet_name=sheet_name_index)
        df.columns = df.columns.str.lower().str.replace(' ', '_')

        df['value'] = df['value'].apply(parse_json)

        if 'at' in df.columns:
            df['at'] = pd.to_datetime(
                df['at'], errors='coerce', utc=True, format="mixed")
        if 'from' in df.columns:
            df['from'] = pd.to_datetime(
                df['from'], errors='coerce', utc=True, format="mixed")

        if 'path' in df.columns:
            df['path'] = df['path'].apply(
                lambda x: [str(item) for item in json.loads(x)] if isinstance(x, str) else x)

        self._process_dataframe(df)
        return self

    @set_method_call
    def build(self) -> 'IotBulkCollectionBuilder':
        """
         Finalizes the construction of the entities search configuration.

         This method prepares the builder to execute the collection by ensuring all necessary configurations are set and validates the overall integrity of the build. It should be called before executing the collection to ensure that the configuration is complete and valid.

         The build process involves checking that mandatory fields such as the device identifier are set. It also ensures that method calls that are incompatible with each other (like `build` and `build_execute`) are not both used.

         Returns:
             IotBulkCollectionBuilder: Returns itself to allow for method chaining, enabling further actions like `execute`.

         Raises:
             ValueError: If required configurations are missing or if incompatible methods are used together.

        Example:
            ~~~python
                 builder.build()
            ~~~
        """
        self._validate_builds()

        if 'build_execute' in self.method_calls:
            raise Exception(
                "You cannot use build() together with build_execute()")

        return self

    @set_method_call
    def build_execute(self, include_payload=False):
        """
        This method is a shortcut that combines building and executing in a single step.

        Returns:
            dict: A dictionary containing the execution response which includes the status code and potentially other metadata about the execution.

        Raises:
            ValueError: If `build` has already been called on this builder instance.

        Example:
            ~~~python
            import pandas as pd
            from datetime import datetime

            data = {
                    "device_id": ['entity'],
                    "data_stream_id": ["device.temperature.value"],
                    "origin_device_identifier": ['entity2'],
                    "value": [40],
                    "version": ["4.0.0"],
                    "path": ["entityTesting3"],
                    "at": [datetime.now()],
                    "from": [datetime.now()],
                }
                new_iot_bulk_collection_builder().from_dataframe(df).from_spreadsheet("collect.xslx",0).add_device_datastream_datapoints_with_from("device_identifier", "device.temperature.value", [(300, datetime.now(), datetime.now())])
                               .add_device_datastream_datapoints("entity", "device.temperature.value", [(300, datetime.now())])
                               .build_execute()
            ~~~
        """

        if 'build' in self.method_calls:
            raise ValueError(
                "You cannot use build_execute() together with build()")

        if 'execute' in self.method_calls:
            raise ValueError(
                "You cannot use build_execute() together with execute()")

        self._validate_builds()
        self._execute_bulk_iot_collection(include_payload)

        return self._execute_bulk_iot_collection(include_payload)

    @set_method_call
    def to_dict(self) -> dict:
        """
        This method is used to retrieve the entire payload that has been constructed by the builder. The payload
        includes all devices, their respective datastreams, and the datapoints that have been added to each datastream.
        This is particularly useful for inspecting the current state of the payload after all configurations and
        additions have been made, but before any execution actions (like sending data to a server) are taken.

        Returns:
            dict: A dictionary representing the current state of the payload within the IotBulkCollectionBuilder.
                  This dictionary includes all devices, datastreams, and datapoints that have been configured.

        Raises:
            Exception: If the build method was not called before this method.

        Example:
            ~~~python
                builder.to_dict()
            ~~~
        """
        if 'build' in self.method_calls:
            if self.method_calls[-2] != 'build':
                raise Exception(
                    "The build() method must be called before calling to_dict()")

        return self.payload

    @set_method_call
    def execute(self, include_payload=False):
        """
        Executes the IoT collection based on the current configuration of the builder.

        Args:
            include_payload (bool): Determine if the payload should be included in the response.

        Returns:
            dict: A dictionary containing the results of the execution, including success messages for each device ID
                  if the data was successfully sent, or error messages detailing what went wrong.

        Raises:
            Exception: If `build()` has not been called before `execute()`, or if it was not the last method invoked prior to `execute()`.

        Example:
            ~~~python
            import pandas as pd
            from datetime import datetime

            data = {
                    "device_id": ['entity', entity2],
                    "data_stream_id": ["device.temperature.value", "device.name"],
                    "origin_device_identifier": ['entity2', None],
                    "value": [40, "Name"],
                    "version": ["4.0.0", "2.0.0],
                    "path": ["entityTesting3", entityTesting4],
                    "at": [datetime.now(), datetime.now()],
                    "from": [datetime.now(), datetime.now()],
                }
                builder.new_iot_bulk_collection_builder().from_dataframe(df).from_spreadsheet("collect.xslx",0).add_device_datastream_datapoints_with_from("device_identifier", "device.temperature.value", [(300, datetime.now(), datetime.now())])
                               .add_device_datastream_datapoints("entity", "device.temperature.value", [(300, datetime.now())])
                               .build().execute())
            ~~~
        """

        if 'build' in self.method_calls:
            if self.method_calls[-2] != 'build':
                raise Exception(
                    "The build() function must be the last method invoked before execute.")

        if 'build' not in self.method_calls and 'build_execute' not in self.method_calls:
            raise Exception(
                "You need to use a build() or build_execute() function the last method invoked before execute.")

        results = self._execute_bulk_iot_collection(include_payload)
        return results

    def _execute_bulk_iot_collection(self, include_payload):
        results = {}
        errors = {}
        for device_id, device_data in self.payload.get('devices', {}).items():
            try:
                if self.client.url is None:
                    base_url = 'https://connector-tcp:9443'
                else:
                    base_url = f'{self.client.url}/south'
                url = f'{base_url}/v80/devices/{device_id}/collect/iot'
                response = send_request(
                    method='post', headers=self.headers, url=url, json_payload=device_data)
                if response.status_code == 201:
                    result = {'status_code': response.status_code}
                    if include_payload:
                        result['payload'] = device_data
                    results[device_id] = result
                else:
                    errors[device_id] = {
                        'error': 'HTTP error', 'code': response.status_code, 'message': response.text}

            except Exception as e:
                return handle_exception(e)

        if errors:
            error_messages = "; ".join(
                f"{key}: (Error: {value['error']}, Status code: {value['code']}), {value['message']}" for key, value in
                errors.items()
            )
            if results:
                results.items()
                raise Exception(
                    f"The following entities were executed successfully: {results}. However, errors occurred for these entities: {error_messages}.")
            else:
                raise Exception(
                    f"Errors occurred for these entities: {error_messages}")
        else:
            return results

    def _process_dataframe(self, df: pd.DataFrame):
        """
        Procesa un DataFrame, aceptando 'feed' como string o número (se convierte a string).
        """
        required_columns = ['device_id', 'data_stream_id', 'value']
        optional_columns = ['origin_device_identifier', 'version', 'path', 'trustedboot', 'at', 'from']

        if not set(required_columns).issubset(df.columns):
            missing_cols = set(required_columns) - set(df.columns)
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        for _, row in df.iterrows():
            device_id = row['device_id']
            datastream_id = row['data_stream_id']
            value = row['value']

            at = row.get('at', None)
            from_ = row.get('from', None)
            source = row.get('source', None)
            source_info = row.get('sourceInfo', row.get('source_info', None))
            row_feed = row.get('feed', None)

            validate_type(device_id, str, "Device ID")
            validate_type(datastream_id, str, "Data Stream ID")
            validate_type(value, (int, str, float, bool, dict, list), "Value")

            if device_id not in self.payload['devices']:
                device_config = {"datastreams": []}
                for field in optional_columns:
                    if field in df.columns and (
                        pd.Series(row[field]).notna().any() if isinstance(row[field], list) else pd.notna(row[field])
                    ):
                        if field not in ('at', 'from'):
                            device_config[field] = row[field]
                self.payload['devices'][device_id] = device_config
                if 'version' not in device_config or device_config['version'] is None:
                    device_config['version'] = "1.0.0"

            if 'origin_device_identifier' in df.columns and pd.notna(row.get('origin_device_identifier')):
                self.payload['devices'][device_id]['device'] = row['origin_device_identifier']
                if 'origin_device_identifier' in self.payload['devices'][device_id]:
                    del self.payload['devices'][device_id]['origin_device_identifier']

            dp: dict[str, Any] = {"value": value}
            if pd.notna(at):
                if isinstance(at, float):
                    at = int(at)
                validate_type(at, (type(None), datetime, int), "At")
                dp["at"] = int(at.timestamp() * 1000) if isinstance(at, datetime) else at

            if pd.notna(from_):
                if isinstance(from_, float):
                    from_ = int(from_)
                validate_type(from_, (type(None), datetime, int), "From")
                dp["from"] = int(from_.timestamp() * 1000) if isinstance(from_, datetime) else from_

            if pd.notna(source):
                validate_type(source, str, "Source")
                dp["source"] = source

            if pd.notna(source_info):
                validate_type(source_info, str, "SourceInfo")
                dp["sourceInfo"] = source_info

            device_ds = self.payload['devices'][device_id]['datastreams']
            existing_ds = next((ds for ds in device_ds if ds['id'] == datastream_id), None)

            if existing_ds:
                existing_ds['datapoints'].append(dp)
                if pd.notna(row_feed) and 'feed' not in existing_ds:
                    existing_ds['feed'] = str(row_feed)
            else:
                new_ds = {"id": datastream_id, "datapoints": [dp]}
                if pd.notna(row_feed):
                    new_ds["feed"] = str(row_feed)
                device_ds.append(new_ds)

        return self


    def _validate_builds(self):
        if self.method_calls.count('from_spreadsheet') == 0 and self.method_calls.count(
            'from_dataframe') == 0 and self.method_calls.count(
                'add_device_datastream_datapoints_with_from') == 0 and self.method_calls.count(
                'add_device_datastream_datapoints') == 0:
            raise ValueError(
                "The add_device_datastream_datapoints or add_device_datastream_datapoints_with_from() from_add method must be called")
