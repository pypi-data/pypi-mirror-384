#MIT License
#
#Copyright (c) [2024] Lukas Walker
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

'''
``General information:``\n
This package is meant to program small webapps real quick without much required knowledge
docmentation can be found on <https://bbwebservice.eu>
'''

import os
import sys


default_config = '''
{
    "max_threads": 100,
    "max_header_size": 16384,
    "max_body_size": 10485760,
    "server": [
        {
            "ip": "default",
            "port": 5000,
            "queue_size": 10,
            "max_threads": 100,
            "SSL": false,
            "host": "",
            "cert_path": "",
            "key_path": "",
            "https-redirect": false,
            "https-redirect-escape-paths": [],
            "update-cert-state": false
        }
    ]
}
'''


MAIN_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
if not os.path.exists(MAIN_PATH + "/content"):
    os.makedirs(MAIN_PATH + "/content")
if not os.path.exists(MAIN_PATH + "/config"):
    os.makedirs(MAIN_PATH + "/config")
if not os.path.exists(MAIN_PATH + "/config/config.json"):
    with open(MAIN_PATH + "/config/config.json", 'w') as config:
        config.writelines(str(default_config))
