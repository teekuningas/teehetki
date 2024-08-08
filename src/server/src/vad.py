"""Köyhän miehen VAD."""
import numpy as np


class VAD:
    def __init__(
        self,
        sample_rate,
        threshold=0.001,
        energy_window_size=2.0,
        min_speech_length=2.0,
        max_buffer_length=120.0,
    ):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.energy_window_size = int(energy_window_size * sample_rate)
        self.min_speech_length = int(min_speech_length * sample_rate)
        self.max_buffer_length = int(max_buffer_length * sample_rate)
        self.reset()

    def update_threshold(self, threshold):
        self.threshold = threshold

    def detect(self, data):
        self.buffer = np.concatenate([self.buffer, data])

        # Ensure buffer does not exceed max length
        if len(self.buffer) > self.max_buffer_length:
            self.buffer = self.buffer[-self.max_buffer_length :]

        # Ensure buffer has enough samples for the energy window
        if len(self.buffer) >= self.energy_window_size:
            # Take a slice of the buffer for the energy window
            energy_window = self.buffer[-self.energy_window_size :]

            # Compute short-term energy
            energy = np.sum(energy_window**2)

            # Compute average energy
            avg_energy = energy / self.energy_window_size

            # Check if energy exceeds threshold
            if avg_energy > self.threshold:
                self.speech_segments.append(data)
                self.speech_detected = True
            else:
                if self.speech_detected:
                    # Check if the detected speech segment is long enough
                    speech_segment = np.concatenate(self.speech_segments)
                    if len(speech_segment) >= self.min_speech_length:
                        # Adjust the segment to include some past context
                        shift_amount = self.energy_window_size // 2
                        start_index = max(
                            0, len(self.buffer) - len(speech_segment) - shift_amount
                        )
                        segment = self.buffer[start_index : len(self.buffer)]

                        self.reset()
                        return {"segment": segment, "detected": True}
                    else:
                        self.reset()

        return {"segment": None, "detected": False}

    def reset(self):
        self.buffer = np.array([], dtype=np.float32)
        self.speech_segments = []
        self.speech_detected = False
