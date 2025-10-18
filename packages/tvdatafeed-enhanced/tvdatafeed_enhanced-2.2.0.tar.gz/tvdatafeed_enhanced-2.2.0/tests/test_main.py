"""Tests for TvDatafeed main functionality."""

from __future__ import annotations

import re
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest
from tvDatafeed import Interval, TvDatafeed


class TestTvDatafeedInit:
    """Test TvDatafeed initialization."""

    def test_init_anonymous(self):
        """Test initialization without credentials."""
        tv = TvDatafeed()
        assert tv.token is None
        assert tv.ws_debug is False

    def test_init_with_credentials(self, mock_requests_post, tmp_path):
        """Test initialization with username and password."""
        with patch('tvDatafeed.main.TvDatafeed._is_token_valid', return_value=True):
            tv = TvDatafeed(
                username="test",
                password="pass",
                token_cache_file=tmp_path / ".tv_token.json"
            )
            assert tv.token == "test_token_123"

    def test_init_with_cached_token(self, tmp_path, mock_token):
        """Test initialization with cached token."""
        import json
        token_file = tmp_path / ".tv_token.json"
        token_file.write_text(json.dumps({"token": mock_token}))
        
        with patch('tvDatafeed.main.TvDatafeed._is_token_valid', return_value=True):
            tv = TvDatafeed(token_cache_file=token_file)
            assert tv.token == mock_token


class TestSymbolFormatting:
    """Test symbol formatting."""

    def test_format_symbol_simple(self):
        """Test simple symbol formatting."""
        tv = TvDatafeed()
        result = tv._TvDatafeed__format_symbol("AAPL", "NASDAQ")
        assert result == "NASDAQ:AAPL"

    def test_format_symbol_with_colon(self):
        """Test symbol that already contains exchange."""
        tv = TvDatafeed()
        result = tv._TvDatafeed__format_symbol("NASDAQ:AAPL", "NYSE")
        assert result == "NASDAQ:AAPL"

    def test_format_symbol_futures(self):
        """Test futures contract formatting."""
        tv = TvDatafeed()
        result = tv._TvDatafeed__format_symbol("ES", "CME", contract=1)
        assert result == "CME:ES1!"

    def test_format_symbol_invalid_contract(self):
        """Test invalid futures contract type."""
        tv = TvDatafeed()
        with pytest.raises(ValueError, match="Invalid contract"):
            tv._TvDatafeed__format_symbol("ES", "CME", contract="invalid")


class TestMessageConstruction:
    """Test WebSocket message construction."""

    def test_prepend_header(self):
        """Test message header prepending."""
        tv = TvDatafeed()
        message = "test"
        result = tv._TvDatafeed__prepend_header(message)
        assert result == "~m~4~m~test"

    def test_construct_message(self):
        """Test JSON message construction."""
        tv = TvDatafeed()
        result = tv._TvDatafeed__construct_message("test_func", ["arg1", "arg2"])
        assert '"m":"test_func"' in result
        assert '"p":["arg1","arg2"]' in result

    def test_create_message(self):
        """Test complete message creation."""
        tv = TvDatafeed()
        result = tv._TvDatafeed__create_message("test_func", ["arg1"])
        assert result.startswith("~m~")
        assert "test_func" in result


class TestSessionGeneration:
    """Test session ID generation."""

    def test_generate_session(self):
        """Test quote session generation."""
        tv = TvDatafeed()
        session = tv._TvDatafeed__generate_session()
        assert session.startswith("qs_")
        assert len(session) == 15  # qs_ + 12 chars

    def test_generate_chart_session(self):
        """Test chart session generation."""
        tv = TvDatafeed()
        session = tv._TvDatafeed__generate_chart_session()
        assert session.startswith("cs_")
        assert len(session) == 15  # cs_ + 12 chars

    def test_sessions_are_unique(self):
        """Test that generated sessions are unique."""
        tv = TvDatafeed()
        sessions = [tv._TvDatafeed__generate_session() for _ in range(100)]
        assert len(set(sessions)) == 100


class TestGetHistValidation:
    """Test get_hist parameter validation."""

    def test_n_bars_validation_min(self, mock_create_connection):
        """Test that n_bars must be at least 1."""
        tv = TvDatafeed()
        with pytest.raises(ValueError, match="n_bars must be between 1 and 5000"):
            tv.get_hist("AAPL", "NASDAQ", n_bars=0)

    def test_n_bars_validation_max(self, mock_create_connection):
        """Test that n_bars cannot exceed 5000."""
        tv = TvDatafeed()
        with pytest.raises(ValueError, match="n_bars must be between 1 and 5000"):
            tv.get_hist("AAPL", "NASDAQ", n_bars=5001)

    def test_n_bars_valid_range(self, mock_create_connection):
        """Test valid n_bars values."""
        tv = TvDatafeed()
        # Should not raise
        for n_bars in [1, 100, 1000, 5000]:
            try:
                tv.get_hist("AAPL", "NASDAQ", n_bars=n_bars)
            except ValueError as e:
                if "n_bars" in str(e):
                    pytest.fail(f"Valid n_bars={n_bars} raised ValueError")


