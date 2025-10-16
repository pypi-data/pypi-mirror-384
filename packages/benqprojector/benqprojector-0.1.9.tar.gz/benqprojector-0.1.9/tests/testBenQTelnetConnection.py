# pylint: disable=R0801
# pylint: disable=invalid-name
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
"""
Created on 27 Nov 2022

@author: Rogier van Staveren
"""

import logging
import unittest

from benqprojector.benqconnection import BenQTelnetConnection

logger = logging.getLogger(__name__)

HOSTNAME = "benqprojector-livingroom.local"


class Test(unittest.IsolatedAsyncioTestCase):
    _connection = None

    async def asyncSetUp(self):
        self._connection = BenQTelnetConnection(HOSTNAME)

    async def asyncTearDown(self):
        await self._connection.close()

    async def test_open(self):
        result = await self._connection.open()
        self.assertTrue(result)
        self.assertTrue(self._connection.is_open())

    async def test_close(self):
        await self._connection.open()
        result = await self._connection.close()
        self.assertTrue(result)
        self.assertFalse(self._connection.is_open())

    async def test_read(self):
        await self._connection.open()
        await self._connection.write(b"\r")
        result = await self._connection.read(1)
        logger.debug(result)
        self.assertIsNotNone(result)

    async def test_readline(self):
        await self._connection.open()
        await self._connection.write(b"\r")
        result = await self._connection.readline()
        logger.debug(result)
        self.assertIsNotNone(result)

    async def test_write(self):
        await self._connection.open()
        await self._connection.write(b"\r*pow=?#\r")
        await self._connection.readline()
        result = await self._connection.readline()
        self.assertTrue(result.startswith(b"*POW="))
