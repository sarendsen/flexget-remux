FlexGet Remux
=============

[![CircleCI](https://circleci.com/gh/sarendsen/flexget-remux.svg?style=svg)](https://circleci.com/gh/sarendsen/flexget-remux)

Flexget Remux allows for remuxing supported media files into a Matroksa file (mkv). 
Currently supports remuxing subtitles tracks.

Example
-------

    tasks:
      remux_task
        filesystem:
          path: "{? movies_path ?}"
          recursive: yes
          retrieve: files
          regexp: '.*\.(avi|mkv|mp4)$'
        accept_all: yes
        remux:
          subtitles:
            languages:
             - dut
             - jpn
             - und
            formats:
             - S_TEXT/UTF8

Options
-------

| Option  | Info | Description |
| ------------- | --------- | --------- |
| keep_original  | true\|false | keep the original file or not \(default: false\) |
| subtitles  | keep\|remove\|dict | |


### Subtitles options

| Option  | Info | Description |
| ------------- | --------- | --------- |
| languages  | list  | List of language codes (ISO 639-2) to keep |
| formats  | image_only\|text_only\|list  | 'image_only' to keep bitmap/image based subtitles, 'text_only' for text based subtitles or a list of subtitle [format codes](http://matroska-org.github.io/matroska-specification/codec_specs.html ) to keep |


Requirements
------------

- [FlexGet](https://github.com/Flexget/Flexget)
- [MKVToolNix](https://mkvtoolnix.download)


Notes
------------

The entry will be replaced with the remux file name and location, and will have '-remuxed' appended to the filename.
Extra space is required for the remux file to be created. 
The original file will be automaticly deleted afterwards (if the option is not set to true).
