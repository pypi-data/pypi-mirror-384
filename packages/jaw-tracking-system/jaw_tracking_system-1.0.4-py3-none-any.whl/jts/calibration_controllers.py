#!/usr/bin/env python3

"""
calibration_controllers.py: Concrete implementations of online calibration procedures.

This module provides three different calibration strategies:
    1. Button-triggered calibration with stability detection
    2. Automatic calibration based on stability detection
    3. Guided sequential calibration with interactive feedback
"""

__author__ = "Paul-Otto Müller"
__copyright__ = "Copyright 2025, Paul-Otto Müller"
__credits__ = ["Paul-Otto Müller"]
__license__ = "CC BY-NC-SA 4.0"
__version__ = "1.0.4"
__maintainer__ = "Paul-Otto Müller"
__status__ = "Development"
__date__ = '16.10.2025'
__url__ = "https://github.com/paulotto/jaw_tracking_system"

import time
import threading

from typing import Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum, auto

import numpy as np

from . import helper as hlp
from . import streaming as stm

# Set up module logger
logger = hlp.setup_logger(__name__)


class CalibrationStatus(Enum):
    """Status of individual calibration points."""
    PENDING = auto()
    IN_PROGRESS = auto()
    CAPTURED = auto()
    FAILED = auto()
    VALIDATED = auto()


