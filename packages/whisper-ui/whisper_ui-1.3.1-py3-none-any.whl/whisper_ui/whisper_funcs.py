import os
import re
import json

import torch
import faster_whisper
from faster_whisper import WhisperModel, BatchedInferencePipeline
from whisper.tokenizer import LANGUAGES, TO_LANGUAGE_CODE

from whisper_ui.handle_prefs import USER_PREFS, check_model
from whisper_ui.textgrid_utils import get_clip_timestamps, write_textgrid_fill_utterances

os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '0'

SUPPORTED_FILETYPES = ('flac', 'm4a', 'mp3', 'mp4', 'wav')

AVAILABLE_MODELS = faster_whisper.available_models()

VALID_LANGUAGES = sorted(
    LANGUAGES.keys()
) + sorted(
    [k.title() for k in TO_LANGUAGE_CODE.keys()]
)
LANGUAGES_FLIPPED = {v: k for k, v in LANGUAGES.items()}
TO_LANGUAGE_CODE_FLIPPED = {v: k for k, v in TO_LANGUAGE_CODE.items()}

EX_KEYS = {
    'output_dir',
    'model',
    'language',
    'do_translate',
    'text_template',
    'segmentation_template',
    'text_insertion_symbol',
    'segment_insertion_symbol',
    'start_time_insertion_symbol',
    'end_time_insertion_symbol',
    'do_text',
    'do_segmentation',
    'do_json',
    'DEBUG',
    'use_gpu',
    'use_textgrid',
    'clip_timestamps',
    'vad_filter'
}

