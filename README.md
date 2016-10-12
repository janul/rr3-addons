rr3-addons
==========

Additions scripts/tools for Edugate Jagger: https://github.com/Edugate/ResourceRegistry

## Table of Contents

1. [How to enable "Sign" button on Jagger](#how-to-enable-sign-button-on-jagger)

## How to enable "Sign" button on Jagger:

1. Install the required packages:

   * ```sudo apt-get install gearman-job-server php5-dev php-pear memcached libboost-all-dev gperf libevent-dev uuid-dev libcloog-ppl-dev python-setuptools openjdk-7-jdk```

2. Install the latest release of gearman service: 

   * ```cd /opt ; wget https://github.com/gearman/gearmand/releases/download/1.1.13/gearmand-1.1.13.tar.gz```
   * ```tar -xzvf gearmand-1.1.13.tar.gz ; rm -f gearmand-1.1.13.tar.gz```
   * ```cd gearmand-1.1.13 ; ./configure ; make ; make install```

3. Install the gearman PHP and Python libraries:

   * ```easy_install gearman ; pecl install gearman```
   * ```echo "extension=gearman.so" > /etc/php5/cli/php.ini ; service apache2 restart```

4. Modify the ```prefix``` variable in the ```/etc/init.d/gearman-job-server``` file from ```prefix=/usr``` to ```prefix=/usr/local```

5. Check that all works well (version should be 1.1.13):

   * ```service gearman-job-server restart ; gearmand -V```

6. Verify that in the file ```/etc/default/gearman-job-server``` there is ```PARAMS="--listen=127.0.0.1"```

7. Retrieve the **rr3-addons** and put them in the right location: 
   * ```cd /opt ; git clone https://github.com/janul/rr3-addons.git```
   * ```cd /etc/init.d/ ; ln -s /opt/rr3-addons/gearman-workers/gearman-workers```
   * ```chmod u+x /opt/rr3-addons/gearman-workers/gearman-workers```

8. Prepare the location where will be placed the metadata signer certificate and key:
   * ```mkdir /opt/md-signer ; chown root:root /opt/md-signer ; chmod 644 /opt/md-signer```

9. Put your **metadata-signer.crt** and **metadata-signer.key** into the /opt/md-signer folder:

   Example command to create self-signed credentials (valid for 3 years):

   * ```openssl req -x509 -nodes -days 1095 -newkey rsa:2048 -out /opt/md-signer/metadata-signer.crt -keyout /opt/md-signer/metadata-signer.key -subj "/CN=##FULL.QUALIFIED.DOMAIN.VM-NAME##"```

   * ```chmod 400 /opt/md-signer/metadata-signer.key ; chmod 644 /opt/md-signer/metadata-signer.crt```

10. Retrieve the XMLSecTool utility to be used to sign metadatas:
   * ```cd /opt ; wget http://shibboleth.net/downloads/tools/xmlsectool/latest/xmlsectool-2.0.0-bin.zip```
   * ```unzip xmlsectool-2.0.0-bin.zip ; rm -f xmlsectool-2.0.0-bin.zip```

11. Modify the ```/opt/rr3-addons/gearman-workers/gearman-workers``` variables by following this example:

   * ```vim /opt/rr3-addons/gearman-workers/gearman-workers```
     ```
     DAEMON="/usr/bin/python"
     ARGS="/opt/rr3-addons/gearman-workers/gearman-worker-metasigner.py"
     PIDFILE="/var/run/gworker/gworkers.pid"
     USER="root"
     ```

12. Modify the ```/opt/rr3-addons/gearman-workers/gearman-worker-metasigner.py``` variables by following this example:

    ```python
    os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-1.7.0-openjdk-amd64/jre"    /* Yours JAVA_HOME directory */
    xmlsecommand = "/opt/xmlsectool-1.2.0/xmlsectool.sh"                     /* Yours XMLSECTOOL path*/
    cert="/opt/md-signer/metadata-signer.crt"                                /* Certificate for signing */
    certkey="/opt/md-signer/metadata-signer.key"                             /* Key for signing */
    cerpass="#CERTPASS#"                                                     /* Password of the Key or leave empty */
    destination="#JAGGER_PATH#/signedmetadata"                                    /* Path of your Jagger "signedmetadata" folder */
    allowedtypes = ['federation','provider','federationexport']
    ```

13. Enable the "**Sign**" button on your Jagger GUI:

  * ```mkdir /var/run/gworker ; mkdir /opt/rr3/signedmetadata```

14. Add to ```#JAGGER-PATH#/application/config/config_rr.php```:

  ```php
  /*
  * Enable SHA-256 Signature as default
  */
  $config['signdigest'] = 'SHA-256';

  /**
  * gearman - Remove the comment to these lines to enable the "Sign" button on Jagger
  */
  $config['gearman'] = TRUE;
  $config['gearmanconf']['jobserver'] = array(array('ip'=>'127.0.0.1','port'=>'4730'));
  ```

15. Remember to start the services in this order:
    A) service gearman-job-server start
    B) service gearman-workers start
   
16. Now the **Sign** button for your federation is enabled and you can sign your metadata.
