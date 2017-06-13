from __future__ import unicode_literals, absolute_import

import datetime

from pytest import fixture, raises
from six import text_type

from openvpn_status.parser import LogParser, ParsingError


@fixture
def openvpn_status(datadir):
    return datadir.join('openvpn-status.txt')


@fixture
def broken_status(datadir):
    return datadir.join('broken-openvpn-status')


def test_parser(openvpn_status):
    parser = LogParser.fromstring(openvpn_status.read())
    status = parser.parse()

    assert len(status.client_list) == 3
    assert len(status.routing_table) == 3
    assert status.global_stats.max_bcast_mcast_queue_len == 0
    assert status.updated_at == datetime.datetime(2015, 6, 18, 8, 12, 15)

    client = status.client_list['foo@example.com']
    assert text_type(client.real_address) == '10.10.10.10'
    assert text_type(client.real_address.host) == '10.10.10.10'
    assert client.connected_since == datetime.datetime(2015, 6, 18, 4, 23, 3)
    assert client.bytes_received == 334948
    assert client.bytes_sent == 1973012


def test_parser_with_syntax_errors(broken_status):
    def catch_syntax_error(seq):
        datafile = broken_status.join('%d.txt' % seq)
        parser = LogParser.fromstring(datafile.read())
        with raises(ParsingError) as error:
            parser.parse()
        return error

    error = catch_syntax_error(0)
    assert not error.value.args[0].startswith('expected list')
    assert not error.value.args[0].startswith('expected 2-tuple')
    assert error.value.args[0].endswith('got end of input')

    error = catch_syntax_error(1)
    assert not error.value.args[0].startswith('expected list')
    assert not error.value.args[0].startswith('expected 2-tuple')
    assert error.value.args[0].endswith('got %r' % u'BrokenVPN CLIENT LIST')

    error = catch_syntax_error(2)
    assert error.value.args[0] == 'expected list but got end of input'

    error = catch_syntax_error(3)
    assert error.value.args[0] == 'expected 2-tuple but got end of input'

    error = catch_syntax_error(4)
    assert error.value.args[0] == \
        'expected 2-tuple but got %r' % u'Updated,Yo,Hoo'

    error = catch_syntax_error(5)
    assert error.value.args[0] == \
        'expected 2-tuple starting with %r' % u'Updated'

    error = catch_syntax_error(6)
    assert error.value.args[0] == 'expected list but got %r' % u'YO TABLE'
