import unittest
from unittest.mock import patch, MagicMock
from psycopg2logger.cursorinterceptor import CursorInterceptor
from psycopg2.extensions import connection as _connection

class TestCursorInterceptor(unittest.TestCase):

    @patch('psycopg2logger.cursorinterceptor.TCPWriter')
    @patch('psycopg2logger.cursorinterceptor.log_port')
    def test_init(self, mock_log_port, mock_tcp_writer):
        mock_log_port.get.return_value = 1234
        mock_connection = MagicMock(spec=_connection)

        interceptor = CursorInterceptor(mock_connection)

        # Assert TCPWriter is initialized with correct arguments
        mock_tcp_writer.assert_called_once_with("localhost", 1234)

    @patch('psycopg2logger.cursorinterceptor.time.perf_counter', side_effect=[1, 2])
    @patch('psycopg2logger.cursorinterceptor.TCPWriter')
    @patch('psycopg2logger.cursorinterceptor.log_port')
    def test_execute(self, mock_log_port, mock_tcp_writer, mock_perf_counter):
        mock_log_port.get.return_value = 1234
        mock_connection = MagicMock(spec=_connection)
        interceptor = CursorInterceptor(mock_connection)
        interceptor.pass_log_message = MagicMock()

        # Mock the parent class execute method
        with patch.object(CursorInterceptor, 'execute', return_value="result") as mock_super_execute:
            result = interceptor.execute("SELECT 1")

            # Assert the parent execute was called
            mock_super_execute.assert_called_once_with("SELECT 1")

            # Assert pass_log_message was called with correct arguments
            interceptor.pass_log_message.assert_called_once_with("SELECT 1", None, 1000)

            # Assert the result is returned
            self.assertEqual(result, "result")

if __name__ == "__main__":
    unittest.main()

