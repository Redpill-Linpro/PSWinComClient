#! /usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pswinclient import EnvelopeBuilder, SendSingleMessage

class  TestEnvelopeBuilder(unittest.TestCase):
    def setUp(self):
        self.sms = EnvelopeBuilder(SendSingleMessage,
                                   'kalle',
                                   'pelle',
                                   multi=False)

        self.args = {'reciever':'4722334455',
                     'sender':'pswinclient',
                     'message':u'test message',
                     'reciept':'false'}
        
    def  test__init__(self):
        # EnvelopeBuilder takes three arguments
        assert(EnvelopeBuilder(SendSingleMessage,
                               'kalle',
                               'pelle'))

        # Raise a TypeError when called with fewer arguments
        with self.assertRaises(TypeError):
            EnvelopeBuilder()

        # Is sms a instance of EnvelopeBuilder?
        self.assertIsInstance(self.sms,
                              EnvelopeBuilder)

    def test_multi_get(self):
        # Initial value of multi is false
        self.assertFalse(self.sms.multi)

        # We will cheat and set multi to True
        self.sms._multi = True

        # Now multi should be True
        self.assertTrue(self.sms.multi)
        
    def test_multi_set(self):
        # Setting the property should raise an
        # AttributeError
        with self.assertRaises(AttributeError):
            self.sms.multi = True

    def test_buildxml(self):
        # Raise a KeyError when calling buildxml
        # with an empty dict
        with self.assertRaises(KeyError):
            self.sms.buildxml(dict())

        # Raise a TypeError when calling buildxml
        # with a string
        with self.assertRaises(TypeError):
            self.sms.buildxml("")

    def test_xml(self):
        # Raise a KeyError when setting property xml to
        # an empty dict
        with self.assertRaises(KeyError):
            self.sms.xml = dict()

        # Rase a TypeError when setting property xml to
        # a string
        with self.assertRaises(TypeError):
            self.sms.xml = ""

        # Raise no error when setting propertu xml to
        # a valid dict
        self.sms.xml = self.args

        from xml.etree import ElementTree as et

        # Retrive the value of xml and parse it for validity
        doc = et.fromstring(self.sms.xml)
        self.assertIsInstance(doc, et.Element)

        # Retrive the xml property and make sure delete was called
        # to remove the message structure. In this case we need to
        # normalize the xml strings for comparison.
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
