#! /usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pswinclient import EnvelopeBuilder, SendSingleMessage

class  TestEnvelopeBuilder(unittest.TestCase):
    def setUp(self):
        self.sms = EnvelopeBuilder(SendSingleMessage,
                                   'kalle',
                                   'pelle')

        self.args = {'reciever':'4722334455',
                     'sender':'pswinclient',
                     'message':u'test message',
                     'reciept':'false'}
        
    def  test__init__(self):
        assert(EnvelopeBuilder(SendSingleMessage,
                               'kalle',
                               'pelle'))

        with self.assertRaises(TypeError):
            EnvelopeBuilder()

        self.assertIsInstance(self.sms,
                              EnvelopeBuilder)

    def test_multi_get(self):
        self.assertFalse(self.sms.multi)

    def test_multi_set(self):
        with self.assertRaises(AttributeError):
            self.sms.multi = True

    def test_buildxml(self):
        with self.assertRaises(KeyError):
            self.sms.buildxml(dict())

        with self.assertRaises(TypeError):
            self.sms.buildxml("")

    def test_xml(self):
        with self.assertRaises(KeyError):
            self.sms.xml = dict()

        with self.assertRaises(TypeError):
            self.sms.xml = ""

        self.sms.xml = self.args

        from xml.etree import ElementTree as et
        doc = et.fromstring(self.sms.xml)
        self.assertIsInstance(doc, et.Element)

        expected_inn = et.fromstring(u'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <SendSingleMessage xmlns="http://pswin.com/SOAP/Submit/SMS">
      <username>kalle</username>
      <password>pelle</password>
      <m>
        
      </m>
    </SendSingleMessage>
  </soap12:Body>
</soap12:Envelope>''')
        expected = et.tostring(expected_inn)
        result_inn = et.fromstring(self.sms.xml)
        result = et.tostring(result_inn)
        self.assertEqual(expected, result)

if __name__ == "__main__":
    unittest.main()
