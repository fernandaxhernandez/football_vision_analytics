# scripts/calibrate.py
# run: python scripts/calibrate.py path/to/frame.jpg
import cv2, json, sys
imgp = sys.argv[1] if len(sys.argv)>1 else None
img = cv2.imread(imgp) if imgp else None
pts = []
def click(e,x,y,flags,param):
    if e==cv2.EVENT_LBUTTONDOWN:
        pts.append((x,y))
cv2.namedWindow("img"); cv2.setMouseCallback("img", click)
while True:
    if img is None:
        break
    disp = img.copy()
    for p in pts:
        cv2.circle(disp, p, 5, (0,255,0), -1)
    cv2.imshow("img", disp)
    k = cv2.waitKey(1) & 0xFF
    if k==27 or len(pts)>=4:
        break
cv2.destroyAllWindows()
if len(pts) < 4:
    print("Need 4 points. Got:", pts); sys.exit(1)
dst = [(0,0),(105,0),(105,68),(0,68)]  # change if different pitch dims
with open("config/calib.json","w") as f:
    json.dump({"src_pts": pts, "dst_pts": dst}, f, indent=2)
print("Saved config/calib.json")