from . import functions as f
import datetime as dt
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def splitter(
        input_file: str, 
        output_folder: str, 
        splitter_column: str, 
        naming_suffix: str, 
        template_name: str | None = None
):

    current_time = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # get the current time

    sheets = f.load_input_file(input_file)

    newpath, output_log = f.split_files(
                                        output_folder, 
                                        splitter_column, 
                                        template_name, 
                                        naming_suffix, 
                                        sheets, 
                                        current_time
                                    )

    logger.info(f"Output_log: \n{output_log}")