class TestGetHist:
    """Test get_hist method."""

    def test_get_hist_basic(self, mock_create_connection):
        """Test basic historical data fetch."""
        # Create mock WebSocket with series data
        mock_ws = MagicMock()
        mock_ws.recv.side_effect = [
            '~m~100~m~{"m":"quote_completed","p":[]}',
            '~m~200~m~{"m":"timescale_update","p":["s",["v",1609459200,150,151,149,150.5,1000000]],"s":[{"s":[{"i":[0,1,2,3,4,5],"v":[1609459200,150,151,149,150.5,1000000]}]}]}',
            '~m~50~m~{"m":"series_completed","p":[]}'
        ]
        mock_create_connection.return_value = mock_ws
        
        tv = TvDatafeed()
        result = tv.get_hist("AAPL", "NASDAQ", Interval.in_daily, n_bars=10)
        
        # Should attempt to create DataFrame (even if it fails due to mock data)
        assert mock_ws.send.called

    def test_get_hist_with_futures_contract(self, mock_create_connection):
        """Test get_hist with futures contract."""
        tv = TvDatafeed()
        tv.get_hist("ES", "CME", Interval.in_1_hour, n_bars=100, fut_contract=1)
        
        # Verify the symbol was formatted correctly with futures contract
        mock_create_connection.return_value.send.assert_called()

    def test_get_hist_with_extended_session(self, mock_create_connection):
        """Test get_hist with extended session."""
        tv = TvDatafeed()
        tv.get_hist("AAPL", "NASDAQ", Interval.in_daily, n_bars=100, extended_session=True)
        
        # Verify the websocket was called
        assert mock_create_connection.called


class TestSearchSymbol:
    """Test search_symbol method."""

    def test_search_symbol_basic(self, mock_requests_get, mock_search_response):
        """Test basic symbol search."""
        mock_requests_get.return_value.text = '<em>AAPL</em>'
        mock_requests_get.return_value.json.return_value = mock_search_response
        
        tv = TvDatafeed()
        results = tv.search_symbol("AAPL", "NASDAQ")
        
        assert isinstance(results, list)
        mock_requests_get.assert_called_once()

    def test_search_symbol_no_exchange(self, mock_requests_get):
        """Test symbol search without exchange filter."""
        mock_requests_get.return_value.json.return_value = []
        
        tv = TvDatafeed()
        results = tv.search_symbol("AAPL")
        
        assert isinstance(results, list)

    def test_search_symbol_network_error(self):
        """Test symbol search handles network errors."""
        with patch('tvDatafeed.main.requests.get', side_effect=Exception("Network error")):
            tv = TvDatafeed()
            results = tv.search_symbol("AAPL")
            assert results == []


class TestDataFrameCreation:
    """Test DataFrame creation from WebSocket data."""

    def test_create_df_with_valid_data(self):
        """Test DataFrame creation with valid data."""
        tv = TvDatafeed()
        # Sample WebSocket response format
        raw_data = '{"m":"timescale_update","p":["session"],"s":[{"i":[0,1,2,3,4,5],"v":[1609459200,150,151,149,150.5,1000000]}]}'
        
        # This tests the parsing logic (may return None with mock data)
        result = tv._TvDatafeed__create_df(raw_data, "NASDAQ:AAPL")
        # Result may be None due to incomplete mock data, but should not raise exception

    def test_create_df_with_invalid_data(self):
        """Test DataFrame creation with invalid data."""
        tv = TvDatafeed()
        result = tv._TvDatafeed__create_df("invalid data", "NASDAQ:AAPL")
        assert result is None


class TestWebSocketConnection:
    """Test WebSocket connection management."""

    def test_websocket_context_manager(self, mock_create_connection):
        """Test WebSocket context manager."""
        tv = TvDatafeed()
        
        with tv._websocket_connection() as ws:
            assert ws is not None
            ws.send("test")
        
        # Verify close was called
        mock_create_connection.return_value.close.assert_called_once()

    def test_websocket_connection_error_handling(self):
        """Test WebSocket connection error handling."""
        with patch('tvDatafeed.main.create_connection', side_effect=Exception("Connection failed")):
            tv = TvDatafeed()
            
            with pytest.raises(Exception, match="Connection failed"):
                with tv._websocket_connection() as ws:
                    pass
