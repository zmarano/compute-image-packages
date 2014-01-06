#! /usr/bin/python
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A simple start up script to set up the system boto.cfg file.

This will hit the metadata server to get the appropriate project id
and install the compute authenication plugin.

Note that this starts with whatever is in /etc/boto.cfg.template, adds
to that and then persists it into /etc/boto.cfg.  This is done so that
the system boto.cfg can be removed prior to image packaging.
"""

from ConfigParser import SafeConfigParser
import os
import sys
import textwrap
import urllib2

NUMERIC_PROJECT_ID_URL=('http://metadata.google.internal/'
                        'computeMetadata/v1/project/numeric-project-id')
SYSTEM_BOTO_CONFIG_TEMPLATE='/etc/boto.cfg.template'
SYSTEM_BOTO_CONFIG='/etc/boto.cfg'
AUTH_PLUGIN_DIR='/usr/share/google/boto/boto_plugins'


def GetNumericProjectId():
  """Get the numeric project ID for this VM."""
  try:
    request = urllib2.Request(NUMERIC_PROJECT_ID_URL)
    request.add_unredirected_header('X-Google-Metadata-Request', 'True')
    return urllib2.urlopen(request).read()
  except (urllib2.URLError, urllib2.HTTPError, IOError), e:
    return None


def AddConfigFileHeader(fp):
  s = ("""\
    This file is automatically created at boot time by the %s script.
    Do not edit this file directly.  If you need to add items to this
    file, create/edit %s instead and then re-run the script."""
       % (os.path.abspath(__file__), SYSTEM_BOTO_CONFIG_TEMPLATE))
  fp.write('\n'.join(['# ' + s for s in textwrap.wrap(textwrap.dedent(s),
                                                      break_on_hyphens=False)]))
  fp.write('\n\n')


def main(argv):
  config = SafeConfigParser()
  config.read(SYSTEM_BOTO_CONFIG_TEMPLATE)

  # TODO(user): Figure out if we need a retry here.
  project_id = GetNumericProjectId()
  if not project_id:
    # Our project doesn't support service accounts.
    return

  if not config.has_section('GSUtil'):
    config.add_section('GSUtil')
  config.set('GSUtil', 'default_project_id', project_id)
  config.set('GSUtil', 'default_api_version', '2')

  if not config.has_section('GoogleCompute'):
    config.add_section('GoogleCompute')
  # TODO(user): Plumb a metadata value to set this.  We probably want
  # to namespace the metadata values in some way like
  # 'boto_auth.servicee_account'.
  config.set('GoogleCompute', 'service_account', 'default')

  if not config.has_section('Plugin'):
    config.add_section('Plugin')
  config.set('Plugin', 'plugin_directory', AUTH_PLUGIN_DIR)

  with open(SYSTEM_BOTO_CONFIG, 'w') as configfile:
    AddConfigFileHeader(configfile)
    config.write(configfile)


if __name__ == '__main__':
  main(sys.argv[1:])
