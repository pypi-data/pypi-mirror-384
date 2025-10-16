import shutil
import tempfile
from pathlib import Path

from pyspark.sql import DataFrame


def _save_single_file(
    df: DataFrame,
    path: str,
    format: str,  # noqa: A002
    **save_options,
) -> None:
    # Write to a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / Path(path).name
        df.coalesce(1).write.save(
            path=str(output_file), format=format, **save_options
        )
        # Find the file in the temp directory
        for fname in output_file.iterdir():
            if fname.suffix == output_file.suffix:
                shutil.copyfile(fname, path)
                break
        else:
            raise FileNotFoundError("File not found in temporary directory")
