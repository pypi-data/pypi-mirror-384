
import json
from typing import Optional, Callable
from pyspark.sql import DataFrame
from .process_record import ProcessRecord
from ._session import _Session


class ParsingSession(_Session):

    """Session class to manage custom parse process lifecycle.

    Initializes parse process record and provides methods to parse
    data frames and handle failures, updating metadata and notifying the Core API.
    """
    _parsing_parameters: dict
    def __init__(self, input_id: Optional[int] = None):
        """Initialize custom parse session and start a new custom parse process.

        Args:
            input_id (Optional[int]): Optional input_id of the batch for interactive testing.
                Leave blank for production use.
        """
        super().__init__()
        # initialize process
        if input_id is not None:
            self.process_parameters["input_id"] = input_id

        process = self._pg.sql("select sparky.sdk_new_parse(%s)", (json.dumps(self.process_parameters),))
        self.process = ProcessRecord(process)
        self._parsing_parameters = self._pg.sql("select meta.prc_n_start_parse(%s)",
                                                (json.dumps({"input_id": self.process.inputId}),))
        # Extract the file extension
        file_name = self._parsing_parameters["source_file_name"]
        file_extension = file_name.split(".")[-1]
        # Construct the path
        self.file_path = f"{self._systemConfiguration.datalakePath}/source_{self.process.sourceId}/raw/raw_input_{self.process.inputId}.{file_extension}"

    def custom_parameters(self):
        """Retrieve custom parsing parameters.

        Returns:
            dict: The custom parsing parameters dictionary.
        """
        return self._parsing_parameters.get('custom_parameters')

    def run(self,df: DataFrame | Callable[[], DataFrame] | None = None):
        """Save parsed file from the provided DataFrame, and upload it into the DataForge data lake.

        Writes the DataFrame to parsed Parquet file,
        updates the input record with status, file size, record count, and notifies
        the Core API of process completion. On failure, updates logs and flags the input and process
        records as failed.

        Args:
            df (DataFrame): parameterless def that you defined, returning the Spark DataFrame containing parsed file data (recommended),
                or spark DataFrame
        """
        try:
            if not self._is_open:
                raise Exception("Session is closed")
            if callable(df):
                result_df = df()  # call it to get the DataFrame
            else:
                result_df = df

            if result_df is None or result_df.isEmpty():
                file_size, row_count = (0, 0)
            else:
                dest_file_path = f"{self._systemConfiguration.datalakePath}/source_{self.process.sourceId}/parsed/parsed_input_{self.process.inputId}"
                file_size, row_count = self._write_parsed_data(result_df, dest_file_path)
            input_update_json = {
                "file_size": file_size,
                "input_id": self.process.inputId,
                "record_counts": {"Total": row_count}
            }
            self._end_process('P' if row_count > 0 else 'Z', input_update_json)

        except Exception as e:
            self._log_fail(e)
            self._end_process("F")