class ButtonTriggeredCalibration(stm.CalibrationController):
    """
    Button-triggered calibration with stability detection.

    This implementation waits for manual user input (button press/key press)
    to capture calibration points. It provides real-time stability feedback
    to help users know when the tool is stable enough for capture.

    Workflow:
        1. User places calibration tool on landmark
        2. System monitors stability and provides feedback
        3. When stable, user triggers capture via button/key
        4. System captures and averages frames over capture window
        5. User moves to next landmark
    """

    def __init__(self, config: Dict[str, Any], motion_data: stm.StreamingMotionCaptureData):
        """
        Initialize button-triggered calibration controller.

        Args:
            config: Calibration configuration
            motion_data: Streaming motion capture data instance
        """
        super().__init__(config, motion_data)

        # Calibration tool configuration
        self.tool_name = config['online_config'].get('calibration_tool_name', 'CT')
        self.capture_window = config['online_config'].get('capture_window', 1.0)

        # Landmark configuration
        self.landmark_groups = config['online_config'].get('landmarks', {})
        self.all_landmarks = []
        for group_name, landmarks in self.landmark_groups.items():
            for landmark in landmarks:
                self.all_landmarks.append({
                    'name': landmark,
                    'group': group_name,
                    'status': CalibrationStatus.PENDING,
                    'position': None,
                    'capture_time': None,
                    'confidence': 0.0,
                    'frame_count': 0
                })

        # Current landmark tracking
        self.current_landmark_index = -1

        # Stability monitoring
        self._stability_thread = None
        self._monitor_stability = False
        self._current_stability = 0.0
        self._is_stable = False

        # Capture state
        self._capture_in_progress = False
        self._capture_start_time = None
        self._capture_frames = []

        logger.info(f"Initialized ButtonTriggeredCalibration with {len(self.all_landmarks)} landmarks")

    def start_calibration(self) -> bool:
        """
        Start the calibration process.

        Returns:
            bool: True if calibration started successfully
        """
        if self.calibration_state['is_active']:
            logger.warning("Calibration already active")
            return False

        # Reset calibration state
        self.reset_calibration()

        # Set up landmarks
        for landmark in self.all_landmarks:
            landmark['status'] = CalibrationStatus.PENDING
            landmark['position'] = None
            landmark['capture_time'] = None
            landmark['confidence'] = 0.0
            landmark['frame_count'] = 0

        # Start with first landmark
        self.calibration_state['is_active'] = True
        self.calibration_state['start_time'] = datetime.now()

        # Move to first landmark
        if not self.next_landmark():
            logger.error("No landmarks configured")
            return False

        # Start stability monitoring
        self._start_stability_monitoring()

        logger.info("Button-triggered calibration started")
        self._emit_event('calibration_started', {
            'total_landmarks': len(self.all_landmarks),
            'method': 'button_triggered'
        })

        return True

    def capture_point(self) -> bool:
        """
        Capture the current calibration point when triggered by user.

        Returns:
            bool: True if point captured successfully
        """
        if not self.calibration_state['is_active']:
            logger.error("Calibration not active")
            return False

        if self._capture_in_progress:
            logger.warning("Capture already in progress")
            return False

        if self.current_landmark_index < 0 or self.current_landmark_index >= len(self.all_landmarks):
            logger.error("No current landmark selected")
            return False

        current_landmark = self.all_landmarks[self.current_landmark_index]

        # Check stability before allowing capture
        is_stable, variance = self.check_stability(self.tool_name)

        if not is_stable and self.config['online_config'].get('require_stability', True):
            logger.warning(f"Tool not stable enough for capture (variance: {variance:.2f}mm)")
            self._emit_event('capture_rejected', {
                'landmark': current_landmark['name'],
                'reason': 'not_stable',
                'variance': variance
            })
            return False

        # Start capture process
        self._capture_in_progress = True
        self._capture_start_time = time.time()
        self._capture_frames = []

        current_landmark['status'] = CalibrationStatus.IN_PROGRESS

        logger.info(f"Starting capture for landmark '{current_landmark['name']}'")
        self._emit_event('capture_started', {
            'landmark': current_landmark['name'],
            'stability': variance
        })

        # Start capture thread
        capture_thread = threading.Thread(
            target=self._capture_process,
            args=(current_landmark,)
        )
        capture_thread.start()

        return True

    def next_landmark(self) -> bool:
        """
        Move to the next calibration landmark.

        Returns:
            bool: True if moved to next landmark, False if calibration complete
        """
        # Find next pending landmark
        next_index = self.current_landmark_index + 1

        while next_index < len(self.all_landmarks):
            if self.all_landmarks[next_index]['status'] == CalibrationStatus.PENDING:
                self.current_landmark_index = next_index
                self.calibration_state['current_landmark'] = self.all_landmarks[next_index]['name']

                logger.info(f"Moving to landmark '{self.all_landmarks[next_index]['name']}' "
                            f"({next_index + 1}/{len(self.all_landmarks)})")

                self._emit_event('landmark_changed', {
                    'landmark': self.all_landmarks[next_index]['name'],
                    'index': next_index,
                    'total': len(self.all_landmarks)
                })

                return True
            next_index += 1

        # No more landmarks
        logger.info("All landmarks captured")
        self._complete_calibration()
        return False

    def _capture_process(self, landmark: Dict[str, Any]) -> None:
        """
        Capture process running in separate thread.

        Args:
            landmark: Landmark dictionary to update
        """
        capture_duration = self.config['online_config'].get('capture_window', 1.0)
        capture_end_time = self._capture_start_time + capture_duration

        # Collect frames during capture window
        while time.time() < capture_end_time:
            # Get current tool transform
            current_transform = self.motion_data.get_current_transform(self.tool_name)

            if current_transform is not None:
                self._capture_frames.append(current_transform)
                landmark['frame_count'] = len(self._capture_frames)

                # Emit progress update
                if self._capture_start_time is not None:
                    progress = (time.time() - self._capture_start_time) / capture_duration
                else:
                    progress = 0.0
                self._emit_event('capture_progress', {
                    'landmark': landmark['name'],
                    'progress': progress,
                    'frames': len(self._capture_frames)
                })

            time.sleep(0.01)  # Small delay to avoid overwhelming the system

        # Process captured frames
        if len(self._capture_frames) >= 10:  # Minimum frames required
            # Average the transformations
            avg_transform = self._average_transforms(self._capture_frames)

            # Extract tool tip position (origin of calibration tool)
            landmark['position'] = avg_transform[:3, 3]
            landmark['capture_time'] = datetime.now()
            landmark['status'] = CalibrationStatus.CAPTURED

            # Calculate confidence based on position variance
            positions = np.array([t[:3, 3] for t in self._capture_frames])
            position_variance = np.std(positions, axis=0).mean()
            landmark['confidence'] = 1.0 / (1.0 + position_variance)  # Higher confidence for lower variance

            logger.info(f"Successfully captured landmark '{landmark['name']}' "
                        f"with {len(self._capture_frames)} frames, "
                        f"confidence: {landmark['confidence']:.2f}")

            self._emit_event('capture_completed', {
                'landmark': landmark['name'],
                'position': landmark['position'].tolist(),
                'confidence': landmark['confidence'],
                'frames': len(self._capture_frames)
            })

            # Add to calibration state
            group = landmark['group']
            if group not in self.calibration_state['captured_points']:
                self.calibration_state['captured_points'][group] = []
            self.calibration_state['captured_points'][group].append(landmark['position'])

            # Automatically move to next landmark if configured
            if self.config['online_config'].get('auto_advance', True):
                time.sleep(0.5)  # Brief pause before advancing
                self.next_landmark()

        else:
            landmark['status'] = CalibrationStatus.FAILED
            logger.error(f"Failed to capture landmark '{landmark['name']}': insufficient frames")

            self._emit_event('capture_failed', {
                'landmark': landmark['name'],
                'reason': 'insufficient_frames',
                'frames': len(self._capture_frames)
            })

        self._capture_in_progress = False
        self._capture_frames = []

    def _average_transforms(self, transforms: List[np.ndarray]) -> np.ndarray:
        """
        Average a list of transformation matrices.

        Args:
            transforms: List of 4x4 transformation matrices

        Returns:
            Averaged 4x4 transformation matrix
        """
        # Average positions
        positions = np.array([t[:3, 3] for t in transforms])
        avg_position = np.mean(positions, axis=0)

        # Average rotations using quaternions
        from scipy.spatial.transform import Rotation as R
        quaternions = []
        for t in transforms:
            rot = R.from_matrix(t[:3, :3])
            quaternions.append(rot.as_quat())

        # Simple quaternion averaging (works for small variations)
        avg_quat = np.mean(quaternions, axis=0)
        avg_quat = avg_quat / np.linalg.norm(avg_quat)  # Normalize
        avg_rotation = R.from_quat(avg_quat).as_matrix()

        # Build averaged transform
        avg_transform = np.eye(4)
        avg_transform[:3, :3] = avg_rotation
        avg_transform[:3, 3] = avg_position

        return avg_transform

    def _start_stability_monitoring(self) -> None:
        """Start the stability monitoring thread."""
        self._monitor_stability = True
        self._stability_thread = threading.Thread(
            target=self._stability_monitor_loop,
            name="StabilityMonitor"
        )
        self._stability_thread.daemon = True
        self._stability_thread.start()

    def _stability_monitor_loop(self) -> None:
        """Continuous stability monitoring loop."""
        while self._monitor_stability and self.calibration_state['is_active']:
            # Update stability buffer with recent frames
            recent_frames = list(self.motion_data.frame_buffer)[-30:]  # Last ~1 second at 30Hz
            self.stability_buffer.clear()
            self.stability_buffer.extend(recent_frames)

            # Check stability
            is_stable, variance = self.check_stability(self.tool_name)

            # Update state
            self._is_stable = is_stable
            self._current_stability = variance

            # Emit stability update
            self._emit_event('stability_update', {
                'is_stable': is_stable,
                'variance': variance,
                'threshold': self.stability_threshold
            })

            time.sleep(0.1)  # Update at 10Hz

    def _complete_calibration(self) -> None:
        """Complete the calibration process."""
        self._monitor_stability = False

        # Wait for monitoring thread to stop
        if self._stability_thread and self._stability_thread.is_alive():
            self._stability_thread.join(timeout=1.0)

        # Calculate overall statistics
        total_captured = sum(1 for lm in self.all_landmarks
                             if lm['status'] == CalibrationStatus.CAPTURED)

        avg_confidence = np.mean([lm['confidence'] for lm in self.all_landmarks
                                  if lm['status'] == CalibrationStatus.CAPTURED])

        duration = (datetime.now() - self.calibration_state['start_time']).total_seconds()

        self.calibration_state['is_active'] = False

        logger.info(f"Calibration completed: {total_captured}/{len(self.all_landmarks)} landmarks, "
                    f"avg confidence: {avg_confidence:.2f}, duration: {duration:.1f}s")

        self._emit_event('calibration_completed', {
            'total_landmarks': len(self.all_landmarks),
            'captured_landmarks': total_captured,
            'average_confidence': avg_confidence,
            'duration': duration,
            'captured_points': self.calibration_state['captured_points']
        })