class ModelInterface:

    def __init__(self):
        if USER_PREFS['DEBUG']:
            self.model = 'abc'
        else:
            self.model = None
        self.device = None
        self.device_name = None
        self.update_device(True)

    def update_device(self, log: bool = False):
        if torch.cuda.is_available() and USER_PREFS['use_gpu']:
            self.device_name = 'cuda'
        elif torch.backends.mps.is_available() and USER_PREFS['use_gpu']:
            self.device_name = 'mps'
        else:
            self.device_name = 'cpu'
        self.device = torch.device(self.device_name)
        if log:
            print(f'Device set to {self.device_name}.')
        
    def map_available_language_to_valid_language(self, available_language):
        
        if available_language == 'None':
            return None
        
        al = available_language.lower()
        if al not in VALID_LANGUAGES:
            if al in LANGUAGES_FLIPPED and LANGUAGES_FLIPPED[al] in VALID_LANGUAGES:
                return LANGUAGES_FLIPPED[al]
            elif al in TO_LANGUAGE_CODE_FLIPPED and TO_LANGUAGE_CODE_FLIPPED[al] in VALID_LANGUAGES:
                return TO_LANGUAGE_CODE_FLIPPED[al]
        else:
            return al

    def get_model(self, switch_model: bool = False):
        
        model_name = USER_PREFS["model"]
        
        if not check_model(model_name):
            msg = f'\t"model" is set to "{model_name}" which has not been downloaded.\n'
            msg += f'\tYou should first download this model from the "Download models" menu.\n'
            msg += f'\tCanceling. No files processed.'
            print(msg)
            return
            
        
        if self.model is None or switch_model:
            print(f'\tLoading model {model_name}. This may take a moment...')
            
            try:
                try:
                    self.model = BatchedInferencePipeline(
                        WhisperModel(model_size_or_path=USER_PREFS['model'], compute_type='float16')
                    )
                except:
                    self.model = BatchedInferencePipeline(
                        WhisperModel(model_size_or_path=USER_PREFS['model'])
                    )
                    print(f'\t\tCould not load half precision. Defaulting to full.')
            except:
                print('\t\tWarning: issue loading model onto GPU. Using CPU.')
                self.model = BatchedInferencePipeline(
                    WhisperModel(model_size_or_path=USER_PREFS['model'], device='cpu')
                )
            print(f'\tLoaded model {model_name} successfully.')
        else:
            print(f'\tUsing currently loaded model ({model_name}).')

    def format_outputs(self, segments):
        
        text_template = USER_PREFS['text_template']
        segmentation_template = USER_PREFS['segmentation_template']
        
        text_template_filled = None
        segmentation_lines = None

        full_text = ''
        segment_texts = []

        text_is = USER_PREFS['segment_insertion_symbol']
        start_is = USER_PREFS['start_time_insertion_symbol']
        end_is = USER_PREFS['end_time_insertion_symbol']
        
        segmentation_lines = []
        for segment in segments:
            full_text += segment.text
            text = segment.text.strip()
            segment_texts.append(text)
            start = str(segment.start)
            end = str(segment.end)
            seg_template_filled = segmentation_template.replace(
                text_is, text
            ).replace(
                start_is, start
            ).replace(
                end_is, end
            )
            segmentation_lines.append(seg_template_filled)

        text_is = USER_PREFS['text_insertion_symbol']
        text_template_filled = text_template.replace(
            text_is, full_text
        )
                
        return {
            'text': text_template_filled,
            'segmentation_lines': segmentation_lines,
            'segment_texts': segment_texts
        }

    def make_paths(self, output_dir, fname):
        
        txt_loc = os.path.join(output_dir, fname + '.txt')
        seg_loc = os.path.join(output_dir, fname + '.seg')
        json_loc = os.path.join(output_dir, fname + '.json')
        
        # if any of the files already exist, make new ones with incremented numbers
        while any((os.path.exists(txt_loc), os.path.exists(seg_loc), os.path.exists(json_loc))):
            
            # if already numbered, just increment
            endswith_suffix = re.search(r'_\d+$', fname)
            if endswith_suffix:
                fname = fname[:endswith_suffix.start()] +'_' + str(int(endswith_suffix.group()[1:])+1)
            
            # if not numbered, add _1
            else:
                fname += '_1'
                
            txt_loc = os.path.join(output_dir, fname + '.txt')
            seg_loc = os.path.join(output_dir, fname + '.seg')
            json_loc = os.path.join(output_dir, fname + '.json')
        
        # if none of the files exist, fname is fine
        else:
            return txt_loc, seg_loc, json_loc

    def write_outputs(self, outputs: dict, formatted_outputs: dict, fname: str):
        text = formatted_outputs['text']
        segmentation_lines = formatted_outputs['segmentation_lines']
        
        output_dir = USER_PREFS['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        txt_loc, seg_loc, json_loc = self.make_paths(output_dir, fname)
        
        if USER_PREFS['do_text']:
            with open(txt_loc, 'w+', encoding='utf-8') as f:
                f.write(text.strip())
            print(f'\t\tWrote transcription to "{os.path.abspath(txt_loc)}".')
        if USER_PREFS['do_segmentation']:
            with open(seg_loc, 'w+', encoding='utf-8') as g:
                for line in segmentation_lines:
                    g.write(line.strip() + '\n')
            print(f'\t\tWrote segmentation to "{os.path.abspath(seg_loc)}".')
        if USER_PREFS['do_json']:
            with open(json_loc, 'w+', encoding='utf-8') as h:
                json.dump(outputs, h, indent=4)
            print(f'\t\tWrote JSON data to "{os.path.abspath(json_loc)}".')

    def transcribe(self, paths: list, switch_model: bool):
        
        if not paths:
            print('No matching files found. Canceling.\n')
            return
        
        if not os.path.exists(USER_PREFS['output_dir']):
            print(f'Output directory {USER_PREFS["output_dir"]} does not exist. Canceling.\n')
            return
        
        print(f'Beginning transcription of {len(paths)} audio file(s).')

        self.get_model(switch_model=switch_model)

        if self.model is None:
            return
        
        for i, path in enumerate(paths):
            
            print(f'\tTranscribing "{path}" (file {i+1}/{len(paths)})...')
            
            path = os.path.normpath(path)
            assert os.path.exists(path)
            
            basename = os.path.basename(path)
            fname, ext = os.path.splitext(basename)
            
            if ext[1:] not in SUPPORTED_FILETYPES:
                msg = f'\tWarning: file "{path}" may not be supported. '
                msg += '\tSupported filetypes are: ' + ', '.join(SUPPORTED_FILETYPES)
                print(msg)
            
            if USER_PREFS['DEBUG']:
                outputs = json.load(
                    open(os.path.join('test_outputs', 'example_output.json'), 'r', encoding='utf-8')
                )
                formatted_outputs = {}
            else:
                kwargs = {
                        k: v for k, v in USER_PREFS.items()
                    }
                for ex_key in EX_KEYS:
                    del kwargs[ex_key]

                clip_timestamps = []
                textgrid_path = None
                if USER_PREFS['use_textgrid']:
                    path_no_ext = os.path.splitext(path)[0]
                    try:
                        textgrid_path = path_no_ext + '.TextGrid'
                        clip_timestamps = get_clip_timestamps(textgrid_path)
                    except:
                        try:
                            textgrid_path = path_no_ext + '.textgrid'
                            clip_timestamps = get_clip_timestamps(textgrid_path)
                        except:
                            print(f'\tWarning: Could not find a matching textgrid file.')

                using_textgrid = (clip_timestamps != [])
                
                segments, info = self.model.transcribe(
                    path,
                    language = self.map_available_language_to_valid_language(USER_PREFS['language']),
                    task = 'translate' if USER_PREFS['do_translate'] else 'transcribe',
                    clip_timestamps = clip_timestamps,
                    log_progress=True,
                    vad_filter=not using_textgrid,
                    **kwargs
                )
                formatted_outputs = self.format_outputs(segments)
                outputs = {}
                for attr in dir(info):
                    if attr.startswith('__'):
                        continue
                    elif attr == 'transcription_options':
                        sub_dict = {}
                        transcription_options = info.__getattribute__(attr)
                        for sub_attr in dir(transcription_options):
                            if sub_attr.startswith('__'):
                                continue
                            sub_dict[sub_attr] = transcription_options.__getattribute__(sub_attr)
                        outputs[attr] = sub_dict
                    else:
                        outputs[attr] = info.__getattribute__(attr)
                if textgrid_path is not None:
                    write_textgrid_fill_utterances(textgrid_path, formatted_outputs['segment_texts'])
            self.write_outputs(outputs, formatted_outputs, fname)
            print('\tDone.')
        
        print(f'Transcribed {len(paths)} files.\n')

        return self