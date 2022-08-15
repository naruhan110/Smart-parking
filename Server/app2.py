
import cv2
import numpy as np
from lib_detection import load_model, detect_lp, im2single
import pyqrcode
import time

class parking:
    def __init__(self, wpod_net_path, model_svm_path):
        self.wpod_net = load_model(wpod_net_path)
        self.model_svm = cv2.ml.SVM_load(model_svm_path)

    def scanqr(self, img):
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        #self.save_data_2("data.txt", data)
        return data

    """def save_data(self, path, plate):
        with open(path, 'a') as data2:
            data2.write(plate[0] +","+ plate[1] +",")

    def save_data_2(self, path, qr):
        with open(path, 'a') as data2:
            data2.write(' '+ qr +'/n')"""

    def read_plate(self, img):
        # Đọc file ảnh đầu vào
        Ivehicle = img.copy()

        # Kích thước lớn nhất và nhỏ nhất của 1 chiều ảnh
        Dmax = 608
        Dmin = 288

        # Lấy tỷ lệ giữa W và H của ảnh và tìm ra chiều nhỏ nhất
        ratio = float(max(Ivehicle.shape[:2])) / min(Ivehicle.shape[:2])
        side = int(ratio * Dmin)
        bound_dim = min(side, Dmax)
        _, LpImg, lp_type = detect_lp(self.wpod_net, im2single(Ivehicle), bound_dim, lp_threshold=0.5)
        # Cau hinh tham so cho model SVM
        digit_w = 30  # Kich thuoc ki tu
        digit_h = 60  # Kich thuoc ki tu

        plate_info = ""
        if (len(LpImg)):
            # Chuyen doi anh bien so
            LpImg[0] = cv2.convertScaleAbs(LpImg[0], alpha=(255.0))
            #roi = LpImg[0]

            # Chuyen anh bien so ve gray
            gray = cv2.cvtColor(LpImg[0], cv2.COLOR_RGB2GRAY)

            [height, long] = gray.shape
            if lp_type == 2:
                gray2 = gray[height // 2:height, 0:long]
                gray = gray[0:height // 2, 0:long]
                # ratio = float(max(gray.shape[:2])) / min(gray.shape[:2])
            else:
                gray2 = gray[height - 1:height, long - 1:long]

            # Ap dung threshold de phan tach so va nen
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV, 49, 20)

            # Segment kí tự
            kernel3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            thre_mor = cv2.morphologyEx(binary, cv2.MORPH_DILATE, kernel3)
            cont, _ = cv2.findContours(thre_mor, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            for c in sort_contours(cont):
                (x, y, w, h) = cv2.boundingRect(c)
                ratio = h / w
                if 1.5 <= ratio <= 4:  # Chon cac contour dam bao ve ratio w/h
                    if 0.95 >= h / gray.shape[0] >= 0.65:  # Chon cac contour cao tu 65% - 95%

                        # Tach so va predict
                        curr_num = thre_mor[y:y + h, x:x + w]
                        curr_num = cv2.resize(curr_num, dsize=(digit_w, digit_h))
                        _, curr_num = cv2.threshold(curr_num, 30, 255, cv2.THRESH_BINARY)
                        curr_num = np.array(curr_num, dtype=np.float32)
                        curr_num = curr_num.reshape(-1, digit_w * digit_h)

                        # Dua vao model SVM
                        result = self.model_svm.predict(curr_num)[1]
                        result = int(result[0, 0])

                        if result <= 9:  # Neu la so thi hien thi luon
                            result = str(result)
                        else:  # Neu la chu thi chuyen bang ASCII
                            result = chr(result)
                        plate_info += result

            binary2 = cv2.adaptiveThreshold(gray2, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY_INV, 49, 20)
            thre_mor_2 = cv2.morphologyEx(binary2, cv2.MORPH_DILATE, kernel3)
            cont_2, _ = cv2.findContours(thre_mor_2, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            for c in sort_contours(cont_2):
                (x, y, w, h) = cv2.boundingRect(c)
                ratio = h / w
                if 1.5 <= ratio <= 4:  #Chon cac contour dam bao ve ratio w/h
                    if 0.95 >= h/gray2.shape[0] >= 0.65:  #Chon cac contour cao tu 60% - 95%

                        # Tach so va predict
                        curr_num = thre_mor_2[y:y + h, x:x + w]
                        curr_num = cv2.resize(curr_num, dsize=(digit_w, digit_h))
                        _, curr_num = cv2.threshold(curr_num, 30, 255, cv2.THRESH_BINARY)
                        curr_num = np.array(curr_num, dtype=np.float32)
                        curr_num = curr_num.reshape(-1, digit_w * digit_h)

                        # Dua vao model SVM
                        result = self.model_svm.predict(curr_num)[1]
                        result = int(result[0, 0])

                        if result <= 9:  # Neu la so thi hien thi luon
                            result = str(result)
                        else:  # Neu la chu thi chuyen bang ASCII
                            result = chr(result)

                        plate_info += result

            # Hien thi anh
            print("Bien so=", plate_info)
        #self.save_data("data.txt", [plate_info, timenow])
        return plate_info


# Ham sap xep contour tu trai sang phai
def sort_contours(cnts):

    reverse = False
    i = 0
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
                                        key=lambda b: b[1][i], reverse=reverse))
    return cnts

# Ham fine tune bien so, loai bo cac ki tu khong hop ly
def fine_tune(lp):
    # Dinh nghia cac ky tu tren bien so
    char_list = '0123456789ABCDEFGHKLMNPRSTUVXYZ'
    newString = ""
    for i in range(len(lp)):
        if lp[i] in char_list:
            newString += lp[i]
    return newString


if __name__ == "__main__":
    img_path = "test/test2.jpg"
    img = cv2.imread(img_path)
    plate = parking("wpod-net_update1.json", "svm.xml")
    print(plate.read_plate(img))

