#!/usr/bin/env python3

from pytbox.base import vm, get_cronjob_counter
from pytbox.utils.cronjob import cronjob_counter


def test_query():
    r = vm.query('ping_average_response_ms')
    print(r)

def test_check_ping_result():
    r = vm.check_ping_result(target='10.20.3.106', last_minute=10)
    print(r)

def test_get_labels():
    r = vm.get_labels('ping_average_response_ms')
    print(r)

@get_cronjob_counter(app_type="tests", app="tests.test_victoriameterics", schedule_interval='5s')
def test_check_snmp_port_status():
    r = vm.check_snmp_port_status(sysname="shylf-prod-coresw-ce6820-182", if_name="10GE1/0/47", last_minute=10)
    print(r)


test_check_ping_result()

# r = vm.check_interface_avg_rate(direction='in', sysname='whcq-prod-coresw-s6720-254', ifname='XGigabitEthernet0/0/47', last_hours=24*30, last_minutes=5)
# print(r)

# r = vm.check_interface_max_rate(direction='in', sysname='whcq-prod-coresw-s6720-254', ifname='XGigabitEthernet0/0/47', last_hours=24*30, last_minutes=5)
# print(r)

# r = vm.check_unreachable_ping_result()
# print(r)


if __name__ == "__main__":
    # test_get_labels()
    # test_query()
    # test_check_ping_result()
    # test_check_snmp_port_status()
    # test_check_interface_avg_rate()
    pass