class AutomaticCalibration(stm.CalibrationController):
    """
    Automatic calibration based on stability detection.

    This implementation automatically captures calibration points when
    the tool remains stable for a specified duration. No manual triggering
    is required - the system detects stability and captures automatically.

    Workflow:
        1. User places calibration tool on landmark
        2. System detects when tool is stable for required duration
        3. Automatic capture and confirmation
        4. System prompts for next landmark
        5. User moves tool to next position
    """

    def __init__(self, config: Dict[str, Any], motion_data: stm.StreamingMotionCaptureData):
        """
        Initialize automatic calibration controller.

        Args:
            config: Calibration configuration
            motion_data: Streaming motion capture data instance
        """
        super().__init__(config, motion_data)

        # Calibration tool configuration
        self.tool_name = config['online_config'].get('calibration_tool_name', 'CT')

        # Auto-capture configuration
        self.auto_capture_delay = config['online_config'].get('auto_capture_delay', 0.5)
        self.post_capture_delay = config['online_config'].get('post_capture_delay', 2.0)

        # Landmark configuration (same as button-triggered)
        self.landmark_groups = config['online_config'].get('landmarks', {})
        self.all_landmarks = []
        for group_name, landmarks in self.landmark_groups.items():
            for landmark in landmarks:
                self.all_landmarks.append({
                    'name': landmark,
                    'group': group_name,
                    'status': CalibrationStatus.PENDING,
                    'position': None,
                    'capture_time': None,
                    'stability_duration': 0.0,
                    'attempts': 0
                })

        # Current landmark tracking
        self.current_landmark_index = -1

        # Stability tracking
        self._stability_start_time = None
        self._continuous_stability_duration = 0.0
        self._auto_capture_thread = None
        self._monitor_active = False

        logger.info(f"Initialized AutomaticCalibration with {len(self.all_landmarks)} landmarks")

    def start_calibration(self) -> bool:
        """
        Start the automatic calibration process.

        Returns:
            bool: True if calibration started successfully
        """
        if self.calibration_state['is_active']:
            logger.warning("Calibration already active")
            return False

        # Reset calibration state
        self.reset_calibration()

        # Set up landmarks
        for landmark in self.all_landmarks:
            landmark['status'] = CalibrationStatus.PENDING
            landmark['position'] = None
            landmark['capture_time'] = None
            landmark['stability_duration'] = 0.0
            landmark['attempts'] = 0

        # Start calibration
        self.calibration_state['is_active'] = True
        self.calibration_state['start_time'] = datetime.now()

        # Move to first landmark
        if not self.next_landmark():
            logger.error("No landmarks configured")
            return False

        # Start automatic capture monitoring
        self._start_auto_capture_monitoring()

        logger.info("Automatic calibration started")
        self._emit_event('calibration_started', {
            'total_landmarks': len(self.all_landmarks),
            'method': 'automatic'
        })

        return True

    def capture_point(self) -> bool:
        """
        In automatic mode, this method is called internally when stability is detected.

        Returns:
            bool: True if point captured successfully
        """
        if not self.calibration_state['is_active']:
            return False

        current_landmark = self.all_landmarks[self.current_landmark_index]

        # Get averaged transform over stability duration
        avg_transform = self.get_average_tool_transform(
            self.tool_name,
            duration=self.config['online_config'].get('capture_window', 1.0)
        )

        if avg_transform is None:
            logger.error(f"Failed to get tool transform for landmark '{current_landmark['name']}'")
            current_landmark['attempts'] += 1
            return False

        # Extract position and store
        current_landmark['position'] = avg_transform[:3, 3]
        current_landmark['capture_time'] = datetime.now()
        current_landmark['status'] = CalibrationStatus.CAPTURED
        current_landmark['stability_duration'] = self._continuous_stability_duration

        # Add to calibration state
        group = current_landmark['group']
        if group not in self.calibration_state['captured_points']:
            self.calibration_state['captured_points'][group] = []
        self.calibration_state['captured_points'][group].append(current_landmark['position'])

        logger.info(f"Automatically captured landmark '{current_landmark['name']}' "
                    f"after {self._continuous_stability_duration:.1f}s stability")

        self._emit_event('capture_completed', {
            'landmark': current_landmark['name'],
            'position': current_landmark['position'].tolist(),
            'stability_duration': self._continuous_stability_duration,
            'automatic': True
        })

        return True

    def next_landmark(self) -> bool:
        """
        Move to the next calibration landmark.

        Returns:
            bool: True if moved to next landmark, False if calibration complete
        """
        # Reset stability tracking
        self._stability_start_time = None
        self._continuous_stability_duration = 0.0

        # Find next pending landmark
        next_index = self.current_landmark_index + 1

        while next_index < len(self.all_landmarks):
            if self.all_landmarks[next_index]['status'] == CalibrationStatus.PENDING:
                self.current_landmark_index = next_index
                self.calibration_state['current_landmark'] = self.all_landmarks[next_index]['name']

                logger.info(f"Ready for landmark '{self.all_landmarks[next_index]['name']}' "
                            f"({next_index + 1}/{len(self.all_landmarks)})")

                self._emit_event('landmark_changed', {
                    'landmark': self.all_landmarks[next_index]['name'],
                    'index': next_index,
                    'total': len(self.all_landmarks),
                    'instruction': 'Place calibration tool on landmark and hold steady'
                })

                return True
            next_index += 1

        # No more landmarks
        logger.info("All landmarks captured")
        self._complete_calibration()
        return False

    def _start_auto_capture_monitoring(self) -> None:
        """Start the automatic capture monitoring thread."""
        self._monitor_active = True
        self._auto_capture_thread = threading.Thread(
            target=self._auto_capture_loop,
            name="AutoCaptureMonitor"
        )
        self._auto_capture_thread.daemon = True
        self._auto_capture_thread.start()

    def _auto_capture_loop(self) -> None:
        """Main loop for automatic capture monitoring."""
        last_capture_time = 0

        while self._monitor_active and self.calibration_state['is_active']:
            # Check if enough time has passed since last capture
            if time.time() - last_capture_time < self.post_capture_delay:
                time.sleep(0.1)
                continue

            # Update stability buffer
            recent_frames = list(self.motion_data.frame_buffer)[-30:]
            self.stability_buffer.clear()
            self.stability_buffer.extend(recent_frames)

            # Check stability
            is_stable, variance = self.check_stability(self.tool_name)

            # Track continuous stability duration
            if is_stable:
                if self._stability_start_time is None:
                    self._stability_start_time = time.time()
                    self._emit_event('stability_detected', {
                        'landmark': self.calibration_state['current_landmark'],
                        'variance': variance
                    })

                self._continuous_stability_duration = time.time() - self._stability_start_time

                # Emit progress updates
                progress = self._continuous_stability_duration / self.stability_duration
                self._emit_event('stability_progress', {
                    'landmark': self.calibration_state['current_landmark'],
                    'duration': self._continuous_stability_duration,
                    'required_duration': self.stability_duration,
                    'progress': min(1.0, progress)
                })

                # Check if stable long enough for capture
                if self._continuous_stability_duration >= self.stability_duration:
                    logger.info(f"Stability threshold met, capturing in {self.auto_capture_delay}s")

                    # Brief delay before capture
                    time.sleep(self.auto_capture_delay)

                    # Capture the point
                    if self.capture_point():
                        last_capture_time = time.time()

                        # Wait before moving to next
                        time.sleep(self.post_capture_delay)

                        # Move to next landmark
                        self.next_landmark()

            else:
                # Lost stability
                if self._stability_start_time is not None:
                    self._emit_event('stability_lost', {
                        'landmark': self.calibration_state['current_landmark'],
                        'duration': self._continuous_stability_duration
                    })

                self._stability_start_time = None
                self._continuous_stability_duration = 0.0

            # Update at reasonable rate
            time.sleep(0.05)  # 20Hz update rate

    def _complete_calibration(self) -> None:
        """Complete the automatic calibration process."""
        self._monitor_active = False

        # Wait for monitoring thread
        if self._auto_capture_thread and self._auto_capture_thread.is_alive():
            self._auto_capture_thread.join(timeout=1.0)

        # Calculate statistics
        total_captured = sum(1 for lm in self.all_landmarks
                             if lm['status'] == CalibrationStatus.CAPTURED)

        total_attempts = sum(lm['attempts'] for lm in self.all_landmarks)

        avg_stability_time = np.mean([lm['stability_duration'] for lm in self.all_landmarks
                                      if lm['status'] == CalibrationStatus.CAPTURED])

        duration = (datetime.now() - self.calibration_state['start_time']).total_seconds()

        self.calibration_state['is_active'] = False

        logger.info(f"Automatic calibration completed: {total_captured}/{len(self.all_landmarks)} landmarks, "
                    f"avg stability time: {avg_stability_time:.1f}s, duration: {duration:.1f}s")

        self._emit_event('calibration_completed', {
            'total_landmarks': len(self.all_landmarks),
            'captured_landmarks': total_captured,
            'total_attempts': total_attempts,
            'average_stability_time': avg_stability_time,
            'duration': duration,
            'captured_points': self.calibration_state['captured_points']
        })


