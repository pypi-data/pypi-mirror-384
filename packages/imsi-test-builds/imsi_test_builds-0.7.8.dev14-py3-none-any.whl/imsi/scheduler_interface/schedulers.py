import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# TODO:
# - deal with submission prefix
#        if "submit_prefix" in self.sim.machine_config['batch_commands'].keys():
#            self.submission_command =  self.sim.machine_config['batch_commands']["submit_prefix"] + " " + self.submission_command

@dataclass
class BatchJob:
    '''Defines a batch job with specific directives'''
    user_script: List[str]
    job_directives: Dict[str, str] = field(default_factory=dict)

    def construct_job_script(self, scheduler: 'Scheduler') -> List[str]:
        '''Constructs the entire job script from the header and user script using the scheduler's directives'''

        # A bit of a messy hack. We could insist that shebangs are provided separately....
        if self.user_script and self.user_script[0].startswith('#!'):
            shebang = self.user_script[0]
            script_body = self.user_script[1:]
        else:
            shebang = ''
            script_body = self.user_script

        job_header = scheduler.construct_job_header(self.job_directives)

        # Combine the shebang, job header, and script body (space before)
        job_script = [shebang] if shebang else []
        job_script.extend(job_header)
        job_script.extend([''] + script_body)

        return job_script

@dataclass
class Scheduler(ABC):
    '''Defines an abstract interface for scheduler classes'''
    name: str
    directive_prefix: str
    submission_command: str
    queue_info_command: str
    cancel_command: str
    output_redirect: str

    @abstractmethod
    def construct_job_header(self, job_directives: List) -> List:
        '''Constructs the job header based on directives'''
        pass

    @abstractmethod
    def submit(self, job: BatchJob) -> str:
        '''Submits a job and returns the job ID'''
        pass

    @abstractmethod
    def query_queue(self) -> str:
        '''Queries the job queue and returns the queue status'''
        pass

    @abstractmethod
    def cancel_job(self, job_id: str) -> str:
        '''Cancels a job given its job ID'''
        pass

    def _run_command(self, command: List[str]) -> str:
        '''Helper method to run a command and return its output'''
        result = subprocess.run(command, capture_output=True, text=True)
        result.check_returncode()
        return result.stdout.strip()

@dataclass
class PBSScheduler(Scheduler):
    name: str = "PBS"
    directive_prefix: str = '#PBS'
    submission_command: str = 'qsub'
    queue_info_command: str = 'qstat'
    cancel_command: str = 'qdel'
    output_redirect: str = '-o {PATH}.o'
    default_directives: list = field(default_factory=lambda: ["-l walltime=02:00:00", "-l select=1:mem=100GB", "-j oe"])

    def construct_job_header(self, job_directives: List) -> str:
        directives = [f"{self.directive_prefix} {directive}" for directive in job_directives]
        return directives

    def submit(self, job_script_filename: str) -> str:
        command = [self.submission_command, job_script_filename]
        output = self._run_command(command)
        job_id = output.split('.')[0]  # Extract the job ID
        return job_id

    def query_queue(self) -> str:
        command = [self.queue_info_command]
        return self._run_command(command)

    def cancel_job(self, job_id: str) -> str:
        command = [self.cancel_command, job_id]
        return self._run_command(command)

@dataclass
class SLURMScheduler(Scheduler):
    name: str = "SLURM"
    directive_prefix: str = '#SBATCH'
    submission_command: str = 'sbatch'
    queue_info_command: str = 'squeue'
    cancel_command: str = 'scancel'
    output_redirect: str = '-o {PATH}_%j.out'
    default_directives: list = field(default_factory=lambda: ["--time=06:00:00","--nodes=1"])

    def construct_job_header(self, job_directives: List) -> str:
        directives = [f"{self.directive_prefix} {directive}" for directive in job_directives]
        return directives

    def submit(self, job_script_filename: str) -> str:
        command = [self.submission_command, job_script_filename]
        output = self._run_command(command)
        job_id = output.split()[-1]  # Extract the job ID
        return job_id

    def query_queue(self) -> str:
        command = [self.queue_info_command]
        return self._run_command(command)

    def cancel_job(self, job_id: str) -> str:
        command = [self.cancel_command, job_id]
        return self._run_command(command)

def create_scheduler(scheduler_name: str) -> Scheduler:
    '''Factory method to create a scheduler instance based on the scheduler name'''
    if scheduler_name.lower() == 'pbs':
        return PBSScheduler()
    elif scheduler_name.lower() == 'slurm':
        return SLURMScheduler()
    else:
        raise ValueError(f"Unknown scheduler name: {scheduler_name}")

# Example usage (out of date)
def main():
    user_script_content = "echo 'Hello, World!'"

    pbs_scheduler = create_scheduler('pbs')
    pbs_job = Job(user_script=user_script_content, job_directives={'nodes': '1', 'walltime': '01:00:00', 'account': 'my_account', 'queue': 'my_queue'})

    print("PBS Job Script:")
    print(pbs_job.construct_job_script(pbs_scheduler))

    job_id = pbs_scheduler.submit(pbs_job)
    print(f"PBS Job ID: {job_id}")

    queue_status = pbs_scheduler.query_queue()
    print("PBS Queue Status:")
    print(queue_status)

    cancel_output = pbs_scheduler.cancel_job(job_id)
    print("PBS Cancel Output:")
    print(cancel_output)

    slurm_scheduler = create_scheduler('slurm')
    slurm_job = Job(user_script=user_script_content, job_directives={'nodes': '1', 'walltime': '01:00:00', 'account': 'my_account', 'queue': 'my_partition'})

    print("SLURM Job Script:")
    print(slurm_job.construct_job_script(slurm_scheduler))

    job_id = slurm_scheduler.submit(slurm_job)
    print(f"SLURM Job ID: {job_id}")

    queue_status = slurm_scheduler.query_queue()
    print("SLURM Queue Status:")
    print(queue_status)

    cancel_output = slurm_scheduler.cancel_job(job_id)
    print("SLURM Cancel Output:")
    print(cancel_output)

if __name__ == "__main__":
    main()
