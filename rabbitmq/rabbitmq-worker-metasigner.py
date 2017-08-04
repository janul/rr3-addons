import signal
import time
import multiprocessing
import pwd
import grp
import os
import sys
import json
import subprocess
import urllib2
import pika
import time
import base64


# this just example template to allow use gearman feature in RR3.
# guessing -  it can be done in prettier way. please share with you ideas

# details about xmlsec script
os.environ["JAVA_HOME"] = "/usr/lib/jvm/jdk1.8";
xmlsecommand = "/opt/tools/xmlsectool-2.0.0/xmlsectool.sh"
cert="/opt/tools/certs/metadatasigner.crt"
certkey="/opt/tools/certs/metadatasigner.key"
cerpass="XXXXXX"
destination="/opt/Jagger/signedmetadata"
allowedtypes = ['federation','provider','federationexport']
rabbitmqHost = 'localhost'
rabbitmqPort = 5672
rabbitmqUser = 'guest'
rabbitmqPassword = 'guest'
rabbitmqVhost = '/'

# your apache uid
uid=pwd.getpwnam("www-data").pw_uid
gid=grp.getgrnam("www-data").gr_gid
setOwnerShip = False

if not os.path.exists(xmlsecommand):
    sys.exit('Error! '+xmlsecommand+' doesnt exist')
if not os.path.exists(cert):
    sys.exit('Error! '+cert+' doesnt exist')
if not os.path.exists(certkey):
    sys.exit('Error! '+certkey+' doesnt exist')
if not os.path.exists(destination+'/'):
    sys.exit('Error! '+destination+' doesnt exist')

credentials = pika.PlainCredentials(rabbitmqUser, rabbitmqPassword)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmqHost,port=rabbitmqPort,credentials=credentials,virtual_host=rabbitmqVhost))
channel = connection.channel()
channel.queue_declare(queue='metadatasigner', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')




def finalcallback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    time.sleep(body.count(b'.'))
    print(" Decoding body...")
    decoded = base64_url_decode(body)
    print(" Decoded body:: %r " % decoded) 
    y = json.loads(decoded)
    if isinstance(y, dict) and 'encname' in y:
        signer(y)
    else:
        for a in y:
            signer(a)


    print(" [x] Done")
    ch.basic_ack(delivery_tag = method.delivery_tag)

def parse_signed_request( signed_request ):
    encoded_sig, payload = signed_request.split('.',2)
    data = json.loads(base64.b64decode( payload.replace('-_', '+/') ))
    return data

def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord,
u'-_'), u'+/'))))





def signer(data):
    print('Signer triggered...')
    if data['type'] in allowedtypes:
        if 'encname' in data:
            print "encname exists in json"
            encnamestr = str(data['encname']);
            print("Encoded entityID: %r , " %encnamestr)
            if len(encnamestr) > 0:
                print "encname not empty"
                fullpath = destination+'/'+str(data['type'])+'/'+str(data['encname'])
                print(fullpath)
                if not os.path.exists(fullpath):
                    print "fullpath not existing creating"
                    os.makedirs(fullpath) 
                else:
                    print "full path exists"
            else:
                print "encmae is empty"
        else:
            print "encname key not found in json"
        digestMethod = str(data['digest'])
        outputFile = destination+"/"+data['type']+"/"+data['encname']+"/metadata.xml"
        sourcePath = str(data["src"])
        print(sourcePath)
        outputFile = destination+"/"+data['type']+"/"+data['encname']+"/metadata.xml"
        sourcePath = str(data["src"])
        if len(cerpass) > 0:
            print('cerpass > 0')
            bcommand = xmlsecommand + " --verbose --referenceIdAttributeName ID  --sign --certificate "+ cert  +" --key "+certkey+" --keyPassword "+cerpass+" --digest  "+digestMethod+" --outFile "+outputFile+"  --inUrl " +  sourcePath
        else:
            bcommand = xmlsecommand + " --verbose --referenceIdAttributeName ID  --sign --certificate "+ cert  +" --key "+certkey+"  --digest  "+digestMethod+" --outFile "+outputFile+"  --inUrl " +  sourcePath
        print('running final command : %r' %bcommand)
        u = subprocess.Popen(bcommand.split(), stdout=subprocess.PIPE)
        output = u.communicate()[0]
        if setOwnerShip:
            os.chown(outputFile, uid, gid)
        print('Signingn metadata for %r has beend finished' %encnamestr)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(finalcallback,
                      queue='metadatasigner')

channel.start_consuming()
