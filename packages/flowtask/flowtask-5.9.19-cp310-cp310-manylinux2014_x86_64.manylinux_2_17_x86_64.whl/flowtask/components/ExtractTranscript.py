import asyncio
from typing import List, Optional
from collections.abc import Callable
from pathlib import Path, PurePath
import pandas as pd
from parrot.loaders.audio import AudioLoader
from .flow import FlowComponent
from ..exceptions import ConfigError, ComponentError


class ExtractTranscript(FlowComponent):
    """
    ExtractTranscript Component

    **Overview**

    This component extracts audio transcripts, VTT subtitles, SRT files with speaker diarization,
    and AI-generated summaries from audio files specified in a DataFrame. It uses Parrot's
    AudioLoader which leverages WhisperX for high-quality transcription with word-level timestamps.

    The component processes audio files in batch from a pandas DataFrame and generates multiple
    output formats for each audio file, returning an enhanced DataFrame with paths to all
    generated files.

    .. table:: Properties
       :widths: auto

    +----------------------------+----------+----------------------------------------------------------------------------------------------+
    |   Name                     | Required | Summary                                                                                      |
    +----------------------------+----------+----------------------------------------------------------------------------------------------+
    |   audio_column             | Yes      | Name of DataFrame column containing audio file paths. Default: `"audio_path"`.              |
    |                            |          | The DataFrame must contain this column with valid paths to audio files.                     |
    +----------------------------+----------+----------------------------------------------------------------------------------------------+
    |   language                 | No       | Language code for transcription. Accepts language codes like `"en"`, `"es"`, `"fr"`, etc.   |
    |                            |          | Default: `"en"`. Used to improve transcription accuracy.                                    |
    +----------------------------+----------+----------------------------------------------------------------------------------------------+
    |   model_size               | No       | Whisper model size for transcription. Accepts `"tiny"`, `"small"`, `"medium"`, `"large"`.   |
    |                            |          | Default: `"small"`. Larger models provide better accuracy but require more resources.       |
    +----------------------------+----------+----------------------------------------------------------------------------------------------+
    |   diarization              | No       | Enable speaker diarization to identify different speakers in the audio.                     |
    |                            |          | Default: `false`. When enabled, generates SRT files with speaker labels.                    |
    +----------------------------+----------+----------------------------------------------------------------------------------------------+
    |   summarization            | No       | Enable AI-generated summaries of the transcripts.                                          |
    |                            |          | Default: `true`. Generates summary files using LLM models.                                 |
    +----------------------------+----------+----------------------------------------------------------------------------------------------+
    |   device                   | No       | Device to use for processing. Accepts `"cpu"`, `"cuda"`, or `"mps"`.                       |
    |                            |          | Default: `"cpu"`. Use `"cuda"` for GPU acceleration (10-20x faster).                       |
    +----------------------------+----------+----------------------------------------------------------------------------------------------+
    |   skip_errors              | No       | Continue processing if a file fails. Default: `true`.                                      |
    |                            |          | When `false`, the first error stops the entire workflow.                                   |
    +----------------------------+----------+----------------------------------------------------------------------------------------------+

    **Returns**

    This component returns a pandas DataFrame containing the original data plus additional
    columns with transcription results. The structure includes:

    - **Original DataFrame columns**: All columns from the input DataFrame are preserved.
    - **transcript_success**: Boolean indicating if processing succeeded for each file.
    - **transcript_error**: Error message if processing failed (None if successful).
    - **transcript_vtt_path**: Path to generated WebVTT file with timestamps.
    - **transcript_transcript_path**: Path to plain text transcript file.
    - **transcript_srt_path**: Path to SRT subtitle file (if diarization enabled).
    - **transcript_summary_path**: Path to AI-generated summary file.
    - **transcript_summary**: Summary text content.
    - **transcript_language**: Detected or specified language.

    **Example**

    ```yaml
    ExtractTranscript:
      audio_column: audio_path
      language: en
      model_size: small
      diarization: false
      summarization: true
      device: cuda
      cuda_number: 0
      skip_errors: true
    ```

    """  # noqa

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        """Initialize ExtractTranscript component.

        Args:
            audio_column: Name of DataFrame column containing audio file paths (default: 'audio_path')
            language: Language code for transcription (default: 'en')
            model_size: Whisper model size: tiny, small, medium, large (default: 'small')
            model_name: Explicit model name (optional, overrides model_size)
            diarization: Enable speaker diarization (default: False)
            summarization: Enable summary generation (default: True)
            device: Device to use: cpu, cuda, mps (default: 'cpu')
            cuda_number: CUDA device number if multiple GPUs (default: 0)
            source_type: Source type for metadata (default: 'AUDIO')
            batch_size: Batch size for processing (default: 1)
            skip_errors: Continue processing if a file fails (default: True)
        """
        # Audio processing configuration
        self.audio_column: str = kwargs.pop('audio_column', 'audio_path')
        self.language: str = kwargs.pop('language', 'en')
        self.model_size: str = kwargs.pop('model_size', 'small')
        self.model_name: Optional[str] = kwargs.pop('model_name', None)
        self.diarization: bool = kwargs.pop('diarization', True)
        self.summarization: bool = kwargs.pop('summarization', True)
        self.source_type: str = kwargs.pop('source_type', 'AUDIO')
        self.do_summarization: bool = kwargs.pop('summarization', False)

        # Device configuration
        self._device: str = kwargs.pop('device', 'cpu')
        self._cuda_number: int = kwargs.pop('cuda_number', 0)

        # Processing configuration
        self.batch_size: int = kwargs.pop('batch_size', 1)
        self.skip_errors: bool = kwargs.pop('skip_errors', True)

        super().__init__(
            loop=loop, job=job, stat=stat, **kwargs
        )

        # AudioLoader instance (initialized in start)
        self._audio_loader: Optional[AudioLoader] = None

    async def start(self, **kwargs):
        """Initialize the component and validate configuration."""
        await super().start(**kwargs)

        # Validate that we have input from previous component
        if self.previous is None or self.input is None:
            raise ConfigError(
                "ExtractTranscript requires input from a previous component (e.g., DataFrame)"
            )

        # Validate input is a DataFrame
        if not isinstance(self.input, pd.DataFrame):
            raise ComponentError(
                f"ExtractTranscript expects a DataFrame as input, got {type(self.input)}"
            )

        # Validate audio_column exists in DataFrame
        if self.audio_column not in self.input.columns:
            raise ConfigError(
                f"Column '{self.audio_column}' not found in input DataFrame. "
                f"Available columns: {list(self.input.columns)}"
            )

        # Initialize AudioLoader with configuration
        self._audio_loader = AudioLoader(
            source=None,  # We'll pass source per file
            language=self.language,
            source_type=self.source_type,
            diarization=self.diarization,
            model_size=self.model_size,
            model_name=self.model_name,
            device=self._device,
            cuda_number=self._cuda_number,
            use_summary_pipeline=self.do_summarization,
            video_path=None,  # Not needed for audio-only processing
        )

        print("ExtractTranscript initialized:")
        print(f"  - Audio column: {self.audio_column}")
        print(f"  - Language: {self.language}")
        print(f"  - Model: {self.model_name or f'whisper-{self.model_size}'}")
        print(f"  - Diarization: {self.diarization}")
        print(f"  - Summarization: {self.summarization}")
        print(f"  - Device: {self._device}")

    async def close(self):
        """Clean up resources."""
        if self._audio_loader:
            # Clear any CUDA cache if used
            if hasattr(self._audio_loader, 'clear_cuda'):
                self._audio_loader.clear_cuda()
        await super().close()

    async def _process_audio_file(self, audio_path: str, row_idx: int) -> dict:
        """Process a single audio file and extract transcripts.

        Args:
            audio_path: Path to the audio file
            row_idx: Row index for logging

        Returns:
            Dictionary with extracted metadata and file paths
        """
        try:
            # Convert to Path and validate
            path = Path(audio_path).resolve()

            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {path}")

            print(f"Processing [{row_idx}]: {path.name}")

            # Extract audio using Parrot's AudioLoader
            metadata = await self._audio_loader.extract_audio(path)

            # Add success flag
            metadata['success'] = True
            metadata['error'] = None

            print(f"  ✓ Completed: {path.name}")
            if 'transcript_path' in metadata:
                print(f"    - Transcript: {metadata['transcript_path']}")
            if 'vtt_path' in metadata:
                print(f"    - VTT: {metadata['vtt_path']}")
            if metadata.get('summary'):
                print(f"    - Summary generated")

            return metadata

        except Exception as e:
            error_msg = f"Error processing {audio_path}: {str(e)}"
            print(f"  ✗ {error_msg}")

            if self.skip_errors:
                # Return error metadata
                return {
                    'success': False,
                    'error': str(e),
                    'source': audio_path,
                    'vtt_path': None,
                    'transcript_path': None,
                    'srt_path': None,
                    'summary_path': None,
                    'summary': None,
                    'language': None,
                }
            else:
                raise ComponentError(error_msg) from e

    async def run(self):
        """Process all audio files in the DataFrame."""
        df = self.input.copy()

        print(f"\nProcessing {len(df)} audio files from column '{self.audio_column}'...")

        # Process each audio file
        results = []
        for idx, row in df.iterrows():
            audio_path = row[self.audio_column]

            # Skip if path is None or empty
            if pd.isna(audio_path) or not audio_path:
                print(f"Skipping row {idx}: No audio path provided")
                results.append({
                    'success': False,
                    'error': 'No audio path provided',
                    'source': None,
                    'vtt_path': None,
                    'transcript_path': None,
                    'srt_path': None,
                    'summary_path': None,
                    'summary': None,
                    'language': None,
                })
                continue

            # Process the audio file
            result = await self._process_audio_file(audio_path, idx)
            results.append(result)

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)

        # Merge with original DataFrame
        # Add prefix to avoid column name conflicts
        results_df = results_df.add_prefix('transcript_')
        output_df = pd.concat([df, results_df], axis=1)

        # Calculate metrics
        success_count = sum(1 for r in results if r.get('success', False))
        error_count = len(results) - success_count

        self.add_metric('TOTAL_FILES', len(results))
        self.add_metric('SUCCESS_COUNT', success_count)
        self.add_metric('ERROR_COUNT', error_count)

        print(f"\n{'='*60}")
        print(f"Extraction complete:")
        print(f"  - Total files: {len(results)}")
        print(f"  - Successful: {success_count}")
        print(f"  - Errors: {error_count}")
        print(f"{'='*60}\n")

        # Set result as the enhanced DataFrame
        self._result = output_df

        return True
