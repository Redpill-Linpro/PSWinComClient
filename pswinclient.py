#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Karmoy SMS - A simple SMS gateway client

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

import httplib
from xml.etree import ElementTree as ET


__author__ = "Rune Hansen"
__copyright__ = "Copyright 2012, Redpill Linpro AS"
__credits__ = ["Torbjorn Maro","https://github.com/tormaroe/pswinpy","pswin.com"]
__license__ = "GPL3"
__version__ = "1.0.2"
__maintainer__ = "Rune Hansen"
__email__ = "rune.hansen@redpill-linpro.com"
__status__ = "Production"

##
# Ref: http://sms.pswin.com/SOAP/SMS.asmx?op=SendSingleMessage
# Template for sending a single SMS message
##

SendSingleMessage =  u'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <SendSingleMessage xmlns="http://pswin.com/SOAP/Submit/SMS">
      <username>{username}</username>
      <password>{password}</password>
      <m>
        {SMSMessage}
      </m>
    </SendSingleMessage>
  </soap12:Body>
</soap12:Envelope>
'''

##
# Ref: http://sms.pswin.com/SOAP/SMS.asmx?op=SendMessages
# Template for sending multiple SMS messages
##

SendMessages = u'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <SendMessages xmlns="http://pswin.com/SOAP/Submit/SMS">
      <username>{username}</username>
      <password>{password}</password>
      <m>
      {SMSMessage}
      </m>
    </SendMessages>
  </soap12:Body>
</soap12:Envelope>
'''

SendMessagesContainer = u'''<SMSMessage>
          {SMSMessage}
        </SMSMessage>'''

##
# Ref: http://wiki.pswin.com/SMSMessage-SOAP.ashx
# Template for the SMS message container
##

SMSMessage = u'''<ReceiverNumber>{reciever}</ReceiverNumber>
        <SenderNumber>{sender}</SenderNumber>
        <Text>{message}</Text>
        <Network></Network>
        <TypeOfMessage>Text</TypeOfMessage>
        <Tariff>0</Tariff>
        <TimeToLive>0</TimeToLive>
        <CPATag></CPATag>
        <RequestReceipt>{reciept}</RequestReceipt>
        <SessionData></SessionData>
        <AffiliateProgram></AffiliateProgram>
        <DeliveryTime></DeliveryTime>
        <ServiceCode></ServiceCode>'''

class EnvelopeBuilder(object):
    """Create a soap:Envelope"""
    smsmessage = SMSMessage
    messagecontainer = SendMessagesContainer

    def __init__(self, template, username, password, multi=False):
        self.tpl = template.format(username=username,
                                   password=password,
                                   SMSMessage="{SMSMessage}").encode('utf-8')

        self._multi = multi
        self._xml = []

    @property
    def multi(self):
        return self._multi

    def buildxml(self, kwargs):
        """Legacy API"""
        self.xml = kwargs

    @property
    def xml(self):
        try:
            return "".join(self.tpl.format(SMSMessage="\n".join(self._xml).encode('utf-8')))
        finally:
            del self.xml

    @xml.setter
    def xml(self, kwargs):
        _msg = self.smsmessage.format(**kwargs)
        if self.multi:
            _msg = self.messagecontainer.format(SMSMessage=_msg).encode('utf-8')
            self._xml.append(_msg)
        else:
            self._xml = [_msg]

    @xml.deleter
    def xml(self):
        self._xml = []

