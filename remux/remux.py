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
from flexget.utils.template import render_from_entry, RenderError

log = logging.getLogger('remux')

# See http://matroska-org.github.io/matroska-specification/codec_specs.html for codec mappings

def default_config(f):
    def wrapper(*args):
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

    dst_name = entry.get('location')
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
    # TODO: Add identify_file mocking
    # TODO: Set meta on entry for reuse?
    # TODO: Allow remuxing if there are no track changes but source is not an mkv
    # TODO: change entry location/title for further processing
    if not task.accepted:
      log.debug('nothing accepted, aborting')
      return

    if config['subtitles'] == 'keep':
      log.debug('nothing to remux, aborting')
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
      remove_all = True if config['subtitles'] == 'remove' else False

      if not remove_all:
        languages = config['subtitles'].get('languages', {})
        formats = config['subtitles'].get('formats', {})

        if not languages and not formats:
          log.debug('Nothing to remux')
          return

        # get current subtitle tracks
        sub_tracks = self.filter_tracks(file_info['tracks'], 'type', ['subtitles'])
        sub_tracks_count = len(sub_tracks)
        sub_tracks = self.filter_subtitle_tracks(
          tracks=sub_tracks,
          languages=languages,
          formats=formats
        )

        if sub_tracks_count == len(sub_tracks):
          log.debug('Nothing to remux')
          return
      else:
        if len(self.filter_tracks(file_info['tracks'], 'type', ['subtitles'])) == 0:
          log.debug('Nothing to remux')
          return

      dst = get_destination('', entry['title'] + '.remux', entry)

      # remux file
      self.remux(
        src=entry['location'],
        dst=dst,
        tracks=sub_tracks
      )

      # cleanup
      backup_dst = get_destination('', entry['title'] + '.backup', entry)
      shutil.move(entry['location'], backup_dst)
      shutil.move(dst, entry['location'])
      os.remove(backup_dst)

      log.debug('Succesfully remuxed: %s', entry['location'])

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
    return json.loads(output)

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
