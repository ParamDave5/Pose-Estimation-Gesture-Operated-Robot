import cv2

cam = cv2.VideoCapture(0)
ret_val, image = cam.read()
print('cam image=%dx%d' % (image.shape[1], image.shape[0]))

while True:
    ret_val, image = cam.read()
    print(type(image))
    cv2.imshow('frame',image)
    if cv2.waitKey(1) == 27:
        break

cv2.destroyAllWindows()
