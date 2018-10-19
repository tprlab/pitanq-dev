import tanq_rest as tanq
import track_cv as track
import time
import numpy as np
import traceback
import math
import logging

logging.basicConfig(filename="track.log",level=logging.DEBUG)

PN = 0

def find_line(side):
    logging.debug (("Finding line", side))
    if side == 0:
        return None, None
        
    for i in xrange(0, 5):
        turn(side, 0.2)
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
                    turn(np.sign(90 - last_angle), 0.25)
                    continue
                else:
                    break

            logging.debug((i, "Angle", a, "Shift", shift))

            turn_state = 0
            if a < 45 or a > 135:
                turn_state = np.sign(90 - a)

            shift_state = 0
            if abs(shift) > 20:
                shift_state = np.sign(shift)

            turn_dir = 0
            turn_val = 0

            turn_K = 2.0

            if shift_state != 0:
                turn_dir = shift_state
                turn_val = 1.0 if shift_state != turn_state else turn_K
            elif turn_state != 0:
                turn_dir = turn_state
                turn_val = turn_K
                

            if turn_dir != 0:
                turn(turn_dir, 0.125 * turn_val)
                last_turn = turn_dir
            else:
                time.sleep(0.5)
                last_turn = 0
            last_angle = a
        
    finally:
        tanq.set_motors("ss")



#time.sleep(5)
follow(10)
