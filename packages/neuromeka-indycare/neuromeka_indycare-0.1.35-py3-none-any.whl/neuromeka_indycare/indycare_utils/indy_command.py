'''
Created on 2020. 3. 13.

@author: YJHeo
@author: GWKim

@edit: Jan 5 2022
    add shm_sys_access
    add some get data function
    get_last_emergency_info return int
'''

import os
import time
import grpc

from neuromeka import IndyDCP3


class IndyCommand:
    def __init__(self, joint_dof=6):
        """ Select IndyDCP3 (v3) or IndyDCP (v2) """
        self.joint_dof = joint_dof
        self.indy_master = IndyDCP3("127.0.0.1")

    def try_except(self, func, default):
        try:
            return func()
        except Exception as e:
            print(f"error message: {e}")
            return default

    # Robot control state
    def get_robot_status(self):
        '''
        OP_SYSTEM_OFF = 0,
        OP_SYSTEM_ON = 1,
        OP_VIOLATE = 2,
        OP_RECOVER_HARD = 3,
        OP_RECOVER_SOFT = 4,
        OP_IDLE = 5,
        OP_MOVING = 6,
        OP_TEACHING = 7,
        OP_COLLISION = 8,
        OP_STOP_AND_OFF = 9,
        OP_COMPLIANCE = 10,
        OP_BRAKE_CONTROL = 11,
        OP_SYSTEM_RESET = 12,
        OP_SYSTEM_SWITCH = 13,
        OP_VIOLATE_HARD = 15,
        OP_MANUAL_RECOVER = 16,
        TELE_OP = 17,
        '''
        attr = ['ready', 'emergency', 'collision', 'error', 'busy', 'movedone',
                'home', 'zero', 'resetting', 'teaching', 'direct_teaching']
        res = {a: False for a in attr}
        val = self.try_except(lambda: self.indy_master.get_control_data()['op_state'], 2)
        if val == 5:
            res['ready'] = True
        elif val == 2 or val == 15:
            res['emergency'] = True
            res['error'] = True
        elif val == 8:
            res['collision'] = True
        elif val == 6 or val == 12:
            res['busy'] = True
        elif val == 3 or val == 4 or val == 16:
            res['resetting'] = True
        elif val == 7:
            res['teaching'] = True
            res['direct_teaching'] = True
        return res

    # Program state
    def get_program_state(self):
        program_state = ['stop', 'running', 'pause']
        val = self.try_except(lambda: self.indy_master.get_program_data()['program_state'], 1)
        res = {a: False for a in program_state}
        if val == 0:
            res['stop'] = True
        elif val == 1:
            res['running'] = True
        elif val == 2:
            res['pause'] = True
        return res

    def get_collision_level(self):
        val = self.try_except(lambda: self.indy_master.get_coll_sens_level(), {'level' : 3})
        return val


    # Get robot data
    def get_rt_data(self):
        attr = ['time', 'task_time', 'max_task_time', 'compute_time', 'max_compute_time',
                'ecat_time', 'max_ecat_time', 'ecat_master_state', 'ecat_slave_num']
        time = self.try_except(lambda: self.indy_master.get_control_data()['running_hours']*3600 + self.indy_master.get_control_data()['running_mins']*60 + self.indy_master.get_control_data()['running_secs'], 0)
        val = [time, 0, 0, 0, 0, 0, 0, 0, 0]
        res = {}
        for att in attr:
            res[att] = val[attr.index(att)]
        return res

    def get_joint_pos(self):
        val = self.try_except(lambda: self.indy_master.get_control_data()['q'], [0] * self.joint_dof)
        return val

    def get_curr_joint_pos(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['qdes'], [0] * self.joint_dof)
        return val

    def get_joint_vel(self):
        val = self.try_except(lambda: self.indy_master.get_control_data()['qdot'], [0] * self.joint_dof)
        return val

    # New Jan 5
    def get_joint_vel_des(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['qdotdes'], [0] * self.joint_dof)
        return val

    # New Jan 5
    def get_joint_vel_ref(self):
        qdotdes = self.try_except(lambda: self.indy_master.get_control_state()['qdotdes'], [0] * self.joint_dof)
        qdot = self.try_except(lambda: self.indy_master.get_control_state()['qdot'], [0] * self.joint_dof)
        edot = [item1 - item2 for item1, item2 in zip(qdotdes, qdot)]
        return edot

    def get_task_pos(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['p'], [0] * self.joint_dof)
        return val

    # New Jan 5
    def get_curr_task_pos(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['pdes'], [0] * self.joint_dof)
        return val

    def get_task_vel(self):
        val = self.try_except(lambda: self.indy_master.get_control_data()['pdot'], [0] * self.joint_dof)
        return val

    # New Jan 5
    def get_task_vel_des(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['pdotdes'], [0] * self.joint_dof)
        return val

    # New Jan 5
    def get_task_vel_ref(self):
        pdotdes = self.try_except(lambda: self.indy_master.get_control_state()['pdotdes'], [0] * self.joint_dof)
        pdot = self.try_except(lambda: self.indy_master.get_control_state()['pdot'], [0] * self.joint_dof)
        evel = [item1 - item2 for item1, item2 in zip(pdotdes, pdot)]
        return evel


    def get_actual_torque(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['tau_act'], [0] * self.joint_dof)
        return val

    def get_external_torque(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['tau_ext'], [0] * self.joint_dof)
        return val

    def get_torque_ref(self):
        res = [0.0] * self.joint_dof
        return res

    # New Jan 5
    def get_overruns(self):
        return 0

    def get_joint_acc(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['pddot'], [0] * self.joint_dof)
        return val

    def get_joint_acc_des(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['pddotdes'], [0] * self.joint_dof)
        return val

    def get_task_acc(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['pddot'], [0] * self.joint_dof)
        return val

    def get_task_acc_des(self):
        val = self.try_except(lambda: self.indy_master.get_control_state()['pddotdes'], [0] * self.joint_dof)
        return val

    # Robot emergency data
    def get_last_emergency_info(self):
        attr = ['error_code', 'args_int', 'args_double', 'time']
        #     error_code = ['EMG button', 'Collision', 'Position limit', 'Vel/Acc limit', 'Motor state error',
        #                   'Torque limit', 'Connection lost', 'Path error', 'Endtool error', 'Singularity',
        #                   'Overcurrent', 'Near position limit', 'Near velocity limit', 'Near singularity',
        #                   'No error']
        val = self.try_except(lambda: self.indy_master.get_violation_data(), {'i_args': [0], 'f_args': [0.0], 'violation_code': '80', 'j_index': 0, 'violation_str': 'EMERG_ROBOTSPEC_READ_FAILED'})
        violation_code = val['violation_code']
        violation_str = val['violation_str']
        # if violation_code == 0x01 << (7 + 11): # EMG button:
        #     error_val = 0
        if 'EMG' in violation_str: # EMG button:
            error_val = 0

        elif "Collision Detected" in violation_str: # Collision
            error_val = 1

        # elif violation_code == 0x01 << (7 + 0): # Position limit
        #     error_val = 2
        elif 'Joint Position Limit' in violation_str: # Position limit
            error_val = 2

        # elif violation_code == 0x01 << (2) or violation_code == 0x01 << (7 + 1) or violation_code == 0x01 << (7 + 3) or violation_code == 0x01 << (7 + 0): # Vel/Acc limit
        #     error_val = 3
        elif "Joint Velocity Limit" in violation_str: # Vel/Acc limit
            error_val = 3

        # elif violation_code == 0x01 << (7 + 12 + 2) or violation_code == 0x01 << (7 + 12 + 4) or violation_code == 0x01 << (7 + 12 + 5) or violation_code == 0x01 << (7 + 12 + 6) or violation_code == 0x01 << (7 + 12 + 7): #Motor state error
        #     error_val = 4
        elif 'Motor Status Error' in violation_str: #Motor state error
            error_val = 4

        # elif violation_code == 0x01 << (4) or violation_code == 0x01 << (7 + 2): #Torque limit
        #     error_val = 5
        elif 'Torque Limit' in violation_str: #Torque limit
            error_val = 5

        # elif violation_code == 0x01 << (7 + 12 + 1): #Connection lost
        #     error_val = 6
        elif 'Connection Lost' in violation_str: #Connection lost
            error_val = 6

        # elif violation_code == 0x01 << (5): #Singularity
        #     error_val = 9
        # elif "TCP Singular Closed" in violation_str: # Singularity
        #     error_val = 9

        # elif violation_code == 0x01 << (7 + 12 + 3): #Overcurrent
        #     error_val = 10
        elif 'Over Current' in violation_str: #Overcurrent
            error_val = 10

        # elif violation_code == 0x01 << (1): #Near position limit
        #     error_val = 11
        elif 'Position Limit Closed' in violation_str: #Near position limit
            error_val = 12

        # elif violation_code == 0x01 << (2): #Near velocity limit
        #     error_val = 12
        elif 'Velocity Limit Closed' in violation_str: #Near velocity limit
            error_val = 13

        # elif violation_code == 0x01 << (6): #Near singularity
        #     error_val = 13
        elif "TCP Singular Closed" in violation_str: #Near singularity
            error_val = 14

        elif "TCP Speed Limit" in violation_str: #Near singularity
            error_val = 17

        elif "TCP Force Limit" in violation_str: #Near singularity
            error_val = 18
        
        elif "Over Heated" in violation_str: #Motor Over heated
            error_val = 22
        
        elif "Standstill Failed" in violation_str: #Standstill failed
            error_val = 30
        elif "EMERG_ROBOTSPEC_READ_FAILED" in violation_str:
            error_val = 80

        else: # no error
            error_val = -1

        res = {attr[0]: error_val,  # error_code[shm_val[0]],
               attr[1]: val['i_args'],
               attr[2]: val['f_args'],
               'violation_str': violation_str}
        return res

    def get_motor_state(self):
        val = self.try_except(lambda: self.indy_master.get_servo_data()['servo_actives'], [False] * self.joint_dof)
        return val
    def get_temperature_data(self):
        val = self.try_except(lambda: self.indy_master.get_servo_data()['temperatures'], [0] * self.joint_dof)
        return val

    def get_float_variable_data(self):
        """
        Float Variables:
            [
                addr -> int32
                value -> float
            ]
        """
        val = self.try_except(lambda: self.indy_master.get_float_variable()['variables'], [])
        return val

    def get_tactTime(self):
        val = self.try_except(lambda: self.indy_master.get_tact_time()['tact_time'], 0.0)
        return val
    
    def get_device_info(self):
        val = self.try_except(lambda: self.indy_master.get_device_info(), {})
        return val
    