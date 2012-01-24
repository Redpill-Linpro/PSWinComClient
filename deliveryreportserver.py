#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Redpill Linpro AS
# Author(s): Rune Hansen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

##
# Running:
#
# Requires Cherrypy 3.x
#
# Hosted behind Nginx proxy
#
# Start the server in prod using the shell script cherryd
#
# $ cherryd -d -p /path/to/pid/file.pid -i /path/to/deliveryreportserver
#
# Start the server in dev using
#
# $ python deliveryreportserver.py
##

import cherrypy
import sqlite3
import datetime
from json import dumps

__author__ = "Rune Hansen"
__copyright__ = "Copyright 2012, Redpill Linpro AS"
__credits__ = []
__license__ = "GPL3"
__version__ = "1.0.0"
__maintainer__ = "Rune Hansen"
__email__ = "rune.hansen@redpill-linpro.com"
__status__ = "Production"

config = {
    'global':
    {
        'server.socket_port': 8080,
    },
    '/':
    {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.trailing_slash.on': False,
    },
    'Database':
    {
    'db':'/home/sms-karmoy/python/db/deliveryreport.db'
    },
}


##
# DB Connection
##

def initdb():
    sql='''create table if not exists deliveryreport (state text,
    ref int ,
    reciever text,
    time datetime);'''
    conn=sqlite3.connect(config['Database']['db'])
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
    c.execute('CREATE INDEX if not exists main.refindex on deliveryreport (ref);')
    conn.commit()
    conn.close()
initdb()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect(thread_index):
    conn = sqlite3.connect(config['Database']['db'])
    conn.row_factory = dict_factory
    cherrypy.thread_data.db = conn
cherrypy.engine.subscribe('start_thread', connect)

##
# End
##

@cherrypy.expose
def index():
    cherrypy.response.headers['Content-Type']='text/plain'
    return "Redpill Linpro SMS Delivery Report Server"

class DeliveryReport():
    """Method dispatching server for HTTP communication from PSWinCom

    POST method kwargs is a dictionary with the following keys:

    Delivered state:
    {'STATE': u'DELIVRD',
     'REF': u'288803343',
     'RCV': u'4792810913',
     'ID': u'1',
     'DELIVERYTIME': u'2012.01.04 14:13:50'}

    Undelivered state:
    {'STATE': u'UNDELIV',
     'REF': u'288811300',
     'RCV': u'792810913',
     'ID': u'1',
     'DELIVERYTIME': u'2012.01.04 13:16:29'}

     The REF key contains the same reference as given by the pswincom client on
     successfull gateway delivery.
    """
    exposed = True

    def GET(self, ref=None):
        """ """
        if ref:
            try:
                cur = cherrypy.thread_data.db.cursor()
                cur.execute("SELECT * FROM deliveryreport WHERE ref={0}".format(ref))
                res = cur.fetchone()
                cur.close()
                if res:
                    cherrypy.response.headers['Content-Type']='application/json'
                    return dumps(res)
            except Exception as e:
                cherrypy.response.headers['Content-Type']='text/plain'
                return
        else:
            cherrypy.response.headers['Content-Type']='text/plain'
            return

    def POST(self, *args, **kwargs):
        try:
            conn = cherrypy.thread_data.db
            sql = "INSERT INTO deliveryreport VALUES('{0}','{1}','{2}','{3}')"
            with conn:
                conn.execute(sql.format(str(kwargs['STATE']),
                                        int(kwargs['REF']),
                                        str(kwargs['RCV']),
                                        datetime.datetime.strptime(kwargs['DELIVERYTIME'],
                                                                   '%Y.%m.%d %H:%M:%S')))
        except Exception as e:
            """Must always return 200 OK"""
            pass
        cherrypy.response.headers['Content-Type']='text/plain'
        return

cherrypy.tree.mount(DeliveryReport(), "/deliveryreport", config=config)
cherrypy.tree.mount(index, "/", config={'/':{'tools.trailing_slash.on':True,}})

if __name__ == "__main__":
    if hasattr(cherrypy.engine, 'block'):
        #<3.1
        cherrypy.engine.start()
        cherrypy.engine.block()
    else:
        #>=3.0
        cherrypy.server.quickstart()
        cherrypy.engine.start()
