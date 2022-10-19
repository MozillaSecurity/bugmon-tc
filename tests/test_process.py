# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest

from bugmon_tc.common import BugmonTaskError
from bugmon_tc.process.cli import process_bug


@pytest.mark.parametrize("with_trace", [True, False])
def test_process_bug(mocker, tmp_path, bug_data, with_trace):
    """Test bug processing"""
    mocker.patch("bugmon_tc.process.cli.BugMonitor.process", return_value=None)
    dest = tmp_path / "results.json"

    trace_dest = None
    if with_trace:
        trace_dest = tmp_path / "trace.tar.gz"
        raw_trace = tmp_path / "latest-trace"
        raw_trace.mkdir()
        mocker.patch("bugmon_tc.process.cli.get_pernosco_trace", return_value=raw_trace)

    process_bug(bug_data, dest, trace_dest=trace_dest)

    assert dest.exists() is True
    assert dest.read_text() == '{\n  "bug_number": 123456,\n  "diff": {}\n}'

    if with_trace:
        assert trace_dest.exists() is True


def test_process_bug_raises_no_trace(mocker, tmp_path, bug_data):
    """Test that process raises when no trace_path is discovered"""
    mocker.patch("bugmon_tc.process.cli.BugMonitor.process", return_value=None)
    dest = tmp_path / "results.json"
    trace_dest = tmp_path / "trace.tar.gz"
    with pytest.raises(BugmonTaskError) as e_info:
        process_bug(bug_data, dest, trace_dest=trace_dest)

    assert str(e_info.value) == "Unable to identify a pernosco trace!"
