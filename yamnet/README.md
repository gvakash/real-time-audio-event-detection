# YAMNet Model Reference

This project uses **YAMNet**, a pretrained acoustic event classification model developed by Google and trained on the AudioSet dataset.

## Model Source
- TensorFlow Hub: https://tfhub.dev/google/yamnet/1
- Architecture: MobileNet-based audio CNN
- Training Data: Google AudioSet (521 sound classes)

## Usage in This Project
- The model is used **as-is** for inference only
- No fine-tuning or retraining is performed
- Audio input is resampled to 16 kHz to match model requirements
- Frame-level predictions are temporally aggregated into clip-level decisions

## Model Files
The full YAMNet model files are **not included** in this repository.

To run the project, download the model locally from TensorFlow Hub and place it in a directory referenced by the application configuration.

## License
YAMNet is provided under the Apache 2.0 License.
Please refer to the original TensorFlow Hub page for licensing details.
