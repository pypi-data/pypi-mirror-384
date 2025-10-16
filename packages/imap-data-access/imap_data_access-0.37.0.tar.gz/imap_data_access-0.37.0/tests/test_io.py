"""Tests for the ``io`` module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

import imap_data_access
from imap_data_access.io import _get_base_url, _make_request

test_science_filename = "imap_swe_l1_test-description_20100101_v000.cdf"
test_science_path = "imap/swe/l1/2010/01/" + test_science_filename


@pytest.mark.parametrize(
    ("url", "api_key", "access_token", "expected"),
    [
        # Default return base url
        ("https://api.test.com", None, None, "https://api.test.com"),
        # API Key appends /api-key
        ("https://api.test.com", "test_key", None, "https://api.test.com/api-key"),
        # API Key with already specified /api-key doesn't double add it
        (
            "https://api.test.com/api-key",
            "test_key",
            None,
            "https://api.test.com/api-key",
        ),
        # Access token appends /authorized
        ("https://api.test.com", None, "test_token", "https://api.test.com/authorized"),
        # Access token with already specified /authorized doesn't double add it
        (
            "https://api.test.com/authorized",
            None,
            "test_token",
            "https://api.test.com/authorized",
        ),
        # API Key takes precedence over access token
        (
            "https://api.test.com",
            "test_key",
            "test_token",
            "https://api.test.com/api-key",
        ),
    ],
)
def test_base_url(url, api_key, access_token, expected, monkeypatch):
    """Test that the base URL is set correctly based on the config."""
    monkeypatch.setitem(imap_data_access.config, "DATA_ACCESS_URL", url)
    monkeypatch.setitem(imap_data_access.config, "API_KEY", api_key)
    monkeypatch.setitem(imap_data_access.config, "ACCESS_TOKEN", access_token)
    assert _get_base_url() == expected


def test_redirect(mock_send_request):
    """Verify that we follow a 307 redirect from newly created s3 buckets.

    Since we are mocking here, we just need to make sure that we are getting
    back the correct response and it doesn't raise for status. We could probably
    use mock_requests here to do something fancier in the future.
    """
    # Mocking the first response (307 Redirect)
    mock_redirect_response = MagicMock()
    mock_redirect_response.status_code = 307
    mock_redirect_response.headers = {"Location": "http://followed-redirect.com"}

    # Using side_effect to alternate between 307 and 200 responses
    mock_send_request.return_value = mock_redirect_response

    request = MagicMock()
    request.url = "http://test-example.com"
    with _make_request(request) as response:
        assert mock_send_request.call_count == 1
        assert response.status_code == 307


def test_request_errors(mock_send_request):
    """Test that invalid URLs raise an appropriate HTTPError or RequestException.

    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for requests.Session
    """
    # Set up the mock to raise an HTTPError with a response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = "Not Found"
    mock_response.text = "The requested resource was not found."
    mock_send_request.side_effect = requests.exceptions.HTTPError(
        response=mock_response
    )
    with pytest.raises(imap_data_access.io.IMAPDataAccessError, match="404 Not Found"):
        imap_data_access.download(test_science_path)

    # Set up the mock to raise a RequestException
    mock_response.status_code = 400
    mock_response.reason = "Request failed"
    mock_response.text = ""
    mock_send_request.side_effect = requests.exceptions.RequestException(
        response=mock_response
    )
    with pytest.raises(
        imap_data_access.io.IMAPDataAccessError, match="400 Request failed"
    ):
        imap_data_access.download(test_science_path)


@pytest.mark.parametrize(
    ("file_path", "destination"),
    [
        # Directory structure inferred
        (
            test_science_filename,
            test_science_path,
        ),
        # Directory structure provided in the request
        (test_science_path, test_science_path),
        # Pathlib.Path object
        (Path(test_science_path), test_science_path),
        # Ancillary files
        (
            "imap_mag_test_20210101_v001.csv",
            "imap/ancillary/mag/imap_mag_test_20210101_v001.csv",
        ),
        (
            "imap_mag_test_20210101_v001.cdf",
            "imap/ancillary/mag/imap_mag_test_20210101_v001.cdf",
        ),
        # SPICE file
        (
            "imap_1000_100_1000_100_01.ap.bc",
            "imap/spice/ck/imap_1000_100_1000_100_01.ap.bc",
        ),
    ],
)
def test_download(mock_send_request, file_path: str | Path, destination: str):
    """Test that the download API works as expected.

    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for requests.Session
    file_path : str or Path
        The path to the file to download
    destination : str
        The path to which the file is expected to be downloaded
    """
    # Mock the response to return binary content
    mock_response = MagicMock()
    mock_response.content = b"Mock file content"
    mock_response.status_code = 200
    mock_send_request.return_value = mock_response

    # Call the download function
    result = imap_data_access.download(file_path)

    # Assert that the file was created
    assert result.exists()
    # Test that the file was saved in the correct location
    expected_destination = imap_data_access.config["DATA_DIR"] / destination
    assert result == expected_destination

    # Assert that the file content matches the mock data
    assert result.read_bytes() == b"Mock file content"

    # Should have only been one call to send
    mock_send_request.assert_called_once()

    # Assert that the correct URL was used for the download
    sent_request = mock_send_request.call_args[0][0]
    called_url = sent_request.url
    expected_url_encoded = f"https://api.test.com/download/{destination}"
    assert called_url == expected_url_encoded
    assert sent_request.method == "GET"


def test_download_already_exists(mock_send_request):
    """Test that downloading a file that already exists does not result in any requests.

    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for requests.Session
    """
    # Call the download function
    # set up the destination and create a file
    destination = imap_data_access.config["DATA_DIR"] / test_science_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.touch(exist_ok=True)
    result = imap_data_access.download(test_science_path)
    assert result == destination
    # Make sure we didn't make any requests
    assert mock_send_request.call_count == 0


@pytest.mark.parametrize(
    "query_params",
    [
        # All parameters should send full query
        {
            "table": "science",
            "instrument": "swe",
            "data_level": "l0",
            "descriptor": "test-description",
            "start_date": "20100101",
            "end_date": "20100102",
            "ingestion_start_date": "20100101",
            "ingestion_end_date": "20100102",
            "repointing": "repoint00001",
            "version": "v000",
            "extension": "pkts",
        },
        # Make sure not all query params are sent if they are missing
        {"instrument": "swe", "data_level": "l0"},
        {"instrument": "glows", "data_level": "l1a", "repointing": 1},
        {"instrument": "glows", "data_level": "l1a", "repointing": "1"},
    ],
)
def test_query(mock_send_request, query_params: dict):
    """Test a basic call to the Query API.

    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for requests.Session
    query_params : dict
        Dictionary of key/value pairs that set the query parameters
    """
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_send_request.return_value = mock_response

    response = imap_data_access.query(**query_params)
    # No data found, and JSON decoding works as expected
    assert response == list()

    # Should have only been one call to send
    mock_send_request.assert_called_once()
    # Assert that the correct URL was used for the query
    sent_request = mock_send_request.call_args[0][0]
    called_url = sent_request.url
    fixed_query = query_params.copy()
    if "repointing" in fixed_query:
        fixed_query["repointing"] = 1
    if "table" not in fixed_query:
        fixed_query["table"] = "science"
    # Move 'table' to front if it exists
    if "table" in fixed_query:
        fixed_query = {
            "table": fixed_query["table"],
            **{k: v for k, v in fixed_query.items() if k != "table"},
        }
    str_params = "&".join(f"{k}={v}" for k, v in fixed_query.items())
    expected_url_encoded = f"https://api.test.com/query?{str_params}"
    assert called_url == expected_url_encoded


def test_query_no_params(mock_send_request):
    """Test a call to the Query API that has no parameters.
    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for ``requests.session``
    """
    with pytest.raises(ValueError, match="At least one query"):
        imap_data_access.query()
    # Should not have made any calls to urlopen
    assert mock_send_request.call_count == 0


def test_query_bad_params(mock_send_request):
    """Test a call to the Query API that has invalid parameters.
    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for ``requests.session``
    """
    with pytest.raises(TypeError, match="got an unexpected"):
        imap_data_access.query(bad_param="test")
    # Should not have made any calls to urlopen
    assert mock_send_request.call_count == 0


@pytest.mark.parametrize(
    ("query_flag", "query_input", "expected_output"),
    [
        # All parameters should  not send query
        (
            "instrument",
            "badInput",
            "Not a valid instrument, please choose from "
            + ", ".join(imap_data_access.VALID_INSTRUMENTS),
        ),
        (
            "data_level",
            "badInput",
            "Not a valid data level, choose from "
            + ", ".join(imap_data_access.VALID_DATALEVELS),
        ),
        ("start_date", "badInput", "Not a valid start date, use format 'YYYYMMDD'."),
        ("end_date", "badInput", "Not a valid end date, use format 'YYYYMMDD'."),
        (
            "ingestion_start_date",
            "badInput",
            "Not a valid ingestion start date, use format 'YYYYMMDD'.",
        ),
        (
            "ingestion_end_date",
            "badInput",
            "Not a valid ingestion end date, use format 'YYYYMMDD'.",
        ),
        (
            "repointing",
            "badInput",
            "Not a valid repointing, use format repoint<num>, "
            "where <num> is a 5 digit integer.",
        ),
        ("version", "badInput", "Not a valid version, use format 'vXXX'."),
        (
            "extension",
            "badInput",
            r"Not a valid extension for 'science', "
            r"choose from \{'(cdf|pkts)', '(pkts|cdf)'\}.",
        ),
    ],
)
def test_bad_query_input(query_flag, query_input, expected_output):
    """Test a function call to query with correct params but bad values.
     Ensures correct error message is returned.
    Parameters
    ----------
    query_flag : str
        correct query flag.
    query_input : str
        incorrect query input.
    expected_output : str
        Output error expected to be given.
    """
    kwargs = {query_flag: query_input}

    # Check if the ValueError is raised and contains the correct message
    with pytest.raises(ValueError, match=expected_output):
        imap_data_access.query(**kwargs)


def test_upload_no_file(mock_send_request):
    """Test a call to the upload API that has no filename supplied.
    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for ``requests.session``
    """
    path = Path("/non-existant/file.txt")
    assert not path.exists()
    with pytest.raises(FileNotFoundError):
        imap_data_access.upload(path)
    # Should not have made any calls to urlopen
    assert mock_send_request.call_count == 0


@pytest.mark.parametrize(
    "upload_file_path", ["a/b/test-file.txt", Path("a/b/test-file.txt")]
)
@pytest.mark.parametrize(
    ("api_key", "access_token", "expected_header"),
    [
        (None, None, {}),
        ("test-api-key", None, {"x-api-key": "test-api-key"}),
        (None, "test-access-token", {"Authorization": "Bearer test-access-token"}),
        (
            "test-api-key-default",
            "test-access-token",
            {"x-api-key": "test-api-key-default"},
        ),
    ],
)
def test_upload(
    mock_send_request,
    upload_file_path: str | Path,
    api_key: str | None,
    access_token: str | None,
    expected_header: dict,
    monkeypatch,
):
    """Test a basic call to the upload API.
    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for ``requests.session``
    upload_file_path : str or Path
        The upload file path to test with
    api_key : str or None
        The API key to use for the upload
    access_token : str or None
        The access token to use for the upload
    expected_header : dict
        The expected header to be sent with the request
    """
    monkeypatch.setitem(imap_data_access.config, "API_KEY", api_key)
    monkeypatch.setitem(imap_data_access.config, "ACCESS_TOKEN", access_token)
    mock_send_request.return_value.json.return_value = "https://s3-test-bucket.com"
    # Call the upload function
    file_to_upload = imap_data_access.config["DATA_DIR"] / upload_file_path
    file_to_upload.parent.mkdir(parents=True, exist_ok=True)
    file_to_upload.write_bytes(b"test file content")

    os.chdir(imap_data_access.config["DATA_DIR"])
    imap_data_access.upload(upload_file_path)

    # Should have been two calls to make a request
    # 1. To get the s3 upload url
    # 2. To upload the file to the url returned in 1.
    assert mock_send_request.call_count == 2

    # We get all returned calls, but we only need the calls
    # where we sent requests
    mock_calls = [
        call
        for call in mock_send_request.mock_calls
        if len(call.args) and isinstance(call.args[0], requests.PreparedRequest)
    ]

    # First urlopen call should be to get the s3 upload url
    auth_path = ""
    if api_key:
        auth_path = "/api-key"
    elif access_token:
        auth_path = "/authorized"
    request_sent = mock_calls[0].args[0]
    called_url = request_sent.url
    expected_url_encoded = f"https://api.test.com{auth_path}/upload/test-file.txt"
    assert called_url == expected_url_encoded
    assert request_sent.method == "GET"
    # An API key needs to be added to the header for uploads
    assert request_sent.headers == expected_header

    # Verify that we put that response into our second request
    request_sent = mock_calls[1].args[0]
    called_url = request_sent.url
    expected_url_encoded = "https://s3-test-bucket.com/"
    assert called_url == expected_url_encoded
    assert request_sent.method == "PUT"

    # Assert that the original data from the test file was sent
    assert request_sent.body == b"test file content"


@pytest.mark.parametrize(
    "reprocess_params",
    [
        {
            "start_date": "20100101",
            "end_date": "20100102",
            "instrument": "idex",
            "data_level": "l0",
            "descriptor": "sci",
        },
        {"start_date": "20100101", "end_date": "20100102"},
        {"start_date": "20100101", "end_date": "20100102", "instrument": "idex"},
    ],
)
def test_reprocess(mock_send_request, reprocess_params: dict):
    """Test a basic call to the reprocess API.

    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for requests.Session
    reprocess_params : dict
        Dictionary of key/value pairs that set the reprocessing parameters
    """
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_send_request.return_value = mock_response

    imap_data_access.reprocess(**reprocess_params)

    # Should have only been one call to send
    mock_send_request.assert_called_once()
    # Assert that the correct URL was used for the query
    sent_request = mock_send_request.call_args[0][0]
    called_url = sent_request.url
    fixed_query = reprocess_params.copy()
    str_params = "&".join(f"{k}={v}" for k, v in fixed_query.items())
    expected_url_encoded = (
        f"https://api.test.com/reprocess?{str_params}&reprocessing=True"
    )
    assert called_url == expected_url_encoded


def test_reprocess_only_data_level(mock_send_request):
    """Test a call to the reprocess API that has only the data level.
    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for ``requests.session``
    """
    with pytest.raises(
        ValueError,
        match="If data_level is provided, instrument and descriptor are required",
    ):
        imap_data_access.reprocess(
            start_date="20251017", end_date="20251017", data_level="l1a"
        )
    # Should not have made any calls to mock_send_request
    assert mock_send_request.call_count == 0


def test_reprocess_bad_instrument(mock_send_request):
    """Test a call to the reprocess API that has an invalid instrument.
    Parameters
    ----------
    mock_send_request : unittest.mock.MagicMock
        Mock object for ``requests.session``
    """
    with pytest.raises(ValueError, match="Not a valid instrument"):
        imap_data_access.reprocess(
            start_date="20251017", end_date="20251017", instrument="sdc"
        )
    # Should not have made any calls to urlopen
    assert mock_send_request.call_count == 0
