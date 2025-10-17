#!/usr/bin/env python3

"""
streaming.py: Real-time streaming framework for motion capture data processing.

This module provides abstract base classes and utilities for handling real-time
motion capture data streams. It's designed to work with any motion capture system
that can stream marker and rigid body data, including Qualisys, OptiTrack, Vicon, etc.

The module implements:
- Abstract interfaces for streaming data sources
- Buffer management for real-time data
- State management for online processing
- Event-driven architecture for interactive calibration
- Thread-safe data handling for concurrent acquisition and processing

Architecture Overview:
    StreamingDataSource (Abstract)
        ├── Stream management (connect/disconnect)
        ├── Data acquisition loop
        └── Event dispatching

    StreamingMotionCaptureData (Abstract)
        ├── Buffered data storage
        ├── Real-time transform computation
        └── State synchronization

    StreamingProcessor (Abstract)
        ├── Online algorithm adaptation
        ├── State persistence
        └── Real-time constraints handling
"""

__author__ = "Paul-Otto Müller"
__copyright__ = "Copyright 2025, Paul-Otto Müller"
__credits__ = ["Paul-Otto Müller"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "1.0.4"
__maintainer__ = "Paul-Otto Müller"
__status__ = "Development"
__date__ = '16.10.2025'
__url__ = "https://github.com/paulotto/jaw-tracking-system"

import time
import threading
import queue

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Any, Callable, Deque
from datetime import datetime

import numpy as np

from . import helper as hlp

# Set up module logger
logger = hlp.setup_logger(__name__)


# Data structures for streaming

@dataclass
class StreamingFrame:
    """
    Represents a single frame of streaming motion capture data.

    This class encapsulates all data received in one frame from the motion capture system,
    including timing information, marker positions, and rigid body poses.

    Attributes:
        frame_number: Sequential frame identifier
        timestamp: Hardware timestamp from motion capture system (seconds)
        system_time: Local system time when frame was received
        markers: Dictionary of marker positions {name: (x, y, z)}
        rigid_bodies: Dictionary of rigid body data {name: StreamingRigidBody}
        latency: Estimated latency between capture and reception (seconds)
        metadata: Additional frame-specific metadata
    """
    frame_number: int
    timestamp: float
    system_time: datetime
    markers: Dict[str, np.ndarray] = field(default_factory=dict)
    rigid_bodies: Dict[str, 'StreamingRigidBody'] = field(default_factory=dict)
    latency: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate frame data structure."""
        for marker_name, position in self.markers.items():
            if position.shape != (3,):
                raise ValueError(f"Marker {marker_name} position must be 3D vector")


@dataclass
class StreamingRigidBody:
    """
    Represents a rigid body in streaming data.

    Attributes:
        name: Unique identifier for the rigid body
        position: 3D position vector (x, y, z) in mm
        rotation: 3x3 rotation matrix
        quaternion: Quaternion representation (w, x, y, z)
        tracking_valid: Whether tracking is currently valid
        marker_error: RMS error of marker fit (mm)
        markers: Individual marker positions in body frame
    """
    name: str
    position: np.ndarray
    rotation: np.ndarray
    quaternion: Optional[np.ndarray] = None
    tracking_valid: bool = True
    marker_error: float = 0.0
    markers: Optional[Dict[str, np.ndarray]] = None

    def __post_init__(self):
        """Validate and normalize rigid body data."""
        if self.position.shape != (3,):
            raise ValueError(f"Position must be 3D vector for rigid body {self.name}")
        if self.rotation.shape != (3, 3):
            raise ValueError(f"Rotation must be 3x3 matrix for rigid body {self.name}")

        # Ensure rotation matrix is orthonormal
        self.rotation = hlp.ensure_orthonormal(self.rotation)

        # Compute quaternion if not provided
        if self.quaternion is None:
            from scipy.spatial.transform import Rotation as R
            self.quaternion = R.from_matrix(self.rotation).as_quat(scalar_first=True)

    def to_transform(self) -> np.ndarray:
        """
        Convert rigid body pose to 4x4 homogeneous transformation matrix.

        Returns:
            4x4 transformation matrix representing the rigid body pose
        """
        return hlp.build_transform(self.position, self.rotation)


class StreamingState(Enum):
    """
    Enumeration of possible streaming states.

    States:
        DISCONNECTED: No active connection to motion capture system
        CONNECTING: Attempting to establish connection
        CONNECTED: Connected but not receiving data
        STREAMING: Actively receiving and processing data
        PAUSED: Connection active but data processing paused
        ERROR: Error state requiring intervention
    """
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    STREAMING = auto()
    PAUSED = auto()
    ERROR = auto()


@dataclass
class StreamingStatistics:
    """
    Real-time statistics for streaming performance monitoring.

    Attributes:
        frames_received: Total number of frames received
        frames_dropped: Number of frames dropped due to buffer overflow
        frames_processed: Number of frames successfully processed
        average_fps: Average frames per second over recent window
        average_latency: Average system latency in seconds
        buffer_usage: Current buffer utilization (0.0 to 1.0)
        uptime: Total streaming duration in seconds
        last_frame_time: Timestamp of most recent frame
    """
    frames_received: int = 0
    frames_dropped: int = 0
    frames_processed: int = 0
    average_fps: float = 0.0
    average_latency: float = 0.0
    buffer_usage: float = 0.0
    uptime: float = 0.0
    last_frame_time: Optional[datetime] = None

    def update_fps(self, frame_times: Deque[float], window_size: int = 100) -> None:
        """
        Update average FPS calculation based on recent frame timestamps.

        Args:
            frame_times: Deque of recent frame timestamps
            window_size: Number of frames to consider for average (currently not used)
        """
        if len(frame_times) >= 2:
            time_span = frame_times[-1] - frame_times[0]
            if time_span > 0:
                self.average_fps = (len(frame_times) - 1) / time_span


class StreamingDataSource(ABC):
    """
    Abstract base class for streaming motion capture data sources.

    This class defines the interface for connecting to and receiving data from
    motion capture systems in real-time. Implementations should handle system-specific
    protocols and data formats.

    The class implements a producer-consumer pattern where data acquisition runs
    in a separate thread and communicates via thread-safe queues.

    Attributes:
        config: Configuration dictionary for the data source
        state: Current streaming state
        frame_queue: Thread-safe queue for buffering frames
        event_handlers: Dictionary of registered event callbacks
        statistics: Real-time performance statistics
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize streaming data source.

        Args:
            config: Configuration dictionary containing connection parameters
                Expected keys may include:
                - host: IP address of motion capture server
                - port: Network port for streaming
                - buffer_size: Maximum number of frames to buffer
                - timeout: Connection timeout in seconds
        """
        self.config = config
        self.state = StreamingState.DISCONNECTED
        self.frame_queue = queue.Queue(maxsize=config.get('buffer_size', 1000))
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.statistics = StreamingStatistics()

        # Threading components
        self._acquisition_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()

        # Performance monitoring
        self._frame_times: Deque[float] = deque(maxlen=100)
        self._start_time: Optional[float] = None

        logger.info(f"Initialized {self.__class__.__name__} with config: {config}")

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the motion capture system.

        This method should handle all system-specific connection procedures,
        including network setup, handshaking, and initial configuration.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Cleanly disconnect from the motion capture system.

        This method should properly close all connections and free resources.
        """
        pass

    @abstractmethod
    def _acquire_frame(self) -> Optional[StreamingFrame]:
        """
        Acquire a single frame from the motion capture system.

        This method is called repeatedly by the acquisition thread and should
        block until data is available or timeout occurs.

        Returns:
            StreamingFrame if data received, None on timeout or error
        """
        pass

    def start_streaming(self) -> bool:
        """
        Start the data acquisition thread and begin streaming.

        Returns:
            bool: True if streaming started successfully
        """
        with self._state_lock:
            if self.state != StreamingState.CONNECTED:
                logger.error(f"Cannot start streaming in state {self.state}")
                return False

            self._stop_event.clear()
            self._start_time = time.time()
            self._acquisition_thread = threading.Thread(
                target=self._acquisition_loop,
                name=f"{self.__class__.__name__}-AcquisitionThread"
            )
            self._acquisition_thread.daemon = True
            self._acquisition_thread.start()

            self._set_state(StreamingState.STREAMING)
            logger.info("Started streaming data acquisition")
            return True

    def stop_streaming(self) -> None:
        """Stop the data acquisition thread and halt streaming."""
        logger.info("Stopping streaming data acquisition")
        self._stop_event.set()

        if self._acquisition_thread and self._acquisition_thread.is_alive():
            self._acquisition_thread.join(timeout=5.0)
            if self._acquisition_thread.is_alive():
                logger.warning("Acquisition thread did not stop cleanly")

        with self._state_lock:
            if self.state == StreamingState.STREAMING:
                self._set_state(StreamingState.CONNECTED)

    def _acquisition_loop(self) -> None:
        """
        Main acquisition loop running in separate thread.

        Continuously acquires frames from the motion capture system and
        places them in the frame queue for processing.
        """
        logger.info("Acquisition thread started")

        while not self._stop_event.is_set():
            try:
                # Acquire frame from motion capture system
                frame = self._acquire_frame()

                if frame is not None:
                    # Update statistics
                    self.statistics.frames_received += 1
                    self._frame_times.append(frame.timestamp)
                    self.statistics.last_frame_time = frame.system_time

                    # Try to put frame in queue
                    try:
                        self.frame_queue.put_nowait(frame)
                        self._emit_event('frame_received', frame)
                    except queue.Full:
                        self.statistics.frames_dropped += 1
                        self._emit_event('buffer_overflow', frame)
                        logger.warning(f"Frame buffer full, dropped frame {frame.frame_number}")

                    # Update performance metrics
                    self._update_statistics()

            except Exception as e:
                logger.error(f"Error in acquisition loop: {e}", exc_info=True)
                self._emit_event('acquisition_error', e)
                if self.state == StreamingState.STREAMING:
                    self._set_state(StreamingState.ERROR)
                break

        logger.info("Acquisition thread stopped")

    def get_frame(self, timeout: Optional[float] = None) -> Optional[StreamingFrame]:
        """
        Retrieve a frame from the buffer.

        Args:
            timeout: Maximum time to wait for frame (None = block indefinitely)

        Returns:
            StreamingFrame if available, None on timeout
        """
        try:
            frame = self.frame_queue.get(timeout=timeout)
            self.statistics.frames_processed += 1
            return frame
        except queue.Empty:
            return None

    def _set_state(self, new_state: StreamingState) -> None:
        """
        Update streaming state and emit state change event.

        Args:
            new_state: New streaming state
        """
        old_state = self.state
        self.state = new_state
        logger.info(f"State changed: {old_state} -> {new_state}")
        self._emit_event('state_changed', {'old': old_state, 'new': new_state})

    def _update_statistics(self) -> None:
        """Update real-time performance statistics."""
        # Update FPS
        self.statistics.update_fps(self._frame_times)

        # Update buffer usage
        self.statistics.buffer_usage = self.frame_queue.qsize() / self.frame_queue.maxsize

        # Update uptime
        if self._start_time:
            self.statistics.uptime = time.time() - self._start_time

    # Event handling system

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register a callback for specific events.

        Args:
            event_type: Type of event to handle (e.g., 'frame_received', 'state_changed')
            handler: Callback function to invoke when event occurs
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event '{event_type}'")

    def unregister_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Remove a previously registered event handler.

        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(handler)

    def _emit_event(self, event_type: str, data: Any = None) -> None:
        """
        Emit an event to all registered handlers.

        Args:
            event_type: Type of event to emit
            data: Event data to pass to handlers
        """
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for '{event_type}': {e}")


class StreamingMotionCaptureData(ABC):
    """
    Abstract base class for streaming motion capture data processing.

    This class extends the offline MotionCaptureData interface to support
    real-time streaming scenarios. It manages buffered data, performs
    incremental computations, and maintains state between processing windows.

    The class is designed to work with any StreamingDataSource implementation
    and provides methods for real-time transformation computation and analysis.

    Attributes:
        config: Configuration dictionary
        data_source: StreamingDataSource instance
        frame_buffer: Circular buffer of recent frames
        transform_buffer: Buffer of computed transformations
        processing_state: Current state of data processing
    """

    def __init__(self, config: Dict[str, Any], data_source: StreamingDataSource):
        """
        Initialize streaming motion capture data processor.

        Args:
            config: Configuration dictionary containing processing parameters
            data_source: Initialized StreamingDataSource instance
        """
        self.config = config
        self.data_source = data_source

        # Buffers for data storage
        buffer_size = config.get('buffer_size', 1000)
        self.frame_buffer: Deque[StreamingFrame] = deque(maxlen=buffer_size)
        self.transform_buffer: Dict[str, Deque[np.ndarray]] = {}

        # Processing state
        self.processing_state = {
            'last_processed_frame': -1,
            'reference_frame': None,
            'calibration_complete': False,
            'processing_enabled': True
        }

        # Register event handlers
        self.data_source.register_event_handler('frame_received', self._on_frame_received)
        self.data_source.register_event_handler('state_changed', self._on_state_changed)

        logger.info(f"Initialized {self.__class__.__name__} with buffer size {buffer_size}")

    @abstractmethod
    def process_frame(self, frame: StreamingFrame) -> Dict[str, Any]:
        """
        Process a single frame of streaming data.

        This method should implement system-specific processing logic to
        extract relevant information and compute transformations.

        Args:
            frame: StreamingFrame to process

        Returns:
            Dictionary containing processed results
        """
        pass

    def _on_frame_received(self, frame: StreamingFrame) -> None:
        """
        Handle incoming frames from the data source.

        Args:
            frame: Newly received StreamingFrame
        """
        # Add to buffer
        self.frame_buffer.append(frame)

        # Process if enabled
        if self.processing_state['processing_enabled']:
            try:
                results = self.process_frame(frame)
                self._store_results(results)
            except Exception as e:
                logger.error(f"Error processing frame {frame.frame_number}: {e}")

    def _on_state_changed(self, state_info: Dict[str, StreamingState]) -> None:
        """
        Handle streaming state changes.

        Args:
            state_info: Dictionary with 'old' and 'new' states
        """
        new_state = state_info['new']

        if new_state == StreamingState.STREAMING:
            logger.info("Streaming started, enabling processing")
            self.processing_state['processing_enabled'] = True
        elif new_state in [StreamingState.PAUSED, StreamingState.ERROR]:
            logger.info(f"Streaming {new_state}, disabling processing")
            self.processing_state['processing_enabled'] = False

    def _store_results(self, results: Dict[str, Any]) -> None:
        """
        Store processed results in appropriate buffers.

        Args:
            results: Dictionary of processing results
        """
        # Store transformations
        if 'transforms' in results:
            for name, transform in results['transforms'].items():
                if name not in self.transform_buffer:
                    self.transform_buffer[name] = deque(maxlen=self.frame_buffer.maxlen)
                self.transform_buffer[name].append(transform)

    def get_buffered_transforms(self, body_name: str,
                                window_size: Optional[int] = None) -> np.ndarray:
        """
        Retrieve buffered transformations for a specific body.

        Args:
            body_name: Name of the rigid body
            window_size: Number of recent frames to retrieve (None = all)

        Returns:
            Array of transformation matrices
        """
        if body_name not in self.transform_buffer:
            return np.array([])

        buffer = self.transform_buffer[body_name]
        if window_size is None:
            transforms = list(buffer)
        else:
            transforms = list(buffer)[-window_size:]

        return np.array(transforms)

    def get_current_transform(self, body_name: str) -> Optional[np.ndarray]:
        """
        Get the most recent transformation for a body.

        Args:
            body_name: Name of the rigid body

        Returns:
            4x4 transformation matrix or None if not available
        """
        if body_name in self.transform_buffer and self.transform_buffer[body_name]:
            return self.transform_buffer[body_name][-1]
        return None

    def compute_relative_transform_realtime(self, ref_body: str,
                                            moving_body: str) -> Optional[np.ndarray]:
        """
        Compute relative transformation between two bodies in real-time.

        Args:
            ref_body: Reference body name
            moving_body: Moving body name

        Returns:
            4x4 relative transformation matrix ${ref}^T_{moving}$ or None if bodies not available
        """
        ref_transform = self.get_current_transform(ref_body)
        moving_transform = self.get_current_transform(moving_body)

        if ref_transform is None or moving_transform is None:
            return None

        # T_ref_moving = inv(T_ref) @ T_moving
        return np.linalg.inv(ref_transform) @ moving_transform

    def clear_buffers(self) -> None:
        """Clear all data buffers."""
        self.frame_buffer.clear()
        self.transform_buffer.clear()
        self.processing_state['last_processed_frame'] = -1
        logger.info("Cleared all data buffers")


class StreamingProcessor(ABC):
    """
    Abstract base class for real-time processing algorithms.

    This class provides the interface for implementing online versions of
    processing algorithms (e.g., calibration, trajectory smoothing, etc.).
    Implementations should handle incremental processing, state management,
    and real-time constraints.

    Attributes:
        config: Algorithm-specific configuration
        state: Current processing state
        results_buffer: Buffer for storing intermediate results
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize streaming processor.

        Args:
            config: Configuration dictionary for the processor
        """
        self.config = config
        self.state = {}
        self.results_buffer = deque(maxlen=config.get('buffer_size', 1000))
        self._lock = threading.Lock()

    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        Process incoming data incrementally.

        Args:
            data: Input data to process

        Returns:
            Processing results
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset processor to initial state."""
        pass

    def get_state(self) -> Dict[str, Any]:
        """
        Get current processor state.

        Returns:
            Dictionary containing current state
        """
        with self._lock:
            return self.state.copy()

    def set_state(self, state: Dict[str, Any]) -> None:
        """
        Set processor state.

        Args:
            state: New state dictionary
        """
        with self._lock:
            self.state.update(state)


class CalibrationController(ABC):
    """
    Abstract base class for interactive calibration controllers.

    This class provides the framework for implementing different calibration
    strategies (button-triggered, automatic, guided) for online calibration.
    It manages the calibration workflow, user interaction, and data collection.

    Attributes:
        config: Calibration configuration
        motion_data: StreamingMotionCaptureData instance
        calibration_state: Current calibration progress
        event_handlers: Registered event callbacks
    """

    def __init__(self, config: Dict[str, Any], motion_data: StreamingMotionCaptureData):
        """
        Initialize calibration controller.

        Args:
            config: Calibration configuration dictionary
            motion_data: Streaming motion capture data instance
        """
        self.config = config
        self.motion_data = motion_data

        # Calibration state tracking
        self.calibration_state = {
            'current_landmark': None,
            'landmarks_completed': [],
            'captured_points': {},
            'capture_intervals': {},
            'is_active': False,
            'start_time': None
        }

        # Event handling
        self.event_handlers: Dict[str, List[Callable]] = {}

        # Stability detection
        self.stability_threshold = config.get('stability_threshold', 0.5)  # mm
        self.stability_duration = config.get('stability_duration', 0.5)  # seconds
        self.stability_buffer: Deque[StreamingFrame] = deque(maxlen=int(
            motion_data.data_source.statistics.average_fps * self.stability_duration
        ) if motion_data.data_source.statistics.average_fps > 0 else 30)

        logger.info(f"Initialized {self.__class__.__name__} with config: {config}")

    @abstractmethod
    def start_calibration(self) -> bool:
        """
        Start the calibration process.

        Returns:
            bool: True if calibration started successfully
        """
        pass

    @abstractmethod
    def capture_point(self) -> bool:
        """
        Capture the current calibration point.

        Returns:
            bool: True if point captured successfully
        """
        pass

    @abstractmethod
    def next_landmark(self) -> bool:
        """
        Move to the next calibration landmark.

        Returns:
            bool: True if moved to next landmark, False if calibration complete
        """
        pass

    def check_stability(self, tool_body_name: str) -> Tuple[bool, float]:
        """
        Check if the calibration tool is stable.

        Args:
            tool_body_name: Name of the calibration tool rigid body

        Returns:
            Tuple of (is_stable, variance) where variance is in mm
        """
        if self.stability_buffer.maxlen is None or len(self.stability_buffer) < self.stability_buffer.maxlen:
            return False, float('inf')

        # Extract tool positions from buffer
        positions = []
        for frame in self.stability_buffer:
            if tool_body_name in frame.rigid_bodies:
                rb = frame.rigid_bodies[tool_body_name]
                if rb.tracking_valid:
                    positions.append(rb.position)

        if len(positions) < len(self.stability_buffer) * 0.8:  # Require 80% valid frames
            return False, float('inf')

        positions = np.array(positions)

        # Calculate position variance
        mean_pos = np.mean(positions, axis=0)
        variance = np.mean(np.linalg.norm(positions - mean_pos, axis=1))

        is_stable = variance < self.stability_threshold

        return is_stable, variance

    def get_average_tool_transform(self, tool_body_name: str,
                                   duration: float = 1.0) -> Optional[np.ndarray]:
        """
        Get averaged transformation of the calibration tool over a time window.

        Args:
            tool_body_name: Name of the calibration tool rigid body
            duration: Time window in seconds

        Returns:
            4x4 averaged transformation matrix or None if insufficient data
        """
        # Collect frames from the specified duration
        frames_needed = int(self.motion_data.data_source.statistics.average_fps * duration)
        recent_frames = list(self.motion_data.frame_buffer)[-frames_needed:]

        if len(recent_frames) < frames_needed * 0.8:  # Require 80% of expected frames
            logger.warning(f"Insufficient frames for averaging: {len(recent_frames)}/{frames_needed}")
            return None

        # Extract transformations
        transforms = []
        for frame in recent_frames:
            if tool_body_name in frame.rigid_bodies:
                rb = frame.rigid_bodies[tool_body_name]
                if rb.tracking_valid:
                    transforms.append(rb.to_transform())

        if len(transforms) < len(recent_frames) * 0.8:
            logger.warning(f"Too many invalid frames: {len(transforms)}/{len(recent_frames)}")
            return None

        # Average transformations
        # Note: For proper rotation averaging, we should use quaternion averaging
        # but for small variations, arithmetic mean is acceptable
        avg_transform = np.mean(transforms, axis=0)

        # Ensure valid rotation matrix
        avg_transform[:3, :3] = hlp.ensure_orthonormal(avg_transform[:3, :3])

        return avg_transform

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def _emit_event(self, event_type: str, data: Any = None) -> None:
        """Emit an event to registered handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in calibration event handler: {e}")

    def reset_calibration(self) -> None:
        """Reset calibration to initial state."""
        self.calibration_state = {
            'current_landmark': None,
            'landmarks_completed': [],
            'captured_points': {},
            'capture_intervals': {},
            'is_active': False,
            'start_time': None
        }
        self.stability_buffer.clear()
        logger.info("Calibration reset to initial state")


def create_streaming_handler(system_type: str, config: Dict[str, Any]) -> StreamingMotionCaptureData:
    """
    Factory function to create appropriate streaming handler.

    Args:
        system_type: Type of motion capture system ('qualisys', 'optitrack', etc.)
        config: Configuration dictionary

    Returns:
        Appropriate StreamingMotionCaptureData instance

    Raises:
        ValueError: If system_type is not supported
    """
    if system_type == 'qualisys':
        from . import qualisys_streaming as qstm

        return qstm.create_qualisys_streaming_handler(config)
    else:
        raise NotImplementedError(f"Streaming handler for '{system_type}' not yet implemented")