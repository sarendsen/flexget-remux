from __future__ import unicode_literals, division, absolute_import

import logging
#from subprocess import Popen, PIPE, STDOUT
import subprocess
import json
import os
import tempfile
import shutil

from flexget import plugin
from flexget.event import event
from flexget.utils.template import *

log = logging.getLogger('remux')

# See http://matroska-org.github.io/matroska-specification/codec_specs.html for codec mappings

def default_config(f):
    def wrapper(*args):
      if 'keep_original' not in args[2]:
        args[2]['keep_original'] = False
      if 'subtitles' not in args[2]:
        args[2]['subtitles'] = 'keep'

      return f(*args)
    return wrapper


def get_destination(to, rename, entry):
    try:
        if to:
            dst = render_from_entry(to, entry)
        else:
            dst = os.path.dirname(entry.get('location'))
    except RenderError:
        raise plugin.PluginError('Could not render path: %s' % to)

    dst_name = entry.get('title')
    if rename:
      dst_name = entry.render(rename)

    return os.path.join(dst, dst_name)


class Remux(object):
  """
  Remux a support media file.

  - Removing subtitles based on language or format.

  """

  schema = {
    'type': 'object',
    'properties': {
      'languages': {
        'oneOf': [
            {'type': 'string', 'default': 'all'},
            {'type': 'array', 'items': {'type': 'string'}}
        ]
      }
    }
  }

  @default_config
  def on_task_output(self, task, config):
    # TODO: Check if dst file already exists
    # TODO: Allow remuxing if there are no track changes but source is not an mkv
    if not task.accepted:
      log.debug('nothing accepted, aborting')
      return

    for entry in task.accepted:
      if not 'location' in entry:
        log.debug('no file location specified, aborting')
        return

      file_info = self.identify_file(entry['location'])

      if not file_info['container']['supported']:
        log.debug('unsupported file, aborting')
        return

      # subtitles
      sub_tracks = {}
      languages = {}
      formats = {}
      remove_all = True if config['subtitles'] == 'remove' else False
      keep_all = True if config['subtitles'] == 'keep' else False

      if not remove_all:
        if not keep_all:
          languages = config['subtitles'].get('languages', {})
          formats = config['subtitles'].get('formats', {})

        # get current subtitle tracks
        sub_tracks = self.filter_tracks(file_info['tracks'], 'type', ['subtitles'])
        sub_tracks = self.filter_subtitle_tracks(
          tracks=sub_tracks,
          languages=languages,
          formats=formats
        )

      src = entry['location']
      file_name = filter_pathname(src)
      file_ext = filter_pathext(src)
      file_dir = filter_pathdir(src)
      dst = os.path.join(file_dir, file_name + '-remuxed.mkv')

      # remux file
      try:
        self.remux(
          src=src,
          dst=dst,
          tracks=sub_tracks
        )
      except Exception as e:
        shutil.move(src, entry['location'])
        raise e

      if not config['keep_original']:
        os.remove(src)
      else:
        entry['location_original'] = src

      # set to entry
      entry['location'] = dst
      entry['title'] = filter_pathbase(dst)

      log.debug('Succesfully remuxed: %s to: %s', src, dst)

  def filter_subtitle_tracks(self, tracks, languages, formats):
    """
    Filter subtitle tracks on given paramaters.
    """

    # filter on formats
    if isinstance(formats, list):
      tracks = self.filter_tracks(tracks, 'properties.codec_id', [f.upper() for f in formats])
    elif formats == 'text_only':
      tracks = self.filter_tracks(tracks, 'properties.text_subtitles', [True])
    elif formats == 'image_only':
      tracks = self.filter_tracks(tracks, 'properties.text_subtitles', [False])

    # filter on languages
    if languages:
      tracks = self.filter_tracks(tracks, 'properties.language', [f.lower() for f in languages])

    return tracks

  def identify_file(self, location):
    command = [
        'mkvmerge',
        '-J',
        location
    ]
    log.debug('Identifying %s', location)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, err = p.communicate()
    data = json.loads(output)

    if data['errors']:
      raise Exception(data['errors'])

    return data

  def remux(self, src, dst, tracks):
    command = ['mkvmerge', '-o', dst]

    if not tracks:
      command += ['--no-subtitles']
    else:
      command += [
        '--subtitle-tracks', ','.join([str(track['id']) for track in tracks])
      ]

    command += [src]

    log.debug('Remuxing with command: %s', ' '.join(command))
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, err = p.communicate()

    # bad error handling. Check if out file is present. If not, raise an error
    if not os.path.isfile(dst):
      log.debug('%s', output)
      raise Exception("Something went wrong during remuxing. Output file is missing")

  def filter_tracks(self, tracks, key, value):
    def drill(x, key, value):
      keys = key.split('.')
      for k in keys:
        x = x.get(k, False)
      return x

    return list(filter(lambda x: drill(x, key, value) in value, tracks))


@event('plugin.register')
def register_plugin():
  plugin.register(Remux, 'remux', api_ver=2)
