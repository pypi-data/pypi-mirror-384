# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import wave
from typing import Dict
from ovos_utils.log import LOG
from ovos_plugin_manager.templates.tts import TTS

from phoonnx.model_manager import TTSModelManager, TTSModelInfo
from phoonnx.voice import TTSVoice, SynthesisConfig


class PhoonnxTTSPlugin(TTS):
    """Interface to Phoonnx TTS."""
    engines = {}

    def __init__(self, config=None):
        super().__init__(config=config)

        self.synth_params = SynthesisConfig(
            enable_phonetic_spellings=self.config.get("enable_phonetic_spelling", True),
            noise_scale=self.config.get("noise-scale"),  # generator noise
            length_scale=self.config.get("length-scale"),  # Phoneme length
            noise_w_scale=self.config.get("noise-w")  # Phoneme width noise
        )

        self.model_manager = TTSModelManager()
        try:
            self.model_manager.refresh_voices()
        except:
            self.model_manager.load()

        default = self.get_default_voice(self.lang)
        self.voices: Dict[str, TTSVoice] = {
            default.voice_id: default.load()
        }

    def get_default_voice(self, lang: str) -> TTSModelInfo:
        voices = self.model_manager.get_lang_voices(lang)
        if not voices:
            raise ValueError(f"No voices available for language: {lang}")
        return voices[0]

    def get_model(self, voice_id: str) -> TTSVoice:
        if voice_id in self.voices:
            return self.voices[voice_id]
        if voice_id not in self.model_manager.voices:
            raise Exception(f"Unknown voice: {voice_id}")
        LOG.debug(f"Using voice: {voice_id}")
        self.voices[voice_id] = self.model_manager.voices[voice_id].load()
        return self.voices[voice_id]

    def get_tts(self, sentence, wav_file, lang=None, voice=None):
        """Generate WAV and phonemes.

        Arguments:
            sentence (str): sentence to generate audio for
            wav_file (str): output file
            lang (str): optional lang override
            voice (str): optional voice override
            speaker (int): optional speaker override

        Returns:
            tuple ((str) file location, (str) generated phonemes)
        """
        if voice:
            model = self.get_model(voice)
        else:
            voice = self.get_default_voice(lang or self.lang)
            model = self.get_model(voice.voice_id)

    with wave.open(wav_file, "wb") as wav_out:
        model.synthesize_wav(sentence, wav_out, self.synth_params)

    return wav_file, None


if __name__ == "__main__":
    utterance = "Guimarães é uma das mais importantes cidades históricas do país, estando o seu centro histórico inscrito na lista de Património Mundial da UNESCO desde 2001, o que a torna definitivamente num dos maiores centros turísticos da região. As suas ruas e monumentos respiram história e encantam quem a visita."
    #utterance = "Um arco-íris, também popularmente denominado arco-da-velha, é um fenômeno óptico e meteorológico que separa a luz do sol em seu espectro contínuo quando o sol brilha sobre gotículas de água suspensas no ar."

    tts = PhoonnxTTSPlugin()
    tts.get_tts(utterance, "tmiro-pt-PT.wav",
                voice="OpenVoiceOS/phoonnx_pt-PT_miro_tugaphone")
    tts.get_tts(utterance, "tdii-pt-PT.wav",
                voice="OpenVoiceOS/phoonnx_pt-PT_dii_tugaphone")
    tts.get_tts(utterance, "miro-pt-PT.wav",
                voice="OpenVoiceOS/pipertts_pt-PT_miro")
    tts.get_tts(utterance, "dii-pt-PT.wav",
                voice="OpenVoiceOS/pipertts_pt-PT_dii")
