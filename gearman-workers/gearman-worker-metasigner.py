import signal
import time
import multiprocessing
import pwd
import grp
import os
import sys
import json
import subprocess
import gearman
import urllib2

# this just example template to allow use gearman feature in RR3.
# guessing -  it can be done in prettier way. please share with you ideas

# details about xmlsec script
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-6-sun";
xmlsecommand = "PATH/xmlsectool.sh"
cert="CERTPATH/metadata-signer.crt"
certkey="CERTKEYPATH/metadata-signer.key"
cerpass="CERTPASS"
destination="PATH_TO_RR3_FOLDER/signedmetadata"
allowedtypes = ['federation','provider','federationexport']


# your apache uid
uid=pwd.getpwnam("www-data").pw_uid
gid=grp.getgrnam("www-data").gr_gid

if not os.path.exists(xmlsecommand):
    sys.exit('Error! '+xmlsecommand+' doesnt exist')
if not os.path.exists(cert):
    sys.exit('Error! '+cert+' doesnt exist')
if not os.path.exists(certkey):
    sys.exit('Error! '+certkey+' doesnt exist')
if not os.path.exists(destination+'/'):
    sys.exit('Error! '+destination+' doesnt exist')



gm_worker = gearman.GearmanWorker(['127.0.0.1:4730'])

def metadatasigner(gearman_worker, gearman_job):
    y = json.loads(gearman_job.data)
    print(type(str(y['type'])))
    print(y)
    if y['type'] in allowedtypes:
       if 'encname' in y:
           print "encname exists in json"
           encnamestr = str(y['encname']);
           print(encnamestr)
           if len(encnamestr) > 0:
               print "encname not empty"
               fullpath = destination+'/'+str(y['type'])+'/'+str(y['encname'])
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
       digestMethod = str(y['digest'])   
       outputFile = destination+"/"+y['type']+"/"+y['encname']+"/metadata.xml"
       sourcePath = str(y["src"])
       if len(cerpass) > 0:
         bcommand = xmlsecommand + "--referenceIdAttributeName ID  --sign --certificate "+ cert  +" --key "+certkey+" --keyPassword "+cerpass+" --digest  "+digestMethod+" --outFile "+outputFile+"  --inUrl " +  sourcePath
       else:
         bcommand = xmlsecommand + " --referenceIdAttributeName ID  --sign --certificate "+ cert  +" --key "+certkey+"  --digest  "+digestMethod+" --outFile "+outputFile+"  --inUrl " +  sourcePath
       #u = urllib2.urlopen(y['src'])
       gearman_worker.send_job_data(gearman_job, "downloding and signing metadata")
       u = subprocess.Popen(bcommand.split(), stdout=subprocess.PIPE)
       output = u.communicate()[0]
       os.chown(outputFile, uid, gid)
       gearman_worker.send_job_data(gearman_job, "done")
       print gm_worker.gearmanJobRequest.state
       return gearman_job.data


gm_worker.set_client_id('metadata')
gm_worker.register_task('metadatasigner', metadatasigner)

gm_worker.work()
