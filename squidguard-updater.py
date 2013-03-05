#!/bin/env python
# -*- coding: utf-8 -*-
#TODO: Propósito del script es actualizar la BD de squidguard agregando cada uno de los elementos de la lista de shallalist a /var/lib/squidguard/db/ . Luego, agregar los dominios en domainlist de /etc/squid/squidGuard.conf y denegarlos en la parte del dominio. Finalmente actualizar la BD de squidguard y reconfigurar script.  
import urllib, tarfile, os, shutil, re

#Descargar las listas a bloquear
print "Descargando listas a bloquear"
if os.path.exists('/tmp/blacklist.tar.gz'):
    os.remove('/tmp/blacklist.tar.gz')
tarbl = urllib.urlretrieve('http://www.shallalist.de/Downloads/shallalist.tar.gz','/tmp/blacklist.tar.gz')
bl = tarfile.open('/tmp/blacklist.tar.gz', 'r:gz')
if os.path.exists('/tmp/BL'):
    shutil.rmtree('/tmp/BL')
bl.extractall('/tmp/')
bl.close()

#Generar el /etc/squid/squidGuard.conf
print "Generando squidGuard.conf"
default = "dbhome /var/lib/squidguard/db/\nlogdir /var/log/squid\n"
dirname = []
domains = ""
for a, b, c in os.walk('/tmp/BL'):
	if not b and 'urls' in c and 'domains' in c:
		dirname.append(re.sub('/tmp/BL/', '', a))
		#print a, re.sub('/tmp/BL/','',a) , dirname[-1], "\n-----"
		domains += "\ndest %s {\n\tdomainlist %s/domains\n\turllist %s/urls\n}\n" % (dirname[-1], dirname[-1], dirname[-1])
blockedurls = ""
for dn in dirname:
	if dn == "":
		continue
	blockedurls += " !"+dn
acl = "acl {\n\tdefault {\n\t\tpass" + blockedurls + " all\n\t\tredirect http://192.168.2.100/block.html\n\t}\n}"
squidguard = default + domains + acl
if os.path.exists('/etc/squid/squidGuard.conf'):
	os.rename('/etc/squid/squidGuard.conf', '/etc/squid/squidGuard.conf.bkp')
fd=open('/etc/squid/squidGuard.conf', 'w')   #CAMBIAR
fd.write(squidguard)
fd.close()

#Copiar los archivos a /var/lib/squidguard/db/ 
print "Copiando archivos a la bd de squidGuard"
root_src_dir = '/tmp/BL/'
root_dst_dir = '/var/lib/squidguard/db/' #CAMBIAR
shutil.rmtree('/var/lib/squidguard/db/') #CAMBIAR
for src_dir, dirs, files in os.walk(root_src_dir):
	dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
	if not os.path.exists(dst_dir):
		os.mkdir(dst_dir)
	for file_ in files:
		src_file = os.path.join(src_dir, file_)
		dst_file = os.path.join(dst_dir, file_)
		if os.path.exists(dst_file):
			os.remove(dst_file)
		shutil.move(src_file, dst_dir)

#Regenerar la BD de squidguard, reconfigurar squid y arrancarlo.
print "generando BD"
os.system('squidGuard -C all')
print "cambiando permisos"
os.system('chown -R proxy:proxy /var/lib/squidguard/db/')
print "reiniciando squid"
os.system('squid3 -k reconfigure')

