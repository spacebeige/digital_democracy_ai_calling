"""
Emotion Detection Module - Anger & Stress Detection from Voice
==============================================================
Analyzes voice patterns to detect:
- Anger/frustration
- Stress levels
- Tone changes and intensity spikes
- Speech rate abnormalities
"""

from typing import Tuple, List
from dataclasses import dataclass
import numpy as np
from models.grievance_models import EmotionAnalysis, EmotionState


@dataclass
class VoiceFeatures:
    """Extracted voice feature metrics."""
    mean_pitch: float  # Hz
    max_pitch: float  # Hz
    min_pitch: float  # Hz
    pitch_variance: float  # Variability
    mean_intensity: float  # dB
    max_intensity: float  # dB (peaks)
    intensity_variance: float  # Variability
    speech_rate: float  # Words per minute
    pause_count: int  # Number of pauses
    pause_duration: float  # Seconds of total pauses
    zero_crossings: float  # Audio signal feature (roughness)


def extract_voice_features(audio_data: np.ndarray, sample_rate: int = 16000) -> VoiceFeatures:
    """
    Extract acoustic features from audio.
    
    Args:
        audio_data: Audio samples (numpy array)
        sample_rate: Sample rate in Hz
        
    Returns:
        VoiceFeatures object with metrics
    """
    # Normalize audio
    audio_normalized = audio_data / (np.max(np.abs(audio_data)) + 1e-8)
    
    # Calculate zero crossings (roughness/tension indicator)
    zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_normalized)))) / 2
    zero_crossing_rate = zero_crossings / len(audio_data)
    
    # Calculate RMS (intensity)
    rms = np.sqrt(np.mean(audio_normalized ** 2))
    intensity_db = 20 * np.log10(rms + 1e-8)
    max_intensity_db = 20 * np.log10(np.max(np.abs(audio_normalized)) + 1e-8)
    
    # Simple pitch estimation using autocorrelation (simplified)
    # For production, use librosa.yin() or similar
    pitch_estimate = estimate_pitch_autocorr(audio_normalized, sample_rate)
    
    # Estimate speech rate (simplified: based on energy envelope)
    speech_rate = estimate_speech_rate(audio_normalized, sample_rate)
    
    # Count pauses/silence regions
    energy_envelope = np.convolve(np.abs(audio_normalized), np.ones(sample_rate // 50), mode='same')
    silence_threshold = np.mean(energy_envelope) * 0.1
    silent_frames = np.sum(energy_envelope < silence_threshold)
    pause_count = np.sum(np.diff((energy_envelope < silence_threshold).astype(int)) == 1)
    pause_duration = silent_frames / sample_rate
    
    return VoiceFeatures(
        mean_pitch=pitch_estimate[0],
        max_pitch=pitch_estimate[1],
        min_pitch=pitch_estimate[2],
        pitch_variance=pitch_estimate[3],
        mean_intensity=intensity_db,
        max_intensity=max_intensity_db,
        intensity_variance=np.var(energy_envelope),
        speech_rate=speech_rate,
        pause_count=pause_count,
        pause_duration=pause_duration,
        zero_crossings=zero_crossing_rate,
    )


def estimate_pitch_autocorr(audio: np.ndarray, sample_rate: int, min_hz: int = 50, max_hz: int = 400) -> Tuple[float, float, float, float]:
    """
    Simple pitch estimation using autocorrelation.
    
    Args:
        audio: Normalized audio signal
        sample_rate: Sample rate in Hz
        min_hz: Minimum expected pitch
        max_hz: Maximum expected pitch
        
    Returns:
        (mean_pitch, max_pitch, min_pitch, variance)
    """
    # Frame-based analysis
    frame_size = sample_rate // 50  # 20ms frames
    pitches = []
    
    for i in range(0, len(audio) - frame_size, frame_size // 2):
        frame = audio[i:i+frame_size]
        
        # Autocorrelation
        autocorr = np.correlate(frame, frame, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        autocorr = autocorr / autocorr[0]
        
        # Find pitch period
        min_period = sample_rate // max_hz
        max_period = sample_rate // min_hz
        
        if max_period < len(autocorr):
            autocorr_search = autocorr[min_period:max_period]
            if len(autocorr_search) > 0:
                period = np.argmax(autocorr_search) + min_period
                pitch = sample_rate / period if period > 0 else 0
                if min_hz < pitch < max_hz:
                    pitches.append(pitch)
    
    if pitches:
        mean_pitch = np.mean(pitches)
        max_pitch = np.max(pitches)
        min_pitch = np.min(pitches)
        pitch_variance = np.var(pitches)
    else:
        mean_pitch = max_pitch = min_pitch = pitch_variance = 0
    
    return mean_pitch, max_pitch, min_pitch, pitch_variance


def estimate_speech_rate(audio: np.ndarray, sample_rate: int) -> float:
    """
    Estimate speech rate in words per minute.
    
    Args:
        audio: Audio signal
        sample_rate: Sample rate
        
    Returns:
        Estimated words per minute
    """
    # Energy envelope
    frame_size = sample_rate // 50  # 20ms
    energy = []
    
    for i in range(0, len(audio) - frame_size, frame_size):
        frame = audio[i:i+frame_size]
        energy.append(np.sqrt(np.mean(frame ** 2)))
    
    energy = np.array(energy)
    
    # Count peaks (speech bursts ~ words)
    threshold = np.mean(energy) * 0.5
    peaks = np.sum(np.diff((energy > threshold).astype(int)) == 1)
    
    # Duration in seconds
    duration = len(audio) / sample_rate
    
    # Assume ~200ms per word burst on average
    estimated_words = peaks * (200 / 1000) / (duration / 60)
    
    return max(0, min(300, estimated_words))  # Clamp to reasonable range


def analyze_emotions(
    audio_data: np.ndarray,
    sample_rate: int = 16000,
    transcript_length: int = 0,
) -> EmotionAnalysis:
    """
    Comprehensive emotion analysis from voice.
    
    Args:
        audio_data: Audio samples
        sample_rate: Sample rate
        transcript_length: Length of transcript (helps contextualize)
        
    Returns:
        EmotionAnalysis with detected emotion and scores
    """
    
    # Extract features
    features = extract_voice_features(audio_data, sample_rate)
    
    # Calculate emotion indicators
    anger_indicators = []
    frustration_indicators = []
    stress_indicators = []
    
    # 1. PITCH ANALYSIS: Elevated pitch + high variance = Anger
    # Angry speech typically: higher mean pitch, increased variance
    pitch_elevation = min(1.0, features.mean_pitch / 200)  # Normalize to 0-1
    if features.mean_pitch > 150:  # Higher than neutral
        anger_indicators.append(pitch_elevation * 0.8)
    
    if features.pitch_variance > 100:  # High variability in pitch
        anger_indicators.append(min(1.0, features.pitch_variance / 200) * 0.7)
        frustration_indicators.append(0.6)
    
    # 2. INTENSITY ANALYSIS: Louder + More peaks = Anger/Stress
    intensity_level = min(1.0, (features.max_intensity + 40) / 50)  # Normalize -40dB to +10dB
    if features.max_intensity > -10:  # Loud
        anger_indicators.append(intensity_level * 0.8)
        stress_indicators.append(intensity_level * 0.7)
    
    # 3. SPEECH RATE ANALYSIS
    # Too fast (>200 WPM) = Anger/Stress
    # Too slow (<80 WPM with pauses) = Frustration/Sadness
    if features.speech_rate > 200:  # Very fast speech
        anger_indicators.append(0.7)
        stress_indicators.append(0.8)
    elif features.speech_rate < 80:  # Slow speech
        frustration_indicators.append(0.6)
    
    # 4. PAUSE ANALYSIS
    # Many pauses + long pauses = Hesitation/Stress
    if features.pause_count > 5 or features.pause_duration > 2:
        stress_indicators.append(0.7)
        frustration_indicators.append(0.5)
    
    # 5. ROUGHNESS ANALYSIS: High zero-crossing = Tense/Angry voice
    if features.zero_crossings > 0.1:  # Higher zero-crossing rate
        anger_indicators.append(min(1.0, features.zero_crossings * 5))
        stress_indicators.append(0.6)
    
    # Calculate average scores
    anger_score = np.mean(anger_indicators) if anger_indicators else 0.0
    frustration_score = np.mean(frustration_indicators) if frustration_indicators else 0.0
    stress_level = np.mean(stress_indicators) if stress_indicators else 0.0
    
    # Detect emotion state
    if anger_score > 0.7:
        detected_emotion = EmotionState.ANGRY
    elif anger_score > 0.5 and frustration_score > 0.5:
        detected_emotion = EmotionState.FRUSTRATED
    elif stress_level > 0.6:
        detected_emotion = EmotionState.ANXIOUS
    elif stress_level > 0.3:
        detected_emotion = EmotionState.NEUTRAL
    else:
        detected_emotion = EmotionState.CALM
    
    # Tone changes (count peaks in pitch)
    tone_changes = features.pause_count
    
    # Determine if speech rate is abnormal
    speech_rate_abnormal = features.speech_rate > 200 or features.speech_rate < 60
    
    # Build reasoning
    reasoning_parts = []
    if anger_score > 0.5:
        reasoning_parts.append(f"High pitch/intensity (anger: {anger_score:.1%})")
    if frustration_score > 0.5:
        reasoning_parts.append(f"Multiple pauses/hesitation (frustration: {frustration_score:.1%})")
    if stress_level > 0.5:
        reasoning_parts.append(f"Elevated stress indicators (stress: {stress_level:.1%})")
    if speech_rate_abnormal:
        reasoning_parts.append(f"Abnormal speech rate ({features.speech_rate:.0f} WPM)")
    
    reasoning = " + ".join(reasoning_parts) if reasoning_parts else "Neutral emotion detected"
    
    return EmotionAnalysis(
        detected_emotion=detected_emotion,
        anger_score=float(anger_score),
        frustration_score=float(frustration_score),
        stress_level=float(stress_level),
        tone_changes=tone_changes,
        speech_rate_abnormal=speech_rate_abnormal,
        reasoning=reasoning,
    )


def should_escalate_based_on_emotion(emotion: EmotionAnalysis) -> bool:
    """
    Determine if issue should be escalated based on emotion.
    
    Args:
        emotion: EmotionAnalysis object
        
    Returns:
        True if escalation recommended
    """
    # Escalate if: angry + high stress
    if emotion.anger_score > 0.7 and emotion.stress_level > 0.6:
        return True
    
    # Escalate if: extreme stress or anxiety
    if emotion.stress_level > 0.8:
        return True
    
    return False
