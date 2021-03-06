# Created by: Gustavo Antonio Lutz de Matos
# e-mail: gustavo.almatos@gmail.com
# Zabbix and LDAP Integration

from zabbix_user_get import ZabbixGetModule
from zabbix_user_create import ZabbixCreateModule
from zabbix_user_delete import ZabbixDeleteModule
from zabbix_api_connection import ZabbixConnectionModule
from ldap_query import LDAPQuery
import logging
import sys


class ZabbixLDAPIntegration:

    def __init__(
            self,
            zabbix_server,
            zabbix_username,
            zabbix_password,
            ldap_server,
            ldap_username,
            ldap_password,
            ldap_basedn,
            ldap_memberof
    ):
        self.zabbix_server = zabbix_server
        self.zabbix_username = zabbix_username
        self.zabbix_password = zabbix_password

        self.zabbix_connection_obj = ZabbixConnectionModule(
            self.zabbix_server,
            self.zabbix_username,
            self.zabbix_password
        )

        self.ldap_server = ldap_server
        self.ldap_username = ldap_username
        self.ldap_password = ldap_password
        self.ldap_basedn = ldap_basedn
        self.ldap_memberof = ldap_memberof

    def get_zabbix_users_function(self):
        zabbix_user_list = ZabbixGetModule(self.zabbix_connection_obj.zabbix_api_connect())
        return zabbix_user_list.get_zabbix_user_list()

    def get_ldap_users_function(self):
        query_object = LDAPQuery(
            self.ldap_server,
            self.ldap_username,
            self.ldap_password,
            self.ldap_basedn,
            self.ldap_memberof
        )
        return query_object.ldap_search(query_object.ldap_bind())

    def create_zabbix_users_function(self, ldap_samaccountname, ldap_givenname, ldap_sn):
        zabbix_create_user = ZabbixCreateModule(self.zabbix_connection_obj.zabbix_api_connect())
        return zabbix_create_user.create_zabbix_user(ldap_samaccountname, ldap_givenname, ldap_sn)

    # def update_zabbix_users_function(self, zabbix_user_id):
    #     exit()
    #
    # def disable_zabbix_users_function(self, ldap_samaccountname, ldap_givenname, ldap_sn):
    #     exit()

    def delete_zabbix_users_function(self, zabbix_user_id, zabbix_user_name, zabbix_user_surname):
        zabbix_delete_user = ZabbixDeleteModule(self.zabbix_connection_obj.zabbix_api_connect())
        return zabbix_delete_user.delete_zabbix_user(zabbix_user_id, zabbix_user_name, zabbix_user_surname)


def compare_users_function(zabbix_conn_obj, zabbix_user_list, ldap_user_list, bind_user):
    result = 0
    # Create zabbix user list to do checks
    zabbix_login_list = []
    for user_alias in zabbix_user_list:
        zabbix_login_list.append(user_alias['alias'])

    # Create ldap user list to do checks
    ldap_login_list = []
    for user_alias in ldap_user_list:
        ldap_login_list.append(user_alias['sAMAccountName'])

    # Check if the user needs to be created
    for account_name in ldap_user_list:
        if (
                account_name['sAMAccountName'] == bind_user or
                account_name['sAMAccountName'] == 'Admin' or
                account_name['sAMAccountName'] == 'guest'
        ):
            continue
        if account_name['sAMAccountName'] not in zabbix_login_list:
            result = zabbix_conn_obj.create_zabbix_users_function(
                account_name['sAMAccountName'],
                account_name['givenName'],
                account_name['sn']
            )
            if result == 1:
                logging.info(f"User {account_name['givenName']} {account_name['sn']} added!")

    # Check if the user needs to be removed
    for account_name in zabbix_user_list:
        if (
                account_name['alias'] == bind_user or
                account_name['alias'] == 'Admin' or
                account_name['alias'] == 'guest'
        ):
            continue
        elif account_name['alias'] not in ldap_login_list:
            result = zabbix_conn_obj.delete_zabbix_users_function(
                account_name['userid'],
                account_name['name'],
                account_name['surname']
            )
            if result == 1:
                logging.info(f"User {account_name['name']} {account_name['surname']} removed!")


def main():

    zabbix_server_input = input()
    zabbix_user_input = input()
    zabbix_pass_input = input()

    ldap_server_input = input()
    ldap_username_input = input()
    ldap_password_input = input()
    ldap_basedn_input = input()
    ldap_memberof_input = input()

    logging.basicConfig(
        level=logging.INFO,
        filename='zabbix-ldap.log',
        filemode='a',
        format='[%(asctime)s] - %(levelname)s: %(message)s, ',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if zabbix_server_input == '':
        logging.error('Missing "zabbix_server" parameter to complete the connection.')
        sys.exit()
    if zabbix_user_input == '':
        logging.error('Missing "zabbix_user" parameter to complete the connection.')
        sys.exit()
    if zabbix_pass_input == '':
        logging.error('Missing "zabbix_passowrd" parameter to complete the connection.')
        sys.exit()
    if ldap_server_input == '':
        logging.error('Missing "ldap_server" parameter to complete the connection.')
        sys.exit()
    if ldap_username_input == '':
        logging.error('Missing "ldap_user" parameter to complete the connection.')
        sys.exit()
    if ldap_password_input == '':
        logging.error('Missing "ldap_password" parameter to complete the connection.')
        sys.exit()
    if ldap_basedn_input == '':
        logging.error('Missing "ldap_basedn" parameter to complete the connection.')
        sys.exit()
    if ldap_memberof_input == '':
        logging.error('Missing "ldap_memberof" parameter to complete the connection.')
        sys.exit()

    compare_obj = ZabbixLDAPIntegration(
        zabbix_server_input,
        zabbix_user_input,
        zabbix_pass_input,
        ldap_server_input,
        ldap_username_input,
        ldap_password_input,
        ldap_basedn_input,
        ldap_memberof_input
    )

    logging.info('Begin of the script.')
    zbx_usr_list = compare_obj.get_zabbix_users_function()
    ldap_usr_list = compare_obj.get_ldap_users_function()
    compare_users_function(compare_obj, zbx_usr_list, ldap_usr_list, zabbix_user_input)
    logging.info('End of the script.')
    sys.exit()


if __name__ == "__main__":
    main()
