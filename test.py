from base64 import b64decode, b64encode

s = b64encode(str('Тестовая строка из 5 слов\nНовая строка').encode('utf-8'))
print('|', s, '|', sep='')
