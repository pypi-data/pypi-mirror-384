from collections.abc import Callable
import asyncio
import pandas as pd
from ..interfaces.ParrotBot import ParrotBot
from .flow import FlowComponent


class CallAnalysis(ParrotBot, FlowComponent):
    """
        CallAnalysis.

        Overview

            The CallAnalysis class is a component for interacting with an IA Agent for making Call Analysis.
            It extends the FlowComponent class and adds functionality to load file content from paths.

        .. table:: Properties
        :widths: auto

            +------------------+----------+--------------------------------------------------------------------------------------------------+
            | Name             | Required | Description                                                                                      |
            +------------------+----------+--------------------------------------------------------------------------------------------------+
            | output_column    |   Yes    | Column for saving the Call Analysis information.                                                 |
            +------------------+----------+--------------------------------------------------------------------------------------------------+
            | use_dataframe    |   No     | If True (default), use dataframe mode with file_path_column. If False, use directory/pattern.   |
            +------------------+----------+--------------------------------------------------------------------------------------------------+
            | file_path_column |   No     | Column containing file paths to load content from (dataframe mode).                             |
            +------------------+----------+--------------------------------------------------------------------------------------------------+
            | directory        |   No     | Directory path to search for files (file mode).                                                 |
            +------------------+----------+--------------------------------------------------------------------------------------------------+
            | pattern          |   No     | Glob pattern to match files (file mode).                                                        |
            +------------------+----------+--------------------------------------------------------------------------------------------------+
            | content_column   |   No     | Column to store loaded file content (defaults to 'content').                                   |
            +------------------+----------+--------------------------------------------------------------------------------------------------+
            | as_text          |   No     | Whether to read files as text (True) or bytes (False). Defaults to True.                      |
            +------------------+----------+--------------------------------------------------------------------------------------------------+
        Return

            A Pandas Dataframe with the Call Analysis statistics.

        Example Configuration (Dataframe Mode - Default):
        
        .. code-block:: yaml
        
            - CallAnalysis:
                prompt_file: prompt.txt
                llm:
                  llm: google
                  model: gemini-2.5-flash
                  temperature: 0.4
                  max_tokens: 4096
                use_dataframe: true
                description_column: call_id
                file_path_column: srt_file_path
                content_column: transcript_content
                output_column: call_analysis
                as_text: true
                columns:
                  - call_id
                  - customer_name
                  - agent_name
                  - duration
                  - call_date
                  - srt_file_path

        Example Configuration (File Mode):
        
        .. code-block:: yaml
        
            - CallAnalysis:
                prompt_file: prompt.txt
                llm:
                  llm: google
                  model: gemini-2.5-flash
                  temperature: 0.4
                  max_tokens: 4096
                use_dataframe: false
                directory: /home/ubuntu/symbits/placerai/traffic/{day_six}/
                pattern: "*.srt"
                description_column: filename
                content_column: transcript_content
                output_column: call_analysis
                as_text: true

    """ # noqa

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        # Set default goal for call analysis
        kwargs.setdefault('goal', 'Your task is to analyze call recordings and provide detailed sentiment analysis')
        
        super().__init__(
            loop=loop, job=job, stat=stat, **kwargs
        )
        
        # File handling parameters
        self.use_dataframe: bool = kwargs.get('use_dataframe', True)
        self.file_path_column: str = kwargs.get('file_path_column')
        self.directory: str = kwargs.get('directory')
        self.pattern: str = kwargs.get('pattern')
        self.content_column: str = kwargs.get('content_column', 'content')
        self.as_text: bool = kwargs.get('as_text', True)
        
        # Columns to preserve in the result (required by ParrotBot)
        self.columns: list = kwargs.get('columns', [])
        
        # Set survey mode to True to avoid rating column dependency
        self._survey_mode: bool = True  # NEW: Force survey mode to avoid rating column
        
        # Override goal if not provided
        self._goal: str = kwargs.get('goal', 'Your task is to analyze call recordings and provide detailed sentiment analysis')

    def load_from_file(
        self,
        df: pd.DataFrame,
        field: str,
        column: str = None,
        as_text: bool = True
    ) -> pd.DataFrame:
        """
        Loads the content of a file specified as a path in `column` into `field`.

        Args:
            df: pandas DataFrame with a column containing file paths.
            field: name of the new column to store the file content.
            column: name of the column with file paths (defaults to `field`).
            as_text: if True, read file as text; otherwise, read as bytes.
        """
        if column is None:
            column = field

        def read_file_content(path: str) -> str | bytes | None:
            if not isinstance(path, str):
                self._logger.warning(f"Invalid path type: {type(path)}, expected string")
                return None
            if pd.isna(path) or path.strip() == '':
                self._logger.warning("Empty or NaN path found")
                return None
            try:
                with open(path, 'r' if as_text else 'rb') as f:
                    content = f.read()
                    self._logger.debug(f"Successfully loaded content from {path}")
                    return content
            except FileNotFoundError:
                self._logger.error(f"File not found: {path}")
                return None
            except PermissionError:
                self._logger.error(f"Permission denied reading file: {path}")
                return None
            except Exception as e:
                self._logger.error(f"Error reading {path}: {e}")
                return None

        df[field] = df[column].apply(read_file_content)
        return df

    async def start(self, **kwargs):
        """
        start

        Overview

            The start method is a method for starting the CallAnalysis component.
            Validates required parameters and loads file content.

        Parameters

            kwargs: dict
                A dictionary containing the parameters for the CallAnalysis component.

        Return

            True if the CallAnalysis component started successfully.

        """
        # Check if we're in dataframe mode or file mode
        if not self.use_dataframe:
            # File mode - use directory and pattern like FileList
            self._logger.info("Using file mode with directory and pattern")
            
            # Validate required parameters for file mode
            if not self.directory:
                from ..exceptions import ConfigError
                raise ConfigError(
                    f"{self._bot_name.lower()}: directory is required when use_dataframe is false"
                )
            
            if not self.pattern:
                from ..exceptions import ConfigError
                raise ConfigError(
                    f"{self._bot_name.lower()}: pattern is required when use_dataframe is false"
                )
            
            # Process directory with mask replacement
            if isinstance(self.directory, str) and "{" in self.directory:
                self.directory = self.mask_replacement(self.directory)
                self._logger.info(f"Directory after mask replacement: {self.directory}")
            
            # Check if directory exists
            from pathlib import Path
            dir_path = Path(self.directory)
            if not dir_path.exists() or not dir_path.is_dir():
                from ..exceptions import ComponentError
                raise ComponentError(f"Directory doesn't exist: {self.directory}")
            
            # Find files matching pattern
            import glob
            pattern_path = dir_path / self.pattern
            matching_files = glob.glob(str(pattern_path))
            
            if not matching_files:
                from ..exceptions import ComponentError
                raise ComponentError(f"No files found matching pattern: {pattern_path}")
            
            # Create dataframe with found files
            import pandas as pd
            data = []
            for file_path in matching_files:
                path_obj = Path(file_path)
                data.append({
                    self._desc_column: path_obj.stem,  # filename without extension
                    'file_path': str(file_path)
                })
            
            self.data = pd.DataFrame(data)
            self.file_path_column = 'file_path'  # Set the column name for file paths
            self._logger.info(f"Found {len(self.data)} files matching pattern '{self.pattern}' in directory '{self.directory}'")
            
            # Set up columns for ParrotBot (include description_column and file_path)
            if not self.columns:
                self.columns = [self._desc_column, 'file_path']
            else:
                # Ensure description_column is in columns
                if self._desc_column not in self.columns:
                    self.columns.append(self._desc_column)
                if 'file_path' not in self.columns:
                    self.columns.append('file_path')
            
            # Set up the data for ParrotBot (bypass the previous component check)
            self.input = self.data
            self._component = self  # Set _component to self to satisfy ParrotBot's previous check
            
        else:
            # Dataframe mode - validate file_path_column parameter
            if not self.file_path_column:
                from ..exceptions import ConfigError
                raise ConfigError(
                    f"{self._bot_name.lower()}: file_path_column is required when use_dataframe is true"
                )
            
            # Check if file_path_column exists in the data
            if self.file_path_column not in self.data.columns:
                from ..exceptions import ComponentError
                raise ComponentError(
                    f"{self._bot_name.lower()}: file_path_column '{self.file_path_column}' not found in data columns: {list(self.data.columns)}"
                )
            
            # Set up columns for ParrotBot
            if not self.columns:
                # Default columns: include description_column and file_path_column
                self.columns = [self._desc_column, self.file_path_column]
            else:
                # Ensure required columns are in the list
                if self._desc_column not in self.columns:
                    self.columns.append(self._desc_column)
                if self.file_path_column not in self.columns:
                    self.columns.append(self.file_path_column)
            
            self._logger.info("Using dataframe mode")
        
        # Now call parent start method (ParrotBot.start)
        await super().start(**kwargs)
        
        # Load file content into the dataframe
        self._logger.info(f"Loading file content from column '{self.file_path_column}' into '{self.content_column}'")
        self.data = self.load_from_file(
            df=self.data,
            field=self.content_column,
            column=self.file_path_column,
            as_text=self.as_text
        )
        
        # Set eval_column to the content column for bot processing
        self._eval_column = self.content_column
        
        # Log statistics
        content_loaded = self.data[self.content_column].notna().sum()
        total_files = len(self.data)
        self._logger.info(f"Successfully loaded content from {content_loaded}/{total_files} files")
        
        return True

    def format_question(self, call_identifier, transcripts, row=None):
        """
        Format the question for call analysis.
        
        Args:
            call_identifier: identifier for the call (from description_column)
            transcripts: list of transcript content
            row: optional row data for additional context
            
        Returns:
            str: formatted question for the AI bot
        """
        # Combine all transcripts for this call identifier
        combined_transcript = "\n\n".join([
            transcript.strip() if transcript and len(transcript) < 10000 
            else (transcript[:10000] + "..." if transcript else "")
            for transcript in transcripts
        ])
        
        question = f"""
        Call ID: {call_identifier}

        Please analyze the following call transcript and provide a detailed sentiment analysis:

        TRANSCRIPT:
        {combined_transcript}
        
        Please provide your analysis in the specified JSON format.
        """
        
        return question

    async def bot_evaluation(self):
        """
        bot_evaluation

        Overview

            Custom bot evaluation for call analysis that doesn't require rating column.

        Return

            A Pandas Dataframe with the Call Analysis results.

        """
        # Group transcripts by call identifier and aggregate them into a list
        grouped = self.data.groupby(self._desc_column)[self._eval_column].apply(list).reset_index()
        _evaluation = {}
        
        for _, row in grouped.iterrows():
            call_identifier = row[self._desc_column]
            transcripts = row[self._eval_column]
            
            # Use our custom format_question method
            formatted_question = self.format_question(call_identifier, transcripts, row)
            
            result = await self._bot.invoke(
                question=formatted_question,
            )
            _evaluation[call_identifier] = {
                "answer": result.output
            }
        
        # Create a dataframe with the columns we want to preserve
        # For call analysis, we don't need rating statistics
        grouped_df = self.data.groupby(self.columns).agg(
            num_calls=(self._eval_column, "count")
        ).reset_index()
        
        # Add the Call Analysis column, using the dictionary and match per call identifier
        grouped_df[self.output_column] = grouped_df[self._desc_column].map(
            lambda x: _evaluation[x]['answer']
        )
        
        # Remove the starting ```json and ending ``` using a regex
        grouped_df[self.output_column] = grouped_df[self.output_column].str.replace(r'^```json\s*|\s*```$', '', regex=True)
        
        # return the grouped dataframe
        return grouped_df

    async def run(self):
        """
        Run the CallAnalysis component.
        
        Returns:
            pandas.DataFrame: DataFrame with call analysis results
        """
        self._result = await self.bot_evaluation()
        self._print_data_(self._result, 'CallAnalysis')
        return self._result

    async def close(self):
        """
        Close the CallAnalysis component.
        """
        pass 