# Tank autopilot follows a white line using OpenCV
There is a code to make [tank PiTanq](https://github.com/tprlab/pitanq) follow a white line using its own intelligence.

It is client-side code, need to be run from a computer. The computer should be able to connect with PiTanq. 

All the logic and calculations are doing locally, the tank provides pictures and follows the directional commands.

## Image processing
Images from the tank camera are the only source of the input information. 

The idea is to detect a white line on a photo and determine its direction.


### Grayscale the image
The first operation on the image is to grayscale it and then blur.
```
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, (9, 9), 0)
```    

### Threshold
The general approach is to set up a threshold to keep only light parts of the image.
```
        rc, gray = cv.threshold(image, T, 255, 0)
```       

But the images have different brightness and it is impossible to select the same threshold for all cases.

Then I decide to adjust the threshold individually for each image until its white pixels are some reasonable part of the whole image.

(Heuristical approach found 4-10% range for the best results)

```
def balance_pic(image):
    global T
    ret = None
    direction = 0
    for i in range(0, 10):
        rc, gray = cv.threshold(image, T, 255, 0)
        crop = Roi.crop_roi(gray)
        nwh = cv.countNonZero(crop)
        perc = int(100 * nwh / Roi.get_area())
        logging.debug(("balance attempt", i, T, perc))
        if perc > 12:
            if T > 199:
                break
            if direction == -1:
                ret = crop
                break
            T += 10
            direction = 1
        elif perc < 4:
            if T < 50:
                break
            if  direction == 1:
                ret = crop
                break
            T -= 10
            direction = -1
        else:
            ret = crop
            break  
    return ret      
```

### Detecting lines
The general approach is to use Canny edge detector and then apply Hough line transformation to get a set of lines.

So far the colors and geometry of images are not perfect the Hough detector demonstrated very odd results.

Then I decided to change the approach and use contours detection to find the line.

In most of the cases the biggest light countour turned out to be the line.

A line between long sides of the countour bounding box to be considered as a driving vector.

```
def find_main_countour(image):
    im2, cnts, hierarchy = cv.findContours(image, cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE)
    C = None
    if cnts is not None and len(cnts) > 0:
         C = max(cnts, key = cv.contourArea)
    if C is None:
        return None, None
    rect = cv.minAreaRect(C)
    box = cv.boxPoints(rect)
    box = np.int0(box)
    box = geom.order_box(box)
    return C, box
```

### Making decisions
The vector has 2 main features:
* angle with horizontal axis
* shift relatively to the image middle point

Depending on these features the algo decides if the tank should go straight or turn (light or hard)

```
        while(True):
            a, shift = get_vector()
            if a is None:
              # there is some code omitted related to line finding
              break
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
            else:
                time.sleep(0.5)
```
