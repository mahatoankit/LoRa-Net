import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import joblib
from scipy import signal

# Optimize TensorFlow for low-resource environments
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings
tf.config.threading.set_intra_op_parallelism_threads(2)  # Limit CPU threads
tf.config.threading.set_inter_op_parallelism_threads(2)

# Disable GPU (if not needed) to save memory
try:
    tf.config.set_visible_devices([], 'GPU')
except:
    pass

print("Loading Label Binarizer...")
label_binarizer = joblib.load('label_binarizer.pkl')
print("Loaded Successfully")

# Load YAMNet model from TensorFlow Hub (provides 1024-dim embeddings)
print("Loading YAMNet model from TensorFlow Hub...")
yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
print("YAMNet loaded.")

# Load classifier as TFLite if available, otherwise use Keras
print("Loading Keras Model...")
try:
    # Try to load TFLite version first (if you convert it)
    classifier_interpreter = tf.lite.Interpreter(model_path='multi_class_audio_classifier.tflite')
    classifier_interpreter.allocate_tensors()
    classifier_input_details = classifier_interpreter.get_input_details()
    classifier_output_details = classifier_interpreter.get_output_details()
    use_tflite_classifier = True
    print("TFLite classifier loaded.")
except:
    # Fallback to Keras model
    from tensorflow.keras.models import load_model
    keras_model = load_model('multi_class_audio_classifier.h5', compile=False)
    use_tflite_classifier = False
    print("Keras Model Loaded Successfully.")

def run_classifier_tflite(embedding):
    """Run classifier TFLite inference."""
    classifier_interpreter.set_tensor(classifier_input_details[0]['index'], embedding)
    classifier_interpreter.invoke()
    return classifier_interpreter.get_tensor(classifier_output_details[0]['index'])[0]

def run_inference(waveform, sr=16000, window_size=2.0, hop_size=1.0,
                  confidence_threshold=0.6, unknown_threshold=0.4):
    """
    Optimized inference for embedded systems.
    Uses TensorFlow Hub YAMNet for embeddings and TFLite/Keras for classification.
    """

    waveform = waveform.astype(np.float32)
    
    # Resample to 16kHz if needed (YAMNet requirement)
    if sr != 16000:
        num_samples = int(len(waveform) * 16000 / sr)
        waveform = signal.resample(waveform, num_samples)
        sr = 16000

    # YAMNet processes the entire audio and outputs multiple windows automatically
    # Each window is ~0.96s with 0.48s hop
    scores, embeddings, spectrogram = yamnet_model(waveform)
    
    prob_sums = np.zeros(len(label_binarizer.classes_))
    confident_window_count = 0
    
    # Process each embedding window
    for embedding in embeddings.numpy():
        embedding = embedding.reshape(1, -1).astype(np.float32)
        
        # Run classifier
        if use_tflite_classifier:
            probs = run_classifier_tflite(embedding)
        else:
            probs = keras_model(embedding, training=False).numpy()[0]
        
        max_prob = np.max(probs)
        
        if max_prob >= confidence_threshold:
            prob_sums += probs
            confident_window_count += 1
    
    num_windows = len(embeddings)

    if confident_window_count > 0:
        avg_probs = prob_sums / confident_window_count
    else:
        avg_probs = np.zeros(len(label_binarizer.classes_))

    unknown_prob = 0.0
    # If too few confident windows or max avg prob low, assign unknown prob
    if confident_window_count < num_windows or np.max(avg_probs) < unknown_threshold:
        unknown_prob = 1.0 - np.sum(avg_probs)
        unknown_prob = max(0.0, unknown_prob)

    final_classes = list(label_binarizer.classes_) + ['unknown']
    final_percentages = list(avg_probs * 100) + [unknown_prob * 100]

    final_classes = [str(x) for x in final_classes]
    final_percentages = [float(x) for x in final_percentages]

    return final_classes, final_percentages
