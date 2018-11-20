FlexGet Remux
=============

Flexget Remux allows for remuxing supported media files into a Matroksa file (mkv). 
Currently supports remuxing subtitles tracks.

Example
=======

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
=======

| Name  | Info | Description |
| ------------- | --------- | --------- |
| subtitles  | keep|remove|dict  | |


Subitle options
===============


Requirements
============

- [FlexGet](https://github.com/Flexget/Flexget)
- [MKVToolNix](https://mkvtoolnix.download)