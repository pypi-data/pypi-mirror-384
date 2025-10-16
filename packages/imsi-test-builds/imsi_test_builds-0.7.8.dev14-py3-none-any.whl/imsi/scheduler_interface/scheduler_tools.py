"""
scheduler_tools
================

A module to create submission scripts and tools for different schedulers based on input directives

This is not the core aim of imsi, but is included for development and testing, and in particular it
enables the imsi shell sequencer (:mod:`imsi.iss`) to work across platforms.
"""

import json
import subprocess
from functools import reduce
from imsi.utils.general import get_date_string

fields = [
    ['Job_Name'],
    ['Job_Owner'],
    ['job_state'],
    ['queue'],
    ['Resource_List', 'nodect'],
    ['Resource_List', 'walltime']
]


def pbs_q_query(user=None):
    """
    Not functional
    """
    qstring = subprocess.check_output('qstat -f -Fjson', shell=True)
    qjson = json.loads(qstring)

    for job, job_info in qjson['Jobs'].items():
        pstr=""
        vals = [job]
        for f in fields:
            vals.append(str(reduce(dict.get, f, job_info)).split('@')[0][:65] )

        # Only for running jobs do used times exist
        if vals[3] == 'R':
            f = ['resources_used', 'walltime']
            vals.append(str(reduce(dict.get, f, job_info)).split('@')[0][:65] )
        else:
            vals.append('00:00')

        if user:
            if (job_info['Job_Owner'].split('@')[0] != user):
                #print(job_info['Job_Owner'].split('@')[0], user, job_info['Job_Owner'].split('@')[0]==user)
                continue
        print('{:15s} {:65s} {:8s} {:1s} {:15s} {:4s} {:10s} {:10s}'.format(*vals))

# TODO:
# Make this a general scheduler class. Then have subclass as caps to different schedulers.
# Each class should then have functions to set the resources / directives, etc.
# See: https://realpython.com/python-interface/
class scheduler():
    """
    A class that absracts properties for interacting  with different batch schedulers

    This is at a general level. It could be used to provide generic functionality,
    maybe a bit like rsub or jobsub, but not quite.
    """
    def __init__(self, scheduler_name):
        self.type = scheduler_name
        print("Init scheduler")
        # Move this into a json!(?)
        self._syntax = {
            "pbs" : {
                "directive_prefix" : "#PBS",
                "submission_command" : "qsub",
                "queue_info_command" : "qstat",
                "output_redirect" : '-o "{PATH}.o"',
                "nominal_directives" : [
                    "-l walltime=02:00:00",
                    "-l select=1:mem=100GB",
                    "-j oe"
                ]
            },
            "slurm" : {
                "directive_prefix" : "#SBATCH",
                "submission_command" : "sbatch",
                "queue_info_command" : "squeue",
                "output_redirect" : "-o {PATH}_%j.out",
                "nominal_directives" : [
                    "--time=04:00:00",
                    "--nodes=1"
                ]
            }
        }
        if scheduler_name in self._syntax.keys():
            for key, v in self._syntax[scheduler_name].items():
                setattr(self, key, v)
        else:
            raise ValueError(f"Unsupported scheduler {scheduler_name}. Supported schedulers are {','.join(list(self.syntax.keys()))}")


