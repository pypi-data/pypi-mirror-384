# Whisper UI 1.3.0

A simple GUI to transcribe audio using OpenAI's Whisper models.

## Installation

### Mac

#### Python for Mac

Install Python 3.11.0 or higher. [Here is a direct link to an installer for 3.11.9](https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg).

To confirm that Python is installed, open a terminal window and run the following command:

```bash
python3 --version
```

#### FFmpeg for Mac

The simplest way to install `ffmpeg` is to use `brew`. You can install `brew` by running the following command in a terminal window:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Once this command finishes running, you can follow the instructions printed out in the terminal window to add `brew` to your path.

Then, you can install `ffmpeg` by running the following command:

```bash
brew install ffmpeg
```

You can confirm that `ffmpeg` is installed by running the following command:

```bash
ffmpeg -version
```

#### Whisper-UI for Mac

Download `Whisper_UI.command` from the link above (click on Download for Mac). I recommend placing the file in your Downloads folder for now.

Assuming you downloaded the file to your Downloads folder, open a terminal and enter:

```bash
chmod -R +x ~/Downloads/Whisper_UI.command
```

Once you have done this step, you can place this script wherever you like on your computer to access it easily. You can launch the program by double-clicking on this script. Expect it to take a bit of time to start up the first time you run it as it installs itself.

***NOTE:*** If Mac OS blocks you from running the script, open your System Settings. Go to "Security & Privacy", scroll down to the "Security" section, and click "Open Anyway" next to the message about the file being blocked. If you don't see this message, try restarting your computer and running the script again.

### Windows

#### Python for Windows

