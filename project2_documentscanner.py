import cv2
import numpy as np

##################################
widthImg = 640
heightImg = 480
##################################


####################################################################
def empty(a):
    pass

def preProcessing(img):
    #Input an image and convert it into canny for edge detection
    imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray,(5,5),1)
    imgCanny = cv2.Canny(imgBlur, 200, 200)

    # for documents with thin edges. Dilate and erode
    kernel = np.ones((5,5),np.uint8)
    imgDial = cv2.dilate(imgCanny,kernel,iterations=2)
    imgThres = cv2.erode(imgDial,kernel,iterations=2)

    return imgThres

def getContours(img):
    biggest = np.array([])
    maxArea = 0

    #finding the Contour: RETR_EXTERNAL retrieves outter contours.
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    #loop for each contours
    for cnt in contours:
        area = cv2.contourArea(cnt)
        area_min = cv2.getTrackbarPos("Min Area", "TrackBars")
        if area > area_min:
            #cv2.drawContours(imgContour, cnt, -1, (255, 0, 0), 3)
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02*peri,True)
            if area > maxArea and len(approx) == 4:
                biggest = approx
                maxArea = area

    cv2.drawContours(imgContour, biggest, -1, (255, 0, 0), 10)
    #print("biggest\n", biggest)
    return biggest

def reorder(myPoints):
    myPoints = myPoints.reshape((4,2))
    myPointsNew = np.zeros((4,1,2),np.int32)
    add = myPoints.sum(1)
    #("add:", add)

    myPointsNew[0] = myPoints[np.argmin(add)]   #argmin finds index of the smallest value
    myPointsNew[3] = myPoints[np.argmax(add)]   #argmax finds index of the largest value


    #Subtrack two points to figure out whichone comes first
    diff = np.diff(myPoints, axis=1)
    #print("diff:",diff)
    myPointsNew[1] = myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]
    #("NewPoints\n\n", myPointsNew)
    return myPointsNew


def getWarp(img,biggest):
    #print(biggest)
    biggest = reorder(biggest)
    # Getting the corner locations of the card
    pts1 = np.float32(biggest)
    # defining second set of points to transform the image into
    pts2 = np.float32([[0, 0], [widthImg,0], [0, heightImg], [widthImg, heightImg]])

    # getting transformation matrix
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgOutput = cv2.warpPerspective(img, matrix, (widthImg, heightImg))

    imgCropped = imgOutput[20:imgOutput.shape[0] - 20, 20:imgOutput.shape[1]-20]
    imgCropped = cv2.resize(imgCropped, (widthImg,heightImg))

    return imgOutput

def stackImages(scale,imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape [:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None,scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        ver = hor
    return ver
####################################################################



cap = cv2.VideoCapture(0)
cap.set(3, widthImg)      # 3, set window width
cap.set(4, heightImg)     # 4, set window height
cap.set(10, 150)            #

cv2.namedWindow("TrackBars")
cv2.resizeWindow("TrackBars",640,240)
cv2.createTrackbar("Min Area","TrackBars", 2000, 9999, empty)


while True:

    success, img = cap.read()
    img = cv2.resize(img, (widthImg,heightImg))
    imgContour = img.copy()
    imgThres = preProcessing(img)
    biggest = getContours(imgThres) #Get contours for min are and get the biggest one
    if biggest.size != 0:
        imgWarped = getWarp(img, biggest)
        imageArray = ([img,imgContour],
                      [imgThres,imgWarped])
        stackedImages = stackImages(0.6,imageArray)
        cv2.imshow("Result", stackedImages)
        cv2.imshow("ImagedWrapped", imgWarped)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break