class SOAPClient(object):
    """Sets up SOAP communication"""

    def __init__(self, host, path, msg, agent="RL-PythonPSWinComSOAP"):
        """Initialize communication

        keyword arguments:
        host -- your.soap.host
        path -- /path/to/SOAP/handler
        msg -- <soapxx:Envelope>..</soap>
        agent -- Useragent string
        """
        self.host = host
        self.path = path
        self.msg = msg.xml
        self.agent = agent
        self.msg_type = 'single' if not msg.multi else 'multi'
        self.__set_headers()

    def __set_headers(self):
        self.webservice = httplib.HTTP(self.host)
        self.webservice.putrequest("POST", self.path)
        self.webservice.putheader("Host", self.host)
        self.webservice.putheader("User-Agent", self.agent)
        self.webservice.putheader("Content-type", "application/soap+xml;\
        charset=\"utf-8\"")
        self.webservice.putheader("Content-length", "%d" % len(self.msg))
        self.webservice.putheader("SOAPAction", "\"\"")
        self.webservice.endheaders()

    def send(self):
        self.webservice.send(self.msg)
        statuscode, statusmessage, header = self.webservice.getreply()
        envelope_response = getattr(self, "_"+self.msg_type+"_soapenvelope")()
        return (statuscode, envelope_response)

    def _single_soapenvelope(self):
        res = self.webservice.getfile().read()
        res_soapenv = ET.fromstring(res)
        code = res_soapenv.find('*//{http://pswin.com/SOAP/Submit/SMS}Code')
        reference = res_soapenv.find('*//{http://pswin.com/SOAP/Submit/SMS}Reference')
        description = res_soapenv.find('*//{http://pswin.com/SOAP/Submit/SMS}Description')
        return [(code.text, reference.text, description.text)]

    def _multi_soapenvelope(self):
        res = self.webservice.getfile().read()
        res_soapenv = ET.fromstring(res)
        results = res_soapenv.findall('*//{http://pswin.com/SOAP/Submit/SMS}ReturnValue')
        result_list = []
        for item in results:
            for i in item.iter():
                if "Code" in i.tag:
                    _code = i.text
                if "Reference" in i.tag:
                    _reference = i.text
                if "Description" in i.tag:
                    _description = i.text

            result_list.append((_code,_reference, _description))
        return result_list


def main(args):
    """One wonders"""
    sms_message = EnvelopeBuilder(SendSingleMessage, args.user,
                                  args.password)
    sms_message.buildxml(dict(reciever=args.number,
                              sender=args.reference_name,
                              message=u"{}".format(args.message),
                              reciept=str(args.reciept).lower()))

    if args.debug:
        from xml.etree import ElementTree as et
        doc  = et.fromstring(sms_message.xml)
        et.dump(doc)
        return(0,0)
    else:
        soap_client = SOAPClient('sms.pswin.com','/SOAP/SMS.asmx', sms_message)
        statuscode, envelope_response = soap_client.send()
        return(statuscode, envelope_response)

if __name__ == "__main__":
    """ API Usage:
    >>> sms_message = EnvelopeBuilder(SendSingleMessage,
                                      '<PSWinCom-username>',
                                      '<PSWinCom-Password>')
    >>> sms_message.buildxml(dict(reciever='47<phone number>'
                                  sender='<Your ref>',
                                  message=u'<Your message string>',
                                  reciept='false'))
    >>> soap_client = SOAPClient('sms.pswin.com','/SOAP/SMS.asmx',
                                  sms_message)
    statuscode, envelope_response = soap_client.send()
    """
    import argparse

    class LenAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if len(values) > 140:
                raise parser.error("Your message text is too long")
            setattr(namespace, self.dest, values)

    parser = argparse.ArgumentParser(prog="pswinclient",
                                     description="PSWinCom SMS CLI © Redpill Linpro AS 2012",
                                     epilog='''The CLI allows you to send a
                                     single SMS message to a single recipient.
                                     This does of course require a
                                     valid PSWinCom account.
                                     NB: Be aware that the
                                     PSWinCom SOAP API will return 200 OK no
                                     matter what you do. If you want to be
                                     sure that your message has been delivered
                                     you need to set "reciept" to True
                                     and fire up the deliveryreport server.
                                     The address of the deliveryreport server
                                     needs to be added through your PSWinCom
                                     administration web console.''')

    parser.add_argument("-u","--user",
                           dest="user",
                           required=True,
                           help="PSWinCom username")

    parser.add_argument("-p","--password",
                           dest="password",
                           required=True,
                           help="PSWinCom password")

    parser.add_argument("-r", "--recipient",
                           type=int,
                           dest="number",
                           required=True,
                           help="""Mobile phone number formatted as xx<number>
                           , where xx is the country number and <number> is
                           between 7 and 11""")

    parser.add_argument("-m","--message",
                           type=str,
                           action=LenAction,
                           dest="message",
                           required=True,
                           help="The message to send (max 140 characters)")

    parser.add_argument("-n", "--name",
                           dest="reference_name",
                           default=parser.prog+"/Redpill Linpro AS 2012",
                           help="Optional name used as your reference")

    parser.add_argument("--reciept",
                           dest="reciept",
                           action="store_true",
                           help="Send a reciept request to PSWinCom")

    parser.add_argument("--debug",
                           dest="debug",
                           action="store_true",
                           help="""Dump generated message to console without
                           sending""")

    args = parser.parse_args()

    status, response = main(args)

    print"""
---------------------------------------
{0!s:<20} {1}
---------------------------------------
{2!s:<20} {3}
---------------------------------------
---------------------------------------
    """.format("Status", "Reference", status, response)
