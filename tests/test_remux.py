from __future__ import unicode_literals, division, absolute_import
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

import os
import shutil

import pytest

from remux.remux import Remux
from flexget.tests.conftest import *

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))
FILES_ORG_PATH = os.path.join(LOCAL_PATH, 'files/org')
FILES_REMUX_PATH = os.path.join(LOCAL_PATH, 'files/testdir')

@pytest.fixture
def setup_files(request):
  files = [
    os.path.join(FILES_ORG_PATH, 'test.mkv')
  ]

  shutil.rmtree(FILES_REMUX_PATH, ignore_errors=True)
  os.makedirs(FILES_REMUX_PATH)

  for file in files:
    shutil.copy2(file, FILES_REMUX_PATH)


@pytest.mark.usefixtures("setup_files")
class TestRemuxSubtitles(object):
  org_file = os.path.join(FILES_ORG_PATH, 'test.mkv')
  test_file = os.path.join(FILES_REMUX_PATH, 'test.mkv')
  remuxed_file = os.path.join(FILES_REMUX_PATH, 'test-remuxed.mkv')

  config = """
      tasks:
        test_mixed:
          accept_all: yes
          mock:
            - {title: 'test.mkv', 'location': '""" + test_file + """'}
          remux:
            subtitles:                  # 'keep' | 'remove' | dict of options
              languages:                # allowed languages
               - dut
               - jpn
               - und
              formats:                  # allowed formats
               - S_TEXT/UTF8
        test_keep:
          accept_all: yes
          mock:
            - {title: 'test.mkv', 'location': '""" + test_file + """'}
          remux:
            subtitles: keep
        test_remove:
          accept_all: yes
          mock:
            - {title: 'test.mkv', 'location': '""" + test_file + """'}
          remux:
            subtitles: remove
        test_formats_text_only:
          accept_all: yes
          mock:
            - {title: 'test.mkv', 'location': '""" + test_file + """'}
          remux:
            subtitles:
              formats: text_only
        test_formats_image_only:
          accept_all: yes
          mock:
            - {title: 'test.mkv', 'location': '""" + test_file + """'}
          remux:
            subtitles:
              formats: image_only
        test_formats_list:
          accept_all: yes
          mock:
            - {title: 'test.mkv', 'location': '""" + test_file + """'}
          remux:
            subtitles:
              formats:
               - S_HDMV/PGS
        test_languages:
          accept_all: yes
          mock:
            - {title: 'test.mkv', 'location': '""" + test_file + """'}
          remux:
            subtitles:
              languages:
               - dut
               - jpn
               - ger
  """

  def test_keep(self, execute_task):
    """ Make sure nothing changed """
    execute_task('test_keep')

    ct_org = Remux().identify_file(self.org_file)
    ct_remux = Remux().identify_file(self.remuxed_file)
    assert ct_remux['tracks'] == ct_org['tracks']

  def test_remove(self, execute_task):
    """ Test if all subtitles are removed """
    execute_task('test_remove')

    ct_remux = Remux().identify_file(self.remuxed_file)
    tracks_remux = Remux().filter_tracks(ct_remux['tracks'], 'type', ['subtitles'])
    assert len(tracks_remux) == 0

  def test_formats_text_only(self, execute_task):
    execute_task('test_formats_text_only')

    ct_remux = Remux().identify_file(self.remuxed_file)
    tracks_remux = Remux().filter_tracks(ct_remux['tracks'], 'type', ['subtitles'])
    assert len(tracks_remux) == 8

    for track in tracks_remux:
      assert track['properties'].get('text_subtitles') == True

  def test_formats_image_only(self, execute_task):
    execute_task('test_formats_image_only')

    ct_remux = Remux().identify_file(self.remuxed_file)
    tracks_remux = Remux().filter_tracks(ct_remux['tracks'], 'type', ['subtitles'])
    assert len(tracks_remux) == 1

    for track in tracks_remux:
      assert 'text_subtitles' not in track['properties']

  def test_languages(self, execute_task):
    execute_task('test_languages')

    ct_remux = Remux().identify_file(self.remuxed_file)
    tracks_remux = Remux().filter_tracks(ct_remux['tracks'], 'type', ['subtitles'])
    assert len(tracks_remux) == 3

    expected = ['dut', 'jpn', 'ger']
    for track in tracks_remux:
      assert track['properties']['language'] in expected

  def test_mixed(self, execute_task):
    execute_task('test_mixed')

    ct_remux = Remux().identify_file(self.remuxed_file)
    tracks_remux = Remux().filter_tracks(ct_remux['tracks'], 'type', ['subtitles'])
    assert len(tracks_remux) == 2

    expected = ['jpn', 'und']
    for track in tracks_remux:
      assert track['properties']['language'] in expected
