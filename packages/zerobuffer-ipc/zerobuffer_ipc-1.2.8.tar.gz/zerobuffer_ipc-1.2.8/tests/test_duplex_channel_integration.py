"""
Duplex Channel integration tests matching C# DuplexChannelIntegrationTests.cs
"""

import os
import time
import threading
import pytest
from zerobuffer import DuplexChannelFactory, BufferConfig, Writer
from zerobuffer.types import Frame


class TestDuplexChannelIntegration:
    """Test duplex channel integration scenarios - matches C# DuplexChannelIntegrationTests"""

    def setup_method(self) -> None:
        """Setup test channel name"""
        self._test_channel_name = f"test_duplex_{os.getpid()}_{id(self)}"

    def test_simplified_protocol_echo_test(self) -> None:
        """SimplifiedProtocol_EchoTest - matches C# test"""
        factory = DuplexChannelFactory.get_instance()
        config = BufferConfig(4096, 10 * 1024 * 1024)

        # Create server that echoes data back
        server = factory.create_immutable_server(self._test_channel_name, config)

        def on_handle(request: Frame, writer: Writer) -> None:
            with writer.get_frame_buffer(len(request.data)) as buffer:
                buffer[:] = request.data
            writer.commit_frame()

        server_thread = threading.Thread(target=lambda: server.start(on_handle))
        server_thread.daemon = True
        server_thread.start()

        time.sleep(0.1)

        # Create client
        client = factory.create_client(self._test_channel_name)

        try:
            # Send request and get sequence number
            test_data = b"Hello, simplified duplex!"
            sequence_number = client.send_request(test_data)

            # Receive response
            response = client.receive_response(5000)  # 5 seconds

            # Verify sequence number matches
            assert response.is_valid
            assert response.sequence == sequence_number
            assert response.to_bytes() == test_data

            response.dispose()

        finally:
            client.close()
            server.stop()

    def test_zero_copy_client_test(self) -> None:
        """ZeroCopyClient_Test - matches C# test"""
        factory = DuplexChannelFactory.get_instance()
        config = BufferConfig(4096, 10 * 1024 * 1024)

        # Create server
        server = factory.create_immutable_server(self._test_channel_name, config)

        def on_handle(request: Frame, writer: Writer) -> None:
            with writer.get_frame_buffer(len(request.data)) as buffer:
                buffer[:] = request.data
            writer.commit_frame()

        server_thread = threading.Thread(target=lambda: server.start(on_handle))
        server_thread.daemon = True
        server_thread.start()

        time.sleep(0.1)

        client = factory.create_client(self._test_channel_name)

        try:
            # Use zero-copy write
            test_data = "Zero-copy test data"
            test_bytes = test_data.encode("utf-8")

            sequence_number, buffer = client.acquire_request_buffer(len(test_bytes))
            try:
                buffer[:] = test_bytes
                client.commit_request()
            finally:
                # Release the buffer memoryview
                buffer.release()

            # Receive response
            response = client.receive_response(5000)

            assert response.is_valid
            assert response.sequence == sequence_number
            assert response.to_bytes().decode("utf-8") == test_data

            response.dispose()

        finally:
            client.close()
            server.stop()

    def test_independent_send_receive_test(self) -> None:
        """IndependentSendReceive_Test - matches C# test"""
        factory = DuplexChannelFactory.get_instance()
        config = BufferConfig(4096, 10 * 1024 * 1024)

        # Create server that adds 1 to each byte
        server = factory.create_immutable_server(self._test_channel_name, config)

        def increment_handler(request: Frame, writer: Writer) -> None:
            data = bytearray(request.data)
            for i in range(len(data)):
                data[i] = (data[i] + 1) % 256
            with writer.get_frame_buffer(len(data)) as buffer:
                buffer[:] = data
            writer.commit_frame()

        server_thread = threading.Thread(target=lambda: server.start(increment_handler))
        server_thread.daemon = True
        server_thread.start()

        time.sleep(0.1)

        client = factory.create_client(self._test_channel_name)

        try:
            # Send multiple requests from one thread
            sequences = []

            def send_requests() -> None:
                nonlocal sequences
                for i in range(10):
                    seq = client.send_request(bytes([i]))
                    sequences.append(seq)
                    time.sleep(0.01)

            # Receive responses from another thread
            responses = []

            def receive_responses() -> None:
                nonlocal responses
                for i in range(10):
                    response = client.receive_response(5000)
                    if response.is_valid:
                        data = response.to_bytes()
                        responses.append((response.sequence, data[0]))
                        response.dispose()

            # Run send and receive concurrently
            send_thread = threading.Thread(target=send_requests)
            receive_thread = threading.Thread(target=receive_responses)

            send_thread.start()
            receive_thread.start()

            # Wait for both threads
            send_thread.join()
            receive_thread.join()

            # Verify all responses match their requests
            for i, seq in enumerate(sequences):
                # Find matching response
                found = False
                for resp_seq, resp_value in responses:
                    if resp_seq == seq:
                        expected_value = (i + 1) % 256
                        assert resp_value == expected_value
                        found = True
                        break
                assert found, f"Response for sequence {seq} not found"

        finally:
            client.close()
            server.stop()

    def test_server_preserves_sequence_number_test(self) -> None:
        """ServerPreservesSequenceNumber_Test - matches C# test"""
        factory = DuplexChannelFactory.get_instance()
        config = BufferConfig(4096, 10 * 1024 * 1024)

        # Create server
        server = factory.create_immutable_server(self._test_channel_name, config)

        captured_sequence = None

        def capture_handler(request: Frame, writer: Writer) -> None:
            nonlocal captured_sequence
            # Capture the sequence number from request
            captured_sequence = request.sequence
            with writer.get_frame_buffer(1) as buffer:
                buffer[:] = bytes([42])
            writer.commit_frame()

        server_thread = threading.Thread(target=lambda: server.start(capture_handler))
        server_thread.daemon = True
        server_thread.start()

        time.sleep(0.1)

        client = factory.create_client(self._test_channel_name)

        try:
            # Send request
            sent_sequence = client.send_request(bytes([1]))

            # Receive response
            response = client.receive_response(1000)

            # Verify server saw the same sequence we sent
            assert sent_sequence == captured_sequence

            # Verify response has the same sequence
            assert sent_sequence == response.sequence

            response.dispose()

        finally:
            client.close()
            server.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
