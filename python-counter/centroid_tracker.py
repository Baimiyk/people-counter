import numpy as np
from typing import List, Dict, Tuple

class CentroidTracker:
    def __init__(self, max_disappeared: int = 50, max_distance: int = 50):
        # Inisialisasi ID unik
        self.nextObjectID = 0
        
        # Dictionary untuk menyimpan ID dan Centroid-nya
        self.objects: Dict[int, np.ndarray] = {}
        
        # Dictionary untuk menghitung berapa frame objek 'menghilang'
        self.disappeared: Dict[int, int] = {}

        # Parameter tuning
        self.max_disappeared = max_disappeared 
        self.max_distance = max_distance       

    def register(self, centroid: np.ndarray):
        """Mendaftarkan objek baru."""
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1

    def deregister(self, objectID: int):
        """Menghapus ID objek dari tracking."""
        self.objects.pop(objectID, None)
        self.disappeared.pop(objectID, None)

    def update(self, rects: List[Tuple[int, int, int, int]]):
        """
        Update lokasi objek berdasarkan bounding box baru.
        :param rects: List of bounding boxes (startX, startY, endX, endY)
        """
        # Cek apakah list bounding box kosong
        if len(rects) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.max_disappeared:
                    self.deregister(objectID)
            return self.objects

        # Inisialisasi centroid input baru
        rects_array = np.array(rects)
        inputCentroids = np.zeros((len(rects_array), 2), dtype="int")
        
        # Hitung titik tengah (centroid)
        inputCentroids[:, 0] = (rects_array[:, 0] + rects_array[:, 2]) // 2
        inputCentroids[:, 1] = (rects_array[:, 1] + rects_array[:, 3]) // 2

        # Jika belum ada objek yang dilacak, daftarkan semua
        if len(self.objects) == 0:
            for i in range(len(inputCentroids)):
                self.register(inputCentroids[i])
        
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = np.array(list(self.objects.values()))

            # Hitung jarak Euclidean antara objek lama dan input baru
            D = np.linalg.norm(objectCentroids[:, np.newaxis] - inputCentroids[np.newaxis, :], axis=2)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue

                if D[row][col] > self.max_distance:
                    continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.disappeared[objectID] = 0

                usedRows.add(row)
                usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            # Hapus objek lama yang tidak punya pasangan baru (Lost)
            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1

                    if self.disappeared[objectID] > self.max_disappeared:
                        self.deregister(objectID)

            # Daftarkan input baru yang tidak punya pasangan lama (New)
            else:
                for col in unusedCols:
                    self.register(inputCentroids[col])

        return self.objects