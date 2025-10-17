#!/usr/bin/env python3

"""
qualisys_streaming.py: Qualisys-specific streaming implementations.

This module provides concrete implementations of the streaming framework
for Qualisys motion capture systems using the QTM Real-Time protocol.
"""

__author__ = "Paul-Otto Müller"
__copyright__ = "Copyright 2025, Paul-Otto Müller"
__credits__ = ["Paul-Otto Müller"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "1.1.0"
__maintainer__ = "Paul-Otto Müller"
__status__ = "Development"
__date__ = '16.10.2025'
__url__ = "https://github.com/paulotto/jaw_tracking_system"

import asyncio
import threading

from datetime import datetime
from typing import Dict, Optional, Any

import numpy as np

try:
    import qtm_rt
except ImportError:
    raise ImportError("qtm_rt package required. Install with: pip install qtm-rt")

from . import helper as hlp
from . import streaming as stm

# Set up module logger
logger = hlp.setup_logger(__name__)


class QualysisStreamingDataSource(stm.StreamingDataSource):
    """
    Concrete implementation of StreamingDataSource for Qualisys systems.

    This class handles real-time streaming from Qualisys Track Manager (QTM)
    using the QTM RT protocol via the qtm_rt Python SDK.

    Attributes:
        connection: QTM RT connection object
        event_loop: Asyncio event loop for QTM communication
        components: List of data components to stream
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Qualisys streaming data source.

        Args:
            config: Configuration dictionary with Qualisys-specific settings
                Required keys:
                - host: QTM server IP address
                - port: QTM RT port (default: 22223)
                - version: RT protocol version (default: "1.25")
                - components: List of components to stream
        """
        super().__init__(config)

        self.connection: Optional[qtm_rt.QRTConnection] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None

        # Parse component configuration
        self.components = config.get('components', ['3d', '6d'])
        self.stream_rate = config.get('stream_rate', 'allframes')

        # Frame number tracking for synchronization
        self._last_frame_number = -1

        logger.info(f"Initialized QualysisStreamingDataSource for {config['host']}:{config.get('port', 22223)}")

    def connect(self) -> bool:
        """
        Establish connection to QTM server.

        Returns:
            bool: True if connection successful
        """
        try:
            # Create event loop in separate thread for asyncio
            self.event_loop = asyncio.new_event_loop()
            self._loop_thread = threading.Thread(
                target=self._run_event_loop,
                name="QualysisEventLoop"
            )
            self._loop_thread.daemon = True
            self._loop_thread.start()

            # Connect to QTM
            future = asyncio.run_coroutine_threadsafe(
                self._async_connect(),
                self.event_loop
            )

            # Wait for connection with timeout
            self.connection = future.result(timeout=self.config.get('timeout', 5))

            if self.connection and self.connection.has_transport():
                self._set_state(stm.StreamingState.CONNECTED)
                logger.info("Successfully connected to QTM")
                return True
            else:
                logger.error("Failed to establish QTM connection")
                return False

        except Exception as e:
            logger.error(f"Connection failed: {e}", exc_info=True)
            self._set_state(stm.StreamingState.ERROR)
            return False

    def disconnect(self) -> None:
        """Disconnect from QTM server."""
        logger.info("Disconnecting from QTM")

        # Stop streaming if active
        if self.state == stm.StreamingState.STREAMING:
            self.stop_streaming()

        # Disconnect from QTM
        if self.connection:
            if self.event_loop is None:
                raise RuntimeError("Event loop not initialized")
            future = asyncio.run_coroutine_threadsafe(
                self._async_disconnect(),
                self.event_loop
            )
            future.result(timeout=2)

        # Stop event loop
        if self.event_loop and self._loop_thread:
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
            self._loop_thread.join(timeout=5)

        self._set_state(stm.StreamingState.DISCONNECTED)
        logger.info("Disconnected from QTM")

    def _acquire_frame(self) -> Optional[stm.StreamingFrame]:
        """
        Acquire a single frame from QTM.

        This method is called by the base class acquisition loop.
        It blocks until a frame is available from the async stream.

        Returns:
            StreamingFrame if data received, None on timeout or error
        """
        if not self._packet_queue:
            return None

        try:
            # Get packet from async queue (non-blocking)
            # Note: asyncio.Queue doesn't support timeout parameter in get()
            packet = self._packet_queue.get_nowait()

            # Convert QTM packet to StreamingFrame
            return self._convert_packet_to_frame(packet)

        except Exception:
            return None

    def start_streaming(self) -> bool:
        """
        Start streaming data from QTM.

        Returns:
            bool: True if streaming started successfully
        """
        # Start base class streaming thread
        if not super().start_streaming():
            return False

        # Start QTM streaming
        try:
            if self.event_loop is None:
                raise RuntimeError("Event loop not initialized")
            future = asyncio.run_coroutine_threadsafe(
                self._async_start_streaming(),
                self.event_loop
            )
            result = future.result(timeout=5)

            if result == 'Ok':
                logger.info("QTM streaming started successfully")
                return True
            else:
                logger.error(f"Failed to start QTM streaming: {result}")
                self._set_state(stm.StreamingState.ERROR)
                return False

        except Exception as e:
            logger.error(f"Error starting QTM stream: {e}", exc_info=True)
            self._set_state(stm.StreamingState.ERROR)
            return False

    def stop_streaming(self) -> None:
        """Stop streaming data from QTM."""
        # Stop QTM streaming
        if self.connection:
            if self.event_loop is None:
                raise RuntimeError("Event loop not initialized")
            future = asyncio.run_coroutine_threadsafe(
                self.connection.stream_frames_stop(),
                self.event_loop
            )
            try:
                future.result(timeout=2)
                logger.info("QTM streaming stopped")
            except Exception as e:
                logger.warning(f"Error stopping QTM stream: {e}")

        # Stop base class streaming
        super().stop_streaming()

    # Async methods for QTM communication

    async def _async_connect(self) -> qtm_rt.QRTConnection:
        """Async method to connect to QTM."""
        connection = await qtm_rt.connect(
            self.config['host'],
            port=self.config.get('port', 22223),
            version=self.config.get('version', '1.25'),
            on_event=self._on_qtm_event,
            on_disconnect=self._on_qtm_disconnect,
            timeout=self.config.get('timeout', 5)
        )

        if connection is None:
            raise ConnectionError("Failed to connect to QTM")

        return connection

    async def _async_disconnect(self) -> None:
        """Async method to disconnect from QTM."""
        if self.connection:
            self.connection.disconnect()

    async def _async_start_streaming(self) -> str:
        """Async method to start streaming from QTM."""
        # Create queue for passing packets between async and sync contexts
        self._packet_queue = asyncio.Queue()

        if self.connection is None:
            raise RuntimeError("Connection not established")

        # Start streaming with callback
        result = await self.connection.stream_frames(
            frames=self.stream_rate,
            components=self.components,
            on_packet=self._on_qtm_packet
        )

        return result

    def _run_event_loop(self) -> None:
        """Run the asyncio event loop in a separate thread."""
        if self.event_loop is None:
            raise RuntimeError("Event loop not initialized")
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    def _on_qtm_packet(self, packet: qtm_rt.QRTPacket) -> None:
        """
        Callback for QTM packet reception.

        Args:
            packet: QTM RT packet
        """
        # Put packet in queue for sync processing
        try:
            if self.event_loop is None:
                raise RuntimeError("Event loop not initialized")
            self.event_loop.call_soon_threadsafe(
                self._packet_queue.put_nowait, packet
            )
        except asyncio.QueueFull:
            logger.warning("Packet queue full, dropping packet")

    def _on_qtm_event(self, event: qtm_rt.QRTEvent) -> None:
        """
        Handle QTM events.

        Args:
            event: QTM event
        """
        logger.info(f"QTM Event: {event}")

        # Map QTM events to streaming events
        if event == qtm_rt.QRTEvent.EventConnectionClosed:
            self._emit_event('connection_closed', event)
        elif event == qtm_rt.QRTEvent.EventRTfromFileStarted:
            self._emit_event('rtfromfile_started', event)
        elif event == qtm_rt.QRTEvent.EventRTfromFileStopped:
            self._emit_event('rtfromfile_stopped', event)

    def _on_qtm_disconnect(self) -> None:
        """Handle QTM disconnection."""
        logger.warning("Disconnected from QTM")
        self._set_state(stm.StreamingState.DISCONNECTED)
        self._emit_event('disconnected', None)

    def _convert_packet_to_frame(self, packet: qtm_rt.QRTPacket) -> stm.StreamingFrame:
        """
        Convert QTM packet to StreamingFrame.

        Args:
            packet: QTM RT packet

        Returns:
            StreamingFrame containing the packet data
        """
        frame = stm.StreamingFrame(
            frame_number=packet.framenumber,
            timestamp=packet.timestamp / 1e6,  # Convert microseconds to seconds
            system_time=datetime.now()
        )

        # Extract 3D markers if available
        if qtm_rt.packet.QRTComponentType.Component3d in packet.components:
            marker_data = packet.get_3d_markers()
            if marker_data is not None:
                header, markers = marker_data
                for i, marker in enumerate(markers):
                    if marker is not None:  # Check for occluded markers
                        marker_name = f"marker_{i}"
                        frame.markers[marker_name] = np.array([marker.x, marker.y, marker.z])

        # Extract 6DOF rigid bodies
        if qtm_rt.packet.QRTComponentType.Component6d in packet.components:
            body_data = packet.get_6d()
            if body_data is not None:
                header, bodies = body_data
                for i, body in enumerate(bodies):
                    if body[0] is not None:  # Check if body is tracked
                        rb_name = self._get_rigid_body_name(i)
                        frame.rigid_bodies[rb_name] = self._convert_6dof_to_rigid_body(
                            rb_name, body
                        )

        # Calculate latency if possible
        frame.latency = (datetime.now() - frame.system_time).total_seconds()

        return frame

    def _convert_6dof_to_rigid_body(self, name: str,
                                    body_data: tuple) -> stm.StreamingRigidBody:
        """
        Convert QTM 6DOF data to StreamingRigidBody.

        Args:
            name: Rigid body name
            body_data: Tuple of (position, rotation_matrix)

        Returns:
            StreamingRigidBody instance
        """
        position, rotation_matrix = body_data

        # QTM returns position in mm and rotation as 3x3 matrix
        position_array = np.array([position.x, position.y, position.z])

        # Convert rotation matrix from QTM format
        rot_array = np.array(rotation_matrix).reshape(3, 3).T  # Transpose for column-major

        return stm.StreamingRigidBody(
            name=name,
            position=position_array,
            rotation=rot_array,
            tracking_valid=True
        )

    def _get_rigid_body_name(self, index: int) -> str:
        """
        Get rigid body name from index.

        This would ideally query QTM for the actual names,
        but for now we'll use the names from the configuration.

        Args:
            index: Rigid body index

        Returns:
            Rigid body name
        """
        # Known rigid bodies from config
        known_bodies = ["HP", "MP", "CT"]  # Head Plate, Mandible Plate, Calibration Tool

        if index < len(known_bodies):
            return known_bodies[index]
        else:
            return f"RigidBody_{index}"

    async def get_parameters_async(self) -> Dict[str, Any]:
        """
        Get QTM parameters including rigid body names.

        Returns:
            Dictionary of QTM parameters
        """
        if not self.connection:
            return {}

        # Get parameters XML from QTM
        xml_string = await self.connection.get_parameters(['general', '6d'])

        # Parse XML to extract rigid body names
        # This is simplified - in production you'd properly parse the XML
        return {'xml': xml_string}


class QualysisStreamingMotionCaptureData(stm.StreamingMotionCaptureData):
    """
    Concrete implementation for Qualisys streaming motion capture data.

    This class processes streaming data from QTM and provides real-time
    transformation computation specific to the Qualisys system.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Qualisys streaming motion capture processor.

        Args:
            config: Configuration dictionary
        """
        # Create Qualisys data source
        streaming_config = config['data_source']['streaming']
        data_source = QualysisStreamingDataSource(streaming_config)

        # Initialize base class
        super().__init__(config, data_source)

        # Qualisys-specific state
        self.rigid_body_names = {}
        self.marker_names = {}

        logger.info("Initialized QualysisStreamingMotionCaptureData")

    def process_frame(self, frame: stm.StreamingFrame) -> Dict[str, Any]:
        """
        Process a frame of Qualisys streaming data.

        Args:
            frame: StreamingFrame from QTM

        Returns:
            Dictionary containing processed results with 'transforms' key
        """
        results = {
            'frame_number': frame.frame_number,
            'timestamp': frame.timestamp,
            'transforms': {},
            'markers': {}
        }

        # Process rigid bodies
        for rb_name, rb_data in frame.rigid_bodies.items():
            if rb_data.tracking_valid:
                # Store transformation
                transform = rb_data.to_transform()
                results['transforms'][rb_name] = transform

                # Update rigid body name mapping if needed
                if rb_name not in self.rigid_body_names:
                    self.rigid_body_names[rb_name] = rb_name
                    logger.info(f"Detected rigid body: {rb_name}")

        # Process markers
        for marker_name, position in frame.markers.items():
            results['markers'][marker_name] = position

        # Update processing state
        self.processing_state['last_processed_frame'] = frame.frame_number

        return results

    def get_rigid_body_transform(self, body_name: str,
                                 window_size: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Get transformation matrices for a rigid body over time.

        Args:
            body_name: Name of the rigid body
            window_size: Number of recent frames (None for all buffered)

        Returns:
            Array of shape (N, 4, 4) or None if not available
        """
        transforms = self.get_buffered_transforms(body_name, window_size)

        if len(transforms) == 0:
            return None

        return transforms

    def compute_relative_transform(self, body1: str, body2: str,
                                   window_size: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Compute relative transformation between two rigid bodies.

        Args:
            body1: Reference body name
            body2: Moving body name
            window_size: Number of recent frames (None for all buffered)

        Returns:
            Array of relative transformations or None
        """
        transforms1 = self.get_rigid_body_transform(body1, window_size)
        transforms2 = self.get_rigid_body_transform(body2, window_size)

        if transforms1 is None or transforms2 is None:
            return None

        # Ensure same length
        min_len = min(len(transforms1), len(transforms2))
        transforms1 = transforms1[-min_len:]
        transforms2 = transforms2[-min_len:]

        # Compute relative transforms
        relative_transforms = np.zeros_like(transforms1)
        for i in range(min_len):
            relative_transforms[i] = np.linalg.inv(transforms1[i]) @ transforms2[i]

        return relative_transforms


# Update the factory function in streaming.py
def create_qualisys_streaming_handler(config: Dict[str, Any]) -> QualysisStreamingMotionCaptureData:
    """
    Factory function to create Qualisys streaming handler.

    Args:
        config: Configuration dictionary

    Returns:
        QualysisStreamingMotionCaptureData instance
    """
    return QualysisStreamingMotionCaptureData(config)
