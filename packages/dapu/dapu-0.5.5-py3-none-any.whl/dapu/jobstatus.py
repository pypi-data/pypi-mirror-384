from enum import Enum

class JobStatus(Enum):
    """
    Task instance (in Agenda) execution status. Important ones are 0 and -1.
    """
    COMING = 21 # Manager is just preparing this instance but not ended yet, Worker is not allowed to execute this
    UNMANAGED = 22 # Manager failed without noice -> after some time COMING are changed to UNMANAGER (it is dangerous to mark this IDLE) 
    
    STARTED = -1 # alias for busy
    BUSY = -1 # Task instance is being executed (in bad case it have beed stalled)  
    IDLE = 0 # Task instance is ready to execute
    DONE = 1 # Task instance execution is done, no problems
    FAILED = 13 # Task instance execution failed
    STALLED = 14 # Sudden death have been detected later (long time BUSY is marked as failed), may be occured "power cut"
    SKIPPED = 30 # one Worker have skipped this because other instance of same Task is later in Agenda too
    LOST = 31 # during execution on instance the Task files were lost
