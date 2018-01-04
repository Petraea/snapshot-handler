#!/usr/bin/python
import sys,os,time
import logging
import argparse
from dateutil.parser import parse
from subprocess import Popen, PIPE
try:
   from configparser import ConfigParser
except:
   from ConfigParser import ConfigParser
basepath =os.path.dirname(os.path.realpath(__file__))
config = ConfigParser()
configfile=basepath+os.sep+'config.cfg'
if not os.path.exists(configfile):
    configfile=basepath+os.sep+'config.cfg.example'
config.read(configfile)

snaptimes = [float(x) for x in config.get('main','times').split(',')]
time_separator=config.get('main','separator')

now = time.time()

def parse_snaps(snapshots):
    snaps=[]
    for s in snapshots:
        then = time.mktime(snapshots[s]['ctime'])
        days = (now - then)/86400
        snaps.append((snapshots[s],days))
    return snaps

def elimination_list(snapshots):
    todel = parse_snaps(snapshots)
    logging.debug("Current snapshot list: %s" % [(x[0]['lv'],int(x[1])) for x in todel])
    for t in snaptimes:
        relatimes=[]
        for s in todel:
            relatimes.append((s[0],abs(t-s[1])))
        relatimes.sort(key=lambda x: x[1])
        if len(relatimes)>0:
            bestfit = relatimes[0][0]
            for s in todel[:]:
                if s[0] == bestfit:
                    logging.info("%s is fine for time %s" % (s[0]['lv'],t))
                    todel.remove(s)
    return [x[0] for x in todel]

def get_snapshots(lv_name):
    separator='$'
    p = Popen(['lvs','-o','lv_name,lv_all','--separator='+separator],stdout=PIPE)
    values = [x.strip().split(separator) for x in p.communicate()[0].strip().split('\n')]
    keys=[x.lower() for x in values[0]]
    lvs={}
    for l in values[1:]:
        lvs[l[0]]={keys[x]:l[x] for x in range(len(l))}
        lvs[l[0]]['ctime']=parse(lvs[l[0]]['ctime']).timetuple()
    origin_lv=lvs[lv_name]
    snapdict = {x:lvs[x] for x in lvs if lvs[x]['origin uuid']==origin_lv['lv uuid']}
    return origin_lv, snapdict

def delete_snapshot(snapshot):
    if snapshot['origin']=='':
        raise ValueError("This is not a snapshot!")
    logging.warn('Deleting snapshot %s' % snapshot['lv'])
    cmd = ['lvremove',snapshot['lv']]
    p = Popen(cmd,stdout=PIPE,stderr=PIPE)
    if p.returncode==0:
        logging.debug(p.communicate())
    else:
        logging.warn(p.communicate())

def create_snapshot(origin_lv):
    snap_name = origin_lv['lv']+time_separator+time.strftime('%Y%m%d',time.localtime(now))
    cmd = ['lvcreate','-s','--thinpool',origin_lv['pool'],'--name',snap_name,origin_lv['lv']]
    p = Popen(cmd,stdout=PIPE,stderr=PIPE)
    if p.returncode==0:
        logging.debug(p.communicate())
    else:
        logging.warn(p.communicate())

def do_snapshot(lv_name,no_delete=False,no_create=False):
    origin, snaps = get_snapshots(lv_name)
    to_delete = elimination_list(snaps)
    logging.info("Deletion list: %s" % to_delete)
    if not no_delete:
         for d in to_delete:
            delete_snapshot(d)
    if not no_create:
        create_snapshot(origin)

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("lv_name",help="The LV to snapshot/tidy")
    parser.add_argument("-D",help="Don't delete old snapshots",action="store_true")
    parser.add_argument("-C",help="Don't create new snapshot",action="store_true")
    parser.add_argument("-v",help="Increase verbosity",action="count",default=0)
    parser.add_argument("-q",help="Decrease verbosity",action="count",default=0)
    args = parser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(min(max(30+(args.q-args.v)*10,0),50))
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    do_snapshot(args.lv_name,args.D,args.C)
