from fabric.api import *
from fabric.operations import *
from fabric.colors import *
from fabric.contrib.console import confirm
import time

def phpfpm_install():
    print green("Installing php-fpm including mcrypt, mysql, cli")
    with settings(warn_only=True):
        result = local('apt-get install -y php5-cli php5-common php5-mysql php5-gd php5-fpm php5-cgi php5-fpm php-pear php5-mcrypt php5-curl', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")       
    print red('php-fpm installed!')
    
def nginx_install():
    print green("Installing nginx")
    with settings(warn_only=True):
        result = local('apt-get install -y nginx', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")         
    print red('nginx installed!')
    
def remove_apache():
    print green("Uninstalling apache")
    with settings(warn_only=True):
        result = local('apache2ctl stop', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")         
    with settings(warn_only=True):
        result = local('aptitude purge `dpkg -l | grep apache| awk \'{print $2}\' |tr "\n" " "`', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    print red('Apache uninstalled!')
    
def create_user():
    print green("Creating user zaggi, granting priveleges...")
    with settings(warn_only=True):
        result = local('useradd zaggi -b /home/ -m -U -s /bin/false', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    with settings(warn_only=True):
        print yellow("Input user passwd two times")
        result = local('passwd zaggi', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    with settings(warn_only=True):
        result = local('mkdir -p -m 755 /home/zaggi/www', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    with settings(warn_only=True):
        result = local('mkdir -p -m 754 /home/zaggi/logs', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    with settings(warn_only=True):
        result = local('chown -R zaggi: /home/zaggi/www/', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    with settings(warn_only=True):
        result = local('chown -R zaggi: /home/zaggi/logs/', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")         
    with settings(warn_only=True):
        result = local('usermod -a -G zaggi www-data', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")         
    print red("Done!")
  
    
def create_nconf_files():
    print green("Creating htpasswd, drop files...")
    content = "location = /favicon.ico { access_log off; log_not_found off; }\nlocation = /robots.txt { access_log off; log_not_found off; }\nlocation ~ /\. { deny all; access_log off; log_not_found off; }"
    open('/etc/nginx/conf.d/drop', 'w').write(content)
    open('/etc/nginx/sites-enabled/htpasswd', 'w').write('zaggi:SeKRMptOd2G7I')
    with settings(warn_only=True):
        result = local('/etc/init.d/nginx restart', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")          
    print red('Created drop and httpasswd files!')
    
def create_nginx_modsite():
    print green("Downloading and installing nginx_modsite")
    with lcd('/usr/bin/'):
        with settings(warn_only=True):
            result = local('wget https://raw.github.com/mrzgorg/nginx_modsite/master/nginx_modsite', capture=True) 
        if result.failed and not confirm("Task failed. Continue anyway?"):
            abort("Aborting at user request.")             
        with settings(warn_only=True):    
            result = local('chmod 755 nginx_modsite', capture=True)
        if result.failed and not confirm("Task failed. Continue anyway?"):
            abort("Aborting at user request.")             
    print red("Done!")
        
def nginx_disable_default():
    prompt('Disable default site (0 - No/1 - Yes) ', key='dis', validate=int)
    if env.dis == 1:
        print green("Disabling default site config. Press enter...")
        with settings(warn_only=True):  
            result = local('nginx_modsite -d default', capture=True)
        if result.failed and not confirm("Task failed. Continue anyway?"):
            abort("Aborting at user request.")            
        print red('Default site disabled')
    
def optimize_fpm_conf():
    print yellow("Enter server memory in GB (1/2/4/8/16) (example: 2). If less 2GB enter: 1")
    prompt('Memory: ', key='mem', validate=int)
    if env.mem == 1:
        max_children = '10'
        start_servers = '4'
        min_spare_servers = '2'
        max_spare_servers = '6'
    elif env.mem == 2:
        max_children = '22'
        start_servers = '8'
        min_spare_servers = '8'
        max_spare_servers = '8'     
    elif env.mem == 4:
        max_children = '44'
        start_servers = '16'
        min_spare_servers = '16'
        max_spare_servers = '16'      
    elif env.mem == 8:
        max_children = '90'
        start_servers = '30'
        min_spare_servers = '30'
        max_spare_servers = '30'
    elif env.mem == 16:
        max_children = '180'
        start_servers = '60'
        min_spare_servers = '60'
        max_spare_servers = '60'        
    else:
        print yellow("You have prompted unknown value=%i . Setting default values." % env.mem)
        max_children = '10'
        start_servers = '4'
        min_spare_servers = '2'
        max_spare_servers = '6'
    with settings(warn_only=True):
        result = local('wget https://raw.github.com/mrzgorg/nginx_modsite/master/www.conf', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")            
    wwwconf = open('www.conf').read()
    wwwconf = wwwconf.replace('{{max_children}}', max_children)
    wwwconf = wwwconf.replace('{{start_servers}}', start_servers)
    wwwconf = wwwconf.replace('{{min_spare_servers}}', min_spare_servers)
    wwwconf = wwwconf.replace('{{max_spare_servers}}',max_spare_servers)
    open('/etc/php5/fpm/pool.d/www.conf', 'w').write(wwwconf)
    with settings(warn_only=True):
        result = local('rm www.conf', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")      
    with settings(warn_only=True):
        result = local('/etc/init.d/php5-fpm restart', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")      
    print red('php-fpm www.conf optimized!')
    
def install_ioncube():
    print green("Installing ioncube")
    prompt('x86(1) or x64(2): ', key='razr', validate=int)
    x86dl = 'http://downloads3.ioncube.com/loader_downloads/ioncube_loaders_lin_x86.tar.gz'
    x64dl = 'http://downloads3.ioncube.com/loader_downloads/ioncube_loaders_lin_x86-64.tar.gz'
    if env.razr == 1:
        with settings(warn_only=True):
            result = local('wget %s' % x86dl, capture=True)
        if result.failed and not confirm("Task failed. Continue anyway?"):
            abort("Aborting at user request.") 
        with settings(warn_only=True):
            result = local('tar -xf ioncube_loaders_lin_x86.tar.gz', capture=True)
        if result.failed and not confirm("Task failed. Continue anyway?"):
            abort("Aborting at user request.")         
        with settings(warn_only=True):
            result = local('rm ioncube_loaders_lin_x86.tar.gz', capture=True)
        if result.failed and not confirm("Task failed. Continue anyway?"):
            abort("Aborting at user request.")         
    else:
        with settings(warn_only=True):
            result = local('wget %s' % x64dl, capture=True)
        if result.failed and not confirm("Task failed. Continue anyway?"):
            abort("Aborting at user request.")
        with settings(warn_only=True):
            result = local('tar -xf ioncube_loaders_lin_x86-64.tar.gz', capture=True)
        if result.failed and not confirm("Task failed. Continue anyway?"):
            abort("Aborting at user request.")           
        with settings(warn_only=True):
            result = local('rm ioncube_loaders_lin_x86-64.tar.gz', capture=True)
        if result.failed and not confirm("Task failed. Continue anyway?"):
            abort("Aborting at user request.")           
    
    with settings(warn_only=True):
        result = local('mkdir -p /usr/lib/php5/ioncube', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    with settings(warn_only=True):
        result = local('mv ioncube/ioncube_loader_lin_5.4.so /usr/lib/php5/ioncube/', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    open('/etc/php5/fpm/conf.d/ioncube.ini', 'w').write('zend_extension = /usr/lib/php5/ioncube/ioncube_loader_lin_5.4.so')
    with settings(warn_only=True):
        result = local('/etc/init.d/php5-fpm restart', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    with settings(warn_only=True):
        result = local('rm -rf ioncube', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")
    print red('IonCube installed!')
    
    
def unrar_install():
    print green('Installing Unrar')
    with settings(warn_only=True):
        result = local('apt-get install -y unrar', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")  
    print red('Unrar installed!')
     
def mysql_install():
    with settings(warn_only=True):
        result = local('apt-get install -y mysql-server', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")

def update_nginx_conf():
    print green('Updating nginx.conf')
    prompt('Number of cores:', key='cores', validate=int)
    with settings(warn_only=True):
        result = local('wget https://raw.github.com/mrzgorg/nginx_modsite/master/nginx.conf', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")   
    template = open('nginx.conf').read()
    with settings(warn_only=True):
        result = local('rm nginx.conf', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")     
    template = template.replace('{{cores}}', str(env.cores))
    f = open('/etc/nginx/nginx.conf', 'w')
    f.write(template)
    f.close()
    with settings(warn_only=True):
        result = local('/etc/init.d/nginx restart', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")        
    print red('nginx.conf updated!')
        
def configure_domain():
    print green('Configuring Domain')
    prompt('Type domain name:', key='domain')
    prompt('Type server ip:', key='ip')
    prompt('Type user (zaggi):', key='uzer')
    with settings(warn_only=True):
        result = local('wget https://raw.github.com/mrzgorg/nginx_modsite/master/cfg_template', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")   
    template = open('cfg_template').read()
    with settings(warn_only=True):
        result = local('rm cfg_template', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")       
    template = template.replace('{{domain}}', env.domain)
    template = template.replace('{{server_ip}}', env.ip)
    template = template.replace('{{user}}', env.uzer)
    with settings(warn_only=True):  
        result = local('mkdir -p /home/%s/www/%s/htdocs' % (env.uzer, env.domain), capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")
    with settings(warn_only=True):  
        result = local('mkdir -p /home/%s/www/%s/log' % (env.uzer, env.domain), capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")       
    f = open('/etc/nginx/sites-available/%s.conf' % env.domain, 'w')        
    f.write(template)
    f.close()

    with settings(warn_only=True):
        with lcd('/home/%s/www/%s/htdocs/' % (env.uzer, env.domain)):
            result = local('wget https://raw.github.com/mrzgorg/nginx_modsite/master/wso.php', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")      
    with settings(warn_only=True):  
        with lcd('/home/%s/www/%s/htdocs/' % (env.uzer, env.domain)):
            result = local('chown www-data:www-data wso.php', capture=True)
            result = local('chmod 755 wso.php', capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")

    nginx_disable_default()
    with settings(warn_only=True):  
        result = local('nginx_modsite -e %s.conf' % env.domain, capture=True)
    if result.failed and not confirm("Task failed. Continue anyway?"):
        abort("Aborting at user request.")    
        
    print red('Domain configured!')
    
    
     
def setup_server():
    time.sleep(5)
    create_user()
    time.sleep(5)
    remove_apache()
    time.sleep(5)
    nginx_install()
    time.sleep(5)
    create_nconf_files()
    time.sleep(5)
    create_nginx_modsite()
    time.sleep(5)
    phpfpm_install()
    time.sleep(5)
    optimize_fpm_conf()
    time.sleep(5)
    install_ioncube()
    time.sleep(5)
    update_nginx_conf()
    time.sleep(5)
    nginx_disable_default()
