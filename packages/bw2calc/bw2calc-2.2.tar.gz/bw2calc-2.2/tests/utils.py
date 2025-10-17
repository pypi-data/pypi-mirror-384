import multiprocessing
from pathlib import Path

import bw_processing as bwp
import pytest
from bw_processing.io_helpers import generic_directory_filesystem
from fsspec.implementations.zip import ZipFileSystem as ZFS

from bw2calc.utils import get_datapackage, get_seed

fixture_dir = Path(__file__).resolve().parent / "fixtures"


def test_get_seeds_different_under_mp_pool():
    with multiprocessing.Pool(processes=4) as pool:
        results = list(pool.map(get_seed, [None] * 10))
    assert sorted(set(results)) == sorted(results)


def test_consistent_global_index():
    # TODO
    pass


def test_get_datapackage():
    dp = bwp.load_datapackage(ZFS(fixture_dir / "basic_fixture.zip"))
    assert get_datapackage(dp) is dp

    assert get_datapackage(ZFS(fixture_dir / "basic_fixture.zip")).metadata == dp.metadata

    assert get_datapackage(fixture_dir / "basic_fixture.zip").metadata == dp.metadata

    assert get_datapackage(str(fixture_dir / "basic_fixture.zip")).metadata == dp.metadata

    dp = bwp.load_datapackage(generic_directory_filesystem(dirpath=fixture_dir / "basic_fixture"))
    assert get_datapackage(dp) is dp

    assert (
        get_datapackage(
            generic_directory_filesystem(dirpath=fixture_dir / "basic_fixture")
        ).metadata
        == dp.metadata
    )

    assert get_datapackage(str(fixture_dir / "basic_fixture")).metadata == dp.metadata

    with pytest.raises(TypeError):
        get_datapackage(1)
