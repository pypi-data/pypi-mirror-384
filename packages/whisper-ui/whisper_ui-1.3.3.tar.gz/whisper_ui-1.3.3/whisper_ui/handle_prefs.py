import os
import json
from pathlib import Path

from whisper.tokenizer import LANGUAGES, TO_LANGUAGE_CODE
from faster_whisper.utils import _MODELS

USER_PREFS = json.load(
    open(
        os.path.abspath(os.path.join(os.path.dirname(__file__), 'user_prefs.json')),
         'r',
         encoding='utf-8'
    )
)

AVAILABLE_LANGUAGES = ['None'] + sorted(list(set(
    [x.title() for x in LANGUAGES.values()] +
    [x.title() for x in TO_LANGUAGE_CODE.keys()]
)))

def check_model(model_name):
    path = os.path.join(
        Path(os.getenv('HF_HOME', Path.home() / '.cache' / 'huggingface')) / 'hub',
        'models--' + _MODELS[model_name].replace(os.path.sep, '--')
    )
    return os.path.exists(
        path
    )

def check_warn(pref_name: str, template_name: str, content: str):
    pref_name += '_insertion_symbol'
    template_name += '_template'
    output_name = template_name.split('_')[0]
    pref = USER_PREFS[pref_name]
    template = USER_PREFS[template_name]
    if pref not in template:
        msg = f'Warning: {pref_name} "{pref}" is not found in {template_name} "{template}". '
        msg += f'Output {output_name} files will not contain the {content}.'
        print(msg)

def validate(option: str):
    
    if option == 'output_dir':
        t = USER_PREFS['output_dir']
        if not os.path.exists(t):
            msg = f'Warning: "output_dir" is set to "{t}" which does not exist.\n'
            msg += 'This directory will be created upon running transcription.'
            print(msg)
            
    elif option in ('model', 'language'):
        if option == 'model':
            t = USER_PREFS['model']
            if not check_model(t):
                msg = f'Warning: "model" is set to "{t}" which has not been downloaded.\n'
                msg += 'You must navigate to "Download models" and download this model first.'
                print(msg)
        m, l = USER_PREFS['model'], USER_PREFS['language']
        if '.en' in m and l not in ('None', 'English'):
            msg = f'Warning: "model" is set to "{m}" which is English-only, '
            msg += f'but "language" is set to {l}.\n'
            msg += 'Whisper will assume all audio is English for this model selection.'
            print(msg)
        if '.en' in m and l == 'None':
            msg = f'Warning: language detection is not available for English-only models.\n'
            msg += 'Whisper will assume all audio is English for this model selection.'
            print(msg)
        # assert l in AVAILABLE_LANGUAGES # TODO remove
    
    elif option in ('text_template', 'text_insertion_symbol'):
        check_warn('text', 'text', 'transcribed text')
    elif option in ('segmentation_template', 'segment_insertion_symbol', 'start_time_insertion_symbol', 'end_time_insertion_symbol'):
        check_warn('segment', 'segmentation', 'segmented text')
        check_warn('start_time', 'segmentation', 'segment start times')
        check_warn('end_time', 'segmentation', 'segment end times')
    
def set_option(option: str, new_value, run_validate=True):
    
    if option not in USER_PREFS:
        raise ValueError(f'Invalid option: {option}.')
    
    old_value = USER_PREFS[option]
    
    try:
        USER_PREFS[option] = new_value
        if run_validate:
            validate(option)
    except AssertionError as e:
        USER_PREFS[option] = old_value
        print(f'Warning: failed to update option {option} to {new_value}. Reason:')
        print(e + '\n')
    
    json.dump(
        USER_PREFS,
        open(
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'user_prefs.json')),
            'w+',
            encoding='utf-8'
        ),
        indent=4
    )
    
    # msg = f'Updated "{option}" to "{new_value}". Saved successfully.\n'
    
if __name__ == "__main__":
    for pref in USER_PREFS:
        validate(pref)