Install Python 3.11.0 or higher. [Here is a direct link to an installer for 3.11.9 if you have 64-bit Windows](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe). If you have 32 bit Windows, you can use [this link](https://www.python.org/ftp/python/3.11.9/python-3.11.9.exe). Be sure to check the box to add Python to your PATH when you run the installer, and to install any optional add-ons like `tcl`, `tk`, `tkinter`, and `pip` if you are given the option.

To confirm that Python is installed, open a terminal window and run the following command:

```bash
python --version
```

#### FFmpeg for Windows (credits to Jack Gagnon for documenting this process)

1. Run PowerShell as Administrator

    a. Type the Windows key and type "PowerShell" into the search bar.
    b. In the options of the top result, select "Run as Administrator."
    c. Press "Okay" to allow the app to make changes to your device.
    d. You should now get a terminal window titled "Administrator: Windows PowerShell" with the cursor on a line that reads:

    ```text
    PS C:\Windows\system32>
    ```

2. Install Chocolatey from PowerShell

    a. Copy and paste the following command and press `Enter`:

    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```

    b. The command will take a dozen or so seconds to complete. When it is done, you should see a new line with `PS C:\Windows\system32>` again.
    c. Type `choco` and press `Enter`. You should get the following feedback in green text.

    ```text
    Chocolatey v2.4.3
    Please run 'choco -?' or 'choco <command> -?' for help menu.
    ```

    d. If you encounter an error (like if you weren't in Admin mode) and want to try reinstalling by running the command in (a) again, first navigate in your File Explorer to This PC > Windows (C:) > ProgramData, and then, if you see a folder named `chocolatey`, delete it.

3. Install FFmpeg

    a. From the PowerShell, run the following command:

    ```powershell
    choco install ffmpeg
    ```

    b. To confirm that FFmpeg is installed, run:

    ```powershell
    ffmpeg -version
    ```

    c. If you get an error, try restarting your computer and running the command again.

#### Whisper-UI for Windows

Download `Whisper UI.cmd` from this repository (or click the download link for Windows). Place it wherever you like on your computer. You can launch the program by running this file. Expect it to take a bit of time to start up the first time you run it as it installs itself. If you get a pop-up about security, click "More info" and then "Run anyway."

## Interface

### Menu bar

#### File menu

- "Open file" - select an audio file from your computer to transcribe.
- "Open audio directory" - select a folder from your computer containing audio files to transcribe. Avoid choosing a directory containing non-audio files.
- "Choose output directory" - select a folder from your computer to write transcriptions to.

#### Download models

A list of available models can be viewed here. A checkmark indicates you have already downloaded the model, while a download symbol is shown otherwise. Simply click on a model to initiate the download process.

#### Debug

If the UI is glitching at all, try navigating here and clicking "Reload window."

### Console

Most of the window is occupied by the console, which will display information as you adjust settings and run transcription. The  "clear output" button at the bottom of the console can be used to erase all the information on screen.

### Controls

#### Input files

The first text box allows you to entire a Unix-style pathname pattern to find audio files you want to transcribe:

- You can enter an absolute or relative path to a file on your computer, or select multiple files by entering an asterisk (*) somewhere in the path. The asterisk can stand for (match) any folder or file name, and even partial folder and filenames. For instance, if you have a folder called `audio_files` which contains `sample1.mp3` and `sample2.mp3`, you can grab both of them at once by writing `audio_files/*.mp3` (or `audio_files/*` if there are no other files in the folder).
- You can fill this box by typing or by going to "File" > "Open file" or "File" > "Open audio directory."
- You can drag files onto the text box to fill it with their paths.

Once you have entered a path or paths, you can click "List files" to display a list of all files that were found.

If you are ready to transcribe, you can hit "Transcribe." Acceptable filetypes include: `.flac`, `.m4a`, `.mp3`, `.mp4`, and `.wav`.

#### Output files

The second textbox allows you to specify the folder where you want to put the transcripts. You can enter a path to any folder. If you enter a path to a folder that doesn't exist, that folder will be created. You can click "Set output directory" to confirm the existence of the chosen folder. You can fill this box by typing or by going to "File" > "Choose output directory."

The three checkboxes below the second textbox allow you to control which kinds of output you want.

- Check "Output plain transcript txt?" to get a plain `.txt` file containing the transcribed text.
- Check "Output segmentation file?" to get a `.seg` file showing the "segments" of your audio file (lengths of speech with breaks between them). By default, this file is a tab-separated values, with each line containing the speech occurring in a segment, the start time, and the end time.
- Check "Output full JSON output?" to get the full `.json` output of Whisper, which also includes a detected language code if no language is specified.

"Template formatting options..." allows you to modify the format of the plain `.txt` file and the way each line in the `.seg` file are formatted. If you modify these, be sure to click "Save" to save your choices.

##### Formatting the `.txt` output

- "Template for full transcript" allows you to decide how to format the transcript. By default, this field contains only the symbol `<<<TEXT>>>`.
- "Symbol to replace with full transcript" allows you to decide what symbol in the above template is replaced with the transcript.
- Example: If you want the transcript to be repeated a second time with an ellipsis between, you would enter `<<<TEXT>>>...<<<TEXT>>>` into the "Template for full transcript" field.

##### Formatting the `.seg` output

- "Template for each segment" allows you to decide how to format the lines of the `.seg` file. By default, this field contains the pattern `<<<SEG>>>\t<<<START>>>\t<<<END>>>`. This formatting will write the speech segment's text, then the start time, and finally the end time, with `tab` characters in between.
- "Symbol to replace with segment in each line" allows you to decide what symbol in the above template is replaced with a speech segment in each line of the `.seg` file.
- "Symbol to replace with start time in each line" works just like the segment symbol, but is replaced by the start time of the segment.
- "Symbol to replace with end time in each line" works just like the segment symbol, but is replaced by the end time of the segment.

#### Whisper options

"Currently selected Whisper model" displays the current model you are using. Any model having the `.en` suffix is a monolingual English model, and should not be used for other languages. All other models are multilingual. In general, models further down the list will be more accurate, but slower to run. They may also require more memory than your computer has. It is quite safe to attempt to use any model you like, but be advised that you may need to switch to a smaller one if a larger one fails.

"Currently selected Whisper language" displays the language Whisper will use to condition its output. You can set it to "NONE" if you prefer that Whisper automatically detect the spoken language. This may also be preferable for code-switched speech, but be advised that code-switched data in general is fairly hard to find in order to train speech models on it. As such, Whisper may handle code-switching rather poorly. Note that Whisper will generally struggle with low-resource languages.

Check "Translate to English?" if you would like the transcript of your non-English audio to be output in English. Note that Whisper will generally struggle to translate from low-resource languages.

Check "Use GPU?" if you would like to use hardware acceleration. This may be faster on a Windows or Linux machine with an NVIDIA GPU. For Macs, many things are not implemented on MPS (Mac GPU), so this probably won't work.

#### Using TextGrids

You can check this button to supply time alignments from a textgrid. WhisperUI assumes that your textgrid file is named identically to its corresponding audio file, except for the extension. For example, having both of the following files in your Downloads folder would work:

```bash
- my_audio_file.wav
- my_audio_file.textgrid
```

Supplying this information will yield the following:

```bash
- my_audio_file.wav
- my_audio_file.textgrid
- my_audio_file_blank.textgrid
```

Where `my_audio_file.textgrid` now contains words filled in for each silence. `my_audio_file_blank.textgrid` is the original textgrid with `'silent'` still written instead of words.

## Future updates

I plan to expand this project in the future to allow access to a curated collection of ASR models from HuggingFace, but this will take some time. [Other models on HF can be found here.](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard)

I encourage feedback and suggestions for improvement. Please feel free to open an issue on [the Issues page](https://github.com/dan-the-meme-man/whisper-ui/issues) if you have any ideas or problems, or send me an email at [drd92@georgetown.edu](mailto:drd92@georgetown.edu).
