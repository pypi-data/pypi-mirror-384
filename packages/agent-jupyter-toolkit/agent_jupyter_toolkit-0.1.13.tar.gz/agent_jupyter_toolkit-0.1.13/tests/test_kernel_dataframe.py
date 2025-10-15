"""
Test DataFrame creation, manipulation, and export in kernel (no notebook).
"""

import os
from pathlib import Path

import pytest

from agent_jupyter_toolkit.kernel import SessionConfig, create_session

pytestmark = pytest.mark.asyncio


async def test_kernel_dataframe():
    out_csv = str(Path(__file__).parent / "data/test_kernel_output.csv")
    sess = create_session(SessionConfig(mode="local", kernel_name="python3"))
    await sess.start()
    try:
        code = [
            "import pandas as pd",
            "df = pd.DataFrame({'a': [1, 3], 'b': [2, 4]})",
            f"df.to_csv(r'{out_csv}', index=False)",
            "del df",
        ]
        for c in code:
            result = await sess.execute(c)
            if result.status != "ok":
                print(f"Error executing code: {c}")
                print(f"stderr: {result.stderr}")
                print(f"evalue: {result.evalue}")
                print(f"traceback: {result.traceback}")
            assert result.status == "ok"
        assert os.path.exists(out_csv)
    finally:
        await sess.shutdown()
        os.remove(out_csv)