class GuidedSequentialCalibration(stm.CalibrationController):
    """
    Guided sequential calibration with interactive feedback.

    This implementation provides step-by-step guidance through the calibration
    process with real-time visual and audio feedback. It combines automatic
    detection with user confirmation for the best of both approaches.

    Workflow:
        1. System displays/announces current landmark to capture
        2. Real-time visual feedback shows tool position and stability
        3. Countdown timer when tool is stable
        4. Automatic capture with option to retry
        5. Visual confirmation and progress tracking
        6. Guided transition to next landmark
    """

    def __init__(self, config: Dict[str, Any], motion_data: stm.StreamingMotionCaptureData):
        """
        Initialize guided calibration controller.

        Args:
            config: Calibration configuration
            motion_data: Streaming motion capture data instance
        """
        super().__init__(config, motion_data)

        # Calibration tool configuration
        self.tool_name = config['online_config'].get('calibration_tool_name', 'CT')

        # Feedback configuration
        self.enable_visual = config['online_config']['feedback'].get('visual', True)
        self.enable_audio = config['online_config']['feedback'].get('audio', True)
        self.enable_voice = config['online_config']['feedback'].get('voice_prompts', False)

        # Guided mode configuration
        self.countdown_duration = config['online_config'].get('countdown_duration', 3.0)
        self.require_confirmation = config['online_config'].get('require_confirmation', True)
        self.allow_retry = config['online_config'].get('allow_retry', True)
        self.max_retries = config['online_config'].get('max_retries', 3)

        # Landmark configuration with detailed info
        self.landmark_groups = config['online_config'].get('landmarks', {})
        self.all_landmarks = []
        for group_name, landmarks in self.landmark_groups.items():
            for i, landmark in enumerate(landmarks):
                self.all_landmarks.append({
                    'name': landmark,
                    'group': group_name,
                    'status': CalibrationStatus.PENDING,
                    'position': None,
                    'capture_time': None,
                    'instruction': self._get_landmark_instruction(landmark, group_name),
                    'order': i,
                    'retries': 0,
                    'quality_score': 0.0
                })

        # Current state
        self.current_landmark_index = -1
        self._countdown_active = False
        self._countdown_start = None
        self._guidance_thread = None
        self._guidance_active = False

        # Quality metrics
        self.quality_thresholds = {
            'position_variance': 0.3,  # mm
            'rotation_variance': 0.5,  # degrees
            'min_frames': 30,
            'confidence_threshold': 0.8
        }

        logger.info(f"Initialized GuidedSequentialCalibration with {len(self.all_landmarks)} landmarks")

    def start_calibration(self) -> bool:
        """
        Start the guided calibration process.

        Returns:
            bool: True if calibration started successfully
        """
        if self.calibration_state['is_active']:
            logger.warning("Calibration already active")
            return False

        # Reset calibration state
        self.reset_calibration()

        # Set up landmarks
        for landmark in self.all_landmarks:
            landmark['status'] = CalibrationStatus.PENDING
            landmark['position'] = None
            landmark['capture_time'] = None
            landmark['retries'] = 0
            landmark['quality_score'] = 0.0

        # Start calibration
        self.calibration_state['is_active'] = True
        self.calibration_state['start_time'] = datetime.now()

        # Emit welcome message
        self._emit_event('calibration_started', {
            'total_landmarks': len(self.all_landmarks),
            'method': 'guided_sequential',
            'message': 'Welcome to guided calibration. Follow the on-screen instructions.'
        })

        # Start with first landmark
        if not self.next_landmark():
            logger.error("No landmarks configured")
            return False

        # Start guidance thread
        self._start_guidance_system()

        logger.info("Guided calibration started")
        return True

    def capture_point(self) -> bool:
        """
        Capture point with quality assessment and confirmation.

        Returns:
            bool: True if point captured successfully
        """
        if not self.calibration_state['is_active'] or self._countdown_active:
            return False

        current_landmark = self.all_landmarks[self.current_landmark_index]

        # Assess capture quality
        quality_score, quality_details = self._assess_capture_quality()

        if quality_score < self.quality_thresholds['confidence_threshold']:
            # Poor quality capture
            current_landmark['retries'] += 1

            if current_landmark['retries'] < self.max_retries and self.allow_retry:
                self._emit_event('capture_quality_low', {
                    'landmark': current_landmark['name'],
                    'quality_score': quality_score,
                    'details': quality_details,
                    'retry_count': current_landmark['retries'],
                    'message': 'Quality too low. Please try again.'
                })
                return False
            else:
                # Max retries reached, accept anyway
                logger.warning(f"Accepting low quality capture for '{current_landmark['name']}' "
                               f"after {current_landmark['retries']} retries")

        # Get averaged transform
        avg_transform = self.get_average_tool_transform(
            self.tool_name,
            duration=self.config['online_config'].get('capture_window', 1.0)
        )

        if avg_transform is None:
            return False

        # Store capture
        current_landmark['position'] = avg_transform[:3, 3]
        current_landmark['capture_time'] = datetime.now()
        current_landmark['status'] = CalibrationStatus.CAPTURED
        current_landmark['quality_score'] = quality_score

        # Add to calibration state
        group = current_landmark['group']
        if group not in self.calibration_state['captured_points']:
            self.calibration_state['captured_points'][group] = []
        self.calibration_state['captured_points'][group].append(current_landmark['position'])

        # Request confirmation if enabled
        if self.require_confirmation:
            self._emit_event('capture_confirmation_required', {
                'landmark': current_landmark['name'],
                'position': current_landmark['position'].tolist(),
                'quality_score': quality_score,
                'message': 'Confirm capture? (Press ENTER to confirm, ESC to retry)'
            })
            # Actual confirmation would be handled by UI callback
        else:
            # Auto-confirm
            self._confirm_capture()

        return True

    def next_landmark(self) -> bool:
        """
        Move to next landmark with guidance.

        Returns:
            bool: True if moved to next landmark, False if complete
        """
        # Find next pending landmark
        next_index = self.current_landmark_index + 1

        while next_index < len(self.all_landmarks):
            if self.all_landmarks[next_index]['status'] == CalibrationStatus.PENDING:
                self.current_landmark_index = next_index
                current = self.all_landmarks[next_index]
                self.calibration_state['current_landmark'] = current['name']

                # Emit guidance for new landmark
                self._emit_event('landmark_changed', {
                    'landmark': current['name'],
                    'group': current['group'],
                    'index': next_index,
                    'total': len(self.all_landmarks),
                    'instruction': current['instruction'],
                    'progress': (next_index / len(self.all_landmarks)) * 100
                })

                # Voice prompt if enabled
                if self.enable_voice:
                    self._emit_event('voice_prompt', {
                        'text': f"Please place the calibration tool on {current['name']}"
                    })

                return True
            next_index += 1

        # All landmarks complete
        self._complete_calibration()
        return False

    def _start_guidance_system(self) -> None:
        """Start the guidance monitoring system."""
        self._guidance_active = True
        self._guidance_thread = threading.Thread(
            target=self._guidance_loop,
            name="GuidanceSystem"
        )
        self._guidance_thread.daemon = True
        self._guidance_thread.start()

    def _guidance_loop(self) -> None:
        """Main guidance loop providing real-time feedback."""
        last_feedback_time = 0
        feedback_interval = 0.1  # 10Hz feedback rate

        while self._guidance_active and self.calibration_state['is_active']:
            current_time = time.time()

            # Rate limit feedback
            if current_time - last_feedback_time < feedback_interval:
                time.sleep(0.01)
                continue

            # Update stability buffer
            recent_frames = list(self.motion_data.frame_buffer)[-30:]
            self.stability_buffer.clear()
            self.stability_buffer.extend(recent_frames)

            # Check tool visibility
            tool_transform = self.motion_data.get_current_transform(self.tool_name)

            if tool_transform is None:
                self._emit_event('tool_not_visible', {
                    'message': 'Calibration tool not visible. Please check markers.'
                })
                self._countdown_active = False
                self._countdown_start = None
                time.sleep(feedback_interval)
                continue

            # Check stability
            is_stable, variance = self.check_stability(self.tool_name)

            # Provide real-time feedback
            feedback = {
                'tool_visible': True,
                'is_stable': is_stable,
                'stability_variance': variance,
                'stability_threshold': self.stability_threshold,
                'landmark': self.calibration_state['current_landmark']
            }

            # Handle countdown when stable
            if is_stable and not self._countdown_active:
                # Start countdown
                self._countdown_active = True
                self._countdown_start = current_time
                self._emit_event('countdown_started', {
                    'duration': self.countdown_duration,
                    'landmark': self.calibration_state['current_landmark']
                })

            elif is_stable and self._countdown_active:
                # Update countdown
                if self._countdown_start is not None:
                    elapsed = current_time - self._countdown_start
                    remaining = max(0, self.countdown_duration - elapsed)
                else:
                    remaining = self.countdown_duration

                feedback['countdown_active'] = True
                feedback['countdown_remaining'] = remaining

                if remaining <= 0:
                    # Countdown complete, capture
                    self._countdown_active = False
                    self.capture_point()

            elif not is_stable and self._countdown_active:
                # Lost stability during countdown
                self._countdown_active = False
                self._countdown_start = None
                self._emit_event('countdown_cancelled', {
                    'reason': 'stability_lost',
                    'message': 'Tool moved. Please hold steady.'
                })

            # Emit feedback
            self._emit_event('guidance_feedback', feedback)
            last_feedback_time = current_time

    def _assess_capture_quality(self) -> Tuple[float, Dict[str, Any]]:
        """
        Assess the quality of the current capture.

        Returns:
            Tuple of (quality_score, quality_details)
        """
        recent_transforms = self.motion_data.get_buffered_transforms(
            self.tool_name,
            window_size=int(self.motion_data.data_source.statistics.average_fps)
        )

        if len(recent_transforms) < self.quality_thresholds['min_frames']:
            return 0.0, {'error': 'insufficient_frames'}

        # Calculate position variance
        positions = np.array([t[:3, 3] for t in recent_transforms])
        position_variance = np.std(positions, axis=0).mean()

        # Calculate rotation variance
        from scipy.spatial.transform import Rotation as R
        rotations = [R.from_matrix(t[:3, :3]) for t in recent_transforms]
        euler_angles = np.array([r.as_euler('xyz', degrees=True) for r in rotations])
        rotation_variance = np.std(euler_angles, axis=0).mean()

        # Calculate quality scores
        position_score = 1.0 / (1.0 + position_variance / self.quality_thresholds['position_variance'])
        rotation_score = 1.0 / (1.0 + rotation_variance / self.quality_thresholds['rotation_variance'])
        frame_score = min(1.0, len(recent_transforms) / (self.quality_thresholds['min_frames'] * 2))

        # Overall quality score
        quality_score = (position_score + rotation_score + frame_score) / 3.0

        details = {
            'position_variance': position_variance,
            'rotation_variance': rotation_variance,
            'frame_count': len(recent_transforms),
            'position_score': position_score,
            'rotation_score': rotation_score,
            'frame_score': frame_score
        }

        return quality_score, details

    def _confirm_capture(self) -> None:
        """Confirm the current capture and move to next landmark."""
        current_landmark = self.all_landmarks[self.current_landmark_index]

        self._emit_event('capture_confirmed', {
            'landmark': current_landmark['name'],
            'quality_score': current_landmark['quality_score'],
            'position': current_landmark['position'].tolist()
        })

        # Brief pause before moving to next
        time.sleep(1.0)

        # Move to next landmark
        self.next_landmark()

    def _get_landmark_instruction(self, landmark_name: str, group: str) -> str:
        """
        Generate instruction text for a landmark.

        Args:
            landmark_name: Name of the landmark
            group: Landmark group (mandibular/maxillary)

        Returns:
            Instruction string
        """
        # Generate anatomically meaningful instructions
        instructions = {
            'mandibular': {
                'mand_point_1': 'Place tool on the left mandibular condyle',
                'mand_point_2': 'Place tool on the right mandibular condyle',
                'mand_point_3': 'Place tool on the mandibular symphysis (chin)'
            },
            'maxillary': {
                'max_point_1': 'Place tool on the left maxillary tuberosity',
                'max_point_2': 'Place tool on the right maxillary tuberosity',
                'max_point_3': 'Place tool on the anterior nasal spine'
            }
        }

        default_instruction = f'Place calibration tool on {landmark_name}'

        return instructions.get(group, {}).get(landmark_name, default_instruction)

    def _complete_calibration(self) -> None:
        """Complete the guided calibration process."""
        self._guidance_active = False

        # Wait for guidance thread
        if self._guidance_thread and self._guidance_thread.is_alive():
            self._guidance_thread.join(timeout=1.0)

        # Calculate comprehensive statistics
        total_captured = sum(1 for lm in self.all_landmarks
                             if lm['status'] == CalibrationStatus.CAPTURED)

        avg_quality = np.mean([lm['quality_score'] for lm in self.all_landmarks
                               if lm['status'] == CalibrationStatus.CAPTURED])

        total_retries = sum(lm['retries'] for lm in self.all_landmarks)

        duration = (datetime.now() - self.calibration_state['start_time']).total_seconds()

        self.calibration_state['is_active'] = False

        # Generate calibration report
        report = {
            'total_landmarks': len(self.all_landmarks),
            'captured_landmarks': total_captured,
            'average_quality': avg_quality,
            'total_retries': total_retries,
            'duration': duration,
            'captured_points': self.calibration_state['captured_points'],
            'landmark_details': [
                {
                    'name': lm['name'],
                    'group': lm['group'],
                    'status': lm['status'].name,
                    'quality_score': lm['quality_score'],
                    'retries': lm['retries']
                }
                for lm in self.all_landmarks
            ]
        }

        logger.info(f"Guided calibration completed: {total_captured}/{len(self.all_landmarks)} landmarks, "
                    f"avg quality: {avg_quality:.2f}, duration: {duration:.1f}s")

        self._emit_event('calibration_completed', report)

        # Voice announcement if enabled
        if self.enable_voice:
            self._emit_event('voice_prompt', {
                'text': f"Calibration complete. Captured {total_captured} landmarks successfully."
            })


# Factory function to create appropriate calibration controller
def create_calibration_controller(method: str, config: Dict[str, Any],
                                  motion_data: stm.StreamingMotionCaptureData) -> stm.CalibrationController:
    """
    Factory function to create calibration controller based on method.

    Args:
        method: Calibration method ('button_triggered', 'automatic', 'guided')
        config: Calibration configuration
        motion_data: Streaming motion capture data instance

    Returns:
        Appropriate CalibrationController instance

    Raises:
        ValueError: If method is not supported
    """
    controllers = {
        'button_triggered': ButtonTriggeredCalibration,
        'automatic': AutomaticCalibration,
        'guided': GuidedSequentialCalibration,
        'guided_sequential': GuidedSequentialCalibration  # Alias
    }

    if method not in controllers:
        raise ValueError(f"Unknown calibration method: {method}. "
                         f"Supported methods: {list(controllers.keys())}")

    return controllers[method](config, motion_data)
