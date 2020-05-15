# coding: utf8

# mysql相关配置
MYSQL_ADDRESS = '10.16.2.40'
MYSQL_PORT = 3306
MYSQL_DATABASE = 'sso'
MYSQL_USERNAME = 'sso'
MYSQL_PASSWORD = 'sso'

# redis相关配置，如果redis未设置密码请注释REDIS_PASSWORD选项
REDIS_HOST = '10.16.2.40'
REDIS_PORT = 6379
REDIS_PASSWORD = 'rocshen'

# 超级管理员用户名列表
SUPER_USERNAME_LIST = ['shenp']


# ldap相关配置
LDAP_HOST = '10.16.2.101'
LDAP_PORT = 389
LDAP_SEARCH_BASE = 'ou=people,dc=antrice,dc=cn'


# 邮件相关配置
MAIL_SERVER = "localhost"
MAIL_PORT = 25
MAIL_USERNAME = "admin"
MAIL_PASSWORD = "admin"
