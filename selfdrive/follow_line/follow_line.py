import tanq_rest as tanq
import track_cv as track
import time
import numpy as np
import traceback
import math
import track_conf as tconf
import logging

logging.basicConfig(filename="track.log",level=logging.DEBUG)

PN = 0

def find_line(side):
    logging.debug (("Finding line", side))
    if side == 0:
        return None, None
        
    for i in xrange(0, tconf.find_turn_attempts):
        turn(side, tconf.find_turn_step)
        angle, shift = get_vector()
        if angle is not None:
            return angle, shift

    return None, None

def get_photo():
    global PN
    ph, hc = tanq.photo()
    if ph is None:
        return False, None, None
    if not ph["rc"]:
        return False, None, None
    phid = ph["name"]
    fname = tanq.get_photo(phid, "photos")
    PN += 1
    return True, phid, fname


def get_vector():
    rc, phid, fname = get_photo()
    angle, shift = track.handle_pic(fname, fout="photos/out/{0}.jpg".format(PN))
    return angle, shift


def turn(r, t):
    turn_cmd = "s0" if r > 0 else "0s"
    ret_cmd = "f0" if r > 0 else "0f"
    turn = "Right" if r > 0 else "Left"
    logging.debug(("Turn", turn, t))
    tanq.set_motors(turn_cmd)
    time.sleep(t)
    tanq.set_motors(ret_cmd)

def check_shift_turn(angle, shift):
    turn_state = 0
    if angle < tconf.turn_angle or angle > 180 - tconf.turn_angle:
        turn_state = np.sign(90 - angle)

    shift_state = 0
    if abs(shift) > tconf.shift_max:
        shift_state = np.sign(shift)
    return turn_state, shift_state

def get_turn(turn_state, shift_state):
    turn_dir = 0
    turn_val = 0
    if shift_state != 0:
        turn_dir = shift_state
        turn_val = tconf.shift_step if shift_state != turn_state else tconf.turn_step
    elif turn_state != 0:
        turn_dir = turn_state
        turn_val = tconf.turn_step
    return turn_dir, turn_val                


def follow(iterations):
    tanq.set_motors("ff")   

    try:
        last_turn = 0
        last_angle = 0 

        for i in range(0, iterations):
            a, shift = get_vector()
            if a is None:
                if last_turn != 0:
                    a, shift = find_line(last_turn)
                    if a is None:
                        break
                elif last_angle != 0:
                    logging.debug(("Looking for line by angle", last_angle))
                    turn(np.sign(90 - last_angle), tconf.turn_step)
                    continue
                else:
                    break

            logging.debug((i, "Angle", a, "Shift", shift))

            turn_state, shift_state = check_shift_turn(a, shift)

            turn_dir, turn_val = get_turn(turn_state, shift_state)

            if turn_dir != 0:
                turn(turn_dir, turn_val)
                last_turn = turn_dir
            else:
                time.sleep(tconf.straight_run)
                last_turn = 0
            last_angle = a
        
    finally:
        tanq.set_motors("ss")



if __name__ == '__main__':
    follow(tconf.max_steps)
