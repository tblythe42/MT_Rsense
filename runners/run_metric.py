# ===============================================================================
# Copyright 2017 dgketchum
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
# ===============================================================================
import os
from metric.metric_py import run
from weather.get_meteo import get_gridded_met_data


def run_metric(config, (path, row)):
    met = get_gridded_met_data()
    metric = run(config)


if __name__ == '__main__':
    home = os.path.expanduser('~')
    print 'home: {}'.format(home)
    configuration_file = os.path.join(home, 'images', 'configs', 'conf_test.txt')
    run_metric(configuration_file, ('036', '029'))
