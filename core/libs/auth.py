# coding: utf8

from ldap3 import Server, Connection, ALL, SUBTREE


class LDAPAuth:
    __domain = None
    __search_base = None
    __attribute_list = ['cn', 'displayName', 'mail', 'member', 'mobile', 'uid']
    __search_filter_key = None
    # 该子字段用于判断认证服务器为OpenLDAP还是Windows的AD域，带有该字段的为OpenLDAP服务器
    __openldap_flag = 'OpenLDAProotDSE'

    """
    admin_dn及admin_password仅在OpenLDAP下生效
    """
    def __init__(self, host='localhost', domain=None, port=389, search_base=None, admin_dn=None, admin_password=None):
        self.__domain = domain
        self.__search_base = search_base
        self.__server = Server(host, port=port, get_info=ALL)
        self.__conn = Connection(self.__server)
        if self.__conn.bind():
            if self.__openldap_flag in self.__server.info.to_json():
                self.__search_filter_key = 'uid'
                self.__conn = Connection(self.__server, user=admin_dn, password=admin_password)
                if not self.__conn.bind():
                    raise Exception(self.__conn.result['message'])
            else:
                self.__search_filter_key = 'sAMAccountName'
                self.__attribute_list.append('sAMAccountName')
        else:
            raise Exception('connect to ldap server {}:{} failed'.format(host, port))

    def __search(self, username):
        res = self.__conn.search(search_base=self.__search_base,
                                 search_filter='({}={})'.format(self.__search_filter_key, username),
                                 search_scope=SUBTREE, attributes=self.__attribute_list)
        if res:
            return self.__conn.response[0]
        return False

    """
    OpenLDAP返回的属性信息均为长度为1的列表格式，此处进行提取
    """
    def __pretty_user_info(self, ldap_user_info):
        user_info = {}
        if self.__search_filter_key == 'uid':
            for key in self.__attribute_list:
                value = ldap_user_info['attributes'][key]
                if len(value) > 0:
                    user_info[key] = value[0]
                else:
                    user_info[key] = ''
            user_info['username'] = ldap_user_info['attributes']['uid'][0]
            user_info['displayName'] = ldap_user_info['attributes']['cn'][0]
        else:
            user_info = ldap_user_info
            user_info['username'] = ldap_user_info['attributes']['sAMAccountName']
        return user_info

    def auth(self, username, password):
        ldap_user_info = None
        """
        如果是OpenLDAP则需要先获取用户的DN，然后使用DN作为用户名登录
        如果是Windows的AD域则使用username@domain形式作为登录名
        """
        if self.__search_filter_key == 'uid':
            ldap_user_info = self.__search(username)
            if ldap_user_info:
                ldap_user = ldap_user_info.get('dn')
            else:
                return False
        else:
            ldap_user = '{}@{}'.format(username, self.__domain)

        # 带上用户名和密码进行校验
        self.__conn = Connection(self.__server, user=ldap_user, password=password)

        if self.__conn.bind():
            if self.__search_filter_key == 'uid':
                return self.__pretty_user_info(ldap_user_info)
            else:
                return self.__search(username)['attributes']
        return False
