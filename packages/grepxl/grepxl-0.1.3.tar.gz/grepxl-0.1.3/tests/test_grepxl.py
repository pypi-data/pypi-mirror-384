import pytest
import pandas as pd
import pandas.testing as pdt

import grepxl


@pytest.fixture
def data():
    df = pd.DataFrame(
        [['yo', 'ho', 1],
         ['fo', 'mo', 2]],
        columns=['a', 'b', 'n'],
    )
    return df


def test_fix(data):
    search = grepxl.grep('yo', data)
    df = pd.DataFrame(
        [['yo', 'ho', 1]],
        columns=['a', 'b', 'n'],
    )
    pdt.assert_frame_equal(search, df)
